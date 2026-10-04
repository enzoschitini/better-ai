"""Cria um fragmento vazio para cada página do manifest que ainda não tem um.

Uso único por idioma, para levantar a base do site com todas as páginas
contempladas antes de existir conteúdo. Idempotente: nunca sobrescreve um
fragmento existente.

    python -m doc_page.tools.make_stubs pt
    python -m doc_page.tools.make_stubs pt --force   # reescreve os stubs

As páginas marcadas empty=True no manifest são puladas de propósito: elas não
têm fragmento nenhum, e o build renderiza o bloco `.empty`.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from doc_page import manifest  # noqa: E402
from doc_page.builder.slugs import esc, slug  # noqa: E402

CONTENT = ROOT / "doc_page" / "content"

STUB = """<article
  data-title="{title}"
  data-lead="">
  <div class="callout" data-kind="note">
    <p>Esta página ainda não tem conteúdo. O texto entra aqui, dentro do
      <code>&lt;article&gt;</code>, usando os componentes do design system.</p>
  </div>
</article>
"""

HOME = """<article
  data-title="Documentação da BetterAI"
  data-lead="Múltiplos modelos de IA, um único back-end unificado.">
  <div class="callout" data-kind="note">
    <p>A home ainda não tem conteúdo. O corpo entra aqui.</p>
  </div>
</article>
"""


def leaves():
    """(slug_path, nome, empty) para cada folha do manifest."""
    out = []

    def walk(kids, path):
        for k in kids:
            s = k.get("slug") or slug(k["t"])
            p = path + [s]
            if "kids" in k:
                walk(k["kids"], p)
            else:
                out.append(("/".join(p), k["t"], bool(k.get("empty"))))

    for a in manifest.AREAS:
        walk(a["kids"], [a.get("slug") or slug(a["t"])])
    return out


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    lang = argv[0] if argv else manifest.DEFAULT_LANG
    force = "--force" in argv
    if lang not in manifest.LANGS:
        print(f"idioma {lang!r} não está em manifest.LANGS ({manifest.LANGS})")
        return 2

    root = CONTENT / lang
    made = skipped = 0

    home = root / "index.html"
    if force or not home.exists():
        home.parent.mkdir(parents=True, exist_ok=True)
        home.write_text(HOME, encoding="utf-8")
        made += 1
    else:
        skipped += 1

    for sp, name, is_empty in leaves():
        if is_empty:
            continue
        f = root / f"{sp}.html"
        if f.exists() and not force:
            skipped += 1
            continue
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(STUB.format(title=esc(name)), encoding="utf-8")
        made += 1

    total = sum(1 for _, _, e in leaves() if not e)
    print(f"{lang}: {made} criados, {skipped} já existiam")
    print(f"     {total} folhas com conteúdo + 1 home; "
          f"{sum(1 for _, _, e in leaves() if e)} marcadas empty=True (sem fragmento)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
