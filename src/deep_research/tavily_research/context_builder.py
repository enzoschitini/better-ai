import os
from typing import Dict, Any, List, Optional, Dict, Any

from src.deep_research.tavily_research.tavily_core import TavilyDeepResearch
from src.tracing.tracing_core import ApplicationTracing

tracer = ApplicationTracing(
    flag="Deep Research",
    file_name="context_builder.py",
    show_info_logs=False
)

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
        try:
            research_results = self.researcher.start_search(search_config)

            """
            tracer.INFO(
                func_name="search",
                message="Web search results",
                metadata=research_results
            )
            """

            return research_results

        except Exception as e:
            message = "Error during web search"
            tracer.ERROR(
                func_name="search",
                message=message,
                metadata={
                    "error": str(e),
                    "search_config": search_config
                }
            )

            raise RuntimeError(f"{message}: {str(e)}")

    # ---------- Filtros ----------
    def filter_results(self, research_results: Dict[str, Any]) -> Dict[str, Any]:
        try:
            filtered = {
                **research_results,
                "results": [
                    item for item in research_results.get("results", [])
                    if isinstance(item, dict) and item.get("score", 0) >= self.min_score
                ],
            }

            # Remove chaves globais inúteis
            for key in self.remove_keys:
                filtered.pop(key, None)

            # Remove raw_content de cada resultado
            for item in filtered.get("results", []):
                if isinstance(item, dict):
                    item.pop("raw_content", None)
            
            """
            tracer.INFO(
                func_name="filter_results",
                message="Web search results filtered",
                metadata=filtered
            )
            """

            return filtered

        except Exception as e:
            message = "Error filtering web search results"
            tracer.ERROR(
                func_name="filter_results",
                message=message,
                metadata={
                    "error": str(e),
                    "research_results": research_results
                },
            )

            raise RuntimeError(f"{message}: {str(e)}")

    # ---------- Markdown ----------
    def to_markdown(self, data: Dict[str, Any]) -> str:
        try:
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

            results = data.get("results", [])

            for i, item in enumerate(results, start=1):
                if not isinstance(item, dict):
                    continue

                score = item.get("score", 0)
                try:
                    score = round(float(score), 5)
                except Exception:
                    score = 0

                md.append(f"### {i}. {item.get('title', 'Sem título')}")
                md.append(f"- **URL:** {item.get('url', '')}")
                md.append(f"- **Score de relevância:** {score}\n")
                md.append("**Conteúdo:**  ")
                md.append(item.get("content", "") + "\n")
                md.append("---\n")

            markdown = "\n".join(md)

            """
            tracer.INFO(
                func_name="to_markdown",
                message="Web search results to markdown",
                metadata=markdown
            )
            """

            return markdown

        except Exception as e:
            message = "Error converting web search results to markdown"
            tracer.ERROR(
                func_name="to_markdown",
                message=message,
                metadata={
                    "error": str(e),
                    "data": data
                }
            )

            raise RuntimeError(f"{message}: {str(e)}")
    
    def get_web_sites(self, filtered_result: dict) -> list:
        urls = []
        for result in filtered_result["results"]:
            urls.append(result["url"])

        """
        tracer.INFO(
            func_name="get_web_sites",
            message="Links to analyzed sites",
            metadata=urls
        )
        """
        
        return urls

    # ---------- Pipeline completo ----------
    def build_context(self, search_config: Dict[str, Any]) -> str:
        try:
            raw_research_results = self.search(search_config)
            filtered_result = self.filter_results(raw_research_results)
            markdown = self.to_markdown(filtered_result)
            urls = self.get_web_sites(filtered_result)

            context = {
                "markdown": markdown,
                "urls": urls,
            }

            """
            tracer.INFO(
                func_name="build_context",
                message="Research context built successfully",
                metadata={
                    "query": search_config.get("query"),
                    "context": context,
                }
            )
            """

            return context

        except Exception as e:
            message = "Error building research context"
            tracer.ERROR(
                func_name="build_context",
                message=message,
                metadata={
                    "error": str(e),
                    "search_config": search_config
                }
            )

            raise RuntimeError(f"{message}: {str(e)}")


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
    from dotenv import load_dotenv

    load_dotenv()

    researcher = TavilyDeepResearch()

    builder = TavilyContextBuilder(
        researcher=researcher,
        min_score=0.5
    )

    runner = TavilyResearchRunner(builder)

    context = runner.run(
        query="Quais as principais tendências de IA em 2026?",
        search_depth="advanced",
        max_results=2,
        topic="general",
        include_answer=True
    )

    print(f"\n\n --------------------------------------------\n{context}")

    # python -m src.deep_research.tavily_research.context_builder
