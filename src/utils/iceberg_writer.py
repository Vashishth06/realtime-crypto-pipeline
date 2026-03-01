"""
Reusable Iceberg table writer for Bronze/Silver/Gold layers
"""

from pyiceberg.catalog.sql import SqlCatalog
from pyiceberg.schema import Schema
from pyiceberg.table import Table
import pyarrow as pa
from src.utils.logger import setup_logger
from src.utils.config import Config

logger = setup_logger(__name__)

class IcebergWriter:
    def __init__(self, env: str = "dev"):
        self.config = Config(env=env)
        self.catalog = self._init_catalog()
    
    def _init_catalog(self) -> SqlCatalog:
        """Initialize Iceberg SQL catalog with MinIO"""
        catalog = SqlCatalog(
            "crypto_catalog",
            **{
                "uri": f"postgresql+psycopg2://{self.config.postgres.user}:{self.config.postgres.password}@{self.config.postgres.host}:{self.config.postgres.port}/{self.config.postgres.database}?options=-csearch_path%3Diceberg",
                "warehouse": self.config.minio_config.warehouse_path,
                "s3.endpoint": f"http://{self.config.minio_config.endpoint}",
                "s3.access-key-id": self.config.minio_config.access_key,
                "s3.secret-access-key": self.config.minio_config.secret_key,
            }
        )
        logger.info("Iceberg catalog initialized")
        return catalog  
    
    def create_table(self, namespace: str, table_name: str, schema: Schema) -> Table:
        """Create Iceberg table if it doesn't exist"""
        
        # Create namespace if needed
        try:
            self.catalog.create_namespace(namespace)
            logger.info(f"Namespace '{namespace}' created")
        except Exception:
            logger.debug(f"Namespace '{namespace}' already exists")

        # Create table location
        table_location = f"{self.config.minio_config.warehouse_path}/{namespace}/{table_name}"
        
        # Create table
        try:
            table = self.catalog.create_table(
                f"{namespace}.{table_name}",  # identifier
                schema=schema,
                location=table_location
            )
            logger.info(f"Table '{namespace}.{table_name}' created")
            return table
        except Exception:
            logger.info(f"Table '{namespace}.{table_name}' already exists")
            return self.catalog.load_table(f"{namespace}.{table_name}")
        
    def write_data(self, namespace: str, table_name: str, data: pa.Table) -> None:
        """
        Write PyArrow table to Iceberg table.
        
        Args:
            namespace: Database/schema name
            table_name: Table name
            data: PyArrow Table with data
        """
        logger.info(f"Writing {len(data)} rows to {namespace}.{table_name}")
        
        # Load table
        table = self.catalog.load_table(f"{namespace}.{table_name}")
        
        # Append data
        table.append(data)
        
        logger.info(f"Successfully wrote {len(data)} rows")

    def reset_catalog(self):
        """Delete catalog and recreate (DEV ONLY)"""
        import os
        
        catalog_path = "catalog.db"
        if os.path.exists(catalog_path):
            os.remove(catalog_path)
            logger.warning("Catalog deleted - starting fresh")
        
        # Reinitialize catalog
        self.catalog = self._init_catalog()
        logger.info("Catalog recreated")

    def clear_warehouse(self, namespace: str):
        """Clear all data in namespace (DEV ONLY)"""
        import boto3
        
        s3 = boto3.client(
            's3',
            endpoint_url=f"http://{self.config.minio_config.endpoint}",
            aws_access_key_id=self.config.minio_config.access_key,
            aws_secret_access_key=self.config.minio_config.secret_key
        )
        
        # Delete all objects in warehouse/namespace/
        bucket = 'bronze'
        prefix = f'warehouse/{namespace}/'
        
        objects = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if 'Contents' in objects:
            delete_keys = [{'Key': obj['Key']} for obj in objects['Contents']]
            s3.delete_objects(Bucket=bucket, Delete={'Objects': delete_keys})
            logger.warning(f"Cleared {len(delete_keys)} objects from {namespace}")