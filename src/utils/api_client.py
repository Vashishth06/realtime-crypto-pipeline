"""
API client for cryptocurrency data retrieval and management.    
"""

import time
import requests
from src.utils.logger import setup_logger
from src.utils.config import Config
from src.utils.exceptions import CryptoAPIError, RateLimitError
from src.utils.retry import retry_with_backoff

logger = setup_logger(__name__)

class CryptoAPIClient:
    """
    A client for interacting with cryptocurrency APIs to retrieve and manage data.
    """
    def __init__(self, 
                 env: str = "dev",
                 ) -> None:
        
        config = Config(env=env)
        logger.info("Initializing CryptoAPIClient")
        
        self.base_url = config.api_config.base_url
        self.requests_per_minute = config.api_config.requests_per_minute
        self.timeout = config.api_config.timeout
        self.last_request_time = 0.0  # Track the time of the last request for rate limiting

    @retry_with_backoff(max_retries=3, initial_delay=2.0, exceptions=(requests.exceptions.ConnectionError, requests.exceptions.Timeout))
    def get_coin_price(self, coin_id: str) -> dict:
        """
        Retrieve the current price of a specific cryptocurrency.

        Args:
            coin_id (str): The ID of the cryptocurrency (e.g., 'bitcoin').

        Returns:
            dict: A dictionary containing the current price of the cryptocurrency.
        """
        
        endpoint = f"{self.base_url}/simple/price"
        params = {
            'ids': coin_id,
            'vs_currencies': 'usd'
        }

        # Check for rate limiting before making the request
        min_interval = 60.0 / self.requests_per_minute
        time_since_last_request = time.time() - self.last_request_time
        if time_since_last_request < min_interval:
            time.sleep(min_interval - time_since_last_request)

        response = requests.get(endpoint, params=params, timeout=self.timeout)
        self.last_request_time = time.time()  # Update after request

        # Raise an exception for HTTP errors
        if response.status_code == 429:
            logger.warning("Rate limit exceeded. Retrying...")
            raise RateLimitError("Rate limit exceeded")
        elif response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            raise CryptoAPIError(f"API error: {response.status_code}")

        logger.info(f"Successfully retrieved price for {coin_id}")
        return response.json()
    