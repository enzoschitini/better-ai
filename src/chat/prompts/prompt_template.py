import json
import os

from langchain.prompts import PromptTemplate

def chat_system_prompt(empresa: str, path_json: str = "src/chat/prompts/prompts.json") -> str:
    """
    Retorna o prompt do sistema correspondente à empresa informada.

    Parâmetros:
    -----------
    empresa : str
        Nome da empresa para buscar o prompt.
    path_json : str
        Caminho para o arquivo JSON com os prompts. Padrão: "prompts.json".

    Retorna:
    --------
    str
        Prompt do sistema correspondente à empresa.

    Lança:
    ------
    ValueError se a empresa não for encontrada no JSON.
    """
    if not os.path.exists(path_json):
        raise FileNotFoundError(f"Arquivo JSON não encontrado: {path_json}")

    with open(path_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for item in data.get("empresas", []):
        if item.get("nome").lower() == empresa.lower():
            return item.get("prompt")
    
    raise ValueError(f"Nenhum prompt encontrado para a empresa: {empresa}")
