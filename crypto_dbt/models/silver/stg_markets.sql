WITH raw AS (
    SELECT
        coin_id,
        ingested_at,
        payload
    FROM iceberg.bronze.raw_markets
),

deduplicated AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY coin_id
            ORDER BY ingested_at DESC
        ) AS rn
    FROM raw
)

SELECT
    coin_id,
    json_extract_scalar(payload, '$.symbol') AS symbol,
    json_extract_scalar(payload, '$.name') AS name,
    CAST(json_extract_scalar(payload, '$.market_cap_rank') AS BIGINT) AS market_cap_rank,
    CAST(json_extract_scalar(payload, '$.current_price') AS DOUBLE) AS current_price,
    CAST(json_extract_scalar(payload, '$.market_cap') AS DOUBLE) AS market_cap,
    CAST(json_extract_scalar(payload, '$.total_volume') AS DOUBLE) AS total_volume,
    CAST(json_extract_scalar(payload, '$.price_change_percentage_24h') AS DOUBLE) AS price_change_24h_pct,
    ingested_at
FROM deduplicated
WHERE rn = 1