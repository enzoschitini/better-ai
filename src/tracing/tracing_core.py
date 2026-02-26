from typing import Optional, Dict, Any
from src.tracing.logger_engine import LoggerEngine


class ApplicationTracing:
    def __init__(
        self,
        log_id: Optional[str] = None,
        flag: Optional[str] = None,
        file_name: Optional[str] = None,
        log_file_name: Optional[str] = None,
        show_info_logs: bool = False,
        show_metadata: bool = False,
        save_logs: bool = False,
        format_metadata: bool = False,
    ):
        self.enginer = LoggerEngine(
            log_id=log_id,
            flag=flag,
            file_name=file_name,
            log_file_name=log_file_name,
            show_info_logs=show_info_logs,
            show_metadata=show_metadata,
            save_logs=save_logs,
            format_metadata=format_metadata,
        )

    def INFO(
        self,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = None,
        show_info_logs: Optional[bool] = None,
        show_metadata: Optional[bool] = None,
    ):
        """
        INFO LEVEL

        Usado para registrar mensagens informativas gerais sobre o fluxo normal do aplicativo.
        Esses registros são úteis para acompanhar as etapas de execução e entender o comportamento esperado.

        Exemplos:
        - Início de um processo
        - Conclusão bem-sucedida de uma operação
        - Pontos de verificação importantes no fluxo de trabalho
        """
        self.enginer.log(
            "info",
            func_name=func_name,
            message=message,
            metadata=metadata,
            save_logs=save_logs,
            show_info_logs=show_info_logs,
            show_metadata=show_metadata,
        )

    def DEBUG(
        self,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = None,
        show_info_logs: Optional[bool] = None,
        show_metadata: Optional[bool] = None,
    ):
        """
        DEBUG LEVEL

        Utilizado para informações de diagnóstico detalhadas, geralmente úteis apenas durante o desenvolvimento.
        Ajuda os desenvolvedores a entender os estados internos e o fluxo de dados.

        Exemplos:
        - Valores de variáveis
        - Entradas/saídas de funções
        - Etapas intermediárias de processamento
        """
        self.enginer.log("debug", func_name=func_name, message=message, metadata=metadata,
                save_logs=save_logs, show_info_logs=show_info_logs,
                show_metadata=show_metadata)


    def WARNING(
        self,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = None,
        show_info_logs: Optional[bool] = None,
        show_metadata: Optional[bool] = None,
    ):
        """
        WARNING LEVEL

        Indica um problema potencial ou uma situação inesperada que não interrompe a execução, mas pode exigir atenção.

        Exemplos:
        - Uso obsoleto
        - Lógica de fallback sendo aplicada
        - Dados opcionais ausentes
        """
        self.enginer.log("warning", func_name=func_name, message=message, metadata=metadata,
                save_logs=save_logs, show_info_logs=show_info_logs,
                show_metadata=show_metadata)


    def ERROR(
        self,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = None,
        show_info_logs: Optional[bool] = None,
        show_metadata: Optional[bool] = None,
    ):
        """
        ERROR LEVEL

        Utilizado quando uma operação falha e afeta a funcionalidade esperada.
        O aplicativo pode continuar em execução, mas algo deu errado.

        Exemplos:
        - Chamada de API com falha
        - Exceção capturada
        - Falha na operação do banco de dados
        """
        self.enginer.log("error", func_name=func_name, message=message, metadata=metadata,
                save_logs=save_logs, show_info_logs=show_info_logs,
                show_metadata=show_metadata)


    def CRITICAL(
        self,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = None,
        show_info_logs: Optional[bool] = None,
        show_metadata: Optional[bool] = None,
    ):
        """
        CRITICAL LEVEL

        Utilizado para erros graves que podem causar a interrupção ou instabilidade do aplicativo.
        É necessária atenção imediata.

        Exemplos:
        - Falha do sistema
        - Dependência crítica indisponível
        - Risco de corrupção de dados
        """
        self.enginer.log("critical", func_name=func_name, message=message, metadata=metadata,
                save_logs=save_logs, show_info_logs=show_info_logs,
                show_metadata=show_metadata)

# python -m src.tracing.tracing_core