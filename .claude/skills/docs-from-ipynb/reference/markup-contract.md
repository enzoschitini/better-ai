# Markup contract

What you may write in a `_content/<page-id>.<lang>.html` file, and what the build turns it
into. The build validates against this list and fails on anything else — it is an
allowlist, not a suggestion.

Everything lives inside one root element:

    <page data-lead="One sentence. Plain text, no markup.">
      ...
    </page>

`data-lead` is the page's standfirst, rendered as `.lead` under the title. It comes from
the source's opening paragraph. The page's `<h1>` is rendered by the build from the
documentation tree — never write one.

## Headings

| You write | Why |
|---|---|
| `<h2>Section</h2>` | The source's `###` level. Appears in "Nesta página". |
| `<h3>Subsection</h3>` | The source's `####` level. Also in the TOC. |

The build adds the `id` and the `#` anchor link. Do not write either — deep links and the
search index depend on the build owning them, and `ds.js` would add a second anchor.

## Prose

`<p>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<em>`, `<code>`, `<br>`, `<a>`.

Inline code is `<code>`. A `<code>` inside a `<p>`, `<li>`, `<td>` or heading is styled as
inline code; the build never highlights it.

### Links

| Target | You write |
|---|---|
| Another documentation page | `<a href="@/getting-started/quickstart">Quickstart</a>` |
| A heading on another page | `<a href="@/modules/agents/utils/model-gateway#metodos">` |
| A heading on this page | `<a href="#metodos">` |
| Anything external | `<a href="https://...">` — written in full |

`@/` takes a page id, the same id as the `_content` file name with `--` back to `/`. The
build rewrites it to a relative URL **in the current language**, so a `pt` page links to
`pt` pages. Writing `#/...` (the old prototype's hash routing) is rejected: the static
site has real URLs.

An asset is `@assets/img/diagram.png`, rewritten the same way.

## Code

A single block:

    <pre data-lang="bash"><code>
    uv sync
    </code></pre>

`data-lang` picks the highlighter: `python`, `bash`, `json`, `env`. Any other value, or
none, renders unhighlighted — which is correct for output dumps, directory trees and logs.
One leading newline after `<code>` is stripped, so the first line can start at column 0.

With a file name in the header:

    <pre data-lang="env" data-title=".env"><code>
    BETTERAI_API_KEY=********************
    </code></pre>

Alternatives of the same command — one tab each, first one visible:

    <codetabs>
      <tab title="PowerShell"><pre data-lang="bash"><code>
    .\.venv\Scripts\Activate.ps1
    </code></pre></tab>
      <tab title="CMD"><pre data-lang="bash"><code>
    .venv\Scripts\activate.bat
    </code></pre></tab>
    </codetabs>

Use `<codetabs>` only for genuine alternatives — one OS or one tool instead of another.
Sequential steps are separate blocks.

Code stays in English in all three language files; only its comments are translated (see
`translation.md`, "Code blocks"). Every `<pre>` must exist in `pt`, `it` and `en`.

The content of a `<pre>` is HTML-escaped text: write `&lt;`, `&gt;` and `&amp;` escaped.
The build unescapes it, highlights it, and re-escapes it.

## Tables

Plain HTML. The build wraps them in `.table-wrap` for horizontal scrolling.

    <table>
      <thead><tr><th>Variável</th><th>Descrição</th></tr></thead>
      <tbody>
        <tr><td><code>BETTERAI_API_KEY</code></td><td>Chave interna</td></tr>
      </tbody>
    </table>

A markdown table in the source becomes exactly this, cell for cell. Keep the header row.

## Callouts

A markdown blockquote (`>`) in the source becomes a callout. Pick the kind by what the
source actually says — do not promote a neutral aside into a warning.

    <div class="callout" data-kind="warn"><p><strong>Só em desenvolvimento.</strong>
    <code>LOCAL=true</code> desliga a autenticação.</p></div>

| `data-kind` | For |
|---|---|
| `note` | An aside. The neutral default. |
| `info` | A prerequisite or a useful fact. |
| `tip` | A recommendation, a shortcut. |
| `warn` | Something that bites: a footgun, a non-obvious constraint. |
| `danger` | Data loss, a security hole, production breakage. |

The icon is inserted by `ds.js`. Do not write one. Keep the text in `<p>`; a callout may
hold several `<p>` or a short list.

## Collapsed detail

For a long dump that would drown the page — a full `.env`, a complete response payload.

    <details>
      <summary>Ver o modelo completo do .env</summary>
      <pre data-lang="env" data-title=".env"><code>
    ...
    </code></pre>
    </details>

## HTTP endpoint

    <endpoint method="POST" path="/v1/document-parse"></endpoint>

`method` is any HTTP verb; `GET` gets its own colour. Use it when the source documents a
route, in addition to — not instead of — the prose that explains it.

## Cards

A grid of links. Appropriate when the source ends with a list of "see also" pages; not a
substitute for prose.

    <cards>
      <card href="@/getting-started/quickstart" icon="bolt" title="Quickstart">Do clone ao
    primeiro request.</card>
      <card href="@/modules/pinecone-vector-store/pinecone-client" icon="boxes"
    title="Pinecone Client">Ingestão e busca semântica.</card>
    </cards>

`<cards one>` makes it a single full-width column. `icon` is one of: `bolt`, `boxes`,
`code`, `layout`, `folder`, `note`, `blank`, `info`, `tip`, `warn`, `danger`, `go`, `edit`,
`list`, `search`, `globe`, `copy`, `check`, `chevron`, `down`, `up`, `dn`, `menu`, `close`,
`sun`, `moon`. Anything else fails the build.

## Media

    <media src="@assets/video/acquarello.mp4" caption="O fluxo completo no Acquarello."></media>

`.mp4`, `.webm` and `.mov` render as a `<video controls>`; anything else as an `<img>`.
`caption` is optional. A missing file degrades to the design system's placeholder frame
instead of a broken element.

## Rejected

The build fails, by design, on: `<h1>`, `<div>` with any class other than `callout`,
`<script>`, `<style>`, inline `style=`, `<blockquote>`, `<img>` or `<video>` written
directly, `class=` on prose elements, `href="#/..."`, `id=` on headings, `<table>` without
`<thead>`, and any tag not named above.

If you need something the contract does not cover, say so in your report rather than
inventing markup — the design system may already have the component under a name you did
not find, or it genuinely needs adding.

## Worked example

Source — `ipynb_contents/Getting Started/1. Quickstart.ipynb`, first three markdown cells:

    # Quickstart - Guia de Inicialização

    Guia rápido para configurar o ambiente, instalar dependências e executar os
    serviços do BetterAI pela primeira vez.

    ### **1. Atualize o Projeto**

    Primeiro, certifique-se de estar na branch correta e de que o seu código está
    atualizado:

    ~~~
    git checkout production
    git pull
    ~~~

    ---

    ### **2. Crie o Ambiente Virtual**

    > **Requisito:** Python 3.14 ou superior (versão fixada em `.python-version`).

    Crie um ambiente virtual para isolar as dependências do projeto:

    ~~~
    python -m venv .venv
    ~~~

Result — `_content/getting-started--quickstart.pt.html`:

    <page data-lead="Guia rápido para configurar o ambiente, instalar dependências e executar os serviços do BetterAI pela primeira vez.">
      <h2>1. Atualize o Projeto</h2>
      <p>Primeiro, certifique-se de estar na branch correta e de que o seu código está atualizado:</p>
      <pre data-lang="bash"><code>
    git checkout production
    git pull
    </code></pre>

      <h2>2. Crie o Ambiente Virtual</h2>
      <div class="callout" data-kind="info"><p><strong>Requisito:</strong> Python 3.14 ou superior (versão fixada em <code>.python-version</code>).</p></div>
      <p>Crie um ambiente virtual para isolar as dependências do projeto:</p>
      <pre data-lang="bash"><code>
    python -m venv .venv
    </code></pre>
    </page>

Note what did **not** happen: the `---` separators vanished (they were visual padding
between markdown sections, and `<h2>` already separates), the bold-inside-heading markup
dropped to plain text, the untagged code fence was identified as `bash`, and the blockquote
became an `info` callout. Note what also did not happen: not one word of the prose changed.
