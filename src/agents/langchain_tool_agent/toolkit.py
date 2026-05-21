# app/agent/build/retrieve.py

from __future__ import annotations

from datetime import datetime
from typing import Any, List

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────
# COLETOR DE DADOS LATERAIS (não passam para o LLM)
# ──────────────────────────────────────────────────────────────
class SideChannelEntry(BaseModel):
    tool_name: str
    payload: Any                   # qualquer estrutura que a tool queira guardar
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolResponseCollector:
    """
    Armazena dados laterais emitidos pelas tools.
    Esses dados NÃO aparecem no contexto do LLM — só no payload da entry.
    """

    def __init__(self) -> None:
        self._entries: List[SideChannelEntry] = []

    def add(self, tool_name: str, payload: Any) -> None:
        self._entries.append(SideChannelEntry(tool_name=tool_name, payload=payload))

    def get_all(self) -> List[SideChannelEntry]:
        return list(self._entries)

    def get_by_tool(self, tool_name: str) -> List[SideChannelEntry]:
        return [e for e in self._entries if e.tool_name == tool_name]

    def clear(self) -> None:
        self._entries.clear()

    def __repr__(self) -> str:  # facilita debug
        return f"ToolResponseCollector({len(self._entries)} entries)"


# ──────────────────────────────────────────────────────────────
# SCHEMAS DE INPUT (Pydantic) — evita que LangChain injete args errados
# ──────────────────────────────────────────────────────────────
class SimilaritySearchInput(BaseModel):
    query: str = Field(..., description="Mansegm completa do usuário para busca semântica")
    k: int = Field(..., description="Número máximo de resultados")


class DatetimeInput(BaseModel):
    timezone: str = Field(default="America/Sao_Paulo", description="Fuso horário desejado")


# ──────────────────────────────────────────────────────────────
# TOOLKIT
# ──────────────────────────────────────────────────────────────
class Toolkit:
    """
    Cada tool é uma closure que:
      • retorna ao LLM apenas o texto relevante
      • grava dados arbitrários no `collector` (score bruto, metadados, etc.)
    """

    def __init__(self, metadata: dict = None) -> None:
        self.collector = ToolResponseCollector()
        self.metadata = metadata or {}

    # ── interfaces pública ─────────────────────────────────────

    def insert_metadata(self, dict_data: dict) -> None:
        """Permite inserir ou atualizar metadados do toolkit."""
        self.metadata.update(dict_data)
    
    def get_collector(self) -> ToolResponseCollector:
        """Retorna o coletor para uso externo (ex: AgentExecutor)."""
        return self.collector

    def get_tools(self) -> List[BaseTool]:
        """Retorna as tools prontas para o AgentExecutor."""
        return [
            self._make_similarity_search(),
            self._make_current_datetime(),
        ]

    # ── factories privadas ────────────────────────────────────

    def _make_similarity_search(self) -> BaseTool:
        collector = self.collector          # captura por referência

        def _run(query: str, k: int = 4) -> str:
            # ① resultado que vai para o LLM
            llm_context = (
                "Score: 0.95 | Content: Enzo é um desenvolvedor de software com "
                "experiência em Python e inteligência artificial.\n"
                "Score: 0.89 | Content: Ele trabalhou em projetos de NLP e construção "
                "de chatbots usando LangChain.\n"
                "Score: 0.22 | Content: Enzo gosta de viajar e cozinhar nas horas vagas."
            )

            # ② dados laterais — NÃO chegam ao LLM
            collector.add(
                tool_name="similarity_search",
                payload={
                    "created_by": self.metadata.get("created_by", "unknown"),
                    "query": query,
                    "k": k,
                    "raw_hits": [
                        {"text": "Enzo é um dev Python / IA", "score": 0.95},
                        {"text": "Projetos de NLP / LangChain", "score": 0.89},
                        {"text": "Hobbies: viajar, cozinhar",  "score": 0.22},
                    ],
                },
            )

            return llm_context  # só isso vai para o contexto do modelo

        return StructuredTool.from_function(
            func=_run,
            name="get_similarity_search",
            description=(
                "Realiza busca semântica na base de conhecimento. "
                "Use para perguntas sobre pessoas, projetos ou contextos específicos."
            ),
            args_schema=SimilaritySearchInput,
        )

    def _make_current_datetime(self) -> BaseTool:
        collector = self.collector

        def _run(timezone: str = "America/Sao_Paulo") -> str:
            now = datetime.now()

            # ① o que o LLM vê
            llm_text = (
                f"Data: {now.strftime('%d/%m/%Y')}\n"
                f"Hora: {now.strftime('%H:%M:%S')}\n"
                f"Dia da semana: {now.strftime('%A')}\n"
                f"Fuso horário configurado: {timezone}"
            )

            # ② dado lateral — timestamp como objeto Python (não serializado)
            collector.add(
                tool_name="current_datetime",
                payload={"datetime_obj": now, "timezone_requested": timezone},
            )

            return llm_text

        return StructuredTool.from_function(
            func=_run,
            name="get_current_datetime",
            description=(
                "Retorna a data e hora atual. "
                "Use quando o usuário perguntar sobre horário, data ou dia da semana."
            ),
            args_schema=DatetimeInput,
        )
