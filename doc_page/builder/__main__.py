"""CLI do gerador.

    uv run python -m doc_page.builder build
    uv run python -m doc_page.builder check
    uv run python -m doc_page.builder serve

Stdlib only. Nada entra no pyproject.toml por causa do build.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from doc_page import manifest  # noqa: E402
from doc_page.builder import assets, render, searchindex, seo, settings  # noqa: E402
from doc_page.builder.tree import ManifestError, build_pages  # noqa: E402


def cmd_build(args) -> int:
    st = settings.load(ROOT / "doc_page", args.base)
    langs = args.langs.split(",") if args.langs else manifest.LANGS
    default = manifest.DEFAULT_LANG

    print(f"doc_page build · idiomas: {', '.join(langs)} · base: {st.base or '/'}")

    pages, areas = build_pages(
        manifest, st.content, st.theme / "js" / "ds.js", langs, default, st.base
    )
    by_id = {(p.lang, p.id): p for p in pages}
    print(f"  {len(pages)} páginas ({len(pages) // len(langs)} por idioma)")

    dist = st.dist
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)

    layout = (st.theme / "layout.html").read_text(encoding="utf-8")
    css_href = assets.build_css(st, dist)
    js_href = assets.build_js(st, dist)
    print(f"  css: {css_href.rsplit('/', 1)[-1]}   js: {js_href.rsplit('/', 1)[-1]}")

    # passada 1: corpo de cada página (o índice de busca depende dele)
    prose: dict[tuple[str, str], tuple[str, str, str, str]] = {}
    for p in pages:
        prose[(p.lang, p.id)] = render.build_prose(p, st, areas, by_id)

    # índice de busca, por idioma
    index_href: dict[str, str] = {}
    for lang in langs:
        rendered = {pid: prose[(l, pid)][0] for (l, pid) in prose if l == lang}
        idx = searchindex.build(pages, lang, manifest.POPULAR, rendered)
        index_href[lang] = searchindex.write(idx, dist, lang, st.base)
        print(f"  busca {lang}: {len(idx['p'])} páginas, {len(idx['s'])} seções, "
              f"{len(Path(dist / lang / index_href[lang].rsplit('/', 1)[-1]).read_bytes()) // 1024} KB")

    # passada 2: páginas completas
    written: list[Path] = []
    for p in pages:
        body, title, lead, eyebrow = prose[(p.lang, p.id)]
        html = render.render(
            p, st, areas, by_id, layout, css_href, js_href,
            index_href[p.lang], body, title, lead, eyebrow,
        )
        out = dist / p.out_path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        written.append(out)
    print(f"  {len(written)} arquivos HTML")

    # catálogo do design system, servido mas fora do índice
    cat_src = st.theme / "catalog"
    cat_dst = dist / "_design-system"
    cat_dst.mkdir(parents=True, exist_ok=True)
    cat_html = (cat_src / "index.html").read_text(encoding="utf-8")
    cat_html = cat_html.replace(
        "<head>", '<head>\n<meta name="robots" content="noindex, nofollow">', 1
    )
    cat_html = cat_html.replace('href="../css/', 'href="css/').replace(
        'src="../js/', 'src="js/'
    ).replace('src="../../assets/', f'src="{st.base}/assets/')
    (cat_dst / "index.html").write_text(cat_html, encoding="utf-8")
    shutil.copytree(st.theme / "css", cat_dst / "css", dirs_exist_ok=True)
    shutil.copytree(st.theme / "js", cat_dst / "js", dirs_exist_ok=True)

    # SEO
    n = seo.sitemap(pages, st, dist)
    seo.robots(st, dist)
    seo.root_redirect(st, dist, langs, default)
    print(f"  sitemap: {n} URLs indexáveis ({len(pages) - n} noindex)")

    # 404 com chrome completo, reusando o layout
    home = by_id[(default, "home")]
    from doc_page.builder.strings import tr as _tr
    b = (f'<p>{_tr(default, "notFoundText")}</p>\n<div class="cards">\n'
         + "\n".join(
             f'  <a class="card" href="{st.base}/{default}/{a.slug}/">'
             f'<span class="card-icon" data-ico="{a.icon}"></span>'
             f'<span class="card-title">{a.title(default)}</span></a>'
             for a in areas) + "\n</div>")
    html404 = render.render(
        home, st, areas, by_id, layout, css_href, js_href, index_href[default],
        b, _tr(default, "notFound"), "", _tr(default, "notFound"),
    ).replace("<head>", '<head>\n<meta name="robots" content="noindex, nofollow">', 1)
    (dist / "404.html").write_text(html404, encoding="utf-8")

    # assets referenciados — o catálogo entra na varredura, senão as imagens
    # que só ele usa não são copiadas e o link quebra
    copied, missing = assets.copy_referenced(
        st, dist, written + [dist / "404.html", cat_dst / "index.html"]
    )
    print(f"  assets: {copied} copiados")
    if missing:
        print("  AVISO, referenciados mas inexistentes em assets/:")
        for m in missing:
            print(f"    - {m}")

    # structure.json por idioma, para quem quiser a árvore como dado
    import json
    for lang in langs:
        rows = [{"id": p.id, "kind": p.kind, "url": p.url, "title": p.title,
                 "nav": p.nav_label, "empty": p.empty, "mirror": p.is_mirror,
                 "crumbs": p.crumbs} for p in pages if p.lang == lang]
        (dist / lang / "structure.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\nok · {dist}")
    return 0


def cmd_check(args) -> int:
    from doc_page.builder import check
    st = settings.load(ROOT / "doc_page", args.base)
    return check.run(st, manifest, args.langs.split(",") if args.langs else manifest.LANGS)


def cmd_serve(args) -> int:
    import functools
    import http.server
    import socketserver

    st = settings.load(ROOT / "doc_page", args.base)
    dist = st.dist
    if not dist.is_dir():
        print("dist/ não existe. Rode o build primeiro.")
        return 1

    class H(http.server.SimpleHTTPRequestHandler):
        """Mapeia /x/ → /x/index.html, para URL sem barra final se comportar
        como vai se comportar em produção."""

        def translate_path(self, path):
            p = super().translate_path(path)
            if Path(p).is_dir():
                idx = Path(p) / "index.html"
                if idx.is_file():
                    return str(idx)
            if not Path(p).exists() and not path.endswith("/"):
                alt = Path(p + "/index.html")
                if alt.is_file():
                    return str(alt)
            return p

        def log_message(self, *a):
            pass

    handler = functools.partial(H, directory=str(dist))
    with socketserver.TCPServer(("", args.port), handler) as srv:
        print(f"servindo {dist} em http://localhost:{args.port}/  (Ctrl C para parar)")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print()
    return 0


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="doc_page.builder")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name, fn in (("build", cmd_build), ("check", cmd_check), ("serve", cmd_serve)):
        p = sub.add_parser(name)
        p.add_argument("--langs", default=None, help="ex: pt ou pt,en,it")
        p.add_argument("--base", default=None, help="prefixo de caminho")
        if name == "serve":
            p.add_argument("--port", type=int, default=8080)
        p.set_defaults(fn=fn)

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except ManifestError as e:
        print(f"\nERRO · {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
