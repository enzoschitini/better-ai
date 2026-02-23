import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from src.utils.unique_id_factory import IDGenerator


class ApplicationTracing:
    def __init__(
        self,
        log_id: Optional[str] = IDGenerator.timestamp(prefix="log_"),
        flag: Optional[str] = None,
        file_name: Optional[str] = None,
        show_info_logs: bool = False,
        show_metadata: bool = False,
        save_logs: bool = False,
        format_metadata: bool = False,
    ):
        self.log_id = log_id
        self.flag = flag or "ApplicationTracing"
        self.file_name = file_name

        self.show_info_logs = show_info_logs
        self.show_metadata = show_metadata

        self.save_logs = save_logs
        self.format_metadata = format_metadata

        self.logger = self._setup_logger()

    # =========================================================
    # LOGGER CONFIGURATION
    # =========================================================
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.flag)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        # limpa handlers antigos
        if logger.handlers:
            logger.handlers.clear()

        formatter = logging.Formatter(
            #"%(asctime)s | %(levelname)s | %(name)s | %(filename)s | %(message)s"
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        # =========================
        # FILE HANDLER
        # =========================
        if self.save_logs:
            file_handler = logging.FileHandler("app.log")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # =========================
        # CONSOLE HANDLER
        # =========================
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        if self.show_info_logs:
            console_handler.setLevel(logging.DEBUG)
        else:
            console_handler.setLevel(logging.ERROR)

        logger.addHandler(console_handler)

        return logger

    def _refresh_logger(self):
        """
        Atualiza handlers dinamicamente caso flags mudem em runtime
        """
        self.logger = self._setup_logger()

    # =========================================================
    # metadata
    # =========================================================
    def _format_metadata(self, metadata: Optional[Dict[str, Any]]) -> Optional[str]:
        if not metadata or not self.show_metadata:
            return None

        try:
            if self.format_metadata:
                return f"\n{json.dumps(metadata, indent=4, ensure_ascii=False)}\n"
            return str(metadata)
        except Exception:
            return str(metadata)

    # =========================================================
    # MESSAGE BUILDER
    # =========================================================
    def _build_message(
        self,
        func_name: Optional[str],
        message: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> str:
        parts = []

        # base message
        if func_name:
            parts.append(f"{func_name}()")

        if message:
            parts.append(message)

        # metadata
        metadata_str = self._format_metadata(metadata)
        if metadata_str:
            if self.format_metadata:
                parts.append(f"\nmetadata:\n{metadata_str}")
            else:
                parts.append(f"metadata={metadata_str}")

        # metadata
        if self.file_name:
            parts.append(f"file={self.file_name}")

        if self.log_id:
            parts.append(f"log_id={self.log_id}")

        return " | ".join(parts)

    # =========================================================
    # MONGO metadata BUILDER
    # =========================================================
    def _build_mongo_metadata(
        self,
        level: Optional[str],
        func_name: Optional[str],
        message: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> str:

        now = datetime.now()
        log_time_str = now.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]  # corta para milissegundos
        
        mongo_metadata = {
            "log_id": self.log_id,
            "level": level.upper(),
            "flag": self.flag,
            "func_name": func_name,
            "message": message,
            "metadata": metadata,
            "file_name": self.file_name,
            "time": log_time_str
        }

        print(f"\n\n_build_mongo_metadata:\n {json.dumps(mongo_metadata, indent= 4)}\n\n")

        return mongo_metadata

    # =========================================================
    # DECISION ENGINE
    # =========================================================
    def _should_log(
        self,
        save_logs: Optional[bool],
        show_info: Optional[bool],
    ) -> bool:
        save_logs = self.save_logs if save_logs is None else save_logs
        show_info = (
            self.show_info_logs
            if show_info is None
            else show_info
        )

        return save_logs or show_info

    # =========================================================
    # CORE LOG METHOD
    # =========================================================
    def _log(
        self,
        level: str,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = None,
        show_info_logs: Optional[bool] = None,
        show_metadata: Optional[bool] = None,
    ):
        # Atualiza flags se vierem no método
        if show_metadata is not None:
            self.show_metadata = show_metadata

        if save_logs is not None:
            self.save_logs = save_logs

        if show_info_logs is not None:
            self.show_info_logs = show_info_logs

        # Atualiza logger caso flags mudem
        self._refresh_logger()

        msg = self._build_message(func_name, message, metadata)
        mongo_metadata = self._build_mongo_metadata(level, func_name, message, metadata)

        log_method = getattr(self.logger, level.lower())

        log_method(
            msg,
            extra={
                "log_id": self.log_id,
                "file_name": self.file_name,
            },
        )

    # =========================================================
    # PUBLIC METHODS
    # =========================================================

    def INFO(
        self,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = False,
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
        self._log(
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
        save_logs: Optional[bool] = False,
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
        self._log("debug", func_name=func_name, message=message, metadata=metadata,
                save_logs=save_logs, show_info_logs=show_info_logs,
                show_metadata=show_metadata)


    def WARNING(
        self,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = False,
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
        self._log("warning", func_name=func_name, message=message, metadata=metadata,
                save_logs=save_logs, show_info_logs=show_info_logs,
                show_metadata=show_metadata)


    def ERROR(
        self,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = False,
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
        self._log("error", func_name=func_name, message=message, metadata=metadata,
                save_logs=save_logs, show_info_logs=show_info_logs,
                show_metadata=show_metadata)


    def CRITICAL(
        self,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = False,
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
        self._log("critical", func_name=func_name, message=message, metadata=metadata,
                save_logs=save_logs, show_info_logs=show_info_logs,
                show_metadata=show_metadata)

tracer = ApplicationTracing(
    log_id="log_1234", 
    flag="TracingCore", 
    file_name="tracing_core.py",
    show_info_logs=True,
    show_metadata=True,
    save_logs=False,
    format_metadata=False
)

tracer.INFO(
    func_name="create_user",
    message="App Init"
)

tracer.DEBUG(
    func_name="create_user",
    message="User created",
    metadata={"user": "Enzo"},
    save_logs=True
)

tracer.WARNING(
    func_name="create_user",
    message="User created",
    metadata={"user": "Enzo"}
)

tracer.ERROR(
    func_name="create_user",
    message="User created",
    metadata={"user": "Enzo"}
)

tracer.CRITICAL(
    func_name="create_user",
    message="User created",
    metadata={"user": "Enzo"}
)

# Prossimi passaggi:
# -------------------- #
# 1. Eseguire delle provere per capire se le funzionalità sono giuste
# 2. Fare un ripasso e aggiustare il codice
# 3. Sistemare le classi


#print(IDGenerator.timestamp(prefix="log_"))

"""
1. Short metadata -> Bool
"""


"""



    def DEBUG(self, 
             func_name:str = None, 
             message:str = None,
             save: bool = False):
        print(
            f"{time.time()} | INFO | {func_name}() | {message} | {self.file_name} | {self.log_id}"
        )

    def WARNING(self, 
             func_name:str = None, 
             message:str = None,
             save: bool = False):
        print(
            f"{time.time()} | INFO | {func_name}() | {message} | {self.file_name} | {self.log_id}"
        )

    def ERROR(self, 
             func_name:str = None, 
             message:str = None,
             save: bool = False):
        print(
            f"{time.time()} | INFO | {func_name}() | {message} | {self.file_name} | {self.log_id}"
        )

    def CRITICAL(self, 
             func_name:str = None, 
             message:str = None,
             save: bool = False):
        print(
            f"{time.time()} | INFO | {func_name}() | {message} | {self.file_name} | {self.log_id}"
        )
"""

# python -m src.tracing.tracing_core