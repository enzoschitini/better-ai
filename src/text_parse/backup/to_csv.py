import json
import csv
from typing import Any, Dict, List, Iterable

class JsonFlattener:
    """
    Responsabile della trasformazione di JSON annidati in dizionari flat
    """

    def __init__(self, separator: str = "_"):
        self.separator = separator

    def flatten(
        self,
        data: Any,
        parent_key: str = ""
    ) -> Dict[str, Any]:
        items: Dict[str, Any] = {}

        if isinstance(data, dict):
            items.update(self._flatten_dict(data, parent_key))

        elif isinstance(data, list):
            items.update(self._flatten_list(data, parent_key))

        else:
            items[parent_key] = data

        return items

    def _flatten_dict(
        self,
        data: Dict[str, Any],
        parent_key: str
    ) -> Dict[str, Any]:
        items = {}

        for key, value in data.items():
            new_key = (
                f"{parent_key}{self.separator}{key}"
                if parent_key else key
            )
            items.update(self.flatten(value, new_key))

        return items

    def _flatten_list(
        self,
        data: List[Any],
        parent_key: str
    ) -> Dict[str, Any]:
        items = {}

        for index, value in enumerate(data):
            new_key = f"{parent_key}{self.separator}{index}"
            items.update(self.flatten(value, new_key))

        return items


class JsonToCSVConverter:
    """
    Pipeline completa:
    JSON → flatten → CSV
    """

    def __init__(
        self,
        separator: str = "_",
        encoding: str = "utf-8"
    ):
        self.flattener = JsonFlattener(separator)
        self.encoding = encoding

    def load_json(self, path: str) -> List[Dict[str, Any]]:
        with open(path, "r", encoding=self.encoding) as file:
            return json.load(file)

    def transform(
        self,
        json_data: Iterable[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return [
            self.flattener.flatten(entry)
            for entry in json_data
        ]

    def save_csv(
        self,
        rows: List[Dict[str, Any]],
        output_path: str
    ) -> None:
        fieldnames = sorted(
            {key for row in rows for key in row.keys()}
        )

        with open(output_path, "w", newline="", encoding=self.encoding) as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def run(
        self,
        input_json_path: str,
        output_csv_path: str
    ) -> None:
        data = self.load_json(input_json_path)
        flat_rows = self.transform(data)
        self.save_csv(flat_rows, output_csv_path)


if __name__ == "__main__":
    converter = JsonToCSVConverter(separator="_")
    converter.run(
        "src/text_parse/output_lezioni.json",
        "output.csv"
    )



