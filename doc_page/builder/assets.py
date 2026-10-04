"""CSS e JS concatenados e hasheados; mídia referenciada copiada.

A cadeia de `@import` do design-system.css é 7 requisições em série, todas
bloqueando render, com as fontes escondidas dentro de um stylesheet. Aqui a
ordem é LIDA das próprias linhas `@import` — nunca duplicada em Python, logo
não pode divergir do arquivo que o README define como autoritativo. E o
`catalog.css` sai de graça, porque não é importado.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import struct
from pathlib import Path

from .settings import Settings

_IMPORT = re.compile(r'@import\s+url\(["\']([^"\')]+)["\']\)\s*;')


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:8]


def css_order(entry: Path) -> list[Path]:
    """Os parciais locais, na ordem em que o entry os importa."""
    out = []
    for m in _IMPORT.finditer(entry.read_text(encoding="utf-8")):
        href = m.group(1)
        if href.startswith("http"):
            continue  # as fontes vão para o <head>, não para o bundle
        p = entry.parent / href
        if p.is_file():
            out.append(p)
    return out


def build_css(st: Settings, dist: Path) -> str:
    entry = st.theme / "css" / "design-system.css"
    parts = css_order(entry)
    if not parts:
        raise RuntimeError(f"{entry}: nenhum @import local encontrado")
    header = ("/* Gerado por doc_page.builder — não edite.\n"
              "   Ordem lida de theme/css/design-system.css:\n"
              + "".join(f"     {p.name}\n" for p in parts) + " */\n")
    body = header + "\n".join(p.read_text(encoding="utf-8") for p in parts)
    data = body.encode("utf-8")
    name = f"ds.{_hash(data)}.css"
    out = dist / "assets" / "css" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return f"{st.base}/assets/css/{name}"


def build_js(st: Settings, dist: Path) -> str:
    """ds.js + docs.js. O ds.js é IIFE autocontido, então concatenar é seguro."""
    parts = [st.theme / "js" / "ds.js", st.theme / "js" / "docs.js"]
    body = "\n;\n".join(p.read_text(encoding="utf-8") for p in parts if p.is_file())
    data = body.encode("utf-8")
    name = f"docs.{_hash(data)}.js"
    out = dist / "assets" / "js" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return f"{st.base}/assets/js/{name}"


def png_size(p: Path) -> tuple[int, int] | None:
    """Dimensão de PNG sem dependência: o IHDR está em offset fixo."""
    b = p.read_bytes()[:24]
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", b[16:24])


_REF = re.compile(r'(?:src|href)="([^"]*?/assets/[^"]+)"')


def copy_referenced(st: Settings, dist: Path, html_files: list[Path]) -> tuple[int, list[str]]:
    """Copia de assets/ para dist/assets/ só o que alguma página referencia.

    Evita embarcar o Logo_Text.png de 3,5 MB por nada, e é o que torna
    verificável a regra de higiene de assets do check.
    """
    wanted: set[str] = set()
    for f in html_files:
        for m in _REF.finditer(f.read_text(encoding="utf-8")):
            rel = m.group(1).split("/assets/", 1)[1]
            if rel.startswith(("css/", "js/")):
                continue
            wanted.add(rel)

    copied, missing = 0, []
    for rel in sorted(wanted):
        src = st.assets / rel
        if not src.is_file():
            missing.append(rel)
            continue
        dst = dist / "assets" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    return copied, missing
