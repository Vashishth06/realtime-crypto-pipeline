import streamlit as st
import pandas as pd
import trino
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- 1. Page Config & Auto-Refresh ---
st.set_page_config(page_title="Crypto Lakehouse", layout="wide")
st.title("🪙 Live Crypto Data Lakehouse")

# Refresh the page automatically every 60 seconds
st_autorefresh(interval=60000, limit=10000, key="data_refresh")

# --- 2. Database Connection ---
# Set cache to 30 seconds so we always get fresh data on clicks/refreshes
@st.cache_data(ttl=30)
def fetch_data(query: str):
    conn = trino.dbapi.connect(
        host='localhost', 
        port=8080,
        user='admin',
        catalog='iceberg',
        schema='gold'
    )
    return pd.read_sql_query(query, conn)

# --- 3. Fetch Top 100 Coins (Gold Layer) ---
st.subheader("Top 100 Cryptocurrencies")
st.caption("🟢 Live updates every 60 seconds. **Click any row to view live charts!**")

summary_query = """
    SELECT 
        market_cap_rank AS Rank,
        name AS Coin,
        symbol AS Symbol,
        current_price AS "Price (USD)",
        market_cap_billions AS "Market Cap (B)",
        price_change_24h_pct AS "24h Change (%)",
        price_trend AS Trend
    FROM mart_market_summary
    ORDER BY Rank
"""
df_summary = fetch_data(summary_query)

# Render interactive dataframe that captures row clicks
selection_event = st.dataframe(
    df_summary, 
    use_container_width=True, 
    hide_index=True,
    on_select="rerun",           # Rerun the app when a row is clicked
    selection_mode="single-row"  # Only allow selecting one coin at a time
)

# --- 4. Interactive Deep Dive (Triggers on Click) ---
st.divider()

# Check if the user has clicked a row
selected_rows = selection_event.selection.rows

if selected_rows:
    # Get the specific coin the user clicked on
    selected_idx = selected_rows[0]
    selected_coin = df_summary.iloc[selected_idx]
    
    coin_name = selected_coin["Coin"]
    coin_symbol = selected_coin["Symbol"]
    
    st.subheader(f"🔴 Live Terminal: {coin_name} ({coin_symbol.upper()})")
    
    # Show quick metrics at a glance
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Price", f"${selected_coin['Price (USD)']}")
    col2.metric("Market Cap", f"${selected_coin['Market Cap (B)']}B")
    col3.metric("24h Trend", f"{selected_coin['24h Change (%)']}%")
    
    # Query the BRONZE layer to see every single micro-batch Airflow has ingested!
    # We use lower() to ensure the symbol matches the JSON payload
    # Query the BRONZE layer to see every single micro-batch Airflow has ingested!
    live_query = f"""
        SELECT 
            from_iso8601_timestamp(ingested_at) AS time,
            CAST(json_extract_scalar(payload, '$.current_price') AS DOUBLE) AS live_price
        FROM iceberg.bronze.raw_markets
        WHERE LOWER(json_extract_scalar(payload, '$.symbol')) = '{coin_symbol.lower()}'
        ORDER BY time DESC
        LIMIT 60
    """
    df_live = fetch_data(live_query)

    if not df_live.empty and len(df_live) > 1:
        # Sort chronologically from left to right for the chart
        df_live = df_live.sort_values("time")
        
        fig = px.line(
            df_live, 
            x="time", 
            y="live_price", 
            title=f"Intraday Micro-Batch Prices (Last {len(df_live)} Pipeline Runs)",
            labels={"time": "Airflow Ingestion Time", "live_price": "Price (USD)"},
            markers=True
        )
        
        # Color the line green if it went up, red if it went down
        start_price = df_live['live_price'].iloc[0]
        end_price = df_live['live_price'].iloc[-1]
        line_color = '#00ff00' if end_price >= start_price else '#ff0000'
        fig.update_traces(line_color=line_color)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"⏳ Waiting for Airflow to collect more live data points for {coin_name}... (Leave the pipeline running!)")

else:
    # This shows up when the dashboard first loads and nothing is clicked yet
    st.info("👆 Click on any coin in the table above to open its live trading terminal.")