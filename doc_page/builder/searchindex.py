"""Índice de busca gerado no build, um por idioma.

Corrige a fraqueza do protótipo, que indexava só títulos e migalhas e nunca o
corpo. O texto do corpo já sai `fold()`ado daqui, então o cliente nunca
normaliza centenas de KB na primeira tecla.

Forma: dois arrays, com seções referenciando páginas por índice inteiro, para
não repetir a migalha 20× por página.

  p: [id, url, título, migalhas, ordem]
  s: [índice da página, âncora, texto do título, texto do corpo folded]
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .model import Page
from .slugs import fold

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_ENT = (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'))

BODY_CAP = 1200
DISPLAY_CAP = 240


def _text(html: str) -> str:
    t = _TAG.sub(" ", html)
    for ent, ch in _ENT:
        t = t.replace(ent, ch)
    return _WS.sub(" ", t).strip()


def _sections(html: str) -> list[tuple[str, str, str]]:
    """[(id, título, texto do corpo até o próximo heading)]"""
    hs = list(re.finditer(r'<(h2|h3)[^>]*\sid="([^"]+)"[^>]*>(.*?)</\1>', html, re.S))
    out = []
    for i, m in enumerate(hs):
        start = m.end()
        end = hs[i + 1].start() if i + 1 < len(hs) else len(html)
        title = _text(m.group(3)).replace("#", "").strip()
        out.append((m.group(2), title, _text(html[start:end])))
    return out


def build(pages: list[Page], lang: str, popular: list[str], rendered: dict) -> dict:
    """`rendered` mapeia page.id -> html do .prose já ancorado."""
    p_rows: list[list] = []
    s_rows: list[list] = []
    idx_of: dict[str, int] = {}

    for page in pages:
        if page.lang != lang:
            continue
        # vazias não têm nada para achar; espelhos já estão indexados em pt
        if page.empty or page.is_mirror:
            continue
        crumbs = " / ".join([page.area.name] + page.crumbs) if page.area else ""
        idx_of[page.id] = len(p_rows)
        # caminho relativo à raiz; o cliente prefixa com DOCS.root
        p_rows.append([page.id, page.path, page.title, crumbs, page.order])

        html = rendered.get(page.id, "")
        for sid, title, body in _sections(html):
            s_rows.append([
                idx_of[page.id], sid, title,
                fold(body)[:BODY_CAP],
                body[:DISPLAY_CAP],
            ])

    return {
        "v": 1,
        "lang": lang,
        "p": p_rows,
        "s": s_rows,
        "popular": [idx_of[i] for i in popular if i in idx_of],
    }


def write(index: dict, dist: Path, lang: str) -> str:
    import hashlib

    data = json.dumps(index, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    h = hashlib.sha256(data).hexdigest()[:8]
    name = f"search-index.{h}.json"
    out = dist / lang / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return f"{lang}/{name}"
