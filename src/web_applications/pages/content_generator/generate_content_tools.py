
import streamlit as st
from src.content_generation.module import GenerateContent, ContentBatchOutput

class GenerateContentTools:
    """Utility class to configure, generate, and expose AI-generated content data."""

    def __init__(self, config: dict, show: bool = False):
        """
        Initialize content generation settings from the provided configuration.

        Args:
            config: Dictionary containing all generation and filtering parameters.
            show: Whether to display the loaded configuration in the Streamlit UI.
        """
        self.config = config

        self.objective = config["objective_input"]
        self.extra_requirements = config["extra_requirements"]
        self.model_id = config["llm_model_id"]
        self.language_id = config.get("language_id", "livre")
        self.language_prompt = config.get("language_prompt", "")
        self.extra_requirements = self._compose_extra_requirements()
        self.filter_search = config["database"]["filter_search"]
        self.content_count = config["content_count"]
        self.max_results = config.get("max_results", 5)
        self.body_min_chars, self.body_max_chars = config["content_size_range"]
        self.generated_content = None

        if show:
            self._show_config()

    def _show_config(self):
        """Render the current configuration values to the Streamlit interface."""
        st.write(f"Objetivo: {self.objective}")
        st.write(f"Requisitos extras: {self.extra_requirements}")
        st.write(f"Modelo de LLM: {self.model_id}")
        st.write(f"Idioma: {self.language_id}")
        st.write(f"Prompt do idioma: {self.language_prompt}")
        st.write(f"Filter search: {self.filter_search}")
        st.write(f"Quantidade de conteúdo: {self.content_count}")
        st.write(f"Máximo de resultados: {self.max_results}")
        st.write(f"Faixa de tamanho: {self.body_min_chars} a {self.body_max_chars} caracteres")

    def _compose_extra_requirements(self) -> str:
        """
        Combine base extra requirements with the optional language instruction.

        Returns:
            A single formatted instruction string.
        """
        try:
            base_requirements = (self.extra_requirements or "").strip()

            language_instruction = (self.language_prompt or "").strip()
            if not language_instruction:
                return base_requirements

            if not base_requirements:
                return f"{language_instruction}"

            return f"{base_requirements}\n\n{language_instruction}"
        except Exception as e:
            st.error(f"Erro ao compor requisitos extras: {e}")
            return self.extra_requirements

    def generate_content(self, prompt: str):
        """
        Generate content using the configured model and retrieval settings.

        Args:
            prompt: The user query used as the generation input.

        Returns:
            Generated content payload on success, otherwise None.
        """
        try:
            generator = GenerateContent(
                model_id=self.model_id,
                filter_search=self.filter_search
            )

            generated_content = generator.generate(
                query=prompt,
                objective=self.objective,
                max_results=self.max_results,
                content_count=self.content_count,
                body_min_chars=self.body_min_chars,
                body_max_chars=self.body_max_chars,
                extra_requirements=self.extra_requirements,
            )
            self.generated_content = generated_content
            return generated_content
        except Exception as e:
            st.error(f"Erro ao gerar conteúdo: {e}")
            self.generated_content = None
            return None
    
    def get_contents(self):
        """
        Extract generated content items in a normalized list format.

        Returns:
            A list of content items represented as dictionaries.

        Raises:
            TypeError: If the stored generated content type is not supported.
        """
        content_data = self.generated_content
        if content_data is None:
            return []

        if isinstance(content_data, ContentBatchOutput):
            return [item.model_dump() for item in content_data.items]

        if isinstance(content_data, dict):
            items = content_data.get("items", [])
            return [item.model_dump() if hasattr(item, "model_dump") else item for item in items]

        raise TypeError(f"Unsupported generated content type: {type(content_data).__name__}")

    def get_relevant_docs(self):
        """
        Return document names used as relevant sources during generation.

        Returns:
            A list with source document names.
        """
        try:
            content_data = self.generated_content
            documents = []

            if content_data is None:
                return documents

            if isinstance(content_data, ContentBatchOutput):
                relevant_docs = content_data.relevant_docs
            elif isinstance(content_data, dict):
                relevant_docs = content_data.get("relevant_docs", [])
            else:
                raise TypeError(f"Unsupported generated content type: {type(content_data).__name__}")

            for document in relevant_docs:
                if isinstance(document, dict):
                    file_name = document.get("name", "Unknown")
                else:
                    file_name = getattr(document, "name", "Unknown")
                documents.append(file_name)
            return documents
        except Exception as e:
            st.error(f"Erro ao obter documentos relevantes: {e}")
            return []

    def get_latency(self):
        """
        Get the generation latency rounded to two decimal places.

        Returns:
            The latency value in seconds, or None when unavailable.

        Raises:
            TypeError: If the stored generated content type is not supported.
        """
        content_data = self.generated_content
        if content_data is None:
            return None

        if isinstance(content_data, ContentBatchOutput):
            if content_data.latency is None:
                return None
            return round(float(content_data.latency), 2)
        elif isinstance(content_data, dict):
            latency_value = content_data.get("latency")
            if latency_value is None:
                return None
            return round(float(latency_value), 2)
        else:
            raise TypeError(f"Unsupported generated content type: {type(content_data).__name__}")
