# Day 3-5: Trino Query Engine + Postgres Metastore

## What We Built

### Infrastructure Changes
- **PostgreSQL metastore** (replaced SQLite)
  - Docker container for Iceberg catalog metadata
  - Persistent volume for data durability
- **Trino query engine** (Docker)
  - SQL interface to query Iceberg tables
  - Federated query capability (ready for multi-source)

### Configuration Updates
- **PostgresConfig** dataclass added
  - Host, port, database, user, password
  - Loaded from `config/secrets.yaml`
- **MinIOConfig** extended
  - Added `warehouse_path` parameter
  - Dynamic warehouse location configuration

### IcebergWriter Refactoring
- Catalog URI now uses Postgres instead of SQLite
- Dynamic URI construction from config:
```python
  postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}
```
- All credentials loaded from config (no hardcoding)
- Warehouse path from config instead of hardcoded

### Trino Setup
- **Docker Compose** orchestration
  - Postgres + Trino services
  - Dependency management (Trino depends on Postgres)
  - Environment variable injection
- **Trino Configuration**
  - JVM settings (`jvm.config`)
  - Coordinator config (`config.properties`)
  - Node properties (`node.properties`)
- **Iceberg Catalog** for Trino
  - JDBC connection to Postgres metastore
  - MinIO S3 endpoint configuration
  - Path-style access enabled

## Key Concepts

### Why Postgres Over SQLite?

**SQLite limitations:**
- Single-writer (no concurrent ingestion)
- Local file (not accessible from Docker containers)
- No network access

**Postgres benefits:**
- Multi-writer support (concurrent ingestion)
- Network-accessible (Docker containers can connect)
- Production-ready metadata store
- ACID guarantees for catalog operations

### Trino Architecture
```
Trino Coordinator
    ↓
Iceberg Catalog (Postgres)
    ↓
Data Files (MinIO S3)
```

**Query Flow:**
1. Trino receives SQL query
2. Queries Postgres for table metadata
3. Reads data files from MinIO
4. Executes query and returns results

### JSON Extraction in Trino

Bronze tables store full payloads as JSON strings. Trino can extract fields:
```sql
SELECT 
    coin_id,
    json_extract_scalar(payload, '$.name') AS name,
    CAST(json_extract_scalar(payload, '$.current_price') AS DOUBLE) AS price
FROM iceberg.bronze.raw_markets;
```

**Functions:**
- `json_extract_scalar()` - Extract string value
- `json_extract()` - Extract JSON object/array
- `CAST()` - Convert types

## File Structure
```
trino/
  etc/
    catalog/
      iceberg.properties    - Iceberg connector config
    jvm.config             - JVM heap/GC settings
    config.properties      - Coordinator settings
    node.properties        - Node identity
docker-compose.yml         - Postgres + Trino orchestration
.env                       - Environment variables (gitignored)
pgdata/                    - Postgres data volume (gitignored)
```

## Challenges Solved

### Docker Networking
- **Issue:** Trino couldn't reach MinIO at `localhost:9000`
- **Fix:** Use `host.docker.internal:9000` (Docker host gateway)

### Environment Variables in Trino
- **Issue:** `${DB_USER}` not substituted in catalog properties
- **Solution (attempted):** `${ENV:DB_USER}` syntax
- **Workaround:** Hardcoded credentials in catalog file for now
- **TODO:** Proper secret injection via Docker secrets or config templates

### Catalog Migration
- **Change:** SQLite → Postgres
- **Impact:** All Python code (IcebergWriter) needed URI update
- **Benefit:** Concurrent writes now possible

## Testing & Verification

**Successful Queries:**
```sql
SHOW SCHEMAS FROM iceberg;
-- Returns: bronze

SELECT * FROM iceberg.bronze.raw_markets LIMIT 5;
-- Returns: 5 rows with coin_id, payload, timestamps

SELECT 
    json_extract_scalar(payload, '$.name') AS name,
    CAST(json_extract_scalar(payload, '$.current_price') AS DOUBLE) AS price
FROM iceberg.bronze.raw_markets;
-- Returns: Extracted structured fields from JSON
```

## Next Steps
- Add Supabase Postgres catalog to Trino (federated queries)
- Silver layer with dbt (transform JSON → structured tables)
- Airflow orchestration for scheduled ingestion
- Proper secret management (Docker secrets or Vault)