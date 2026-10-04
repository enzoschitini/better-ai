"""manifest.py → lista plana de páginas, com urls, prev/next, crumbs e traduções.

É aqui que vivem as validações que fazem a promessa de "não pode divergir"
valer. Todas são fatais: um manifest que mente falha o build, não o site.
"""

from __future__ import annotations

import re
from pathlib import Path

from .fragment import scan
from .model import Area, Node, Page
from .slugs import slug


class ManifestError(ValueError):
    pass


def _icons_from_ds(ds_js: Path) -> set[str]:
    """Extrai as chaves do mapa ICON do ds.js.

    O conjunto válido é lido da implementação, nunca duplicado aqui — se
    alguém adicionar um ícone, o build passa a aceitá-lo sem nenhuma edição.
    """
    txt = ds_js.read_text(encoding="utf-8")
    block = re.search(r"ICON\s*=\s*\{(.*?)\n\s*\};", txt, re.S)
    if not block:
        return set()
    # Atenção: o mapa tem várias chaves por linha (`chevron: '…', down: '…'`),
    # então ancorar em ^ só pegaria a primeira de cada linha.
    return set(re.findall(r"(\w+)\s*:\s*'", block.group(1)))


def _walk(kids, parent_path, parent_node, out):
    """Converte os dicts do manifest em Node/folha, acumulando o caminho."""
    for k in kids:
        s = k.get("slug") or slug(k["t"])
        path = parent_path + [s]
        if "kids" in k:
            node = Node(name=k["t"], slug=s, parent=parent_node)
            _walk(k["kids"], path, node, out)
        else:
            out.append((k, path, parent_node))


def build_pages(
    manifest,
    content_dir: Path,
    ds_js: Path,
    langs: list[str],
    default_lang: str,
    base: str = "",
) -> tuple[list[Page], list[Area]]:
    valid_icons = _icons_from_ds(ds_js)
    frags = {l: scan(content_dir, l) for l in langs}

    areas: list[Area] = []
    leaves: list[tuple[dict, list[str], Node | None, Area]] = []

    for a in manifest.AREAS:
        aslug = a.get("slug") or slug(a["t"])
        if valid_icons and a["icon"] not in valid_icons:
            raise ManifestError(
                f"área {a['t']!r}: ícone {a['icon']!r} não existe no mapa ICON do ds.js. "
                f"Disponíveis: {', '.join(sorted(valid_icons))}"
            )
        area = Area(
            name=a["t"], slug=aslug, icon=a["icon"],
            titles=a.get("titles", {}), about=a.get("about", {}), loose=a.get("loose", {}),
            kids=a["kids"],
        )
        areas.append(area)
        collected: list[tuple[dict, list[str], Node | None]] = []
        _walk(a["kids"], [aslug], None, collected)
        for k, path, node in collected:
            leaves.append((k, path, node, area))

    # --- validações fatais -------------------------------------------------
    seen: dict[str, str] = {}
    problems: list[str] = []
    for k, path, _node, area in leaves:
        sp = "/".join(path)
        if sp in seen:
            problems.append(f"id duplicado {sp!r} (áreas {seen[sp]} e {area.name})")
        seen[sp] = area.name

        has_pt = sp in frags[default_lang]
        if k.get("empty") and has_pt:
            problems.append(
                f"{sp}: declarada empty=True mas content/{default_lang}/{sp}.html existe. "
                f"Tire o empty=True do manifest."
            )
        if not k.get("empty") and not has_pt:
            problems.append(
                f"{sp}: declarada com conteúdo mas content/{default_lang}/{sp}.html não existe. "
                f"Escreva o fragmento ou marque empty=True."
            )
    # fragmento sem lugar no manifest
    for lang in langs:
        for sp in frags[lang]:
            if sp == "index":
                continue
            if sp not in seen:
                problems.append(f"content/{lang}/{sp}.html não tem entrada no manifest.py")
    if problems:
        raise ManifestError("manifest inconsistente:\n  - " + "\n  - ".join(problems))

    # --- montagem das páginas ---------------------------------------------
    pages: list[Page] = []
    for lang in langs:
        order = 0
        home_frag = frags[lang].get("index") or frags[default_lang].get("index")
        pages.append(Page(
            id="home", kind="home", lang=lang, name="BetterAI",
            slug_path="index", url=f"{base}/{lang}/", out_path=f"{lang}/index.html",
            fragment=home_frag,
            is_mirror=("index" not in frags[lang] and home_frag is not None),
            translations={l for l in langs if "index" in frags[l]},
            order=order,
        ))
        order += 1

        for area in areas:
            pages.append(Page(
                id=area.slug, kind="overview", lang=lang, name=area.name,
                slug_path="", url=f"{base}/{lang}/{area.slug}/",
                out_path=f"{lang}/{area.slug}/index.html",
                area=area, translations=set(langs), order=order,
            ))
            order += 1

            collected: list[tuple[dict, list[str], Node | None]] = []
            _walk(area.kids, [area.slug], None, collected)
            for k, path, node in collected:
                sp = "/".join(path)
                frag = frags[lang].get(sp)
                mirror = False
                if frag is None and not k.get("empty"):
                    frag = frags[default_lang].get(sp)
                    mirror = frag is not None and lang != default_lang
                chain: list[Node] = []
                n = node
                while n is not None:
                    chain.insert(0, n)
                    n = n.parent
                pages.append(Page(
                    id=sp, kind="leaf", lang=lang, name=k["t"],
                    slug_path=sp, url=f"{base}/{lang}/{sp}/",
                    out_path=f"{lang}/{sp}/index.html",
                    area=area, crumbs=[c.name for c in chain], ancestors=chain,
                    empty=bool(k.get("empty")), fragment=frag, is_mirror=mirror,
                    translations={l for l in langs if sp in frags[l]},
                    order=order,
                ))
                order += 1

    # --- prev/next, dentro do mesmo idioma --------------------------------
    by_lang: dict[str, list[Page]] = {l: [] for l in langs}
    for p in pages:
        by_lang[p.lang].append(p)
    for seq in by_lang.values():
        for i, p in enumerate(seq):
            p.prev = seq[i - 1] if i else None
            p.next = seq[i + 1] if i + 1 < len(seq) else None

    # --- alternates por idioma --------------------------------------------
    by_id: dict[tuple[str, str], Page] = {(p.lang, p.id): p for p in pages}
    for p in pages:
        p.alt = {l: by_id[(l, p.id)].url for l in langs if (l, p.id) in by_id}

    return pages, areas
