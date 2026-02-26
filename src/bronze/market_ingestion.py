from src.bronze.base_ingestor import BaseBronzeIngestor

class MarketsIngestor(BaseBronzeIngestor):
    """
    Ingests coin market data from the API to the "raw_markets" Iceberg table.
    """

    def run(self, limit=100):
        data = self.client.get_coin_markets(limit=limit)

        records = []
        for coin in data:
            records.append({
                "coin_id": coin["id"],
                "source_updated_at": coin.get("last_updated"),
                "payload": coin
            })

        self.ingest("raw_markets", records)