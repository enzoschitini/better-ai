"""
Generatore di PDF eleganti per canti / poesie / testi letterari.

USO BASE:
    from canto_pdf import CantoPDF

    canto = CantoPDF(
        titolo="L'incontro con Paolo e Francesca",
        sottotitolo="Inferno · Canto V",
        autore="di Dante Alighieri",
        pie_pagina="Dante Alighieri · Divina Commedia · Inferno, Canto V",
    )
    canto.set_epigrafe(
        "«Amor, ch'a nullo amato amar perdona,<br/>"
        "mi prese del costui piacer sì forte,<br/>"
        "che, come vedi, ancor non m'abbandona.»"
    )
    canto.aggiungi_terzina(
        ["Così discesi del cerchio primaio",
         "giù nel secondo, che men loco cinghia,",
         "e tanto più dolor, che punge a guaio."],
        numero=3,
    )
    # ... altre terzine ...
    canto.aggiungi_parafrasi("Così discesi dal I Cerchio al II...")
    # ... altri paragrafi di parafrasi ...
    canto.salva("Canto_V_Paolo_e_Francesca.pdf")
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether,
    Table, TableStyle
)


class CantoPDF:
    """Genera un PDF elegante per un canto o una poesia."""

    # Palette di colori (modificabile da sottoclassi o tramite set_colori)
    DARK_RED   = colors.HexColor("#1A1A1A") # "#5C1A1B"
    GOLD       = colors.HexColor("#8B6914")
    INK        = colors.HexColor("#1A1A1A")
    SOFT_GREY  = colors.HexColor("#555555")
    PAPER_RULE = colors.HexColor("#A89070")

    def __init__(
        self,
        titolo: str,
        sottotitolo: str = "",
        autore: str = "",
        pie_pagina: str = "",
        intro_testo: str = "",
        intro_parafrasi: str = "",
        titolo_sezione_testo: str = "Il Testo",
        titolo_sezione_parafrasi: str = "Parafrasi",
    ):
        # Metadati
        self.titolo = titolo
        self.sottotitolo = sottotitolo
        self.autore = autore
        self.pie_pagina = pie_pagina or titolo
        self.intro_testo = intro_testo
        self.intro_parafrasi = intro_parafrasi
        self.titolo_sezione_testo = titolo_sezione_testo
        self.titolo_sezione_parafrasi = titolo_sezione_parafrasi

        # Contenuti
        self.epigrafe: str | None = None
        self.terzine: list[tuple[list[str], int | None]] = []
        self.parafrasi: list[str] = []

        # Stili (creati in fondo all'__init__)
        self._build_styles()

    # ---------------- API pubblica ----------------

    def set_epigrafe(self, testo: str) -> "CantoPDF":
        """Imposta l'epigrafe sul frontespizio. Usa <br/> per andare a capo."""
        self.epigrafe = testo
        return self

    def aggiungi_terzina(self, versi: list[str], numero: int | None = None) -> "CantoPDF":
        """Aggiunge una terzina (o strofa di qualunque lunghezza).

        Args:
            versi: lista di stringhe, una per verso.
            numero: numero del verso finale (mostrato a destra). None per nasconderlo.
        """
        self.terzine.append((versi, numero))
        return self

    def aggiungi_terzine(self, terzine: list[tuple[list[str], int | None]]) -> "CantoPDF":
        """Aggiunge una lista di terzine in un colpo solo."""
        self.terzine.extend(terzine)
        return self

    def aggiungi_parafrasi(self, paragrafo: str) -> "CantoPDF":
        """Aggiunge un paragrafo alla parafrasi."""
        self.parafrasi.append(paragrafo)
        return self

    def aggiungi_parafrasi_multipla(self, paragrafi: list[str]) -> "CantoPDF":
        """Aggiunge più paragrafi di parafrasi."""
        self.parafrasi.extend(paragrafi)
        return self

    def set_colori(
        self,
        primario: str | None = None,
        secondario: str | None = None,
        testo: str | None = None,
    ) -> "CantoPDF":
        """Personalizza i colori principali (titoli, dettagli, corpo).

        Args:
            primario: colore di titoli ed elementi salienti (default: rosso scuro).
            secondario: colore di sottotitoli e dettagli (default: oro).
            testo: colore del corpo del testo (default: quasi nero).
        """
        if primario:
            self.DARK_RED = colors.HexColor(primario)
        if secondario:
            self.GOLD = colors.HexColor(secondario)
        if testo:
            self.INK = colors.HexColor(testo)
        self._build_styles()
        return self

    def salva(self, percorso: str) -> str:
        """Genera il PDF e lo salva al percorso indicato. Ritorna il percorso."""
        doc = SimpleDocTemplate(
            percorso, pagesize=A4,
            leftMargin=2.5 * cm, rightMargin=2.5 * cm,
            topMargin=2.6 * cm, bottomMargin=2.4 * cm,
            title=self.titolo, author=self.autore,
        )
        story = self._build_story()
        doc.build(
            story,
            onFirstPage=self._page_decoration,
            onLaterPages=self._page_decoration,
        )
        return percorso

    # ---------------- Costruzione interna ----------------

    def _build_styles(self) -> None:
        """Inizializza tutti gli stili di paragrafo usati dal documento."""
        base = getSampleStyleSheet()

        # Fonti: Times-Bold

        self.style_title = ParagraphStyle(
            "Title", parent=base["Title"],
            fontName="Times-Roman", fontSize=26, leading=32,
            alignment=TA_CENTER, textColor=self.DARK_RED, spaceAfter=6,
        )
        self.style_subtitle = ParagraphStyle(
            "Subtitle", parent=base["Normal"],
            fontName="Times-Italic", fontSize=15, leading=20,
            alignment=TA_CENTER, textColor=self.GOLD, spaceAfter=4,
        )
        self.style_author = ParagraphStyle(
            "Author", parent=base["Normal"],
            fontName="Times-Roman", fontSize=12, leading=16,
            alignment=TA_CENTER, textColor=self.SOFT_GREY, spaceAfter=24,
        )
        self.style_section = ParagraphStyle(
            "Section", parent=base["Heading1"],
            fontName="Times-Roman", fontSize=18, leading=22,
            alignment=TA_CENTER, textColor=self.DARK_RED,
            spaceBefore=12, spaceAfter=18,
        )
        self.style_verse = ParagraphStyle(
            "Verse", parent=base["Normal"],
            fontName="Times-Roman", fontSize=11.5, leading=17,
            alignment=TA_LEFT, textColor=self.INK,
        )
        self.style_verse_num = ParagraphStyle(
            "VerseNum", parent=base["Normal"],
            fontName="Times-Italic", fontSize=10, leading=17,
            alignment=TA_LEFT, textColor=self.GOLD,
        )
        self.style_paraphrase = ParagraphStyle(
            "Paraphrase", parent=base["Normal"],
            fontName="Times-Roman", fontSize=11, leading=16,
            alignment=TA_JUSTIFY, textColor=self.INK,
            spaceAfter=10, firstLineIndent=14,
        )
        self.style_intro = ParagraphStyle(
            "Intro", parent=base["Normal"],
            fontName="Times-Italic", fontSize=11, leading=16,
            alignment=TA_CENTER, textColor=self.SOFT_GREY, spaceAfter=18,
        )
        self.style_ornament = ParagraphStyle(
            "Orn", parent=base["Normal"],
            fontName="Times-Roman", fontSize=18,
            alignment=TA_CENTER, textColor=self.GOLD, spaceAfter=24,
        )
        self.style_epigrafe = ParagraphStyle(
            "Quote", parent=base["Normal"],
            fontName="Times-Italic", fontSize=12, leading=18,
            alignment=TA_CENTER, textColor=self.DARK_RED,
        )

    def _build_story(self) -> list:
        """Costruisce la lista dei flowable (gli elementi del PDF)."""
        story = []

        # --- Frontespizio ---
        story.append(Spacer(1, 3 * cm))
        story.append(Paragraph(self.titolo, self.style_title))
        if self.sottotitolo:
            story.append(Paragraph(self.sottotitolo, self.style_subtitle))
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("❦", self.style_ornament))
        if self.autore:
            story.append(Paragraph(self.autore, self.style_author))
        if self.epigrafe:
            story.append(Spacer(1, 1 * cm))
            story.append(Paragraph(self.epigrafe, self.style_epigrafe))
        story.append(PageBreak())

        # --- Sezione: testo ---
        if self.terzine:
            story.append(Paragraph(self.titolo_sezione_testo, self.style_section))
            if self.intro_testo:
                story.append(Paragraph(self.intro_testo, self.style_intro))

            for versi, numero in self.terzine:
                versi_html = "<br/>".join(versi)
                p_versi = Paragraph(versi_html, self.style_verse)
                num_text = f"<i>{numero}</i>" if numero is not None else ""
                p_num = Paragraph(num_text, self.style_verse_num)

                tbl = Table(
                    [[p_versi, p_num]],
                    colWidths=[13.0 * cm, 1.5 * cm],
                )
                tbl.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]))
                # KeepTogether: la terzina non viene spezzata fra due pagine.
                story.append(KeepTogether([tbl, Spacer(1, 10)]))

        # --- Sezione: parafrasi ---
        if self.parafrasi:
            story.append(PageBreak())
            story.append(Paragraph(self.titolo_sezione_parafrasi, self.style_section))
            if self.intro_parafrasi:
                story.append(Paragraph(self.intro_parafrasi, self.style_intro))
            for par in self.parafrasi:
                story.append(Paragraph(par, self.style_paraphrase))

        # --- Chiusura ---
        story.append(Spacer(1, 0.6 * cm))
        story.append(Paragraph("❦", self.style_ornament))

        return story

    def _page_decoration(self, canv, doc) -> None:
        """Disegna le linee decorative e il piè di pagina su ogni pagina."""
        canv.saveState()
        width, height = A4
        canv.setStrokeColor(self.PAPER_RULE)
        canv.setLineWidth(0.6)
        canv.line(2.2 * cm, height - 1.7 * cm, width - 2.2 * cm, height - 1.7 * cm)
        canv.line(2.2 * cm, 1.8 * cm, width - 2.2 * cm, 1.8 * cm)
        canv.setFont("Times-Italic", 9)
        canv.setFillColor(self.SOFT_GREY)
        canv.drawCentredString(width / 2.0, 1.3 * cm, self.pie_pagina)
        canv.setFont("Times-Roman", 9)
        canv.drawRightString(width - 2.2 * cm, 1.3 * cm, f"— {doc.page} —")
        canv.restoreState()


# =====================================================================
# ESEMPIO D'USO — viene eseguito solo lanciando direttamente questo file.
# Copia/adatta questa parte per i tuoi canti, oppure importa la classe
# in un altro script: `from canto_pdf import CantoPDF`
# =====================================================================
if __name__ == "__main__":
    canto = CantoPDF(
        titolo="L'incontro con Paolo e Francesca",
        sottotitolo="Inferno · Canto V",
        autore="di Dante Alighieri",
        pie_pagina="Dante Alighieri  ·  Divina Commedia  ·  Inferno, Canto V",
        intro_testo="Il secondo cerchio dell'Inferno, dove Dante incontra le anime dei lussuriosi.",
        intro_parafrasi="Una resa in italiano moderno del canto, per facilitarne la lettura.",
    )

    canto.set_epigrafe(
        "«Amor, ch'a nullo amato amar perdona,<br/>"
        "mi prese del costui piacer sì forte,<br/>"
        "che, come vedi, ancor non m'abbandona.»"
    )

    # Puoi aggiungere le terzine una a una...
    canto.aggiungi_terzina(
        ["Così discesi del cerchio primaio",
         "giù nel secondo, che men loco cinghia,",
         "e tanto più dolor, che punge a guaio."],
        numero=3,
    )
    canto.aggiungi_terzina(
        ["Stavvi Minòs orribilmente, e ringhia:",
         "essamina le colpe ne l'intrata;",
         "giudica e manda secondo ch'avvinghia."],
        numero=6,
    )
    # ... oppure in blocco con aggiungi_terzine([...])

    canto.aggiungi_parafrasi(
        "Così discesi dal I Cerchio al II, che cinge uno spazio minore, "
        "ma contiene tanto maggior dolore che spinge a lamentarsi."
    )
    canto.aggiungi_parafrasi(
        "Minosse sta orribilmente sulla soglia e ringhia: esamina le colpe "
        "dei dannati che si presentano; li giudica e li destina a seconda di "
        "come attorcigli la coda."
    )

    percorso = canto.salva("Canto_V_Paolo_e_Francesca.pdf")
    print(f"PDF creato: {percorso}")