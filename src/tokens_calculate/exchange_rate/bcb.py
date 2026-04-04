import time
import requests
from datetime import datetime, timedelta
from src.tracing.tracing_core import ApplicationTracing

tracer = ApplicationTracing(
    flag="ExchangeRate",
    log_file_name="exchange_rate",
    file_name="bcb.py"
)

class BCBExchangeRateService:
    """
    Serviço para consultar cotações do dólar em relação ao real diretamente pela API do Banco Central do Brasil (BCB).
    Permite buscar a taxa de câmbio do dólar para datas específicas e encontrar a mais recente disponível em um intervalo de dias.

    Args:
        :param timeout (int): Tempo limite (em segundos) para requisições HTTP. Default é 10.

    Methods:
            get_latest_rate(max_days_back): Busca a melhor cotação do dólar nos últimos dias informados.
    """
    BCB_API_URL = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def _build_url(self, date: datetime) -> str:
        date_str_api = date.strftime("%m-%d-%Y")
        return (
            f"{self.BCB_API_URL}"
            f"CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='{date_str_api}'"
            f"&$top=1&$format=json"
        )

    def _fetch_rate_for_date(self, date: datetime):
        url = self._build_url(date)
        try:
            response = requests.get(url, timeout=self.timeout)

            log = (f"Attempt for {date.strftime('%m-%d-%Y')}: "
                  f"{'Success' if response.status_code == 200 else 'Error'}")

            tracer.INFO(log)

            if response.status_code == 200:
                dados = response.json()

                if dados["value"]:
                    rate = float(dados["value"][0]["cotacaoVenda"])
                    date_api = datetime.strptime(
                        dados["value"][0]["dataHoraCotacao"].split(" ")[0],
                        "%Y-%m-%d",
                    )
                    return rate, date_api

        except Exception as e:
            tracer.ERROR(f"Error fetching rate for {date.strftime('%m-%d-%Y')}: {e}")

        return None, None

    def get_latest_rate(self, max_days_back: int = 5):
        """
        Busca a melhor cotação do dólar em relação ao real disponível nos últimos dias especificados.
        Varre os últimos dias começando do dia atual e retorna a maior cotação encontrada.

        Args:
            max_days_back (int): Quantidade de dias para buscar cotações anteriores. Default é 5.

        Returns:
                dict: Dicionário contendo 'rate' (float ou None) com a melhor cotação encontrada e 'date' (datetime ou None) da cotação.

        """
        try:
            today = datetime.now()
            best_rate = None
            best_date = None

            for delta in range(0, max_days_back):
                date_try = today - timedelta(days=delta)

                rate, date_api = self._fetch_rate_for_date(date_try)

                if rate and date_api:
                    if best_date is None or date_api > best_date:
                        best_rate = rate
                        best_date = date_api

                time.sleep(0.2)

            log = (
                f"\nBest rate found: "
                f"{best_rate} BRL/USD on "
                f"{best_date.strftime('%Y-%m-%d') if best_date else 'N/A'}\n"
            )
            tracer.INFO(log)

            return {
                "rate": best_rate,
                "date": best_date
            }
        except Exception as e:
            tracer.ERROR(f"General error occurred while fetching exchange rate: {e}")
            return {
                "rate": None,
                "date": None
            }