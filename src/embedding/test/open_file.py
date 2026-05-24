from pathlib import Path
from io import BytesIO

pasta = Path("B2")

for arquivo in pasta.glob("*.pdf"):
    with open(arquivo, "rb") as f:
        file_bytes = BytesIO(f.read())
    print(f"Carregado: {arquivo.name}")