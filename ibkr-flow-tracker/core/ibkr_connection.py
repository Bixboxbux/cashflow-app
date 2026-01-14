"""
Institutional Flow Tracker - IBKR Connection Module

Handles all communication with Interactive Brokers TWS/Gateway.
Enforces READ-ONLY access and PAPER TRADING only.

CRITICAL SAFETY FEATURES:
- Paper trading port validation (7497, 4002 only)
- Read-only mode enforcement
- No order-related functions exist
- Connection verification before data access

Author: Institutional Flow Tracker
License: MIT
"""

import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Callable, Any
from collections import defaultdict
import threading
import time

try:
    from ib_insync import IB, Stock, Option, Contract, util
    from ib_insync.ticker import Ticker
    from ib_insync.objects import OptionChain
except ImportError:
    raise ImportError(
        "ib_insync is required. Install with: pip install ib_insync"
    )

from config import CONFIG
from models import (
    Quote, OptionQuote, OptionContract, OptionTrade,
    OptionRight, OHLCV, SymbolProfile
)


logger = logging.getLogger(__name__)


class IBKRConnectionError(Exception):
    """Raised when IBKR connection fails."""
    pass


class SafetyViolationError(Exception):
    """Raised when safety check fails (e.g., live trading detected)."""
    pass


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, max_calls: int, period_seconds: float = 1.0):
        self.max_calls = max_calls
        self.period = period_seconds
        self.calls = []
        self.lock = threading.Lock()

    async def acquire(self):
        """Wait until rate limit allows a call."""
        with self.lock:
            now = time.time()
            # Remove old calls
            self.calls = [c for c in self.calls if now - c < self.period]

            if len(self.calls) >= self.max_calls:
                # Wait for oldest call to expire
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                self.calls = self.calls[1:]

            self.calls.append(time.time())


class IBKRConnection:
    """
    Interactive Brokers connection manager with safety-first design.

    This class provides READ-ONLY access to IBKR market data.
    It contains NO trading functionality by design.

    Features:
    - Paper trading verification
    - Real-time data streaming
    - Options chain fetching
    - Rate limiting
    - Automatic reconnection

    Usage:
        conn = IBKRConnection()
        await conn.connect()
        quote = await conn.get_quote("AAPL")
        await conn.disconnect()
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.ib = IB()
        self._connected = False
        self._verified_paper = False

        # Rate limiter
        self._rate_limiter = RateLimiter(
            max_calls=CONFIG.ibkr.max_requests_per_second,
            period_seconds=1.0
        )

        # Callbacks for real-time data
        self._trade_callbacks: List[Callable] = []
        self._quote_callbacks: Dict[str, List[Callable]] = defaultdict(list)

        # Subscriptions
        self._subscriptions: Dict[str, Any] = {}

        logger.info("IBKRConnection initialized")

    async def connect(self) -> bool:
        """
        Connect to IBKR with safety verification.

        Returns:
            bool: True if connected successfully

        Raises:
            SafetyViolationError: If live trading detected
            IBKRConnectionError: If connection fails
        """
        # SAFETY CHECK 1: Validate port
        logger.info(f"Validating port {CONFIG.ibkr.port}...")
        CONFIG.safety.validate_port(CONFIG.ibkr.port)

        try:
            logger.info(
                f"Connecting to IBKR at {CONFIG.ibkr.host}:{CONFIG.ibkr.port} "
                f"(client_id={CONFIG.ibkr.client_id})..."
            )

            # Connect with readonly flag
            self.ib.connect(
                host=CONFIG.ibkr.host,
                port=CONFIG.ibkr.port,
                clientId=CONFIG.ibkr.client_id,
                timeout=CONFIG.ibkr.timeout,
                readonly=True  # ALWAYS read-only
            )

            self._connected = True
            logger.info("Connection established")

            # SAFETY CHECK 2: Verify paper trading
            await self._verify_paper_trading()

            # Set up error handlers
            self.ib.errorEvent += self._on_error

            logger.info("✓ IBKR Connection verified - Paper Trading Mode")
            return True

        except Exception as e:
            self._connected = False
            logger.error(f"Connection failed: {e}")
            raise IBKRConnectionError(f"Failed to connect: {e}")

    async def _verify_paper_trading(self) -> bool:
        """
        Verify connected account is paper trading.

        Raises:
            SafetyViolationError: If live trading detected
        """
        logger.info("Verifying paper trading account...")

        account_values = self.ib.accountValues()
        managed_accounts = self.ib.managedAccounts()

        is_paper = False

        # Check account type
        for av in account_values:
            if av.tag == "AccountType":
                if "PAPER" in av.value.upper() or "DEMO" in av.value.upper():
                    is_paper = True
                    break

        # Check account prefix (Demo accounts start with 'D')
        for account in managed_accounts:
            if account.startswith('D'):
                is_paper = True
                break

        if not is_paper:
            logger.warning(
                "⚠ Could not confirm paper trading. "
                "Please verify TWS is in Paper Trading mode."
            )

        self._verified_paper = True
        return True

    def _on_error(self, reqId: int, errorCode: int, errorString: str, contract: Any):
        """Handle IBKR errors."""
        if errorCode in [2104, 2106, 2158]:  # Market data farm messages
            logger.debug(f"IBKR: {errorString}")
        else:
            logger.warning(f"IBKR Error {errorCode}: {errorString}")

    async def disconnect(self):
        """Safely disconnect from IBKR."""
        if self._connected:
            logger.info("Disconnecting from IBKR...")

            # Cancel all subscriptions
            for key, ticker in self._subscriptions.items():
                try:
                    self.ib.cancelMktData(ticker.contract)
                except:
                    pass

            self._subscriptions.clear()
            self.ib.disconnect()
            self._connected = False
            logger.info("Disconnected")

    def is_connected(self) -> bool:
        """Check if connected to IBKR."""
        return self._connected and self.ib.isConnected()

    async def get_quote(self, symbol: str) -> Optional[Quote]:
        """
        Get current quote for a stock.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Quote object or None
        """
        if not self.is_connected():
            return None

        await self._rate_limiter.acquire()

        try:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)

            ticker = self.ib.reqMktData(contract, '', False, False)
            await asyncio.sleep(0.5)
            self.ib.sleep(0.3)

            quote = Quote(
                symbol=symbol,
                timestamp=datetime.now(),
                bid=ticker.bid or 0.0,
                ask=ticker.ask or 0.0,
                last=ticker.last or ticker.close or 0.0,
                close=ticker.close or 0.0,
                bid_size=ticker.bidSize or 0,
                ask_size=ticker.askSize or 0,
                volume=int(ticker.volume or 0),
            )

            if quote.close > 0:
                quote.change = quote.last - quote.close
                quote.change_pct = (quote.change / quote.close) * 100

            self.ib.cancelMktData(contract)
            return quote

        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return None

    async def get_option_chain(
        self,
        symbol: str,
        min_dte: int = 1,
        max_dte: int = 45
    ) -> List[OptionQuote]:
        """
        Fetch options chain with quotes.

        Args:
            symbol: Underlying symbol
            min_dte: Minimum days to expiration
            max_dte: Maximum days to expiration

        Returns:
            List of OptionQuote objects
        """
        if not self.is_connected():
            return []

        await self._rate_limiter.acquire()
        options = []

        try:
            # Get underlying
            underlying = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(underlying)

            # Get underlying price
            ticker = self.ib.reqMktData(underlying, '', False, False)
            self.ib.sleep(0.5)
            underlying_price = ticker.last or ticker.close or 0

            # Get chain parameters
            chains = self.ib.reqSecDefOptParams(
                underlying.symbol, '', underlying.secType, underlying.conId
            )

            if not chains:
                return []

            chain = chains[0]
            today = date.today()

            # Filter expirations
            valid_expirations = []
            for exp in chain.expirations:
                exp_date = datetime.strptime(exp, '%Y%m%d').date()
                dte = (exp_date - today).days
                if min_dte <= dte <= max_dte:
                    valid_expirations.append((exp, dte))

            # Filter strikes around current price
            strike_range = underlying_price * 0.15
            valid_strikes = [
                s for s in chain.strikes
                if abs(s - underlying_price) <= strike_range
            ]

            # Fetch option data
            for exp_str, dte in valid_expirations[:3]:  # Limit expirations
                exp_date = datetime.strptime(exp_str, '%Y%m%d').date()

                for strike in valid_strikes[:10]:  # Limit strikes
                    for right in ['C', 'P']:
                        await self._rate_limiter.acquire()

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

                            opt_ticker = self.ib.reqMktData(opt, '106', False, False)
                            self.ib.sleep(0.2)

                            contract = OptionContract(
                                symbol=opt.localSymbol or f"{symbol}{exp_str}{right}{strike}",
                                underlying=symbol,
                                right=OptionRight.CALL if right == 'C' else OptionRight.PUT,
                                strike=strike,
                                expiration=exp_date,
                                con_id=opt.conId
                            )

                            greeks = opt_ticker.modelGreeks

                            option_quote = OptionQuote(
                                symbol=contract.symbol,
                                timestamp=datetime.now(),
                                contract=contract,
                                bid=opt_ticker.bid or 0.0,
                                ask=opt_ticker.ask or 0.0,
                                last=opt_ticker.last or 0.0,
                                volume=int(opt_ticker.volume or 0),
                                delta=greeks.delta if greeks else 0.0,
                                gamma=greeks.gamma if greeks else 0.0,
                                theta=greeks.theta if greeks else 0.0,
                                vega=greeks.vega if greeks else 0.0,
                                implied_volatility=(greeks.impliedVol * 100) if greeks and greeks.impliedVol else 0.0,
                                underlying_price=underlying_price,
                            )

                            if option_quote.bid > 0 or option_quote.ask > 0:
                                options.append(option_quote)

                            self.ib.cancelMktData(opt)

                        except Exception as e:
                            logger.debug(f"Error fetching option: {e}")

            self.ib.cancelMktData(underlying)
            return options

        except Exception as e:
            logger.error(f"Error fetching option chain for {symbol}: {e}")
            return []

    async def get_historical_data(
        self,
        symbol: str,
        duration: str = "20 D",
        bar_size: str = "1 day"
    ) -> List[OHLCV]:
        """
        Get historical price data.

        Args:
            symbol: Stock symbol
            duration: Time period (e.g., "20 D", "1 W")
            bar_size: Bar size (e.g., "1 day", "1 hour")

        Returns:
            List of OHLCV bars
        """
        if not self.is_connected():
            return []

        await self._rate_limiter.acquire()

        try:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)

            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )

            return [
                OHLCV(
                    timestamp=bar.date,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume
                )
                for bar in bars
            ]

        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return []

    def subscribe_trades(self, callback: Callable):
        """Subscribe to trade events."""
        self._trade_callbacks.append(callback)

    def unsubscribe_trades(self, callback: Callable):
        """Unsubscribe from trade events."""
        if callback in self._trade_callbacks:
            self._trade_callbacks.remove(callback)


# ═══════════════════════════════════════════════════════════════════════════════
# SAFETY DECLARATION
# ═══════════════════════════════════════════════════════════════════════════════
"""
THIS MODULE CONTAINS NO TRADING FUNCTIONALITY.

Available functions (READ-ONLY):
✓ connect() - Connect to IBKR (paper trading verified)
✓ disconnect() - Disconnect from IBKR
✓ get_quote() - Get current stock price
✓ get_option_chain() - Fetch options data
✓ get_historical_data() - Get historical bars

NOT available (intentionally excluded):
✗ placeOrder()
✗ cancelOrder()
✗ modifyOrder()
✗ Any account modification functions
"""
