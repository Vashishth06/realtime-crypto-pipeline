# Crypto API Comparison

## Selected: CoinGecko

Chosen for generous free tier (10-30 calls/min) and no API key requirement.

## Comparison Table

| Feature         | CoinGecko      | CoinMarketCap  | CoinPaprika   |
|-----------------|----------------|----------------|---------------|
| Free Tier       | Yes (Generous) | Yes (Basic)    | Yes (No card) |
| Asset Coverage  | 18,000+        | 10,000+        | 10,000+       |
| Data Refresh    | 10s cache      | 30-60s         | 1-3 min       |
| Endpoints | 80+ | 40+            | Varies         |               |
| Historical Data | Yes (Free)     | No (Paid only) | Yes (Limited) |
| Network Support | 250+           | 120+           | 30+           |

## Decision

Using CoinGecko because:
- No API key needed (easier setup)
- Best data freshness (10s cache)
- Most endpoints available
- Historical data in free tier