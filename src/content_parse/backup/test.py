import asyncio
from fastapi import UploadFile
import json
import time
from text_parse.backup.text_parse_module import TextParserModule
import httpx

url = "http://127.0.0.1:8000/text_parse"

schema = [
    {
        "name": "nome_insegnate",
        "type": "str",
        "title": "Nome Insegnate",
        "description": "Il nome dell'insegnate della lezione",
        "examples": ["Alice", "Anna"]
    },
    {
        "name": "prezzo_della_lezione",
        "type": "str",
        "title": "Prezzo della lezione",
        "description": "Il prezzo della lezione in reais",
        "examples": ["48,69 R$", "54,10 R$"]
    },
    {
        "name": "ora_inizio",
        "type": "str",
        "title": "Ora Inizio",
        "description": "Ora di inizio dell'aula",
        "examples": ["07:00", "11:30"]
    },
    {
        "name": "ora_fine",
        "type": "str",
        "title": "Ora Fine",
        "description": "Ora di fine dell'aula",
        "examples": ["07:50", "12:20"]
    },
    {
        "name": "giorno_della_settimana",
        "type": "str",
        "title": "Giorno della Settimana",
        "description": "Nome del giorno della settimana in cui si svolge l'aula",
        "examples": ["Martedì", "Sabato"]
    },
    {
        "name": "mese",
        "type": "str",
        "title": "Nome del Mese",
        "description": "Nome del mese in cui si svolge l'aula",
        "examples": ["Novembre", "Settembre"]
    },
    {
        "name": "data",
        "type": "str",
        "title": "Data",
        "description": "Data completa in formato gg/mm",
        "examples": ["22/12", "15/09"]
    }
]

payload = {
    "client_id": "client_123",
    "job_id": "lezioni_job_001",
    "metadata": None,
    "schema": schema
}

file_name = "g1.txt" # "Candidatura.pdf" #
file_path = f"src/text_parse/txt_examples/{file_name}"

async def run_test():
    start_time = time.time()

    with open(file_path, "rb") as f:
        upload_file = UploadFile(
            filename=file_name,
            file=f
        )

        module = TextParserModule(
            payload=payload,
            file=upload_file
        )

        result = await module.execute()

        print(f"\n{json.dumps(result, indent=2, ensure_ascii=False)}")

        end_time = time.time()
        print(f"Tempo de execução: {end_time - start_time:.2f} segundos")


def test(value):
    if value == 1:
        asyncio.run(run_test())
    
    else:
        with open(file_path, "rb") as f:
            response = httpx.post(
                url,
                files={
                    # payload come stringa JSON (Form)
                    "payload": (None, json.dumps(payload), "application/json"),
                    # file upload
                    "file": ("lezione2.txt", f, "text/plain"),
                },
                timeout=60.0
            )

        print("Status:", response.status_code)
        print("Response:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

test(2)
# python -m src.content_parse.test
