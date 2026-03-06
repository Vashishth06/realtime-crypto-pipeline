"""
Entry point for running any bronze ingestor from command line.

Usage:
    python -m src.bronze.run_ingestion --ingestor markets
    python -m src.bronze.run_ingestion --ingestor coin_details
    python -m src.bronze.run_ingestion --ingestor historical_prices
"""

import argparse
import importlib
import os
from src.utils.api_client import CryptoAPIClient
from src.utils.iceberg_writer import IcebergWriter


INGESTOR_MAP = {
    "markets": ("src.bronze.market_ingestion", "MarketsIngestor"),
    "coin_details": ("src.bronze.coin_details_ingestion", "CoinDetailsIngestor"),
    "historical_prices": ("src.bronze.historical_price_ingestion", "HistoricalPricesIngestor"),
}


def run(ingestor_name: str):
    from src.utils.api_client import CryptoAPIClient
    from src.utils.iceberg_writer import IcebergWriter

    if ingestor_name not in INGESTOR_MAP:
        raise ValueError(f"Unknown ingestor: {ingestor_name}. Valid: {list(INGESTOR_MAP.keys())}")

    module_path, class_name = INGESTOR_MAP[ingestor_name]
    module = importlib.import_module(module_path)
    ingestor_class = getattr(module, class_name)

    env = os.getenv("PIPELINE_ENV", "dev")
    client = CryptoAPIClient()
    writer = IcebergWriter(env=env)
    ingestor_class(writer, client).run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ingestor", required=True, help="Ingestor to run")
    args = parser.parse_args()
    run(args.ingestor)