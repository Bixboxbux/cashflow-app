"""
Institutional Flow Tracker - Settings Configuration

Central configuration for the entire application.
All safety settings are enforced here.

SAFETY NOTICE:
═══════════════════════════════════════════════════════════════
This system is READ-ONLY and connects to PAPER TRADING only.
No order execution functionality exists in this codebase.
═══════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set
from enum import Enum
import os


class Environment(Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    DEMO = "demo"


@dataclass
class SafetyConfig:
    """
    Non-negotiable safety configuration.

    These settings CANNOT be overridden.
    """
    paper_trading_only: bool = True
    allowed_ports: List[int] = field(default_factory=lambda: [7497, 4002])
    blocked_ports: List[int] = field(default_factory=lambda: [7496, 4001])
    read_only: bool = True
    human_execution_only: bool = True
    max_api_calls_per_second: int = 50

    def validate_port(self, port: int) -> bool:
        """Validate port is paper trading only."""
        if port in self.blocked_ports:
            raise ValueError(
                f"SAFETY VIOLATION: Port {port} is a LIVE trading port! "
                f"This system only supports paper trading on ports {self.allowed_ports}"
            )
        if port not in self.allowed_ports:
            raise ValueError(
                f"SAFETY VIOLATION: Port {port} is not recognized. "
                f"Allowed ports: {self.allowed_ports}"
            )
        return True


@dataclass
class IBKRConfig:
    """Interactive Brokers connection configuration."""
    host: str = "127.0.0.1"
    port: int = 7497  # Paper trading ONLY
    client_id: int = 1
    timeout: int = 30
    readonly: bool = True

    # Rate limiting
    max_requests_per_second: int = 45
    request_timeout: int = 10

    # Scanning settings
    scan_interval_seconds: float = 1.0
    max_concurrent_subscriptions: int = 100


@dataclass
class FlowDetectionConfig:
    """Flow detection thresholds and settings."""

    # Premium thresholds (in USD)
    mega_whale_threshold: int = 1_000_000
    whale_threshold: int = 250_000
    notable_threshold: int = 50_000
    min_tracking_threshold: int = 25_000

    # Volume thresholds
    unusual_volume_multiplier: float = 3.0
    unusual_oi_multiplier: float = 1.5

    # Sweep detection
    sweep_time_window_ms: int = 1000  # 1 second
    min_sweep_exchanges: int = 2

    # Accumulation tracking
    accumulation_lookback_days: int = 5
    distribution_lookback_days: int = 5

    # Technical levels
    support_resistance_lookback_days: int = 20
    min_touches_for_level: int = 2


@dataclass
class UIConfig:
    """Dashboard UI configuration."""
    host: str = "0.0.0.0"
    port: int = 8080

    # WebSocket
    ws_ping_interval: int = 30
    ws_max_connections: int = 100

    # Display
    max_signals_display: int = 100
    default_refresh_interval_ms: int = 1000

    # Theme
    background_color: str = "#0a0a0f"
    card_background: str = "#12121a"
    accent_bullish: str = "#00d4aa"
    accent_bearish: str = "#ff4757"
    accent_neutral: str = "#ffa502"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    log_dir: str = "logs"
    log_level: str = "INFO"
    log_format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    flow_log_file: str = "flow_signals.log"
    system_log_file: str = "system.log"

    max_log_size: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5


@dataclass
class AppConfig:
    """Master application configuration."""

    # Sub-configurations
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    ibkr: IBKRConfig = field(default_factory=IBKRConfig)
    flow: FlowDetectionConfig = field(default_factory=FlowDetectionConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Environment
    environment: Environment = Environment.DEMO
    debug: bool = False

    # Demo mode
    demo_mode: bool = True
    demo_signal_interval_seconds: float = 3.0

    def validate(self) -> bool:
        """Validate all configuration settings."""
        # Always validate safety first
        self.safety.validate_port(self.ibkr.port)

        if not self.safety.read_only:
            raise ValueError("SAFETY VIOLATION: read_only must be True")

        if not self.safety.paper_trading_only:
            raise ValueError("SAFETY VIOLATION: paper_trading_only must be True")

        return True


def load_config() -> AppConfig:
    """Load and validate application configuration."""
    config = AppConfig()

    # Override from environment variables
    if os.getenv("IBKR_HOST"):
        config.ibkr.host = os.getenv("IBKR_HOST")
    if os.getenv("IBKR_PORT"):
        config.ibkr.port = int(os.getenv("IBKR_PORT"))
    if os.getenv("UI_PORT"):
        config.ui.port = int(os.getenv("UI_PORT"))
    if os.getenv("DEMO_MODE"):
        config.demo_mode = os.getenv("DEMO_MODE").lower() == "true"
    if os.getenv("DEBUG"):
        config.debug = os.getenv("DEBUG").lower() == "true"

    # Validate configuration
    config.validate()

    return config


# Global configuration instance
CONFIG = load_config()


# ═══════════════════════════════════════════════════════════════════════════════
# SAFETY DECLARATION
# ═══════════════════════════════════════════════════════════════════════════════
"""
THIS SYSTEM IS READ-ONLY AND FOR INFORMATIONAL PURPOSES ONLY.

CAPABILITIES:
✓ Read market data from IBKR (paper trading only)
✓ Detect institutional/whale option flows
✓ Classify and display flow signals
✓ Track multi-day accumulation patterns
✓ Calculate technical support/resistance

RESTRICTIONS:
✗ NO order placement functionality
✗ NO account modification
✗ NO automated trading
✗ NO live trading connections

All trading decisions must be executed MANUALLY by the user.
This system provides ANALYSIS and ALERTS only.
"""
