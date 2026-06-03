import json
import re

class CantoParser:
    def txt_to_json(self, filepath: str) -> dict:
        with open(filepath, "r", encoding="utf-8") as f:
            righe = [r.strip() for r in f.readlines()]

        risultato = {
            "original": [],
            "parafrasi": []
        }

        sezione = None
        buffer = []

        for riga in righe:

            if not riga:
                continue

            lower = riga.lower()

            if lower == "testo":
                sezione = "testo"
                continue

            if lower == "parafrasi":
                sezione = "parafrasi"
                continue

            if sezione == "testo":
                # Cerca un numero finale
                match = re.match(r"^(.*?)(?:\s+(\d+))?$", riga)

                frase = match.group(1).strip()
                numero = match.group(2)

                buffer.append(frase)

                # Quando troviamo il numero finale, uniamo i versi
                if numero:
                    risultato["original"].append({
                        "frase": "\n".join(buffer),
                        "numero": int(numero)
                    })
                    buffer = []

            elif sezione == "parafrasi":
                risultato["parafrasi"].append(riga)

        return risultato

if __name__ == "__main__":
    canto = CantoParser()
    data = canto.txt_to_json("CantoPDF/canto.txt")

    print(json.dumps(data, ensure_ascii=False, indent=4))

# python -m CantoPDF.parse_content