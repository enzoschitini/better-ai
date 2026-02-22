import json
import logging
from typing import Optional, Dict, Any


class ApplicationTracing:
    def __init__(
        self,
        log_id: Optional[str] = None,
        flag: Optional[str] = None,
        file_name: Optional[str] = None,
        save_logs: bool = False,
        show_informations_messages: bool = False,
        show_payloads: bool = False,
        format_payloads: bool = False,
    ):
        self.log_id = log_id
        self.flag = flag or "ApplicationTracing"
        self.file_name = file_name

        self.save_logs = save_logs
        self.show_informations_messages = show_informations_messages

        self.show_payloads = show_payloads
        self.format_payloads = format_payloads

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
            "%(asctime)s | %(levelname)s | %(name)s | %(filename)s | %(message)s"
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

        if self.show_informations_messages:
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
    # PAYLOAD
    # =========================================================
    def _format_payload(self, payload: Optional[Dict[str, Any]]) -> Optional[str]:
        if not payload or not self.show_payloads:
            return None

        try:
            if self.format_payloads:
                return f"\n{json.dumps(payload, indent=4, ensure_ascii=False)}\n"
            return str(payload)
        except Exception:
            return str(payload)

    # =========================================================
    # MESSAGE BUILDER
    # =========================================================
    def _build_message(
        self,
        func_name: Optional[str],
        message: Optional[str],
        payload: Optional[Dict[str, Any]],
    ) -> str:
        parts = []

        # base message
        if func_name:
            parts.append(f"{func_name}()")

        if message:
            parts.append(message)

        # payload
        payload_str = self._format_payload(payload)
        if payload_str:
            if self.format_payloads:
                parts.append(f"\nPayload:\n{payload_str}")
            else:
                parts.append(f"Payload={payload_str}")

        # metadata
        if self.file_name:
            parts.append(f"file={self.file_name}")

        if self.log_id:
            parts.append(f"log_id={self.log_id}")

        return " | ".join(parts)

    # =========================================================
    # MONGO PAYLOAD BUILDER
    # =========================================================
    def _build_mongo_payload(
        self,
        level: Optional[str],
        func_name: Optional[str],
        message: Optional[str],
        payload: Optional[Dict[str, Any]],
    ) -> str:
        
        mongo_payload = {
            "log_id": self.log_id,
            "level": level,
            "flag": self.flag,
            "func_name": func_name,
            "message": message,
            "payload": payload,
            "time": "xxxxxxxxxxx"
        }

        print(f"\n\n_build_mongo_payload:\n {json.dumps(mongo_payload, indent= 4)}\n\n")

        return mongo_payload

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
            self.show_informations_messages
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
        payload: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = None,
        show_informations_messages: Optional[bool] = None,
        show_payloads: Optional[bool] = None,
    ):
        # Atualiza flags se vierem no método
        if show_payloads is not None:
            self.show_payloads = show_payloads

        if save_logs is not None:
            self.save_logs = save_logs

        if show_informations_messages is not None:
            self.show_informations_messages = show_informations_messages

        # Atualiza logger caso flags mudem
        self._refresh_logger()

        msg = self._build_message(func_name, message, payload)
        mongo_payload = self._build_mongo_payload(level, func_name, message, payload)

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
        payload: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = None,
        show_informations_messages: Optional[bool] = None,
        show_payloads: Optional[bool] = None,
    ):
        self._log(
            "info",
            func_name=func_name,
            message=message,
            payload=payload,
            save_logs=save_logs,
            show_informations_messages=show_informations_messages,
            show_payloads=show_payloads,
        )

    def DEBUG(
        self,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = None,
        show_informations_messages: Optional[bool] = None,
        show_payloads: Optional[bool] = None,
    ):
        self._log("debug", func_name=func_name, message=message, payload=payload,
                save_logs=save_logs, show_informations_messages=show_informations_messages,
                show_payloads=show_payloads)


    def WARNING(
        self,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = None,
        show_informations_messages: Optional[bool] = None,
        show_payloads: Optional[bool] = None,
    ):
        self._log("warning", func_name=func_name, message=message, payload=payload,
                save_logs=save_logs, show_informations_messages=show_informations_messages,
                show_payloads=show_payloads)


    def ERROR(
        self,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = None,
        show_informations_messages: Optional[bool] = None,
        show_payloads: Optional[bool] = None,
    ):
        self._log("error", func_name=func_name, message=message, payload=payload,
                save_logs=save_logs, show_informations_messages=show_informations_messages,
                show_payloads=show_payloads)


    def CRITICAL(
        self,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = None,
        show_informations_messages: Optional[bool] = None,
        show_payloads: Optional[bool] = None,
    ):
        self._log("critical", func_name=func_name, message=message, payload=payload,
                save_logs=save_logs, show_informations_messages=show_informations_messages,
                show_payloads=show_payloads)

tracer = ApplicationTracing(
    log_id="log_1234", 
    flag="TracingCore", 
    file_name="tracing_core.py",
    show_informations_messages=True,
    save_logs=True,
    show_payloads=True,
    format_payloads=True)

tracer.INFO(
    func_name="create_user",
    message="App Init"
)

tracer.DEBUG(
    func_name="create_user",
    message="User created",
    payload={"user": "Enzo"}
)

tracer.ERROR(
    func_name="create_user",
    message="User created",
    payload={"user": "Enzo"}
)
 



#print(IDGenerator.timestamp(prefix="log_"))

"""
1. Short payload -> Bool
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