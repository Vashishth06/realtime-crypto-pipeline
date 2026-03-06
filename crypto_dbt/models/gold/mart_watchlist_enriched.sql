SELECT
    w.user_id,
    p.username,
    w.coin_id,
    m.name                          AS coin_name,
    m.current_price,
    m.market_cap_billions,
    m.price_change_24h_pct,
    m.price_trend,
    w.added_at
FROM appdb.crypto_app.user_watchlists w
JOIN appdb.crypto_app.user_profiles p
    ON w.user_id = p.user_id
JOIN {{ ref('mart_market_summary') }} m
    ON w.coin_id = m.symbol