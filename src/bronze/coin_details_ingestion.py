from src.bronze.base_ingestor import BaseBronzeIngestor

class CoinDetailsIngestor(BaseBronzeIngestor):
    """ 
    Ingests coin details data from the API to the "coin_details_raw" Iceberg table.
    """
    
    def run(self, coin_id: str="bitcoin"):
        data = self.client.get_coin_details(coin_id)

        records = [{
            "coin_id": coin_id,
            "source_updated_at": data.get("last_updated"),
            "payload": data
        }]

        self.ingest("raw_coin_details", records)