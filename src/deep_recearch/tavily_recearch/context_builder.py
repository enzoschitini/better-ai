
import os
from typing import Dict, Any, List, Optional, Dict, Any

from src.deep_recearch.tavily_recearch.tavily_core import TavilyDeepResearch

# python -m src.deep_recearch.tavily_recearch.context_builder

class TavilyContextBuilder:
    def __init__(
        self,
        researcher,
        min_score: float = 0.5,
        remove_keys: List[str] | None = None
    ):
        self.researcher = researcher
        self.min_score = min_score
        self.remove_keys = remove_keys or [
            "response_time",
            "follow_up_questions",
            "images",
            "request_id",
        ]

    # ---------- Pesquisa ----------
    def search(self, search_config: Dict[str, Any]) -> Dict[str, Any]:
        return self.researcher.start_search(search_config)

    # ---------- Filtros ----------
    def filter_results(self, result: Dict[str, Any]) -> Dict[str, Any]:
        filtered = {
            **result,
            "results": [
                item for item in result.get("results", [])
                if item.get("score", 0) >= self.min_score
            ],
        }

        # Remove chaves globais inúteis
        for key in self.remove_keys:
            filtered.pop(key, None)

        # Remove raw_content de cada resultado
        for item in filtered.get("results", []):
            item.pop("raw_content", None)

        return filtered

    # ---------- Markdown ----------
    def to_markdown(self, data: Dict[str, Any]) -> str:
        md = []

        # Consulta
        md.append("# Consulta")
        md.append(f"**Pergunta:**  \n{data.get('query', '')}\n")

        # Resposta
        md.append("---\n")
        md.append("## Resposta resumida")
        md.append(data.get("answer", "") + "\n")

        # Fontes
        md.append("---\n")
        md.append("## Fontes analisadas\n")

        for i, item in enumerate(data.get("results", []), start=1):
            md.append(f"### {i}. {item.get('title', 'Sem título')}")
            md.append(f"- **URL:** {item.get('url', '')}")
            md.append(
                f"- **Score de relevância:** {round(item.get('score', 0), 5)}\n"
            )
            md.append("**Conteúdo:**  ")
            md.append(item.get("content", "") + "\n")
            md.append("---\n")

        return "\n".join(md)

    # ---------- Pipeline completo ----------
    def build_context(self, search_config: Dict[str, Any]) -> str:
        raw_result = self.search(search_config)
        filtered_result = self.filter_results(raw_result)
        return self.to_markdown(filtered_result)


class TavilyResearchRunner:
    def __init__(
        self,
        builder,
        default_search_depth: str = "advanced",
        default_topic: str = "general",
        default_include_answer: bool = True,
    ):
        self.builder = builder
        self.default_search_depth = default_search_depth
        self.default_topic = default_topic
        self.default_include_answer = default_include_answer

    def build_search_config(
        self,
        *,
        query: str,
        max_results: int,
        search_depth: Optional[str] = None,
        topic: Optional[str] = None,
        include_answer: Optional[bool] = None,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not query:
            raise ValueError("`query` é obrigatório.")
        if max_results is None:
            raise ValueError("`max_results` é obrigatório.")

        config = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth or self.default_search_depth,
            "topic": topic or self.default_topic,
            "include_answer": (
                include_answer
                if include_answer is not None
                else self.default_include_answer
            ),
        }

        if extra_params:
            config.update(extra_params)

        return config

    def run(
        self,
        *,
        query: str,
        max_results: int,
        search_depth: Optional[str] = None,
        topic: Optional[str] = None,
        include_answer: Optional[bool] = None,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        search_config = self.build_search_config(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            topic=topic,
            include_answer=include_answer,
            extra_params=extra_params,
        )

        return self.builder.build_context(search_config)



if __name__ == "__main__":

    researcher = TavilyDeepResearch(
        api_key=os.getenv("TAVILY_API_KEY")
    )

    builder = TavilyContextBuilder(
        researcher=researcher,
        min_score=0.5
    )

    runner = TavilyResearchRunner(builder)

    markdown_context = runner.run(
        query="Quais as principais tendências de IA em 2026?",
        search_depth="advanced",
        max_results=2,
        topic="general",
        include_answer=True
    )

    print(markdown_context)
