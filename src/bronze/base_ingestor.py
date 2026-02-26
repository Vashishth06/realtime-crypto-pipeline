import json
from datetime import datetime, timezone
import pyarrow as pa

from pyiceberg.schema import Schema
from pyiceberg.types import NestedField, StringType

from src.utils.api_client import CryptoAPIClient
from src.utils.iceberg_writer import IcebergWriter
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseBronzeIngestor:
    """
    Generic Bronze ingestion engine.
    Subclasses only provide:
    - table_name
    - records
    """

    namespace = "bronze"

    def __init__(self, writer: IcebergWriter, client: CryptoAPIClient):
        self.writer = writer
        self.client = client

    # ---- schema is same for ALL bronze tables ----
    def _schema(self):
        return Schema(
            NestedField(1, "coin_id", StringType(), required=True),
            NestedField(2, "source_updated_at", StringType(), required=False),
            NestedField(3, "ingested_at", StringType(), required=True),
            NestedField(4, "payload", StringType(), required=True),
        )

    def ingest(self, table_name: str, records: list[dict]):
        """Write records to Iceberg"""

        self.writer.create_table(self.namespace, table_name, self._schema())

        ingested_at = datetime.now(timezone.utc).isoformat()

        rows = []
        for r in records:
            rows.append({
                "coin_id": r["coin_id"],
                "source_updated_at": r.get("source_updated_at"),
                "ingested_at": ingested_at,
                "payload": json.dumps(r["payload"])
            })

        pa_schema = pa.schema([
            ('coin_id', pa.string(), False),
            ('source_updated_at', pa.string(), True),
            ('ingested_at', pa.string(), False),
            ('payload', pa.string(), False),
        ])

        table = pa.Table.from_pylist(rows, schema=pa_schema)

        self.writer.write_data(self.namespace, table_name, table)

        logger.info(f"{len(rows)} records written to bronze.{table_name}")