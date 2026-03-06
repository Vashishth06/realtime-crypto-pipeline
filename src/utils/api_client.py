"""
API client for cryptocurrency data retrieval and management.
Centralized HTTP execution, retries, and rate limiting.
"""

import time
import requests
from typing import Optional, Dict, Any

from src.utils.logger import setup_logger
from src.utils.config import Config
from src.utils.exceptions import (
    CryptoAPIError,
    RateLimitError,
    ServerUnavailableError,
    InvalidCoinIDError
)
from src.utils.retry import retry_with_backoff

logger = setup_logger(__name__)


class CryptoAPIClient:
    """
    CoinGecko API connector.

    This class is the ONLY place in the project that should ever
    make HTTP requests to the crypto API.
    """

    _last_request_time = 0.0  # shared across all instances (global rate limiting)

    # ---------- Initialization ----------

    def __init__(self, env: str = "dev") -> None:
        config = Config(env=env)

        self.base_url = config.api_config.base_url
        self.requests_per_minute = config.api_config.requests_per_minute
        self.timeout = config.api_config.timeout

        logger.info("CryptoAPIClient initialized")

    # ============================================================
    # CORE HTTP ENGINE (MOST IMPORTANT FUNCTION)
    # ============================================================

    @retry_with_backoff(
        max_attempts=3,
        initial_delay=2.0,
        exceptions=(requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    ServerUnavailableError,
                    RateLimitError)
    )
    def _request(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Core HTTP executor used by all API methods.

        Handles:
        - rate limiting
        - retries
        - error handling
        - JSON decoding
        """

        url = f"{self.base_url}{path}"

        # Rate limit before sending request
        self._rate_limit()

        logger.info(f"GET {path} params={params}")

        response = requests.get(url, params=params, timeout=self.timeout)

        # update last request timestamp
        CryptoAPIClient._last_request_time = time.time()

        # validate response
        self._handle_response(response)

        return response.json()

    # ============================================================
    # PUBLIC API METHODS (ONLY DESCRIBE ENDPOINTS)
    # ============================================================

    def ping(self) -> dict:
        """Check if API is reachable."""
        return self._request("/ping")

    def get_coin_price(self, coin_id: str) -> dict:
        """Get current price of a coin."""
        return self._request(
            path="/simple/price",
            params={
                "ids": coin_id,
                "vs_currencies": "usd"
            }
        )

    def get_coin_markets(self, vs_currency: str = "usd", limit: int = 100) -> list:
        """Get top coins by market cap."""
        return self._request(
            path="/coins/markets",
            params={
                "vs_currency": vs_currency,
                "per_page": min(limit, 250),
                "page": 1,
                "sparkline": False
            }
        )

    def get_coin_details(self, coin_id: str) -> dict:
        """Get detailed metadata for a coin."""
        return self._request(
            path=f"/coins/{coin_id}",
            params={
                "localization": False,
                "tickers": False,
                "market_data": True,
                "community_data": False,
                "developer_data": False,
                "sparkline": False
            }
        )

    def get_historical_prices(self, coin_id: str, vs_currency: str = "usd", days: int = 30) -> dict:
        """Get historical price time-series."""
        return self._request(
            path=f"/coins/{coin_id}/market_chart",
            params={
                "vs_currency": vs_currency,
                "days": days
            }
        )

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================

    def _rate_limit(self) -> None:
        """Enforce API rate limiting."""
        min_interval = 60.0 / self.requests_per_minute
        elapsed = time.time() - CryptoAPIClient._last_request_time

        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

    def _handle_response(self, response: requests.Response) -> None:
        """Validate HTTP response and raise appropriate errors."""

        if response.status_code == 200:
            return

        if response.status_code == 429:
            logger.warning("Rate limit exceeded (429)")
            raise RateLimitError("Rate limit exceeded")

        elif response.status_code == 503:
            logger.error("Server unavailable (503)")
            raise ServerUnavailableError("Server unavailable")

        elif response.status_code == 404:
            logger.error("Invalid coin ID (404)")
            raise InvalidCoinIDError("Invalid coin ID")

        else:
            logger.error(f"API error {response.status_code}: {response.text}")
            raise CryptoAPIError(f"API error {response.status_code}")