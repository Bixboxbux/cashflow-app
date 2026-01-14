#!/usr/bin/env python3
"""
Institutional Flow Tracker - Main Application

Real-time options flow detection for institutional/whale activity.
Inspired by Unusual Whales, FlowAlgo, and Cheddar Flow.

SAFETY FEATURES:
═══════════════════════════════════════════════════════════════════════════════
1. Paper trading verification before connecting (ports 7497, 4002 only)
2. Read-only mode enforcement - NO order placement functions exist
3. All signals are for human review only
═══════════════════════════════════════════════════════════════════════════════

Usage:
    python main.py [--port PORT] [--host HOST] [--demo]

    --port PORT     Dashboard port (default: 8080)
    --host HOST     Dashboard host (default: 0.0.0.0)
    --demo          Run in demo mode with simulated signals

Author: Institutional Flow Tracker
License: MIT
"""

import asyncio
import argparse
import logging
import logging.handlers
import signal
import sys
import random
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List
import threading
import time

import uvicorn

# Import our modules
from config import CONFIG
from config.thresholds import (
    SignalType, FlowDirection, ConvictionLevel, PositioningType,
    get_sector,
)
from models import (
    FlowSignal, FlowMetrics, TechnicalLevels,
    OptionDetails, ConvictionBreakdown,
)
from core import (
    IBKRConnection, IBKRConnectionError, SafetyViolationError,
    FlowDetector, FlowClassifier, AccumulationTracker,
    TechnicalLevelsCalculator,
)
from api import app, get_app_state, get_ws_manager, broadcast_signal


# ═══════════════════════════════════════════════════════════════════════════════
# Logging Setup
# ═══════════════════════════════════════════════════════════════════════════════

def setup_logging():
    """Configure logging."""
    log_dir = Path(CONFIG.logging.log_dir)
    log_dir.mkdir(exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / CONFIG.logging.system_log_file,
        maxBytes=CONFIG.logging.max_log_size,
        backupCount=CONFIG.logging.backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(CONFIG.logging.log_format)
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)

    return root_logger


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Demo Signal Generator
# ═══════════════════════════════════════════════════════════════════════════════

class DemoSignalGenerator:
    """Generates realistic demo signals for testing."""

    # Sample data for demo signals
    DEMO_DATA = [
        {
            "symbol": "HOOD",
            "signal_type": SignalType.INSTITUTIONAL_FLOW,
            "direction": FlowDirection.BULLISH,
            "price_target": 135.0,
            "target_date": date(2026, 1, 23),
            "positioning": PositioningType.ACCUMULATION,
            "positioning_details": "Last 5 trading days showed accumulation",
            "underlying_price": 118.50,
            "floor": 117.0,
            "resistance": 120.0,
            "premium": 450000,
            "contracts": 3500,
            "strike": 130.0,
            "option_type": "C",
            "dte": 10,
            "conviction": 78,
        },
        {
            "symbol": "NVDA",
            "signal_type": SignalType.SWEEP,
            "direction": FlowDirection.BULLISH,
            "price_target": 980.0,
            "target_date": date(2026, 2, 21),
            "positioning": PositioningType.ACCUMULATION,
            "positioning_details": "Golden sweep detected near ATM",
            "underlying_price": 920.50,
            "floor": 880.0,
            "resistance": 950.0,
            "premium": 1250000,
            "contracts": 2800,
            "strike": 950.0,
            "option_type": "C",
            "dte": 38,
            "conviction": 92,
            "is_sweep": True,
            "sweep_exchanges": 4,
        },
        {
            "symbol": "TSLA",
            "signal_type": SignalType.BLOCK,
            "direction": FlowDirection.BEARISH,
            "price_target": 380.0,
            "target_date": date(2026, 1, 16),
            "positioning": PositioningType.DISTRIBUTION,
            "positioning_details": "Large block put purchase",
            "underlying_price": 412.30,
            "floor": 380.0,
            "resistance": 425.0,
            "premium": 680000,
            "contracts": 1500,
            "strike": 400.0,
            "option_type": "P",
            "dte": 3,
            "conviction": 72,
        },
        {
            "symbol": "AAPL",
            "signal_type": SignalType.UNUSUAL_VOLUME,
            "direction": FlowDirection.BULLISH,
            "price_target": 245.0,
            "target_date": date(2026, 2, 14),
            "positioning": PositioningType.SPECULATIVE,
            "positioning_details": "5x average volume on weekly calls",
            "underlying_price": 228.75,
            "floor": 220.0,
            "resistance": 235.0,
            "premium": 320000,
            "contracts": 4200,
            "strike": 235.0,
            "option_type": "C",
            "dte": 31,
            "conviction": 68,
        },
        {
            "symbol": "META",
            "signal_type": SignalType.GOLDEN_SWEEP,
            "direction": FlowDirection.BULLISH,
            "price_target": 680.0,
            "target_date": date(2026, 1, 23),
            "positioning": PositioningType.ACCUMULATION,
            "positioning_details": "Golden sweep at resistance",
            "underlying_price": 612.50,
            "floor": 590.0,
            "resistance": 620.0,
            "premium": 890000,
            "contracts": 1800,
            "strike": 630.0,
            "option_type": "C",
            "dte": 10,
            "conviction": 85,
            "is_sweep": True,
            "sweep_exchanges": 3,
        },
        {
            "symbol": "SPY",
            "signal_type": SignalType.INSTITUTIONAL_FLOW,
            "direction": FlowDirection.NEUTRAL,
            "price_target": 605.0,
            "target_date": date(2026, 1, 31),
            "positioning": PositioningType.HEDGING,
            "positioning_details": "Balanced straddle positioning",
            "underlying_price": 598.20,
            "floor": 590.0,
            "resistance": 610.0,
            "premium": 2100000,
            "contracts": 8500,
            "strike": 600.0,
            "option_type": "C",
            "dte": 17,
            "conviction": 55,
        },
        {
            "symbol": "AMD",
            "signal_type": SignalType.SWEEP,
            "direction": FlowDirection.BEARISH,
            "price_target": 130.0,
            "target_date": date(2026, 1, 16),
            "positioning": PositioningType.DISTRIBUTION,
            "positioning_details": "Put sweep across 3 exchanges",
            "underlying_price": 142.80,
            "floor": 135.0,
            "resistance": 150.0,
            "premium": 420000,
            "contracts": 2200,
            "strike": 140.0,
            "option_type": "P",
            "dte": 3,
            "conviction": 75,
            "is_sweep": True,
            "sweep_exchanges": 3,
        },
        {
            "symbol": "GOOGL",
            "signal_type": SignalType.INSTITUTIONAL_FLOW,
            "direction": FlowDirection.BULLISH,
            "price_target": 210.0,
            "target_date": date(2026, 2, 21),
            "positioning": PositioningType.ACCUMULATION,
            "positioning_details": "Consistent buying over 4 days",
            "underlying_price": 192.40,
            "floor": 185.0,
            "resistance": 200.0,
            "premium": 780000,
            "contracts": 3100,
            "strike": 200.0,
            "option_type": "C",
            "dte": 38,
            "conviction": 82,
        },
        {
            "symbol": "QQQ",
            "signal_type": SignalType.BLOCK,
            "direction": FlowDirection.BEARISH,
            "price_target": 495.0,
            "target_date": date(2026, 1, 23),
            "positioning": PositioningType.HEDGING,
            "positioning_details": "Large put block, likely hedge",
            "underlying_price": 512.30,
            "floor": 500.0,
            "resistance": 525.0,
            "premium": 1500000,
            "contracts": 5000,
            "strike": 510.0,
            "option_type": "P",
            "dte": 10,
            "conviction": 62,
        },
        {
            "symbol": "MSFT",
            "signal_type": SignalType.UNUSUAL_VOLUME,
            "direction": FlowDirection.BULLISH,
            "price_target": 460.0,
            "target_date": date(2026, 2, 14),
            "positioning": PositioningType.ACCUMULATION,
            "positioning_details": "8x avg volume pre-earnings",
            "underlying_price": 428.50,
            "floor": 415.0,
            "resistance": 440.0,
            "premium": 560000,
            "contracts": 2900,
            "strike": 440.0,
            "option_type": "C",
            "dte": 31,
            "conviction": 79,
        },
    ]

    def __init__(self):
        self._index = 0
        self._used_signals = set()

    def generate(self) -> FlowSignal:
        """Generate a single demo signal."""
        # Cycle through demo data with some randomization
        data = self.DEMO_DATA[self._index % len(self.DEMO_DATA)]
        self._index += 1

        # Add randomization
        premium_mult = random.uniform(0.7, 1.5)
        conviction_adj = random.randint(-8, 8)

        signal = FlowSignal(
            timestamp=datetime.now(),
            symbol=data["symbol"],
            signal_type=data["signal_type"],
            direction=data["direction"],
            price_target=data["price_target"] * random.uniform(0.95, 1.05),
            target_date=data["target_date"],
            positioning=data["positioning"],
            positioning_details=data["positioning_details"],
            underlying_price=data["underlying_price"] * random.uniform(0.98, 1.02),
            technical_levels=TechnicalLevels(
                floor_price=data["floor"],
                resistance_price=data["resistance"],
                pivot_point=(data["floor"] + data["resistance"]) / 2,
            ),
            option=OptionDetails(
                contract_type=data["option_type"],
                strike=data["strike"],
                expiration=data["target_date"],
                days_to_expiry=data["dte"],
                bid=data["premium"] / data["contracts"] / 100 * 0.98,
                ask=data["premium"] / data["contracts"] / 100 * 1.02,
            ),
            metrics=FlowMetrics(
                premium_paid=data["premium"] * premium_mult,
                contracts=int(data["contracts"] * premium_mult),
                volume=int(data["contracts"] * premium_mult),
                avg_volume=int(data["contracts"] * 0.3),
                open_interest=int(data["contracts"] * 5),
                prev_open_interest=int(data["contracts"] * 4),
            ),
            conviction_score=min(100, max(0, data["conviction"] + conviction_adj)),
            conviction_level=(
                ConvictionLevel.HIGH if data["conviction"] + conviction_adj >= 75
                else ConvictionLevel.MEDIUM if data["conviction"] + conviction_adj >= 50
                else ConvictionLevel.LOW
            ),
            sector=get_sector(data["symbol"]),
            is_sweep=data.get("is_sweep", False),
            sweep_exchanges=data.get("sweep_exchanges", 0),
        )

        # Set option mid price
        if signal.option:
            signal.option.mid = (signal.option.bid + signal.option.ask) / 2
            signal.option.last = signal.option.mid

        return signal

    async def run_generator(self, interval: float = 3.0):
        """Continuously generate demo signals."""
        logger.info(f"Starting demo signal generator (interval: {interval}s)")

        while True:
            try:
                signal = self.generate()

                # Broadcast to dashboard
                await broadcast_signal(signal)

                logger.info(
                    f"[DEMO] {signal.signal_type.value} | {signal.symbol} | "
                    f"${signal.metrics.premium_paid:,.0f} | {signal.direction.value}"
                )

                await asyncio.sleep(interval + random.uniform(-1, 2))

            except Exception as e:
                logger.error(f"Error generating demo signal: {e}")
                await asyncio.sleep(5)


# ═══════════════════════════════════════════════════════════════════════════════
# Main Application Class
# ═══════════════════════════════════════════════════════════════════════════════

class FlowTracker:
    """
    Main application orchestrator.

    Coordinates:
    - IBKR connection (or demo mode)
    - Flow detection and classification
    - Signal broadcasting
    - Accumulation tracking
    """

    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode
        self.connection = None
        self.detector = FlowDetector()
        self.classifier = FlowClassifier()
        self.accumulation_tracker = AccumulationTracker()
        self.technical_calc = TechnicalLevelsCalculator()

        self.demo_generator = DemoSignalGenerator() if demo_mode else None
        self.running = False

        logger.info("=" * 60)
        logger.info("INSTITUTIONAL FLOW TRACKER")
        logger.info("=" * 60)
        logger.info(f"Mode: {'DEMO' if demo_mode else 'LIVE (Paper Trading)'}")
        logger.info("=" * 60)

    async def initialize(self):
        """Initialize the tracker."""
        if self.demo_mode:
            logger.info("Running in DEMO mode - generating simulated signals")
            return True

        try:
            logger.info("Initializing IBKR connection...")
            self.connection = IBKRConnection()
            await self.connection.connect()
            logger.info("✓ IBKR connected (Paper Trading)")
            return True

        except SafetyViolationError as e:
            logger.error(f"SAFETY VIOLATION: {e}")
            return False

        except IBKRConnectionError as e:
            logger.error(f"Connection failed: {e}")
            logger.info("Falling back to DEMO mode...")
            self.demo_mode = True
            self.demo_generator = DemoSignalGenerator()
            return True

    async def run(self):
        """Run the main tracking loop."""
        self.running = True

        if self.demo_mode:
            await self.demo_generator.run_generator(
                interval=CONFIG.demo_signal_interval_seconds
            )
        else:
            # Real IBKR mode would go here
            while self.running:
                await asyncio.sleep(1)

    async def shutdown(self):
        """Clean shutdown."""
        logger.info("Shutting down...")
        self.running = False

        if self.connection:
            await self.connection.disconnect()

        logger.info("Shutdown complete")


# ═══════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Institutional Flow Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                    # Run with IBKR connection
    python main.py --demo             # Run in demo mode
    python main.py --port 8000        # Use custom port

SAFETY NOTICE:
    This system operates in READ-ONLY mode only.
    It will REFUSE to connect to live trading accounts.
    All alerts are for informational purposes only.
        """
    )

    parser.add_argument(
        '--port', type=int, default=CONFIG.ui.port,
        help=f'Dashboard port (default: {CONFIG.ui.port})'
    )
    parser.add_argument(
        '--host', type=str, default=CONFIG.ui.host,
        help=f'Dashboard host (default: {CONFIG.ui.host})'
    )
    parser.add_argument(
        '--demo', action='store_true', default=True,
        help='Run in demo mode (default: True)'
    )
    parser.add_argument(
        '--live', action='store_true',
        help='Run in live mode with IBKR (requires paper trading)'
    )
    parser.add_argument(
        '--debug', action='store_true',
        help='Enable debug mode'
    )

    args = parser.parse_args()

    # Demo mode is default unless --live is specified
    demo_mode = not args.live

    # Setup logging
    setup_logging()

    # Print banner
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🐋  INSTITUTIONAL FLOW TRACKER                           ║
║                                                              ║
║    Real-Time Options Flow Detection                          ║
║    Whale • Sweep • Block • Dark Pool                         ║
║                                                              ║
║    ⚠️  READ-ONLY MODE - NO AUTOMATED TRADING                ║
║    📋  Paper Trading Connection Only                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Create tracker
    tracker = FlowTracker(demo_mode=demo_mode)

    # Initialize
    async def init_and_start():
        success = await tracker.initialize()
        if not success:
            logger.error("Initialization failed!")
            return False
        return True

    loop = asyncio.new_event_loop()
    if not loop.run_until_complete(init_and_start()):
        sys.exit(1)

    # Start background tracking
    def run_tracker():
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_until_complete(tracker.run())

    tracker_thread = threading.Thread(target=run_tracker, daemon=True)
    tracker_thread.start()

    # Signal handlers
    def signal_handler(sig, frame):
        print("\nShutting down...")
        loop.run_until_complete(tracker.shutdown())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Update app state
    state = get_app_state()
    state.is_demo_mode = demo_mode
    state.is_connected = True

    # Run web server
    logger.info(f"Starting dashboard at http://{args.host}:{args.port}")
    logger.info("Press Ctrl+C to stop")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="warning" if not args.debug else "debug"
    )


if __name__ == "__main__":
    main()
