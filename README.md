# Realtime Crypto Pipeline

End-toend cryptocurrency data lakehouse built with modern data engineering tools. Ingests live market data from CoinGecko API, processes it through a medallion architecture (Bronze→Silver→Gold), orchestrates with Airflow, and visualizes with a live Streamlit dashboard.

---

## Architecture
```
CoinGecko API
      ↓
Bronze Layer (Raw JSON → Apache Iceberg → MinIO)
      ↓
Silver Layer (dbt transformations → cleaned, typed tables)
      ↓
Gold Layer (dbt aggregations → analytics-ready marts)
      ↓
Trino (federated query engine)
      ↓
Streamlit Dashboard (live market data, 2-min refresh)

Orchestration: Apache Airflow (3 DAGs)
Infrastructure: Docker (7 containers)
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Ingestion | Python, CoinGecko API |
| Storage | Apache Iceberg, MinIO (S3-compatible) |
| Metadata | PostgreSQL |
| Transformation | dbt-core, dbt-trino |
| Query Engine | Trino |
| Orchestration | Apache Airflow 2.9.3 |
| Dashboard | Streamlit, Plotly |
| Infrastructure | Docker, Docker Compose |

---

## Data Flow

### Bronze Layer
- Ingests raw JSON from CoinGecko API (100 coins)
- Stores as Parquet files in MinIO via Apache Iceberg
- Three tables: `raw_markets`, `raw_coin_details`, `raw_historical_prices`
- Schema-agnostic — raw payload preserved for time travel

### Silver Layer
- Parses raw JSON, enforces schema, deduplicates
- Three staging models: `stg_markets`, `stg_coin_details`, `stg_historical_prices`
- dbt tests for data quality

### Gold Layer
- Analytics-ready aggregations
- `mart_market_summary` — current prices, market caps, 24h changes
- `mart_price_history` — 90-day price history per coin
- `mart_watchlist_enriched` — user watchlist joined with live market data

---

## Infrastructure

7 Docker containers on a shared bridge network:

| Container | Purpose | Port |
|---|---|---|
| `iceberg-postgres` | Iceberg metadata store + app DB | 5432 |
| `airflow-postgres` | Airflow metadata DB | - |
| `airflow-webserver` | Airflow UI | 8081 |
| `airflow-scheduler` | DAG scheduler | - |
| `trino` | Query engine | 8080 |
| `minio` | Object storage | 9000/9001 |

---

## Airflow DAGs

- `bronze_ingestion` — runs 3 ingestors sequentially
- `dbt_transform` — runs Silver then Gold dbt models
- `crypto_pipeline` — master DAG, triggers both above with `TriggerDagRunOperator`
- `live_markets_tracker` — runs every 2 minutes for live dashboard data

---

## Key Engineering Decisions

**Why dbt over PySpark?**
Data volume (100 coins, daily) doesn't justify distributed compute overhead. dbt + Trino handles all transformations efficiently at this scale. PySpark would be appropriate for millions of rows or complex ML feature engineering.

**Why Iceberg over plain Parquet?**
Schema evolution, time travel, and ACID transactions without rewriting entire datasets. Iceberg's metadata layer (stored in Postgres) enables Trino to query efficiently without full table scans.

**Why separate Python venv inside Docker?**
pyiceberg requires SQLAlchemy >= 2.0 but Airflow 2.9.x requires SQLAlchemy 1.4.x. Isolated `/opt/airflow/project-env` for project dependencies, Airflow uses its own env. BashOperator calls project scripts using the isolated venv's Python.

**Why layered YAML config?**
`base.yaml` → `secrets.yaml` → `docker.yaml` — each layer overrides the previous. Environment-specific config (container hostnames) always takes precedence over local credentials without touching code.

---

## Setup

### Prerequisites
- Docker Desktop
- Python 3.11+

### Run
```bash
# Clone
git clone https://github.com/Vashishth06/realtime-crypto-pipeline
cd realtime-crypto-pipeline

# Copy secrets template and fill in values
cp config/secrets.example.yaml config/secrets.yaml

# Start all containers
docker-compose up -d

# Wait ~2 minutes for Trino to initialize, then create Airflow admin
docker exec -it airflow-webserver airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password admin

# Trigger pipeline
# Open http://localhost:8081 → trigger crypto_pipeline DAG

# View dashboard
streamlit run src/app/dashboard.py
```

### Useful Commands
```bash
# Check container status
docker ps

# Check logs
docker logs trino --tail 30
docker logs airflow-scheduler --tail 50

# Shell into container
docker exec -it airflow-scheduler bash

# Rebuild after dependency changes
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Project Structure
```
realtime-crypto-pipeline/
├── Dockerfile                  # Custom Airflow image with project venv
├── docker-compose.yml          # 7-container infrastructure
├── docker-requirements.txt     # Project dependencies (isolated from Airflow)
├── config/
│   ├── base.yaml               # Universal settings (API, logging)
│   ├── dev.yaml                # Local dev overrides
│   └── docker.yaml             # Docker container hostnames
├── dags/
│   ├── bronze_dag.py           # Bronze ingestion DAG
│   ├── transform_dag.py        # dbt Silver/Gold DAG
│   ├── pipeline_dag.py         # Master orchestration DAG
│   └── live_markets_tracker.py # 2-min micro-batch DAG
├── src/
│   ├── bronze/
│   │   ├── base_ingestor.py    # Abstract base class
│   │   ├── market_ingestion.py
│   │   ├── coin_details_ingestion.py
│   │   ├── historical_price_ingestion.py
│   │   └── run_ingestion.py    # CLI entry point
│   ├── utils/
│   │   ├── config.py           # Layered YAML config system
│   │   ├── api_client.py       # CoinGecko API client with retry
│   │   ├── iceberg_writer.py   # Reusable Iceberg table writer
│   │   ├── logger.py           # Centralized logging setup
│   │   └── retry.py            # Exponential backoff decorator
│   └── app/
│       └── dashboard.py        # Streamlit live dashboard
├── crypto_dbt/
│   ├── models/
│   │   ├── silver/             # Staging models
│   │   └── gold/               # Mart models
│   └── macros/
│       └── generate_schema_name.sql
├── dbt_profiles/
│   └── profiles.yml            # Trino connection config
└── trino/
    └── etc/catalog/
        ├── iceberg.properties  # Iceberg catalog config
        └── appdb.properties    # PostgreSQL catalog config
```

---

## Lessons Learned

- **Docker networking** — containers communicate via service names, not `localhost`. Hardcoding `localhost` in config fails inside containers.
- **Dependency isolation** — conflicting SQLAlchemy versions between pyiceberg and Airflow solved with separate virtual environments.
- **Config merge order matters** — last loaded file wins. `docker.yaml` must load after `secrets.yaml` to override localhost with container hostnames.
- **BashOperator env propagation** — `append_env=True` required to merge with system environment instead of replacing it.

---

## Author

**Vashishth Chhatbar**
- GitHub: [Vashishth06](https://github.com/Vashishth06)
- Transitioning from Chemical Engineering to Data Engineering
- MSc Computer Science, Scaler x Woolf University (2026)

