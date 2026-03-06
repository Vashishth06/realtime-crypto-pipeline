WITH raw AS (
    SELECT
        coin_id,
        ingested_at,
        payload
    FROM iceberg.bronze.raw_historical_prices
),

deduplicated AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY coin_id
            ORDER BY ingested_at DESC
        ) AS rn
    FROM raw
),

latest AS (
    SELECT coin_id, ingested_at, payload
    FROM deduplicated
    WHERE rn = 1
),

exploded AS (
    SELECT
        coin_id,
        ingested_at,
        price_entry
    FROM latest
    CROSS JOIN UNNEST(
        CAST(json_extract(payload, '$.prices') AS ARRAY(ARRAY(DOUBLE)))
    ) AS t(price_entry)
)

SELECT
    coin_id,
    from_unixtime(price_entry[1] / 1000)  AS price_timestamp,
    price_entry[2]                         AS price_usd,
    ingested_at
FROM exploded
ORDER BY coin_id, price_timestamp