import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import requests
from src.database.no_relational_db.router import DocumentStore

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
            #erro = 1 / 0
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

        except Exception as e:
            print(f"Erro ao buscar cotação para {date.strftime('%m-%d-%Y')}: {e}")

        return None, None

    def get_latest_rate(self, max_days_back: int = 5):
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

            print(
                f"\nMelhor cotação encontrada: "
                f"{best_rate} BRL/USD em "
                f"{best_date.strftime('%Y-%m-%d') if best_date else 'N/A'}\n"
            )

            return {
                "rate": best_rate,
                "date": best_date
            }
        except Exception as e:
            print(f"Erro geral ao obter cotação: {e}")
            return {
                "rate": None,
                "date": None
            }






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

        # ordena pela data (mais recente primeiro)
        docs_sorted = sorted(docs, key=lambda x: x["date"], reverse=True)
        return docs_sorted[0]

    def _enforce_limit(self, limit: int = 5):
        docs = self.manager.fetch_documents("tokens_calculate", "exchange_rate")

        if len(docs) < limit:
            return

        # ordena do mais antigo → mais recente
        docs_sorted = sorted(docs, key=lambda x: x["date"])

        # calcula quantos precisam ser removidos
        to_delete = len(docs_sorted) - limit + 1

        for i in range(to_delete):
            doc = docs_sorted[i]

            print(f"Removendo registro antigo: {doc}")

            # ⚠️ ajuste aqui conforme sua implementação
            self.manager.delete_documents(
                "tokens_calculate",
                "exchange_rate",
                {"date": doc["date"]}
            )

    def get_usd_rate(self):
        print("\n--- INÍCIO get_usd_rate ---")

        # 🔥 GARANTE LIMITE SEMPRE
        self._enforce_limit(limit=6)

        last_record = self._get_last_db_record()

        # 1. Se já existe registro e é de hoje → retorna direto
        if last_record:
            print(f"Último registro encontrado: {last_record}")

            if last_record["date"] == self.date_str_api:
                print("Registro já é de hoje. Retornando do banco.")
                return last_record["rate"]

        # 2. Tenta buscar na API
        print("Buscando cotação na API...")
        api_rate = self._get_bcb_rate()

        if api_rate is not None:
            print(f"Cotação obtida da API: {api_rate}")

            payload = {
                "date": self.date_str_api,
                "currency": "USD",
                "rate": api_rate,
                "source": "bcb"
            }

            # (opcional manter aqui também, mas não obrigatório)
            self._enforce_limit(limit=5)

            self.manager.save_payload("tokens_calculate", "exchange_rate", payload)
            print("Salvo no banco.")

            return api_rate

        # 2.1 Se API falhar → usa último do banco
        if last_record:
            print("API falhou. Usando último valor do banco.")
            return last_record["rate"]

        # 3. Pior caso → salva base
        print("Nenhum dado disponível. Usando base.")

        self._enforce_limit(limit=5)
        self.manager.save_payload("tokens_calculate", "exchange_rate", self.base)

        return self.base["rate"]

if __name__ == "__main__":
    #"""
    service = ExchangeRateService()
    rate = service.get_usd_rate()

    print(rate)
    #"""

# python -m src.tokens_calculate.exchange_rate