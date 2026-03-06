# Day 5-9: Airflow Orchestration + Docker + Streamlit Dashboard

## What We Built

### Airflow DAGs (3 + 1 Live Tracker)

**Master Pipeline DAG (`dags/pipeline_dag.py`)**
- `dag_id='crypto_pipeline'`, scheduled daily at 9am (`0 9 * * *`)
- Uses `TriggerDagRunOperator` with `wait_for_completion=True`
- Flow: `start` → `trigger_bronze` → `trigger_transform` → `end`

**Bronze Ingestion DAG (`dags/bronze_dag.py`)**
- `dag_id='bronze_ingestion'`, `schedule_interval=None` (triggered by master)
- 3 tasks: `ingest_markets` → `ingest_coin_details` → `ingest_historical_prices`
- Uses `BashOperator` calling project venv Python
- Passes `PIPELINE_ENV=docker` with `append_env=True`

**dbt Transform DAG (`dags/transform_dag.py`)**
- `dag_id='dbt_transform'`, `schedule_interval=None`
- 2 tasks: `run_silver_models` → `run_gold_models`
- Uses dbt graph selectors (`--select tag:silver`, `--select tag:gold`)

**Live Markets Tracker (`dags/live_markets_tracker.py`)**
- Runs every 2 minutes (`*/2 * * * *`)
- Isolated from heavy historical loads
- Uses graph selectors to run only `stg_markets` + `mart_market_summary`
- Reduces dbt run time from ~40s to ~8s

### Bronze Layer CLI Entry Point

**`src/bronze/run_ingestion.py`**
- Accepts `--ingestor` argument (markets, coin_details, historical_prices)
- Reads `PIPELINE_ENV` env var → loads correct config
- Dynamically imports ingestor class via `importlib`
- Called directly by BashOperator inside Airflow container

### Docker Infrastructure

**`Dockerfile`** — Custom Airflow image
- Base: `apache/airflow:2.9.3`
- Creates isolated `/opt/airflow/project-env` for project dependencies
- Separates project deps from Airflow's own Python environment
- Layer caching: `COPY requirements` before `COPY src/` — code changes don't invalidate dependency cache

**`docker-compose.yml`** — 7 containers on `crypto-network` bridge network

| Container | Image | Port | Purpose |
|---|---|---|---|
| `iceberg-postgres` | postgres:15 | 5432 | Iceberg metastore + app DB |
| `airflow-postgres` | postgres:15 | - | Airflow metadata DB |
| `airflow-init` | custom | - | One-time DB initialization |
| `airflow-webserver` | custom | 8081 | Airflow UI |
| `airflow-scheduler` | custom | - | DAG scheduler |
| `trino` | trinodb/trino | 8080 | Query engine |
| `minio` | minio | 9000/9001 | Object storage |

**Volume mounts (webserver + scheduler):**
```yaml
- ./dags:/opt/airflow/dags
- ./src:/opt/airflow/src
- ./config:/opt/airflow/config
- ./crypto_dbt:/opt/airflow/crypto_dbt
- ./dbt_profiles:/opt/airflow/dbt_profiles
```

### Layered Config System

Three-layer YAML with deep merge — last loaded wins:

```
base.yaml     → universal settings (API URL, timeouts, logging)
secrets.yaml  → credentials with localhost (local dev only)
docker.yaml   → container hostnames (loaded last, always wins)
```

`PIPELINE_ENV=docker` → loads `docker.yaml` last → `iceberg-postgres` overrides `localhost`

### Streamlit Dashboard (`src/app/dashboard.py`)

- Connects to Trino via `trino` Python connector
- Queries Gold layer directly — no duplicate data movement
- 3 tabs: Market Summary, Price History, Watchlist
- Interactive coin selection via `on_select="rerun"`
- 60-second auto-refresh via `st_autorefresh`
- Dynamic Plotly charts — green/red color based on price delta between first and last record
- Cross-layer join: Gold summary + Silver staging to resolve `coin_id` ↔ `symbol`
- Direct Bronze layer access (`iceberg.bronze.raw_markets`) for intraday precision

---

## Key Concepts

### Why Isolated Python Venv in Docker

pyiceberg >= 0.5.1 requires SQLAlchemy >= 2.0. Airflow 2.9.x requires SQLAlchemy 1.4.x. They cannot coexist in the same Python environment.

**Solution:** Two separate Python environments inside the container:
```
/usr/local/lib/python3.12/     ← Airflow's env (SQLAlchemy 1.4.x)
/opt/airflow/project-env/      ← Project env (SQLAlchemy 2.0+, pyiceberg)
```

BashOperator explicitly calls project venv:
```python
PYTHON = '/opt/airflow/project-env/bin/python'
DBT   = '/opt/airflow/project-env/bin/dbt'
```

### Docker Networking

Containers communicate via service names, not `localhost`:
```
localhost        → the container itself (nothing listening on 5432)
iceberg-postgres → Docker DNS resolves to correct container IP
```

**Request flow:**
```
Browser (localhost:8501)
      ↓
Streamlit container
      ↓ SQL query
Trino (trino:8080)
      ↓ metadata              ↓ data files
Postgres (iceberg-postgres)  MinIO (minio:9000)
      ↓
Result returned to Streamlit
```

### Volume Mounts vs Image Layers

| What changed | Action needed |
|---|---|
| Python code (`src/`, `dags/`) | `docker-compose restart` only |
| Config files (`config/`) | `docker-compose restart` only |
| `docker-requirements.txt` | Full `--no-cache` rebuild |
| `Dockerfile` | Full `--no-cache` rebuild |

Volume mounts = live tunnel between Windows and container. No rebuild needed for code changes.

### Micro-Batch Architecture

Moved from manual cold-start runs to a scheduled heartbeat model:

```
live_markets_tracker  (*/2 * * * *)  ← high frequency, lightweight
crypto_pipeline       (0 9 * * *)    ← daily, full pipeline
```

dbt graph selectors bypass heavy historical models:
```bash
# Full run (~40s)
dbt run

# Live tracker only (~8s)
dbt run --select stg_markets mart_market_summary
```

### Trino Timestamp Handling

Trino cannot `CAST()` ISO 8601 strings with timezone offsets:
```sql
-- Fails
CAST('2026-03-01T05:17:08.433794+00:00' AS TIMESTAMP)

-- Works — Trino-specific function
from_iso8601_timestamp('2026-03-01T05:17:08.433794+00:00')
```

### Cross-Layer Joins in Trino

Dashboard searched by `symbol` (BTC) but Iceberg tables indexed by `coin_id` (bitcoin).

**Solution:** Join Gold and Silver layers dynamically in Trino:
```sql
SELECT g.*, s.symbol
FROM gold.mart_market_summary g
JOIN silver.stg_markets s ON g.coin_id = s.coin_id
WHERE s.symbol = 'BTC'
```

Same query engine serves both analytics and BI layers — core lakehouse pattern.

---

## Challenges Solved

### SQLAlchemy Version Conflict
- **Issue:** pyiceberg and Airflow require incompatible SQLAlchemy versions
- **Fix:** Isolated project venv at `/opt/airflow/project-env`
- **Lesson:** Isolate tool environments from day one, not as an afterthought

### Docker Networking (`localhost` vs container names)
- **Issue:** `secrets.yaml` had `host: localhost` — works locally, fails inside containers
- **Fix:** `config/docker.yaml` with `host: iceberg-postgres`
- **Lesson:** Understand your network topology before writing connection strings

### Config Merge Order Bug
- **Issue:** `secrets.yaml` loaded last, overriding `docker.yaml` — `localhost` always won
- **Fix:** Load order: `base` → `secrets` → `env-specific` (`docker.yaml` loads last, wins)
- **Lesson:** Test config loading assumptions with a debug print before building on top

### BashOperator Environment Variables
- **Issue:** `env={'PIPELINE_ENV': 'docker'}` replaced the entire subprocess environment
- **Fix:** Added `append_env=True` to merge with system env instead of replacing it
- **Alternative fix:** Inline env var in bash command: `PIPELINE_ENV=docker python -m ...`
- **Lesson:** Test env var propagation with a simple echo before running real code

### Trino `INVALID_CAST_ARGUMENT`
- **Issue:** Trino rejected ISO 8601 timestamps via `CAST()`
- **Fix:** Replaced with `from_iso8601_timestamp()`
- **Lesson:** Trino has specific functions for non-standard formats — never assume SQL is universal

### Streamlit Cache + Trino Connection
- **Issue:** `RuntimeError: no transaction was started` inside `@st.cache_data`
- **Fix:** Stabilized Trino DBAPI connection lifecycle within the cache wrapper
- **Lesson:** Connection lifecycle must be managed carefully inside caching decorators

### ID-Symbol Mismatch (Silent Failure)
- **Issue:** Dashboard searched by `symbol` (BTC), table indexed by `coin_id` (bitcoin) — returned empty results with no error
- **Fix:** Cross-layer Trino join between Gold and Silver to resolve identifiers dynamically
- **Lesson:** Always verify what field your data is actually indexed by before querying

### Missing Python Module (`streamlit_autorefresh`)
- **Issue:** `ModuleNotFoundError: streamlit_autorefresh` at dashboard startup
- **Fix:** Added to Streamlit requirements and reconciled local pip environment
- **Lesson:** Keep a separate `requirements.txt` per service — dashboard deps != pipeline deps

---

## Testing & Verification

**Airflow DAGs running successfully:**
```bash
# List all DAGs
docker exec -it airflow-scheduler airflow dags list

# Trigger master pipeline manually
docker exec -it airflow-scheduler airflow dags trigger crypto_pipeline

# Check task logs
docker exec -it airflow-scheduler airflow tasks logs bronze_ingestion ingest_markets
```

**Verifying env var propagation inside container:**
```bash
docker exec -it airflow-scheduler bash
cd /opt/airflow && PIPELINE_ENV=docker /opt/airflow/project-env/bin/python \
  -m src.bronze.run_ingestion --ingestor markets
```

**Streamlit dashboard — http://localhost:8501**

**Trino verification queries:**
```sql
-- Verify Bronze data flowing
SELECT COUNT(*) FROM iceberg.bronze.raw_markets;

-- Verify Silver models
SELECT * FROM iceberg.silver.stg_markets LIMIT 5;

-- Verify Gold marts
SELECT * FROM iceberg.gold.mart_market_summary
ORDER BY market_cap DESC LIMIT 10;

-- Cross-layer join
SELECT g.coin_id, s.symbol, g.current_price
FROM iceberg.gold.mart_market_summary g
JOIN iceberg.silver.stg_markets s ON g.coin_id = s.coin_id
LIMIT 10;
```

---

## Next Steps
- Scale to full data volume (250 coins, 365-day backfill)
- Add dbt tests for Silver/Gold data quality
- Idempotency verification in `IcebergWriter` (upsert vs append)
- Row count validation and pipeline observability
- Architecture diagram for README
- WebSockets (Binance API) for sub-minute latency
- Indian market integration (NSE/BSE via Dhan/Shoonya API)
- Coin Genesis detail page with historical origins + news API integration