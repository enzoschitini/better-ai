#!/usr/bin/env python3
"""BetterAI docs build: ipynb_contents/ + _content/ -> web_documentation/pages/.

The documentation tree is the source folder tree. Page bodies come from
web_documentation/_content/<page-id>.<lang>.html, written by hand (see the
docs-from-ipynb skill). Everything else on a page is generated here: chrome,
navigation, pager, language switcher, heading anchors, syntax highlighting,
the search index and the language dispatcher at web_documentation/index.html.

Nothing under web_documentation/pages/ is ever hand-edited; it is all output.
web_documentation/_design-system/ is input and is never written to.

Usage:
    python build.py                       build into web_documentation/
    python build.py --check               build into a temp dir, diff, report drift
    python build.py --page-id <src path>  print the page id for a source file
    python build.py --list [<folder>]     list source files and their content status
"""

from __future__ import annotations

import argparse
import hashlib
import html as html_mod
import json
import posixpath
import re
import shutil
import sys
import tempfile
import unicodedata
from pathlib import Path

LANGS = ["pt", "it", "en"]
BASE_LANG = "pt"
LANG_NAMES = {"pt": "Português", "it": "Italiano", "en": "English"}
HTML_LANG = {"pt": "pt-BR", "it": "it", "en": "en"}

SRC_DIR_NAME = "ipynb_contents"
WEB_DIR_NAME = "web_documentation"

IGNORE_DIRS = {"graphify-out", ".ipynb_checkpoints", "__pycache__", "videos", ".git"}
IGNORE_FILES = {"__init__.py", "README.md", ".gitkeep", ".DS_Store"}
SOURCE_EXTS = {".ipynb", ".md"}

ORDER_PREFIX = re.compile(r"^\s*(\d+)\s*[.)-]?\s+")


# --------------------------------------------------------------------------- #
# text helpers                                                                #
# --------------------------------------------------------------------------- #

def strip_marks(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if not unicodedata.combining(c))


def slug(s: str) -> str:
    """Mirrors slug() in ds.js and in the prototype."""
    s = strip_marks(s).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def fold(s: str) -> str:
    """Mirrors fold() in docs.js: NFD, no diacritics, lowercase.

    Length-preserving with respect to the input, so the <mark> offsets the
    client computes on the folded text are valid on the raw text.
    """
    return strip_marks(s).lower()


def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def ext(url) -> str:
    """Atributos para um link que sai do site: abre em outra aba."""
    return (' target="_blank" rel="noopener"'
            if str(url).startswith(("http://", "https://")) else "")


def asset_v(path: Path) -> str:
    """?v=<hash> no url do asset, para o navegador nunca servir css/js velho."""
    if not path.exists():
        return ""
    return "?v=" + hashlib.md5(path.read_bytes()).hexdigest()[:8]


def css_links(root: str, cfg: dict) -> str:
    """One <link> per stylesheet the design system imports, each with its own ?v=hash.

    design-system.css pulls the partials in with @import, and those urls carry no version,
    so a browser keeps serving a stale content.css even when the entry file is fresh.
    Linking the partials directly (same order as the @imports) closes that gap.
    """
    return "\n".join('<link rel="stylesheet" href="%s">'
                     % (u if u.startswith("http") else "%s_design-system/css/%s" % (root, u))
                     for u in cfg["_cssurls"])


def strip_tags(s: str) -> str:
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html_mod.unescape(s)).strip()


# --------------------------------------------------------------------------- #
# icons (copied from ds.js so the build never depends on JS for chrome)        #
# --------------------------------------------------------------------------- #

ICON = {
    "chevron": '<path d="m9 6 6 6-6 6"/>',
    "down": '<path d="m6 9 6 6 6-6"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6 7 7M17 17l1.4 1.4M5.6 18.4 7 17M17 7l1.4-1.4"/>',
    "moon": '<path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.6-3.6"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "close": '<path d="m6 6 12 12M18 6 6 18"/>',
    "copy": '<rect x="9" y="9" width="11" height="11" rx="2.5"/><path d="M5 15V6.5A2.5 2.5 0 0 1 7.5 4H15"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "list": '<path d="M4 6h16M4 12h10M4 18h13"/>',
    "go": '<path d="M8 16 16 8M9 8h7v7"/>',
    "edit": '<path d="M4 20h4L19 9l-4-4L4 16zM13.5 6.5l4 4"/>',
    "up": '<path d="M7 11v9H4v-9zM7 11l4-7a2 2 0 0 1 2.6 2.3L13 10h5.2a2 2 0 0 1 2 2.4l-1.2 6a2 2 0 0 1-2 1.6H7"/>',
    "dn": '<path d="M17 13V4h3v9zM17 13l-4 7a2 2 0 0 1-2.6-2.3L11 14H5.8a2 2 0 0 1-2-2.4l1.2-6A2 2 0 0 1 7 4h10"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.6v.2"/>',
    "tip": '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.6.5 1 1.3 1 2.2h5.2c0-.9.4-1.7 1-2.2A6 6 0 0 0 12 3z"/>',
    "warn": '<path d="M12 4 2.8 19.5h18.4z"/><path d="M12 10v4.5M12 17.2v.2"/>',
    "danger": '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6M15 9l-6 6"/>',
    "note": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    "blank": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>',
    "bolt": '<path d="M13 3 5 14h6l-1 7 8-11h-6z"/>',
    "boxes": '<path d="M12 3 4 7v10l8 4 8-4V7z"/><path d="m4 7 8 4 8-4M12 11v10"/>',
    "code": '<path d="m8 8-4 4 4 4M16 8l4 4-4 4M13.5 5l-3 14"/>',
    "layout": '<rect x="3" y="4" width="18" height="16" rx="2.5"/><path d="M3 9h18M9 9v11"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "folder": '<path d="M3.5 7a2 2 0 0 1 2-2h4l2 2.5h7a2 2 0 0 1 2 2V17a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z"/>',
}


def ico(name: str, cls: str = "") -> str:
    return ('<svg class="ico %s" viewBox="0 0 24 24" aria-hidden="true">%s</svg>'
            % (cls, ICON.get(name, "")))


# --------------------------------------------------------------------------- #
# syntax highlighting (ported from the prototype's RULES/highlight)            #
# --------------------------------------------------------------------------- #

_STR = r"\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'"

RULES = {
    "python": (re.compile(
        r"(#.*$)|(" + _STR + r")|\b(def|class|return|import|from|as|if|else|elif|for|in"
        r"|while|try|except|raise|with|and|or|not|lambda|await|async|pass)\b"
        r"|\b(None|True|False|\d+(?:\.\d+)?)\b|([A-Za-z_]\w*)(?=\()", re.M),
        ["c", "s", "k", "n", "f"]),
    "bash": (re.compile(
        r"((?:^|(?<=\s))#.*$)|(" + _STR + r")|((?<=\s)--?[A-Za-z][\w-]*)"
        r"|(^[ \t]*[A-Za-z.][\w.\\/-]*)", re.M),
        ["c", "s", "n", "f"]),
    "json": (re.compile(
        r"(\"(?:\\.|[^\"\\])*\")(?=\s*:)|(\"(?:\\.|[^\"\\])*\")|\b(true|false|null)\b"
        r"|(-?\b\d+(?:\.\d+)?\b)"),
        ["f", "s", "k", "n"]),
    "env": (re.compile(r"(#.*$)|(^[A-Z_]+)(?==)", re.M), ["c", "f"]),
}


def highlight(src: str, lang: str) -> str:
    rule = RULES.get(lang)
    if not rule:
        return esc(src)
    regex, classes = rule
    out, last = [], 0
    for m in regex.finditer(src):
        if not m.group(0):
            continue
        gi = next(i for i, g in enumerate(m.groups()) if g is not None)
        out.append(esc(src[last:m.start()]))
        out.append('<span class="t-%s">%s</span>' % (classes[gi], esc(m.group(0))))
        last = m.end()
    out.append(esc(src[last:]))
    return "".join(out)


# --------------------------------------------------------------------------- #
# the documentation tree                                                      #
# --------------------------------------------------------------------------- #

class Node:
    __slots__ = ("title", "children", "src", "ext", "parent_titles", "page_id",
                 "area", "source_empty")

    def __init__(self, title, children=None, src=None, ext=None, parent_titles=()):
        self.title = title
        self.children = children
        self.src = src
        self.ext = ext
        self.parent_titles = list(parent_titles)
        self.page_id = None
        self.area = None
        self.source_empty = False

    @property
    def is_dir(self):
        return self.children is not None


def title_of(name: str) -> str:
    return ORDER_PREFIX.sub("", name).strip()


def sort_key(path: Path):
    stem = path.stem if path.is_file() else path.name
    m = ORDER_PREFIX.match(stem)
    return (int(m.group(1)) if m else 10 ** 6, strip_marks(stem).lower())


def source_is_empty(path: Path) -> bool:
    if path.stat().st_size == 0:
        return True
    if path.suffix == ".md":
        return not path.read_text(encoding="utf-8", errors="replace").strip()
    try:
        nb = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (ValueError, OSError):
        return False
    return not "".join("".join(c.get("source", []))
                       for c in nb.get("cells", [])).strip()


def notebook_text(path: Path) -> str:
    """The markdown of a notebook, in cell order. Code cells become fences."""
    if path.suffix == ".md":
        return path.read_text(encoding="utf-8", errors="replace")
    nb = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    parts = []
    for cell in nb.get("cells", []):
        text = "".join(cell.get("source", []))
        if not text.strip():
            continue
        if cell.get("cell_type") == "code":
            parts.append("```python\n%s\n```" % text.rstrip())
        else:
            parts.append(text)
    return "\n\n".join(parts)


def walk_dir(directory: Path, parents: list) -> list:
    out = []
    for entry in sorted(directory.iterdir(), key=sort_key):
        if entry.name in IGNORE_FILES or entry.name.startswith("."):
            continue
        if entry.is_dir():
            if entry.name in IGNORE_DIRS:
                continue
            title = title_of(entry.name)
            kids = walk_dir(entry, parents + [title])
            if kids:
                out.append(Node(title, children=kids, parent_titles=parents))
        elif entry.suffix in SOURCE_EXTS:
            node = Node(title_of(entry.stem), src=entry, ext=entry.suffix.lstrip("."),
                        parent_titles=parents)
            node.source_empty = source_is_empty(entry)
            out.append(node)
    return out


class Area:
    def __init__(self, title, icon, cfg_entry, children):
        # the folder name fixes the url/id; config "title" only changes the label
        self.title = cfg_entry.get("title", title)
        self.icon = icon
        self.cfg = cfg_entry
        self.children = children
        self.area_id = slug(title)


class Page:
    """A rendered page: the home, an area overview, or a leaf."""

    def __init__(self, kind, title, area=None, node=None):
        self.kind = kind                      # home | overview | leaf
        self.title = title
        self.area = area
        self.node = node
        self.page_id = ("home" if kind == "home"
                        else area.area_id if kind == "overview"
                        else node.page_id)
        self.crumb_titles = list(node.parent_titles) if node else []

    @property
    def rel_path(self) -> str:
        if self.kind == "home":
            return "index.html"
        if self.kind == "overview":
            return "%s/index.html" % self.area.area_id
        parts = [self.area.area_id] + [slug(t) for t in self.crumb_titles]
        return "/".join(parts + [slug(self.title) + ".html"])

    def url(self, lang: str) -> str:
        return "pages/%s/%s" % (lang, self.rel_path)

    def root_prefix(self, lang: str) -> str:
        depth = len(self.url(lang).split("/")) - 1
        return "../" * depth

    @property
    def source_label(self):
        if self.kind != "leaf":
            return None
        return "%s/%s" % (SRC_DIR_NAME,
                          self.node.src.as_posix().split(SRC_DIR_NAME + "/", 1)[-1])


def rel_url(frm: Page, target_url: str, lang: str) -> str:
    """A link from `frm` to a site-root-relative url, as a relative path."""
    base = posixpath.dirname(frm.url(lang))
    return posixpath.relpath(target_url, base) if base else target_url


def build_tree(src_root: Path, cfg: dict):
    configured = {a["dir"]: a for a in cfg["areas"]}
    dirs = [d for d in src_root.iterdir()
            if d.is_dir() and d.name not in IGNORE_DIRS and not d.name.startswith(".")]
    ordered = [d for name in configured for d in dirs if d.name == name]
    ordered += sorted([d for d in dirs if d.name not in configured], key=sort_key)

    areas = []
    for d in ordered:
        entry = configured.get(d.name, {"dir": d.name, "icon": "folder"})
        kids = walk_dir(d, [])
        if not kids:
            continue
        area = Area(title_of(d.name), entry.get("icon", "folder"), entry, kids)
        areas.append(area)

        def assign(nodes):
            for n in nodes:
                n.area = area
                if n.is_dir:
                    assign(n.children)
                else:
                    n.page_id = "/".join(
                        [area.area_id] + [slug(t) for t in n.parent_titles]
                        + [slug(n.title)])
        assign(kids)

    pages = [Page("home", cfg["ui"][BASE_LANG]["homeTitle"])]
    for area in areas:
        pages.append(Page("overview", area.title, area=area))

        def collect(nodes):
            for n in nodes:
                if n.is_dir:
                    collect(n.children)
                else:
                    pages.append(Page("leaf", n.title, area=area, node=n))
        collect(area.children)
    return areas, pages


def leaves(node) -> list:
    if node.is_dir:
        return [l for k in node.children for l in leaves(k)]
    return [node]


# --------------------------------------------------------------------------- #
# content fragments -> prose HTML                                             #
# --------------------------------------------------------------------------- #

ALLOWED_TAGS = {
    "page", "h2", "h3", "p", "ul", "ol", "li", "strong", "em", "code", "br", "a",
    "pre", "codetabs", "tab", "table", "thead", "tbody", "tr", "th", "td", "div",
    "details", "summary", "endpoint", "cards", "card", "media",
}
CALLOUT_KINDS = {"note", "info", "tip", "warn", "danger"}


class ContentError(Exception):
    pass


def validate_fragment(raw: str, where: str):
    problems = []
    for m in re.finditer(r"<\s*/?\s*([A-Za-z][\w-]*)([^>]*)>", raw):
        tag, attrs = m.group(1).lower(), m.group(2)
        if tag not in ALLOWED_TAGS:
            problems.append("<%s> is not in the markup contract" % tag)
            continue
        if tag == "div":
            cls = re.search(r'class\s*=\s*"([^"]*)"', attrs)
            if not cls or "callout" not in cls.group(1).split():
                problems.append('<div> is only allowed as class="callout"')
            else:
                kind = re.search(r'data-kind\s*=\s*"([^"]*)"', attrs)
                if not kind or kind.group(1) not in CALLOUT_KINDS:
                    problems.append("callout needs data-kind of %s"
                                    % "/".join(sorted(CALLOUT_KINDS)))
        if tag in ("h2", "h3") and re.search(r"\bid\s*=", attrs):
            problems.append("<%s> must not carry an id; the build assigns it" % tag)
        if re.search(r"\bstyle\s*=", attrs):
            problems.append("inline style= on <%s>" % tag)
    if re.search(r'href\s*=\s*"#/', raw):
        problems.append('href="#/..." is prototype hash routing; use href="@/<page-id>"')
    if re.search(r"(?i)<h1\b", raw):
        problems.append("<h1> belongs to the build, not the body")
    if problems:
        raise ContentError("%s:\n  - %s" % (where, "\n  - ".join(sorted(set(problems)))))


def code_block(lang: str, title: str, body: str) -> str:
    code = highlight(body, lang)
    pre = '<pre data-lang="%s"><code>%s</code></pre>' % (esc(lang), code)
    if title:
        return ('<div class="code"><div class="code-head">'
                '<span class="code-title">%s</span>'
                '<button class="copy" type="button"></button></div>'
                '<div class="code-body">%s</div></div>' % (esc(title), pre))
    return ('<div class="code plain"><div class="code-body">%s'
            '<button class="copy floating" type="button"></button></div></div>' % pre)


def pre_text(block: str) -> str:
    """The raw text inside <pre><code>...</code></pre>."""
    m = re.search(r"(?s)<code[^>]*>(.*?)</code>", block)
    inner = m.group(1) if m else ""
    return html_mod.unescape(inner).lstrip("\n").rstrip()


def render_codetabs(block: str) -> str:
    tabs = re.findall(r'(?s)<tab\s+title\s*=\s*"([^"]*)"\s*>(.*?)</tab>', block)
    if not tabs:
        raise ContentError("<codetabs> without any <tab title=\"...\">")
    heads, bodies = [], []
    for i, (title, inner) in enumerate(tabs):
        pre = re.search(r"(?s)<pre([^>]*)>.*?</pre>", inner)
        if not pre:
            raise ContentError("<tab title=\"%s\"> has no <pre> block" % title)
        lang = re.search(r'data-lang\s*=\s*"([^"]*)"', pre.group(1))
        text = pre_text(pre.group(0))
        heads.append('<button class="code-tab" type="button" role="tab" '
                     'aria-selected="%s">%s</button>'
                     % ("true" if i == 0 else "false", esc(title)))
        bodies.append('<pre data-lang="%s"%s><code>%s</code></pre>'
                      % (esc(lang.group(1) if lang else ""),
                         "" if i == 0 else " hidden",
                         highlight(text, lang.group(1) if lang else "")))
    return ('<div class="code" data-tabs><div class="code-head">'
            '<div class="code-tabs" role="tablist">%s</div>'
            '<button class="copy" type="button"></button></div>'
            '<div class="code-body">%s</div></div>'
            % ("".join(heads), "".join(bodies)))


def render_endpoint(attrs: str) -> str:
    method = (re.search(r'method\s*=\s*"([^"]*)"', attrs) or [None, "GET"])[1].upper()
    path = (re.search(r'path\s*=\s*"([^"]*)"', attrs) or [None, "/"])[1]
    return ('<div class="endpoint"><span class="method" data-m="%s">%s</span>'
            '<span>%s</span></div>' % (esc(method), esc(method), esc(path)))


def render_cards(attrs: str, inner: str) -> str:
    one = " one" if re.search(r"\bone\b", attrs) else ""
    items = re.findall(r'(?s)<card\s+([^>]*)>(.*?)</card>', inner)
    out = []
    for card_attrs, text in items:
        href = (re.search(r'href\s*=\s*"([^"]*)"', card_attrs) or [None, "#"])[1]
        icon = (re.search(r'icon\s*=\s*"([^"]*)"', card_attrs) or [None, "note"])[1]
        title = (re.search(r'title\s*=\s*"([^"]*)"', card_attrs) or [None, ""])[1]
        if icon not in ICON:
            raise ContentError("unknown card icon %r" % icon)
        out.append('<a class="card" href="%s"><span class="card-icon">%s</span>'
                   '<span class="card-title">%s</span>'
                   '<span class="card-text">%s</span></a>'
                   % (esc(href), ico(icon), esc(title), text.strip()))
    return '<div class="cards%s">%s</div>' % (one, "".join(out))


def render_media(attrs: str) -> str:
    src = (re.search(r'src\s*=\s*"([^"]*)"', attrs) or [None, ""])[1]
    caption = (re.search(r'caption\s*=\s*"([^"]*)"', attrs) or [None, ""])[1]
    cap = '<figcaption>%s</figcaption>' % esc(caption) if caption else ""
    missing = ('<div class="frame-missing" hidden>%s<span>%s</span></div>'
               % (ico("blank"), esc(caption or src)))
    if src.lower().endswith((".mp4", ".webm", ".mov")):
        body = '<video controls preload="metadata" src="%s"></video>' % esc(src)
    else:
        body = '<img src="%s" alt="%s">' % (esc(src), esc(caption))
    return '<figure class="frame">%s%s%s</figure>' % (body, missing, cap)


def rewrite_links(text: str, page: Page, lang: str, by_id: dict) -> str:
    def page_link(m):
        target, anchor = m.group(1), m.group(2) or ""
        if target not in by_id:
            raise ContentError("link to unknown page id %r" % target)
        return 'href="%s%s"' % (rel_url(page, by_id[target].url(lang), lang), anchor)

    text = re.sub(r'href="@/([A-Za-z0-9/-]+)(#[A-Za-z0-9_-]+)?"', page_link, text)
    return text.replace('"@assets/', '"%sassets/' % page.root_prefix(lang))


def render_prose(fragment: str, page: Page, lang: str, by_id: dict):
    """Returns (prose_html, lead, sections) for one _content fragment."""
    m = re.search(r"(?s)<page([^>]*)>(.*)</page>", fragment)
    if not m:
        raise ContentError("fragment must be wrapped in <page data-lead=\"...\">")
    attrs, body = m.group(1), m.group(2)
    lead_m = re.search(r'data-lead\s*=\s*"([^"]*)"', attrs)
    lead = html_mod.unescape(lead_m.group(1)) if lead_m else ""

    # headings: assign ids first, so the search index and the anchors agree
    seen, heads = {}, []
    def head_id(text):
        base = slug(text) or "secao"
        hid, n = base, 2
        while hid in seen:
            hid = "%s-%d" % (base, n)
            n += 1
        seen[hid] = True
        return hid

    def on_heading(mh):
        level, inner = mh.group(1), mh.group(2)
        text = strip_tags(inner)
        hid = head_id(text)
        heads.append((hid, text, mh.start()))
        return ('<h%s id="%s"><a class="anchor" href="#%s" '
                'aria-label="Link para esta seção">#</a>%s</h%s>'
                % (level, hid, hid, inner, level))

    # section bodies for the index, taken before the structural rewrites
    plain_heads = [(hm.start(), hm.end(), strip_tags(hm.group(2)))
                   for hm in re.finditer(r"(?s)<h([23])\b[^>]*>(.*?)</h\1>", body)]
    sections = []
    for i, (start, end, text) in enumerate(plain_heads):
        stop = plain_heads[i + 1][0] if i + 1 < len(plain_heads) else len(body)
        sections.append({"heading": text, "text": strip_tags(body[end:stop])})

    body = re.sub(r"(?s)<h([23])\b[^>]*>(.*?)</h\1>", on_heading, body)
    for i, (hid, text, _) in enumerate(heads):
        if i < len(sections):
            sections[i]["id"] = hid

    # protect blocks that must not be touched by the later passes
    vault = []
    def stash(replacement):
        vault.append(replacement)
        return "\x00B%d\x00" % (len(vault) - 1)

    body = re.sub(r"(?s)<codetabs\b[^>]*>.*?</codetabs>",
                  lambda mm: stash(render_codetabs(mm.group(0))), body)
    body = re.sub(r"(?s)<pre([^>]*)>.*?</pre>",
                  lambda mm: stash(code_block(
                      (re.search(r'data-lang\s*=\s*"([^"]*)"', mm.group(1)) or [None, ""])[1],
                      (re.search(r'data-title\s*=\s*"([^"]*)"', mm.group(1)) or [None, ""])[1],
                      pre_text(mm.group(0)))), body)
    body = re.sub(r"(?s)<endpoint([^>]*)>\s*</endpoint>",
                  lambda mm: stash(render_endpoint(mm.group(1))), body)
    body = re.sub(r"(?s)<cards([^>]*)>(.*?)</cards>",
                  lambda mm: stash(render_cards(mm.group(1), mm.group(2))), body)
    body = re.sub(r"(?s)<media([^>]*)>\s*</media>",
                  lambda mm: stash(render_media(mm.group(1))), body)
    body = re.sub(r"(?s)(<table\b.*?</table>)",
                  lambda mm: stash('<div class="table-wrap">%s</div>' % mm.group(1)), body)

    body = rewrite_links(body, page, lang, by_id)
    for i, block in enumerate(vault):
        body = body.replace("\x00B%d\x00" % i, rewrite_links(block, page, lang, by_id))

    sections = [s for s in sections if s.get("id")]
    return body.strip(), lead, sections


# --------------------------------------------------------------------------- #
# generated bodies: home, area overview, empty state                          #
# --------------------------------------------------------------------------- #

def card_html(href, icon, title, text, row=False):
    go = ico("go", "card-go") if row else ""
    return ('<a class="card%s" href="%s"><span class="card-icon">%s</span>'
            '<span class="card-title">%s</span><span class="card-text">%s</span>%s</a>'
            % (" row" if row else "", esc(href), ico(icon), esc(title), esc(text), go))


def home_body(page, lang, cfg, areas, by_id):
    t = cfg["ui"][lang]
    h = cfg["home"][lang]
    url = lambda pid: rel_url(page, by_id[pid].url(lang), lang)
    quick = h["quick"]
    cards = "".join(card_html(url(a.area_id), a.icon, a.title,
                              a.cfg["about"][lang]) for a in areas)
    pop = "".join(card_html(url(p["id"]), p["icon"], by_id[p["id"]].title, p["text"])
                  for p in h["popular"] if p["id"] in by_id)
    hero = render_media('src="%sassets/img/betterai-cover.png" caption="%s"'
                        % (page.root_prefix(lang), cfg["site"]["tagline"]))
    cr = h["creator"]
    lk = lambda href, label, i: ('<a class="btn-soft" href="%s" target="_blank" rel="noopener">%s%s</a>'
                                 % (esc(href), ico(i), label))
    creator = ('<h2 id="criador">%s</h2><div class="profile">'
               '<img src="%sassets/img/profile.jpg" alt="Enzo Schitini" width="96" height="96">'
               '<div class="profile-info"><strong>Enzo Schitini</strong><span>%s</span><p>%s</p>'
               '<div class="profile-links">%s%s</div></div></div>'
               % (esc(cr["h"]), page.root_prefix(lang), esc(cr["role"]), cr["text"],
                  lk(cfg["links"]["linkedin"], "LinkedIn", "user"),
                  lk(cfg["links"]["profile"], "GitHub", "code")))
    return (hero + "<p>%s</p>"
            "<h2 id=\"comece\">%s</h2><div class=\"cards one\">%s</div>"
            "<div class=\"callout\" data-kind=\"tip\"><p>%s</p></div>"
            "<p>%s</p><ul>%s</ul>"
            "%s<h2 id=\"areas\">%s</h2><div class=\"cards\">%s</div>"
            "<h2 id=\"populares\">%s</h2><div class=\"cards\">%s</div>"
            % (h["p1"], esc(h["startH"]),
               card_html(url(quick["id"]), quick["icon"], by_id[quick["id"]].title,
                         quick["text"], row=True),
               h["tip"], h["p2"], "".join("<li>%s</li>" % i for i in h["li"]),
               creator, esc(h["exploreH"]), cards, esc(t["popular"]), pop))


def overview_body(page, lang, cfg, by_id):
    t = cfg["ui"][lang]
    area = page.area
    loose = [k for k in area.children if not k.is_dir]
    dirs = [k for k in area.children if k.is_dir]
    out = []
    if loose:
        out.append('<h2 id="%s">%s</h2>' % (slug(area.cfg["loose"][lang]),
                                            esc(area.cfg["loose"][lang])))
        out.append('<div class="cards">%s</div>' % "".join(
            card_html(rel_url(page, by_id[n.page_id].url(lang), lang), "note", n.title,
                      t["blankCard"] if n.source_empty else t["pageCard"])
            for n in loose))
    if dirs:
        out.append('<h2 id="%s">%s</h2>' % (slug(t["sections"]), esc(t["sections"])))
        cards = []
        for d in dirs:
            names = [l.title for l in leaves(d)]
            text = ", ".join(names[:3])
            if len(names) > 3:
                text += t["more"] % (len(names) - 3)
            first = leaves(d)[0]
            cards.append(card_html(rel_url(page, by_id[first.page_id].url(lang), lang),
                                   "folder", d.title, text))
        out.append('<div class="cards">%s</div>' % "".join(cards))
    return "".join(out)


def empty_body(page, lang, cfg, nxt, by_id):
    t = cfg["ui"][lang]
    src = page.source_label or ""
    text = (t["emptySourceBlank"] if page.node and page.node.source_empty
            else t["emptyPending"]) % esc(src)
    go = ""
    if nxt:
        go = ('<a class="btn-cta" href="%s%s">%s</a>'
              % (page.root_prefix(lang), nxt.url(lang),
                 esc(t["goTo"] % nxt.title)))
    return ('<div class="empty">%s<p class="empty-title">%s</p><p>%s</p>%s</div>'
            % (ico("blank"), esc(t["emptyTitle"]), text, go))


# --------------------------------------------------------------------------- #
# page chrome                                                                 #
# --------------------------------------------------------------------------- #

def nav_html(page, lang, cfg, areas, by_id):
    t = cfg["ui"][lang]
    root = page.root_prefix(lang)
    active = page.page_id
    area = page.area

    def link(node):
        p = by_id[node.page_id]
        cur = ' aria-current="page"' if p.page_id == active else ""
        badge = ('<span class="badge">%s</span>' % esc(t["badge"])) if node.source_empty else ""
        return ('<li><a class="side-link" href="%s%s"%s><span>%s</span>%s</a></li>'
                % (root, p.url(lang), cur, esc(node.title), badge))

    def on_path(node):
        return any(l.page_id == active for l in leaves(node))

    def tree_html(node):
        if not node.is_dir:
            return link(node)
        open_ = on_path(node)
        return ('<li><button class="side-link side-folder" type="button" '
                'aria-expanded="%s"><span>%s</span>%s</button>'
                '<ul class="side-sub"%s>%s</ul></li>'
                % ("true" if open_ else "false", esc(node.title),
                   ico("chevron", "chev"), "" if open_ else " hidden",
                   "".join(tree_html(k) for k in node.children)))

    def group(title, inner):
        return ('<div class="side-group"><p class="side-title">%s</p><ul>%s</ul></div>'
                % (esc(title), inner))

    tabs = [("home", t["overview"], root + by_id["home"].url(lang))] + \
           [(a.area_id, a.title, root + by_id[a.area_id].url(lang)) for a in areas]
    current_area = "home" if page.kind == "home" else area.area_id
    switcher = '<div class="side-areas">%s</div>' % "".join(
        '<a href="%s"%s>%s</a>' % (href, ' aria-current="page"' if aid == current_area else "",
                                   esc(label)) for aid, label, href in tabs)

    if page.kind == "home":
        body = ('<a class="side-link" href="%s%s" aria-current="page"><span>%s</span></a>'
                % (root, by_id["home"].url(lang), esc(t["overview"])))
        body += group(t["areas"], "".join(
            '<li><a class="side-link" href="%s%s"><span>%s</span></a></li>'
            % (root, by_id[a.area_id].url(lang), esc(a.title)) for a in areas))
        body += group(t["popular"], "".join(
            '<li><a class="side-link" href="%s%s"><span>%s</span></a></li>'
            % (root, by_id[p["id"]].url(lang), esc(by_id[p["id"]].title))
            for p in cfg["home"][lang]["popular"] if p["id"] in by_id))
    else:
        cur = ' aria-current="page"' if page.kind == "overview" else ""
        body = ('<a class="side-link" href="%s%s"%s><span>%s</span></a>'
                % (root, by_id[area.area_id].url(lang), cur, esc(t["overview"])))
        loose = [k for k in area.children if not k.is_dir]
        dirs = [k for k in area.children if k.is_dir]
        if loose:
            body += group(area.cfg["loose"][lang], "".join(link(n) for n in loose))
        for d in dirs:
            body += group(d.title, "".join(tree_html(k) for k in d.children))
    return switcher + body


def page_html(page, lang, cfg, areas, pages, by_id, body, lead, status):
    t = cfg["ui"][lang]
    root = page.root_prefix(lang)
    i = pages.index(page)
    prev = pages[i - 1] if i > 0 else None
    nxt = pages[i + 1] if i + 1 < len(pages) else None

    def label(p):
        if p.kind == "overview":
            return t["overviewOf"] % p.title
        if p.kind == "home":
            return t["overview"]
        return p.title

    eyebrow = ""
    if page.kind == "leaf":
        eyebrow = (" / ".join(page.crumb_titles) if page.crumb_titles
                   else page.area.cfg["loose"][lang])

    docs_cfg = {
        "lang": lang,
        "root": root,
        "index": "%ssearch-%s.json" % (root, lang),
        "alt": {l: page.url(l) for l in LANGS},
        "i": {"noResults": t["noResults"]},
    }

    lang_items = "".join(
        '<li role="none"><button type="button" role="menuitemradio" data-lang="%s" '
        'aria-checked="%s"><span>%s</span>%s</button></li>'
        % (l, "true" if l == lang else "false", esc(LANG_NAMES[l]), ico("check", "ck"))
        for l in LANGS)

    tabs_row = "".join(
        '<a class="tab" href="%s%s"%s>%s</a>'
        % (root, by_id[aid].url(lang),
           ' aria-current="page"' if aid == (page.area.area_id if page.area else "home") else "",
           esc(label_))
        for aid, label_ in [("home", t["overview"])] + [(a.area_id, a.title) for a in areas])

    pager = ""
    if prev:
        pager += ('<a class="pager-link prev" href="%s%s">%s<div><small>%s</small>'
                  '<span>%s</span></div></a>'
                  % (root, prev.url(lang), ico("chevron"), esc(t["prev"]),
                     esc(label(prev))))
    if nxt:
        pager += ('<a class="pager-link next" href="%s%s"><div><small>%s</small>'
                  '<span>%s</span></div>%s</a>'
                  % (root, nxt.url(lang), esc(t["next"]), esc(label(nxt)),
                     ico("chevron")))

    source = ""
    if page.source_label:
        source = ('<p class="source">%s <code>%s</code></p>'
                  % (esc(t["source"]), esc(page.source_label)))

    edit = ""
    if page.source_label and cfg["links"].get("repo"):
        edit_url = "%s/%s" % (cfg["links"]["repo"].rstrip("/"), page.source_label)
        edit = ('<a class="edit" href="%s"%s>%s%s</a>'
                % (esc(edit_url), ext(edit_url), ico("edit"), esc(t["edit"])))

    def foot_link(l):
        if "page" in l:
            return '<a href="%s%s">%s</a>' % (root, by_id[l["page"]].url(lang),
                                              esc(by_id[l["page"]].title))
        label = l["label"][lang] if isinstance(l["label"], dict) else l["label"]
        return '<a href="%s"%s>%s</a>' % (esc(l["url"]), ext(l["url"]), esc(label))

    footer_res = "".join(foot_link(l) for l in cfg["footer"]["resources"])
    footer_docs = "".join('<a href="%s%s">%s</a>' % (root, by_id[a.area_id].url(lang), esc(a.title))
                          for a in areas)
    cr = cfg["home"][lang]["creator"]
    footer_creator = (
        '<div class="foot-me"><img src="%sassets/img/profile.jpg" alt="" width="44" height="44">'
        '<div><strong>Enzo Schitini</strong><span>%s</span></div></div>'
        '<a href="%s"%s>LinkedIn</a><a href="%s"%s>GitHub</a>'
        % (root, esc(cr["short"]), esc(cfg["links"]["linkedin"]), ext(cfg["links"]["linkedin"]),
           esc(cfg["links"]["profile"]), ext(cfg["links"]["profile"])))

    title_tag = (cfg["site"]["name"] if page.kind == "home"
                 else "%s | %s" % (page.title, cfg["site"]["name"]))

    # Tarja de aviso no topo. Opcional: ui.<lang>.banner vazio e nenhuma tarja sai.
    # ds.js ja cuida do botao de fechar via #banner button.
    banner_text = (t.get("banner") or "").strip()
    banner = ('  <div class="banner" id="banner">\n'
              '    <span><a href="%s"%s>%s</a></span>\n'
              '    <button type="button" aria-label="%s">%s</button>\n'
              '  </div>\n' % (esc(cfg["links"]["linkedin"]), ext(cfg["links"]["linkedin"]),
                              esc(banner_text), esc(t.get("closeBanner", "")),
                              ico("close"))) if banner_text else ""

    return """<!doctype html>
<html lang="%(htmllang)s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(lead_attr)s">
<link rel="canonical" href="%(canonical)s">
<script>
  // Tema antes da pintura, para nao piscar.
  (function () {
    var t = null;
    try { t = localStorage.getItem('betterai-docs-theme'); } catch (e) {}
    if (!t) t = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    document.documentElement.dataset.theme = t;
  })();
</script>
%(cssLinks)s
</head>
<body>
<a class="skip" href="#main">%(skip)s</a>

<header class="header" id="header">
%(banner)s  <div class="bar">
    <div class="row1">
      <a class="brand" href="%(home)s">
        <img src="%(root)sassets/img/logo-icon.png" alt="" onerror="this.hidden=true">
        <span class="brand-name">%(brand)s</span>
        <span class="brand-sub">%(brandsub)s</span>
      </a>
      <button class="search-trigger" type="button" data-open-search aria-label="%(searchLbl)s">
        %(searchIco)s<span>%(searchPh)s</span><kbd>Ctrl K</kbd>
      </button>
      <div class="actions">
        <a class="btn-soft" href="%(github)s"%(githubExt)s>%(codeIco)sGitHub</a>
        <a class="btn-cta" href="%(quickstart)s">%(quickstartLbl)s%(chevIco)s</a>
        <div class="lang">
          <button class="lang-btn" id="langBtn" type="button" aria-haspopup="menu"
                  aria-expanded="false" aria-label="%(langLbl)s">%(globeIco)s<b>%(langUp)s</b></button>
          <ul class="lang-menu" id="langMenu" role="menu" hidden>%(langItems)s</ul>
        </div>
        <button class="icon-btn" type="button" data-theme-toggle aria-label="%(themeLbl)s"></button>
      </div>
    </div>
    <nav class="tabs-row" aria-label="%(tabsLbl)s">%(tabsRow)s</nav>
    <div class="subbar">
      <button type="button" data-menu-toggle aria-controls="side" aria-expanded="false">
        %(menuIco)s<span>%(crumbArea)s</span>
      </button>
      %(chevIco)s
      <span class="here">%(crumbPage)s</span>
    </div>
  </div>
  <div class="header-line"></div>
</header>

<div class="shell">
  <aside class="side-wrap" id="side" aria-label="%(navLbl)s">
    <nav class="side">%(nav)s</nav>
  </aside>
  <div class="main">
    <div class="main-row">
      <main class="article" id="main">
        <header>
          %(eyebrow)s
          <div class="title-row">
            <h1 class="page-title" tabindex="-1">%(h1)s</h1>
            <div class="copy-page">
              <button class="cp-main" type="button" data-copy-page>%(copyIco)s<span>%(copyPage)s</span></button>
            </div>
          </div>
          %(lead)s
          <details class="toc-inline"><summary>%(onThisPage)s</summary><ul></ul></details>
        </header>
        <div class="prose">%(body)s</div>
        <div class="feedback">%(edit)s</div>
        %(source)s
        <nav class="pager" aria-label="%(pagerLbl)s">%(pager)s</nav>
      </main>
      <aside class="toc" id="toc" data-toc aria-label="%(onThisPage)s"></aside>
    </div>
    <footer class="site-foot">
      <div class="foot-grid">
        <div class="foot-brand">
          <a class="brand" href="%(home)s"><span class="brand-name">%(brand)s</span><span class="brand-sub">%(brandsub)s</span></a>
          <p>%(tagline)s</p>
          <a class="btn-soft" href="%(github)s"%(githubExt)s>%(codeIco)s%(footRepo)s</a>
        </div>
        <div class="foot-col"><h2>%(footDocs)s</h2>%(footerDocs)s</div>
        <div class="foot-col"><h2>%(footRes)s</h2>%(footerRes)s</div>
        <div class="foot-col"><h2>%(footCreator)s</h2>%(footerCreator)s</div>
      </div>
      <div class="foot-bottom">
        <span>&copy; 2026 %(brand)s &middot; %(footLicense)s</span>
        <span>%(footMadeBy)s <a href="%(linkedin)s"%(linkedinExt)s>Enzo Schitini</a></span>
      </div>
    </footer>
  </div>
</div>
<div class="scrim"></div>

<dialog class="search" id="search" aria-label="%(searchLbl)s">
  <div class="search-field">
    %(searchIco)s
    <input id="q" type="search" placeholder="%(dlgPh)s" autocomplete="off" spellcheck="false" aria-controls="results">
    <kbd>Esc</kbd>
  </div>
  <ul class="results" id="results" role="listbox" aria-label="%(results)s"></ul>
  <div class="search-foot">
    <span><kbd>&#8593;</kbd><kbd>&#8595;</kbd><span>%(navigate)s</span></span>
    <span><kbd>Enter</kbd><span>%(open)s</span></span>
  </div>
</dialog>

<script>window.DOCS = %(docs)s;</script>
<script src="%(root)s_design-system/js/ds.js%(vDs)s"></script>
<script src="%(root)s_design-system/js/docs.js%(vDocs)s"></script>
</body>
</html>
""" % {
        "htmllang": HTML_LANG[lang],
        "title": esc(title_tag),
        "lead_attr": esc(lead or cfg["site"]["name"]),
        "canonical": esc(cfg["site"].get("baseUrl", "").rstrip("/") + "/" + page.url(lang))
                     if cfg["site"].get("baseUrl") else esc(page.url(lang)),
        "root": root,
        "skip": esc(t["skip"]),
        "home": root + by_id["home"].url(lang),
        "brand": esc(cfg["site"]["brand"]),
        "brandsub": esc(cfg["site"]["brandSub"]),
        "searchLbl": esc(t["searchLbl"]),
        "searchPh": esc(t["searchPh"]),
        "dlgPh": esc(t["dlgPh"]),
        "results": esc(t["results"]),
        "navigate": esc(t["navigate"]),
        "open": esc(t["open"]),
        "searchIco": ico("search"),
        "codeIco": ico("code"),
        "chevIco": ico("chevron"),
        "globeIco": ico("globe"),
        "menuIco": ico("menu"),
        "copyIco": ico("copy"),
        "github": esc(cfg["links"].get("github", "#")),
        "githubExt": ext(cfg["links"].get("github", "#")),
        "quickstart": root + by_id["getting-started/quickstart"].url(lang),
        "quickstartLbl": esc(by_id["getting-started/quickstart"].title),
        "langLbl": esc(t["langLbl"]),
        "langUp": lang.upper(),
        "langItems": lang_items,
        "themeLbl": esc(t["themeLbl"]),
        "tabsLbl": esc(t["tabsLbl"]),
        "tabsRow": tabs_row,
        "navLbl": esc(t["navLbl"]),
        "nav": nav_html(page, lang, cfg, areas, by_id),
        "crumbArea": esc(cfg["site"]["brand"] if page.kind == "home" else page.area.title),
        "crumbPage": esc(t["overview"] if page.kind in ("home", "overview") else page.title),
        "eyebrow": '<div class="eyebrow">%s</div>' % esc(eyebrow) if eyebrow else "",
        "h1": esc(t["homeTitle"] if page.kind == "home" else page.title),
        "copyPage": esc(t["copyPage"]),
        "lead": '<p class="lead">%s</p>' % esc(lead) if lead else "",
        "onThisPage": esc(t["onThisPage"]),
        "body": body,
        "edit": edit,
        "source": source,
        "pagerLbl": esc(t["pagerLbl"]),
        "pager": pager,
        "tagline": esc(cfg["site"]["tagline"]),
        "footRes": esc(t["footRes"]),
        "footPlat": esc(t["footPlat"]),
        "footDocs": esc(t["footDocs"]),
        "footCreator": esc(t["footCreator"]),
        "footRepo": esc(t["footRepo"]),
        "footLicense": esc(t["footLicense"]),
        "footMadeBy": esc(t["footMadeBy"]),
        "footerDocs": footer_docs,
        "footerCreator": footer_creator,
        "linkedin": esc(cfg["links"]["linkedin"]),
        "linkedinExt": ext(cfg["links"]["linkedin"]),
        "footerRes": footer_res,
        "banner": banner,
        "docs": json.dumps(docs_cfg, ensure_ascii=False),
        "cssLinks": css_links(root, cfg),
        "vDs": cfg.get("_assetv", {}).get("ds", ""),
        "vDocs": cfg.get("_assetv", {}).get("docs", ""),
    }


def dispatcher_html(cfg, by_id):
    alts = json.dumps({l: by_id["home"].url(l) for l in LANGS}, ensure_ascii=False)
    return """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<!--
  Gerado por .claude/skills/docs-from-ipynb/scripts/build.py. Nao edite.
  Esta pagina so escolhe o idioma e redireciona. O site vive em pages/<lang>/.
-->
<script>
  (function () {
    var alts = %s, order = %s, pick = null;
    try { pick = localStorage.getItem('betterai-docs-lang'); } catch (e) {}
    if (!alts[pick]) {
      var nav = (navigator.language || '').toLowerCase();
      for (var i = 0; i < order.length; i++) {
        if (nav.indexOf(order[i]) === 0) { pick = order[i]; break; }
      }
    }
    if (!alts[pick]) pick = %s;
    location.replace(alts[pick] + location.hash);
  })();
</script>
<meta http-equiv="refresh" content="0; url=%s">
<style>
  body { margin: 0; min-height: 100vh; display: grid; place-items: center;
         font: 400 1rem/1.5 system-ui, sans-serif; background: #fff; color: #030710; }
  a { color: #4b61d1; }
  @media (prefers-color-scheme: dark) { body { background: #030710; color: #eceef3; } a { color: #93a4ff; } }
</style>
</head>
<body>
<p><a href="%s">%s</a></p>
</body>
</html>
""" % (esc(cfg["site"]["name"]), alts, json.dumps(LANGS), json.dumps(BASE_LANG),
       esc(by_id["home"].url(BASE_LANG)), esc(by_id["home"].url(BASE_LANG)),
       esc(cfg["site"]["name"]))


# --------------------------------------------------------------------------- #
# build                                                                       #
# --------------------------------------------------------------------------- #

def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def content_path(content_dir: Path, page_id: str, lang: str) -> Path:
    return content_dir / ("%s.%s.html" % (page_id.replace("/", "--"), lang))


def build(repo: Path, out_dir: Path, cfg: dict, report: list):
    src_root = repo / SRC_DIR_NAME
    content_dir = repo / WEB_DIR_NAME / "_content"
    ds_dir = repo / WEB_DIR_NAME / "_design-system"
    entry = (ds_dir / "css" / "design-system.css").read_text(encoding="utf-8")
    cfg["_cssurls"] = [u if u.startswith("http") else u + asset_v(ds_dir / "css" / u)
                       for u in re.findall(r"@import\s+url\([\"']?([^\"')]+)", entry)]
    cfg["_assetv"] = {
                      "ds": asset_v(ds_dir / "js" / "ds.js"),
                      "docs": asset_v(ds_dir / "js" / "docs.js")}
    areas, pages = build_tree(src_root, cfg)
    by_id = {p.page_id: p for p in pages}
    counts = {"content": 0, "fallback": 0, "empty": 0, "generated": 0}
    errors = []

    # A blank source file only counts as "empty" while _content holds no real text for
    # it. Pages documented straight from the code (no notebook) carry real content.
    for p in pages:
        if p.node and p.node.source_empty:
            base = content_path(content_dir, p.page_id, BASE_LANG)
            if base.exists() and "Fonte ainda vazia" not in base.read_text(encoding="utf-8"):
                p.node.source_empty = False

    for lang in LANGS:
        index_pages, index_sections, popular_idx = [], [], []
        t = cfg["ui"][lang]
        for order, page in enumerate(pages):
            status, lead, sections = "generated", "", []
            nxt = pages[order + 1] if order + 1 < len(pages) else None

            if page.kind == "home":
                body = home_body(page, lang, cfg, areas, by_id)
                lead = t["homeLead"]
            elif page.kind == "overview":
                body = overview_body(page, lang, cfg, by_id)
                lead = page.area.cfg["about"][lang]
            else:
                frag_path = content_path(content_dir, page.page_id, lang)
                base_path = content_path(content_dir, page.page_id, BASE_LANG)
                use, prefix = None, ""
                if frag_path.exists():
                    use, status = frag_path, "content"
                elif base_path.exists():
                    use, status = base_path, "fallback"
                    prefix = ('<div class="callout" data-kind="note"><p>%s</p></div>'
                              % esc(t["untranslated"]))
                if use is None:
                    body, status = empty_body(page, lang, cfg, nxt, by_id), "empty"
                else:
                    try:
                        rendered, lead, sections = render_prose(
                            use.read_text(encoding="utf-8"), page,
                            BASE_LANG if status == "fallback" else lang, by_id)
                        body = prefix + rendered
                    except ContentError as exc:
                        errors.append("%s: %s" % (use.name, exc))
                        body, status = empty_body(page, lang, cfg, nxt, by_id), "error"

            counts[status] = counts.get(status, 0) + 1
            target = out_dir / page.url(lang)
            write(target, page_html(page, lang, cfg, areas, pages, by_id,
                                    body, lead, status))
            report.append("%-9s %s" % (status, page.url(lang)))

            crumb = (t["areaOverview"] if page.kind == "overview"
                     else cfg["site"]["brand"] if page.kind == "home"
                     else " / ".join([page.area.title] + page.crumb_titles))
            if page.kind != "home":
                pi = len(index_pages)
                index_pages.append([page.area.area_id if page.area else "home",
                                    page.url(lang), page.title, crumb, order])
                if page.page_id in [p["id"] for p in cfg["home"][lang]["popular"]]:
                    popular_idx.append((pi, page.page_id))
                for sec in sections:
                    index_sections.append([pi, sec["id"], sec["heading"],
                                           fold(sec["text"]), sec["text"]])

        pop_order = [p["id"] for p in cfg["home"][lang]["popular"]]
        popular_idx = [pi for pi, pid in sorted(popular_idx,
                                                key=lambda x: pop_order.index(x[1]))]
        write(out_dir / ("search-%s.json" % lang),
              json.dumps({"p": index_pages, "s": index_sections,
                          "popular": popular_idx}, ensure_ascii=False))
        report.append("%-9s %s" % ("index", "search-%s.json" % lang))

    write(out_dir / "index.html", dispatcher_html(cfg, by_id))
    report.append("%-9s %s" % ("dispatch", "index.html"))
    return counts, errors, pages, areas


# --------------------------------------------------------------------------- #
# default config                                                              #
# --------------------------------------------------------------------------- #

def default_config() -> dict:
    ui = {
        "pt": {
            "skip": "Ir para o conteúdo", "searchLbl": "Buscar na documentação",
            "searchPh": "Buscar...", "dlgPh": "Buscar páginas e seções",
            "results": "Resultados", "navigate": "navegar", "open": "abrir",
            "themeLbl": "Alternar tema claro e escuro", "langLbl": "Idioma",
            "tabsLbl": "Áreas da documentação", "navLbl": "Navegação da documentação",
            "onThisPage": "Nesta página", "footRes": "Recursos", "footPlat": "Plataforma",
            "overview": "Visão geral", "areas": "Áreas", "popular": "Mais consultadas",
            "suggestions": "Sugestões", "areaOverview": "Visão geral da área",
            "overviewOf": "%s: visão geral", "badge": "vazio",
            "copyPage": "Copiar página", "helpful": "Esta página foi útil?",
            "edit": "Editar no GitHub", "source": "Fonte:", "prev": "Anterior",
            "next": "Próxima", "pagerLbl": "Páginas vizinhas",
            "noResults": "Nada encontrado para “%s”. Tente o nome de um módulo, como “Pinecone”.",
            "untranslated": "Esta página ainda não foi traduzida. Você está vendo a versão em português.",
            "homeTitle": "Documentação da BetterAI",
            "homeLead": "Múltiplos modelos de IA, um único back-end unificado.",
            "sections": "Seções", "more": " e mais %d",
            "blankCard": "Página ainda em branco.", "pageCard": "Página da documentação.",
            "emptyTitle": "Esta página ainda está em branco",
            "emptySourceBlank": "O arquivo <code>%s</code> existe, mas não tem conteúdo. Quando ele for preenchido, o texto aparece aqui.",
            "emptyPending": "O conteúdo de <code>%s</code> ainda não foi publicado nesta documentação.",
            "goTo": "Ir para %s",
            "banner": "Protótipo de layout. O conteúdo das páginas é de exemplo.",
            "closeBanner": "Fechar aviso",
        },
        "it": {
            "skip": "Vai al contenuto", "searchLbl": "Cerca nella documentazione",
            "searchPh": "Cerca...", "dlgPh": "Cerca pagine e sezioni",
            "results": "Risultati", "navigate": "naviga", "open": "apri",
            "themeLbl": "Cambia tema chiaro o scuro", "langLbl": "Lingua",
            "tabsLbl": "Aree della documentazione", "navLbl": "Navigazione della documentazione",
            "onThisPage": "In questa pagina", "footRes": "Risorse", "footPlat": "Piattaforma",
            "overview": "Panoramica", "areas": "Aree", "popular": "Più consultate",
            "suggestions": "Suggerimenti", "areaOverview": "Panoramica dell’area",
            "overviewOf": "%s: panoramica", "badge": "vuota",
            "copyPage": "Copia pagina", "helpful": "Questa pagina ti è stata utile?",
            "edit": "Modifica su GitHub", "source": "Fonte:", "prev": "Precedente",
            "next": "Successiva", "pagerLbl": "Pagine vicine",
            "noResults": "Nessun risultato per “%s”. Prova con il nome di un modulo, come “Pinecone”.",
            "untranslated": "Questa pagina non è ancora stata tradotta. Stai vedendo la versione in portoghese.",
            "homeTitle": "Documentazione di BetterAI",
            "homeLead": "Più modelli di IA, un unico back-end unificato.",
            "sections": "Sezioni", "more": " e altre %d",
            "blankCard": "Pagina ancora vuota.", "pageCard": "Pagina della documentazione.",
            "emptyTitle": "Questa pagina è ancora vuota",
            "emptySourceBlank": "Il file <code>%s</code> esiste, ma non ha contenuto. Quando verrà compilato, il testo comparirà qui.",
            "emptyPending": "Il contenuto di <code>%s</code> non è ancora stato pubblicato in questa documentazione.",
            "goTo": "Vai a %s",
            "banner": "Prototipo di layout. Il contenuto delle pagine è di esempio.",
            "closeBanner": "Chiudi avviso",
        },
        "en": {
            "skip": "Skip to content", "searchLbl": "Search the documentation",
            "searchPh": "Search...", "dlgPh": "Search pages and sections",
            "results": "Results", "navigate": "navigate", "open": "open",
            "themeLbl": "Toggle light and dark theme", "langLbl": "Language",
            "tabsLbl": "Documentation areas", "navLbl": "Documentation navigation",
            "onThisPage": "On this page", "footRes": "Resources", "footPlat": "Platform",
            "overview": "Overview", "areas": "Areas", "popular": "Most visited",
            "suggestions": "Suggestions", "areaOverview": "Area overview",
            "overviewOf": "%s: overview", "badge": "empty",
            "copyPage": "Copy page", "helpful": "Was this page helpful?",
            "edit": "Edit on GitHub", "source": "Source:", "prev": "Previous",
            "next": "Next", "pagerLbl": "Neighboring pages",
            "noResults": "Nothing found for “%s”. Try a module name, such as “Pinecone”.",
            "untranslated": "This page has not been translated yet. You are seeing the Portuguese version.",
            "homeTitle": "BetterAI documentation",
            "homeLead": "Multiple AI models, one unified back end.",
            "sections": "Sections", "more": " and %d more",
            "blankCard": "Page still blank.", "pageCard": "Documentation page.",
            "emptyTitle": "This page is still blank",
            "emptySourceBlank": "The file <code>%s</code> exists but has no content. Once it is filled in, the text will show up here.",
            "emptyPending": "The content of <code>%s</code> has not been published to this documentation yet.",
            "goTo": "Go to %s",
            "banner": "Layout prototype. Page content is placeholder text.",
            "closeBanner": "Dismiss notice",
        },
    }

    areas = [
        {"dir": "Getting Started", "icon": "bolt",
         "about": {
             "pt": "Instalação, dependências e licença. Do clone ao primeiro request.",
             "it": "Installazione, dipendenze e licenza. Dal clone alla prima richiesta.",
             "en": "Installation, dependencies and license. From clone to first request."},
         "loose": {"pt": "Primeiros passos", "it": "Primi passi", "en": "First steps"}},
        {"dir": "Modules", "icon": "boxes",
         "about": {
             "pt": "Os serviços de IA da plataforma: agentes, parsing de documentos, deep research, embeddings, imagens, Pinecone e a API.",
             "it": "I servizi di IA della piattaforma: agenti, parsing di documenti, deep research, embedding, immagini, Pinecone e l’API.",
             "en": "The platform’s AI services: agents, document parsing, deep research, embeddings, images, Pinecone and the API."},
         "loose": {"pt": "Geral", "it": "Generale", "en": "General"}},
        {"dir": "Internal Source Code", "icon": "code",
         "about": {
             "pt": "A infraestrutura por baixo: tracing, bancos de dados, storage, custo por token e utilitários.",
             "it": "L’infrastruttura sottostante: tracing, database, storage, costo per token e utilità.",
             "en": "The infrastructure underneath: tracing, databases, storage, token cost and utilities."},
         "loose": {"pt": "Geral", "it": "Generale", "en": "General"}},
        {"dir": "Streamlit Applications", "icon": "layout",
         "about": {
             "pt": "Acquarello e Content Generator, as duas aplicações que rodam sobre a plataforma.",
             "it": "Acquarello e Content Generator, le due applicazioni che girano sulla piattaforma.",
             "en": "Acquarello and Content Generator, the two applications that run on the platform."},
         "loose": {"pt": "Aplicações", "it": "Applicazioni", "en": "Applications"}},
    ]

    home = {
        "pt": {
            "p1": "A BetterAI é um back-end de IA modular, escrito em Python, que coloca OpenAI, Anthropic, Google Gemini e Groq atrás da mesma interface. Sobre essa base roda a Web Service Network, a API FastAPI que expõe os serviços em produção.",
            "p2": "A plataforma faz hoje o seguinte:",
            "li": [
                "<strong>Parsing de documentos:</strong> converte <code>txt</code>, <code>md</code>, <code>pdf</code> e <code>docx</code> em dados estruturados, conforme o schema de quem chama.",
                "<strong>Deep research:</strong> busca web profunda via Tavily, devolvida como contexto em markdown.",
                "<strong>Base vetorial:</strong> ingestão, busca semântica e exclusão no Pinecone.",
                "<strong>Embeddings locais:</strong> chunking e recuperação em FAISS na memória.",
                "<strong>Geração de imagens:</strong> o serviço Da-Vinci gera e edita imagens a partir de texto e de referências visuais."],
            "startH": "Comece por aqui",
            "quick": {"id": "getting-started/quickstart", "icon": "bolt",
                      "text": "Do clone ao primeiro GET /health, em seis passos."},
            "tip": "Com a API no ar, a documentação interativa dos endpoints fica em <code>http://localhost:8000/docs</code>.",
            "exploreH": "Explore por área",
            "popular": [
                {"id": "modules/agents/utils/model-gateway", "icon": "boxes",
                 "text": "Modelos e agentes de qualquer provedor pela mesma chamada."},
                {"id": "modules/web-service-network/web-service-network-api", "icon": "code",
                 "text": "Autenticação, formato das respostas e endpoints."}],
        },
        "it": {
            "p1": "BetterAI è un back-end di IA modulare, scritto in Python, che mette OpenAI, Anthropic, Google Gemini e Groq dietro la stessa interfaccia. Su questa base gira la Web Service Network, l’API FastAPI che espone i servizi in produzione.",
            "p2": "Oggi la piattaforma fa quanto segue:",
            "li": [
                "<strong>Parsing di documenti:</strong> converte file <code>txt</code>, <code>md</code>, <code>pdf</code> e <code>docx</code> in dati strutturati, secondo lo schema di chi chiama.",
                "<strong>Deep research:</strong> ricerca web approfondita tramite Tavily, restituita come contesto in markdown.",
                "<strong>Base vettoriale:</strong> ingestione, ricerca semantica ed eliminazione su Pinecone.",
                "<strong>Embedding locali:</strong> chunking e recupero in memoria con FAISS.",
                "<strong>Generazione di immagini:</strong> il servizio Da-Vinci genera e modifica immagini a partire da testo e riferimenti visivi."],
            "startH": "Parti da qui",
            "quick": {"id": "getting-started/quickstart", "icon": "bolt",
                      "text": "Dal clone al primo GET /health, in sei passi."},
            "tip": "Con l’API attiva, la documentazione interattiva degli endpoint si trova su <code>http://localhost:8000/docs</code>.",
            "exploreH": "Esplora per area",
            "popular": [
                {"id": "modules/agents/utils/model-gateway", "icon": "boxes",
                 "text": "Modelli e agenti di qualsiasi provider con la stessa chiamata."},
                {"id": "modules/web-service-network/web-service-network-api", "icon": "code",
                 "text": "Autenticazione, formato delle risposte ed endpoint."}],
        },
        "en": {
            "p1": "BetterAI is a modular AI back end written in Python that puts OpenAI, Anthropic, Google Gemini and Groq behind the same interface. On top of it runs the Web Service Network, the FastAPI service that exposes the platform in production.",
            "p2": "Today the platform does the following:",
            "li": [
                "<strong>Document parsing:</strong> turns <code>txt</code>, <code>md</code>, <code>pdf</code> and <code>docx</code> files into structured data, following the caller’s schema.",
                "<strong>Deep research:</strong> deep web search through Tavily, returned as markdown context.",
                "<strong>Vector store:</strong> ingestion, semantic search and deletion on Pinecone.",
                "<strong>Local embeddings:</strong> in-memory chunking and retrieval with FAISS.",
                "<strong>Image generation:</strong> the Da-Vinci service generates and edits images from text and visual references."],
            "startH": "Start here",
            "quick": {"id": "getting-started/quickstart", "icon": "bolt",
                      "text": "From clone to your first GET /health, in six steps."},
            "tip": "With the API running, the interactive endpoint docs are at <code>http://localhost:8000/docs</code>.",
            "exploreH": "Explore by area",
            "popular": [
                {"id": "modules/agents/utils/model-gateway", "icon": "boxes",
                 "text": "Models and agents from any provider through the same call."},
                {"id": "modules/web-service-network/web-service-network-api", "icon": "code",
                 "text": "Authentication, response format and endpoints."}],
        },
    }

    return {
        "site": {"name": "BetterAI Docs", "brand": "BetterAI", "brandSub": "Docs",
                 "tagline": "Where intelligence finds purpose.", "baseUrl": ""},
        "links": {"github": "#", "swagger": "#", "repo": ""},
        "footer": {
            "resources": [{"label": "Swagger UI", "url": "#"},
                          {"label": "GitHub", "url": "#"}],
            "platform": ["modules/web-service-network/web-service-network-api",
                         "streamlit-applications/acquarello",
                         "streamlit-applications/content-generator"],
        },
        "areas": areas,
        "ui": ui,
        "home": home,
    }


def load_config(repo: Path, report: list) -> dict:
    path = repo / WEB_DIR_NAME / "_build" / "site.config.json"
    if not path.exists():
        write(path, json.dumps(default_config(), ensure_ascii=False, indent=2) + "\n")
        report.append("%-9s %s" % ("seeded", "_build/site.config.json"))
    cfg = json.loads(path.read_text(encoding="utf-8"))
    base = default_config()
    for key, value in base.items():                     # forward-compatible defaults
        if key not in cfg:
            cfg[key] = value
        elif isinstance(value, dict):
            for k2, v2 in value.items():
                cfg[key].setdefault(k2, v2)
                if isinstance(v2, dict) and isinstance(cfg[key][k2], dict):
                    for k3, v3 in v2.items():
                        cfg[key][k2].setdefault(k3, v3)
    return cfg


def retire_prototype(repo: Path, report: list):
    index = repo / WEB_DIR_NAME / "index.html"
    target = repo / WEB_DIR_NAME / "_prototype.html"
    if not index.exists():
        return
    text = index.read_text(encoding="utf-8", errors="replace")
    if "data-page=" not in text:            # already the generated dispatcher
        return
    if target.exists():
        report.append("%-9s %s" % ("skip", "_prototype.html already exists"))
        return
    shutil.move(str(index), str(target))
    report.append("%-9s %s" % ("moved", "index.html -> _prototype.html"))


# --------------------------------------------------------------------------- #
# cli                                                                         #
# --------------------------------------------------------------------------- #

def find_repo(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / SRC_DIR_NAME).is_dir() and (candidate / WEB_DIR_NAME).is_dir():
            return candidate
    raise SystemExit("could not locate the repo root (need %s/ and %s/)"
                     % (SRC_DIR_NAME, WEB_DIR_NAME))


def page_id_for(repo: Path, raw: str) -> str:
    path = Path(raw)
    if not path.is_absolute():
        path = (repo / raw) if (repo / raw).exists() else Path(raw).resolve()
    rel = path.resolve().relative_to((repo / SRC_DIR_NAME).resolve())
    parts = [title_of(p) for p in rel.parts[:-1]]
    return "/".join(slug(p) for p in parts + [title_of(rel.stem)])


def cmd_list(repo: Path, folder: str | None):
    src = repo / SRC_DIR_NAME / (folder or "")
    content_dir = repo / WEB_DIR_NAME / "_content"
    rows = []
    for path in sorted(src.rglob("*")):
        if (path.is_dir() or path.suffix not in SOURCE_EXTS
                or path.name in IGNORE_FILES
                or any(part in IGNORE_DIRS for part in path.parts)):
            continue
        pid = page_id_for(repo, str(path))
        have = [l for l in LANGS if content_path(content_dir, pid, l).exists()]
        state = ("blank-source" if source_is_empty(path)
                 else "done" if len(have) == len(LANGS)
                 else "partial(%s)" % ",".join(have) if have else "TODO")
        rows.append((state, pid, path.relative_to(repo).as_posix()))
    width = max((len(r[0]) for r in rows), default=4)
    for state, pid, rel in rows:
        print("%-*s  %-55s %s" % (width, state, pid, rel))
    todo = [r for r in rows if r[0] == "TODO"]
    print("\n%d source files, %d still to do" % (len(rows), len(todo)))
    if todo:
        print("next: %s" % todo[0][2])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="repo root (default: inferred from this script)")
    ap.add_argument("--check", action="store_true",
                    help="build into a temp dir and report drift against pages/")
    ap.add_argument("--page-id", metavar="SRC", help="print the page id for a source file")
    ap.add_argument("--list", nargs="?", const="", metavar="FOLDER",
                    help="list source files and whether they have content")
    ap.add_argument("--quiet", action="store_true", help="only print the summary")
    args = ap.parse_args(argv)

    repo = Path(args.root).resolve() if args.root else find_repo(Path(__file__).resolve())

    if args.page_id:
        print(page_id_for(repo, args.page_id))
        return 0
    if args.list is not None:
        cmd_list(repo, args.list or None)
        return 0

    report = []
    cfg = load_config(repo, report)
    web = repo / WEB_DIR_NAME

    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            counts, errors, pages, areas = build(repo, out, cfg, report)
            drift = []
            for path in sorted(out.rglob("*")):
                if path.is_dir():
                    continue
                rel = path.relative_to(out)
                live = web / rel
                if not live.exists():
                    drift.append("missing in pages/: %s" % rel.as_posix())
                elif live.read_bytes() != path.read_bytes():
                    drift.append("differs: %s" % rel.as_posix())
            for line in drift[:40]:
                print("DRIFT   %s" % line)
            print("\ncheck: %d files, %d drifted, errors: %d"
                  % (sum(1 for p in out.rglob("*") if p.is_file()), len(drift),
                     len(errors)))
            for err in errors:
                print("ERROR   %s" % err)
            return 1 if (drift or errors) else 0

    retire_prototype(repo, report)
    counts, errors, pages, areas = build(repo, web, cfg, report)

    if not args.quiet:
        for line in report:
            print(line)
    print("\n%d pages x %d languages | content: %d  fallback: %d  empty: %d  generated: %d"
          % (len(pages), len(LANGS), counts.get("content", 0), counts.get("fallback", 0),
             counts.get("empty", 0), counts.get("generated", 0)))
    print("errors: %d" % len(errors))
    for err in errors:
        print("ERROR   %s" % err)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
