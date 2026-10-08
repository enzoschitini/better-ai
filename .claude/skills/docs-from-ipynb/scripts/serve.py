#!/usr/bin/env python3
"""Servidor de preview da documentacao, sem cache.

`python -m http.server` manda Last-Modified mas nao manda Cache-Control. Sem essa
diretiva o navegador aplica cache heuristico: guarda a pagina por uma fracao da
idade do arquivo e, nesse intervalo, nem pergunta ao servidor. O resultado e uma
pagina antiga na tela depois de um rebuild, so nas rotas que ja tinham sido
abertas antes. Aqui toda resposta sai com no-store, entao o que aparece no
navegador e sempre o que esta em disco.

Uso:
    python .claude/skills/docs-from-ipynb/scripts/serve.py
    python .claude/skills/docs-from-ipynb/scripts/serve.py --port 8765
"""

from __future__ import annotations

import argparse
import functools
import http.server
import socketserver
import sys
from pathlib import Path

WEB_DIR_NAME = "web_documentation"


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / WEB_DIR_NAME).is_dir():
            return candidate
    return Path.cwd()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--root", help="pasta servida (padrao: a raiz do repo)")
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve() if args.root else find_root(Path(__file__).resolve())
    if not (root / WEB_DIR_NAME).is_dir():
        print("nao achei %s/ em %s" % (WEB_DIR_NAME, root), file=sys.stderr)
        return 1

    handler = functools.partial(NoCacheHandler, directory=str(root))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((args.host, args.port), handler) as httpd:
        print("servindo %s" % root)
        print("http://%s:%d/%s/index.html" % (args.host, args.port, WEB_DIR_NAME))
        print("sem cache: toda resposta sai com no-store. Ctrl+C para parar.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nparado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
