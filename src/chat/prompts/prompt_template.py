import os
import yaml
import logging

from src.chat.utils.logging_utils import setup_logging

#setup_logging()

def chat_system_prompt(empresa: str, path_yaml: str = "src/chat/prompts/prompts.yaml") -> str:
    """
    Retorna o prompt do sistema correspondente à empresa informada (lendo de YAML).
    """
    logging.info(f"Iniciando chat_system_prompt() para empresa='{empresa}' com arquivo='{path_yaml}'")

    # Verifica se o YAML existe
    if not os.path.exists(path_yaml):
        logging.error(f"Arquivo YAML não encontrado: {path_yaml}")
        raise FileNotFoundError(f"Arquivo YAML não encontrado: {path_yaml}")

    logging.debug("Arquivo YAML encontrado, iniciando leitura...")

    # Lê o YAML
    try:
        with open(path_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        logging.debug("YAML carregado com sucesso.")
    except Exception as e:
        logging.exception(f"Erro lendo o arquivo YAML: {e}")
        raise

    # Procura a empresa
    empresas = data.get("empresas", [])
    logging.debug(f"Número de empresas encontradas no YAML: {len(empresas)}")

    for item in empresas:
        nome_emp = item.get("nome", "").lower()
        if nome_emp == empresa.lower():
            logging.info(f"Prompt encontrado para a empresa: {empresa}")
            return item.get("prompt")

    logging.warning(f"Nenhum prompt encontrado para a empresa: {empresa}")
    raise ValueError(f"Nenhum prompt encontrado para a empresa: {empresa}")

#print(chat_system_prompt(empresa="standard"))