import time
from functools import wraps

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def retry_with_backoff(max_retries=3, initial_delay=1.0, exceptions=(Exception,)):
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_retries (int): Maximum number of retries before giving up.
        initial_delay (float): Initial delay in seconds before the first retry.
        exceptions (tuple): A tuple of exception classes to catch and retry on.

    Returns:
        The result of the decorated function if successful, or raises the last exception after max retries.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            retries = 0
            current_delay = initial_delay
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"Error: {e}. Retrying in {current_delay} seconds...")
                    time.sleep(current_delay)
                    retries += 1
                    current_delay *= 2  # Exponential backoff
            if last_exception:
                raise last_exception
        return wrapper
    return decorator