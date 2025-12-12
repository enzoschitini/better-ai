from datetime import datetime, timezone
from src.chat.utils.mongo_manage import MongoDBManager
import requests
import os
from dotenv import load_dotenv

load_dotenv()


class DollarRateService:
    """
    Serviço simples para:
    - Ler a cotação do MongoDB
    - Verificar se é de hoje
    - Buscar cotação atualizada de um provider externo (Apilayer Fixer)
    - Atualizar o banco caso necessário
    """

    MAPPING = {
        "BRL": "dollar_rate_BRL",
        "EUR": "dollar_rate_EUR",
    }

    def __init__(self):
        self.mongo = MongoDBManager()
        self.API_KEY = os.getenv("EXCHANGE_RATES_API_KEY")

    # ------------------------------
    # 1. Ler do banco
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
    # 2. Provider externo (Apilayer)
    # ------------------------------
    def _fetch_from_provider(self):
        """
        Busca BRL e EUR em uma única chamada Apilayer (Fixer).
        Retorna dict: { "BRL": valor, "EUR": valor }
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
            raise RuntimeError("Erro ao buscar provider") from e

    # ------------------------------
    # 3. Atualizar banco
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
    # 4. Função principal
    # ------------------------------
    def get_rate(self, currency: str):

        doc = self._get_from_db()
        db_rate = doc[self.MAPPING[currency]]
        updated_at = doc["updated_at"]

        hoje = datetime.now(timezone.utc).date()
        data_banco = updated_at.date()

        # 4.1 Se já é de hoje → usar banco
        if data_banco == hoje:
            print("✔ Usando cotação do banco (já é de hoje).")
            return db_rate

        print("ℹ Cotação desatualizada. Tentando atualizar...")

        # 4.2 Tentar provider externo
        try:
            rates = self._fetch_from_provider()
            print("✔ Provider retornou valores. Atualizando banco...")
            self._update_db(rates["BRL"], rates["EUR"])
            return rates[currency]

        except Exception:
            print("⚠ Provider falhou. Usando cotação antiga do banco.")
            return db_rate


# ============================================================
# Execução direta (apenas para teste)
# ============================================================
if __name__ == "__main__":
    service = DollarRateService()
    rate = service.get_rate("BRL")
    print("\nCOTAÇÃO FINAL:", rate)




"""
    1. Controlla su Mongo la se la cotazione è aggiornata (data di oggi)
    2. Se sì, usa quella
    3. Se no, prova a prendere la cotazione da un provider esterno
    4. Se riesce, aggiorna il DB e usa quella
    5. Se non riesce, usa la cotazione vecchia del DB 5.406098
"""

"""
python -m src.embedding_reference.dollar_rates
"""