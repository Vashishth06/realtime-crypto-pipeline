import time
from functools import wraps

import requests

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def retry_with_backoff(max_attempts=3, initial_delay=1.0, exceptions=(requests.exceptions.Timeout,)):
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_attempts (int): Maximum number of attempts before giving up.
        initial_delay (float): Initial delay in seconds before the first attempt.
        exceptions (tuple): A tuple of exception classes to catch and retry on.

    Returns:
        The result of the decorated function if successful, or raises the last exception after max attempts.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            retries = 0
            current_delay = initial_delay
            while retries < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"[{func.__name__}] Attempt {retries + 1}/{max_attempts} failed: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    time.sleep(current_delay)
                    retries += 1
                    current_delay *= 2  # Exponential backoff
            if last_exception:
                logger.error(f"[{func.__name__}] All {max_attempts} attempts failed. Last error: {last_exception}")
                raise last_exception
        return wrapper
    return decorator