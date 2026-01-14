"""
Institutional Flow Tracker - Technical Levels Calculator

Calculates support/resistance levels and pivot points for symbols.
Used to provide technical context for flow signals.

Methods:
- Support/Resistance from price action
- Pivot Points (daily/weekly)
- Volume-weighted levels
"""

import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from statistics import mean, stdev

from config import TECHNICAL_THRESHOLDS
from models import TechnicalLevels, OHLCV


logger = logging.getLogger(__name__)


class TechnicalLevelsCalculator:
    """
    Calculates technical support and resistance levels.

    Features:
    - Support/Resistance detection from price pivots
    - Pivot point calculations (standard, Fibonacci)
    - Volume-weighted level importance
    - Multi-timeframe analysis

    Usage:
        calc = TechnicalLevelsCalculator()
        levels = calc.calculate(bars)
    """

    def __init__(self):
        """Initialize the calculator."""
        self.config = TECHNICAL_THRESHOLDS
        self._cache: Dict[str, TechnicalLevels] = {}

        logger.info("TechnicalLevelsCalculator initialized")

    def calculate(
        self,
        bars: List[OHLCV],
        symbol: str = "",
        lookback: int = None
    ) -> TechnicalLevels:
        """
        Calculate technical levels from price data.

        Args:
            bars: OHLCV bars (most recent last)
            symbol: Symbol for caching
            lookback: Number of bars to analyze

        Returns:
            TechnicalLevels object
        """
        lookback = lookback or self.config.LOOKBACK_DAYS

        if not bars or len(bars) < 5:
            return TechnicalLevels()

        # Use recent bars
        recent_bars = bars[-lookback:] if len(bars) > lookback else bars

        # Calculate pivot points from most recent bar
        pivot_levels = self._calculate_pivot_points(recent_bars[-1])

        # Find support and resistance from price action
        support, resistance = self._find_sr_levels(recent_bars)

        # Combine and prioritize levels
        floor_price = support[0] if support else pivot_levels["s1"]
        resistance_price = resistance[0] if resistance else pivot_levels["r1"]

        levels = TechnicalLevels(
            floor_price=round(floor_price, 2),
            resistance_price=round(resistance_price, 2),
            pivot_point=round(pivot_levels["pivot"], 2),
            support_1=round(pivot_levels["s1"], 2),
            support_2=round(pivot_levels["s2"], 2),
            resistance_1=round(pivot_levels["r1"], 2),
            resistance_2=round(pivot_levels["r2"], 2),
            calculated_at=datetime.now(),
            lookback_days=len(recent_bars),
        )

        # Cache result
        if symbol:
            self._cache[symbol] = levels

        return levels

    def _calculate_pivot_points(self, bar: OHLCV) -> Dict[str, float]:
        """
        Calculate standard pivot points.

        Standard Pivot Point Formula:
        - Pivot = (High + Low + Close) / 3
        - R1 = 2 * Pivot - Low
        - R2 = Pivot + (High - Low)
        - S1 = 2 * Pivot - High
        - S2 = Pivot - (High - Low)
        """
        high = bar.high
        low = bar.low
        close = bar.close

        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)

        return {
            "pivot": pivot,
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "s1": s1,
            "s2": s2,
            "s3": s3,
        }

    def _find_sr_levels(
        self,
        bars: List[OHLCV],
        tolerance_pct: float = None
    ) -> Tuple[List[float], List[float]]:
        """
        Find support and resistance levels from price action.

        Identifies levels where price has:
        - Bounced (support) or been rejected (resistance)
        - Multiple touches confirm the level

        Returns:
            Tuple of (support_levels, resistance_levels)
        """
        tolerance_pct = tolerance_pct or self.config.LEVEL_TOLERANCE_PCT

        if len(bars) < 5:
            return [], []

        # Find local minima and maxima
        lows = []
        highs = []

        for i in range(2, len(bars) - 2):
            # Local minimum
            if (bars[i].low <= bars[i-1].low and
                bars[i].low <= bars[i-2].low and
                bars[i].low <= bars[i+1].low and
                bars[i].low <= bars[i+2].low):
                lows.append(bars[i].low)

            # Local maximum
            if (bars[i].high >= bars[i-1].high and
                bars[i].high >= bars[i-2].high and
                bars[i].high >= bars[i+1].high and
                bars[i].high >= bars[i+2].high):
                highs.append(bars[i].high)

        # Cluster nearby levels
        support_levels = self._cluster_levels(lows, tolerance_pct)
        resistance_levels = self._cluster_levels(highs, tolerance_pct)

        # Sort by strength (number of touches)
        return (
            sorted(support_levels, reverse=True),
            sorted(resistance_levels)
        )

    def _cluster_levels(
        self,
        prices: List[float],
        tolerance_pct: float
    ) -> List[float]:
        """
        Cluster nearby price levels.

        Groups prices within tolerance and returns average of each cluster.
        """
        if not prices:
            return []

        prices = sorted(prices)
        clusters = []
        current_cluster = [prices[0]]

        for price in prices[1:]:
            avg_cluster = mean(current_cluster)
            tolerance = avg_cluster * (tolerance_pct / 100)

            if abs(price - avg_cluster) <= tolerance:
                current_cluster.append(price)
            else:
                if len(current_cluster) >= self.config.MIN_TOUCHES:
                    clusters.append(mean(current_cluster))
                current_cluster = [price]

        # Don't forget the last cluster
        if len(current_cluster) >= self.config.MIN_TOUCHES:
            clusters.append(mean(current_cluster))

        return clusters

    def get_cached(self, symbol: str) -> Optional[TechnicalLevels]:
        """Get cached levels for a symbol."""
        return self._cache.get(symbol)

    def calculate_from_price(
        self,
        current_price: float,
        high_52w: float = None,
        low_52w: float = None
    ) -> TechnicalLevels:
        """
        Estimate technical levels from current price.

        Used when historical data is not available.

        Args:
            current_price: Current stock price
            high_52w: 52-week high (optional)
            low_52w: 52-week low (optional)

        Returns:
            Estimated TechnicalLevels
        """
        # Estimate based on percentage from current
        if high_52w and low_52w:
            range_52w = high_52w - low_52w
            resistance = current_price + range_52w * 0.1
            support = current_price - range_52w * 0.1
        else:
            resistance = current_price * 1.05  # 5% above
            support = current_price * 0.95     # 5% below

        pivot = current_price

        return TechnicalLevels(
            floor_price=round(support, 2),
            resistance_price=round(resistance, 2),
            pivot_point=round(pivot, 2),
            support_1=round(support * 0.98, 2),
            support_2=round(support * 0.95, 2),
            resistance_1=round(resistance * 1.02, 2),
            resistance_2=round(resistance * 1.05, 2),
        )

    def is_near_support(self, price: float, levels: TechnicalLevels) -> bool:
        """Check if price is near support."""
        return self.config.is_near_support(price, levels.floor_price)

    def is_near_resistance(self, price: float, levels: TechnicalLevels) -> bool:
        """Check if price is near resistance."""
        return self.config.is_near_resistance(price, levels.resistance_price)

    def get_nearest_level(
        self,
        price: float,
        levels: TechnicalLevels
    ) -> Tuple[str, float, float]:
        """
        Find the nearest technical level.

        Returns:
            Tuple of (level_type, level_price, distance_pct)
        """
        all_levels = [
            ("floor", levels.floor_price),
            ("resistance", levels.resistance_price),
            ("pivot", levels.pivot_point),
            ("s1", levels.support_1),
            ("s2", levels.support_2),
            ("r1", levels.resistance_1),
            ("r2", levels.resistance_2),
        ]

        nearest = None
        min_distance = float('inf')

        for level_type, level_price in all_levels:
            if level_price <= 0:
                continue
            distance = abs(price - level_price)
            if distance < min_distance:
                min_distance = distance
                nearest = (level_type, level_price, (distance / price) * 100)

        return nearest if nearest else ("none", 0, 0)
