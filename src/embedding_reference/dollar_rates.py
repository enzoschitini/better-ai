from datetime import datetime, timezone
from src.chat.utils.mongo_manage import MongoDBManager
import requests


class DollarRateService:
    """
    Serviço simples para:
    - Ler a cotação do MongoDB
    - Verificar se é de hoje
    - Buscar cotação atualizada de um provider
    - Atualizar o banco caso necessário
    """

    MAPPING = {
        "BRL": "dollar_rate_BRL",
        "EUR": "dollar_rate_EUR",
    }

    def __init__(self):
        self.mongo = MongoDBManager()

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
    # 2. Buscar provider externo
    # ------------------------------
    def _fetch_from_provider(self, currency: str):
        """
        Retorna um valor atualizado OU levanta exceção.
        """

        try:
            url = f"https://api.exchangerate.host/latest?base=USD&symbols={currency}"
            response = requests.get(url, timeout=5)
            data = response.json()

            return data["rates"][currency]

        except Exception as e:
            raise RuntimeError("Erro ao buscar provider") from e

    # ------------------------------
    # 3. Atualizar o banco
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

        # --------------------------
        # 4.1 Se já é de hoje → usa o banco
        # --------------------------
        if data_banco == hoje:
            print("✔ Usando cotação do banco (já é de hoje).")
            return db_rate

        print("ℹ Cotação do banco não é de hoje. Tentando atualizar...")

        # --------------------------
        # 4.2 Tentar provider externo
        # --------------------------
        try:
            rate_brl = self._fetch_from_provider("BRL")
            rate_eur = self._fetch_from_provider("EUR")

            print("✔ Provider retornou valores. Atualizando banco...")
            self._update_db(rate_brl, rate_eur)

            return rate_brl if currency == "BRL" else rate_eur

        except Exception:
            print("⚠ Provider falhou. Usando cotação do banco mesmo.")
            return db_rate


# ============================================================
# Execução direta (apenas para teste)
# ============================================================
if __name__ == "__main__":
    service = DollarRateService()
    rate = service.get_rate("EUR")
    print("\nCOTAÇÃO FINAL:", rate)



"""
python -m src.embedding_reference.dollar_rates
"""