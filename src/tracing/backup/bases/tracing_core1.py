import json
from src.utils.unique_id_factory import IDGenerator
import time
import logging
import json
from typing import Dict, Any

class ApplicationTracing:
    def __init__(self, 
                 log_id: str = None, 
                 flag: str = None, 
                 file_name: str = None,
                 save_logs: bool = False,
                 show_informations_messages: bool = False,
                 show_payloads: bool = False,
                 format_payloads: bool = False):

        self.log_id = log_id
        self.flag = flag
        self.file_name = file_name
        self.save_logs = save_logs
        self.show_informations_messages = show_informations_messages
        self.show_payloads = show_payloads
        self.format_payloads = format_payloads

        self.logger = self._setup_logger("TracingCore")

    def _setup_logger(self, name: str) -> logging.Logger:
        logger = logging.getLogger(name)

        if logger.handlers:
            return logger  # evita duplicação de handlers

        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        # Handler arquivo
        file_handler = logging.FileHandler("app.log")
        file_handler.setFormatter(formatter)

        # Handler console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def INFO(self, 
             func_name: str = None, 
             message: str = None,
             payload: dict = None,
             save_logs: bool = None,
             show_informations_messages: bool = None,
             show_payloads: bool = None):

        # fallback
        save_logs = self.save_logs if save_logs is None else save_logs
        show_informations_messages = (
            self.show_informations_messages 
            if show_informations_messages is None 
            else show_informations_messages
        )
        show_payloads = (
            self.show_payloads 
            if show_payloads is None 
            else show_payloads
        )

        print("\n")
        self.logger.info("Start processing user", extra={"user": "user"})

        if self.format_payloads:
            print(
                f"\n2026-02-21 18:05:24,196 | INFO | {func_name}() | {message} \nPayload {json.dumps(payload, indent=4)}\n{self.file_name} | {self.log_id}\n"
            )
        else:
            print(
                f"2026-02-21 18:05:24,196 | INFO | {func_name}() | {message} | Payload {payload} | {self.file_name} | {self.log_id}"
            )


tracer = ApplicationTracing(
    log_id="log_1234", flag="Logging Test", file_name="tracing_core.py",
    format_payloads=True)

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