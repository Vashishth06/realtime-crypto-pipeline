# Day 1: Foundation + Production Patterns

## Duration
6 hours

## What I Built
- CryptoAPI client with CoinGecko integration
- Custom exception hierarchy (CryptoAPIError, RateLimitError)
- Rate limiting with automatic throttling
- Retry logic with exponential backoff
- Production-grade logging (console + file output)
- Configuration management system (dev/prod environments)
- Unit tests for retry mechanism

## Technical Concepts Mastered

### Error Handling
- Custom exception hierarchies for specific error types
- Fail-fast validation patterns
- Graceful degradation with fallbacks

### Decorators
- Function wrapping for cross-cutting concerns
- @wraps preserves function metadata
- Retry decorator with configurable parameters

### Logging
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Multiple handlers (console + file)
- Formatters for structured output

### Configuration
- YAML-based configuration files
- Environment-specific overrides (dev/prod)
- Deep merge for nested config values
- Type-safe config with dataclasses

## Code Structure
```
src/
  utils/
    api_client.py      - Main API client
    exceptions.py      - Custom exceptions
    retry.py           - Retry decorator
    logger.py          - Logging setup
    config.py          - Configuration loader
tests/
  unit/
    test_retry.py      - Retry logic tests
config/
  base.yaml           - Base configuration
  dev.yaml            - Development overrides
  prod.yaml           - Production overrides
```

## Key Design Decisions

1. **Modular logging**: One logger per module for clear message attribution
2. **Config-driven behavior**: Settings in YAML, not hardcoded
3. **Specific exception catching**: Only retry ConnectionError/Timeout
4. **Deep merge**: Preserve nested config values during override

## Next Steps
- Add data ingestion to Bronze layer
- Implement batch processing
- Build transformation pipeline