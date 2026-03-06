WITH raw AS (
    SELECT
        coin_id,
        ingested_at,
        payload
    FROM iceberg.bronze.raw_coin_details
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
    json_extract_scalar(payload, '$.symbol')                                          AS symbol,
    json_extract_scalar(payload, '$.name')                                            AS name,
    json_extract_scalar(payload, '$.hashing_algorithm')                               AS hashing_algorithm,
    json_extract_scalar(payload, '$.genesis_date')                                    AS genesis_date,
    json_extract_scalar(payload, '$.links.homepage[0]')                               AS homepage,
    CAST(json_extract_scalar(payload, '$.market_data.current_price.usd') AS DOUBLE)   AS current_price_usd,
    CAST(json_extract_scalar(payload, '$.market_data.market_cap.usd') AS DOUBLE)      AS market_cap_usd,
    CAST(json_extract_scalar(payload, '$.market_data.total_volume.usd') AS DOUBLE)    AS total_volume_usd,
    CAST(json_extract_scalar(payload, '$.market_data.price_change_percentage_24h') AS DOUBLE) AS price_change_24h_pct,
    CAST(json_extract_scalar(payload, '$.community_data.twitter_followers') AS BIGINT) AS twitter_followers,
    ingested_at
FROM deduplicated
WHERE rn = 1