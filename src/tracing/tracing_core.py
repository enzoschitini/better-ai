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















class LogBuilder():
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
        # FIX: gerar log_id por instância
        self.log_id = log_id or IDGenerator.timestamp(prefix="log_")
        self.flag = flag or "ApplicationTracing"
        self.file_name = file_name

        # config global (imutável em runtime)
        self.show_info_logs = show_info_logs
        self.show_metadata = show_metadata
        self.save_logs = save_logs
        self.format_metadata = format_metadata

    # =========================================================
    # LOGGER TEMPORÁRIO (sem estado global)
    # =========================================================
    def _setup_logger(self, save_logs: bool, show_info_logs: bool) -> logging.Logger:
        logger_name = f"{self.flag}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        if logger.handlers:
            logger.handlers.clear()

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        # FILE HANDLER
        if save_logs:
            file_handler = logging.FileHandler("app.log")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # CONSOLE HANDLER
        console_handler = logging.StreamHandler()

        if show_info_logs:
            console_handler.setLevel(logging.DEBUG)
        else:
            console_handler.setLevel(logging.ERROR)

        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    # =========================================================
    # CORE LOG
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
        # =========================
        # RESOLVE CONFIG LOCAL
        # =========================
        effective_save_logs = self.save_logs if save_logs is None else save_logs
        effective_show_info = (
            self.show_info_logs if show_info_logs is None else show_info_logs
        )
        effective_show_metadata = (
            self.show_metadata if show_metadata is None else show_metadata
        )

        # =========================
        # INIT BUILDER
        # =========================
        builder = PayloadBuilder(
            log_id=self.log_id,
            flag=self.flag,
            file_name=self.file_name,
            format_metadata=self.format_metadata,
        )
        
        # =========================
        # BUILD MESSAGE
        # =========================

        msg = builder.build_message(
            func_name, message, metadata, effective_show_metadata
        )

        mongo_metadata = builder.build_mongo_payload(
            level, func_name, message, metadata
        )

        #print(f"\n{json.dumps(mongo_metadata, indent=4)}")

        # =========================
        # LOGGER TEMPORÁRIO
        # =========================
        logger = self._setup_logger(
            save_logs=effective_save_logs,
            show_info_logs=effective_show_info,
        )

        log_method = getattr(logger, level.lower())

        log_method(
            msg,
            extra={
                "log_id": self.log_id,
                "file_name": self.file_name,
            },
        )

        return mongo_metadata  # útil para persistência externa










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
        self.builder = LogBuilder(
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
        self.builder._log(
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
        self.builder._log("debug", func_name=func_name, message=message, metadata=metadata,
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
        self.builder._log("warning", func_name=func_name, message=message, metadata=metadata,
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
        self.builder._log("error", func_name=func_name, message=message, metadata=metadata,
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

        self.builder._log("critical", func_name=func_name, message=message, metadata=metadata,
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