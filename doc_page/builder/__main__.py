"""CLI do gerador.

    uv run python -m doc_page.builder build
    uv run python -m doc_page.builder check
    uv run python -m doc_page.builder serve

Stdlib only. Nada entra no pyproject.toml por causa do build.
"""

from __future__ import annotations

import argparse
import re
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
    st = settings.load(ROOT / "doc_page")
    langs = args.langs.split(",") if args.langs else manifest.LANGS
    default = manifest.DEFAULT_LANG

    print(f"doc_page build · idiomas: {', '.join(langs)}")

    pages, areas = build_pages(
        manifest, st.content, st.theme / "js" / "ds.js", langs, default
    )
    by_id = {(p.lang, p.id): p for p in pages}
    print(f"  {len(pages)} páginas ({len(pages) // len(langs)} por idioma)")

    dist = st.dist
    # Limpa o conteúdo, não a pasta. No Windows, um preview rodando dentro do
    # dist/ mantém um handle no diretório, e remover a pasta falharia com
    # PermissionError no meio do build.
    dist.mkdir(parents=True, exist_ok=True)
    for item in dist.iterdir():
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
        else:
            try:
                item.unlink()
            except OSError:
                pass

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
        index_href[lang] = searchindex.write(idx, dist, lang)
        print(f"  busca {lang}: {len(idx['p'])} páginas, {len(idx['s'])} seções, "
              f"{len((dist / index_href[lang]).read_bytes()) // 1024} KB")

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
    # o catálogo fica em _design-system/, então assets sobe um nível só
    cat_html = cat_html.replace('href="../css/', 'href="css/').replace(
        'src="../js/', 'src="js/'
    ).replace('src="../../assets/', 'src="../assets/')
    (cat_dst / "index.html").write_text(cat_html, encoding="utf-8")
    shutil.copytree(st.theme / "css", cat_dst / "css", dirs_exist_ok=True)
    shutil.copytree(st.theme / "js", cat_dst / "js", dirs_exist_ok=True)

    # SEO
    n = seo.sitemap(pages, st, dist)
    seo.robots(st, dist)
    seo.nojekyll(dist)
    seo.root_redirect(st, dist, langs, default)
    print(f"  sitemap: {n} URLs indexáveis ({len(pages) - n} noindex)")

    # 404 com chrome completo, reusando o layout.
    # Precisa de uma Page própria: ele mora na RAIZ do dist, não dentro de
    # /pt/, então seu rel_root é vazio. Reusar o objeto da home daria
    # caminhos com "../" numa página que já está na raiz.
    import dataclasses

    from doc_page.builder.strings import tr as _tr

    home = by_id[(default, "home")]
    p404 = dataclasses.replace(home, id="404", path="", out_path="404.html")
    p404.alt = {}          # não há 404 por idioma; o seletor não deve chutar
    p404.prev = p404.next = None
    b = (f'<p>{_tr(default, "notFoundText")}</p>\n<div class="cards">\n'
         + "\n".join(
             f'  <a class="card" href="{default}/{a.slug}/">'
             f'<span class="card-icon" data-ico="{a.icon}"></span>'
             f'<span class="card-title">{a.title(default)}</span></a>'
             for a in areas) + "\n</div>")
    html404 = render.render(
        p404, st, areas, by_id, layout, css_href, js_href, index_href[default],
        b, _tr(default, "notFound"), "", _tr(default, "notFound"),
    ).replace("<head>", '<head>\n<meta name="robots" content="noindex, nofollow">', 1)
    # Uma página de erro não tem URL canônica: ela responde em qualquer
    # endereço que não existe. Declarar canonical aqui só criaria uma cadeia
    # para o redirect da raiz, que também é noindex.
    html404 = re.sub(r'<link rel="canonical"[^>]*>\n?', "", html404)
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
        rows = [{"id": p.id, "kind": p.kind, "path": p.path, "title": p.title,
                 "nav": p.nav_label, "empty": p.empty, "mirror": p.is_mirror,
                 "crumbs": p.crumbs} for p in pages if p.lang == lang]
        (dist / lang / "structure.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\nok · {dist}")
    return 0


def cmd_check(args) -> int:
    from doc_page.builder import check
    st = settings.load(ROOT / "doc_page")
    return check.run(st, manifest, args.langs.split(",") if args.langs else manifest.LANGS)


def cmd_serve(args) -> int:
    """Atalho para o http.server da stdlib.

    Como todos os caminhos internos do site são relativos, não existe nada a
    reescrever: o `http.server` serve o dist/ exatamente como o GitHub Pages
    vai servir. Este subcomando só poupa o `cd` e já amarra em 127.0.0.1.

    Equivalente:
        cd doc_page/dist && python -m http.server 8765 --bind 127.0.0.1
    """
    import http.server

    st = settings.load(ROOT / "doc_page")
    dist = st.dist
    if not dist.is_dir():
        print("dist/ não existe. Rode o build primeiro.")
        return 1

    import functools
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(dist)
    )
    # ThreadingHTTPServer em vez de TCPServer: ele já liga SO_REUSEADDR, então
    # reiniciar o preview não bate em "porta em uso" por causa do TIME_WAIT.
    # E 127.0.0.1, não 0.0.0.0: preview não precisa estar na rede local.
    with http.server.ThreadingHTTPServer((args.bind, args.port), handler) as srv:
        print(f"servindo {dist}")
        print(f"  http://{args.bind}:{args.port}/   (Ctrl C para parar)")
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
        if name == "serve":
            p.add_argument("--port", type=int, default=8765)
            p.add_argument("--bind", default="127.0.0.1")
        p.set_defaults(fn=fn)

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except ManifestError as e:
        print(f"\nERRO · {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
