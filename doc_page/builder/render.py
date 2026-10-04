"""Montagem do layout: cabeçalho do artigo, corpo, rodapé, hreflang.

Substituição por `{{chave}}`, sem dependência de template engine.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import nav
from .highlight import apply_to_html
from .model import Area, Page
from .settings import Settings
from .slugs import esc, slug
from .strings import HTML_LANG, LANG_NAMES, bag, tr

_ANCHOR_H = re.compile(r"<(h2|h3)([^>]*)>(.*?)</\1>", re.S)
_TAG = re.compile(r"<[^>]+>")


def _anchor_headings(html: str) -> str:
    """Dá id e link de âncora a cada h2/h3, deduplicando slugs repetidos.

    O ds.js monta o TOC a partir desses headings; os ids precisam existir no
    HTML para o índice de busca poder apontar para eles.
    """
    seen: dict[str, int] = {}

    def repl(m: re.Match) -> str:
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        if "id=" in attrs:
            return m.group(0)
        text = _TAG.sub("", inner).strip()
        base = slug(text) or tag
        n = seen.get(base, 0)
        seen[base] = n + 1
        sid = base if n == 0 else f"{base}-{n + 1}"
        return (f'<{tag}{attrs} id="{sid}">{inner}'
                f'<a class="anchor" href="#{sid}" aria-label="{esc(text)}">#</a></{tag}>')

    return _ANCHOR_H.sub(repl, html)


def _empty_body(page: Page, st: Settings) -> str:
    lang = page.lang
    url = page.rel_root + f"{lang}/{page.area.slug}/"
    return (
        '<div class="empty">\n'
        f'  <span class="empty-icon" data-ico="blank"></span>\n'
        f'  <p class="empty-title">{esc(tr(lang, "emptyTitle"))}</p>\n'
        f'  <p>{esc(tr(lang, "emptyText"))}</p>\n'
        f'  <a class="btn-cta" href="{url}">{esc(tr(lang, "emptyCta"))}'
        f'<i data-ico="chevron"></i></a>\n'
        "</div>"
    )


def _overview_body(page: Page, st: Settings, pages_by_id: dict) -> str:
    """Visão geral de área: cartões para os filhos diretos."""
    a, lang = page.area, page.lang
    out = [f'<p>{esc(a.about_text(lang))}</p>', '<div class="cards">']
    for k in a.kids:
        if "kids" in k:
            s = k.get("slug") or slug(k["t"])
            # Desce até a primeira folha em qualquer profundidade: uma pasta
            # pode conter só outras pastas (Agents contém só Utils), e aí não
            # existe folha direta para linkar.
            fid = _first_leaf_id(k, [a.slug, s])
            tgt = pages_by_id.get((lang, fid)) if fid else None
            href = page.href(tgt) if tgt else "#"
            n = sum(1 for _ in _walk_count(k))
            out.append(
                f'  <a class="card" href="{href}">'
                f'<span class="card-icon" data-ico="folder"></span>'
                f'<span class="card-title">{esc(k["t"])}</span>'
                f'<span class="card-text">{n} página(s).</span></a>'
            )
        else:
            pid = f'{a.slug}/{k.get("slug") or slug(k["t"])}'
            p = pages_by_id.get((lang, pid))
            if p is None:
                continue
            lead = p.fragment.lead if p.fragment else ""
            out.append(
                f'  <a class="card" href="{page.href(p)}">'
                f'<span class="card-icon" data-ico="{a.icon}"></span>'
                f'<span class="card-title">{esc(k["t"])}</span>'
                f'<span class="card-text">{esc(lead)}</span></a>'
            )
    out.append("</div>")
    return "\n".join(out)


def _first_leaf_id(node: dict, path: list[str]) -> str | None:
    """id da primeira folha em profundidade, para o cartão de uma pasta."""
    for k in node.get("kids", []):
        s = k.get("slug") or slug(k["t"])
        if "kids" in k:
            found = _first_leaf_id(k, path + [s])
            if found:
                return found
        else:
            return "/".join(path + [s])
    return None


def _walk_count(node):
    for k in node.get("kids", []):
        if "kids" in k:
            yield from _walk_count(k)
        else:
            yield k


def _home_body(page: Page, st: Settings, areas: list[Area]) -> str:
    lang = page.lang
    body = page.fragment.body if page.fragment else ""
    cards = ['<h2>' + esc(tr(lang, "areasLbl")) + "</h2>", '<div class="cards">']
    for a in areas:
        cards.append(
            f'  <a class="card" href="{page.rel_root}{lang}/{a.slug}/">'
            f'<span class="card-icon" data-ico="{a.icon}"></span>'
            f'<span class="card-title">{esc(a.title(lang))}</span>'
            f'<span class="card-text">{esc(a.about_text(lang))}</span></a>'
        )
    cards.append("</div>")
    return body + "\n" + "\n".join(cards)


def _page_foot(page: Page, st: Settings) -> str:
    lang = page.lang
    out = [
        '        <div class="feedback">',
        f'          <span class="q">{esc(tr(lang, "feedbackQ"))}</span>',
        f'          <button class="fb-btn" type="button"><i data-ico="up"></i>{esc(tr(lang, "yes"))}</button>',
        f'          <button class="fb-btn" type="button"><i data-ico="dn"></i>{esc(tr(lang, "no"))}</button>',
    ]
    if page.kind == "leaf" and not page.empty:
        rel = f"content/{st_lang_for(page)}/{page.slug_path}.html"
        out.append(f'          <a class="edit" href="{st.edit(rel)}">'
                   f'<i data-ico="edit"></i>{esc(tr(lang, "edit"))}</a>')
    out.append("        </div>")

    if page.kind == "leaf" and not page.empty:
        rel = f"content/{st_lang_for(page)}/{page.slug_path}.html"
        out.append(f'        <p class="source">{esc(tr(lang, "source"))} '
                   f'<a href="{st.blob(rel)}"><code>{esc(rel)}</code></a></p>')

    if page.prev or page.next:
        out.append(f'        <nav class="pager" aria-label="{esc(tr(lang, "pagerLbl"))}">')
        if page.prev:
            out.append(f'          <a class="pager-link prev" href="{page.href(page.prev)}">'
                       f'<i data-ico="chevron"></i><div><small>{esc(tr(lang, "prev"))}</small>'
                       f'<span>{esc(page.prev.nav_label)}</span></div></a>')
        if page.next:
            out.append(f'          <a class="pager-link next" href="{page.href(page.next)}">'
                       f'<div><small>{esc(tr(lang, "next"))}</small>'
                       f'<span>{esc(page.next.nav_label)}</span></div>'
                       f'<i data-ico="chevron"></i></a>')
        out.append("        </nav>")
    return "\n".join(out)


def st_lang_for(page: Page) -> str:
    """De qual idioma veio o fragmento que está sendo servido."""
    return "pt" if page.is_mirror else page.lang


def _head_meta(page: Page, st: Settings) -> str:
    lang = page.lang
    out = []
    if page.noindex:
        out.append('<meta name="robots" content="noindex, follow">')
        # Espelho: o conteúdo real está em pt, então consolida o sinal lá.
        # Vazia: não existe conteúdo em idioma nenhum, então auto-canonical —
        # apontar para a irmã em pt criaria cadeia de canonical entre duas
        # páginas noindex, que é o que o check pega.
        if page.is_mirror and not page.empty:
            target = "/" + page.alt.get("pt", page.path)
        else:
            target = page.abs_url
        out.append(f'<link rel="canonical" href="{st.site_url}{target}">')
    else:
        out.append(f'<link rel="canonical" href="{st.site_url}{page.abs_url}">')
        # hreflang só para traduções reais. Espelho nunca declara o próprio idioma.
        for l in sorted(page.translations):
            if l in page.alt:
                out.append(f'<link rel="alternate" hreflang="{l}" '
                           f'href="{st.site_url}/{page.alt[l]}">')
        if "pt" in page.alt:
            out.append(f'<link rel="alternate" hreflang="x-default" '
                       f'href="{st.site_url}/{page.alt["pt"]}">')
    return "\n".join(out)


def build_prose(page: Page, st: Settings, areas: list[Area], pages_by_id: dict) -> tuple[str, str, str, str]:
    """(prose, título, resumo, eyebrow) — primeira passada.

    Separado de `render` porque o índice de busca é construído a partir do
    corpo, e o href do índice entra no `window.DOCS` de cada página: sem essa
    separação, o build teria uma dependência circular.
    """
    lang = page.lang
    if page.kind == "home":
        prose = _home_body(page, st, areas)
        title = page.fragment.title if page.fragment else "BetterAI"
        lead = page.fragment.lead if page.fragment else ""
        eyebrow = esc(tr(lang, "overview"))
    elif page.kind == "overview":
        prose = _overview_body(page, st, pages_by_id)
        title = page.area.title(lang)
        lead = page.area.about_text(lang)
        eyebrow = esc(tr(lang, "overview"))
    elif page.empty:
        prose = _empty_body(page, st)
        title = page.name
        lead = ""
        eyebrow = esc(" / ".join([page.area.name] + page.crumbs))
    else:
        prose = page.fragment.body if page.fragment else ""
        title = page.title
        lead = page.fragment.lead if page.fragment else ""
        eyebrow = esc(" / ".join([page.area.name] + page.crumbs) if page.crumbs
                      else (page.area.loose_label(lang) or page.area.name))

    if page.is_mirror:
        prose = (f'<div class="callout" data-kind="note"><p>'
                 f'{esc(tr(lang, "untranslated"))}</p></div>\n' + prose)

    return apply_to_html(_anchor_headings(prose)), title, lead, eyebrow


def render(
    page: Page,
    st: Settings,
    areas: list[Area],
    pages_by_id: dict,
    layout: str,
    css_href: str,
    js_href: str,
    index_href: str,
    prose: str,
    title: str,
    lead: str,
    eyebrow: str,
) -> str:
    lang = page.lang
    s = bag(lang)

    # --- cabeçalho -------------------------------------------------------
    area_label = page.area.title(lang) if page.area else tr(lang, "overview")
    head_title = (f"{title} | {area_label} | BetterAI Docs" if page.kind == "leaf"
                  else f"{title} | BetterAI Docs")

    lang_items = []
    for code, name in LANG_NAMES:
        checked = "true" if code == lang else "false"
        lang_items.append(
            f'            <li role="none"><button type="button" role="menuitemradio" '
            f'data-lang="{code}" aria-checked="{checked}"><span>{name}</span>'
            f'<i class="ck" data-ico="check"></i></button></li>'
        )

    foot = []
    for label, pid in st.foot_links.items():
        p = pages_by_id.get((lang, pid))
        foot.append(f'        <a href="{page.href(p) if p else "#"}">{esc(label)}</a>')

    docs_json = json.dumps({
        "lang": lang, "root": page.rel_root, "alt": page.alt,
        "index": page.rel_root + index_href,
        "i": {"noResults": tr(lang, "noResults", "%s"),
              "suggestions": tr(lang, "suggestions")},
    }, ensure_ascii=False, separators=(",", ":"))

    values = {
        "html_lang": HTML_LANG.get(lang, lang),
        "head_title": esc(head_title),
        "description": esc(lead or tr(lang, "tagline")),
        "head_meta": _head_meta(page, st),
        "css_href": page.rel_root + css_href,
        "js_href": page.rel_root + js_href,
        "docs_json": docs_json,
        "base": page.rel_root.rstrip("/") or ".",
        "home_url": page.rel_root + f"{lang}/",
        "github_url": st.github_url,
        "swagger_url": st.swagger_url,
        "lang_upper": lang.upper(),
        "lang_items": "\n".join(lang_items),
        "tabs": nav.tabs(page, areas),
        "sidebar": nav.sidebar(page, areas, pages_by_id),
        "subbar_area": esc(area_label),
        "subbar_here": esc(title),
        "eyebrow": eyebrow,
        "page_title": esc(title),
        "lead": esc(lead),
        "prose": prose,
        "page_foot": _page_foot(page, st),
        "foot_links": "\n".join(foot),
    }
    values.update({f"s_{k}": esc(v) for k, v in s.items()})

    out = layout
    for k, v in values.items():
        out = out.replace("{{" + k + "}}", str(v))
    # placeholders não preenchidos viram vazio, nunca ficam visíveis
    out = re.sub(r"\{\{[a-z_]+\}\}", "", out)
    return out
