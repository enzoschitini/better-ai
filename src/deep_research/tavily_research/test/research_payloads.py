from typing import Any, Dict

def build_test_cases() -> Dict[str, Dict[str, Any]]:
    """
    Cobre todos os metodos expostos por TavilyDeepResearch com parametros exemplos.
    Ajuste os valores conforme sua necessidade e o plano da API da conta.
    """
    return {
        "search_general_basic": {
            "method": "start_search",
            "description": "Busca geral simples (topic=general, depth=basic).",
            "params": {
                "query": "What are the top AI trends in 2026?",
                "topic": "general",
                "search_depth": "basic",
                "max_results": 5,
                "include_answer": True,
                "include_raw_content": False,
                "include_images": False,
            },
        },
        "search_general_advanced": {
            "method": "start_search",
            "description": "Busca geral avancada com mais profundidade.",
            "params": {
                "query": "How are AI agents changing enterprise workflows?",
                "topic": "general",
                "search_depth": "advanced",
                "max_results": 8,
                "include_answer": True,
                "include_raw_content": True,
                "include_images": True,
            },
        },
        "search_news_mode": {
            "method": "start_search",
            "description": "Busca em modalidade de noticias (topic=news).",
            "params": {
                "query": "Latest AI regulation updates",
                "topic": "news",
                "search_depth": "basic",
                "max_results": 6,
                "include_answer": True,
            },
        },
        "search_domain_filters": {
            "method": "start_search",
            "description": "Busca com filtros de dominios inclusos/excluidos.",
            "params": {
                "query": "Open-source LLM benchmarks",
                "topic": "general",
                "search_depth": "advanced",
                "max_results": 6,
                "include_domains": ["arxiv.org", "huggingface.co"],
                "exclude_domains": ["pinterest.com"],
                "include_answer": True,
            },
        },
        "get_context": {
            "method": "get_context",
            "description": "Retorna contexto otimizado para LLM.",
            "params": {
                "query": "Summarize key AI chip announcements in 2026",
                "search_depth": "advanced",
                "max_results": 5,
                "max_tokens": 1500,
                "topic": "news",
            },
        },
        "qna": {
            "method": "qna",
            "description": "Pergunta e resposta direta.",
            "params": {
                "query": "What is Tavily and when should it be used?",
                "search_depth": "basic",
                "topic": "general",
            },
        },
        "extract_content": {
            "method": "extract_content",
            "description": "Extrai conteudo de uma ou mais URLs.",
            "params": {
                "urls": [
                    "https://www.anthropic.com/news",
                    "https://openai.com/news",
                ],
                "extract_depth": "advanced",
                "format": "markdown",
            },
        },
        "map_site": {
            "method": "map_site",
            "description": "Mapeia estrutura de links de um site.",
            "params": {
                "url": "https://openai.com",
                "limit": 20,
            },
        },
        "crawl_site": {
            "method": "crawl_site",
            "description": "Crawl recursivo de um site.",
            "params": {
                "url": "https://openai.com",
                "limit": 30,
                "max_depth": 2,
                "extract_depth": "basic",
                "format": "markdown",
            },
        },
        "get_company": {
            "method": "get_company",
            "description": "Busca informacoes firmograficas.",
            "params": {
                "query": "OpenAI",
            },
        },
        "start_research": {
            "method": "start_research",
            "description": "Inicia pesquisa autonoma e retorna request_id.",
            "params": {
                "input": "Analyze AI copilots adoption in software teams.",
                "model": "gpt-4o-mini",
            },
        },
        "get_research_status": {
            "method": "get_research_status",
            "description": "Consulta status de pesquisa assincrona.",
            "params": {
                "request_id": "PUT_REQUEST_ID_HERE",
            },
        },
    }