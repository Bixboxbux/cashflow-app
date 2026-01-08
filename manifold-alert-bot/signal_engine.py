"""
signal_engine.py - Signal Detection Logic

This module implements the core detection algorithms for identifying
potentially informed trading activity on Manifold Markets.

Signal Types (priority order):
1. WHALE_BET - Large bets (≥5x market average)
2. NEW_ACCOUNT_LARGE_BET - New accounts (<7 days) placing above-average bets
3. SHARP_MOVEMENT - Rapid probability changes (≥10% in <5 min)
4. HIGH_SKILL_USER - Bets from users with strong track records
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of signals the engine can detect"""
    WHALE_BET = "WHALE_BET"
    NEW_ACCOUNT_LARGE_BET = "NEW_ACCOUNT_LARGE_BET"
    SHARP_MOVEMENT = "SHARP_MOVEMENT"
    HIGH_SKILL_USER = "HIGH_SKILL_USER"


@dataclass
class Alert:
    """Represents a detected alert"""
    signal_type: SignalType
    market_id: str
    market_name: str
    user_id: str
    username: str
    bet_amount: float
    prob_before: float
    prob_after: float
    timestamp: datetime
    bet_id: str
    details: dict = field(default_factory=dict)

    def __hash__(self):
        """Hash by bet_id and signal type to avoid duplicates"""
        return hash((self.bet_id, self.signal_type.value))

    def __eq__(self, other):
        if not isinstance(other, Alert):
            return False
        return self.bet_id == other.bet_id and self.signal_type == other.signal_type


class MarketStats:
    """
    Tracks statistics for a single market.
    Used to calculate rolling averages and detect anomalies.
    """
    def __init__(self, market_id: str, window_size: int = 50):
        self.market_id = market_id
        self.window_size = window_size
        self.bet_amounts: list[float] = []
        self.prob_history: list[tuple[datetime, float]] = []  # (timestamp, probability)
        self.last_updated: datetime = None

    def add_bet(self, amount: float, timestamp: datetime, prob_after: float):
        """Add a bet to the market statistics"""
        self.bet_amounts.append(amount)
        # Keep only the last window_size bets
        if len(self.bet_amounts) > self.window_size:
            self.bet_amounts = self.bet_amounts[-self.window_size:]

        self.prob_history.append((timestamp, prob_after))
        # Keep only recent probability history (last 10 minutes)
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
        self.prob_history = [(t, p) for t, p in self.prob_history if t > cutoff]

        self.last_updated = timestamp

    def get_average_bet(self) -> float:
        """Calculate average bet amount for this market"""
        if not self.bet_amounts:
            return 0.0
        return sum(self.bet_amounts) / len(self.bet_amounts)

    def get_prob_change(self, window_minutes: int = 5) -> Optional[tuple[float, float]]:
        """
        Get probability change within the specified time window.

        Returns:
            Tuple of (start_prob, end_prob) or None if insufficient data
        """
        if len(self.prob_history) < 2:
            return None

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        relevant = [(t, p) for t, p in self.prob_history if t >= cutoff]

        if len(relevant) < 2:
            return None

        return (relevant[0][1], relevant[-1][1])


class SignalEngine:
    """
    Main signal detection engine.

    Processes bets and detects various types of suspicious activity
    based on configurable thresholds.
    """

    def __init__(
        self,
        whale_threshold: float = 5.0,
        new_account_days: int = 7,
        sharp_movement_threshold: float = 0.10,
        sharp_movement_window: int = 5,
        min_bet_for_whale: float = 100,
        min_profit_for_skill: float = 500
    ):
        """
        Initialize the signal engine.

        Args:
            whale_threshold: Multiplier for whale detection (bet >= threshold * avg)
            new_account_days: Account age in days to be considered "new"
            sharp_movement_threshold: Min probability change for sharp movement (0.10 = 10%)
            sharp_movement_window: Time window in minutes for sharp movement detection
            min_bet_for_whale: Minimum absolute bet amount to trigger whale alert
            min_profit_for_skill: Minimum profit to consider user "high skill"
        """
        self.whale_threshold = whale_threshold
        self.new_account_days = new_account_days
        self.sharp_movement_threshold = sharp_movement_threshold
        self.sharp_movement_window = sharp_movement_window
        self.min_bet_for_whale = min_bet_for_whale
        self.min_profit_for_skill = min_profit_for_skill

        # State tracking
        self.market_stats: dict[str, MarketStats] = {}  # market_id -> MarketStats
        self.seen_alerts: set[tuple[str, str]] = set()  # (bet_id, signal_type)
        self.user_cache: dict[str, dict] = {}  # user_id -> user_data

    def _get_market_stats(self, market_id: str) -> MarketStats:
        """Get or create market stats tracker"""
        if market_id not in self.market_stats:
            self.market_stats[market_id] = MarketStats(market_id)
        return self.market_stats[market_id]

    def _is_alert_seen(self, bet_id: str, signal_type: SignalType) -> bool:
        """Check if we've already generated this alert"""
        key = (bet_id, signal_type.value)
        return key in self.seen_alerts

    def _mark_alert_seen(self, bet_id: str, signal_type: SignalType):
        """Mark an alert as seen to avoid duplicates"""
        key = (bet_id, signal_type.value)
        self.seen_alerts.add(key)

        # Cleanup: Remove old entries if set gets too large
        if len(self.seen_alerts) > 10000:
            # Keep only recent alerts (this is a simple cleanup strategy)
            self.seen_alerts = set(list(self.seen_alerts)[-5000:])

    def _is_new_account(self, user_data: dict) -> bool:
        """Check if user account was created recently"""
        if not user_data:
            return False

        created_time = user_data.get("createdTime")
        if not created_time:
            return False

        created_dt = datetime.fromtimestamp(created_time / 1000, tz=timezone.utc)
        age = datetime.now(timezone.utc) - created_dt
        return age.days < self.new_account_days

    def _is_high_skill_user(self, user_data: dict) -> tuple[bool, dict]:
        """
        Check if user has a strong track record.

        Returns:
            Tuple of (is_high_skill, details_dict)
        """
        if not user_data:
            return False, {}

        details = {}

        # Check profit metrics
        profit = user_data.get("profitCached", {})
        all_time_profit = profit.get("allTime", 0) if isinstance(profit, dict) else 0

        # Check balance (high balance often indicates successful trading)
        balance = user_data.get("balance", 0)

        # Check if user has creator earnings (indicates active/known user)
        creator_earnings = user_data.get("creatorTraders", {})
        if isinstance(creator_earnings, dict):
            total_traders = creator_earnings.get("allTime", 0)
        else:
            total_traders = 0

        details = {
            "all_time_profit": all_time_profit,
            "balance": balance,
            "total_traders": total_traders
        }

        # User is "high skill" if they have significant profit
        is_high_skill = all_time_profit >= self.min_profit_for_skill

        return is_high_skill, details

    def process_bet(
        self,
        bet: dict,
        market: dict,
        user_data: Optional[dict] = None
    ) -> list[Alert]:
        """
        Process a single bet and check for signals.

        Args:
            bet: Bet object from API
            market: Market object from API
            user_data: User object from API (optional, will be used if provided)

        Returns:
            List of Alert objects (may be empty)
        """
        alerts = []

        # Extract bet information
        bet_id = bet.get("id", "unknown")
        market_id = bet.get("contractId", market.get("id", "unknown"))
        market_name = market.get("question", "Unknown Market")
        user_id = bet.get("userId", "unknown")
        username = bet.get("userName", bet.get("userUsername", "unknown"))
        amount = abs(bet.get("amount", 0))
        prob_before = bet.get("probBefore", 0)
        prob_after = bet.get("probAfter", 0)

        # Parse timestamp
        created_time = bet.get("createdTime", 0)
        timestamp = datetime.fromtimestamp(created_time / 1000, tz=timezone.utc)

        # Update market statistics
        stats = self._get_market_stats(market_id)
        avg_bet = stats.get_average_bet()
        stats.add_bet(amount, timestamp, prob_after)

        # Cache user data if provided
        if user_data and user_id:
            self.user_cache[user_id] = user_data

        # 1. WHALE BET DETECTION
        # Check if bet is ≥5x the market average (with minimum threshold)
        if avg_bet > 0 and amount >= self.whale_threshold * avg_bet and amount >= self.min_bet_for_whale:
            if not self._is_alert_seen(bet_id, SignalType.WHALE_BET):
                alerts.append(Alert(
                    signal_type=SignalType.WHALE_BET,
                    market_id=market_id,
                    market_name=market_name,
                    user_id=user_id,
                    username=username,
                    bet_amount=amount,
                    prob_before=prob_before,
                    prob_after=prob_after,
                    timestamp=timestamp,
                    bet_id=bet_id,
                    details={
                        "market_avg_bet": avg_bet,
                        "multiplier": amount / avg_bet if avg_bet > 0 else 0
                    }
                ))
                self._mark_alert_seen(bet_id, SignalType.WHALE_BET)

        # 2. NEW ACCOUNT + LARGE BET DETECTION
        if user_data and self._is_new_account(user_data):
            # New account placing above-average bet
            if avg_bet > 0 and amount > avg_bet:
                if not self._is_alert_seen(bet_id, SignalType.NEW_ACCOUNT_LARGE_BET):
                    created_time_user = user_data.get("createdTime", 0)
                    created_dt = datetime.fromtimestamp(created_time_user / 1000, tz=timezone.utc)
                    account_age_days = (datetime.now(timezone.utc) - created_dt).days

                    alerts.append(Alert(
                        signal_type=SignalType.NEW_ACCOUNT_LARGE_BET,
                        market_id=market_id,
                        market_name=market_name,
                        user_id=user_id,
                        username=username,
                        bet_amount=amount,
                        prob_before=prob_before,
                        prob_after=prob_after,
                        timestamp=timestamp,
                        bet_id=bet_id,
                        details={
                            "account_age_days": account_age_days,
                            "market_avg_bet": avg_bet
                        }
                    ))
                    self._mark_alert_seen(bet_id, SignalType.NEW_ACCOUNT_LARGE_BET)

        # 3. SHARP MOVEMENT DETECTION
        # Check if probability moved ≥10% in the last 5 minutes
        prob_change = stats.get_prob_change(self.sharp_movement_window)
        if prob_change:
            start_prob, end_prob = prob_change
            change = abs(end_prob - start_prob)

            if change >= self.sharp_movement_threshold:
                # Create alert for this bet if it contributed to the movement
                if not self._is_alert_seen(bet_id, SignalType.SHARP_MOVEMENT):
                    # Only alert if this bet was a significant contributor
                    bet_contribution = abs(prob_after - prob_before)
                    if bet_contribution >= 0.02:  # At least 2% movement from this bet
                        alerts.append(Alert(
                            signal_type=SignalType.SHARP_MOVEMENT,
                            market_id=market_id,
                            market_name=market_name,
                            user_id=user_id,
                            username=username,
                            bet_amount=amount,
                            prob_before=start_prob,
                            prob_after=end_prob,
                            timestamp=timestamp,
                            bet_id=bet_id,
                            details={
                                "total_movement": change,
                                "window_minutes": self.sharp_movement_window,
                                "bet_contribution": bet_contribution
                            }
                        ))
                        self._mark_alert_seen(bet_id, SignalType.SHARP_MOVEMENT)

        # 4. HIGH SKILL USER DETECTION
        if user_data:
            is_high_skill, skill_details = self._is_high_skill_user(user_data)
            if is_high_skill and amount >= self.min_bet_for_whale / 2:  # Lower threshold for known skilled users
                if not self._is_alert_seen(bet_id, SignalType.HIGH_SKILL_USER):
                    alerts.append(Alert(
                        signal_type=SignalType.HIGH_SKILL_USER,
                        market_id=market_id,
                        market_name=market_name,
                        user_id=user_id,
                        username=username,
                        bet_amount=amount,
                        prob_before=prob_before,
                        prob_after=prob_after,
                        timestamp=timestamp,
                        bet_id=bet_id,
                        details=skill_details
                    ))
                    self._mark_alert_seen(bet_id, SignalType.HIGH_SKILL_USER)

        return alerts

    def get_stats(self) -> dict:
        """Get engine statistics"""
        return {
            "markets_tracked": len(self.market_stats),
            "alerts_seen": len(self.seen_alerts),
            "users_cached": len(self.user_cache)
        }

    def cleanup_old_data(self, max_age_hours: int = 24):
        """
        Clean up old market statistics to prevent memory bloat.

        Args:
            max_age_hours: Remove markets not updated in this many hours
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        markets_to_remove = [
            market_id for market_id, stats in self.market_stats.items()
            if stats.last_updated and stats.last_updated < cutoff
        ]

        for market_id in markets_to_remove:
            del self.market_stats[market_id]

        if markets_to_remove:
            logger.info(f"Cleaned up {len(markets_to_remove)} old market stats")
