"""Abas de área e menu lateral, gerados por página.

Porte de `renderTabs`, `renderNav`, `nodeHtml`, `pageLink` e `group` do
protótipo, com o trabalho de runtime do `markActive` resolvido no build:
a folha atual sai com `aria-current="page"`, e todo `.side-folder` ancestral
sai com `aria-expanded="true"` e seu `<ul>` sem `hidden`.

Resultado: o handler de clique do ds.js continua funcionando, e nenhum JS
precisa abrir o galho ativo.

Os ícones saem como `<i data-ico="x">`. O `icons()` do ds.js troca pelo SVG,
então os 24 caminhos de ícone continuam existindo em um lugar só.
"""

from __future__ import annotations

from .model import Area, Page
from .slugs import esc, slug
from .strings import tr


def tabs(page: Page, areas: list[Area], base: str) -> str:
    """A linha de abas: visão geral + uma por área."""
    out = []
    home = f"{base}/{page.lang}/"
    cur = ' aria-current="page"' if page.kind == "home" else ""
    out.append(f'      <a class="tab" href="{home}"{cur}>{esc(tr(page.lang, "overview"))}</a>')
    for a in areas:
        active = page.area is a and page.kind != "home"
        cur = ' aria-current="page"' if active else ""
        url = f"{base}/{page.lang}/{a.slug}/"
        out.append(f'      <a class="tab" href="{url}"{cur}>{esc(a.title(page.lang))}</a>')
    return "\n".join(out)


def _side_areas(page: Page, areas: list[Area], base: str) -> str:
    """Seletor de áreas, que no celular aparece dentro da gaveta."""
    out = ['      <div class="side-areas">']
    cur = ' aria-current="page"' if page.kind == "home" else ""
    out.append(f'        <a href="{base}/{page.lang}/"{cur}>{esc(tr(page.lang, "overview"))}</a>')
    for a in areas:
        active = page.area is a and page.kind != "home"
        cur = ' aria-current="page"' if active else ""
        out.append(f'        <a href="{base}/{page.lang}/{a.slug}/"{cur}>{esc(a.title(page.lang))}</a>')
    out.append("      </div>")
    return "\n".join(out)


def _link(p: Page, cur: Page, lang: str) -> str:
    attr = ' aria-current="page"' if p.id == cur.id else ""
    if p.empty:
        inner = (f'<span>{esc(p.nav_label)}</span>'
                 f'<span class="badge">{esc(tr(lang, "badge"))}</span>')
    else:
        inner = f"<span>{esc(p.nav_label)}</span>"
    return f'<li><a class="side-link" href="{p.url}"{attr}>{inner}</a></li>'


def _node(k: dict, path: list[str], cur: Page, pages_by_id: dict, lang: str, depth: int) -> str:
    pad = "  " * depth
    s = k.get("slug") or slug(k["t"])
    here = path + [s]
    if "kids" in k:
        inner = "\n".join(
            _node(c, here, cur, pages_by_id, lang, depth + 1) for c in k["kids"]
        )
        # aberto se a página atual está dentro desta pasta
        prefix = "/".join(here) + "/"
        open_ = cur.id.startswith(prefix)
        hidden = "" if open_ else " hidden"
        return (
            f'{pad}<li>\n'
            f'{pad}  <button class="side-link side-folder" type="button" '
            f'aria-expanded="{"true" if open_ else "false"}">'
            f'<span>{esc(k["t"])}</span><i class="chev" data-ico="chevron"></i></button>\n'
            f'{pad}  <ul class="side-sub"{hidden}>\n{inner}\n{pad}  </ul>\n'
            f'{pad}</li>'
        )
    p = pages_by_id.get((lang, "/".join(here)))
    if p is None:
        return ""
    return pad + _link(p, cur, lang)


def sidebar(page: Page, areas: list[Area], pages_by_id: dict, base: str) -> str:
    """O menu lateral: só a área atual, ou a lista de áreas na home."""
    lang = page.lang
    out = [_side_areas(page, areas, base)]

    if page.kind == "home":
        out.append(f'      <div class="side-group">')
        out.append(f'        <p class="side-title">{esc(tr(lang, "areasLbl"))}</p>')
        out.append("        <ul>")
        for a in areas:
            url = f"{base}/{lang}/{a.slug}/"
            out.append(f'          <li><a class="side-link" href="{url}">'
                       f'<span>{esc(a.title(lang))}</span></a></li>')
        out.append("        </ul>")
        out.append("      </div>")
        return "\n".join(out)

    a = page.area
    ov_cur = ' aria-current="page"' if page.kind == "overview" else ""
    out.append(f'      <a class="side-link" href="{base}/{lang}/{a.slug}/"{ov_cur}>'
               f'{esc(tr(lang, "overview"))}</a>')

    loose = [k for k in a.kids if "kids" not in k]
    dirs = [k for k in a.kids if "kids" in k]

    if loose:
        label = a.loose_label(lang) or tr(lang, "overview")
        out.append('      <div class="side-group">')
        out.append(f'        <p class="side-title">{esc(label)}</p>')
        out.append("        <ul>")
        for k in loose:
            out.append("          " + _node(k, [a.slug], page, pages_by_id, lang, 0))
        out.append("        </ul>")
        out.append("      </div>")

    for d in dirs:
        out.append('      <div class="side-group">')
        out.append(f'        <p class="side-title">{esc(d["t"])}</p>')
        out.append("        <ul>")
        for k in d["kids"]:
            out.append("          " + _node(k, [a.slug, d.get("slug") or slug(d["t"])],
                                            page, pages_by_id, lang, 0))
        out.append("        </ul>")
        out.append("      </div>")

    return "\n".join(x for x in out if x.strip())
