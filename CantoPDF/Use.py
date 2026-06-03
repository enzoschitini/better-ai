
import json

from CantoPDF.parse_content import CantoParser
from CantoPDF.generate_pdf import CantoPDF

if __name__ == "__main__":
    canto = CantoPDF(
        titolo="La selva oscura e l'incontro con Virgilio",
        sottotitolo="Inferno · Canto I",
        autore="di Dante Alighieri",
        pie_pagina="Dante Alighieri  ·  Divina Commedia  ·  Inferno, Canto I",
        intro_testo=(
            "L'inizio del viaggio di Dante: la selva oscura, "
            "le tre fiere e l'apparizione di Virgilio."
        ),
        intro_parafrasi=(
            "Una traduzione in italiano moderno del primo canto, "
            "per comprenderne più facilmente il significato."
        ),
    )

    data = CantoParser().txt_to_json("CantoPDF/canto.txt")

    canto.set_epigrafe(
        "«Nel mezzo del cammin di nostra vita<br/>"
        "mi ritrovai per una selva oscura,<br/>"
        "ché la diritta via era smarrita.»"
    )

    for item in data["original"]:
        canto.aggiungi_terzina(
            item["frase"].split("\n"),
            numero=item["numero"]
        )

    for parafrasi in data["parafrasi"]:
        canto.aggiungi_parafrasi(parafrasi)

    percorso = canto.salva("CantoPDF/Canto_I_La_Selva_Oscura.pdf")
    print(f"PDF creato: {percorso}")

# python -m CantoPDF.Use