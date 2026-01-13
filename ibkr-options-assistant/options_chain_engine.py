"""
IBKR Options Trading Assistant - Options Chain Engine

This module processes and manages options chain data.
It provides filtering, sorting, and analysis capabilities
to prepare data for signal detection.

Features:
- Options chain aggregation
- Liquidity filtering
- Strike grouping
- Expiration analysis
- Real-time updates

Author: IBKR Options Assistant
License: MIT
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import statistics

from data_fetcher_ibkr import OptionData, IBKRDataFetcher
from config import CONFIG


# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class OptionsChainSummary:
    """
    Summary statistics for an options chain.

    Provides aggregate metrics across all options for a symbol.
    """
    symbol: str
    underlying_price: float
    timestamp: datetime

    # Volume statistics
    total_call_volume: int = 0
    total_put_volume: int = 0
    put_call_volume_ratio: float = 0.0

    # Open interest statistics
    total_call_oi: int = 0
    total_put_oi: int = 0
    put_call_oi_ratio: float = 0.0

    # IV statistics
    avg_call_iv: float = 0.0
    avg_put_iv: float = 0.0
    iv_skew: float = 0.0  # Put IV - Call IV

    # Count of options
    total_calls: int = 0
    total_puts: int = 0

    # Expiration spread
    nearest_expiry_days: int = 0
    farthest_expiry_days: int = 0

    @property
    def total_volume(self) -> int:
        """Total volume across calls and puts."""
        return self.total_call_volume + self.total_put_volume

    @property
    def total_oi(self) -> int:
        """Total open interest across calls and puts."""
        return self.total_call_oi + self.total_put_oi


@dataclass
class StrikeAnalysis:
    """
    Analysis for a specific strike price.

    Groups call and put data for the same strike.
    """
    strike: float
    underlying_price: float

    # Distance from underlying
    moneyness: float = 0.0  # (strike - underlying) / underlying
    is_itm_call: bool = False
    is_itm_put: bool = False

    # Call data
    call: Optional[OptionData] = None

    # Put data
    put: Optional[OptionData] = None

    @property
    def has_both(self) -> bool:
        """Check if both call and put exist for this strike."""
        return self.call is not None and self.put is not None

    @property
    def combined_volume(self) -> int:
        """Combined volume of call and put."""
        vol = 0
        if self.call:
            vol += self.call.volume
        if self.put:
            vol += self.put.volume
        return vol

    @property
    def straddle_price(self) -> float:
        """Calculate straddle price (call mid + put mid)."""
        if self.has_both:
            return self.call.mid + self.put.mid
        return 0.0


class OptionsChainEngine:
    """
    Options chain processing and analysis engine.

    This engine:
    1. Fetches options data from IBKR
    2. Filters based on liquidity and configuration
    3. Groups options by strike/expiration
    4. Calculates aggregate statistics
    5. Prepares data for signal detection

    Usage:
        engine = OptionsChainEngine(fetcher)
        chain = await engine.fetch_and_process("NVDA")
        summary = engine.get_summary("NVDA")
    """

    def __init__(self, fetcher: IBKRDataFetcher):
        """
        Initialize the options chain engine.

        Args:
            fetcher: IBKR data fetcher instance
        """
        self.fetcher = fetcher

        # Storage for processed chains
        self._chains: Dict[str, List[OptionData]] = {}
        self._summaries: Dict[str, OptionsChainSummary] = {}
        self._strike_analyses: Dict[str, Dict[float, StrikeAnalysis]] = {}

        # Update timestamps
        self._last_update: Dict[str, datetime] = {}

        logger.info("OptionsChainEngine initialized")

    async def fetch_and_process(
        self,
        symbol: str,
        force_refresh: bool = False
    ) -> List[OptionData]:
        """
        Fetch and process options chain for a symbol.

        This is the main entry point for chain processing.

        Args:
            symbol: Stock symbol
            force_refresh: Force refresh even if cached

        Returns:
            List of processed OptionData objects
        """
        # Check if we need to refresh
        last_update = self._last_update.get(symbol)
        if not force_refresh and last_update:
            age = (datetime.now() - last_update).seconds
            if age < CONFIG.ui.refresh_interval:
                logger.debug(f"{symbol} chain still fresh ({age}s old)")
                return self._chains.get(symbol, [])

        logger.info(f"Fetching options chain for {symbol}...")

        # Fetch raw data
        raw_options = await self.fetcher.get_options_chain(symbol)

        if not raw_options:
            logger.warning(f"No options data received for {symbol}")
            return []

        # Filter options
        filtered = self._filter_options(raw_options)

        # Store processed chain
        self._chains[symbol] = filtered
        self._last_update[symbol] = datetime.now()

        # Calculate summary
        self._summaries[symbol] = self._calculate_summary(symbol, filtered)

        # Analyze strikes
        self._strike_analyses[symbol] = self._analyze_strikes(filtered)

        logger.info(
            f"Processed {len(filtered)} options for {symbol} "
            f"(filtered from {len(raw_options)})"
        )

        return filtered

    def _filter_options(self, options: List[OptionData]) -> List[OptionData]:
        """
        Filter options based on liquidity and quality criteria.

        Filters applied:
        1. Minimum volume
        2. Minimum open interest
        3. Maximum bid-ask spread
        4. Valid pricing (bid > 0, ask > 0)

        Args:
            options: List of raw options

        Returns:
            Filtered list of options
        """
        filtered = []

        for opt in options:
            # Check minimum volume
            if opt.volume < CONFIG.signals.min_option_volume:
                continue

            # Check minimum open interest
            if opt.open_interest < CONFIG.signals.min_open_interest:
                continue

            # Check bid-ask spread
            if opt.spread_pct > CONFIG.signals.max_spread_pct:
                continue

            # Check valid pricing
            if opt.bid <= 0 or opt.ask <= 0:
                continue

            # Check valid IV
            if opt.implied_volatility <= 0 or opt.implied_volatility > 500:
                continue

            filtered.append(opt)

        return filtered

    def _calculate_summary(
        self,
        symbol: str,
        options: List[OptionData]
    ) -> OptionsChainSummary:
        """
        Calculate summary statistics for an options chain.

        Args:
            symbol: Stock symbol
            options: List of options

        Returns:
            OptionsChainSummary object
        """
        if not options:
            return OptionsChainSummary(
                symbol=symbol,
                underlying_price=0.0,
                timestamp=datetime.now()
            )

        underlying_price = options[0].underlying_price

        # Separate calls and puts
        calls = [o for o in options if o.option_type == "CALL"]
        puts = [o for o in options if o.option_type == "PUT"]

        # Volume totals
        total_call_volume = sum(c.volume for c in calls)
        total_put_volume = sum(p.volume for p in puts)
        pc_volume_ratio = (total_put_volume / total_call_volume
                         if total_call_volume > 0 else 0.0)

        # Open interest totals
        total_call_oi = sum(c.open_interest for c in calls)
        total_put_oi = sum(p.open_interest for p in puts)
        pc_oi_ratio = (total_put_oi / total_call_oi
                      if total_call_oi > 0 else 0.0)

        # IV averages (volume-weighted)
        avg_call_iv = 0.0
        avg_put_iv = 0.0

        if total_call_volume > 0:
            avg_call_iv = sum(c.implied_volatility * c.volume for c in calls) / total_call_volume
        if total_put_volume > 0:
            avg_put_iv = sum(p.implied_volatility * p.volume for p in puts) / total_put_volume

        iv_skew = avg_put_iv - avg_call_iv

        # Expiration range
        expirations = sorted(set(o.days_to_expiry for o in options))
        nearest_expiry = expirations[0] if expirations else 0
        farthest_expiry = expirations[-1] if expirations else 0

        return OptionsChainSummary(
            symbol=symbol,
            underlying_price=underlying_price,
            timestamp=datetime.now(),
            total_call_volume=total_call_volume,
            total_put_volume=total_put_volume,
            put_call_volume_ratio=pc_volume_ratio,
            total_call_oi=total_call_oi,
            total_put_oi=total_put_oi,
            put_call_oi_ratio=pc_oi_ratio,
            avg_call_iv=avg_call_iv,
            avg_put_iv=avg_put_iv,
            iv_skew=iv_skew,
            total_calls=len(calls),
            total_puts=len(puts),
            nearest_expiry_days=nearest_expiry,
            farthest_expiry_days=farthest_expiry
        )

    def _analyze_strikes(
        self,
        options: List[OptionData]
    ) -> Dict[float, StrikeAnalysis]:
        """
        Group and analyze options by strike price.

        Args:
            options: List of options

        Returns:
            Dictionary mapping strikes to StrikeAnalysis
        """
        if not options:
            return {}

        underlying_price = options[0].underlying_price
        analyses: Dict[float, StrikeAnalysis] = {}

        for opt in options:
            strike = opt.strike

            if strike not in analyses:
                moneyness = (strike - underlying_price) / underlying_price
                analyses[strike] = StrikeAnalysis(
                    strike=strike,
                    underlying_price=underlying_price,
                    moneyness=moneyness,
                    is_itm_call=strike < underlying_price,
                    is_itm_put=strike > underlying_price
                )

            if opt.option_type == "CALL":
                analyses[strike].call = opt
            else:
                analyses[strike].put = opt

        return analyses

    def get_chain(self, symbol: str) -> List[OptionData]:
        """
        Get cached options chain for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            List of OptionData or empty list
        """
        return self._chains.get(symbol, [])

    def get_summary(self, symbol: str) -> Optional[OptionsChainSummary]:
        """
        Get summary statistics for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            OptionsChainSummary or None
        """
        return self._summaries.get(symbol)

    def get_strike_analysis(
        self,
        symbol: str,
        strike: float = None
    ) -> Dict[float, StrikeAnalysis]:
        """
        Get strike analysis for a symbol.

        Args:
            symbol: Stock symbol
            strike: Optional specific strike to retrieve

        Returns:
            Dictionary of StrikeAnalysis or single analysis
        """
        analyses = self._strike_analyses.get(symbol, {})

        if strike is not None:
            return {strike: analyses.get(strike)} if strike in analyses else {}

        return analyses

    def get_atm_options(
        self,
        symbol: str,
        count: int = 5
    ) -> List[OptionData]:
        """
        Get at-the-money options (closest to underlying price).

        Args:
            symbol: Stock symbol
            count: Number of strikes to include (above + below ATM)

        Returns:
            List of ATM options
        """
        chain = self.get_chain(symbol)
        if not chain:
            return []

        underlying_price = chain[0].underlying_price

        # Sort by distance from ATM
        sorted_options = sorted(
            chain,
            key=lambda o: abs(o.strike - underlying_price)
        )

        # Get unique strikes closest to ATM
        seen_strikes = set()
        atm_options = []

        for opt in sorted_options:
            if opt.strike not in seen_strikes:
                seen_strikes.add(opt.strike)
                if len(seen_strikes) > count:
                    break
            atm_options.append(opt)

        return atm_options

    def get_highest_volume_options(
        self,
        symbol: str,
        count: int = 10
    ) -> List[OptionData]:
        """
        Get options with highest volume.

        Args:
            symbol: Stock symbol
            count: Number of options to return

        Returns:
            List of high-volume options
        """
        chain = self.get_chain(symbol)
        return sorted(chain, key=lambda o: o.volume, reverse=True)[:count]

    def get_highest_oi_options(
        self,
        symbol: str,
        count: int = 10
    ) -> List[OptionData]:
        """
        Get options with highest open interest.

        Args:
            symbol: Stock symbol
            count: Number of options to return

        Returns:
            List of high OI options
        """
        chain = self.get_chain(symbol)
        return sorted(chain, key=lambda o: o.open_interest, reverse=True)[:count]

    def get_by_expiration(
        self,
        symbol: str,
        expiration: str = None
    ) -> Dict[str, List[OptionData]]:
        """
        Group options by expiration date.

        Args:
            symbol: Stock symbol
            expiration: Optional specific expiration

        Returns:
            Dictionary mapping expiration to options
        """
        chain = self.get_chain(symbol)
        grouped: Dict[str, List[OptionData]] = defaultdict(list)

        for opt in chain:
            grouped[opt.expiration].append(opt)

        if expiration:
            return {expiration: grouped.get(expiration, [])}

        return dict(grouped)

    def filter_chain(
        self,
        symbol: str,
        option_type: str = None,
        min_volume: int = None,
        min_oi: int = None,
        min_iv: float = None,
        max_iv: float = None,
        min_delta: float = None,
        max_delta: float = None,
        min_dte: int = None,
        max_dte: int = None
    ) -> List[OptionData]:
        """
        Filter chain with custom criteria.

        Args:
            symbol: Stock symbol
            option_type: "CALL" or "PUT"
            min_volume: Minimum volume
            min_oi: Minimum open interest
            min_iv: Minimum implied volatility
            max_iv: Maximum implied volatility
            min_delta: Minimum delta
            max_delta: Maximum delta
            min_dte: Minimum days to expiry
            max_dte: Maximum days to expiry

        Returns:
            Filtered list of options
        """
        chain = self.get_chain(symbol)
        filtered = chain.copy()

        if option_type:
            filtered = [o for o in filtered if o.option_type == option_type]

        if min_volume is not None:
            filtered = [o for o in filtered if o.volume >= min_volume]

        if min_oi is not None:
            filtered = [o for o in filtered if o.open_interest >= min_oi]

        if min_iv is not None:
            filtered = [o for o in filtered if o.implied_volatility >= min_iv]

        if max_iv is not None:
            filtered = [o for o in filtered if o.implied_volatility <= max_iv]

        if min_delta is not None:
            filtered = [o for o in filtered if abs(o.delta) >= min_delta]

        if max_delta is not None:
            filtered = [o for o in filtered if abs(o.delta) <= max_delta]

        if min_dte is not None:
            filtered = [o for o in filtered if o.days_to_expiry >= min_dte]

        if max_dte is not None:
            filtered = [o for o in filtered if o.days_to_expiry <= max_dte]

        return filtered

    def get_chain_age(self, symbol: str) -> int:
        """
        Get age of cached chain in seconds.

        Args:
            symbol: Stock symbol

        Returns:
            Age in seconds or -1 if not cached
        """
        last_update = self._last_update.get(symbol)
        if not last_update:
            return -1
        return (datetime.now() - last_update).seconds

    def clear_cache(self, symbol: str = None):
        """
        Clear cached data.

        Args:
            symbol: Specific symbol to clear, or all if None
        """
        if symbol:
            self._chains.pop(symbol, None)
            self._summaries.pop(symbol, None)
            self._strike_analyses.pop(symbol, None)
            self._last_update.pop(symbol, None)
            logger.info(f"Cleared cache for {symbol}")
        else:
            self._chains.clear()
            self._summaries.clear()
            self._strike_analyses.clear()
            self._last_update.clear()
            logger.info("Cleared all cache")
