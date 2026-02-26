class CryptoAPIError(Exception):
    """Base exception for API errors"""
    pass

class RateLimitError(CryptoAPIError):
    """Raised when rate limit exceeded"""
    pass

class ServerUnavailableError(CryptoAPIError):
    """Raised when server is temporarily unavailable (503)"""
    pass

class InvalidRequestError(CryptoAPIError):
    """Base for permanent user errors"""
    pass

class InvalidCoinIDError(InvalidRequestError):
    """Raised when coin ID doesn't exist (404)"""
    pass