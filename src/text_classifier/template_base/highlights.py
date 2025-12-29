import json
import logging
import time
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from src.text_classifier.template_base.prompt_loader import PromptLoader

from dotenv import load_dotenv
import os

load_dotenv()

class HighlightsExtractor:
    def __init__(self):
        self.loader = PromptLoader("src/text_classifier.template_base/prompt.yaml")

        class Resposta(BaseModel):
            titulo_do_video: str = Field(
                title=self.loader.get("titulo_do_video.title"),
                description=self.loader.get("titulo_do_video.description"),
                examples=self.loader.get("titulo_do_video.examples")
            )

            resumo_do_video: str = Field(
                title=self.loader.get("resumo_do_video.title"),
                description=self.loader.get("resumo_do_video.description"),
                examples=self.loader.get("resumo_do_video.examples")
            )

            pontos_positivos: str = Field(
                title=self.loader.get("pontos_positivos.title"),
                description=self.loader.get("pontos_positivos.description"),
                examples=self.loader.get("pontos_positivos.examples")
            )

            pontos_negativos: str = Field(
                title=self.loader.get("pontos_negativos.title"),
                description=self.loader.get("pontos_negativos.description"),
                examples=self.loader.get("pontos_negativos.examples")
            )

            marcas_mencionadas: str = Field(
                title=self.loader.get("marcas_mencionadas.title"),
                description=self.loader.get("marcas_mencionadas.description"),
                examples=self.loader.get("marcas_mencionadas.examples")
            )

            produtos_mencionados: str = Field(
                title=self.loader.get("produtos_mencionados.title"),
                description=self.loader.get("produtos_mencionados.description"),
                examples=self.loader.get("produtos_mencionados.examples")
            )

            explicacao_geral_do_video: str = Field(
                title=self.loader.get("explicacao_geral_do_video.title"),
                description=self.loader.get("explicacao_geral_do_video.description"),
                examples=self.loader.get("explicacao_geral_do_video.examples")
            )

            ambiente_do_video: str = Field(
                title=self.loader.get("ambiente_do_video.title"),
                description=self.loader.get("ambiente_do_video.description"),
                examples=self.loader.get("ambiente_do_video.examples")
            )

            cenario_principal: str = Field(
                title=self.loader.get("cenario_principal.title"),
                description=self.loader.get("cenario_principal.description"),
                examples=self.loader.get("cenario_principal.examples")
            )

            expressao_facial: str = Field(
                title=self.loader.get("expressao_facial.title"),
                description=self.loader.get("expressao_facial.description"),
                examples=self.loader.get("expressao_facial.examples")
            )

            tom_de_voz: str = Field(
                title=self.loader.get("tom_de_voz.title"),
                description=self.loader.get("tom_de_voz.description"),
                examples=self.loader.get("tom_de_voz.examples")
            )

            musica_trilha_sonora: str = Field(
                title=self.loader.get("musica_trilha_sonora.title"),
                description=self.loader.get("musica_trilha_sonora.description"),
                examples=self.loader.get("musica_trilha_sonora.examples")
            )

            emojis_apresentados: str = Field(
                title=self.loader.get("emojis_apresentados.title"),
                description=self.loader.get("emojis_apresentados.description"),
                examples=self.loader.get("emojis_apresentados.examples")
            )

            legendas_utilizadas: str = Field(
                title=self.loader.get("legendas_utilizadas.title"),
                description=self.loader.get("legendas_utilizadas.description"),
                examples=self.loader.get("legendas_utilizadas.examples")
            )

            apelo_emocional: str = Field(
                title=self.loader.get("apelo_emocional.title"),
                description=self.loader.get("apelo_emocional.description"),
                examples=self.loader.get("apelo_emocional.examples")
            )

            identificacao_de_tendencias: str = Field(
                title=self.loader.get("identificacao_de_tendencias.title"),
                description=self.loader.get("identificacao_de_tendencias.description"),
                examples=self.loader.get("identificacao_de_tendencias.examples")
            )


        self.output_parser = PydanticOutputParser(
            pydantic_object=Resposta
        )

        self.prompt = PromptTemplate(
            template=(
                "Responda de forma estruturada.\n"
                "{format_instructions}\n"
                "Input: {input}"
            ),
            input_variables=["input"],
            partial_variables={
                "format_instructions": self.output_parser.get_format_instructions()
            },
        )


        self.llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0.5
        )

        """
        # Original:

        self.llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0.5
        )

        # Test 1: (Lento)
        self.llm = ChatOpenAI(
            model="gpt-4.1",
            temperature=2.0,
            top_p=1.0
        )

        # Teste 2: (Equilibrado)
        self.llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=1.3,
            top_p=1.0,
            presence_penalty=0.8,
            frequency_penalty=0.4
        )

        # Teste 3: (Ultra criativo)
        self.llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=1.5,
            top_p=1.0,
            presence_penalty=1.0,
            frequency_penalty=0.6
        )
        """

        self.chain = self.prompt | self.llm | self.output_parser

    def parse_prompt(self, objetivo, transcription):
        prompt = self.loader.get(
            "parse_highlights",
            transcription=transcription
        )

        prompt_template = PromptTemplate.from_template(prompt)

        return prompt_template.format(
            objetivo=objetivo,
            transcription=transcription
        )

    # === Agora o scraper_highlights vem de um .txt ===
    def extract(self, objetivo, txt_path: str):
        txt_path = f"src/text_classifier.template_base/{txt_path}"
        
        if not os.path.exists(txt_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {txt_path}")

        with open(txt_path, "r", encoding="utf-8") as file:
            scraper_highlights = file.read().strip()

        input_prompt = self.parse_prompt(objetivo, scraper_highlights)
        resposta = self.chain.invoke({"input": input_prompt})

        return resposta.model_dump()


# ========================
# Exemplo de uso
# ========================

"""

# Início da metrificação
start_time = time.perf_counter()

query = "Gere highlights com base na transcrição do vídeo"
txt_path = "n8n.txt"

parser = HighlightsExtractor()
resultado = parser.extract(query, txt_path)

print(json.dumps(resultado, indent=2, ensure_ascii=False))

# Fim da metrificação
end_time = time.perf_counter()
execution_time = end_time - start_time

minutes = int(execution_time // 60)
seconds = execution_time % 60

print(f"\n⏱ Tempo total de execução: {minutes} min {seconds:.2f} s")


"""

# python -m src.text_classifier.template_base.highlights













