import json
import csv
from typing import Any, Dict, List


def flatten_json(
    data: Any,
    parent_key: str = "",
    sep: str = "_"
) -> Dict[str, Any]:
    """
    Trasforma JSON annidati (dict + list) in un dizionario flat
    """
    items = {}

    if isinstance(data, dict):
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            items.update(flatten_json(value, new_key, sep))

    elif isinstance(data, list):
        for i, value in enumerate(data):
            new_key = f"{parent_key}{sep}{i}"
            items.update(flatten_json(value, new_key, sep))

    else:
        items[parent_key] = data

    return items


def json_to_csv(
    json_data: List[Dict[str, Any]],
    output_csv: str
):
    """
    Converte una lista di JSON in CSV
    """
    flat_rows = []

    for entry in json_data:
        flat_rows.append(flatten_json(entry))

    # tutte le colonne possibili
    fieldnames = sorted(
        {key for row in flat_rows for key in row.keys()}
    )

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_rows)


if __name__ == "__main__":
    with open("src/text_classifier/output_n8n.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    json_to_csv(data, "output.csv")
