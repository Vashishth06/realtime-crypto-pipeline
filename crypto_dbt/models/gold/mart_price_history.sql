SELECT
    coin_id,
    DATE(price_timestamp)                           AS price_date,
    ROUND(MIN(price_usd), 2)                        AS low_price,
    ROUND(MAX(price_usd), 2)                        AS high_price,
    ROUND(AVG(price_usd), 2)                        AS avg_price,
    ROUND(MAX(price_usd) - MIN(price_usd), 2)       AS price_range,
    COUNT(*)                                        AS data_points,
    ingested_at
FROM {{ ref('stg_historical_prices') }}
GROUP BY coin_id, DATE(price_timestamp), ingested_at
ORDER BY coin_id, price_date