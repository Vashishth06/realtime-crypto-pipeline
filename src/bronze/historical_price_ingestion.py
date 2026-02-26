from src.bronze.base_ingestor import BaseBronzeIngestor

class HistoricalPricesIngestor(BaseBronzeIngestor):
    """
    Ingests historical price data from the API to the "historical_prices_raw" Iceberg table.
    """

    def run(self, coin_id: str, days=30):
        data = self.client.get_historical_prices(coin_id, days=days)

        records = [{
            "coin_id": coin_id,
            "source_updated_at": None,
            "payload": data
        }]

        self.ingest("raw_historical_prices", records)