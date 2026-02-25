class CryptoAPIError(Exception):
    """Base exception for API errors"""
    pass

class RateLimitError(CryptoAPIError):
    """Raised when rate limit exceeded"""
    pass