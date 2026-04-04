from datetime import datetime

from src.database.no_relational_db.router import DocumentStore
from src.tokens_calculate.exchange_rate.bcb import BCBExchangeRateService
from src.tracing.tracing_core import ApplicationTracing

tracer = ApplicationTracing(
    flag="ExchangeRate",
    log_file_name="exchange_rate",
    file_name="exchange_rate.py"
)

class ExchangeRateService:
    """
    Serviço para gerenciamento de cotações do dólar americano. 
    Ele busca a cotação mais recente na API do BCB, armazena e recupera registros em um banco local, 
    garantindo que o histórico de dados seja limitado para otimização.

    Args: 
    :param backend (str): Tipo de backend utilizado para armazenar dados, Default é "local".

    Methods:
            generate_post(topic): Explica o metodo em uma frase
    """
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
        """
        Recupera a cotação mais recente do dólar na API do Banco Central do Brasil (BCB).

        Returns:
                float: A cotação mais recente do dólar fornecida pelo BCB.
        """
        service = BCBExchangeRateService()
        result = service.get_latest_rate()
        return result.get("rate")
    
    def _get_last_db_record(self):
        """
        Obtém o último registro de cotação do dólar armazenado no banco de dados local.

        Returns:
                dict or None: O registro de cotação mais recente, ou None se não houver registros.
        """
        docs = self.manager.fetch_documents("tokens_calculate", "exchange_rate")

        if not docs:
            return None

        docs_sorted = sorted(docs, key=lambda x: x["date"], reverse=True)
        return docs_sorted[0]

    def _enforce_limit(self, limit: int = 5):
        """
        Garante que o número de registros armazenados no banco não ultrapasse o limite especificado,
        removendo os registros mais antigos se necessário.

        Args:
            limit (int): Número máximo de registros permitidos no banco. Default é 5.
        """
        docs = self.manager.fetch_documents("tokens_calculate", "exchange_rate")

        if len(docs) < limit:
            return

        docs_sorted = sorted(docs, key=lambda x: x["date"])
        to_delete = len(docs_sorted) - limit + 1

        for i in range(to_delete):
            doc = docs_sorted[i]

            tracer.INFO(f"Removing old record: {doc}")

            self.manager.delete_documents(
                "tokens_calculate",
                "exchange_rate",
                {"date": doc["date"]}
            )

    def get_usd_rate(self):
        """
        Obtém a cotação atual do dólar americano. Primeiro verifica se já existe um registro do dia no banco; 
        caso contrário, busca a cotação na API do BCB, salvando o resultado localmente. Se a API falhar, utiliza 
        o último dado disponível ou uma base padrão.

        Returns:
                float: A cotação do dólar pronta para uso.
        
        Raises:
                RuntimeError: Se ocorrer algum erro obtendo a cotação na API ou no processo de armazenamento.
        """
        try:
            tracer.INFO("Starting process to get USD exchange rate.")

            self._enforce_limit(limit=6)

            last_record = self._get_last_db_record()

            if last_record:
                tracer.INFO(f"Last record in DB: {last_record}")

                if last_record["date"] == self.date_str_api:
                    tracer.INFO("Record is already from today. Returning from DB.")
                    return last_record["rate"]

            tracer.INFO("Fetching rate from BCB API.")
            api_rate = self._get_bcb_rate()

            if api_rate is not None:
                tracer.INFO(f"Rate obtained from API: {api_rate}")

                payload = {
                    "date": self.date_str_api,
                    "currency": "USD",
                    "rate": api_rate,
                    "source": "olinda.bcb.gov.br"
                }

                self._enforce_limit(limit=5)
                self.manager.save_payload("tokens_calculate", "exchange_rate", payload)
                tracer.INFO("New rate saved to DB.")    

                return api_rate

            if last_record:
                tracer.INFO("API failed. Using last value from DB.")
                return last_record["rate"]

            tracer.INFO("No data available. Using base rate.")

            self._enforce_limit(limit=5)
            self.manager.save_payload("tokens_calculate", "exchange_rate", self.base)

            return self.base["rate"]
        except Exception as e:
            tracer.ERROR(f"General error in get_usd_rate: {e}")
            raise RuntimeError("Não foi possível obter a cotação do dólar.") from e