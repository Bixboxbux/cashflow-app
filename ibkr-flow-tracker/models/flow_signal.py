"""
Institutional Flow Tracker - Flow Signal Data Model

Core data structure for representing institutional flow signals.
This is the primary output of the detection and classification system.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from enum import Enum
import uuid
import json

from config.thresholds import (
    SignalType,
    FlowDirection,
    ConvictionLevel,
    PositioningType,
)


@dataclass
class TechnicalLevels:
    """Technical support and resistance levels."""
    floor_price: float = 0.0
    resistance_price: float = 0.0
    pivot_point: float = 0.0

    # Additional levels
    support_1: float = 0.0
    support_2: float = 0.0
    resistance_1: float = 0.0
    resistance_2: float = 0.0

    # Metadata
    calculated_at: datetime = field(default_factory=datetime.now)
    lookback_days: int = 20

    def to_dict(self) -> Dict[str, Any]:
        return {
            "floor": round(self.floor_price, 2),
            "resistance": round(self.resistance_price, 2),
            "pivot": round(self.pivot_point, 2),
            "support_1": round(self.support_1, 2),
            "support_2": round(self.support_2, 2),
            "resistance_1": round(self.resistance_1, 2),
            "resistance_2": round(self.resistance_2, 2),
        }


@dataclass
class OptionDetails:
    """Details of the option contract."""
    contract_type: str  # "CALL" or "PUT"
    strike: float
    expiration: date
    days_to_expiry: int

    # Pricing
    bid: float = 0.0
    ask: float = 0.0
    last: float = 0.0
    mid: float = 0.0

    # Greeks
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    implied_volatility: float = 0.0

    @property
    def spread(self) -> float:
        """Bid-ask spread."""
        return self.ask - self.bid

    @property
    def spread_pct(self) -> float:
        """Spread as percentage of mid."""
        if self.mid > 0:
            return (self.spread / self.mid) * 100
        return 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.contract_type,
            "strike": self.strike,
            "expiration": self.expiration.isoformat(),
            "dte": self.days_to_expiry,
            "bid": round(self.bid, 2),
            "ask": round(self.ask, 2),
            "last": round(self.last, 2),
            "mid": round(self.mid, 2),
            "delta": round(self.delta, 3),
            "iv": round(self.implied_volatility, 1),
            "spread_pct": round(self.spread_pct, 2),
        }


@dataclass
class FlowMetrics:
    """Quantitative metrics for the flow signal."""
    premium_paid: float  # Total premium in USD
    contracts: int
    volume: int
    avg_volume: int
    open_interest: int
    prev_open_interest: int

    # Calculated ratios
    volume_ratio: float = 0.0
    oi_change_pct: float = 0.0

    # Classification
    premium_class: str = ""  # MEGA_WHALE, WHALE, NOTABLE, etc.

    def __post_init__(self):
        """Calculate derived metrics."""
        if self.avg_volume > 0:
            self.volume_ratio = self.volume / self.avg_volume
        if self.prev_open_interest > 0:
            self.oi_change_pct = ((self.open_interest - self.prev_open_interest) /
                                  self.prev_open_interest) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "premium": round(self.premium_paid, 2),
            "premium_formatted": self._format_premium(),
            "contracts": self.contracts,
            "volume": self.volume,
            "avg_volume": self.avg_volume,
            "volume_ratio": round(self.volume_ratio, 1),
            "open_interest": self.open_interest,
            "oi_change_pct": round(self.oi_change_pct, 1),
            "premium_class": self.premium_class,
        }

    def _format_premium(self) -> str:
        """Format premium for display."""
        if self.premium_paid >= 1_000_000:
            return f"${self.premium_paid / 1_000_000:.1f}M"
        elif self.premium_paid >= 1_000:
            return f"${self.premium_paid / 1_000:.0f}K"
        return f"${self.premium_paid:.0f}"


@dataclass
class ConvictionBreakdown:
    """Detailed breakdown of conviction score calculation."""
    scores: Dict[str, float] = field(default_factory=dict)
    bonuses: Dict[str, float] = field(default_factory=dict)
    penalties: Dict[str, float] = field(default_factory=dict)
    final_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scores": {k: round(v, 1) for k, v in self.scores.items()},
            "bonuses": {k: round(v, 1) for k, v in self.bonuses.items()},
            "penalties": {k: round(v, 1) for k, v in self.penalties.items()},
            "final": round(self.final_score, 1),
        }


@dataclass
class FlowSignal:
    """
    Complete flow signal representing detected institutional activity.

    This is the primary data structure passed to the UI and used
    for all display and filtering purposes.
    """
    # Identification
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    timestamp: datetime = field(default_factory=datetime.now)

    # Core classification
    symbol: str = ""
    signal_type: SignalType = SignalType.INSTITUTIONAL_FLOW
    direction: FlowDirection = FlowDirection.NEUTRAL

    # Target & Timeline
    price_target: float = 0.0
    target_date: date = field(default_factory=date.today)

    # Positioning
    positioning: PositioningType = PositioningType.UNKNOWN
    positioning_details: str = ""

    # Underlying data
    underlying_price: float = 0.0
    underlying_change_pct: float = 0.0

    # Technical levels
    technical_levels: TechnicalLevels = field(default_factory=TechnicalLevels)

    # Option details
    option: Optional[OptionDetails] = None

    # Flow metrics
    metrics: FlowMetrics = field(default_factory=lambda: FlowMetrics(
        premium_paid=0, contracts=0, volume=0,
        avg_volume=0, open_interest=0, prev_open_interest=0
    ))

    # Conviction
    conviction_level: ConvictionLevel = ConvictionLevel.LOW
    conviction_score: float = 0.0
    conviction_breakdown: ConvictionBreakdown = field(default_factory=ConvictionBreakdown)

    # Additional context
    sector: str = "Other"
    tags: List[str] = field(default_factory=list)
    notes: str = ""

    # Sweep-specific
    is_sweep: bool = False
    sweep_exchanges: int = 0

    # Multi-day tracking
    consecutive_days: int = 1
    aggregate_premium: float = 0.0

    @property
    def headline(self) -> str:
        """Generate headline for the signal."""
        return (
            f"{self.signal_type.value}  {self.symbol}  "
            f"→ ${self.price_target:.0f} Target  by {self.target_date.strftime('%b %d %Y')}"
        )

    @property
    def subtitle(self) -> str:
        """Generate subtitle with key details."""
        parts = [
            self.signal_type.value.replace("_", " ").title(),
            f"Target ${self.price_target:.0f} by {self.target_date.strftime('%b %d, %Y')}",
        ]

        if self.metrics.volume_ratio >= 3.0:
            parts.append("Unusually Increased Premiums")
        elif self.is_sweep:
            parts.append("Aggressive Sweep Detected")

        return " • ".join(parts)

    @property
    def levels_summary(self) -> str:
        """Generate technical levels summary."""
        return (
            f"${self.technical_levels.floor_price:.0f} Floor • "
            f"${self.technical_levels.resistance_price:.0f} Major Resistance"
        )

    @property
    def direction_color(self) -> str:
        """Get color for direction."""
        colors = {
            FlowDirection.BULLISH: "#00d4aa",
            FlowDirection.BEARISH: "#ff4757",
            FlowDirection.NEUTRAL: "#ffa502",
        }
        return colors.get(self.direction, "#6b7280")

    @property
    def conviction_color(self) -> str:
        """Get color for conviction level."""
        colors = {
            ConvictionLevel.HIGH: "#00d4aa",
            ConvictionLevel.MEDIUM: "#ffa502",
            ConvictionLevel.LOW: "#6b7280",
        }
        return colors.get(self.conviction_level, "#6b7280")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "signal_id": self.signal_id,
            "timestamp": self.timestamp.isoformat(),

            # Core
            "symbol": self.symbol,
            "signal_type": self.signal_type.value,
            "direction": self.direction.value,
            "direction_color": self.direction_color,

            # Target
            "price_target": round(self.price_target, 2),
            "target_date": self.target_date.isoformat(),

            # Positioning
            "positioning": self.positioning.value,
            "positioning_details": self.positioning_details,

            # Underlying
            "underlying_price": round(self.underlying_price, 2),
            "underlying_change_pct": round(self.underlying_change_pct, 2),

            # Technical
            "technical_levels": self.technical_levels.to_dict(),
            "levels_summary": self.levels_summary,

            # Option
            "option": self.option.to_dict() if self.option else None,

            # Metrics
            "metrics": self.metrics.to_dict(),

            # Conviction
            "conviction_level": self.conviction_level.value,
            "conviction_score": round(self.conviction_score, 1),
            "conviction_color": self.conviction_color,
            "conviction_breakdown": self.conviction_breakdown.to_dict(),

            # Display helpers
            "headline": self.headline,
            "subtitle": self.subtitle,

            # Context
            "sector": self.sector,
            "tags": self.tags,
            "notes": self.notes,

            # Flags
            "is_sweep": self.is_sweep,
            "sweep_exchanges": self.sweep_exchanges,
            "consecutive_days": self.consecutive_days,
            "aggregate_premium": round(self.aggregate_premium, 2),
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FlowSignal":
        """Create from dictionary."""
        signal = cls()
        signal.signal_id = data.get("signal_id", signal.signal_id)
        signal.timestamp = datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
        signal.symbol = data.get("symbol", "")
        signal.signal_type = SignalType(data.get("signal_type", "INSTITUTIONAL_FLOW"))
        signal.direction = FlowDirection(data.get("direction", "NEUTRAL"))
        signal.price_target = data.get("price_target", 0.0)
        signal.target_date = date.fromisoformat(data.get("target_date", date.today().isoformat()))
        signal.positioning = PositioningType(data.get("positioning", "Unknown"))
        signal.positioning_details = data.get("positioning_details", "")
        signal.underlying_price = data.get("underlying_price", 0.0)
        signal.sector = data.get("sector", "Other")
        signal.is_sweep = data.get("is_sweep", False)
        signal.conviction_score = data.get("conviction_score", 0.0)
        return signal


@dataclass
class FlowAlert:
    """
    Alert wrapper for FlowSignal with notification metadata.
    """
    signal: FlowSignal
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12].upper())
    created_at: datetime = field(default_factory=datetime.now)
    is_read: bool = False
    is_dismissed: bool = False
    priority: int = 0  # Higher = more important

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "created_at": self.created_at.isoformat(),
            "is_read": self.is_read,
            "is_dismissed": self.is_dismissed,
            "priority": self.priority,
            "signal": self.signal.to_dict(),
        }
