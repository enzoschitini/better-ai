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
        self.flag = flag
        self.file_name = file_name
        self.save_logs = save_logs
        self.show_informations_messages = show_informations_messages
        self.show_payloads = show_payloads
        self.format_payloads = format_payloads

        self.logger = self._setup_logger(self.flag)

    def _setup_logger(self, name: str) -> logging.Logger:
        logger = logging.getLogger(name)

        if logger.handlers:
            return logger  # evita duplicação

        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        # arquivo
        file_handler = logging.FileHandler("app.log")
        file_handler.setFormatter(formatter)

        # console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _format_payload(self, payload: Optional[Dict[str, Any]]) -> Optional[str]:
        if not payload or not self.show_payloads:
            return None

        try:
            if self.format_payloads:
                return json.dumps(payload, indent=4, ensure_ascii=False)
            return str(payload)
        except Exception:
            return str(payload)

    def _build_message(
        self,
        func_name: Optional[str],
        message: Optional[str],
        payload: Optional[Dict[str, Any]],
    ) -> str:
        base = f"{func_name}() | {message}" if func_name else message or ""

        payload_str = self._format_payload(payload)

        parts = [base]

        if payload_str:
            if self.format_payloads:
                parts.append(f"\nPayload:\n{payload_str}")
            else:
                parts.append(f"Payload: {payload_str}")

        if self.file_name:
            parts.append(f"file={self.file_name}")

        if self.log_id:
            parts.append(f"log_id={self.log_id}")

        return " | ".join(parts)

    def _should_log(self, save_logs: Optional[bool], show_info: Optional[bool]) -> bool:
        save_logs = self.save_logs if save_logs is None else save_logs
        show_info = (
            self.show_informations_messages
            if show_info is None
            else show_info
        )

        return save_logs or show_info

    def INFO(
        self,
        func_name: Optional[str] = None,
        message: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        save_logs: Optional[bool] = None,
        show_informations_messages: Optional[bool] = None,
        show_payloads: Optional[bool] = None,
    ):
        if show_payloads is not None:
            self.show_payloads = show_payloads

        if not self._should_log(save_logs, show_informations_messages):
            return

        msg = self._build_message(func_name, message, payload)

        self.logger.info(
            msg,
            extra={
                "log_id": self.log_id,
                "file_name": self.file_name
            }
        )



tracer = ApplicationTracing(
    log_id="log_1234", 
    flag="TracingCore", 
    file_name="tracing_core.py",
    show_informations_messages=False,
    save_logs=True,
    show_payloads=True,
    format_payloads=False)

tracer.INFO("create_user", "User created", {"user": "Enzo"})



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