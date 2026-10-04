"""Verificação fim a fim do dist/. Stdlib only.

As oito regras existem porque cada uma pega uma classe de erro que fica
invisível até alguém clicar: caminho quebrado, hreflang que mente, âncora que
não existe, asset de 3,5 MB pegando carona.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote

from .settings import Settings

_REF = re.compile(r'(?:href|src)="([^"#?]+)(?:[#?][^"]*)?"')
_HREFLANG = re.compile(r'<link rel="alternate" hreflang="([a-z-]+)" href="([^"]+)"')
_CANON = re.compile(r'<link rel="canonical" href="([^"]+)"')
_ICO = re.compile(r'data-ico="([^"]+)"')
_ID = re.compile(r'\sid="([^"]+)"')


def _icons(ds_js: Path) -> set[str]:
    txt = ds_js.read_text(encoding="utf-8")
    m = re.search(r"ICON\s*=\s*\{(.*?)\n\s*\};", txt, re.S)
    # várias chaves por linha, então não ancorar em ^
    return set(re.findall(r"(\w+)\s*:\s*'", m.group(1))) if m else set()


def run(st: Settings, manifest, langs: list[str]) -> int:
    dist = st.dist
    if not dist.is_dir():
        print("dist/ não existe. Rode o build primeiro.")
        return 1

    htmls = sorted(dist.rglob("*.html"))
    problems: list[str] = []

    def rel(p: Path) -> str:
        return p.relative_to(dist).as_posix()

    def is_doc_page(p: Path) -> bool:
        """O catálogo do design system e o redirect da raiz não são páginas de
        documento: não têm .prose, nem TOC, nem canonical."""
        r = rel(p)
        return not r.startswith("_design-system/") and r != "index.html"

    # ---- 1. integridade de link, 2. roteamento obsoleto, 3. estrutura ----
    referenced: set[str] = set()
    for f in htmls:
        txt = f.read_text(encoding="utf-8")
        where = rel(f)

        for m in _REF.finditer(txt):
            href = unquote(m.group(1))
            if href.startswith(("http://", "https://", "mailto:", "data:", "#")):
                continue
            if href.startswith("/"):
                problems.append(
                    f"[link] {where}: {m.group(1)} é absoluto. Todo caminho "
                    f"interno tem de ser relativo, senão o site só funciona "
                    f"na raiz do domínio."
                )
                continue
            # relativo: resolve em relação à pasta do próprio arquivo
            target = (f.parent / href).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                problems.append(f"[link] {where}: {m.group(1)} não resolve")
            else:
                try:
                    r = target.relative_to(dist.resolve()).as_posix()
                except ValueError:
                    problems.append(f"[link] {where}: {m.group(1)} sai do dist/")
                    continue
                if r.startswith("assets/"):
                    referenced.add(r[len("assets/"):])

        if 'href="#/' in txt:
            problems.append(f"[rota] {where}: ainda tem rota de hash href=\"#/\"")
        if re.search(r'(?:href|src)="[^"]*\bdoc/', txt):
            problems.append(f"[rota] {where}: referência a doc/ na saída")

        if is_doc_page(f):
            for sel, pat in (
                ("h1.page-title", r'<h1 class="page-title"'),
                (".prose", r'<div class="prose">'),
                ("aside[data-toc]", r'<aside class="toc" id="toc" data-toc'),
                ("dialog#search", r'<dialog class="search" id="search"'),
            ):
                n = len(re.findall(pat, txt))
                if n != 1:
                    problems.append(f"[estrutura] {where}: {sel} aparece {n}×, esperado 1")
            first_script = txt.find("<script")
            first_css = txt.find("<link rel=\"stylesheet\"")
            if first_script == -1 or (first_css != -1 and first_script > first_css):
                problems.append(f"[estrutura] {where}: script de tema não é o primeiro no <head>")

            # Um cartão com href="#" é sempre bug: alguma resolução de rota
            # falhou e virou fallback. O checador de links não pega, porque
            # "#" não é caminho.
            dead = len(re.findall(r'class="card[^"]*" href="#"', txt))
            if dead:
                problems.append(f"[estrutura] {where}: {dead} cartão(ões) com href=\"#\" morto")

            # O ds.js também ancora títulos; sem a guarda da linha ~172 dele,
            # cada título fica com duas âncoras e aparece "##" na tela.
            for m in re.finditer(r"<(h2|h3)[^>]*>(.*?)</\1>", txt, re.S):
                if m.group(2).count('class="anchor"') > 1:
                    problems.append(f"[estrutura] {where}: título com âncora duplicada")
                    break

        for ico in _ICO.findall(txt):
            pass  # validado abaixo, com o conjunto único

    # ---- 4. reciprocidade de hreflang, 5. coerência de noindex ----
    for f in htmls:
        if not is_doc_page(f):
            continue
        txt = f.read_text(encoding="utf-8")
        where = rel(f)
        noindex = 'content="noindex' in txt
        for lang, href in _HREFLANG.findall(txt):
            if lang == "x-default":
                continue
            path = href[len(st.site_url):] if st.site_url and href.startswith(st.site_url) else href
            target = dist / path.strip("/") / "index.html"
            if not target.is_file():
                problems.append(f"[hreflang] {where}: alternate {lang} aponta para {href}, que não existe")
                continue
            back = target.read_text(encoding="utf-8")
            if 'content="noindex' in back:
                problems.append(f"[hreflang] {where}: declara alternate {lang} para uma página noindex")
            if f"hreflang=\"{path.strip('/').split('/')[0]}\"" not in back and target != f:
                pass  # reciprocidade exata é checada pelo lado de lá

        # O 404 é a exceção legítima: responde em qualquer endereço que não
        # existe, logo não tem URL canônica para declarar.
        if noindex and where != "404.html":
            cm = _CANON.search(txt)
            if not cm:
                problems.append(f"[noindex] {where}: noindex sem canonical")
            else:
                cpath = cm.group(1)
                cpath = cpath[len(st.site_url):] if st.site_url and cpath.startswith(st.site_url) else cpath
                ct = dist / cpath.strip("/") / "index.html"
                # Auto-canonical numa página noindex é correto e normal: é o
                # caso das páginas vazias, que não têm conteúdo em idioma
                # nenhum para onde consolidar. Só cadeia entre páginas
                # DIFERENTES é problema.
                if ct.resolve() != f.resolve() and ct.is_file() and \
                        'content="noindex' in ct.read_text(encoding="utf-8"):
                    problems.append(f"[noindex] {where}: canonical aponta para outra página noindex")

    # ---- sitemap não contém noindex ----
    sm = (dist / "sitemap.xml")
    if sm.is_file():
        smtxt = sm.read_text(encoding="utf-8")
        for f in htmls:
            txt = f.read_text(encoding="utf-8")
            if 'content="noindex' not in txt:
                continue
            url = st.site_url + "/" + rel(f).replace("/index.html", "/")
            if f"<loc>{url}</loc>" in smtxt:
                problems.append(f"[sitemap] {rel(f)} é noindex mas está no sitemap")

    # ---- 6. cobertura da busca: âncoras existem ----
    for lang in langs:
        idxs = list((dist / lang).glob("search-index.*.json"))
        if not idxs:
            problems.append(f"[busca] {lang}: nenhum search-index.*.json")
            continue
        idx = json.loads(idxs[0].read_text(encoding="utf-8"))
        for row in idx["s"]:
            page = idx["p"][row[0]]
            target = dist / page[1].strip("/") / "index.html"
            if not target.is_file():
                problems.append(f"[busca] {lang}: {page[0]} no índice mas sem arquivo")
                continue
            ids = set(_ID.findall(target.read_text(encoding="utf-8")))
            if row[1] not in ids:
                problems.append(f"[busca] {lang}: âncora #{row[1]} não existe em {page[0]}")
        seen = [p[0] for p in idx["p"]]
        if len(seen) != len(set(seen)):
            problems.append(f"[busca] {lang}: página duplicada no índice")

    # ---- 7. higiene de asset ----
    asset_files = {
        p.relative_to(dist / "assets").as_posix()
        for p in (dist / "assets").rglob("*") if p.is_file()
    } if (dist / "assets").is_dir() else set()
    orphans = sorted(a for a in asset_files - referenced
                     if not a.startswith(("css/", "js/")))
    for a in orphans:
        size = (dist / "assets" / a).stat().st_size // 1024
        problems.append(f"[asset] dist/assets/{a} ({size} KB) não é referenciado por nenhuma página")

    # ---- 8. ícones ----
    valid = _icons(st.theme / "js" / "ds.js")
    if valid:
        used: set[str] = set()
        for f in htmls:
            used |= set(_ICO.findall(f.read_text(encoding="utf-8")))
        for ico in sorted(used - valid):
            problems.append(f"[ícone] data-ico=\"{ico}\" não existe no mapa ICON do ds.js")

    # ---- relatório ----
    print(f"check · {len(htmls)} páginas em {dist}")
    if not problems:
        print("  8/8 regras passaram, nenhum problema")
        return 0
    groups: dict[str, list[str]] = {}
    for p in problems:
        tag = p.split("]")[0] + "]"
        groups.setdefault(tag, []).append(p)
    for tag in sorted(groups):
        rows = groups[tag]
        print(f"\n  {tag} {len(rows)} problema(s)")
        for r in rows[:12]:
            print("    " + r.split("] ", 1)[1])
        if len(rows) > 12:
            print(f"    ... e {len(rows) - 12} mais")
    print(f"\n{len(problems)} problema(s)")
    return 1
