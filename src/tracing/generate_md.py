import json
from typing import List, Dict, Any, Optional
from collections import defaultdict


class MarkdownLogFormatter:
    LEVEL_EMOJI = {
        "INFO": "",
        "DEBUG": "",
        "WARNING": "",
        "ERROR": "",
        "CRITICAL": ""
    }

    def __init__(
        self,
        logs: List[Dict[str, Any]],
        use_emoji: bool = True,
        sort_by_time: bool = True,
        group_by_log_id: bool = True
    ):
        self.logs = logs
        self.use_emoji = use_emoji
        self.sort_by_time = sort_by_time
        self.group_by_log_id = group_by_log_id

    # =========================
    # PUBLIC API
    # =========================
    def format(self, mode: str = "standard") -> str:
        if mode == "table":
            return self._format_table()
        elif mode == "standard":
            return self._format_standard()
        else:
            raise ValueError("mode deve ser 'standard' ou 'table'")

    # =========================
    # STANDARD FORMAT
    # =========================
    def _format_standard(self) -> str:
        grouped = self._group_logs()

        md = ["# Logs da Aplicação\n"]

        for log_id, entries in grouped.items():
            md.append(f"## Log ID: {log_id}\n")

            for log in entries:
                level = log.get("level")
                emoji = self.LEVEL_EMOJI.get(level, "") if self.use_emoji else ""

                md.append(f"### {emoji} {level}".strip())
                md.append(f"- **Time:** {log.get('time')}")
                md.append(f"- **Function:** {log.get('func_name')}")
                md.append(f"- **Message:** {log.get('message')}")

                metadata = log.get("metadata")
                if metadata:
                    md.append(f"- **Metadata:** `{json.dumps(metadata, ensure_ascii=False)}`")

                md.append("")

        return "\n".join(md)

    # =========================
    # TABLE FORMAT
    # =========================
    def _format_table(self) -> str:
        header = "| Level | Time | Function | Message | Metadata |\n"
        separator = "|------|------|----------|---------|----------|\n"

        rows = []

        logs = self._sort_logs(self.logs)

        for log in logs:
            level = log.get("level")
            emoji = self.LEVEL_EMOJI.get(level, "") if self.use_emoji else ""

            level_display = f"{emoji} {level}".strip()

            metadata = log.get("metadata")
            metadata_str = "-" if not metadata else json.dumps(metadata, ensure_ascii=False)

            rows.append(
                f"| {level_display} | {log.get('time')} | {log.get('func_name')} | {log.get('message')} | {metadata_str} |"
            )

        return "# Logs\n\n" + header + separator + "\n".join(rows)

    # =========================
    # HELPERS
    # =========================
    def _group_logs(self):
        if not self.group_by_log_id:
            return {"all_logs": self._sort_logs(self.logs)}

        grouped = defaultdict(list)

        for log in self.logs:
            grouped[log.get("log_id")].append(log)

        return {
            log_id: self._sort_logs(entries)
            for log_id, entries in grouped.items()
        }

    def _sort_logs(self, logs):
        if not self.sort_by_time:
            return logs

        return sorted(logs, key=lambda x: x.get("time", ""))


import json
from pathlib import Path

# caminho do arquivo
file_path = Path("data/application_tracings/TracingCore.json")

# ler JSON
with open(file_path, "r", encoding="utf-8") as f:
    logs = json.load(f)

# instanciar formatter
formatter = MarkdownLogFormatter(logs)

# gerar markdown
md_standard = formatter.format(mode="standard")
md_table = formatter.format(mode="table")

# salvar arquivos
output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)

with open(output_dir / "logs_standard.md", "w", encoding="utf-8") as f:
    f.write(md_standard)

with open(output_dir / "logs_table.md", "w", encoding="utf-8") as f:
    f.write(md_table)

print("✅ Markdown gerado com sucesso!")