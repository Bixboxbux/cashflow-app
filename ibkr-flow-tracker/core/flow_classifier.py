"""
Institutional Flow Tracker - Flow Classifier Module

Classifies detected flow signals with:
- Direction (BULLISH/BEARISH/NEUTRAL)
- Conviction level (HIGH/MEDIUM/LOW)
- Positioning type (Accumulation/Distribution/Hedging)
- Price targets and technical levels

This module enriches raw flow detections with analysis and context.
"""

import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from config import (
    CONFIG,
    PREMIUM_THRESHOLDS,
    CONVICTION_SCORING,
    get_sector,
)
from config.thresholds import (
    SignalType,
    FlowDirection,
    ConvictionLevel,
    PositioningType,
)
from models import (
    FlowSignal, FlowMetrics, TechnicalLevels,
    ConvictionBreakdown, OptionDetails,
)


logger = logging.getLogger(__name__)


class FlowClassifier:
    """
    Classifies and enriches flow signals.

    Responsibilities:
    1. Determine bullish/bearish direction
    2. Calculate conviction scores
    3. Classify positioning (accumulation/distribution)
    4. Generate price targets
    5. Add technical levels

    Usage:
        classifier = FlowClassifier()
        enriched_signal = classifier.classify(raw_signal, technical_levels)
    """

    def __init__(self):
        """Initialize the classifier."""
        self._scoring = CONVICTION_SCORING
        logger.info("FlowClassifier initialized")

    def classify(
        self,
        signal: FlowSignal,
        technical_levels: Optional[TechnicalLevels] = None,
        historical_flows: Optional[List[FlowSignal]] = None
    ) -> FlowSignal:
        """
        Classify and enrich a flow signal.

        Args:
            signal: Raw flow signal to classify
            technical_levels: Pre-calculated technical levels
            historical_flows: Historical flows for the same symbol

        Returns:
            Enriched FlowSignal with classification
        """
        # Set sector
        signal.sector = get_sector(signal.symbol)

        # Calculate direction if not set
        if signal.direction == FlowDirection.NEUTRAL:
            signal.direction = self._determine_direction(signal)

        # Calculate conviction score
        signal.conviction_score, signal.conviction_breakdown = self._calculate_conviction(
            signal, historical_flows
        )
        signal.conviction_level = self._scoring.get_conviction_level(signal.conviction_score)

        # Determine positioning
        signal.positioning, signal.positioning_details = self._determine_positioning(
            signal, historical_flows
        )

        # Calculate price target
        if signal.price_target == 0:
            signal.price_target = self._calculate_price_target(signal)

        # Add technical levels
        if technical_levels:
            signal.technical_levels = technical_levels

        # Add tags
        signal.tags = self._generate_tags(signal)

        return signal

    def _determine_direction(self, signal: FlowSignal) -> FlowDirection:
        """
        Determine the direction of a flow signal.

        Direction is based on:
        1. Option type (call = bullish bias, put = bearish bias)
        2. Trade side (buy vs sell)
        3. Premium size (larger = more conviction)
        """
        if not signal.option:
            return FlowDirection.NEUTRAL

        is_call = signal.option.contract_type == "C"
        is_put = signal.option.contract_type == "P"

        # Default assumption: buying options indicates directional bet
        # Calls bought = bullish, Puts bought = bearish
        if is_call:
            return FlowDirection.BULLISH
        elif is_put:
            return FlowDirection.BEARISH

        return FlowDirection.NEUTRAL

    def _calculate_conviction(
        self,
        signal: FlowSignal,
        historical_flows: Optional[List[FlowSignal]] = None
    ) -> Tuple[float, ConvictionBreakdown]:
        """
        Calculate conviction score for a signal.

        Score is based on:
        1. Premium size (30%)
        2. Volume unusualness (20%)
        3. OI change (15%)
        4. Sweep detection (15%)
        5. Multi-day pattern (10%)
        6. Technical alignment (10%)

        Returns:
            Tuple of (score, breakdown)
        """
        breakdown = ConvictionBreakdown()
        scores = {}

        # 1. Premium size score (0-100)
        premium = signal.metrics.premium_paid
        if premium >= PREMIUM_THRESHOLDS.MEGA_WHALE:
            scores["premium_size"] = 100
        elif premium >= PREMIUM_THRESHOLDS.WHALE:
            scores["premium_size"] = 85
        elif premium >= PREMIUM_THRESHOLDS.NOTABLE:
            scores["premium_size"] = 70
        elif premium >= PREMIUM_THRESHOLDS.TRACKING_MIN:
            scores["premium_size"] = 50
        else:
            scores["premium_size"] = 30

        # 2. Volume unusualness (0-100)
        volume_ratio = signal.metrics.volume_ratio
        if volume_ratio >= 10:
            scores["volume_unusual"] = 100
        elif volume_ratio >= 5:
            scores["volume_unusual"] = 80
        elif volume_ratio >= 3:
            scores["volume_unusual"] = 60
        elif volume_ratio >= 2:
            scores["volume_unusual"] = 40
        else:
            scores["volume_unusual"] = 20

        # 3. OI change (0-100)
        oi_change = abs(signal.metrics.oi_change_pct)
        if oi_change >= 100:
            scores["oi_change"] = 100
        elif oi_change >= 50:
            scores["oi_change"] = 75
        elif oi_change >= 20:
            scores["oi_change"] = 50
        else:
            scores["oi_change"] = 25

        # 4. Sweep detection (0-100)
        if signal.is_sweep:
            scores["sweep_detected"] = 80 + min(signal.sweep_exchanges * 10, 20)
        else:
            scores["sweep_detected"] = 0

        # 5. Multi-day pattern (0-100)
        if historical_flows:
            same_direction = sum(
                1 for f in historical_flows
                if f.direction == signal.direction
            )
            if same_direction >= 5:
                scores["multi_day_pattern"] = 100
            elif same_direction >= 3:
                scores["multi_day_pattern"] = 70
            elif same_direction >= 1:
                scores["multi_day_pattern"] = 40
            else:
                scores["multi_day_pattern"] = 0
        else:
            scores["multi_day_pattern"] = 0

        # 6. Technical alignment (0-100)
        if signal.technical_levels and signal.underlying_price > 0:
            near_support = abs(signal.underlying_price - signal.technical_levels.floor_price) / signal.underlying_price < 0.02
            near_resistance = abs(signal.underlying_price - signal.technical_levels.resistance_price) / signal.underlying_price < 0.02

            if signal.direction == FlowDirection.BULLISH and near_support:
                scores["technical_alignment"] = 80
            elif signal.direction == FlowDirection.BEARISH and near_resistance:
                scores["technical_alignment"] = 80
            else:
                scores["technical_alignment"] = 40
        else:
            scores["technical_alignment"] = 40

        breakdown.scores = scores

        # Calculate bonuses
        bonuses = {}
        if signal.is_sweep:
            bonuses["sweep_bonus"] = self._scoring.SWEEP_BONUS
        if signal.option and signal.underlying_price > 0:
            otm_pct = abs(signal.option.strike - signal.underlying_price) / signal.underlying_price * 100
            if otm_pct <= 5:  # Near ATM
                bonuses["atm_bonus"] = self._scoring.ATM_BONUS
        if signal.consecutive_days >= 3:
            bonuses["multi_day_bonus"] = self._scoring.MULTI_DAY_BONUS

        breakdown.bonuses = bonuses

        # Calculate penalties
        penalties = {}
        if signal.option and signal.option.spread_pct > 10:
            penalties["wide_spread"] = self._scoring.WIDE_SPREAD_PENALTY
        if signal.metrics.open_interest < 500:
            penalties["low_liquidity"] = self._scoring.LOW_LIQUIDITY_PENALTY
        if signal.option and signal.underlying_price > 0:
            otm_pct = abs(signal.option.strike - signal.underlying_price) / signal.underlying_price * 100
            if otm_pct > 20:
                penalties["far_otm"] = self._scoring.FAR_OTM_PENALTY

        breakdown.penalties = penalties

        # Calculate final score
        base_score = self._scoring.calculate_conviction(scores)
        bonus_total = sum(bonuses.values())
        penalty_total = sum(penalties.values())

        final_score = base_score + bonus_total + penalty_total
        final_score = max(0, min(100, final_score))

        breakdown.final_score = final_score

        return final_score, breakdown

    def _determine_positioning(
        self,
        signal: FlowSignal,
        historical_flows: Optional[List[FlowSignal]] = None
    ) -> Tuple[PositioningType, str]:
        """
        Determine institutional positioning type.

        Returns:
            Tuple of (PositioningType, details string)
        """
        if not historical_flows:
            # Single signal - use premium and direction
            if signal.direction == FlowDirection.BULLISH:
                if signal.metrics.premium_paid >= PREMIUM_THRESHOLDS.WHALE:
                    return PositioningType.ACCUMULATION, "Large bullish premium detected"
            elif signal.direction == FlowDirection.BEARISH:
                if signal.metrics.premium_paid >= PREMIUM_THRESHOLDS.WHALE:
                    return PositioningType.DISTRIBUTION, "Large bearish premium detected"

            return PositioningType.SPECULATIVE, "Single trade detected"

        # Analyze multi-day pattern
        bullish_count = sum(1 for f in historical_flows if f.direction == FlowDirection.BULLISH)
        bearish_count = sum(1 for f in historical_flows if f.direction == FlowDirection.BEARISH)

        bullish_premium = sum(f.metrics.premium_paid for f in historical_flows if f.direction == FlowDirection.BULLISH)
        bearish_premium = sum(f.metrics.premium_paid for f in historical_flows if f.direction == FlowDirection.BEARISH)

        days = len(set(f.timestamp.date() for f in historical_flows))

        if bullish_count > bearish_count * 2 and bullish_premium > bearish_premium * 1.5:
            details = f"Last {days} trading days showed accumulation"
            return PositioningType.ACCUMULATION, details

        if bearish_count > bullish_count * 2 and bearish_premium > bullish_premium * 1.5:
            details = f"Last {days} trading days showed distribution"
            return PositioningType.DISTRIBUTION, details

        if abs(bullish_premium - bearish_premium) / max(bullish_premium, bearish_premium, 1) < 0.3:
            return PositioningType.HEDGING, "Balanced call/put activity suggests hedging"

        return PositioningType.UNKNOWN, "Mixed signals detected"

    def _calculate_price_target(self, signal: FlowSignal) -> float:
        """
        Calculate price target based on option position.

        Target = Strike + (Premium / 100) * Multiplier for calls
        Target = Strike - (Premium / 100) * Multiplier for puts
        """
        if not signal.option:
            return signal.underlying_price * 1.1 if signal.direction == FlowDirection.BULLISH else signal.underlying_price * 0.9

        option = signal.option
        premium_per_share = option.mid if option.mid > 0 else option.last

        if option.contract_type == "C":
            # Call: target above strike
            # Breakeven = strike + premium, target = breakeven + buffer
            breakeven = option.strike + premium_per_share
            target = breakeven + (breakeven - option.strike) * 0.5
        else:
            # Put: target below strike
            breakeven = option.strike - premium_per_share
            target = breakeven - (option.strike - breakeven) * 0.5

        return round(target, 2)

    def _generate_tags(self, signal: FlowSignal) -> List[str]:
        """Generate descriptive tags for the signal."""
        tags = []

        # Premium class tag
        premium_class = signal.metrics.premium_class
        if premium_class:
            tags.append(premium_class)

        # Signal type tag
        tags.append(signal.signal_type.value)

        # Direction tag
        tags.append(signal.direction.value)

        # Conviction tag
        tags.append(f"{signal.conviction_level.value}_CONVICTION")

        # Sweep tag
        if signal.is_sweep:
            tags.append("SWEEP")
            if signal.sweep_exchanges >= 3:
                tags.append("MULTI_EXCHANGE")

        # Volume tag
        if signal.metrics.volume_ratio >= 5:
            tags.append("EXTREME_VOLUME")
        elif signal.metrics.volume_ratio >= 3:
            tags.append("HIGH_VOLUME")

        # OI tag
        if signal.metrics.oi_change_pct >= 50:
            tags.append("HIGH_OI_CHANGE")

        # Sector tag
        if signal.sector != "Other":
            tags.append(signal.sector.upper())

        return tags

    def batch_classify(
        self,
        signals: List[FlowSignal],
        technical_levels_map: Dict[str, TechnicalLevels] = None
    ) -> List[FlowSignal]:
        """
        Classify a batch of signals.

        Groups signals by symbol for historical context.

        Args:
            signals: List of signals to classify
            technical_levels_map: Map of symbol -> technical levels

        Returns:
            List of classified signals
        """
        technical_levels_map = technical_levels_map or {}

        # Group signals by symbol
        by_symbol: Dict[str, List[FlowSignal]] = {}
        for signal in signals:
            if signal.symbol not in by_symbol:
                by_symbol[signal.symbol] = []
            by_symbol[signal.symbol].append(signal)

        # Classify each signal with historical context
        classified = []
        for symbol, symbol_signals in by_symbol.items():
            tech_levels = technical_levels_map.get(symbol)

            for i, signal in enumerate(symbol_signals):
                # Use previous signals as historical context
                historical = symbol_signals[:i] if i > 0 else None
                classified_signal = self.classify(signal, tech_levels, historical)
                classified.append(classified_signal)

        return classified
