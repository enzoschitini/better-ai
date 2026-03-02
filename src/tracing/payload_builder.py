import json
from datetime import datetime
from typing import Optional, Dict, Any


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
