
import json

from CantoPDF.parse_content import CantoParser
from CantoPDF.generate_pdf import CantoPDF

if __name__ == "__main__":
    canto = CantoPDF(
        titolo="L'incontro con Paolo e Francesca",
        sottotitolo="Inferno · Canto V",
        autore="di Dante Alighieri",
        pie_pagina="Dante Alighieri  ·  Divina Commedia  ·  Inferno, Canto V",
        intro_testo="Il secondo cerchio dell'Inferno, dove Dante incontra le anime dei lussuriosi.",
        intro_parafrasi="Una resa in italiano moderno del canto, per facilitarne la lettura.",
    )

    data = CantoParser().txt_to_json("CantoPDF/canto.txt")

    canto.set_epigrafe(
        "«Amor, ch'a nullo amato amar perdona,<br/>"
        "mi prese del costui piacer sì forte,<br/>"
        "che, come vedi, ancor non m'abbandona.»"
    )

    for item in data["original"]:
        canto.aggiungi_terzina(
            item["frase"].split("\n"),
            numero=item["numero"]
        )

    for parafrasi in data["parafrasi"]:
        canto.aggiungi_parafrasi(parafrasi)

    percorso = canto.salva("CantoPDF/Canto_V_Paolo_e_Francesca.pdf")
    print(f"PDF creato: {percorso}")

# python -m CantoPDF.Use