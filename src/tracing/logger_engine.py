import os
import logging

from datetime import datetime
from typing import Optional, Dict, Any

from src.utils.unique_id_factory import IDGenerator
from src.tracing.payload_builder import PayloadBuilder


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

        self.show_info_logs = self._get_env_bool("SHOW_INFO_LOGS", show_info_logs)
        self.show_metadata = self._get_env_bool("SHOW_METADATA", show_metadata)
        self.save_logs = self._get_env_bool("SAVE_LOGS", save_logs)
        self.format_metadata = self._get_env_bool("FORMAT_METADATA", format_metadata)

    # =========================================================
    # GET BOOL ENV
    # =========================================================
    def _get_env_bool(self, env_name: str, default: bool = None) -> bool:
        if os.getenv(env_name):
            BOOL_MAP = {
                "true": True,
                "false": False
            }

            env = os.getenv(env_name)
            return BOOL_MAP[env.lower()]
        else:
            return default

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

