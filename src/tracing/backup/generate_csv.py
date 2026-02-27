import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional


class CSVLogExporter:
    def __init__(
        self,
        logs: Optional[List[Dict[str, Any]]] = None,
        file_path: Optional[str] = None,
        flatten_metadata: bool = False,
    ):
        if logs is None and file_path is None:
            raise ValueError("Você deve fornecer 'logs' ou 'file_path'")

        self.flatten_metadata = flatten_metadata

        if file_path:
            self.logs = self._load_logs(file_path)
        else:
            self.logs = logs

    # =========================
    # PUBLIC API
    # =========================
    def to_csv(self, output_path: str):
        rows = self._prepare_rows()

        if not rows:
            raise ValueError("Nenhum log encontrado")

        fieldnames = rows[0].keys()

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    # =========================
    # INTERNALS
    # =========================
    def _load_logs(self, path: str) -> List[Dict[str, Any]]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # suporta {"logs": [...]}
        if isinstance(data, dict):
            return data.get("logs", [])

        return data

    def _prepare_rows(self):
        rows = []

        for log in self.logs:
            metadata = log.get("metadata")

            # =========================
            # METADATA
            # =========================
            if self.flatten_metadata and isinstance(metadata, dict):
                metadata_fields = {
                    f"metadata_{k}": v for k, v in metadata.items()
                }
            else:
                metadata_fields = {
                    "metadata": json.dumps(metadata, ensure_ascii=False) if metadata else None
                }

            # =========================
            # ORDEM DAS COLUNAS
            # =========================
            row = {
                "log_id": log.get("log_id"),
                "level": log.get("level"),
                "flag": log.get("flag"),
                "func_name": log.get("func_name"),
                "message": log.get("message"),
                **metadata_fields,
                "file_name": log.get("file_name"),
                "time": log.get("time"),
                "_id": log.get("_id"),
                "_created_at": log.get("_created_at"),
            }

            rows.append(row)

        return rows

exporter = CSVLogExporter(
    file_path="data/application_tracings/TracingCore.json"
)

exporter.to_csv("outputs/logs.csv")

print("✅ CSV gerado!")