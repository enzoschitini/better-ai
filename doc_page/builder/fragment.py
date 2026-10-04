"""Lê um fragmento `<article data-*>` e separa metadado de corpo.

O contrato, documentado em theme/README.md:
  - a raiz é um único <article>
  - data-title e data-lead são obrigatórios
  - valores de atributo são HTML-escapados, então '<' nunca aparece dentro
    da tag de abertura

Qualquer violação falha o build com o caminho do arquivo. Um atributo
malformado é erro barulhento aqui, que é a razão de ter escolhido atributos
em vez de front-matter em comentário.
"""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from .model import Fragment

REQUIRED = ("data-title", "data-lead")


class FragmentError(ValueError):
    pass


class _Root(HTMLParser):
    """Captura só a primeira tag de abertura e onde ela termina."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.attrs: dict[str, str] | None = None
        self.body_start: int | None = None

    def handle_starttag(self, tag, attrs):
        if self.attrs is not None:
            return
        if tag != "article":
            raise FragmentError(f"a raiz do fragmento tem de ser <article>, veio <{tag}>")
        self.attrs = {k: (v or "") for k, v in attrs}
        self.body_start = self.getpos()[0]


def parse(path: Path) -> Fragment:
    raw = path.read_text(encoding="utf-8")

    open_tag_end = raw.find(">")
    if open_tag_end == -1:
        raise FragmentError(f"{path}: não achei a tag de abertura")
    if "<" in raw[raw.find("<") + 1:open_tag_end]:
        raise FragmentError(
            f"{path}: '<' dentro da tag de abertura — algum valor de atributo "
            f"não está escapado. Use &lt; no lugar."
        )

    p = _Root()
    try:
        p.feed(raw)
    except FragmentError as e:
        raise FragmentError(f"{path}: {e}") from None
    if p.attrs is None:
        raise FragmentError(f"{path}: nenhum <article> encontrado")

    missing = [k for k in REQUIRED if k not in p.attrs]
    if missing:
        raise FragmentError(f"{path}: faltam atributos obrigatórios: {', '.join(missing)}")

    body = raw[open_tag_end + 1:]
    close = body.rfind("</article>")
    if close == -1:
        raise FragmentError(f"{path}: falta </article>")

    return Fragment(meta=p.attrs, body=body[:close].strip())


def scan(content_dir: Path, lang: str) -> dict[str, Fragment]:
    """Varre content/<lang>/ e devolve {slug_path: Fragment}."""
    root = content_dir / lang
    if not root.is_dir():
        return {}
    out: dict[str, Fragment] = {}
    for f in sorted(root.rglob("*.html")):
        key = f.relative_to(root).with_suffix("").as_posix()
        out[key] = parse(f)
    return out
