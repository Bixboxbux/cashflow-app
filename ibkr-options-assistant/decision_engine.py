"""
IBKR Options Trading Assistant - Decision Engine

This module generates trading decisions (BUY/SELL/WAIT) based on
detected signals. It combines multiple signals, applies weights,
and calculates confidence scores.

CRITICAL DISCLAIMER:
═══════════════════════════════════════════════════════════════════
This engine produces RECOMMENDATIONS for human consideration ONLY.
It does NOT execute any trades automatically.

All decisions must be manually reviewed and executed by the user.
Past signals do not guarantee future results.
Options trading involves significant risk of loss.
═══════════════════════════════════════════════════════════════════

Author: IBKR Options Assistant
License: MIT
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from data_fetcher_ibkr import OptionData
from signal_engine import (
    SignalEngine, OptionSignals, Signal,
    SignalType, SignalDirection
)
from config import CONFIG, Decision


# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class ConfidenceBreakdown:
    """
    Detailed breakdown of how confidence score was calculated.

    Provides transparency into the decision-making process.
    """
    # Base scores from signals
    signal_scores: Dict[str, float] = field(default_factory=dict)

    # Weighted signal contribution
    weighted_total: float = 0.0

    # Adjustments
    volatility_penalty: float = 0.0
    liquidity_bonus: float = 0.0
    spread_penalty: float = 0.0
    convergence_bonus: float = 0.0  # Multiple signals agreeing

    # Final score
    final_score: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for display."""
        return {
            'signal_scores': self.signal_scores,
            'weighted_total': round(self.weighted_total, 1),
            'adjustments': {
                'volatility_penalty': round(self.volatility_penalty, 1),
                'liquidity_bonus': round(self.liquidity_bonus, 1),
                'spread_penalty': round(self.spread_penalty, 1),
                'convergence_bonus': round(self.convergence_bonus, 1)
            },
            'final_score': round(self.final_score, 1)
        }


@dataclass
class TradingAlert:
    """
    A trading alert representing a potential opportunity.

    This is the final output of the decision engine,
    containing all information needed for human review.
    """
    # Identification
    alert_id: str
    timestamp: datetime

    # Option details
    symbol: str
    option_type: str  # "CALL" or "PUT"
    strike: float
    expiration: str
    days_to_expiry: int

    # Pricing
    underlying_price: float
    option_bid: float
    option_ask: float
    option_mid: float

    # Decision
    decision: Decision
    confidence: float  # 0-100
    confidence_breakdown: ConfidenceBreakdown

    # Signals
    signals: List[Signal]
    signal_count: int
    dominant_direction: SignalDirection

    # Additional metrics
    volume: int
    avg_volume: int
    volume_ratio: float
    open_interest: int
    implied_volatility: float
    delta: float
    spread_pct: float

    @property
    def alert_summary(self) -> str:
        """Generate one-line summary for the alert."""
        return (
            f"{self.symbol} {self.option_type} ${self.strike:.0f} "
            f"Exp {self.expiration} | {self.decision.value} "
            f"({self.confidence:.0f}%)"
        )

    @property
    def is_actionable(self) -> bool:
        """Check if alert suggests action (not WAIT)."""
        return self.decision != Decision.WAIT

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'alert_id': self.alert_id,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'option_type': self.option_type,
            'strike': self.strike,
            'expiration': self.expiration,
            'days_to_expiry': self.days_to_expiry,
            'underlying_price': round(self.underlying_price, 2),
            'option_bid': round(self.option_bid, 2),
            'option_ask': round(self.option_ask, 2),
            'option_mid': round(self.option_mid, 2),
            'decision': self.decision.value,
            'confidence': round(self.confidence, 1),
            'confidence_breakdown': self.confidence_breakdown.to_dict(),
            'signals': [
                {
                    'type': s.signal_type.value,
                    'direction': s.direction.value,
                    'strength': round(s.strength, 1),
                    'description': s.description
                }
                for s in self.signals
            ],
            'signal_count': self.signal_count,
            'dominant_direction': self.dominant_direction.value,
            'volume': self.volume,
            'avg_volume': self.avg_volume,
            'volume_ratio': round(self.volume_ratio, 2),
            'open_interest': self.open_interest,
            'implied_volatility': round(self.implied_volatility, 1),
            'delta': round(self.delta, 3),
            'spread_pct': round(self.spread_pct, 2)
        }


class DecisionEngine:
    """
    Trading decision engine with confidence scoring.

    This engine takes analyzed options with signals and produces
    actionable trading alerts with BUY/SELL/WAIT recommendations.

    Confidence Calculation:
    1. Weight each signal by its type and strength
    2. Apply volatility penalty (high IV = lower confidence)
    3. Apply liquidity bonus (high volume = higher confidence)
    4. Apply spread penalty (wide spreads = lower confidence)
    5. Apply convergence bonus (multiple aligned signals)

    Decision Rules:
    - BUY: Confidence >= 65% AND bullish direction
    - SELL: Confidence >= 65% AND bearish direction
    - WAIT: Confidence < 65% OR neutral direction

    Usage:
        engine = DecisionEngine()
        alerts = engine.generate_alerts(option_signals_list)
    """

    def __init__(self):
        """Initialize the decision engine."""
        self.config = CONFIG.decision

        # Signal weights
        self.weights = self.config.signal_weights

        # Thresholds
        self.min_confidence = self.config.min_confidence_threshold
        self.vol_penalty_threshold = self.config.volatility_penalty_threshold
        self.vol_penalty_factor = self.config.volatility_penalty_factor
        self.liq_bonus_threshold = self.config.liquidity_bonus_threshold
        self.liq_bonus_factor = self.config.liquidity_bonus_factor

        # Alert counter for unique IDs
        self._alert_counter = 0

        logger.info(
            f"DecisionEngine initialized | "
            f"Min confidence: {self.min_confidence}%"
        )

    def generate_alerts(
        self,
        option_signals_list: List[OptionSignals],
        min_confidence: float = None
    ) -> List[TradingAlert]:
        """
        Generate trading alerts from analyzed options.

        Args:
            option_signals_list: List of options with detected signals
            min_confidence: Override minimum confidence threshold

        Returns:
            List of TradingAlert objects
        """
        min_conf = min_confidence if min_confidence is not None else 0.0
        alerts = []

        for option_signals in option_signals_list:
            if not option_signals.has_signals:
                continue

            alert = self._create_alert(option_signals)

            if alert.confidence >= min_conf:
                alerts.append(alert)

        # Sort by confidence (highest first)
        alerts.sort(key=lambda a: a.confidence, reverse=True)

        logger.info(
            f"Generated {len(alerts)} alerts from "
            f"{len(option_signals_list)} analyzed options"
        )

        return alerts

    def _create_alert(self, option_signals: OptionSignals) -> TradingAlert:
        """
        Create a trading alert from option signals.

        Args:
            option_signals: Option with detected signals

        Returns:
            TradingAlert object
        """
        option = option_signals.option
        signals = option_signals.signals

        # Calculate confidence
        confidence, breakdown = self._calculate_confidence(option_signals)

        # Determine decision
        decision = self._determine_decision(
            confidence,
            option_signals.dominant_direction
        )

        # Generate unique alert ID
        self._alert_counter += 1
        alert_id = f"ALT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._alert_counter:04d}"

        return TradingAlert(
            alert_id=alert_id,
            timestamp=datetime.now(),
            symbol=option.symbol,
            option_type=option.option_type,
            strike=option.strike,
            expiration=option.expiration,
            days_to_expiry=option.days_to_expiry,
            underlying_price=option.underlying_price,
            option_bid=option.bid,
            option_ask=option.ask,
            option_mid=option.mid,
            decision=decision,
            confidence=confidence,
            confidence_breakdown=breakdown,
            signals=signals,
            signal_count=len(signals),
            dominant_direction=option_signals.dominant_direction,
            volume=option.volume,
            avg_volume=option.avg_volume,
            volume_ratio=option.volume_ratio,
            open_interest=option.open_interest,
            implied_volatility=option.implied_volatility,
            delta=option.delta,
            spread_pct=option.spread_pct
        )

    def _calculate_confidence(
        self,
        option_signals: OptionSignals
    ) -> Tuple[float, ConfidenceBreakdown]:
        """
        Calculate confidence score with detailed breakdown.

        Confidence is calculated as:
        1. Sum of weighted signal strengths (base)
        2. Normalized to 0-100 scale
        3. Apply penalties and bonuses

        Args:
            option_signals: Option with signals

        Returns:
            Tuple of (confidence score, breakdown)
        """
        option = option_signals.option
        signals = option_signals.signals

        breakdown = ConfidenceBreakdown()

        # Step 1: Calculate weighted signal scores
        signal_scores = {}
        weighted_total = 0.0

        for signal in signals:
            signal_type = signal.signal_type.value
            weight = self.weights.get(signal_type, 0.25)

            # Normalize signal strength to 0-1 range
            normalized_strength = signal.strength / 100.0

            # Calculate weighted contribution
            contribution = normalized_strength * weight * 100

            signal_scores[signal_type] = round(contribution, 1)
            weighted_total += contribution

        breakdown.signal_scores = signal_scores
        breakdown.weighted_total = weighted_total

        # Step 2: Apply volatility penalty
        # High IV options are riskier and may be overpriced
        vol_penalty = 0.0
        if option.implied_volatility > self.vol_penalty_threshold:
            excess_iv = option.implied_volatility - self.vol_penalty_threshold
            vol_penalty = min(20.0, excess_iv * self.vol_penalty_factor)

        breakdown.volatility_penalty = -vol_penalty

        # Step 3: Apply liquidity bonus
        # High volume = better execution, more confidence
        liq_bonus = 0.0
        if option.volume > self.liq_bonus_threshold:
            excess_vol = option.volume - self.liq_bonus_threshold
            liq_bonus = min(10.0, (excess_vol / self.liq_bonus_threshold) *
                           self.liq_bonus_factor * 100)

        breakdown.liquidity_bonus = liq_bonus

        # Step 4: Apply spread penalty
        # Wide spreads = execution risk
        spread_penalty = 0.0
        if option.spread_pct > 5.0:
            spread_penalty = min(15.0, (option.spread_pct - 5.0) * 2)

        breakdown.spread_penalty = -spread_penalty

        # Step 5: Apply convergence bonus
        # Multiple signals agreeing = higher conviction
        convergence_bonus = 0.0
        if len(signals) >= 2:
            # Check if signals agree on direction
            directions = [s.direction for s in signals]
            bullish_count = sum(1 for d in directions if d == SignalDirection.BULLISH)
            bearish_count = sum(1 for d in directions if d == SignalDirection.BEARISH)

            max_agreement = max(bullish_count, bearish_count)
            if max_agreement >= 2:
                convergence_bonus = min(15.0, max_agreement * 5.0)

        breakdown.convergence_bonus = convergence_bonus

        # Calculate final score
        final_score = (
            weighted_total +
            breakdown.volatility_penalty +
            breakdown.liquidity_bonus +
            breakdown.spread_penalty +
            breakdown.convergence_bonus
        )

        # Clamp to 0-100
        final_score = max(0.0, min(100.0, final_score))

        breakdown.final_score = final_score

        return final_score, breakdown

    def _determine_decision(
        self,
        confidence: float,
        direction: SignalDirection
    ) -> Decision:
        """
        Determine trading decision based on confidence and direction.

        Decision Rules:
        - Need >= min_confidence (65%) for actionable decision
        - Bullish direction -> BUY
        - Bearish direction -> SELL
        - Neutral or low confidence -> WAIT

        Args:
            confidence: Confidence score (0-100)
            direction: Dominant signal direction

        Returns:
            Decision enum (BUY, SELL, or WAIT)
        """
        if confidence < self.min_confidence:
            return Decision.WAIT

        if direction == SignalDirection.BULLISH:
            return Decision.BUY
        elif direction == SignalDirection.BEARISH:
            return Decision.SELL
        else:
            return Decision.WAIT

    def filter_alerts(
        self,
        alerts: List[TradingAlert],
        symbol: str = None,
        option_type: str = None,
        decision: Decision = None,
        min_confidence: float = None,
        max_confidence: float = None,
        min_volume: int = None,
        max_dte: int = None
    ) -> List[TradingAlert]:
        """
        Filter alerts based on various criteria.

        Args:
            alerts: List of alerts to filter
            symbol: Filter by symbol
            option_type: Filter by CALL or PUT
            decision: Filter by decision type
            min_confidence: Minimum confidence
            max_confidence: Maximum confidence
            min_volume: Minimum volume
            max_dte: Maximum days to expiry

        Returns:
            Filtered list of alerts
        """
        filtered = alerts.copy()

        if symbol:
            filtered = [a for a in filtered if a.symbol == symbol]

        if option_type:
            filtered = [a for a in filtered if a.option_type == option_type]

        if decision:
            filtered = [a for a in filtered if a.decision == decision]

        if min_confidence is not None:
            filtered = [a for a in filtered if a.confidence >= min_confidence]

        if max_confidence is not None:
            filtered = [a for a in filtered if a.confidence <= max_confidence]

        if min_volume is not None:
            filtered = [a for a in filtered if a.volume >= min_volume]

        if max_dte is not None:
            filtered = [a for a in filtered if a.days_to_expiry <= max_dte]

        return filtered

    def get_actionable_alerts(
        self,
        alerts: List[TradingAlert]
    ) -> List[TradingAlert]:
        """
        Get only actionable alerts (BUY or SELL, not WAIT).

        Args:
            alerts: List of all alerts

        Returns:
            List of actionable alerts
        """
        return [a for a in alerts if a.is_actionable]

    def get_alerts_summary(
        self,
        alerts: List[TradingAlert]
    ) -> Dict:
        """
        Generate summary statistics for alerts.

        Args:
            alerts: List of alerts

        Returns:
            Summary dictionary
        """
        if not alerts:
            return {
                'total': 0,
                'by_decision': {},
                'by_symbol': {},
                'avg_confidence': 0.0,
                'actionable_count': 0
            }

        by_decision = {}
        for d in Decision:
            count = sum(1 for a in alerts if a.decision == d)
            by_decision[d.value] = count

        by_symbol = {}
        for alert in alerts:
            by_symbol[alert.symbol] = by_symbol.get(alert.symbol, 0) + 1

        avg_confidence = sum(a.confidence for a in alerts) / len(alerts)

        actionable = sum(1 for a in alerts if a.is_actionable)

        return {
            'total': len(alerts),
            'by_decision': by_decision,
            'by_symbol': by_symbol,
            'avg_confidence': round(avg_confidence, 1),
            'actionable_count': actionable
        }


# ══════════════════════════════════════════════════════════════════════════════
# DECISION INTERPRETATION GUIDE
# ══════════════════════════════════════════════════════════════════════════════
"""
HOW TO INTERPRET DECISIONS:

BUY Signal:
- Confidence >= 65%
- Dominant direction is BULLISH
- Consider ONLY if you agree with the analysis
- Always verify with your own research

SELL Signal:
- Confidence >= 65%
- Dominant direction is BEARISH
- Note: "SELL" means sell-to-open or close long
- NOT a recommendation to short

WAIT Signal:
- Confidence < 65% OR direction unclear
- Do NOT act on these alerts
- Wait for clearer signals

CONFIDENCE BREAKDOWN:
- 65-75%: Moderate confidence, proceed with caution
- 75-85%: Good confidence, multiple signals aligned
- 85-100%: Strong confidence, high conviction

RISK MANAGEMENT:
- Never risk more than you can afford to lose
- Use appropriate position sizing
- Consider the bid-ask spread
- Check liquidity before trading

DISCLAIMER:
These decisions are algorithmically generated and are NOT financial advice.
Always conduct your own research and consult a financial advisor.
"""
