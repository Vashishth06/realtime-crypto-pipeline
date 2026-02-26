# Day 2: Storage Infrastructure + Bronze Layer

## Duration
~8 hours

## What We Built

### Infrastructure
- MinIO (S3-compatible storage) running in Docker
- Supabase PostgreSQL database
- Iceberg catalog with SQLite metadata store
- Config management with secrets (gitignored)

### Core Utilities
- `IcebergWriter` - Reusable writer for all layers
  - Catalog initialization with MinIO
  - Table creation with schema management
  - Data writing with PyArrow conversion

### API Client Refactoring
- Centralized `_request()` method (single HTTP execution point)
- Added endpoints: ping, get_coin_details, get_historical_prices
- Consistent retry + rate limiting across all endpoints

### Bronze Layer Architecture
- **True medallion**: Store complete raw payloads as JSON strings
- `BaseBronzeIngestor` - Abstract base for all bronze ingestions
- 3 Bronze tables implemented:
  - `markets_raw` - Top coins by market cap
  - `coin_details_raw` - Coin metadata
  - `historical_prices_raw` - Time-series price data

### Schema Design
All bronze tables share same schema:
```
- coin_id (string, required)
- source_updated_at (string, optional) 
- ingested_at (string, required)
- payload (string, required) - Full JSON response
```

## Key Design Decisions

**Bronze = Archive Everything**
- Store complete API responses as JSON
- No field selection at ingestion
- Enables schema evolution without re-ingestion
- Silver layer will extract needed columns

**Shared Resources Pattern**
- Single IcebergWriter instance reused across ingestors
- Single API client instance for all calls
- Reduces initialization overhead

**Catalog Configuration**
- SQLite for metadata (local dev)
- MinIO S3-compatible storage for data files
- Warehouse path: `s3://bronze/warehouse/{namespace}/{table}/`

## Technical Concepts

**MinIO**
- Local S3-compatible object storage
- Docker container: `localhost:9000` (API), `localhost:9001` (Console)
- Buckets: bronze, silver, gold

**PyIceberg**
- Python library for Apache Iceberg
- Schema defined with NestedField types
- PyArrow for data conversion (must match Iceberg schema exactly)
- SqlCatalog tracks table metadata

**Schema Matching**
- Iceberg schema defines table structure
- PyArrow schema defines data format
- Both must align: types, nullability, field order
- Mismatch causes write failures

## File Structure
```
src/
  bronze/
    base_ingestor.py           - Abstract bronze ingestion
    market_ingestion.py        - Markets ingestor
    coin_details_ingestion.py  - Coin details ingestor
    historical_price_ingestion.py - Historical prices
  utils/
    iceberg_writer.py          - Reusable Iceberg writer
    api_client.py              - Refactored with _request()
config/
  secrets.yaml                 - MinIO + Supabase credentials (gitignored)
  catalog.yaml                 - Iceberg catalog config
```

## Challenges Solved

**Schema Mismatch Errors**
- PyArrow defaults to nullable fields
- Explicit schema definition required: `pa.schema([('field', type, nullable)])`
- Field order must match Iceberg schema

**Warehouse Path Doubling**
- Initial: `s3://bronze/` created `bronze/bronze/` 
- Fix: Explicit warehouse path `s3://bronze/warehouse`
- All components aligned on same path

**Resource Reuse**
- Initial: Each ingestor created own writer/client
- Optimized: Share single instances across all ingestors

## Next Steps
- Silver layer transformations (dbt)
- Trino setup for federated queries
- Airflow orchestration
- Historical data backfill