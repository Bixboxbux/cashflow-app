"""
Institutional Flow Tracker - Market Data Models

Data structures for market data from IBKR.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from enum import Enum


class OptionRight(Enum):
    """Option type."""
    CALL = "C"
    PUT = "P"


@dataclass
class OHLCV:
    """Open-High-Low-Close-Volume bar."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "open": round(self.open, 2),
            "high": round(self.high, 2),
            "low": round(self.low, 2),
            "close": round(self.close, 2),
            "volume": self.volume,
        }


@dataclass
class Quote:
    """Real-time quote data."""
    symbol: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Pricing
    bid: float = 0.0
    ask: float = 0.0
    last: float = 0.0
    close: float = 0.0  # Previous close

    # Sizes
    bid_size: int = 0
    ask_size: int = 0
    last_size: int = 0

    # Volume
    volume: int = 0
    avg_volume: int = 0

    # Change
    change: float = 0.0
    change_pct: float = 0.0

    @property
    def mid(self) -> float:
        """Mid price."""
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / 2
        return self.last

    @property
    def spread(self) -> float:
        """Bid-ask spread."""
        return self.ask - self.bid

    @property
    def spread_pct(self) -> float:
        """Spread as percentage of mid."""
        if self.mid > 0:
            return (self.spread / self.mid) * 100
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "bid": self.bid,
            "ask": self.ask,
            "last": self.last,
            "mid": round(self.mid, 2),
            "volume": self.volume,
            "change_pct": round(self.change_pct, 2),
        }


@dataclass
class OptionContract:
    """Option contract specification."""
    symbol: str
    underlying: str
    right: OptionRight
    strike: float
    expiration: date

    # Contract identifiers
    con_id: int = 0
    exchange: str = "SMART"
    currency: str = "USD"

    # Multiplier (usually 100 for US equity options)
    multiplier: int = 100

    @property
    def days_to_expiry(self) -> int:
        """Calculate days until expiration."""
        return (self.expiration - date.today()).days

    @property
    def display_name(self) -> str:
        """Human-readable contract name."""
        return (
            f"{self.underlying} "
            f"{self.expiration.strftime('%b %d')} "
            f"${self.strike:.0f} "
            f"{self.right.value}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "underlying": self.underlying,
            "right": self.right.value,
            "strike": self.strike,
            "expiration": self.expiration.isoformat(),
            "dte": self.days_to_expiry,
            "con_id": self.con_id,
            "display_name": self.display_name,
        }


@dataclass
class OptionQuote(Quote):
    """Extended quote for options with Greeks."""
    contract: Optional[OptionContract] = None

    # Greeks
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    rho: float = 0.0

    # Implied volatility
    implied_volatility: float = 0.0
    iv_rank: float = 0.0  # IV percentile

    # Open interest
    open_interest: int = 0
    prev_open_interest: int = 0

    # Theoretical values
    theoretical_price: float = 0.0
    underlying_price: float = 0.0

    @property
    def oi_change(self) -> int:
        """Open interest change."""
        return self.open_interest - self.prev_open_interest

    @property
    def oi_change_pct(self) -> float:
        """Open interest change percentage."""
        if self.prev_open_interest > 0:
            return (self.oi_change / self.prev_open_interest) * 100
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "contract": self.contract.to_dict() if self.contract else None,
            "delta": round(self.delta, 3),
            "gamma": round(self.gamma, 4),
            "theta": round(self.theta, 3),
            "vega": round(self.vega, 3),
            "iv": round(self.implied_volatility, 1),
            "open_interest": self.open_interest,
            "oi_change": self.oi_change,
            "oi_change_pct": round(self.oi_change_pct, 1),
            "underlying_price": self.underlying_price,
        })
        return base


@dataclass
class OptionTrade:
    """
    Represents a single option trade execution.

    This is the raw input for flow detection.
    """
    timestamp: datetime
    contract: OptionContract
    price: float
    size: int  # Number of contracts
    exchange: str = ""
    condition: str = ""  # Trade condition codes

    # Derived fields
    premium: float = 0.0  # Total premium paid
    side: str = ""  # "BUY" or "SELL" (if determinable)

    # Quote at time of trade
    bid_at_trade: float = 0.0
    ask_at_trade: float = 0.0
    underlying_at_trade: float = 0.0

    def __post_init__(self):
        """Calculate derived fields."""
        self.premium = self.price * self.size * self.contract.multiplier

        # Determine side based on price vs bid/ask
        if self.bid_at_trade > 0 and self.ask_at_trade > 0:
            mid = (self.bid_at_trade + self.ask_at_trade) / 2
            if self.price >= self.ask_at_trade:
                self.side = "BUY"  # Bought at ask (aggressive)
            elif self.price <= self.bid_at_trade:
                self.side = "SELL"  # Sold at bid (aggressive)
            elif self.price > mid:
                self.side = "BUY"  # Above mid, likely buyer
            else:
                self.side = "SELL"  # Below mid, likely seller

    @property
    def is_aggressive_buy(self) -> bool:
        """Check if trade was an aggressive buy (lifted the ask)."""
        return self.price >= self.ask_at_trade and self.ask_at_trade > 0

    @property
    def is_aggressive_sell(self) -> bool:
        """Check if trade was an aggressive sell (hit the bid)."""
        return self.price <= self.bid_at_trade and self.bid_at_trade > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "contract": self.contract.to_dict(),
            "price": round(self.price, 2),
            "size": self.size,
            "premium": round(self.premium, 2),
            "side": self.side,
            "exchange": self.exchange,
            "is_aggressive_buy": self.is_aggressive_buy,
            "is_aggressive_sell": self.is_aggressive_sell,
            "underlying_at_trade": round(self.underlying_at_trade, 2),
        }


@dataclass
class SweepOrder:
    """
    Represents a sweep order detected across multiple exchanges.

    Sweeps are large orders that execute across multiple exchanges
    in rapid succession, indicating institutional urgency.
    """
    id: str
    timestamp: datetime
    contract: OptionContract
    trades: List[OptionTrade] = field(default_factory=list)

    @property
    def total_contracts(self) -> int:
        """Total contracts in sweep."""
        return sum(t.size for t in self.trades)

    @property
    def total_premium(self) -> float:
        """Total premium paid."""
        return sum(t.premium for t in self.trades)

    @property
    def exchanges_hit(self) -> int:
        """Number of exchanges involved."""
        return len(set(t.exchange for t in self.trades))

    @property
    def avg_price(self) -> float:
        """Volume-weighted average price."""
        if self.total_contracts == 0:
            return 0.0
        return sum(t.price * t.size for t in self.trades) / self.total_contracts

    @property
    def time_span_ms(self) -> int:
        """Time span of sweep in milliseconds."""
        if len(self.trades) < 2:
            return 0
        times = sorted(t.timestamp for t in self.trades)
        return int((times[-1] - times[0]).total_seconds() * 1000)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "contract": self.contract.to_dict(),
            "total_contracts": self.total_contracts,
            "total_premium": round(self.total_premium, 2),
            "exchanges_hit": self.exchanges_hit,
            "avg_price": round(self.avg_price, 2),
            "time_span_ms": self.time_span_ms,
            "trades": [t.to_dict() for t in self.trades],
        }


@dataclass
class SymbolProfile:
    """
    Profile for a tradeable symbol with aggregated data.
    """
    symbol: str
    name: str = ""
    sector: str = "Other"

    # Current quote
    price: float = 0.0
    change_pct: float = 0.0
    volume: int = 0

    # Historical data
    high_52w: float = 0.0
    low_52w: float = 0.0
    avg_volume_30d: int = 0

    # Options data
    has_options: bool = True
    options_volume_today: int = 0
    options_oi_total: int = 0

    # Earnings
    next_earnings: Optional[date] = None
    days_to_earnings: int = -1

    # Technical levels
    support: float = 0.0
    resistance: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "sector": self.sector,
            "price": round(self.price, 2),
            "change_pct": round(self.change_pct, 2),
            "volume": self.volume,
            "high_52w": round(self.high_52w, 2),
            "low_52w": round(self.low_52w, 2),
            "avg_volume_30d": self.avg_volume_30d,
            "options_volume_today": self.options_volume_today,
            "next_earnings": self.next_earnings.isoformat() if self.next_earnings else None,
            "support": round(self.support, 2),
            "resistance": round(self.resistance, 2),
        }
