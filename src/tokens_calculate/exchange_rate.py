from dotenv import load_dotenv
from datetime import datetime

from src.database.no_relational_db.router import DocumentStore
from src.tokens_calculate.bcb import BCBExchangeRateService

load_dotenv()

class ExchangeRateService:
    def __init__(self):
        self.manager = DocumentStore(backend="local")
        self.base = {
            "date": "2025-11-09",
            "currency": "USD",
            "rate": 5.25,
            "source": "better-ai"
        }
        self.today = datetime.now()
        self.date_str_api = self.today.strftime("%Y-%m-%d")
    
    def _get_bcb_rate(self):
        service = BCBExchangeRateService()
        result = service.get_latest_rate()
        return result.get("rate")
    
    def _get_last_db_record(self):
        docs = self.manager.fetch_documents("tokens_calculate", "exchange_rate")

        if not docs:
            return None

        docs_sorted = sorted(docs, key=lambda x: x["date"], reverse=True)
        return docs_sorted[0]

    def _enforce_limit(self, limit: int = 5):
        docs = self.manager.fetch_documents("tokens_calculate", "exchange_rate")

        if len(docs) < limit:
            return

        docs_sorted = sorted(docs, key=lambda x: x["date"])
        to_delete = len(docs_sorted) - limit + 1

        for i in range(to_delete):
            doc = docs_sorted[i]

            print(f"Removendo registro antigo: {doc}")

            self.manager.delete_documents(
                "tokens_calculate",
                "exchange_rate",
                {"date": doc["date"]}
            )

    def get_usd_rate(self):
        try:
            print("\n--- INÍCIO get_usd_rate ---")

            self._enforce_limit(limit=6)

            last_record = self._get_last_db_record()

            if last_record:
                print(f"Último registro encontrado: {last_record}")

                if last_record["date"] == self.date_str_api:
                    print("Registro já é de hoje. Retornando do banco.")
                    return last_record["rate"]

            print("Buscando cotação na API...")
            api_rate = self._get_bcb_rate()

            if api_rate is not None:
                print(f"Cotação obtida da API: {api_rate}")

                payload = {
                    "date": self.date_str_api,
                    "currency": "USD",
                    "rate": api_rate,
                    "source": "olinda.bcb.gov.br"
                }

                self._enforce_limit(limit=5)
                self.manager.save_payload("tokens_calculate", "exchange_rate", payload)
                print("Salvo no banco.")

                return api_rate

            if last_record:
                print("API falhou. Usando último valor do banco.")
                return last_record["rate"]

            print("Nenhum dado disponível. Usando base.")

            self._enforce_limit(limit=5)
            self.manager.save_payload("tokens_calculate", "exchange_rate", self.base)

            return self.base["rate"]
        except Exception as e:
            print(f"Erro geral em get_usd_rate: {e}")
            raise RuntimeError("Não foi possível obter a cotação do dólar.") from e

if __name__ == "__main__":
    #"""
    service = ExchangeRateService()
    rate = service.get_usd_rate()

    print(rate)
    #"""

# python -m src.tokens_calculate.exchange_rate