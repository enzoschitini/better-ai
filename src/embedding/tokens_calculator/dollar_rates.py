from datetime import datetime, timezone
from src.chat.utils.mongo_manage import MongoDBManager
import requests
import os
from dotenv import load_dotenv


load_dotenv()


class DollarRateService:
    """
    Simple service to:
    - Read the rate from MongoDB
    - Check if it is updated (today)
    - Fetch updated rates from an external provider (Apilayer Fixer)
    - Update the database if needed
    """

    MAPPING = {
        "BRL": "dollar_rate_BRL",
        "EUR": "dollar_rate_EUR",
    }

    def __init__(self):
        self.mongo = MongoDBManager()
        self.API_KEY = os.getenv("EXCHANGE_RATES_API_KEY")

    # ------------------------------
    # 1. Read from the database
    # ------------------------------
    def _get_from_db(self):
        docs = self.mongo.buscar_documentos(
            database_name="betterai_embeddings",
            collection_name="embedding_costs",
            filtro={"rate": "dollar_rates"},
            limite=1
        )
        return docs[0]

    # ------------------------------
    # 2. External provider (Apilayer)
    # ------------------------------
    def _fetch_from_provider(self):
        """
        Fetch BRL and EUR using a single Apilayer request.
        Returns a dict: { "BRL": value, "EUR": value }
        """

        try:
            url = "https://api.apilayer.com/exchangerates_data/latest"
            headers = {
                "apikey": self.API_KEY
            }
            params = {
                "base": "USD",
                "symbols": "BRL,EUR"
            }

            response = requests.get(url, headers=headers, params=params, timeout=5)
            data = response.json()

            if not data.get("success", False):
                raise RuntimeError(f"Provider error: {data.get('error')}")

            return {
                "BRL": data["rates"]["BRL"],
                "EUR": data["rates"]["EUR"],
            }

        except Exception as e:
            raise RuntimeError("Error fetching provider") from e

    # ------------------------------
    # 3. Update the database
    # ------------------------------
    def _update_db(self, brl, eur):
        self.mongo.atualizar_documentos(
            database_name="betterai_embeddings",
            collection_name="embedding_costs",
            filtro={"rate": "dollar_rates"},
            novos_valores={
                "dollar_rate_BRL": brl,
                "dollar_rate_EUR": eur,
                "updated_at": datetime.now(timezone.utc)
            }
        )

    # ------------------------------
    # 4. Main public method
    # ------------------------------
    def get_rate(self, currency: str):

        doc = self._get_from_db()
        db_rate = doc[self.MAPPING[currency]]
        updated_at = doc["updated_at"]

        today = datetime.now(timezone.utc).date()
        db_date = updated_at.date()

        # 4.1 If it's already from today → use DB
        if db_date == today:
            #print("✔ Usando cotação do banco (já é de hoje).")
            return db_rate

        #print("ℹ Cotação desatualizada. Tentando atualizar...")

        # 4.2 Try provider
        try:
            rates = self._fetch_from_provider()
            #print("✔ Provider retornou valores. Atualizando banco...")
            self._update_db(rates["BRL"], rates["EUR"])
            return rates[currency]

        except Exception:
            #print("⚠ Provider falhou. Usando cotação antiga do banco.")
            return db_rate


# ============================================================
# Direct execution (for testing only)
# ============================================================



"""
#python -m src.embedding.tokens_calculator.dollar_rates

if __name__ == "__main__":
    service = DollarRateService()

    rate = service.get_rate("EUR")
    print("\nCOTAÇÃO FINAL:", rate, "EUR")

    rate = service.get_rate("BRL")
    print("\nCOTAÇÃO FINAL:", rate, "BRL")
#"""