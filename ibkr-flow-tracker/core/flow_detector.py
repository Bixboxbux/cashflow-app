"""
Institutional Flow Tracker - Flow Detector Module

Detects unusual options activity including:
- Whale trades (large premium)
- Sweep orders (multi-exchange rapid execution)
- Block trades (single large transactions)
- Unusual volume patterns

This module processes real-time trade data and identifies
significant institutional activity.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable, Set
from collections import defaultdict
from dataclasses import dataclass, field
import threading

from config import (
    CONFIG,
    PREMIUM_THRESHOLDS,
    VOLUME_THRESHOLDS,
    SWEEP_THRESHOLDS,
)
from models import (
    OptionTrade, OptionQuote, OptionContract, SweepOrder,
    FlowSignal, FlowMetrics, OptionDetails,
)
from config.thresholds import SignalType, FlowDirection


logger = logging.getLogger(__name__)


@dataclass
class TradeBuffer:
    """Buffer for collecting trades for sweep detection."""
    trades: List[OptionTrade] = field(default_factory=list)
    last_update: datetime = field(default_factory=datetime.now)

    def add(self, trade: OptionTrade):
        """Add trade to buffer."""
        self.trades.append(trade)
        self.last_update = datetime.now()

    def get_recent(self, window_ms: int) -> List[OptionTrade]:
        """Get trades within time window."""
        cutoff = datetime.now() - timedelta(milliseconds=window_ms)
        return [t for t in self.trades if t.timestamp >= cutoff]

    def clean_old(self, max_age_seconds: int = 60):
        """Remove trades older than max age."""
        cutoff = datetime.now() - timedelta(seconds=max_age_seconds)
        self.trades = [t for t in self.trades if t.timestamp >= cutoff]


@dataclass
class VolumeTracker:
    """Tracks historical volume for comparison."""
    symbol: str
    daily_volumes: Dict[str, int] = field(default_factory=dict)  # date -> volume
    avg_volume: int = 0
    total_today: int = 0

    def update(self, volume: int):
        """Update today's volume."""
        today = datetime.now().strftime('%Y-%m-%d')
        self.daily_volumes[today] = self.daily_volumes.get(today, 0) + volume
        self.total_today = self.daily_volumes[today]

    def calculate_average(self, days: int = 20):
        """Calculate average daily volume."""
        volumes = list(self.daily_volumes.values())[-days:]
        if volumes:
            self.avg_volume = sum(volumes) // len(volumes)
        return self.avg_volume


class FlowDetector:
    """
    Real-time options flow detector.

    Monitors trade activity and identifies:
    1. Whale trades (premium > threshold)
    2. Sweep orders (rapid multi-exchange execution)
    3. Block trades (single large transactions)
    4. Unusual volume (vs historical average)

    Usage:
        detector = FlowDetector()
        detector.on_signal(callback_function)
        detector.process_trade(trade)
    """

    def __init__(self):
        """Initialize the flow detector."""
        # Trade buffers by contract key
        self._trade_buffers: Dict[str, TradeBuffer] = defaultdict(TradeBuffer)

        # Volume tracking by symbol
        self._volume_trackers: Dict[str, VolumeTracker] = {}

        # Open interest tracking
        self._oi_history: Dict[str, Dict[str, int]] = defaultdict(dict)

        # Detected sweeps (to avoid duplicates)
        self._detected_sweeps: Set[str] = set()

        # Callbacks for detected signals
        self._signal_callbacks: List[Callable] = []

        # Statistics
        self._stats = {
            "trades_processed": 0,
            "signals_detected": 0,
            "sweeps_detected": 0,
            "whales_detected": 0,
        }

        # Lock for thread safety
        self._lock = threading.Lock()

        logger.info("FlowDetector initialized")

    def on_signal(self, callback: Callable[[FlowSignal], None]):
        """Register callback for detected signals."""
        self._signal_callbacks.append(callback)

    def off_signal(self, callback: Callable):
        """Unregister callback."""
        if callback in self._signal_callbacks:
            self._signal_callbacks.remove(callback)

    def _emit_signal(self, signal: FlowSignal):
        """Emit signal to all registered callbacks."""
        self._stats["signals_detected"] += 1
        for callback in self._signal_callbacks:
            try:
                callback(signal)
            except Exception as e:
                logger.error(f"Error in signal callback: {e}")

    async def process_trade(self, trade: OptionTrade) -> Optional[FlowSignal]:
        """
        Process a single option trade.

        Checks for:
        1. Whale-level premium
        2. Part of a sweep order
        3. Unusual volume

        Args:
            trade: The option trade to process

        Returns:
            FlowSignal if significant activity detected
        """
        with self._lock:
            self._stats["trades_processed"] += 1

            # Update volume tracking
            self._update_volume_tracker(trade)

            # Add to trade buffer for sweep detection
            contract_key = self._get_contract_key(trade.contract)
            self._trade_buffers[contract_key].add(trade)

            # Clean old trades periodically
            if self._stats["trades_processed"] % 100 == 0:
                self._clean_old_buffers()

            # Check for whale trade
            if trade.premium >= PREMIUM_THRESHOLDS.TRACKING_MIN:
                signal = await self._process_whale_trade(trade)
                if signal:
                    return signal

            # Check for sweep
            sweep = self._detect_sweep(trade)
            if sweep:
                signal = await self._process_sweep(sweep)
                if signal:
                    return signal

            return None

    async def _process_whale_trade(self, trade: OptionTrade) -> Optional[FlowSignal]:
        """Process a potential whale trade."""
        premium_class = PREMIUM_THRESHOLDS.classify_premium(trade.premium)

        if premium_class == "IGNORED":
            return None

        logger.info(
            f"Whale detected: {trade.contract.underlying} "
            f"${trade.premium:,.0f} premium ({premium_class})"
        )

        self._stats["whales_detected"] += 1

        # Determine direction
        direction = FlowDirection.NEUTRAL
        if trade.contract.right.value == "C":
            direction = FlowDirection.BULLISH if trade.side == "BUY" else FlowDirection.BEARISH
        else:
            direction = FlowDirection.BEARISH if trade.side == "BUY" else FlowDirection.BULLISH

        # Create signal
        signal = FlowSignal(
            symbol=trade.contract.underlying,
            signal_type=SignalType.BLOCK if trade.size >= 100 else SignalType.INSTITUTIONAL_FLOW,
            direction=direction,
            underlying_price=trade.underlying_at_trade,
            price_target=self._calculate_target(trade),
            target_date=trade.contract.expiration,
            option=OptionDetails(
                contract_type=trade.contract.right.value,
                strike=trade.contract.strike,
                expiration=trade.contract.expiration,
                days_to_expiry=trade.contract.days_to_expiry,
                bid=trade.bid_at_trade,
                ask=trade.ask_at_trade,
                last=trade.price,
                mid=(trade.bid_at_trade + trade.ask_at_trade) / 2,
            ),
            metrics=FlowMetrics(
                premium_paid=trade.premium,
                contracts=trade.size,
                volume=trade.size,
                avg_volume=self._get_avg_volume(trade.contract.underlying),
                open_interest=0,
                prev_open_interest=0,
                premium_class=premium_class,
            ),
        )

        self._emit_signal(signal)
        return signal

    def _detect_sweep(self, trade: OptionTrade) -> Optional[SweepOrder]:
        """
        Detect if recent trades form a sweep order.

        A sweep is identified when:
        1. Multiple trades for same contract
        2. Within short time window (< 1 second)
        3. Across multiple exchanges
        """
        contract_key = self._get_contract_key(trade.contract)
        buffer = self._trade_buffers[contract_key]

        # Get recent trades
        recent = buffer.get_recent(SWEEP_THRESHOLDS.TIME_WINDOW_MS)

        if len(recent) < 2:
            return None

        # Check exchanges
        exchanges = set(t.exchange for t in recent if t.exchange)
        if len(exchanges) < SWEEP_THRESHOLDS.MIN_EXCHANGES:
            return None

        # Calculate total premium
        total_premium = sum(t.premium for t in recent)
        if total_premium < SWEEP_THRESHOLDS.MIN_SWEEP_PREMIUM:
            return None

        # Create sweep ID to avoid duplicates
        sweep_id = f"{contract_key}_{recent[0].timestamp.timestamp():.0f}"
        if sweep_id in self._detected_sweeps:
            return None

        self._detected_sweeps.add(sweep_id)

        logger.info(
            f"Sweep detected: {trade.contract.underlying} "
            f"${total_premium:,.0f} across {len(exchanges)} exchanges"
        )

        self._stats["sweeps_detected"] += 1

        return SweepOrder(
            id=sweep_id,
            timestamp=datetime.now(),
            contract=trade.contract,
            trades=recent.copy()
        )

    async def _process_sweep(self, sweep: SweepOrder) -> Optional[FlowSignal]:
        """Process a detected sweep order."""
        # Determine direction based on majority side
        buy_premium = sum(t.premium for t in sweep.trades if t.side == "BUY")
        sell_premium = sum(t.premium for t in sweep.trades if t.side == "SELL")

        if sweep.contract.right.value == "C":
            direction = FlowDirection.BULLISH if buy_premium > sell_premium else FlowDirection.BEARISH
        else:
            direction = FlowDirection.BEARISH if buy_premium > sell_premium else FlowDirection.BULLISH

        # Check for golden sweep
        underlying_price = sweep.trades[0].underlying_at_trade if sweep.trades else 0
        is_golden = SWEEP_THRESHOLDS.is_golden_sweep(
            sweep.total_premium,
            sweep.contract.strike,
            underlying_price
        )

        signal_type = SignalType.GOLDEN_SWEEP if is_golden else SignalType.SWEEP

        signal = FlowSignal(
            symbol=sweep.contract.underlying,
            signal_type=signal_type,
            direction=direction,
            underlying_price=underlying_price,
            price_target=self._calculate_target_from_sweep(sweep),
            target_date=sweep.contract.expiration,
            is_sweep=True,
            sweep_exchanges=sweep.exchanges_hit,
            option=OptionDetails(
                contract_type=sweep.contract.right.value,
                strike=sweep.contract.strike,
                expiration=sweep.contract.expiration,
                days_to_expiry=sweep.contract.days_to_expiry,
                last=sweep.avg_price,
                mid=sweep.avg_price,
            ),
            metrics=FlowMetrics(
                premium_paid=sweep.total_premium,
                contracts=sweep.total_contracts,
                volume=sweep.total_contracts,
                avg_volume=self._get_avg_volume(sweep.contract.underlying),
                open_interest=0,
                prev_open_interest=0,
                premium_class=PREMIUM_THRESHOLDS.classify_premium(sweep.total_premium),
            ),
        )

        self._emit_signal(signal)
        return signal

    def _calculate_target(self, trade: OptionTrade) -> float:
        """Calculate price target from a trade."""
        if trade.contract.right.value == "C":
            # Call: target = strike + premium paid per share
            premium_per_share = trade.price
            return trade.contract.strike + premium_per_share * 2
        else:
            # Put: target = strike - premium paid per share
            premium_per_share = trade.price
            return trade.contract.strike - premium_per_share * 2

    def _calculate_target_from_sweep(self, sweep: SweepOrder) -> float:
        """Calculate price target from a sweep."""
        if sweep.contract.right.value == "C":
            return sweep.contract.strike + sweep.avg_price * 2
        else:
            return sweep.contract.strike - sweep.avg_price * 2

    def _update_volume_tracker(self, trade: OptionTrade):
        """Update volume tracking for symbol."""
        symbol = trade.contract.underlying

        if symbol not in self._volume_trackers:
            self._volume_trackers[symbol] = VolumeTracker(symbol=symbol)

        self._volume_trackers[symbol].update(trade.size)

    def _get_avg_volume(self, symbol: str) -> int:
        """Get average daily volume for symbol."""
        if symbol in self._volume_trackers:
            return self._volume_trackers[symbol].avg_volume
        return 1000  # Default

    def _get_contract_key(self, contract: OptionContract) -> str:
        """Generate unique key for contract."""
        return f"{contract.underlying}_{contract.strike}_{contract.right.value}_{contract.expiration}"

    def _clean_old_buffers(self):
        """Clean old data from buffers."""
        for buffer in self._trade_buffers.values():
            buffer.clean_old(60)

        # Clean old sweep IDs
        # (in production, would use timestamp-based cleanup)
        if len(self._detected_sweeps) > 10000:
            self._detected_sweeps.clear()

    def get_stats(self) -> Dict:
        """Get detector statistics."""
        return self._stats.copy()

    async def analyze_option_chain(
        self,
        symbol: str,
        options: List[OptionQuote]
    ) -> List[FlowSignal]:
        """
        Analyze an options chain for unusual activity.

        This is used for batch analysis of options data.

        Args:
            symbol: Underlying symbol
            options: List of option quotes

        Returns:
            List of detected signals
        """
        signals = []

        for opt in options:
            # Check unusual volume
            if VOLUME_THRESHOLDS.is_unusual_volume(opt.volume, opt.avg_volume):
                signal = self._create_unusual_volume_signal(symbol, opt)
                if signal:
                    signals.append(signal)
                    self._emit_signal(signal)

            # Check unusual OI change
            if opt.oi_change_pct >= VOLUME_THRESHOLDS.UNUSUAL_OI_INCREASE * 100:
                signal = self._create_unusual_oi_signal(symbol, opt)
                if signal:
                    signals.append(signal)
                    self._emit_signal(signal)

        return signals

    def _create_unusual_volume_signal(
        self,
        symbol: str,
        opt: OptionQuote
    ) -> Optional[FlowSignal]:
        """Create signal for unusual volume."""
        if opt.volume < VOLUME_THRESHOLDS.MIN_VOLUME:
            return None

        volume_ratio = opt.volume / max(opt.avg_volume, 1)

        direction = FlowDirection.NEUTRAL
        if opt.contract:
            if opt.contract.right == OptionRight.CALL:
                direction = FlowDirection.BULLISH
            else:
                direction = FlowDirection.BEARISH

        return FlowSignal(
            symbol=symbol,
            signal_type=SignalType.UNUSUAL_VOLUME,
            direction=direction,
            underlying_price=opt.underlying_price,
            price_target=opt.contract.strike if opt.contract else 0,
            target_date=opt.contract.expiration if opt.contract else None,
            option=OptionDetails(
                contract_type=opt.contract.right.value if opt.contract else "C",
                strike=opt.contract.strike if opt.contract else 0,
                expiration=opt.contract.expiration if opt.contract else None,
                days_to_expiry=opt.contract.days_to_expiry if opt.contract else 0,
                bid=opt.bid,
                ask=opt.ask,
                last=opt.last,
                mid=opt.mid,
                delta=opt.delta,
                implied_volatility=opt.implied_volatility,
            ),
            metrics=FlowMetrics(
                premium_paid=opt.last * opt.volume * 100,
                contracts=opt.volume,
                volume=opt.volume,
                avg_volume=opt.avg_volume,
                open_interest=opt.open_interest,
                prev_open_interest=opt.prev_open_interest,
                volume_ratio=volume_ratio,
            ),
        )

    def _create_unusual_oi_signal(
        self,
        symbol: str,
        opt: OptionQuote
    ) -> Optional[FlowSignal]:
        """Create signal for unusual OI change."""
        if opt.open_interest < VOLUME_THRESHOLDS.MIN_OI:
            return None

        direction = FlowDirection.NEUTRAL
        if opt.contract:
            if opt.contract.right == OptionRight.CALL:
                direction = FlowDirection.BULLISH if opt.oi_change > 0 else FlowDirection.BEARISH
            else:
                direction = FlowDirection.BEARISH if opt.oi_change > 0 else FlowDirection.BULLISH

        return FlowSignal(
            symbol=symbol,
            signal_type=SignalType.UNUSUAL_OI,
            direction=direction,
            underlying_price=opt.underlying_price,
            price_target=opt.contract.strike if opt.contract else 0,
            target_date=opt.contract.expiration if opt.contract else None,
            option=OptionDetails(
                contract_type=opt.contract.right.value if opt.contract else "C",
                strike=opt.contract.strike if opt.contract else 0,
                expiration=opt.contract.expiration if opt.contract else None,
                days_to_expiry=opt.contract.days_to_expiry if opt.contract else 0,
                bid=opt.bid,
                ask=opt.ask,
                last=opt.last,
                mid=opt.mid,
                delta=opt.delta,
                implied_volatility=opt.implied_volatility,
            ),
            metrics=FlowMetrics(
                premium_paid=opt.last * opt.volume * 100,
                contracts=opt.volume,
                volume=opt.volume,
                avg_volume=opt.avg_volume,
                open_interest=opt.open_interest,
                prev_open_interest=opt.prev_open_interest,
                oi_change_pct=opt.oi_change_pct,
            ),
        )
