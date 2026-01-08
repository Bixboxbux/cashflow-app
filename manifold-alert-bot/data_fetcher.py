"""
data_fetcher.py - Manifold Markets API interactions

This module handles all API calls to Manifold Markets.
It provides functions to fetch markets, bets, and user information.

API Base: https://api.manifold.markets/v0
Rate limit: 500 requests/minute
"""

import requests
import time
import logging
from typing import Optional
from datetime import datetime, timezone

# Configure logging
logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "https://api.manifold.markets/v0"
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


class ManifoldAPIError(Exception):
    """Custom exception for Manifold API errors"""
    pass


class RateLimiter:
    """
    Simple rate limiter to respect API limits.
    Manifold allows 500 requests/minute.
    """
    def __init__(self, max_requests: int = 400, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []

    def wait_if_needed(self):
        """Block if we're approaching rate limit"""
        now = time.time()
        # Remove old requests outside the window
        self.requests = [r for r in self.requests if now - r < self.window_seconds]

        if len(self.requests) >= self.max_requests:
            # Wait until oldest request exits the window
            sleep_time = self.window_seconds - (now - self.requests[0]) + 0.1
            if sleep_time > 0:
                logger.warning(f"Rate limit approaching, waiting {sleep_time:.1f}s")
                time.sleep(sleep_time)

        self.requests.append(time.time())


# Global rate limiter instance
rate_limiter = RateLimiter()


def _make_request(endpoint: str, params: Optional[dict] = None) -> dict | list:
    """
    Make a GET request to the Manifold API with retry logic.

    Args:
        endpoint: API endpoint (without base URL)
        params: Query parameters

    Returns:
        JSON response data

    Raises:
        ManifoldAPIError: If request fails after retries
    """
    url = f"{BASE_URL}{endpoint}"

    for attempt in range(MAX_RETRIES):
        try:
            rate_limiter.wait_if_needed()

            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
                headers={"Accept": "application/json"}
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limited - wait and retry
                wait_time = RETRY_DELAY * (attempt + 1) * 2
                logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                time.sleep(wait_time)
                continue
            elif response.status_code == 404:
                logger.debug(f"Resource not found: {endpoint}")
                return None
            else:
                logger.error(f"API error {response.status_code}: {response.text[:200]}")

        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout (attempt {attempt + 1}/{MAX_RETRIES})")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY * (attempt + 1))

    raise ManifoldAPIError(f"Failed to fetch {endpoint} after {MAX_RETRIES} attempts")


def get_recent_markets(limit: int = 50, sort: str = "last-bet-time") -> list:
    """
    Fetch recently active markets.

    Args:
        limit: Number of markets to fetch (max 1000)
        sort: Sort by 'created-time', 'updated-time', 'last-bet-time', 'last-comment-time'

    Returns:
        List of LiteMarket objects
    """
    params = {
        "limit": min(limit, 1000),
        "sort": sort,
        "order": "desc"
    }

    result = _make_request("/markets", params)
    return result if result else []


def get_market_details(market_id: str) -> Optional[dict]:
    """
    Fetch full market details including answers.

    Args:
        market_id: The market ID

    Returns:
        FullMarket object or None
    """
    return _make_request(f"/market/{market_id}")


def get_market_bets(
    contract_id: str = None,
    limit: int = 100,
    after_time: int = None,
    order: str = "desc"
) -> list:
    """
    Fetch bets, optionally filtered by market.

    Args:
        contract_id: Filter by market ID (optional)
        limit: Number of bets to fetch (max 1000)
        after_time: Only bets after this timestamp (milliseconds)
        order: 'asc' or 'desc'

    Returns:
        List of Bet objects
    """
    params = {
        "limit": min(limit, 1000),
        "order": order
    }

    if contract_id:
        params["contractId"] = contract_id
    if after_time:
        params["afterTime"] = after_time

    result = _make_request("/bets", params)
    return result if result else []


def get_recent_bets(limit: int = 200, after_time: int = None) -> list:
    """
    Fetch the most recent bets across all markets.

    Args:
        limit: Number of bets to fetch
        after_time: Only bets after this timestamp (milliseconds)

    Returns:
        List of Bet objects
    """
    return get_market_bets(limit=limit, after_time=after_time, order="desc")


def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    Fetch user information by ID.

    Args:
        user_id: The user ID

    Returns:
        User object or None
    """
    return _make_request(f"/user/by-id/{user_id}")


def get_user_by_username(username: str) -> Optional[dict]:
    """
    Fetch user information by username.

    Args:
        username: The username

    Returns:
        User object or None
    """
    return _make_request(f"/user/{username}")


def get_user_bets(user_id: str = None, username: str = None, limit: int = 100) -> list:
    """
    Fetch bets for a specific user.

    Args:
        user_id: Filter by user ID
        username: Filter by username
        limit: Number of bets to fetch

    Returns:
        List of Bet objects
    """
    params = {"limit": limit}

    if user_id:
        params["userId"] = user_id
    if username:
        params["username"] = username

    result = _make_request("/bets", params)
    return result if result else []


def timestamp_to_datetime(timestamp_ms: int) -> datetime:
    """Convert millisecond timestamp to datetime"""
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)


def datetime_to_timestamp(dt: datetime) -> int:
    """Convert datetime to millisecond timestamp"""
    return int(dt.timestamp() * 1000)


# Simple test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Testing Manifold API...")

    # Test fetching recent markets
    markets = get_recent_markets(limit=5)
    print(f"\nFetched {len(markets)} recent markets:")
    for m in markets[:3]:
        print(f"  - {m.get('question', 'N/A')[:60]}...")

    # Test fetching recent bets
    bets = get_recent_bets(limit=10)
    print(f"\nFetched {len(bets)} recent bets")

    if bets:
        # Test fetching user info
        user_id = bets[0].get("userId")
        if user_id:
            user = get_user_by_id(user_id)
            if user:
                print(f"\nUser: {user.get('username', 'N/A')}")

    print("\nAPI tests completed!")
