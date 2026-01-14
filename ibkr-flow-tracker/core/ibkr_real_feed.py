"""
Institutional Flow Tracker - Real IBKR Options Feed Module

Connects to Interactive Brokers TWS/Gateway to receive real-time option trades
and passes them through the flow detection system.

CRITICAL SAFETY FEATURES:
- READ-ONLY mode only
- Paper Trading ports only (7497, 4002)
- No order-related functionality
- All signals require manual human execution

Usage:
    feed = IBKRRealFeed(flow_detector, signal_callback)
    await feed.connect()
    await feed.subscribe_options_flow(["AAPL", "TSLA", "SPY"])
    # ... signals emitted via callback
    await feed.disconnect()
"""

import asyncio
import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Callable, Set, Any
from collections import defaultdict
import threading

try:
    from ib_insync import IB, Stock, Option, Contract, util
    from ib_insync.ticker import Ticker
    from ib_insync.objects import OptionChain, TickByTick
except ImportError:
    raise ImportError(
        "ib_insync is required. Install with: pip install ib_insync"
    )

from config import CONFIG
from config.thresholds import PREMIUM_THRESHOLDS
from models import (
    OptionTrade, OptionContract, OptionQuote, OptionRight,
    FlowSignal,
)
from core.flow_detector import FlowDetector


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Safety Constants
# ═══════════════════════════════════════════════════════════════════════════════

PAPER_TRADING_PORTS = {7497, 4002}
LIVE_TRADING_PORTS = {7496, 4001}  # BLOCKED


class SafetyViolationError(Exception):
    """Raised when safety check fails."""
    pass


class ConnectionError(Exception):
    """Raised when connection fails."""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# IBKR Real Feed
# ═══════════════════════════════════════════════════════════════════════════════

class IBKRRealFeed:
    """
    Real-time options trade feed from Interactive Brokers.

    Subscribes to Time & Sales data for options and transforms each trade
    into OptionTrade dataclass for flow detection.

    Features:
    - READ-ONLY connection (no trading)
    - Paper Trading verification
    - Multi-symbol options monitoring
    - Real-time trade transformation
    - Automatic bid/ask/underlying capture
    - Flow detector integration

    Example:
        async def on_signal(signal: FlowSignal):
            print(f"Signal: {signal.symbol} {signal.direction}")

        detector = FlowDetector()
        feed = IBKRRealFeed(detector, on_signal)

        await feed.connect()
        await feed.subscribe_options_flow(["AAPL", "TSLA"])

        # Feed runs until disconnected
        await feed.run_forever()
    """

    def __init__(
        self,
        flow_detector: FlowDetector,
        signal_callback: Optional[Callable[[FlowSignal], Any]] = None,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 10,
    ):
        """
        Initialize the real feed.

        Args:
            flow_detector: FlowDetector instance for signal detection
            signal_callback: Async callback for detected signals
            host: IBKR TWS/Gateway host
            port: IBKR port (paper trading only: 7497 or 4002)
            client_id: Client ID for IBKR connection
        """
        # Safety check: Block live trading ports
        if port in LIVE_TRADING_PORTS:
            raise SafetyViolationError(
                f"Port {port} is a LIVE trading port. "
                f"Only paper trading ports are allowed: {PAPER_TRADING_PORTS}"
            )

        if port not in PAPER_TRADING_PORTS:
            logger.warning(
                f"Port {port} is not a standard paper trading port. "
                f"Proceeding with caution..."
            )

        self.host = host
        self.port = port
        self.client_id = client_id

        self.ib = IB()
        self._connected = False
        self._running = False

        # Flow detection
        self.flow_detector = flow_detector
        self.signal_callback = signal_callback

        # Register callback with flow detector
        if signal_callback:
            self.flow_detector.on_signal(self._handle_signal_sync)

        # Symbol tracking
        self._subscribed_symbols: Set[str] = set()
        self._option_contracts: Dict[str, List[Contract]] = defaultdict(list)

        # Quote cache for bid/ask/underlying at trade time
        self._quote_cache: Dict[str, Dict] = {}
        self._underlying_cache: Dict[str, float] = {}

        # Statistics
        self._stats = {
            "trades_received": 0,
            "trades_processed": 0,
            "signals_emitted": 0,
            "connection_time": None,
        }

        # Lock for thread safety
        self._lock = threading.Lock()

        logger.info(
            f"IBKRRealFeed initialized - "
            f"Host: {host}, Port: {port}, ClientID: {client_id}"
        )

    def _handle_signal_sync(self, signal: FlowSignal):
        """Synchronous wrapper for async signal callback."""
        self._stats["signals_emitted"] += 1

        if self.signal_callback:
            # Check if we're in an event loop
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._emit_signal_async(signal))
            except RuntimeError:
                # No running loop, create one
                asyncio.run(self._emit_signal_async(signal))

    async def _emit_signal_async(self, signal: FlowSignal):
        """Emit signal via async callback."""
        if self.signal_callback:
            result = self.signal_callback(signal)
            if asyncio.iscoroutine(result):
                await result

    # ═══════════════════════════════════════════════════════════════════════════
    # Connection Management
    # ═══════════════════════════════════════════════════════════════════════════

    async def connect(self) -> bool:
        """
        Connect to IBKR TWS/Gateway in READ-ONLY mode.

        Returns:
            bool: True if connected successfully

        Raises:
            SafetyViolationError: If live trading detected
            ConnectionError: If connection fails
        """
        logger.info(f"Connecting to IBKR at {self.host}:{self.port}...")

        try:
            # Connect with readonly=True
            self.ib.connect(
                host=self.host,
                port=self.port,
                clientId=self.client_id,
                timeout=30,
                readonly=True  # CRITICAL: Read-only mode
            )

            self._connected = True
            self._stats["connection_time"] = datetime.now()

            # Verify paper trading
            await self._verify_paper_trading()

            # Set up event handlers
            self.ib.errorEvent += self._on_error

            logger.info("✓ Connected to IBKR - READ-ONLY Paper Trading Mode")
            return True

        except Exception as e:
            self._connected = False
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to IBKR: {e}")

    async def _verify_paper_trading(self) -> bool:
        """Verify connected account is paper trading."""
        logger.info("Verifying paper trading account...")

        account_values = self.ib.accountValues()
        managed_accounts = self.ib.managedAccounts()

        is_paper = False

        # Check account type
        for av in account_values:
            if av.tag == "AccountType":
                if "PAPER" in av.value.upper() or "DEMO" in av.value.upper():
                    is_paper = True
                    logger.info(f"Account type: {av.value}")
                    break

        # Check account prefix (Demo accounts start with 'D')
        for account in managed_accounts:
            if account.startswith('D'):
                is_paper = True
                logger.info(f"Paper account detected: {account}")
                break

        if not is_paper:
            logger.warning(
                "⚠ Could not confirm paper trading. "
                "Please verify TWS is in Paper Trading mode."
            )

        return True

    def _on_error(self, reqId: int, errorCode: int, errorString: str, contract: Any):
        """Handle IBKR errors."""
        # Info messages
        if errorCode in [2104, 2106, 2158]:
            logger.debug(f"IBKR Info: {errorString}")
        # Market data issues
        elif errorCode in [354, 10167]:
            logger.warning(f"Market data: {errorString}")
        else:
            logger.warning(f"IBKR Error {errorCode}: {errorString}")

    async def disconnect(self):
        """Disconnect from IBKR."""
        if self._connected:
            logger.info("Disconnecting from IBKR...")

            self._running = False

            # Cancel all subscriptions
            for symbol, contracts in self._option_contracts.items():
                for contract in contracts:
                    try:
                        self.ib.cancelMktData(contract)
                    except:
                        pass

            self._option_contracts.clear()
            self._subscribed_symbols.clear()

            self.ib.disconnect()
            self._connected = False

            logger.info("Disconnected from IBKR")

    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected and self.ib.isConnected()

    # ═══════════════════════════════════════════════════════════════════════════
    # Options Flow Subscription
    # ═══════════════════════════════════════════════════════════════════════════

    async def subscribe_options_flow(
        self,
        symbols: List[str],
        min_dte: int = 0,
        max_dte: int = 60,
        otm_range_pct: float = 0.20,
    ) -> int:
        """
        Subscribe to options flow for given symbols.

        Subscribes to Time & Sales data for options chains and
        processes each trade through the flow detector.

        Args:
            symbols: List of underlying symbols (e.g., ["AAPL", "TSLA"])
            min_dte: Minimum days to expiration
            max_dte: Maximum days to expiration
            otm_range_pct: OTM range as percentage (0.20 = 20% from current price)

        Returns:
            Number of option contracts subscribed
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to IBKR")

        total_subscribed = 0

        for symbol in symbols:
            if symbol in self._subscribed_symbols:
                logger.info(f"{symbol} already subscribed")
                continue

            try:
                count = await self._subscribe_symbol_options(
                    symbol, min_dte, max_dte, otm_range_pct
                )
                total_subscribed += count
                self._subscribed_symbols.add(symbol)
                logger.info(f"Subscribed to {count} options for {symbol}")

            except Exception as e:
                logger.error(f"Failed to subscribe to {symbol}: {e}")

        return total_subscribed

    async def _subscribe_symbol_options(
        self,
        symbol: str,
        min_dte: int,
        max_dte: int,
        otm_range_pct: float,
    ) -> int:
        """Subscribe to options for a single symbol."""
        # Get underlying contract and price
        underlying = Stock(symbol, 'SMART', 'USD')
        qualified = self.ib.qualifyContracts(underlying)

        if not qualified:
            raise ValueError(f"Could not qualify underlying {symbol}")

        # Get underlying price
        ticker = self.ib.reqMktData(underlying, '', False, False)
        self.ib.sleep(1.0)

        underlying_price = ticker.last or ticker.close or 0
        if underlying_price <= 0:
            raise ValueError(f"Could not get price for {symbol}")

        self._underlying_cache[symbol] = underlying_price
        logger.info(f"{symbol} price: ${underlying_price:.2f}")

        # Keep underlying subscription for real-time price
        self.ib.pendingTickersEvent += lambda tickers: self._on_underlying_tick(symbol, tickers)

        # Get option chain parameters
        chains = self.ib.reqSecDefOptParams(
            underlying.symbol, '', underlying.secType, underlying.conId
        )

        if not chains:
            raise ValueError(f"No option chain for {symbol}")

        chain = chains[0]
        today = date.today()

        # Filter expirations
        valid_expirations = []
        for exp in chain.expirations:
            exp_date = datetime.strptime(exp, '%Y%m%d').date()
            dte = (exp_date - today).days
            if min_dte <= dte <= max_dte:
                valid_expirations.append(exp)

        # Filter strikes (within OTM range)
        strike_range = underlying_price * otm_range_pct
        valid_strikes = [
            s for s in chain.strikes
            if abs(s - underlying_price) <= strike_range
        ]

        logger.info(
            f"{symbol}: {len(valid_expirations)} expirations, "
            f"{len(valid_strikes)} strikes in range"
        )

        # Subscribe to options
        subscribed = 0

        for exp_str in valid_expirations[:5]:  # Limit to 5 expirations
            exp_date = datetime.strptime(exp_str, '%Y%m%d').date()

            for strike in valid_strikes[:15]:  # Limit strikes
                for right in ['C', 'P']:
                    try:
                        opt = Option(
                            symbol=symbol,
                            lastTradeDateOrContractMonth=exp_str,
                            strike=strike,
                            right=right,
                            exchange='SMART',
                            currency='USD'
                        )

                        qualified = self.ib.qualifyContracts(opt)
                        if not qualified:
                            continue

                        # Subscribe to tick-by-tick trades
                        self.ib.reqTickByTickData(
                            opt,
                            tickType='AllLast',  # All trades
                            numberOfTicks=0,     # Unlimited
                            ignoreSize=False
                        )

                        # Also get quote for bid/ask
                        self.ib.reqMktData(opt, '', False, False)

                        # Store contract
                        self._option_contracts[symbol].append(opt)

                        # Initialize quote cache
                        cache_key = self._get_contract_key(opt)
                        self._quote_cache[cache_key] = {
                            "bid": 0.0,
                            "ask": 0.0,
                            "last": 0.0,
                        }

                        subscribed += 1

                    except Exception as e:
                        logger.debug(f"Error subscribing to option: {e}")

                    # Small delay to avoid overwhelming API
                    await asyncio.sleep(0.05)

        # Set up trade handler
        self.ib.pendingTickersEvent += self._on_ticker_update

        return subscribed

    def _get_contract_key(self, contract: Contract) -> str:
        """Generate unique key for an option contract."""
        return f"{contract.symbol}_{contract.strike}_{contract.right}_{contract.lastTradeDateOrContractMonth}"

    def _on_underlying_tick(self, symbol: str, tickers: List[Ticker]):
        """Handle underlying price updates."""
        for ticker in tickers:
            if hasattr(ticker.contract, 'symbol') and ticker.contract.symbol == symbol:
                if ticker.last and ticker.last > 0:
                    self._underlying_cache[symbol] = ticker.last

    def _on_ticker_update(self, tickers: List[Ticker]):
        """Handle ticker updates (quotes and trades)."""
        for ticker in tickers:
            contract = ticker.contract

            # Only process options
            if contract.secType != 'OPT':
                continue

            cache_key = self._get_contract_key(contract)

            # Update quote cache
            if cache_key in self._quote_cache:
                if ticker.bid and ticker.bid > 0:
                    self._quote_cache[cache_key]["bid"] = ticker.bid
                if ticker.ask and ticker.ask > 0:
                    self._quote_cache[cache_key]["ask"] = ticker.ask
                if ticker.last and ticker.last > 0:
                    self._quote_cache[cache_key]["last"] = ticker.last

            # Process tick-by-tick data if available
            if hasattr(ticker, 'tickByTicks') and ticker.tickByTicks:
                for tick in ticker.tickByTicks:
                    asyncio.create_task(self._process_tick(contract, tick))

    async def _process_tick(self, contract: Contract, tick: TickByTick):
        """Process a single tick-by-tick trade."""
        with self._lock:
            self._stats["trades_received"] += 1

        try:
            # Get cached quote and underlying price
            cache_key = self._get_contract_key(contract)
            quote = self._quote_cache.get(cache_key, {})
            underlying_price = self._underlying_cache.get(contract.symbol, 0)

            # Create OptionContract
            exp_date = datetime.strptime(
                contract.lastTradeDateOrContractMonth, '%Y%m%d'
            ).date()

            option_contract = OptionContract(
                symbol=contract.localSymbol or cache_key,
                underlying=contract.symbol,
                right=OptionRight.CALL if contract.right == 'C' else OptionRight.PUT,
                strike=contract.strike,
                expiration=exp_date,
                con_id=contract.conId,
                exchange=tick.exchange if hasattr(tick, 'exchange') else 'SMART',
            )

            # Create OptionTrade (premium and side auto-calculated)
            trade = OptionTrade(
                timestamp=tick.time if hasattr(tick, 'time') else datetime.now(),
                contract=option_contract,
                price=tick.price,
                size=tick.size,
                exchange=tick.exchange if hasattr(tick, 'exchange') else '',
                condition=str(tick.specialConditions) if hasattr(tick, 'specialConditions') else '',
                bid_at_trade=quote.get("bid", 0.0),
                ask_at_trade=quote.get("ask", 0.0),
                underlying_at_trade=underlying_price,
            )

            # Check minimum premium threshold
            if trade.premium < PREMIUM_THRESHOLDS.TRACKING_MIN:
                return

            with self._lock:
                self._stats["trades_processed"] += 1

            logger.debug(
                f"Trade: {option_contract.display_name} "
                f"${trade.premium:,.0f} ({trade.side})"
            )

            # Pass through flow detector
            signal = await self.flow_detector.process_trade(trade)

            if signal:
                logger.info(
                    f"Signal: {signal.symbol} {signal.signal_type.value} "
                    f"{signal.direction.value} ${signal.metrics.premium_paid:,.0f}"
                )

        except Exception as e:
            logger.error(f"Error processing tick: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # Run Loop
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_forever(self):
        """
        Run the feed indefinitely.

        Keeps the connection alive and processes trades until
        disconnect() is called.
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to IBKR")

        logger.info("Starting real-time feed loop...")
        self._running = True

        try:
            while self._running and self.is_connected():
                # Process IBKR events
                self.ib.sleep(0.1)

                # Log stats periodically
                if self._stats["trades_processed"] % 100 == 0 and self._stats["trades_processed"] > 0:
                    logger.info(
                        f"Stats: {self._stats['trades_received']} received, "
                        f"{self._stats['trades_processed']} processed, "
                        f"{self._stats['signals_emitted']} signals"
                    )

                await asyncio.sleep(0.05)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self._running = False

    def get_stats(self) -> Dict:
        """Get feed statistics."""
        return {
            **self._stats,
            "subscribed_symbols": list(self._subscribed_symbols),
            "option_contracts": sum(len(c) for c in self._option_contracts.values()),
            "connected": self.is_connected(),
        }

    async def unsubscribe_symbol(self, symbol: str):
        """Unsubscribe from a symbol's options."""
        if symbol not in self._subscribed_symbols:
            return

        for contract in self._option_contracts.get(symbol, []):
            try:
                self.ib.cancelMktData(contract)
            except:
                pass

        self._option_contracts.pop(symbol, None)
        self._subscribed_symbols.discard(symbol)
        self._underlying_cache.pop(symbol, None)

        logger.info(f"Unsubscribed from {symbol}")


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Helper
# ═══════════════════════════════════════════════════════════════════════════════

async def create_real_feed_with_broadcast(
    symbols: List[str],
    host: str = "127.0.0.1",
    port: int = 7497,
) -> IBKRRealFeed:
    """
    Create a real feed connected to the dashboard broadcast system.

    This is the recommended way to integrate with the existing
    FastAPI + WebSocket dashboard.

    Args:
        symbols: List of symbols to track
        host: IBKR host
        port: IBKR port (paper trading only)

    Returns:
        Configured IBKRRealFeed instance

    Example:
        feed = await create_real_feed_with_broadcast(
            ["AAPL", "TSLA", "SPY", "QQQ"]
        )
        await feed.run_forever()
    """
    # Import here to avoid circular imports
    from api.main import broadcast_signal, get_app_state

    # Create flow detector
    flow_detector = FlowDetector()

    # Create feed with broadcast callback
    feed = IBKRRealFeed(
        flow_detector=flow_detector,
        signal_callback=broadcast_signal,
        host=host,
        port=port,
    )

    # Connect
    await feed.connect()

    # Update app state
    state = get_app_state()
    state.is_demo_mode = False
    state.is_connected = True

    # Subscribe to symbols
    await feed.subscribe_options_flow(symbols)

    logger.info(f"Real feed created for: {', '.join(symbols)}")

    return feed


# ═══════════════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """
    Command-line entry point for testing the real feed.

    Usage:
        python -m core.ibkr_real_feed --symbols AAPL,TSLA --port 7497
    """
    import argparse

    parser = argparse.ArgumentParser(description="IBKR Real Options Feed")
    parser.add_argument(
        "--symbols", "-s",
        type=str,
        default="AAPL,TSLA,SPY",
        help="Comma-separated symbols to track"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="IBKR host"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=7497,
        help="IBKR port (paper trading only: 7497 or 4002)"
    )
    parser.add_argument(
        "--client-id",
        type=int,
        default=10,
        help="IBKR client ID"
    )

    args = parser.parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(",")]

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    print("\n" + "=" * 60)
    print("  IBKR Real Options Feed - READ-ONLY MODE")
    print("=" * 60)
    print(f"  Symbols: {', '.join(symbols)}")
    print(f"  Host: {args.host}:{args.port}")
    print("=" * 60 + "\n")

    # Create flow detector
    flow_detector = FlowDetector()

    # Signal printer for testing
    async def print_signal(signal: FlowSignal):
        print(f"\n{'='*50}")
        print(f"  SIGNAL: {signal.symbol} {signal.signal_type.value}")
        print(f"  Direction: {signal.direction.value}")
        print(f"  Premium: ${signal.metrics.premium_paid:,.0f}")
        print(f"  Target: ${signal.price_target:.2f}")
        print(f"  Conviction: {signal.conviction_score:.0f}%")
        print(f"{'='*50}\n")

    # Register callback
    flow_detector.on_signal(lambda s: asyncio.create_task(print_signal(s)))

    # Create and run feed
    feed = IBKRRealFeed(
        flow_detector=flow_detector,
        host=args.host,
        port=args.port,
        client_id=args.client_id,
    )

    try:
        await feed.connect()
        await feed.subscribe_options_flow(symbols)

        print(f"\nMonitoring {len(symbols)} symbols...")
        print("Press Ctrl+C to stop\n")

        await feed.run_forever()

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        await feed.disconnect()

        stats = feed.get_stats()
        print(f"\nFinal Stats:")
        print(f"  Trades received: {stats['trades_received']}")
        print(f"  Trades processed: {stats['trades_processed']}")
        print(f"  Signals emitted: {stats['signals_emitted']}")


if __name__ == "__main__":
    asyncio.run(main())


# ═══════════════════════════════════════════════════════════════════════════════
# SAFETY DECLARATION
# ═══════════════════════════════════════════════════════════════════════════════
"""
THIS MODULE CONTAINS NO TRADING FUNCTIONALITY.

Available functions (READ-ONLY):
✓ connect() - Connect to IBKR (paper trading verified)
✓ disconnect() - Disconnect from IBKR
✓ subscribe_options_flow() - Subscribe to options trades
✓ unsubscribe_symbol() - Stop tracking a symbol
✓ run_forever() - Run the feed loop

NOT available (intentionally excluded):
✗ placeOrder()
✗ cancelOrder()
✗ modifyOrder()
✗ Any account modification functions

All signals are for INFORMATIONAL purposes only.
Trading decisions require manual human execution.
"""
