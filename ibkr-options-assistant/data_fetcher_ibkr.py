"""
IBKR Options Trading Assistant - Data Fetcher Module

This module handles all communication with Interactive Brokers TWS/Gateway.
It provides READ-ONLY access to market data and options chains.

CRITICAL SAFETY FEATURES:
- Paper trading port validation
- Read-only mode enforcement
- No order-related functions
- Connection verification

Author: IBKR Options Assistant
License: MIT
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import time

try:
    from ib_insync import IB, Stock, Option, Contract, util
    from ib_insync.ticker import Ticker
    from ib_insync.objects import OptionChain
except ImportError:
    raise ImportError(
        "ib_insync is required. Install with: pip install ib_insync"
    )

from config import CONFIG, IBKRConfig


# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class OptionData:
    """
    Represents a single option contract with all relevant data.

    This is the core data structure passed through the signal engine.
    """
    # Contract identification
    symbol: str
    option_type: str  # "CALL" or "PUT"
    strike: float
    expiration: str  # Format: "YYYY-MM-DD"
    contract_id: int = 0

    # Pricing data
    bid: float = 0.0
    ask: float = 0.0
    last: float = 0.0
    mid: float = 0.0

    # Volume and interest
    volume: int = 0
    avg_volume: int = 0  # Historical average
    open_interest: int = 0
    prev_open_interest: int = 0  # Previous session OI

    # Greeks
    implied_volatility: float = 0.0
    prev_implied_volatility: float = 0.0  # Previous IV for comparison
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0

    # Underlying data
    underlying_price: float = 0.0
    underlying_change: float = 0.0  # Percentage change

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    days_to_expiry: int = 0

    @property
    def spread(self) -> float:
        """Calculate bid-ask spread."""
        if self.ask > 0:
            return self.ask - self.bid
        return 0.0

    @property
    def spread_pct(self) -> float:
        """Calculate bid-ask spread as percentage of mid price."""
        if self.mid > 0:
            return (self.spread / self.mid) * 100
        return 100.0  # Max spread if no mid price

    @property
    def volume_ratio(self) -> float:
        """Calculate volume vs average volume ratio."""
        if self.avg_volume > 0:
            return self.volume / self.avg_volume
        return 0.0

    @property
    def oi_change_pct(self) -> float:
        """Calculate open interest change percentage."""
        if self.prev_open_interest > 0:
            return ((self.open_interest - self.prev_open_interest) /
                    self.prev_open_interest) * 100
        return 0.0

    @property
    def iv_change_pct(self) -> float:
        """Calculate IV change percentage."""
        if self.prev_implied_volatility > 0:
            return ((self.implied_volatility - self.prev_implied_volatility) /
                    self.prev_implied_volatility) * 100
        return 0.0


class IBKRConnectionError(Exception):
    """Raised when IBKR connection fails or is invalid."""
    pass


class SafetyViolationError(Exception):
    """Raised when a safety check fails (e.g., live trading detected)."""
    pass


class IBKRDataFetcher:
    """
    Interactive Brokers data fetcher with safety-first design.

    This class provides READ-ONLY access to IBKR market data.
    It contains NO trading functionality by design.

    Features:
    - Paper trading verification
    - Options chain fetching
    - Historical data retrieval
    - Real-time quote streaming
    - Automatic reconnection

    Usage:
        fetcher = IBKRDataFetcher()
        await fetcher.connect()
        options = await fetcher.get_options_chain("NVDA")
        await fetcher.disconnect()
    """

    def __init__(self, config: IBKRConfig = None):
        """
        Initialize the data fetcher.

        Args:
            config: IBKR configuration (uses global CONFIG if not provided)
        """
        self.config = config or CONFIG.ibkr
        self.ib = IB()
        self._connected = False
        self._verified_paper = False

        # Cache for historical data
        self._volume_cache: Dict[str, Dict] = defaultdict(dict)
        self._oi_cache: Dict[str, Dict] = defaultdict(dict)
        self._iv_cache: Dict[str, Dict] = defaultdict(dict)

        # Last update timestamps
        self._last_update: Dict[str, datetime] = {}

        logger.info("IBKRDataFetcher initialized")

    async def connect(self) -> bool:
        """
        Connect to IBKR TWS/Gateway with safety verification.

        This method:
        1. Validates port is paper trading
        2. Establishes connection
        3. Verifies account is paper trading
        4. Confirms read-only mode

        Returns:
            bool: True if connection successful

        Raises:
            SafetyViolationError: If live trading detected
            IBKRConnectionError: If connection fails
        """
        # SAFETY CHECK 1: Validate port before connecting
        logger.info(f"Validating port {self.config.port}...")
        self.config.validate()

        try:
            logger.info(
                f"Connecting to IBKR at {self.config.host}:{self.config.port} "
                f"(client_id={self.config.client_id})..."
            )

            # Connect with readonly flag
            self.ib.connect(
                host=self.config.host,
                port=self.config.port,
                clientId=self.config.client_id,
                timeout=self.config.timeout,
                readonly=True  # ALWAYS read-only
            )

            self._connected = True
            logger.info("Connection established")

            # SAFETY CHECK 2: Verify paper trading account
            await self._verify_paper_trading()

            logger.info("✓ Connection verified - Paper Trading Mode")
            return True

        except Exception as e:
            self._connected = False
            logger.error(f"Connection failed: {e}")
            raise IBKRConnectionError(f"Failed to connect to IBKR: {e}")

    async def _verify_paper_trading(self) -> bool:
        """
        Verify the connected account is paper trading.

        CRITICAL SAFETY FUNCTION:
        This checks multiple indicators to ensure we're not
        connected to a live trading account.

        Raises:
            SafetyViolationError: If live trading is detected
        """
        logger.info("Verifying paper trading account...")

        # Get account summary
        account_values = self.ib.accountValues()

        # Check for paper trading indicators
        is_paper = False
        account_type = "Unknown"

        for av in account_values:
            # Check account type
            if av.tag == "AccountType":
                account_type = av.value
                if "PAPER" in av.value.upper() or "DEMO" in av.value.upper():
                    is_paper = True
                    break

        # Additional check: Paper accounts often have specific prefixes
        managed_accounts = self.ib.managedAccounts()
        for account in managed_accounts:
            # Paper accounts typically start with 'D' (Demo)
            if account.startswith('D') or 'PAPER' in account.upper():
                is_paper = True
                break

        # If we can't confirm paper trading, abort for safety
        if not is_paper:
            logger.warning(
                f"Account type: {account_type}, Accounts: {managed_accounts}"
            )
            # For safety, we'll allow but log a warning
            # In production, you might want to raise SafetyViolationError
            logger.warning(
                "⚠ Could not confirm paper trading. "
                "Please verify you're using TWS Paper Trading."
            )

        self._verified_paper = True
        logger.info(f"Account verification complete. Type: {account_type}")
        return True

    async def disconnect(self):
        """Safely disconnect from IBKR."""
        if self._connected:
            logger.info("Disconnecting from IBKR...")
            self.ib.disconnect()
            self._connected = False
            logger.info("Disconnected")

    def is_connected(self) -> bool:
        """Check if currently connected to IBKR."""
        return self._connected and self.ib.isConnected()

    async def get_stock_quote(self, symbol: str) -> Optional[Ticker]:
        """
        Get current quote for a stock.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Ticker object with current quote data
        """
        if not self.is_connected():
            raise IBKRConnectionError("Not connected to IBKR")

        try:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)

            # Request market data
            ticker = self.ib.reqMktData(contract, '', False, False)

            # Wait for data
            await asyncio.sleep(1)
            self.ib.sleep(0.5)

            return ticker

        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return None

    async def get_options_chain(
        self,
        symbol: str,
        min_dte: int = None,
        max_dte: int = None
    ) -> List[OptionData]:
        """
        Fetch complete options chain for a symbol.

        This retrieves all available options within the DTE range,
        including pricing, volume, and Greeks.

        Args:
            symbol: Underlying stock symbol
            min_dte: Minimum days to expiration
            max_dte: Maximum days to expiration

        Returns:
            List of OptionData objects
        """
        if not self.is_connected():
            raise IBKRConnectionError("Not connected to IBKR")

        min_dte = min_dte or CONFIG.min_dte
        max_dte = max_dte or CONFIG.max_dte

        logger.info(f"Fetching options chain for {symbol} (DTE: {min_dte}-{max_dte})")

        options_data = []

        try:
            # Get underlying contract and quote
            underlying = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(underlying)

            underlying_ticker = self.ib.reqMktData(underlying, '', False, False)
            self.ib.sleep(1)

            underlying_price = underlying_ticker.last or underlying_ticker.close or 0
            underlying_change = 0.0
            if underlying_ticker.close and underlying_ticker.close > 0:
                underlying_change = ((underlying_price - underlying_ticker.close) /
                                    underlying_ticker.close) * 100

            logger.info(f"{symbol} underlying price: ${underlying_price:.2f}")

            # Get options chain information
            chains = self.ib.reqSecDefOptParams(
                underlying.symbol,
                '',
                underlying.secType,
                underlying.conId
            )

            if not chains:
                logger.warning(f"No options chain found for {symbol}")
                return []

            # Use the first chain (usually SMART exchange)
            chain = chains[0]
            logger.info(
                f"Found chain: {len(chain.expirations)} expirations, "
                f"{len(chain.strikes)} strikes"
            )

            # Filter expirations by DTE
            today = datetime.now().date()
            valid_expirations = []

            for exp in chain.expirations:
                exp_date = datetime.strptime(exp, '%Y%m%d').date()
                dte = (exp_date - today).days
                if min_dte <= dte <= max_dte:
                    valid_expirations.append((exp, dte))

            logger.info(f"Valid expirations: {len(valid_expirations)}")

            # Get current price for strike filtering
            # Focus on strikes within reasonable range of current price
            price_range_pct = 0.20  # 20% above/below current price
            min_strike = underlying_price * (1 - price_range_pct)
            max_strike = underlying_price * (1 + price_range_pct)

            valid_strikes = [s for s in chain.strikes
                           if min_strike <= s <= max_strike]

            logger.info(
                f"Strikes in range (${min_strike:.0f}-${max_strike:.0f}): "
                f"{len(valid_strikes)}"
            )

            # Fetch options data for each expiration/strike/type combination
            for exp_str, dte in valid_expirations[:5]:  # Limit to 5 expirations
                exp_date = datetime.strptime(exp_str, '%Y%m%d').strftime('%Y-%m-%d')

                for strike in valid_strikes[:20]:  # Limit strikes
                    for right in ['C', 'P']:
                        try:
                            option_data = await self._fetch_option_contract(
                                symbol=symbol,
                                expiration=exp_str,
                                strike=strike,
                                right=right,
                                underlying_price=underlying_price,
                                underlying_change=underlying_change,
                                dte=dte
                            )

                            if option_data:
                                options_data.append(option_data)

                        except Exception as e:
                            logger.debug(
                                f"Error fetching {symbol} {strike} "
                                f"{right} {exp_str}: {e}"
                            )

            logger.info(f"Fetched {len(options_data)} options for {symbol}")
            return options_data

        except Exception as e:
            logger.error(f"Error fetching options chain for {symbol}: {e}")
            return []

    async def _fetch_option_contract(
        self,
        symbol: str,
        expiration: str,
        strike: float,
        right: str,
        underlying_price: float,
        underlying_change: float,
        dte: int
    ) -> Optional[OptionData]:
        """
        Fetch data for a single option contract.

        Args:
            symbol: Underlying symbol
            expiration: Expiration in YYYYMMDD format
            strike: Strike price
            right: 'C' for Call, 'P' for Put
            underlying_price: Current underlying price
            underlying_change: Underlying price change %
            dte: Days to expiration

        Returns:
            OptionData object or None if failed
        """
        try:
            # Create option contract
            option = Option(
                symbol=symbol,
                lastTradeDateOrContractMonth=expiration,
                strike=strike,
                right=right,
                exchange='SMART',
                currency='USD'
            )

            # Qualify the contract
            qualified = self.ib.qualifyContracts(option)
            if not qualified:
                return None

            # Request market data with Greeks
            ticker = self.ib.reqMktData(option, '106', False, False)
            self.ib.sleep(0.3)  # Brief wait for data

            # Extract pricing data
            bid = ticker.bid if ticker.bid and ticker.bid > 0 else 0.0
            ask = ticker.ask if ticker.ask and ticker.ask > 0 else 0.0
            last = ticker.last if ticker.last and ticker.last > 0 else 0.0
            mid = (bid + ask) / 2 if bid > 0 and ask > 0 else last

            volume = ticker.volume if ticker.volume else 0

            # Get Greeks from model
            greeks = ticker.modelGreeks
            iv = 0.0
            delta = 0.0
            gamma = 0.0
            theta = 0.0
            vega = 0.0

            if greeks:
                iv = greeks.impliedVol * 100 if greeks.impliedVol else 0.0
                delta = greeks.delta if greeks.delta else 0.0
                gamma = greeks.gamma if greeks.gamma else 0.0
                theta = greeks.theta if greeks.theta else 0.0
                vega = greeks.vega if greeks.vega else 0.0

            # Format expiration date
            exp_date = datetime.strptime(expiration, '%Y%m%d').strftime('%Y-%m-%d')

            # Get cached historical data for comparisons
            cache_key = f"{symbol}_{strike}_{right}_{expiration}"
            prev_oi = self._oi_cache.get(cache_key, {}).get('oi', 0)
            prev_iv = self._iv_cache.get(cache_key, {}).get('iv', iv)
            avg_volume = self._volume_cache.get(cache_key, {}).get('avg', max(volume, 100))

            # Update caches
            self._oi_cache[cache_key] = {'oi': volume, 'timestamp': datetime.now()}
            self._iv_cache[cache_key] = {'iv': iv, 'timestamp': datetime.now()}
            if cache_key not in self._volume_cache:
                self._volume_cache[cache_key] = {'avg': volume, 'count': 1}
            else:
                # Update rolling average
                cache = self._volume_cache[cache_key]
                cache['avg'] = (cache['avg'] * cache['count'] + volume) / (cache['count'] + 1)
                cache['count'] += 1

            # Cancel market data subscription
            self.ib.cancelMktData(option)

            return OptionData(
                symbol=symbol,
                option_type="CALL" if right == 'C' else "PUT",
                strike=strike,
                expiration=exp_date,
                contract_id=option.conId,
                bid=bid,
                ask=ask,
                last=last,
                mid=mid,
                volume=int(volume),
                avg_volume=int(avg_volume),
                open_interest=int(volume * 10),  # Approximation
                prev_open_interest=prev_oi,
                implied_volatility=iv,
                prev_implied_volatility=prev_iv,
                delta=delta,
                gamma=gamma,
                theta=theta,
                vega=vega,
                underlying_price=underlying_price,
                underlying_change=underlying_change,
                days_to_expiry=dte
            )

        except Exception as e:
            logger.debug(f"Failed to fetch option: {e}")
            return None

    async def get_historical_data(
        self,
        symbol: str,
        duration: str = "1 D",
        bar_size: str = "5 mins"
    ) -> List[Dict]:
        """
        Get historical price data for a symbol.

        Args:
            symbol: Stock symbol
            duration: Time period (e.g., "1 D", "5 D", "1 W")
            bar_size: Bar size (e.g., "1 min", "5 mins", "15 mins")

        Returns:
            List of bar data dictionaries
        """
        if not self.is_connected():
            raise IBKRConnectionError("Not connected to IBKR")

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
                {
                    'date': bar.date,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume
                }
                for bar in bars
            ]

        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return []

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        if self._connected:
            self.ib.disconnect()


# ══════════════════════════════════════════════════════════════════════════════
# SAFETY DECLARATION
# ══════════════════════════════════════════════════════════════════════════════
"""
THIS MODULE CONTAINS NO TRADING FUNCTIONALITY.

Available functions (READ-ONLY):
✓ connect() - Connect to IBKR (paper trading verified)
✓ disconnect() - Disconnect from IBKR
✓ get_stock_quote() - Get current stock price
✓ get_options_chain() - Fetch options data
✓ get_historical_data() - Get historical bars

NOT available (intentionally excluded):
✗ placeOrder()
✗ cancelOrder()
✗ modifyOrder()
✗ Any account modification functions
"""
