#!/usr/bin/env python3
"""
main.py - Manifold Markets Alert Bot

A simple, robust console-based alert bot that monitors Manifold Markets
for suspicious trading activity and displays alerts in real-time.

Usage:
    python main.py [--interval SECONDS] [--debug]

Signals detected:
    - WHALE_BET: Large bets (≥5x market average)
    - NEW_ACCOUNT_LARGE_BET: New accounts placing above-average bets
    - SHARP_MOVEMENT: Rapid probability changes (≥10% in <5 min)
    - HIGH_SKILL_USER: Bets from users with strong track records
"""

import argparse
import logging
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Optional

from data_fetcher import (
    get_recent_bets,
    get_market_details,
    get_user_by_id,
    ManifoldAPIError
)
from signal_engine import SignalEngine, Alert, SignalType


# ANSI color codes for console output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


# Signal type to color mapping
SIGNAL_COLORS = {
    SignalType.WHALE_BET: Colors.RED,
    SignalType.NEW_ACCOUNT_LARGE_BET: Colors.MAGENTA,
    SignalType.SHARP_MOVEMENT: Colors.YELLOW,
    SignalType.HIGH_SKILL_USER: Colors.CYAN,
}


def setup_logging(debug: bool = False):
    """Configure logging for the application"""
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def format_probability(prob: float) -> str:
    """Format probability as percentage"""
    return f"{prob * 100:.1f}%"


def format_amount(amount: float) -> str:
    """Format bet amount with currency symbol"""
    return f"M{amount:,.0f}"


def print_alert(alert: Alert):
    """
    Print an alert to the console with formatting.

    Format:
    [ALERT] <type>
    Market: <name>
    User: <username>
    Bet Amount: <amount>
    Probability: <before> -> <after>
    Timestamp: <UTC>
    """
    color = SIGNAL_COLORS.get(alert.signal_type, Colors.RESET)

    print()
    print(f"{color}{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{color}{Colors.BOLD}[ALERT] {alert.signal_type.value}{Colors.RESET}")
    print(f"{Colors.BOLD}Market:{Colors.RESET} {alert.market_name[:80]}")
    print(f"{Colors.BOLD}User:{Colors.RESET} {alert.username}")
    print(f"{Colors.BOLD}Bet Amount:{Colors.RESET} {format_amount(alert.bet_amount)}")
    print(f"{Colors.BOLD}Probability:{Colors.RESET} {format_probability(alert.prob_before)} -> {format_probability(alert.prob_after)}")
    print(f"{Colors.BOLD}Timestamp:{Colors.RESET} {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    # Print additional details based on signal type
    if alert.signal_type == SignalType.WHALE_BET:
        multiplier = alert.details.get("multiplier", 0)
        avg_bet = alert.details.get("market_avg_bet", 0)
        print(f"{Colors.BOLD}Details:{Colors.RESET} {multiplier:.1f}x market avg (avg: {format_amount(avg_bet)})")

    elif alert.signal_type == SignalType.NEW_ACCOUNT_LARGE_BET:
        age = alert.details.get("account_age_days", 0)
        print(f"{Colors.BOLD}Details:{Colors.RESET} Account age: {age} days")

    elif alert.signal_type == SignalType.SHARP_MOVEMENT:
        movement = alert.details.get("total_movement", 0)
        window = alert.details.get("window_minutes", 5)
        print(f"{Colors.BOLD}Details:{Colors.RESET} {format_probability(movement)} movement in {window} min")

    elif alert.signal_type == SignalType.HIGH_SKILL_USER:
        profit = alert.details.get("all_time_profit", 0)
        print(f"{Colors.BOLD}Details:{Colors.RESET} All-time profit: {format_amount(profit)}")

    print(f"{color}{'=' * 60}{Colors.RESET}")
    print()


def print_banner():
    """Print startup banner"""
    print(f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║          MANIFOLD MARKETS ALERT BOT                         ║
║          Detecting informed trading activity                 ║
╚══════════════════════════════════════════════════════════════╝
{Colors.RESET}
Signals monitored:
  {Colors.RED}● WHALE_BET{Colors.RESET}             - Large bets (≥5x market average)
  {Colors.MAGENTA}● NEW_ACCOUNT_LARGE_BET{Colors.RESET} - New accounts with large bets
  {Colors.YELLOW}● SHARP_MOVEMENT{Colors.RESET}       - Rapid probability changes
  {Colors.CYAN}● HIGH_SKILL_USER{Colors.RESET}      - Bets from skilled traders

Press Ctrl+C to stop.
""")


def print_status(last_check: datetime, bets_processed: int, alerts_count: int, engine: SignalEngine):
    """Print status line"""
    stats = engine.get_stats()
    timestamp = last_check.strftime("%H:%M:%S")
    print(
        f"\r[{timestamp}] Processed {bets_processed} bets | "
        f"Alerts: {alerts_count} | "
        f"Markets tracked: {stats['markets_tracked']} | "
        f"Users cached: {stats['users_cached']}    ",
        end="",
        flush=True
    )


class AlertBot:
    """
    Main alert bot class.

    Manages the scanning loop, processes bets, and displays alerts.
    """

    def __init__(
        self,
        scan_interval: int = 45,
        bets_per_scan: int = 100,
        debug: bool = False
    ):
        """
        Initialize the alert bot.

        Args:
            scan_interval: Seconds between scans (30-60 recommended)
            bets_per_scan: Number of bets to fetch per scan
            debug: Enable debug logging
        """
        self.scan_interval = scan_interval
        self.bets_per_scan = bets_per_scan
        self.debug = debug

        self.engine = SignalEngine()
        self.running = False
        self.last_bet_time: Optional[int] = None  # Timestamp of most recent bet processed
        self.total_alerts = 0
        self.total_bets_processed = 0

        # Market cache to avoid redundant API calls
        self.market_cache: dict[str, dict] = {}

    def _get_market(self, market_id: str) -> Optional[dict]:
        """Get market details with caching"""
        if market_id not in self.market_cache:
            try:
                market = get_market_details(market_id)
                if market:
                    self.market_cache[market_id] = market
                    # Limit cache size
                    if len(self.market_cache) > 500:
                        # Remove oldest entries
                        oldest_keys = list(self.market_cache.keys())[:100]
                        for key in oldest_keys:
                            del self.market_cache[key]
            except ManifoldAPIError as e:
                logging.warning(f"Failed to fetch market {market_id}: {e}")
                return None

        return self.market_cache.get(market_id)

    def _process_bet(self, bet: dict) -> list[Alert]:
        """Process a single bet and return any alerts"""
        market_id = bet.get("contractId")
        if not market_id:
            return []

        # Get market details
        market = self._get_market(market_id)
        if not market:
            # Use minimal market info from bet if available
            market = {
                "id": market_id,
                "question": bet.get("contractQuestion", "Unknown Market")
            }

        # Get user details for new account and high skill detection
        user_id = bet.get("userId")
        user_data = None
        if user_id:
            try:
                user_data = get_user_by_id(user_id)
            except ManifoldAPIError:
                pass  # Continue without user data

        # Process through signal engine
        return self.engine.process_bet(bet, market, user_data)

    def _scan_cycle(self) -> int:
        """
        Run one scan cycle.

        Returns:
            Number of alerts generated
        """
        alerts_this_cycle = 0

        try:
            # Fetch recent bets
            # If we have a last bet time, only fetch newer bets
            bets = get_recent_bets(
                limit=self.bets_per_scan,
                after_time=self.last_bet_time
            )

            if not bets:
                return 0

            # Update last bet time for next scan
            # Bets are returned in desc order, so first bet is most recent
            if bets:
                newest_time = bets[0].get("createdTime", 0)
                if newest_time > (self.last_bet_time or 0):
                    self.last_bet_time = newest_time

            # Process each bet (in chronological order)
            for bet in reversed(bets):
                self.total_bets_processed += 1

                try:
                    alerts = self._process_bet(bet)

                    for alert in alerts:
                        print_alert(alert)
                        self.total_alerts += 1
                        alerts_this_cycle += 1

                except Exception as e:
                    logging.error(f"Error processing bet {bet.get('id')}: {e}")
                    if self.debug:
                        import traceback
                        traceback.print_exc()

        except ManifoldAPIError as e:
            logging.error(f"API error during scan: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during scan: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()

        return alerts_this_cycle

    def run(self):
        """
        Start the main scanning loop.

        This method blocks until interrupted (Ctrl+C).
        """
        self.running = True
        print_banner()

        logging.info(f"Starting scan loop (interval: {self.scan_interval}s)")

        # Initial scan to establish baseline
        logging.info("Performing initial scan to establish market baselines...")
        initial_bets = get_recent_bets(limit=200)
        if initial_bets:
            self.last_bet_time = initial_bets[0].get("createdTime", 0)
            logging.info(f"Loaded {len(initial_bets)} recent bets for baseline")

            # Process initial bets without generating alerts (just build stats)
            for bet in reversed(initial_bets):
                market_id = bet.get("contractId")
                if market_id:
                    market = self._get_market(market_id)
                    if market:
                        # Just add to stats, don't generate alerts
                        self.engine._get_market_stats(market_id).add_bet(
                            abs(bet.get("amount", 0)),
                            datetime.fromtimestamp(bet.get("createdTime", 0) / 1000, tz=timezone.utc),
                            bet.get("probAfter", 0)
                        )

        print(f"\n{Colors.GREEN}Bot ready. Monitoring for signals...{Colors.RESET}\n")

        try:
            while self.running:
                scan_start = datetime.now(timezone.utc)

                alerts_count = self._scan_cycle()

                # Print status (only if no alerts were printed)
                if alerts_count == 0:
                    print_status(
                        scan_start,
                        self.total_bets_processed,
                        self.total_alerts,
                        self.engine
                    )

                # Periodic cleanup
                if self.total_bets_processed % 1000 == 0:
                    self.engine.cleanup_old_data()

                # Wait for next scan
                time.sleep(self.scan_interval)

        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Shutting down...{Colors.RESET}")

        self.running = False
        self._print_summary()

    def _print_summary(self):
        """Print final summary on shutdown"""
        print(f"""
{Colors.CYAN}{Colors.BOLD}
══════════════════════════════════════════════════════════════
                     SESSION SUMMARY
══════════════════════════════════════════════════════════════
{Colors.RESET}
Total bets processed: {self.total_bets_processed}
Total alerts generated: {self.total_alerts}
Markets tracked: {len(self.market_cache)}

{Colors.GREEN}Goodbye!{Colors.RESET}
""")

    def stop(self):
        """Signal the bot to stop"""
        self.running = False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Manifold Markets Alert Bot - Monitor for informed trading activity"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=45,
        help="Scan interval in seconds (default: 45)"
    )
    parser.add_argument(
        "--bets", "-b",
        type=int,
        default=100,
        help="Number of bets to fetch per scan (default: 100)"
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    # Validate interval
    if args.interval < 10:
        print(f"{Colors.YELLOW}Warning: Very short interval may hit rate limits.{Colors.RESET}")
    if args.interval > 120:
        print(f"{Colors.YELLOW}Warning: Long intervals may miss rapid movements.{Colors.RESET}")

    setup_logging(args.debug)

    # Create and run bot
    bot = AlertBot(
        scan_interval=args.interval,
        bets_per_scan=args.bets,
        debug=args.debug
    )

    # Handle SIGTERM gracefully
    def handle_sigterm(signum, frame):
        bot.stop()

    signal.signal(signal.SIGTERM, handle_sigterm)

    bot.run()


if __name__ == "__main__":
    main()
