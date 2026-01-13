"""
IBKR Options Trading Assistant - Signal Detection Engine

This module implements the core signal detection logic for options analysis.
It detects 4 types of signals that may indicate trading opportunities:

1. UNUSUAL OPTIONS VOLUME
   - Volume significantly above historical average
   - Indicates potential informed trading activity

2. OPEN INTEREST ACCELERATION
   - Rapid increase in open interest vs previous session
   - Suggests new positions being established

3. IMPLIED VOLATILITY SPIKE
   - Sharp increase in option IV
   - May indicate expected price movement

4. DELTA-ALIGNED MOMENTUM
   - Underlying price movement aligned with option delta
   - Confirms directional conviction

IMPORTANT: These signals are for ANALYSIS only.
They do NOT constitute trading advice.

Author: IBKR Options Assistant
License: MIT
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math

from data_fetcher_ibkr import OptionData
from config import CONFIG


# Configure module logger
logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of signals that can be detected."""
    UNUSUAL_VOLUME = "unusual_volume"
    OI_ACCELERATION = "oi_acceleration"
    IV_SPIKE = "iv_spike"
    DELTA_MOMENTUM = "delta_momentum"


class SignalDirection(Enum):
    """Direction indicated by a signal."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class Signal:
    """
    Represents a detected signal for an option.

    A signal indicates a potentially significant event
    that may warrant attention for trading decisions.
    """
    signal_type: SignalType
    direction: SignalDirection

    # Signal strength (0-100)
    strength: float

    # Descriptive information
    description: str
    details: Dict[str, any] = field(default_factory=dict)

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_strong(self) -> bool:
        """Check if signal is strong (>= 70 strength)."""
        return self.strength >= 70.0

    @property
    def is_moderate(self) -> bool:
        """Check if signal is moderate (50-70 strength)."""
        return 50.0 <= self.strength < 70.0


@dataclass
class OptionSignals:
    """
    Collection of all signals for a single option.

    Groups all detected signals for analysis.
    """
    option: OptionData
    signals: List[Signal] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def signal_count(self) -> int:
        """Number of active signals."""
        return len(self.signals)

    @property
    def has_signals(self) -> bool:
        """Check if any signals are present."""
        return len(self.signals) > 0

    @property
    def total_strength(self) -> float:
        """Sum of all signal strengths."""
        return sum(s.strength for s in self.signals)

    @property
    def avg_strength(self) -> float:
        """Average signal strength."""
        if not self.signals:
            return 0.0
        return self.total_strength / len(self.signals)

    @property
    def dominant_direction(self) -> SignalDirection:
        """
        Determine the dominant direction from all signals.

        Returns the direction with highest weighted strength.
        """
        if not self.signals:
            return SignalDirection.NEUTRAL

        bullish_strength = sum(
            s.strength for s in self.signals
            if s.direction == SignalDirection.BULLISH
        )
        bearish_strength = sum(
            s.strength for s in self.signals
            if s.direction == SignalDirection.BEARISH
        )

        if bullish_strength > bearish_strength:
            return SignalDirection.BULLISH
        elif bearish_strength > bullish_strength:
            return SignalDirection.BEARISH
        else:
            return SignalDirection.NEUTRAL

    def get_signals_by_type(self, signal_type: SignalType) -> List[Signal]:
        """Get all signals of a specific type."""
        return [s for s in self.signals if s.signal_type == signal_type]

    def has_signal_type(self, signal_type: SignalType) -> bool:
        """Check if a specific signal type is present."""
        return any(s.signal_type == signal_type for s in self.signals)


class SignalEngine:
    """
    Options signal detection engine.

    This engine analyzes options data and detects signals
    that may indicate trading opportunities.

    Signal Types:
    1. Unusual Volume - Volume >= 3x average
    2. OI Acceleration - OI increase >= 20% from previous
    3. IV Spike - IV increase >= 15% from previous
    4. Delta Momentum - Price movement aligned with delta

    Usage:
        engine = SignalEngine()
        signals = engine.analyze(option_data)
        all_signals = engine.analyze_chain(options_list)
    """

    def __init__(self):
        """Initialize the signal engine."""
        self.config = CONFIG.signals

        # Signal detection thresholds
        self.volume_threshold = self.config.volume_multiplier_threshold
        self.oi_threshold = self.config.oi_acceleration_threshold
        self.iv_threshold = self.config.iv_spike_threshold
        self.delta_correlation = self.config.delta_momentum_correlation

        logger.info(
            f"SignalEngine initialized | "
            f"Vol: {self.volume_threshold}x | "
            f"OI: {self.oi_threshold}% | "
            f"IV: {self.iv_threshold}% | "
            f"Delta: {self.delta_correlation}"
        )

    def analyze(self, option: OptionData) -> OptionSignals:
        """
        Analyze a single option for all signal types.

        Args:
            option: Option data to analyze

        Returns:
            OptionSignals containing all detected signals
        """
        signals = OptionSignals(option=option)

        # Check each signal type
        volume_signal = self._check_unusual_volume(option)
        if volume_signal:
            signals.signals.append(volume_signal)

        oi_signal = self._check_oi_acceleration(option)
        if oi_signal:
            signals.signals.append(oi_signal)

        iv_signal = self._check_iv_spike(option)
        if iv_signal:
            signals.signals.append(iv_signal)

        delta_signal = self._check_delta_momentum(option)
        if delta_signal:
            signals.signals.append(delta_signal)

        return signals

    def analyze_chain(
        self,
        options: List[OptionData],
        min_signals: int = 1
    ) -> List[OptionSignals]:
        """
        Analyze a complete options chain for signals.

        Args:
            options: List of options to analyze
            min_signals: Minimum number of signals to include in results

        Returns:
            List of OptionSignals for options with signals
        """
        results = []

        for option in options:
            option_signals = self.analyze(option)

            if option_signals.signal_count >= min_signals:
                results.append(option_signals)

        # Sort by total signal strength (descending)
        results.sort(key=lambda x: x.total_strength, reverse=True)

        logger.info(
            f"Analyzed {len(options)} options, "
            f"found {len(results)} with signals"
        )

        return results

    def _check_unusual_volume(self, option: OptionData) -> Optional[Signal]:
        """
        Check for unusual options volume signal.

        Signal triggers when:
        - Current volume >= threshold * average volume
        - Minimum absolute volume met

        The signal strength is proportional to how much
        volume exceeds the threshold.

        Args:
            option: Option to check

        Returns:
            Signal if detected, None otherwise
        """
        if option.avg_volume <= 0:
            return None

        volume_ratio = option.volume_ratio

        if volume_ratio < self.volume_threshold:
            return None

        # Calculate strength based on how much volume exceeds threshold
        # Strength scales from 50 (at threshold) to 100 (at 2x threshold)
        excess_ratio = (volume_ratio - self.volume_threshold) / self.volume_threshold
        strength = min(100.0, 50.0 + (excess_ratio * 50.0))

        # Determine direction based on option type and price action
        if option.option_type == "CALL":
            direction = SignalDirection.BULLISH
        else:
            direction = SignalDirection.BEARISH

        return Signal(
            signal_type=SignalType.UNUSUAL_VOLUME,
            direction=direction,
            strength=strength,
            description=f"Volume {volume_ratio:.1f}x average",
            details={
                'volume': option.volume,
                'avg_volume': option.avg_volume,
                'ratio': volume_ratio,
                'threshold': self.volume_threshold
            }
        )

    def _check_oi_acceleration(self, option: OptionData) -> Optional[Signal]:
        """
        Check for open interest acceleration signal.

        Signal triggers when:
        - OI has increased by >= threshold % from previous session
        - Indicates new positions being established

        Args:
            option: Option to check

        Returns:
            Signal if detected, None otherwise
        """
        if option.prev_open_interest <= 0:
            return None

        oi_change = option.oi_change_pct

        if oi_change < self.oi_threshold:
            return None

        # Calculate strength
        # Strength scales from 50 (at threshold) to 100 (at 2x threshold)
        excess = (oi_change - self.oi_threshold) / self.oi_threshold
        strength = min(100.0, 50.0 + (excess * 50.0))

        # Direction based on option type
        if option.option_type == "CALL":
            direction = SignalDirection.BULLISH
        else:
            direction = SignalDirection.BEARISH

        return Signal(
            signal_type=SignalType.OI_ACCELERATION,
            direction=direction,
            strength=strength,
            description=f"OI increased {oi_change:.1f}%",
            details={
                'current_oi': option.open_interest,
                'prev_oi': option.prev_open_interest,
                'change_pct': oi_change,
                'threshold': self.oi_threshold
            }
        )

    def _check_iv_spike(self, option: OptionData) -> Optional[Signal]:
        """
        Check for implied volatility spike signal.

        Signal triggers when:
        - IV has increased by >= threshold % from previous reading
        - May indicate expected price movement or event

        High IV can indicate:
        - Expected news/earnings
        - Unusual options activity
        - Market uncertainty

        Args:
            option: Option to check

        Returns:
            Signal if detected, None otherwise
        """
        if option.prev_implied_volatility <= 0:
            return None

        iv_change = option.iv_change_pct

        # We only signal on IV increases (not decreases)
        if iv_change < self.iv_threshold:
            return None

        # Calculate strength
        excess = (iv_change - self.iv_threshold) / self.iv_threshold
        strength = min(100.0, 50.0 + (excess * 50.0))

        # IV spike is typically neutral - could go either direction
        # But extreme IV often precedes movement
        direction = SignalDirection.NEUTRAL

        return Signal(
            signal_type=SignalType.IV_SPIKE,
            direction=direction,
            strength=strength,
            description=f"IV spiked {iv_change:.1f}%",
            details={
                'current_iv': option.implied_volatility,
                'prev_iv': option.prev_implied_volatility,
                'change_pct': iv_change,
                'threshold': self.iv_threshold
            }
        )

    def _check_delta_momentum(self, option: OptionData) -> Optional[Signal]:
        """
        Check for delta-aligned momentum signal.

        Signal triggers when:
        - Underlying price movement aligns with option delta
        - For calls: positive delta + positive underlying change
        - For puts: negative delta + negative underlying change

        This indicates the option is moving "in sync" with
        the underlying in a way that benefits holders.

        Args:
            option: Option to check

        Returns:
            Signal if detected, None otherwise
        """
        if abs(option.delta) < 0.1 or abs(option.underlying_change) < 0.5:
            # Too little delta or price movement to matter
            return None

        # Check alignment
        delta_sign = 1 if option.delta > 0 else -1
        price_sign = 1 if option.underlying_change > 0 else -1

        is_aligned = delta_sign == price_sign

        if not is_aligned:
            return None

        # Calculate strength based on:
        # 1. Magnitude of underlying move
        # 2. Delta of the option (higher delta = more directional)
        move_factor = min(abs(option.underlying_change) / 2.0, 1.0)  # Cap at 2% move
        delta_factor = abs(option.delta)

        strength = (move_factor * 50.0) + (delta_factor * 50.0)
        strength = min(100.0, strength)

        # Direction based on movement
        if option.underlying_change > 0:
            direction = SignalDirection.BULLISH
        else:
            direction = SignalDirection.BEARISH

        return Signal(
            signal_type=SignalType.DELTA_MOMENTUM,
            direction=direction,
            strength=strength,
            description=f"Delta ({option.delta:.2f}) aligned with {option.underlying_change:+.1f}% move",
            details={
                'delta': option.delta,
                'underlying_change': option.underlying_change,
                'option_type': option.option_type,
                'aligned': True
            }
        )

    def get_signal_summary(
        self,
        signals_list: List[OptionSignals]
    ) -> Dict[str, any]:
        """
        Generate summary statistics for a list of option signals.

        Args:
            signals_list: List of OptionSignals

        Returns:
            Dictionary with summary statistics
        """
        if not signals_list:
            return {
                'total_options': 0,
                'signals_by_type': {},
                'direction_breakdown': {},
                'avg_strength': 0.0
            }

        # Count signals by type
        signals_by_type = {t.value: 0 for t in SignalType}
        for os in signals_list:
            for signal in os.signals:
                signals_by_type[signal.signal_type.value] += 1

        # Direction breakdown
        direction_breakdown = {d.value: 0 for d in SignalDirection}
        for os in signals_list:
            direction_breakdown[os.dominant_direction.value] += 1

        # Average strength
        total_strength = sum(os.avg_strength for os in signals_list)
        avg_strength = total_strength / len(signals_list)

        return {
            'total_options': len(signals_list),
            'signals_by_type': signals_by_type,
            'direction_breakdown': direction_breakdown,
            'avg_strength': avg_strength
        }

    def get_strongest_signals(
        self,
        signals_list: List[OptionSignals],
        count: int = 10
    ) -> List[OptionSignals]:
        """
        Get options with strongest signal combinations.

        Args:
            signals_list: List of OptionSignals
            count: Number of top results

        Returns:
            Top N options by total signal strength
        """
        sorted_signals = sorted(
            signals_list,
            key=lambda x: x.total_strength,
            reverse=True
        )
        return sorted_signals[:count]

    def filter_by_direction(
        self,
        signals_list: List[OptionSignals],
        direction: SignalDirection
    ) -> List[OptionSignals]:
        """
        Filter signals by dominant direction.

        Args:
            signals_list: List of OptionSignals
            direction: Direction to filter by

        Returns:
            Filtered list
        """
        return [
            os for os in signals_list
            if os.dominant_direction == direction
        ]


# ══════════════════════════════════════════════════════════════════════════════
# SIGNAL INTERPRETATION GUIDE
# ══════════════════════════════════════════════════════════════════════════════
"""
SIGNAL INTERPRETATION (for human traders):

1. UNUSUAL VOLUME
   - What it means: More contracts trading than normal
   - Possible causes: Informed trading, hedging activity, news anticipation
   - Caution: High volume alone doesn't indicate direction

2. OI ACCELERATION
   - What it means: New positions being established
   - Possible causes: Institutional positioning, anticipation of move
   - Caution: Could be hedges against existing positions

3. IV SPIKE
   - What it means: Market expects larger price movement
   - Possible causes: Earnings, FDA decisions, legal rulings
   - Caution: High IV = expensive options, may be priced in

4. DELTA MOMENTUM
   - What it means: Underlying moving in direction favorable to option
   - Possible causes: Trend continuation, momentum
   - Caution: Trends can reverse quickly

IMPORTANT:
- Signals are INFORMATIONAL only
- Multiple aligned signals increase conviction
- Always consider broader market context
- Never trade based on signals alone
"""
