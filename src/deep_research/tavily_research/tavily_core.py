import os

from typing import List, Dict, Any, List
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

class TavilyDeepResearch:
    """
    Wrapper dinâmico para Tavily AI. 
    Recebe dicionários de configuração para máxima flexibilidade.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")

        if not self.api_key:
            raise RuntimeError("TAVILY_API_KEY not found in environment variables")

        self.client = TavilyClient(api_key=self.api_key)

    def start_search(self, params: Dict[str, Any]) -> dict:
        """
        Busca geral. Espera chaves como 'query', 'search_depth', 'max_results', etc.
        """
        # O **params descompacta o dicionário como argumentos nomeados
        return self.client.search(**params)

    def get_context(self, params: Dict[str, Any]) -> str:
        """
        Retorna contexto para LLMs. Espera 'query', 'max_tokens', etc.
        """
        return self.client.get_search_context(**params)

    def qna(self, params: Dict[str, Any]) -> str:
        """
        Q&A Direto. Geralmente requer apenas {'query': 'sua pergunta'}.
        """
        return self.client.qna_search(**params)

    def extract_content(self, params: Dict[str, Any]) -> dict:
        """
        Extração de conteúdo. Espera 'urls' (lista ou str) e 'format'.
        """
        return self.client.extract(**params)

    def map_site(self, params: Dict[str, Any]) -> dict:
        """
        Mapeia estrutura de URLs. Espera 'url' e opcionalmente 'limit'.
        """
        return self.client.map(**params)

    def crawl_site(self, params: Dict[str, Any]) -> dict:
        """
        Explora site recursivamente. Espera 'url', 'limit' e 'max_depth'.
        """
        return self.client.crawl(**params)

    def get_company(self, params: Dict[str, Any]) -> List[dict]:
        """
        Dados firmográficos. Espera 'query'.
        """
        return self.client.get_company_info(**params)

    def start_research(self, params: Dict[str, Any]) -> dict:
        """
        Inicia agente autônomo. Espera 'input' (tópico) e 'model'.
        """
        # Nota: A lib original usa 'input' para o tópico no método research
        return self.client.research(**params)

    def get_research_status(self, params: Dict[str, Any]) -> dict:
        """
        Status da pesquisa. Espera 'request_id'.
        """
        return self.client.get_research(**params)







