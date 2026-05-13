import json
from typing import Any, Dict
from pathlib import Path
import copy


class ManagerProcessInformations:
    def __init__(self, file_name: str = "process_output"):
        self._process_payload: Dict[str, Any] = {}
        self._enabled: bool = False
        self.file_name = file_name

    def start(self) -> None:
        self._enabled = True

    def stop(self) -> None:
        self._enabled = False

    def add(self, key: str, value: Any) -> None:
        if not self._enabled:
            return
        self._process_payload[key] = value

    def remove(self, key: str) -> None:
        self._process_payload.pop(key, None)

    def get_payload(self, copy_payload: bool = True) -> Dict[str, Any]:
        return copy.deepcopy(self._process_payload) if copy_payload else self._process_payload

    def clear(self) -> None:
        self._process_payload.clear()

    def save(self, directory: str | None = None) -> Path:
        path = Path(directory or ".") / f"{self.file_name}.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._process_payload, f, indent=4, default=str, ensure_ascii=False)

        return path

if __name__ == "__main__":
    manager = ManagerProcessInformations("process_output")

    manager.start()

    manager.add("job_id", "abc-123")
    manager.add("step", "upload")
    manager.add("file_info", {
        "name": "image.png",
        "bytes": b"..."
    })

    # remover algo sensível antes de salvar
    payload = manager.get_payload()
    payload["file_info"].pop("bytes", None)

    manager.save()
