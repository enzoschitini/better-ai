import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from src.utils.unique_id_factory import IDGenerator


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
        logger_name = f"{self.flag}_{id(self)}_{datetime.now().timestamp()}"
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
    # METADATA FORMAT
    # =========================================================
    def _format_metadata(
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
    def _build_message(
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
        metadata_str = self._format_metadata(metadata, show_metadata)
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
    def _build_mongo_metadata(
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
        # BUILD MESSAGE
        # =========================
        msg = self._build_message(
            func_name, message, metadata, effective_show_metadata
        )

        mongo_metadata = self._build_mongo_metadata(
            level, func_name, message, metadata
        )

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

    # =========================================================
    # PUBLIC METHODS
    # =========================================================
    def INFO(self, **kwargs):
        self._log("info", **kwargs)

    def DEBUG(self, **kwargs):
        self._log("debug", **kwargs)

    def WARNING(self, **kwargs):
        self._log("warning", **kwargs)

    def ERROR(self, **kwargs):
        self._log("error", **kwargs)

    def CRITICAL(self, **kwargs):
        self._log("critical", **kwargs)

tracer = ApplicationTracing(
    log_id="log_1234",
    flag="TracingCore",
    file_name="tracing_core.py",
    show_info_logs=False,
    show_metadata=True,
    save_logs=False,
)

tracer.INFO(
    func_name="create_user",
    message="App Init",
    show_info_logs=True
)

tracer.DEBUG(
    func_name="create_user",
    message="User created",
    metadata={"user": "Enzo"},
    save_logs=True,
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