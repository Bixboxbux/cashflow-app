#!/usr/bin/env python3
"""
IBKR Options Trading Assistant - Main Application

This is the main entry point for the IBKR Options Trading Assistant.
It orchestrates all components and runs the web dashboard.

SAFETY FEATURES:
═══════════════════════════════════════════════════════════════════════════════
1. Paper trading verification before connecting
2. Read-only mode enforcement
3. No order placement functionality
4. All alerts are for human review only
═══════════════════════════════════════════════════════════════════════════════

Usage:
    python main.py [--port PORT] [--host HOST] [--demo]

    --port PORT     Dashboard port (default: 8080)
    --host HOST     Dashboard host (default: 0.0.0.0)
    --demo          Run in demo mode without IBKR connection

Author: IBKR Options Assistant
License: MIT
"""

import asyncio
import argparse
import logging
import logging.handlers
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import List
import threading
import time

import uvicorn

# Import our modules
from config import CONFIG, load_config
from data_fetcher_ibkr import IBKRDataFetcher, IBKRConnectionError, SafetyViolationError
from options_chain_engine import OptionsChainEngine
from signal_engine import SignalEngine, OptionSignals
from decision_engine import DecisionEngine, TradingAlert
from ui_dashboard import app, update_alert_store


# ══════════════════════════════════════════════════════════════════════════════
# Logging Configuration
# ══════════════════════════════════════════════════════════════════════════════

def setup_logging():
    """Configure logging for the application."""
    # Create logs directory if needed
    log_dir = Path(CONFIG.logging.log_dir)
    log_dir.mkdir(exist_ok=True)

    # Configure root logger
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

    # File handler for system logs
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / CONFIG.logging.system_log_file,
        maxBytes=CONFIG.logging.max_log_size,
        backupCount=CONFIG.logging.backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(CONFIG.logging.log_format)
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)

    # Alert-specific file handler
    alert_handler = logging.handlers.RotatingFileHandler(
        log_dir / CONFIG.logging.alert_log_file,
        maxBytes=CONFIG.logging.max_log_size,
        backupCount=CONFIG.logging.backup_count
    )
    alert_handler.setLevel(logging.INFO)
    alert_handler.setFormatter(file_format)

    alert_logger = logging.getLogger('alerts')
    alert_logger.addHandler(alert_handler)

    return root_logger


# Get logger after setup
logger = logging.getLogger(__name__)
alert_logger = logging.getLogger('alerts')


# ══════════════════════════════════════════════════════════════════════════════
# Demo Mode Data Generator
# ══════════════════════════════════════════════════════════════════════════════

def generate_demo_alerts() -> List[TradingAlert]:
    """Generate demo alerts for testing without IBKR connection."""
    from config import Decision
    from signal_engine import Signal, SignalType, SignalDirection
    from decision_engine import ConfidenceBreakdown

    demo_data = [
        {
            'symbol': 'NVDA',
            'option_type': 'CALL',
            'strike': 200.0,
            'expiration': '2026-01-16',
            'days_to_expiry': 3,
            'underlying_price': 198.50,
            'option_bid': 5.20,
            'option_ask': 5.40,
            'decision': Decision.BUY,
            'confidence': 78.5,
            'volume': 15420,
            'avg_volume': 3200,
            'open_interest': 45000,
            'implied_volatility': 52.3,
            'delta': 0.52,
            'signals': [
                Signal(SignalType.UNUSUAL_VOLUME, SignalDirection.BULLISH, 85.0,
                      "Volume 4.8x average"),
                Signal(SignalType.OI_ACCELERATION, SignalDirection.BULLISH, 72.0,
                      "OI increased 28%"),
            ]
        },
        {
            'symbol': 'AAPL',
            'option_type': 'PUT',
            'strike': 175.0,
            'expiration': '2026-01-23',
            'days_to_expiry': 10,
            'underlying_price': 178.25,
            'option_bid': 2.85,
            'option_ask': 2.95,
            'decision': Decision.SELL,
            'confidence': 71.2,
            'volume': 8900,
            'avg_volume': 2100,
            'open_interest': 32000,
            'implied_volatility': 38.5,
            'delta': -0.35,
            'signals': [
                Signal(SignalType.UNUSUAL_VOLUME, SignalDirection.BEARISH, 75.0,
                      "Volume 4.2x average"),
                Signal(SignalType.DELTA_MOMENTUM, SignalDirection.BEARISH, 68.0,
                      "Delta aligned with -1.2% move"),
            ]
        },
        {
            'symbol': 'MSFT',
            'option_type': 'CALL',
            'strike': 420.0,
            'expiration': '2026-02-21',
            'days_to_expiry': 39,
            'underlying_price': 415.80,
            'option_bid': 12.50,
            'option_ask': 12.80,
            'decision': Decision.WAIT,
            'confidence': 58.3,
            'volume': 4200,
            'avg_volume': 1800,
            'open_interest': 18500,
            'implied_volatility': 28.2,
            'delta': 0.45,
            'signals': [
                Signal(SignalType.IV_SPIKE, SignalDirection.NEUTRAL, 55.0,
                      "IV spiked 18%"),
            ]
        },
        {
            'symbol': 'TSLA',
            'option_type': 'CALL',
            'strike': 250.0,
            'expiration': '2026-01-16',
            'days_to_expiry': 3,
            'underlying_price': 248.75,
            'option_bid': 8.10,
            'option_ask': 8.35,
            'decision': Decision.BUY,
            'confidence': 82.7,
            'volume': 28500,
            'avg_volume': 5500,
            'open_interest': 92000,
            'implied_volatility': 68.5,
            'delta': 0.48,
            'signals': [
                Signal(SignalType.UNUSUAL_VOLUME, SignalDirection.BULLISH, 88.0,
                      "Volume 5.2x average"),
                Signal(SignalType.OI_ACCELERATION, SignalDirection.BULLISH, 78.0,
                      "OI increased 35%"),
                Signal(SignalType.DELTA_MOMENTUM, SignalDirection.BULLISH, 72.0,
                      "Delta aligned with +2.1% move"),
            ]
        },
        {
            'symbol': 'AMD',
            'option_type': 'PUT',
            'strike': 140.0,
            'expiration': '2026-01-23',
            'days_to_expiry': 10,
            'underlying_price': 142.30,
            'option_bid': 3.40,
            'option_ask': 3.55,
            'decision': Decision.WAIT,
            'confidence': 52.1,
            'volume': 3800,
            'avg_volume': 1500,
            'open_interest': 22000,
            'implied_volatility': 55.8,
            'delta': -0.38,
            'signals': [
                Signal(SignalType.UNUSUAL_VOLUME, SignalDirection.BEARISH, 62.0,
                      "Volume 2.5x average"),
            ]
        },
        {
            'symbol': 'SPY',
            'option_type': 'CALL',
            'strike': 600.0,
            'expiration': '2026-01-16',
            'days_to_expiry': 3,
            'underlying_price': 598.50,
            'option_bid': 4.80,
            'option_ask': 4.90,
            'decision': Decision.BUY,
            'confidence': 69.8,
            'volume': 45000,
            'avg_volume': 12000,
            'open_interest': 180000,
            'implied_volatility': 15.2,
            'delta': 0.42,
            'signals': [
                Signal(SignalType.UNUSUAL_VOLUME, SignalDirection.BULLISH, 70.0,
                      "Volume 3.8x average"),
                Signal(SignalType.DELTA_MOMENTUM, SignalDirection.BULLISH, 65.0,
                      "Delta aligned with +0.8% move"),
            ]
        },
        {
            'symbol': 'QQQ',
            'option_type': 'PUT',
            'strike': 510.0,
            'expiration': '2026-01-30',
            'days_to_expiry': 17,
            'underlying_price': 515.20,
            'option_bid': 6.25,
            'option_ask': 6.45,
            'decision': Decision.SELL,
            'confidence': 67.4,
            'volume': 18200,
            'avg_volume': 4800,
            'open_interest': 65000,
            'implied_volatility': 22.8,
            'delta': -0.32,
            'signals': [
                Signal(SignalType.UNUSUAL_VOLUME, SignalDirection.BEARISH, 68.0,
                      "Volume 3.8x average"),
                Signal(SignalType.IV_SPIKE, SignalDirection.NEUTRAL, 58.0,
                      "IV spiked 16%"),
            ]
        },
        {
            'symbol': 'META',
            'option_type': 'CALL',
            'strike': 620.0,
            'expiration': '2026-02-21',
            'days_to_expiry': 39,
            'underlying_price': 612.50,
            'option_bid': 28.50,
            'option_ask': 29.20,
            'decision': Decision.WAIT,
            'confidence': 45.2,
            'volume': 2100,
            'avg_volume': 900,
            'open_interest': 8500,
            'implied_volatility': 42.5,
            'delta': 0.48,
            'signals': [
                Signal(SignalType.UNUSUAL_VOLUME, SignalDirection.BULLISH, 55.0,
                      "Volume 2.3x average"),
            ]
        },
    ]

    alerts = []
    counter = 0

    for data in demo_data:
        counter += 1
        alert_id = f"DEMO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{counter:04d}"

        breakdown = ConfidenceBreakdown(
            signal_scores={s.signal_type.value: s.strength * 0.25 for s in data['signals']},
            weighted_total=data['confidence'] * 0.8,
            volatility_penalty=-5.0 if data['implied_volatility'] > 50 else 0.0,
            liquidity_bonus=5.0 if data['volume'] > 10000 else 0.0,
            spread_penalty=-2.0 if (data['option_ask'] - data['option_bid']) / data['option_bid'] > 0.05 else 0.0,
            convergence_bonus=10.0 if len(data['signals']) >= 2 else 0.0,
            final_score=data['confidence']
        )

        # Determine dominant direction
        bullish = sum(1 for s in data['signals'] if s.direction == SignalDirection.BULLISH)
        bearish = sum(1 for s in data['signals'] if s.direction == SignalDirection.BEARISH)

        if bullish > bearish:
            direction = SignalDirection.BULLISH
        elif bearish > bullish:
            direction = SignalDirection.BEARISH
        else:
            direction = SignalDirection.NEUTRAL

        alert = TradingAlert(
            alert_id=alert_id,
            timestamp=datetime.now(),
            symbol=data['symbol'],
            option_type=data['option_type'],
            strike=data['strike'],
            expiration=data['expiration'],
            days_to_expiry=data['days_to_expiry'],
            underlying_price=data['underlying_price'],
            option_bid=data['option_bid'],
            option_ask=data['option_ask'],
            option_mid=(data['option_bid'] + data['option_ask']) / 2,
            decision=data['decision'],
            confidence=data['confidence'],
            confidence_breakdown=breakdown,
            signals=data['signals'],
            signal_count=len(data['signals']),
            dominant_direction=direction,
            volume=data['volume'],
            avg_volume=data['avg_volume'],
            volume_ratio=data['volume'] / data['avg_volume'],
            open_interest=data['open_interest'],
            implied_volatility=data['implied_volatility'],
            delta=data['delta'],
            spread_pct=((data['option_ask'] - data['option_bid']) /
                       ((data['option_bid'] + data['option_ask']) / 2) * 100)
        )

        alerts.append(alert)

    return alerts


# ══════════════════════════════════════════════════════════════════════════════
# Main Application Class
# ══════════════════════════════════════════════════════════════════════════════

class OptionsAssistant:
    """
    Main application orchestrator.

    This class coordinates all components:
    - IBKR data fetching
    - Options chain processing
    - Signal detection
    - Decision generation
    - Alert management
    """

    def __init__(self, demo_mode: bool = False):
        """
        Initialize the Options Assistant.

        Args:
            demo_mode: If True, use demo data instead of IBKR
        """
        self.demo_mode = demo_mode
        self.fetcher = None
        self.chain_engine = None
        self.signal_engine = SignalEngine()
        self.decision_engine = DecisionEngine()

        self.running = False
        self.update_thread = None

        logger.info("=" * 60)
        logger.info("IBKR OPTIONS TRADING ASSISTANT")
        logger.info("=" * 60)
        logger.info(f"Mode: {'DEMO' if demo_mode else 'LIVE (Paper Trading)'}")
        logger.info(f"Watchlist: {', '.join(CONFIG.watchlist)}")
        logger.info("=" * 60)

    async def initialize(self):
        """Initialize connections and engines."""
        if self.demo_mode:
            logger.info("Running in DEMO mode - no IBKR connection required")
            return True

        try:
            logger.info("Initializing IBKR connection...")

            self.fetcher = IBKRDataFetcher()
            await self.fetcher.connect()

            self.chain_engine = OptionsChainEngine(self.fetcher)

            logger.info("✓ IBKR connection established (Paper Trading)")
            return True

        except SafetyViolationError as e:
            logger.error(f"SAFETY VIOLATION: {e}")
            logger.error("System will NOT connect to live trading accounts!")
            return False

        except IBKRConnectionError as e:
            logger.error(f"Connection failed: {e}")
            logger.info("Falling back to DEMO mode...")
            self.demo_mode = True
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False

    async def scan_watchlist(self) -> List[TradingAlert]:
        """
        Scan all symbols in the watchlist for signals.

        Returns:
            List of generated alerts
        """
        if self.demo_mode:
            return generate_demo_alerts()

        all_alerts = []

        for symbol in CONFIG.watchlist:
            try:
                logger.info(f"Scanning {symbol}...")

                # Fetch options chain
                options = await self.chain_engine.fetch_and_process(symbol)

                if not options:
                    logger.warning(f"No options data for {symbol}")
                    continue

                # Analyze for signals
                signals_list = self.signal_engine.analyze_chain(options)

                if not signals_list:
                    logger.debug(f"No signals for {symbol}")
                    continue

                # Generate alerts
                alerts = self.decision_engine.generate_alerts(signals_list)

                for alert in alerts:
                    all_alerts.append(alert)
                    self._log_alert(alert)

                logger.info(f"  {symbol}: {len(alerts)} alerts generated")

            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")

        # Sort by confidence
        all_alerts.sort(key=lambda a: a.confidence, reverse=True)

        return all_alerts

    def _log_alert(self, alert: TradingAlert):
        """Log an alert to the alert log file."""
        alert_logger.info(
            f"{alert.decision.value} | {alert.symbol} {alert.option_type} "
            f"${alert.strike:.0f} {alert.expiration} | "
            f"Confidence: {alert.confidence:.1f}% | "
            f"Signals: {alert.signal_count}"
        )

    async def update_loop(self, interval: int = 60):
        """
        Continuous update loop for scanning and alerting.

        Args:
            interval: Seconds between scans
        """
        self.running = True

        while self.running:
            try:
                logger.info("Starting watchlist scan...")

                alerts = await self.scan_watchlist()

                # Update the dashboard store
                update_alert_store(alerts, connected=not self.demo_mode)

                logger.info(
                    f"Scan complete: {len(alerts)} alerts | "
                    f"Actionable: {sum(1 for a in alerts if a.is_actionable)}"
                )

                # Wait for next scan
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                await asyncio.sleep(10)  # Brief pause on error

    def start_background_updates(self, interval: int = 60):
        """Start background update thread."""
        def run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.update_loop(interval))

        self.update_thread = threading.Thread(target=run_loop, daemon=True)
        self.update_thread.start()
        logger.info(f"Background updates started (interval: {interval}s)")

    async def shutdown(self):
        """Clean shutdown."""
        logger.info("Shutting down...")
        self.running = False

        if self.fetcher:
            await self.fetcher.disconnect()

        logger.info("Shutdown complete")


# ══════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="IBKR Options Trading Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                    # Run with IBKR connection
    python main.py --demo             # Run in demo mode (no IBKR needed)
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
        '--demo', action='store_true',
        help='Run in demo mode without IBKR connection'
    )
    parser.add_argument(
        '--debug', action='store_true',
        help='Enable debug mode'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Print banner
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     📊  IBKR OPTIONS TRADING ASSISTANT                      ║
║                                                              ║
║     Signal Analysis Dashboard for Options Traders            ║
║                                                              ║
║     ⚠️  READ-ONLY MODE - NO AUTOMATED TRADING               ║
║     📋  Paper Trading Connection Only                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Create assistant
    assistant = OptionsAssistant(demo_mode=args.demo)

    # Initialize in async context
    async def init_and_start():
        success = await assistant.initialize()
        if not success:
            logger.error("Initialization failed!")
            return False

        # Do initial scan
        alerts = await assistant.scan_watchlist()
        update_alert_store(alerts, connected=not assistant.demo_mode)
        logger.info(f"Initial scan: {len(alerts)} alerts loaded")

        return True

    # Run initialization
    loop = asyncio.new_event_loop()
    if not loop.run_until_complete(init_and_start()):
        sys.exit(1)

    # Start background updates
    assistant.start_background_updates(interval=CONFIG.ui.refresh_interval)

    # Setup signal handlers
    def signal_handler(sig, frame):
        print("\nShutting down...")
        loop.run_until_complete(assistant.shutdown())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

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
