import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from src.utils.unique_id_factory import IDGenerator




class PayloadBuilder:
    def __init__(
        self,
        log_id: Optional[str] = None,
        flag: Optional[str] = None,
        file_name: Optional[str] = None,
        format_metadata: bool = False,
    ):
        self.log_id = log_id
        self.flag = flag
        self.file_name = file_name
        self.format_metadata = format_metadata

    # =========================================================
    # METADATA FORMAT
    # =========================================================
    def format_metadata_payload(
        self,
        metadata: Optional[Dict[str, Any]],
        show_metadata: bool,
    ) -> Optional[str]:
        if not metadata or not show_metadata:
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
    def build_message(
        self,
        func_name: Optional[str],
        message: Optional[str],
        metadata: Optional[Dict[str, Any]],
        show_metadata: bool,
    ) -> str:
        parts = []

        if func_name:
            parts.append(f"{func_name}()")

        if message:
            parts.append(message)

        # metadata
        metadata_str = self.format_metadata_payload(metadata, show_metadata)
        if metadata_str:
            if self.format_metadata:
                parts.append(f"\nmetadata:\n{metadata_str}")
            else:
                parts.append(f"metadata={metadata_str}")

        if self.file_name:
            parts.append(f"file={self.file_name}")

        if self.log_id:
            parts.append(f"log_id={self.log_id}")

        return " | ".join(parts)

    # =========================================================
    # MONGO METADATA
    # =========================================================
    def build_mongo_payload(
        self,
        level: str,
        func_name: Optional[str],
        message: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:

        now = datetime.now()
        log_time_str = now.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

        return {
            "log_id": self.log_id,
            "level": level.upper(),
            "flag": self.flag,
            "func_name": func_name,
            "message": message,
            "metadata": metadata,
            "file_name": self.file_name,
            "time": log_time_str,
        }














class LoggerEngine:
    def __init__(
        self,
        log_id: Optional[str] = None,
        flag: Optional[str] = None,
        file_name: Optional[str] = None,
        show_info_logs: bool = False,
        show_metadata: bool = False,
        save_logs: bool = False,
        format_metadata: bool = False,
    ):
        self.log_id = log_id or IDGenerator.timestamp(prefix="log_")
        self.flag = flag or "ApplicationTracing"
        self.file_name = file_name

        self.show_info_logs = show_info_logs
        self.show_metadata = show_metadata
        self.save_logs = save_logs
        self.format_metadata = format_metadata

    # =========================================================
    # CONFIG RESOLVER
    # =========================================================
    def _resolve_config(
        self,
        save_logs: Optional[bool],
        show_info_logs: Optional[bool],
        show_metadata: Optional[bool],
    ):
        return {
            "save_logs": self.save_logs if save_logs is None else save_logs,
            "show_info_logs": self.show_info_logs if show_info_logs is None else show_info_logs,
            "show_metadata": self.show_metadata if show_metadata is None else show_metadata,
        }

    # =========================================================
    # PAYLOAD BUILDER
    # =========================================================
    def _build_payloads(
        self,
        level: str,
        func_name: Optional[str],
        message: Optional[str],
        metadata: Optional[Dict[str, Any]],
        show_metadata: bool,
    ):
        builder = PayloadBuilder(
            log_id=self.log_id,
            flag=self.flag,
            file_name=self.file_name,
            format_metadata=self.format_metadata,
        )

        msg = builder.build_message(
            func_name, message, metadata, show_metadata
        )

        mongo_metadata = builder.build_mongo_payload(
            level, func_name, message, metadata
        )

        return msg, mongo_metadata

    # =========================================================
    # LOGGER FACTORY
    # =========================================================
    def _get_logger(self, save_logs: bool, show_info_logs: bool) -> logging.Logger:
        logger = logging.getLogger(self.flag)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        if logger.handlers:
            logger.handlers.clear()

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        # FILE
        if save_logs:
            file_handler = logging.FileHandler("app.log")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # CONSOLE
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if show_info_logs else logging.ERROR)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    # =========================================================
    # EMIT LOG
    # =========================================================
    def _emit_log(self, logger: logging.Logger, level: str, message: str):
        log_method = getattr(logger, level.lower())
        log_method(
            message,
            extra={
                "log_id": self.log_id,
                "file_name": self.file_name,
            },
        )

    # =========================================================
    # CORE (ORCHESTRATOR)
    # =========================================================
    def log(
        self,
        level: str,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = None,
        show_info_logs: Optional[bool] = None,
        show_metadata: Optional[bool] = None,
    ):
        # 1. Resolve config
        config = self._resolve_config(
            save_logs, show_info_logs, show_metadata
        )

        # 2. Build payloads
        msg, mongo_metadata = self._build_payloads(
            level,
            func_name,
            message,
            metadata,
            config["show_metadata"],
        )

        # 3. Get logger
        logger = self._get_logger(
            config["save_logs"],
            config["show_info_logs"],
        )

        # 4. Emit log
        self._emit_log(logger, level, msg)

        return mongo_metadata








class ApplicationTracing:
    def __init__(
        self,
        log_id: Optional[str] = None,
        flag: Optional[str] = None,
        file_name: Optional[str] = None,
        show_info_logs: bool = False,
        show_metadata: bool = False,
        save_logs: bool = False,
        format_metadata: bool = False,
    ):
        self.enginer = LoggerEngine(
            log_id=log_id,
            flag=flag,
            file_name=file_name,
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

        if save_logs == None:
            save_logs = self.save_logs

        if show_info_logs == None:
            show_info_logs = self.show_info_logs

        if show_metadata == None:
            show_metadata = self.show_metadata

        self.enginer.log("critical", func_name=func_name, message=message, metadata=metadata,
                save_logs=save_logs, show_info_logs=show_info_logs,
                show_metadata=show_metadata)

tracer = ApplicationTracing(
    log_id="log_1234",
    flag="TracingCore",
    file_name="tracing_core.py",
    show_info_logs=True,
    show_metadata=True,
    save_logs=True,
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
    #save_logs=False
    #show_metadata=False  # override LOCAL
)

tracer.ERROR(
    func_name="create_user",
    message="User created",
    metadata={"user": "Enzo"},
)

# aqui ainda respeita o global (show_metadata=True)

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