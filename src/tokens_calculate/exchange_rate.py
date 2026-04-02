import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import requests

load_dotenv()

# https://currencyrateapi.com/it/
# https://exchangerateapi.net/

def bcb_exchange_rate():
    BCB_API_URL = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"

    base_url = BCB_API_URL
    today = datetime.now()
    best_rate = None
    best_date = None

    # Tenta até 4 dias anteriores
    for delta in range(0, 5):
        date_try = today - timedelta(days=delta)
        date_str_api = date_try.strftime("%m-%d-%Y")
        url = (
            f"{base_url}"
            f"CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='{date_str_api}'"
            f"&$top=1&$format=json"
        )
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                dados = response.json()
                if dados["value"]:
                    rate = float(dados["value"][0]["cotacaoVenda"])
                    date_api = datetime.strptime(
                            dados["value"][0]["dataHoraCotacao"].split(" ")[0],
                            "%Y-%m-%d",
                    )
                    if best_date is None or date_api > best_date:
                        best_rate = rate
                        best_date = date_api
            
            print(f"Tentativa para {date_str_api}: {'Sucesso' if response.status_code == 200 else 'Falha'}")
        except requests.RequestException:
            pass
        time.sleep(0.2)

    print(f"\nMelhor cotação encontrada: {best_rate} BRL/USD em {best_date.strftime('%Y-%m-%d') if best_date else 'N/A'}\n")

bcb_exchange_rate()

# python -m src.tokens_calculate.exchange_rate