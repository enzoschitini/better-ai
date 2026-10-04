"""Realce de sintaxe no build. Porte do tokenizador `RULES` do protótipo.

Faz no build porque: zero JS e zero CPU no cliente, código realçado antes de
qualquer script rodar, e as classes `.t-k/.t-s/.t-n/.t-f/.t-c` já estão
estilizadas em theme/css/content.css.

Cobre python, bash, json e env — 99,6% das cercas de código do acervo.

Dois detalhes do porte que mordem se esquecidos:
  - `re.ASCII` é obrigatório: `\\w` em Python é Unicode-aware e engoliria
    acentos nos grupos de nome de função, que em JS são ASCII.
  - os lookbehinds `(?<=\\s)` do bash são de largura fixa, então o `re` do
    Python os aceita como estão.
"""

from __future__ import annotations

import re

from .slugs import esc

_STR = r"\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'"

_PY_KW = (
    "def|class|return|import|from|as|if|elif|else|for|while|try|except|finally|"
    "with|lambda|yield|raise|assert|global|nonlocal|pass|break|continue|del|"
    "in|is|not|and|or|None|True|False|self|async|await|match|case"
)

RULES: dict[str, tuple[re.Pattern, list[str]]] = {
    "python": (
        re.compile(
            rf"(#.*$)|({_STR})|\b({_PY_KW})\b|\b(\d+\.?\d*)\b|([A-Za-z_]\w*)(?=\()",
            re.M | re.ASCII,
        ),
        ["c", "s", "k", "n", "f"],
    ),
    "bash": (
        re.compile(
            rf"((?:^|(?<=\s))#.*$)|({_STR})|((?<=\s)--?[A-Za-z][\w-]*)|"
            r"^\s*([a-z][\w.-]*)",
            re.M | re.ASCII,
        ),
        ["c", "s", "n", "f"],
    ),
    "json": (
        re.compile(
            r"(\"(?:\\.|[^\"\\])*\")(?=\s*:)|(\"(?:\\.|[^\"\\])*\")|"
            r"\b(true|false|null)\b|(-?\d+\.?\d*(?:[eE][+-]?\d+)?)",
            re.ASCII,
        ),
        ["f", "s", "k", "n"],
    ),
    "env": (re.compile(r"(#.*$)|(^[A-Z_]+)(?==)", re.M | re.ASCII), ["c", "f"]),
}

ALIASES = {
    "py": "python", "python3": "python",
    "sh": "bash", "shell": "bash", "zsh": "bash", "console": "bash",
    "dotenv": "env",
}


def highlight(code: str, lang: str | None) -> str:
    """Devolve HTML escapado, com os trechos marcados em <span class="t-*">.

    Sem linguagem ou linguagem desconhecida: só escapa.
    """
    if not lang:
        return esc(code)
    key = ALIASES.get(lang.lower(), lang.lower())
    rule = RULES.get(key)
    if rule is None:
        return esc(code)

    pattern, classes = rule
    out: list[str] = []
    pos = 0
    for m in pattern.finditer(code):
        # qual grupo casou define a classe
        idx = next((i for i, g in enumerate(m.groups(), 1) if g is not None), None)
        if idx is None:
            continue
        out.append(esc(code[pos:m.start(idx)]))
        out.append(f'<span class="t-{classes[idx - 1]}">{esc(m.group(idx))}</span>')
        pos = m.end(idx)
    out.append(esc(code[pos:]))
    return "".join(out)


_PRE = re.compile(
    r'<pre(?P<attrs>[^>]*)><code(?P<cattrs>[^>]*)>(?P<code>.*?)</code></pre>',
    re.S,
)
_LANG = re.compile(r'data-lang="([^"]+)"')
_ENTITIES = (("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'"), ("&amp;", "&"))


def apply_to_html(html: str) -> str:
    """Realça todo <pre data-lang="x"><code> de um fragmento já renderizado."""

    def repl(m: re.Match) -> str:
        attrs, cattrs, code = m.group("attrs"), m.group("cattrs"), m.group("code")
        lm = _LANG.search(attrs) or _LANG.search(cattrs)
        if not lm:
            return m.group(0)
        raw = code
        for ent, ch in _ENTITIES:
            raw = raw.replace(ent, ch)
        return f"<pre{attrs}><code{cattrs}>{highlight(raw, lm.group(1))}</code></pre>"

    return _PRE.sub(repl, html)
