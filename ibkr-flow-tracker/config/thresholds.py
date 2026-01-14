"""
Institutional Flow Tracker - Detection Thresholds

Defines all thresholds for detecting unusual options activity.
Inspired by professional tools like Unusual Whales, FlowAlgo, and Cheddar Flow.
"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class SignalType(Enum):
    """Types of flow signals detected."""
    INSTITUTIONAL_FLOW = "INSTITUTIONAL_FLOW"
    DARK_POOL = "DARK_POOL"
    SWEEP = "SWEEP"
    BLOCK = "BLOCK"
    UNUSUAL_VOLUME = "UNUSUAL_VOLUME"
    UNUSUAL_OI = "UNUSUAL_OI"
    GOLDEN_SWEEP = "GOLDEN_SWEEP"  # Large sweep near ATM


class FlowDirection(Enum):
    """Direction of the flow signal."""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class ConvictionLevel(Enum):
    """Conviction level of the signal."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PositioningType(Enum):
    """Type of institutional positioning."""
    ACCUMULATION = "Accumulation"
    DISTRIBUTION = "Distribution"
    HEDGING = "Hedging"
    SPECULATIVE = "Speculative"
    UNKNOWN = "Unknown"


# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM THRESHOLDS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PremiumThresholds:
    """Premium-based detection thresholds."""

    # Whale classification by premium paid
    MEGA_WHALE: int = 1_000_000      # > $1M premium
    WHALE: int = 250_000              # > $250K premium
    NOTABLE: int = 50_000             # > $50K premium
    TRACKING_MIN: int = 25_000        # > $25K (minimum to track)

    # Conviction score weights
    PREMIUM_WEIGHT: float = 0.35
    VOLUME_WEIGHT: float = 0.25
    OI_WEIGHT: float = 0.20
    TIMING_WEIGHT: float = 0.20

    def classify_premium(self, premium: float) -> str:
        """Classify trade by premium size."""
        if premium >= self.MEGA_WHALE:
            return "MEGA_WHALE"
        elif premium >= self.WHALE:
            return "WHALE"
        elif premium >= self.NOTABLE:
            return "NOTABLE"
        elif premium >= self.TRACKING_MIN:
            return "TRACKED"
        return "IGNORED"

    def get_conviction_boost(self, premium: float) -> float:
        """Get conviction score boost based on premium."""
        if premium >= self.MEGA_WHALE:
            return 30.0
        elif premium >= self.WHALE:
            return 20.0
        elif premium >= self.NOTABLE:
            return 10.0
        return 0.0


PREMIUM_THRESHOLDS = PremiumThresholds()


# ═══════════════════════════════════════════════════════════════════════════════
# VOLUME THRESHOLDS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class VolumeThresholds:
    """Volume-based detection thresholds."""

    # Unusual activity multipliers
    UNUSUAL_VOLUME: float = 3.0       # 3x average volume
    HIGH_VOLUME: float = 5.0          # 5x average volume
    EXTREME_VOLUME: float = 10.0      # 10x average volume

    # Open Interest changes
    UNUSUAL_OI_INCREASE: float = 1.5  # 50% OI increase
    HIGH_OI_INCREASE: float = 2.0     # 100% OI increase
    EXTREME_OI_INCREASE: float = 3.0  # 200% OI increase

    # Minimum absolute thresholds
    MIN_VOLUME: int = 100
    MIN_OI: int = 500
    MIN_TRADES: int = 10

    def is_unusual_volume(self, current: int, average: int) -> bool:
        """Check if volume is unusual."""
        if average <= 0:
            return current >= self.MIN_VOLUME
        return (current / average) >= self.UNUSUAL_VOLUME

    def get_volume_score(self, current: int, average: int) -> float:
        """Get a 0-100 score for volume unusualness."""
        if average <= 0:
            return 50.0 if current >= self.MIN_VOLUME else 0.0

        ratio = current / average
        if ratio >= self.EXTREME_VOLUME:
            return 100.0
        elif ratio >= self.HIGH_VOLUME:
            return 80.0
        elif ratio >= self.UNUSUAL_VOLUME:
            return 60.0
        elif ratio >= 2.0:
            return 40.0
        return 20.0


VOLUME_THRESHOLDS = VolumeThresholds()


# ═══════════════════════════════════════════════════════════════════════════════
# SWEEP DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SweepThresholds:
    """Sweep detection thresholds."""

    # Time window for considering trades as a sweep
    TIME_WINDOW_MS: int = 1000  # 1 second

    # Minimum exchanges hit for sweep classification
    MIN_EXCHANGES: int = 2

    # Minimum premium for sweep to be notable
    MIN_SWEEP_PREMIUM: int = 50_000

    # Aggressiveness indicators
    AGGRESSIVE_FILL_RATIO: float = 0.9  # 90% of ask lifted

    # Golden sweep (near ATM, large premium)
    GOLDEN_SWEEP_MIN_PREMIUM: int = 100_000
    GOLDEN_SWEEP_MAX_OTM_PCT: float = 5.0  # Within 5% of strike

    def is_golden_sweep(
        self,
        premium: float,
        strike: float,
        underlying: float
    ) -> bool:
        """Check if sweep qualifies as a 'golden sweep'."""
        if premium < self.GOLDEN_SWEEP_MIN_PREMIUM:
            return False

        otm_pct = abs(strike - underlying) / underlying * 100
        return otm_pct <= self.GOLDEN_SWEEP_MAX_OTM_PCT


SWEEP_THRESHOLDS = SweepThresholds()


# ═══════════════════════════════════════════════════════════════════════════════
# ACCUMULATION DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AccumulationThresholds:
    """Multi-day accumulation/distribution detection."""

    # Lookback periods
    SHORT_TERM_DAYS: int = 5
    MEDIUM_TERM_DAYS: int = 10
    LONG_TERM_DAYS: int = 20

    # Accumulation signals
    MIN_CONSECUTIVE_BULLISH_DAYS: int = 3
    MIN_ACCUMULATION_RATIO: float = 2.0  # 2x more calls than puts

    # Distribution signals
    MIN_CONSECUTIVE_BEARISH_DAYS: int = 3
    MIN_DISTRIBUTION_RATIO: float = 2.0  # 2x more puts than calls

    # Premium aggregation
    MIN_AGGREGATE_PREMIUM: int = 500_000  # $500K+ over period

    def classify_positioning(
        self,
        bullish_premium: float,
        bearish_premium: float,
        bullish_days: int,
        bearish_days: int
    ) -> PositioningType:
        """Classify the type of institutional positioning."""
        if bullish_days >= self.MIN_CONSECUTIVE_BULLISH_DAYS:
            if bullish_premium > bearish_premium * self.MIN_ACCUMULATION_RATIO:
                return PositioningType.ACCUMULATION

        if bearish_days >= self.MIN_CONSECUTIVE_BEARISH_DAYS:
            if bearish_premium > bullish_premium * self.MIN_DISTRIBUTION_RATIO:
                return PositioningType.DISTRIBUTION

        # Check for hedging (balanced activity)
        total = bullish_premium + bearish_premium
        if total > 0:
            balance_ratio = min(bullish_premium, bearish_premium) / max(bullish_premium, bearish_premium)
            if balance_ratio > 0.7:  # Within 30% of each other
                return PositioningType.HEDGING

        return PositioningType.UNKNOWN


ACCUMULATION_THRESHOLDS = AccumulationThresholds()


# ═══════════════════════════════════════════════════════════════════════════════
# TECHNICAL LEVELS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TechnicalThresholds:
    """Technical analysis thresholds."""

    # Support/Resistance detection
    LOOKBACK_DAYS: int = 20
    MIN_TOUCHES: int = 2
    LEVEL_TOLERANCE_PCT: float = 1.0  # 1% tolerance

    # Pivot points
    USE_PIVOT_POINTS: bool = True
    PIVOT_TIMEFRAME: str = "daily"

    # Price proximity to levels
    NEAR_SUPPORT_PCT: float = 2.0
    NEAR_RESISTANCE_PCT: float = 2.0

    def is_near_support(self, price: float, support: float) -> bool:
        """Check if price is near support level."""
        return abs(price - support) / support * 100 <= self.NEAR_SUPPORT_PCT

    def is_near_resistance(self, price: float, resistance: float) -> bool:
        """Check if price is near resistance level."""
        return abs(price - resistance) / resistance * 100 <= self.NEAR_RESISTANCE_PCT


TECHNICAL_THRESHOLDS = TechnicalThresholds()


# ═══════════════════════════════════════════════════════════════════════════════
# CONVICTION SCORING
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ConvictionScoring:
    """Conviction score calculation parameters."""

    # Base weights (must sum to 1.0)
    WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        "premium_size": 0.30,
        "volume_unusual": 0.20,
        "oi_change": 0.15,
        "sweep_detected": 0.15,
        "multi_day_pattern": 0.10,
        "technical_alignment": 0.10
    })

    # Score thresholds for conviction levels
    HIGH_CONVICTION_MIN: float = 75.0
    MEDIUM_CONVICTION_MIN: float = 50.0

    # Penalties
    WIDE_SPREAD_PENALTY: float = -10.0  # > 10% spread
    LOW_LIQUIDITY_PENALTY: float = -15.0  # Low OI
    FAR_OTM_PENALTY: float = -5.0  # > 20% OTM

    # Bonuses
    ATM_BONUS: float = 10.0  # Near the money
    SWEEP_BONUS: float = 15.0  # Sweep detected
    MULTI_DAY_BONUS: float = 10.0  # Consistent pattern

    def calculate_conviction(self, scores: Dict[str, float]) -> float:
        """Calculate weighted conviction score."""
        total = 0.0
        for key, weight in self.WEIGHTS.items():
            total += scores.get(key, 0.0) * weight
        return min(100.0, max(0.0, total))

    def get_conviction_level(self, score: float) -> ConvictionLevel:
        """Get conviction level from score."""
        if score >= self.HIGH_CONVICTION_MIN:
            return ConvictionLevel.HIGH
        elif score >= self.MEDIUM_CONVICTION_MIN:
            return ConvictionLevel.MEDIUM
        return ConvictionLevel.LOW


CONVICTION_SCORING = ConvictionScoring()


# ═══════════════════════════════════════════════════════════════════════════════
# SECTOR MAPPINGS
# ═══════════════════════════════════════════════════════════════════════════════

SECTOR_MAPPINGS: Dict[str, List[str]] = {
    "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD", "INTC", "CRM", "ORCL", "ADBE"],
    "Finance": ["JPM", "BAC", "GS", "MS", "WFC", "C", "BLK", "SCHW", "AXP", "V", "MA", "HOOD"],
    "Healthcare": ["JNJ", "UNH", "PFE", "MRK", "ABBV", "LLY", "TMO", "ABT", "BMY", "AMGN"],
    "Consumer": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "TGT", "COST", "WMT", "DIS"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL"],
    "ETFs": ["SPY", "QQQ", "IWM", "DIA", "XLF", "XLE", "XLK", "XLV", "GLD", "SLV", "TLT"],
}


def get_sector(symbol: str) -> str:
    """Get sector for a symbol."""
    for sector, symbols in SECTOR_MAPPINGS.items():
        if symbol in symbols:
            return sector
    return "Other"
