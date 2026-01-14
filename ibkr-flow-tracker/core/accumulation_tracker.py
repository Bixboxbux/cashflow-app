"""
Institutional Flow Tracker - Accumulation Tracker Module

Tracks institutional activity over multiple days to identify:
- Accumulation patterns (sustained buying)
- Distribution patterns (sustained selling)
- Hedging activity (balanced positions)

This provides crucial context for flow signals.
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

from config import ACCUMULATION_THRESHOLDS, get_sector
from config.thresholds import FlowDirection, PositioningType
from models import FlowSignal


logger = logging.getLogger(__name__)


@dataclass
class DailyFlow:
    """Aggregated flow data for a single day."""
    date: date
    symbol: str

    # Bullish activity
    bullish_premium: float = 0.0
    bullish_count: int = 0
    bullish_contracts: int = 0

    # Bearish activity
    bearish_premium: float = 0.0
    bearish_count: int = 0
    bearish_contracts: int = 0

    # Neutral activity
    neutral_premium: float = 0.0
    neutral_count: int = 0

    # Sweep activity
    sweep_count: int = 0
    sweep_premium: float = 0.0

    @property
    def total_premium(self) -> float:
        return self.bullish_premium + self.bearish_premium + self.neutral_premium

    @property
    def total_count(self) -> int:
        return self.bullish_count + self.bearish_count + self.neutral_count

    @property
    def net_direction(self) -> FlowDirection:
        """Net direction based on premium."""
        if self.bullish_premium > self.bearish_premium * 1.5:
            return FlowDirection.BULLISH
        elif self.bearish_premium > self.bullish_premium * 1.5:
            return FlowDirection.BEARISH
        return FlowDirection.NEUTRAL

    @property
    def premium_ratio(self) -> float:
        """Ratio of bullish to bearish premium."""
        if self.bearish_premium == 0:
            return float('inf') if self.bullish_premium > 0 else 1.0
        return self.bullish_premium / self.bearish_premium

    def to_dict(self) -> Dict:
        return {
            "date": self.date.isoformat(),
            "symbol": self.symbol,
            "bullish_premium": round(self.bullish_premium, 2),
            "bearish_premium": round(self.bearish_premium, 2),
            "total_premium": round(self.total_premium, 2),
            "bullish_count": self.bullish_count,
            "bearish_count": self.bearish_count,
            "net_direction": self.net_direction.value,
            "premium_ratio": round(self.premium_ratio, 2) if self.premium_ratio != float('inf') else "inf",
        }


@dataclass
class AccumulationPattern:
    """Represents a detected accumulation/distribution pattern."""
    symbol: str
    pattern_type: PositioningType
    start_date: date
    end_date: date

    # Aggregated metrics
    total_premium: float = 0.0
    total_signals: int = 0
    consecutive_days: int = 0

    # Direction breakdown
    bullish_days: int = 0
    bearish_days: int = 0
    neutral_days: int = 0

    # Premium breakdown
    bullish_premium: float = 0.0
    bearish_premium: float = 0.0

    # Confidence in pattern
    confidence: float = 0.0

    # Details
    description: str = ""

    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "pattern_type": self.pattern_type.value,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_premium": round(self.total_premium, 2),
            "total_signals": self.total_signals,
            "consecutive_days": self.consecutive_days,
            "bullish_days": self.bullish_days,
            "bearish_days": self.bearish_days,
            "bullish_premium": round(self.bullish_premium, 2),
            "bearish_premium": round(self.bearish_premium, 2),
            "confidence": round(self.confidence, 1),
            "description": self.description,
        }


class AccumulationTracker:
    """
    Tracks multi-day institutional activity patterns.

    Features:
    - Daily flow aggregation by symbol
    - Pattern detection over configurable windows
    - Consecutive day tracking
    - Historical lookback analysis

    Usage:
        tracker = AccumulationTracker()
        tracker.add_signal(signal)
        pattern = tracker.analyze_symbol("AAPL")
    """

    def __init__(self, lookback_days: int = None):
        """
        Initialize the tracker.

        Args:
            lookback_days: Number of days to track (default from config)
        """
        self.lookback_days = lookback_days or ACCUMULATION_THRESHOLDS.SHORT_TERM_DAYS

        # Daily flows by symbol
        self._daily_flows: Dict[str, Dict[date, DailyFlow]] = defaultdict(dict)

        # Raw signals for detailed analysis
        self._signals: Dict[str, List[FlowSignal]] = defaultdict(list)

        # Detected patterns
        self._patterns: Dict[str, AccumulationPattern] = {}

        logger.info(f"AccumulationTracker initialized (lookback: {self.lookback_days} days)")

    def add_signal(self, signal: FlowSignal):
        """
        Add a signal to the tracker.

        Args:
            signal: Flow signal to track
        """
        symbol = signal.symbol
        signal_date = signal.timestamp.date()

        # Store raw signal
        self._signals[symbol].append(signal)

        # Update daily aggregation
        if signal_date not in self._daily_flows[symbol]:
            self._daily_flows[symbol][signal_date] = DailyFlow(
                date=signal_date,
                symbol=symbol
            )

        daily = self._daily_flows[symbol][signal_date]

        # Aggregate based on direction
        if signal.direction == FlowDirection.BULLISH:
            daily.bullish_premium += signal.metrics.premium_paid
            daily.bullish_count += 1
            daily.bullish_contracts += signal.metrics.contracts
        elif signal.direction == FlowDirection.BEARISH:
            daily.bearish_premium += signal.metrics.premium_paid
            daily.bearish_count += 1
            daily.bearish_contracts += signal.metrics.contracts
        else:
            daily.neutral_premium += signal.metrics.premium_paid
            daily.neutral_count += 1

        if signal.is_sweep:
            daily.sweep_count += 1
            daily.sweep_premium += signal.metrics.premium_paid

        # Clean old data
        self._clean_old_data(symbol)

    def _clean_old_data(self, symbol: str):
        """Remove data older than lookback period."""
        cutoff = date.today() - timedelta(days=self.lookback_days + 5)

        # Clean daily flows
        old_dates = [d for d in self._daily_flows[symbol].keys() if d < cutoff]
        for d in old_dates:
            del self._daily_flows[symbol][d]

        # Clean signals
        self._signals[symbol] = [
            s for s in self._signals[symbol]
            if s.timestamp.date() >= cutoff
        ]

    def analyze_symbol(self, symbol: str) -> Optional[AccumulationPattern]:
        """
        Analyze flow patterns for a symbol.

        Args:
            symbol: Symbol to analyze

        Returns:
            AccumulationPattern if detected, None otherwise
        """
        if symbol not in self._daily_flows:
            return None

        daily_flows = self._daily_flows[symbol]
        if not daily_flows:
            return None

        # Get recent days
        today = date.today()
        recent_dates = sorted([
            d for d in daily_flows.keys()
            if d >= today - timedelta(days=self.lookback_days)
        ])

        if not recent_dates:
            return None

        # Aggregate metrics
        bullish_days = 0
        bearish_days = 0
        neutral_days = 0
        bullish_premium = 0.0
        bearish_premium = 0.0
        total_signals = 0

        consecutive_bullish = 0
        consecutive_bearish = 0
        max_consecutive_bullish = 0
        max_consecutive_bearish = 0

        for d in recent_dates:
            daily = daily_flows[d]
            total_signals += daily.total_count

            direction = daily.net_direction
            if direction == FlowDirection.BULLISH:
                bullish_days += 1
                consecutive_bullish += 1
                consecutive_bearish = 0
                max_consecutive_bullish = max(max_consecutive_bullish, consecutive_bullish)
            elif direction == FlowDirection.BEARISH:
                bearish_days += 1
                consecutive_bearish += 1
                consecutive_bullish = 0
                max_consecutive_bearish = max(max_consecutive_bearish, consecutive_bearish)
            else:
                neutral_days += 1
                consecutive_bullish = 0
                consecutive_bearish = 0

            bullish_premium += daily.bullish_premium
            bearish_premium += daily.bearish_premium

        # Determine pattern type
        pattern_type = PositioningType.UNKNOWN
        description = ""
        confidence = 0.0

        total_premium = bullish_premium + bearish_premium

        if max_consecutive_bullish >= ACCUMULATION_THRESHOLDS.MIN_CONSECUTIVE_BULLISH_DAYS:
            if bullish_premium >= bearish_premium * ACCUMULATION_THRESHOLDS.MIN_ACCUMULATION_RATIO:
                pattern_type = PositioningType.ACCUMULATION
                description = f"Last {max_consecutive_bullish} trading days showed accumulation"
                confidence = min(100, 50 + max_consecutive_bullish * 10 + (bullish_premium / total_premium * 30 if total_premium > 0 else 0))

        elif max_consecutive_bearish >= ACCUMULATION_THRESHOLDS.MIN_CONSECUTIVE_BEARISH_DAYS:
            if bearish_premium >= bullish_premium * ACCUMULATION_THRESHOLDS.MIN_DISTRIBUTION_RATIO:
                pattern_type = PositioningType.DISTRIBUTION
                description = f"Last {max_consecutive_bearish} trading days showed distribution"
                confidence = min(100, 50 + max_consecutive_bearish * 10 + (bearish_premium / total_premium * 30 if total_premium > 0 else 0))

        elif total_premium > 0:
            balance = min(bullish_premium, bearish_premium) / max(bullish_premium, bearish_premium)
            if balance > 0.7:
                pattern_type = PositioningType.HEDGING
                description = "Balanced call/put activity suggests hedging"
                confidence = 50 + balance * 30

        if pattern_type == PositioningType.UNKNOWN:
            return None

        pattern = AccumulationPattern(
            symbol=symbol,
            pattern_type=pattern_type,
            start_date=recent_dates[0],
            end_date=recent_dates[-1],
            total_premium=total_premium,
            total_signals=total_signals,
            consecutive_days=max(max_consecutive_bullish, max_consecutive_bearish),
            bullish_days=bullish_days,
            bearish_days=bearish_days,
            neutral_days=neutral_days,
            bullish_premium=bullish_premium,
            bearish_premium=bearish_premium,
            confidence=confidence,
            description=description,
        )

        self._patterns[symbol] = pattern
        return pattern

    def get_daily_flows(self, symbol: str, days: int = None) -> List[DailyFlow]:
        """
        Get daily flow data for a symbol.

        Args:
            symbol: Symbol to query
            days: Number of days (default: lookback_days)

        Returns:
            List of DailyFlow objects, sorted by date
        """
        days = days or self.lookback_days

        if symbol not in self._daily_flows:
            return []

        cutoff = date.today() - timedelta(days=days)
        flows = [
            f for d, f in self._daily_flows[symbol].items()
            if d >= cutoff
        ]

        return sorted(flows, key=lambda f: f.date)

    def get_signals(self, symbol: str, days: int = None) -> List[FlowSignal]:
        """
        Get raw signals for a symbol.

        Args:
            symbol: Symbol to query
            days: Number of days (default: lookback_days)

        Returns:
            List of FlowSignal objects
        """
        days = days or self.lookback_days

        if symbol not in self._signals:
            return []

        cutoff = date.today() - timedelta(days=days)
        signals = [
            s for s in self._signals[symbol]
            if s.timestamp.date() >= cutoff
        ]

        return sorted(signals, key=lambda s: s.timestamp, reverse=True)

    def get_pattern(self, symbol: str) -> Optional[AccumulationPattern]:
        """Get cached pattern for a symbol."""
        return self._patterns.get(symbol)

    def get_all_patterns(self) -> Dict[str, AccumulationPattern]:
        """Get all detected patterns."""
        return self._patterns.copy()

    def get_summary(self) -> Dict:
        """Get summary of all tracked symbols."""
        summary = {
            "symbols_tracked": len(self._daily_flows),
            "patterns_detected": len(self._patterns),
            "by_pattern_type": defaultdict(list),
            "total_signals": sum(len(s) for s in self._signals.values()),
        }

        for symbol, pattern in self._patterns.items():
            summary["by_pattern_type"][pattern.pattern_type.value].append(symbol)

        return dict(summary)
