import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import requests

load_dotenv()

class BCBExchangeRateService:
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

            print(f"Tentativa para {date.strftime('%m-%d-%Y')}: "
                  f"{'Sucesso' if response.status_code == 200 else 'Falha'}")

            if response.status_code == 200:
                dados = response.json()

                if dados["value"]:
                    rate = float(dados["value"][0]["cotacaoVenda"])
                    date_api = datetime.strptime(
                        dados["value"][0]["dataHoraCotacao"].split(" ")[0],
                        "%Y-%m-%d",
                    )
                    return rate, date_api

        except requests.RequestException as e:
            print(f"Erro na requisição: {e}")

        return None, None

    def get_latest_rate(self, max_days_back: int = 5):
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

        print(
            f"\nMelhor cotação encontrada: "
            f"{best_rate} BRL/USD em "
            f"{best_date.strftime('%Y-%m-%d') if best_date else 'N/A'}\n"
        )

        return {
            "rate": best_rate,
            "date": best_date
        }

if __name__ == "__main__":
    service = BCBExchangeRateService()
    result = service.get_latest_rate()

    print(result)

# python -m src.tokens_calculate.exchange_rate