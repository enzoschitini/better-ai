"""Portes diretos de `slug()`, `fold()` e `esc()` do protótipo.

Os três precisam produzir exatamente o mesmo resultado que as versões em
JavaScript, senão as URLs mudam e o índice de busca deixa de casar com o que
o cliente calcula. Qualquer alteração aqui exige reconferir contra
doc/site-prototype/index.html linhas 1175, 1176 e 1826.
"""

import re
import unicodedata

_COMBINING = re.compile(r"[̀-ͯ]")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_EDGE_DASH = re.compile(r"^-+|-+$")

_ESC = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}
_ESC_RE = re.compile(r'[&<>"]')


def fold(s: str) -> str:
    """NFD, remove diacríticos, minúsculas. Preserva o comprimento.

    Essa última propriedade é load-bearing: os offsets de `<mark>` calculados
    no texto folded valem no texto de exibição.
    """
    return _COMBINING.sub("", unicodedata.normalize("NFD", s)).lower()


def slug(s: str) -> str:
    """`Web Service Network - API` → `web-service-network-api`."""
    return _EDGE_DASH.sub("", _NON_ALNUM.sub("-", fold(s)))


def esc(s) -> str:
    """Escapa para texto e para valor de atributo com aspas duplas."""
    return _ESC_RE.sub(lambda m: _ESC[m.group()], str(s))
