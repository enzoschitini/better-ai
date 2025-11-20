import json
import os

from langchain.prompts import PromptTemplate
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(filename)s - line: %(lineno)d - %(levelname)s - %(message)s'
)

def chat_system_prompt(empresa: str, path_json: str = "src/chat/prompts/prompts.json") -> str:
    """
    Retorna o prompt do sistema correspondente à empresa informada.
    """
    logging.info(f"Iniciando chat_system_prompt() para empresa='{empresa}' com arquivo='{path_json}'")

    # Verifica se o JSON existe
    if not os.path.exists(path_json):
        logging.error(f"Arquivo JSON não encontrado: {path_json}")
        raise FileNotFoundError(f"Arquivo JSON não encontrado: {path_json}")

    logging.debug("Arquivo JSON encontrado, iniciando leitura...")

    # Lê o JSON
    try:
        with open(path_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        logging.debug("JSON carregado com sucesso.")
    except Exception as e:
        logging.exception(f"Erro lendo o arquivo JSON: {e}")
        raise

    # Procura empresa
    empresas = data.get("empresas", [])
    logging.debug(f"Número de empresas encontradas no JSON: {len(empresas)}")

    for item in empresas:
        nome_emp = item.get("nome", "").lower()
        if nome_emp == empresa.lower():
            logging.info(f"Prompt encontrado para a empresa: {empresa}")
            return item.get("prompt")

    logging.warning(f"Nenhum prompt encontrado para a empresa: {empresa}")
    raise ValueError(f"Nenhum prompt encontrado para a empresa: {empresa}")
