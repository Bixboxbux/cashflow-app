"""
IBKR Options Trading Assistant - Configuration Module

This module contains all configuration settings for the application.
All settings are centralized here for easy modification and maintenance.

IMPORTANT: This system is READ-ONLY and designed for PAPER TRADING only.
No automated trading functionality exists in this codebase.
"""

from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum
import os


class TradingMode(Enum):
    """Trading mode enumeration - ONLY PAPER is allowed."""
    PAPER = "paper"
    # LIVE mode is intentionally NOT implemented for safety


class TimeFrame(Enum):
    """Supported analysis timeframes."""
    ONE_MIN = "1min"
    FIVE_MIN = "5min"
    FIFTEEN_MIN = "15min"


class Decision(Enum):
    """Possible trading decisions (for ALERTS only, not execution)."""
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"


@dataclass
class IBKRConfig:
    """
    Interactive Brokers connection configuration.

    CRITICAL SAFETY NOTES:
    - Port 7497 is the TWS Paper Trading port
    - Port 7496 is the TWS Live Trading port (BLOCKED)
    - Port 4002 is the IB Gateway Paper Trading port
    - Port 4001 is the IB Gateway Live Trading port (BLOCKED)

    This system will REFUSE to connect to live trading ports.
    """
    host: str = "127.0.0.1"
    port: int = 7497  # Paper trading port ONLY
    client_id: int = 1
    timeout: int = 30
    readonly: bool = True  # Always read-only

    # Blocked ports - system will abort if these are detected
    BLOCKED_PORTS: List[int] = field(default_factory=lambda: [7496, 4001])
    ALLOWED_PORTS: List[int] = field(default_factory=lambda: [7497, 4002])

    def validate(self) -> bool:
        """Validate configuration is safe (paper trading only)."""
        if self.port in self.BLOCKED_PORTS:
            raise ValueError(
                f"SAFETY ABORT: Port {self.port} is a LIVE trading port! "
                f"This system only supports paper trading on ports {self.ALLOWED_PORTS}"
            )
        if self.port not in self.ALLOWED_PORTS:
            raise ValueError(
                f"SAFETY ABORT: Port {self.port} is not a recognized paper trading port. "
                f"Allowed ports: {self.ALLOWED_PORTS}"
            )
        if not self.readonly:
            raise ValueError(
                "SAFETY ABORT: readonly must be True. This system does not support trading."
            )
        return True


@dataclass
class SignalConfig:
    """
    Signal detection thresholds and parameters.

    These values control when signals are triggered.
    Adjust based on market conditions and backtesting results.
    """

    # Unusual Options Volume: Volume must be >= this multiplier of average
    volume_multiplier_threshold: float = 3.0

    # Open Interest Acceleration: OI increase percentage threshold
    oi_acceleration_threshold: float = 20.0  # 20% increase

    # Implied Volatility Spike: IV change threshold
    iv_spike_threshold: float = 15.0  # 15% increase

    # Delta-Aligned Momentum: Minimum correlation threshold
    delta_momentum_correlation: float = 0.7  # 70% correlation

    # Minimum option volume to consider (filter out illiquid options)
    min_option_volume: int = 100

    # Minimum open interest to consider
    min_open_interest: int = 500

    # Maximum bid-ask spread percentage (liquidity filter)
    max_spread_pct: float = 10.0  # 10% max spread


@dataclass
class DecisionConfig:
    """
    Decision engine configuration.

    Controls how signals are weighted and combined
    to produce final BUY/SELL/WAIT decisions.
    """

    # Minimum confidence to trigger BUY or SELL (otherwise WAIT)
    min_confidence_threshold: float = 65.0

    # Signal weights (must sum to 1.0)
    signal_weights: Dict[str, float] = field(default_factory=lambda: {
        "unusual_volume": 0.30,      # 30% weight
        "oi_acceleration": 0.25,     # 25% weight
        "iv_spike": 0.25,            # 25% weight
        "delta_momentum": 0.20       # 20% weight
    })

    # Volatility penalty: High IV reduces confidence
    volatility_penalty_threshold: float = 50.0  # IV above this gets penalized
    volatility_penalty_factor: float = 0.15     # 15% reduction per threshold

    # Liquidity bonus: Good liquidity increases confidence
    liquidity_bonus_threshold: float = 1000     # Volume above this gets bonus
    liquidity_bonus_factor: float = 0.10        # 10% bonus max


@dataclass
class UIConfig:
    """Web dashboard UI configuration."""

    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False

    # Refresh interval in seconds
    refresh_interval: int = 30

    # Maximum alerts to display
    max_alerts_display: int = 100

    # Default filters
    default_min_confidence: float = 0.0
    default_option_types: List[str] = field(default_factory=lambda: ["CALL", "PUT"])


@dataclass
class LogConfig:
    """Logging configuration."""

    log_dir: str = "logs"
    log_level: str = "INFO"
    log_format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    # Alert logging
    alert_log_file: str = "alerts.log"

    # System logging
    system_log_file: str = "system.log"

    # Maximum log file size (bytes)
    max_log_size: int = 10 * 1024 * 1024  # 10 MB

    # Number of backup files to keep
    backup_count: int = 5


@dataclass
class AppConfig:
    """
    Master application configuration.

    Combines all sub-configurations into a single object.
    """

    ibkr: IBKRConfig = field(default_factory=IBKRConfig)
    signals: SignalConfig = field(default_factory=SignalConfig)
    decision: DecisionConfig = field(default_factory=DecisionConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LogConfig = field(default_factory=LogConfig)

    # Watchlist: Symbols to monitor
    watchlist: List[str] = field(default_factory=lambda: [
        "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN",
        "META", "TSLA", "AMD", "SPY", "QQQ"
    ])

    # Supported timeframes
    timeframes: List[str] = field(default_factory=lambda: ["1min", "5min", "15min"])

    # Default timeframe
    default_timeframe: str = "5min"

    # Maximum days to expiration for options to monitor
    max_dte: int = 45

    # Minimum days to expiration
    min_dte: int = 1

    def validate(self) -> bool:
        """Validate all configuration settings."""
        # Validate IBKR config (most critical)
        self.ibkr.validate()

        # Validate signal weights sum to 1.0
        weight_sum = sum(self.decision.signal_weights.values())
        if abs(weight_sum - 1.0) > 0.001:
            raise ValueError(
                f"Signal weights must sum to 1.0, got {weight_sum}"
            )

        # Validate thresholds are positive
        if self.signals.volume_multiplier_threshold <= 0:
            raise ValueError("Volume multiplier must be positive")
        if self.decision.min_confidence_threshold < 0 or self.decision.min_confidence_threshold > 100:
            raise ValueError("Confidence threshold must be between 0 and 100")

        return True


def load_config() -> AppConfig:
    """
    Load and validate application configuration.

    Returns:
        AppConfig: Validated configuration object

    Raises:
        ValueError: If configuration validation fails
    """
    config = AppConfig()

    # Override from environment variables if present
    if os.getenv("IBKR_HOST"):
        config.ibkr.host = os.getenv("IBKR_HOST")
    if os.getenv("IBKR_PORT"):
        config.ibkr.port = int(os.getenv("IBKR_PORT"))
    if os.getenv("IBKR_CLIENT_ID"):
        config.ibkr.client_id = int(os.getenv("IBKR_CLIENT_ID"))
    if os.getenv("UI_PORT"):
        config.ui.port = int(os.getenv("UI_PORT"))
    if os.getenv("WATCHLIST"):
        config.watchlist = os.getenv("WATCHLIST").split(",")

    # Validate configuration
    config.validate()

    return config


# Global configuration instance
CONFIG = load_config()


# ══════════════════════════════════════════════════════════════════════════════
# SAFETY DECLARATION
# ══════════════════════════════════════════════════════════════════════════════
"""
THIS SYSTEM IS READ-ONLY AND FOR INFORMATIONAL PURPOSES ONLY.

CAPABILITIES:
✓ Read market data from IBKR
✓ Analyze options chains
✓ Detect trading signals
✓ Generate alerts with recommendations
✓ Display information in web dashboard

RESTRICTIONS:
✗ NO order placement functionality
✗ NO account modification
✗ NO automated trading
✗ NO live trading connections

All trading decisions must be executed MANUALLY by the user.
This system provides ANALYSIS and ALERTS only.
"""
