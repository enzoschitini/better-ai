import json
from typing import Optional
from fastapi import HTTPException
from io import BytesIO

from src.content_parse.content_parsing_agent import ContentParsingAgent
from src.content_parse.config import DocumentParseConfig
from src.embedding.services.file_content_extractor import FileContentExtractor
from src.tokens_calculate.module import ModelPricing, ExchangeRateService
from src.database.no_relational_db.router import DocumentStore
from src.tracing.tracing_core import ApplicationTracing

tracer = ApplicationTracing(
    flag="DocumentParse",
    file_name="document_parse",
    log_file_name="parse",
)


class DocumentParse:
    """
    Classe responsável por orquestrar o processo de parsing de documentos,
    desde a extração do conteúdo do arquivo até o salvamento do resultado
    processado no banco de dados.

    Args:
        :param job_id (str): Identificador único do job de processamento.
        :param metadata (dict): Metadados associados ao documento a ser processado.
        :param schema (str): JSON string que define o esquema esperado para os dados.
        :param file_bytes (BytesIO): Conteúdo binário do arquivo a ser processado.
        :param file_extension (str): Extensão do arquivo (ex.: '.pdf', '.txt').
        :param config (Optional[str]): JSON string de configuração customizada para parsing. Default é None.

    Methods:
        run(): Executa o pipeline completo de parsing do documento e retorna a resposta da API.
    """

    def __init__(
        self,
        job_id: str,
        metadata: dict,
        schema: str,
        file_bytes: BytesIO,
        file_extension: str,
        config: Optional[str] = None,
    ):
        tracer.INFO(func_name="__init__", message=f"Initializing DocumentParse with job_id: {job_id}")
        self.job_id = job_id
        self.metadata = metadata
        self.schema = schema
        self.config = config
        self.file_bytes = file_bytes
        self.file_extension = file_extension

        system_settings = DocumentParseConfig()
        self.default_config = system_settings.default_config
        self.database_name = system_settings.database_name
        self.collection_name = system_settings.collection_name

    def run(self):
        """
        Executa todo o processo de parsing do documento, incluindo carregamento da configuração,
        extração do conteúdo do arquivo, parsing do conteúdo, cálculo dos custos relacionados,
        construção da resposta da API e salvamento dos dados no banco.

        Returns:
            dict: Resposta formatada pronta para ser retornada pela API.
        """
        self._load_schema_and_config()
        self._extract_file_content()
        self._parse_content()
        self._calculate_costs()
        self._build_response()
        self._save()

        tracer.INFO(func_name="run", message=f"Completed processing for job_id: {self.job_id}")
        return self.api_response

    def _load_schema_and_config(self):
        """
        Carrega e valida os dados JSON de metadata, schema e configuração personalizada,
        fundindo a configuração padrão com a qualquer configuração customizada passada.
        """
        # Set metadata
        try:
            self.metadata_data = json.loads(self.metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in metadata")

        try:
            self.schema_data = json.loads(self.schema)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in schema")

        if self.config:
            try:
                config_input = json.loads(self.config)
                self.config_data = {**self.default_config, **config_input}
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in config")
        else:
            self.config_data = self.default_config
        
        tracer.INFO(func_name="_load_schema_and_config", message="Loaded schema and configuration")
    
    def _extract_file_content(self):
        """
        Utiliza o extractor de conteúdo para extrair texto raw do arquivo fornecido,
        considerando sua extensão.
        """
        tracer.INFO(func_name="_extract_file_content", message=f"Extracting content from file with extension: {self.file_extension}")
        # Extract file content
        extractor = FileContentExtractor(
            file_bytes=self.file_bytes,
            file_extension=self.file_extension
        )
        self.result_extract = extractor.extract()

        if self.result_extract["response"] == None or self.result_extract["response"].strip() == "":
            raise HTTPException(status_code=400, detail="Failed to extract content from file")
        tracer.INFO(func_name="_extract_file_content", message="Content extracted successfully from file")
    
    def _parse_content(self):
        """
        Executa o agente de parsing para extrair dados formatados conforme o schema,
        a partir do conteúdo extraído do arquivo.
        """
        # Parse content with agent
        tracer.INFO(func_name="_parse_content", message="Parsing content with agent")
        agent_parser = ContentParsingAgent(
            input_data={
                "file_content": self.result_extract["response"]
            },
            output_data=self.schema_data,
            config_data=self.config_data
        )

        raw_content_parsed = agent_parser.run_agent()
        self.agent_response = agent_parser.format_response(raw_content_parsed)
        tracer.INFO(func_name="_parse_content", message="Content parsed successfully with agent")
    
    def _calculate_costs(self):
        """
        Calcula os custos de processamento com base no modelo utilizado,
        tokens utilizados na entrada e saída, e converte para BRL utilizando a taxa de câmbio atual.
        """
        # Calculate tokens and cost
        self.info_process = self.agent_response.get("metadata", {})

        model_pricing = ModelPricing(self.info_process.get("model").get("id"))
        self.input_cost = model_pricing.input_rate_per_token() * self.info_process.get("tokens").get("input_tokens", 0)
        self.output_cost = model_pricing.output_rate_per_token() * self.info_process.get("tokens").get("output_tokens", 0)

        service = ExchangeRateService()
        self.rate = service.get_usd_rate()
        tracer.DEBUG(
            func_name="_calculate_costs",
            message="Calculated costs",
            metadata={
                "model": self.info_process.get("model").get("id"),
                "input_tokens": self.info_process.get("tokens").get("input_tokens", 0),
                "output_tokens": self.info_process.get("tokens").get("output_tokens", 0),
                "input_cost_usd": self.input_cost,
                "output_cost_usd": self.output_cost,
                "exchange_rate_usd_brl": self.rate
            }
        )

    def _build_response(self):
        """
        Constrói o payload de resposta da API e o payload para salvar no banco,
        incluindo conteúdo processado e informações detalhadas do processo.
        """
        # Formatte response result + process
        formatted_info_process = {
            "model": self.info_process.get("model"),
            "tokens": self.info_process.get("tokens"),
            "cost": {
                "input_cost_usd": self.input_cost,
                "output_cost_usd": self.output_cost,
                "total_cost_usd": self.input_cost + self.output_cost,
                "total_cost_brl": (self.input_cost + self.output_cost) * self.rate
            },
            "duration_s": self.info_process.get("duration_s"),
        }

        self.save_payload = {
            "job_id": self.job_id,
            "metadata": self.metadata_data,
            "content": self.agent_response.get("content"),
            "process_info": formatted_info_process
        }

        self.api_response = {
            "job_id": self.job_id,
            "content": self.agent_response.get("content"),
        }

        tracer.DEBUG(
            func_name="_build_response",
            message="Built API response and save payload",
            metadata={
                "api_response": self.api_response,
                "save_payload": self.save_payload
            }
        )
    
    def _save(self):
        """
        Persiste o resultado do processamento no banco de dados NoSQL configurado,
        utilizando o payload estruturado previamente.
        """
        # Save processed result in database
        document_store = DocumentStore()
        document_store.save_payload(
            database_name=self.database_name,
            collection_name=self.collection_name,
            payload=self.save_payload
        )
        tracer.INFO(func_name="_save", message="Saved processed result in database")
