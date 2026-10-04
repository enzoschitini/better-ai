"""sitemap.xml, robots.txt, 404 e o redirect da raiz."""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from .model import Page
from .settings import Settings
from .slugs import esc
from .strings import HTML_LANG, tr


def sitemap(pages: list[Page], st: Settings, dist: Path) -> int:
    """Uma <url> por página indexável, com alternates das traduções reais."""
    rows = []
    for p in pages:
        if p.noindex:
            continue
        rows.append("  <url>")
        rows.append(f"    <loc>{escape(st.site_url + p.url)}</loc>")
        for l in sorted(p.translations):
            if l in p.alt:
                rows.append(
                    f'    <xhtml:link rel="alternate" hreflang="{l}" '
                    f'href="{escape(st.site_url + p.alt[l])}"/>'
                )
        if "pt" in p.alt:
            rows.append(
                f'    <xhtml:link rel="alternate" hreflang="x-default" '
                f'href="{escape(st.site_url + p.alt["pt"])}"/>'
            )
        rows.append("  </url>")

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(rows) + "\n</urlset>\n"
    )
    (dist / "sitemap.xml").write_text(xml, encoding="utf-8")
    return len([p for p in pages if not p.noindex])


def robots(st: Settings, dist: Path) -> None:
    txt = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /_design-system/\n"
        f"\nSitemap: {st.site_url}/sitemap.xml\n"
    )
    (dist / "robots.txt").write_text(txt, encoding="utf-8")


def root_redirect(st: Settings, dist: Path, langs: list[str], default: str) -> None:
    """Num host estático puro não há 302, então o redirect é no cliente.

    Guarda: noindex, canonical para o idioma padrão, sniff de
    navigator.languages, <meta refresh> de reserva e links visíveis para quem
    não tem JavaScript.
    """
    links = "\n".join(
        f'    <li><a href="{st.base}/{l}/">{HTML_LANG.get(l, l)}</a></li>' for l in langs
    )
    html = f"""<!doctype html>
<html lang="{HTML_LANG.get(default, default)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{st.site_url}{st.base}/{default}/">
<title>BetterAI Docs</title>
<script>
  (function () {{
    var langs = {langs!r};
    var pick = null;
    try {{ pick = localStorage.getItem('betterai-docs-lang'); }} catch (e) {{}}
    if (langs.indexOf(pick) < 0) {{
      var prefs = navigator.languages || [navigator.language || ''];
      for (var i = 0; i < prefs.length && !pick; i++) {{
        var two = String(prefs[i]).slice(0, 2).toLowerCase();
        if (langs.indexOf(two) >= 0) pick = two;
      }}
    }}
    location.replace('{st.base}/' + (pick || '{default}') + '/');
  }})();
</script>
<meta http-equiv="refresh" content="0;url={st.base}/{default}/">
</head>
<body>
  <p>{esc(tr(default, 'redirect'))}</p>
  <ul>
{links}
  </ul>
</body>
</html>
""".replace("'", "'")
    (dist / "index.html").write_text(html, encoding="utf-8")

