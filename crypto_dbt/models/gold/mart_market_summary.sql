SELECT
    market_cap_rank,
    name,
    symbol,
    current_price,
    ROUND(market_cap / 1e9, 2)                        AS market_cap_billions,
    ROUND(total_volume / 1e9, 2)                      AS volume_billions,
    ROUND(price_change_24h_pct, 2)                    AS price_change_24h_pct,
    CASE 
        WHEN price_change_24h_pct > 0 THEN 'up'
        WHEN price_change_24h_pct < 0 THEN 'down'
        ELSE 'stable'
    END                                               AS price_trend,
    ROUND(total_volume / NULLIF(market_cap, 0), 4)    AS volume_to_mcap_ratio,
    ingested_at
FROM {{ ref('stg_markets') }}
ORDER BY market_cap_rank