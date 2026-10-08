# Translation

The sources are written in Portuguese. `pt` is a structural conversion of the source; `it`
and `en` are translations of that `pt` file. Three files, one structure.

## Invariant across the three files

The `it` and `en` files are the `pt` file with the prose swapped. Everything else is
identical, element for element:

- the same elements in the same order, the same nesting,
- the same number of `<h2>` and `<h3>`, in the same positions,
- the same `data-kind` on every callout, the same `data-lang` on every `<pre>`,
- the same `@/` link targets and the same `@assets/` paths,
- the same table shape: same columns, same number of rows, same order.

A reviewer should be able to diff the three files and see only prose changes. The build
does not enforce this, but a page whose `it` version has a heading the `pt` version lacks
is a bug — the TOC, the anchors and the search index diverge between languages.

## Never translated

| Kept verbatim | Example |
|---|---|
| Code, in every `<pre>` and every inline `<code>` (only the comments inside a `<pre>` are translated, see below) | `uv sync`, `python -m venv .venv` |
| Identifiers: classes, methods, parameters, fields | `TracingCore`, `run()`, `log_id` |
| Environment variable names | `BETTERAI_API_KEY`, `NOSQL_BACKEND` |
| File and directory names, paths | `.python-version`, `web_services.py` |
| Product, library and service names | FastAPI, Streamlit, Pinecone, Tavily, Supabase |
| HTTP methods, routes, status codes | `POST /v1/document-parse`, `401` |
| Values in a table's identifier column | the left column of an env-var table |

The *description* of an identifier is translated; the identifier is not. In a two-column
table of variables, the left column stays frozen and only the right column changes.

## Code blocks: code in English, comments in three languages

Every `<pre>` appears in all three files. The code itself stays identical (and in English:
identifiers, keywords, strings, commands, output). **Only the comments are translated**, so
the `pt`, `it` and `en` files each carry the comments in their own language:

- Python / bash / env: text after `#` (`# Cria o cliente` -> it `# Crea il client` -> en `# Create the client`).
- Python docstrings: translate the prose, keep the quotes and any `Args:`/`Returns:`-style
  names of parameters.
- JSON has no comments; leave it untouched.
- Comment-only lines and trailing comments both follow this rule; keep them on the same line
  and at the same column/indentation as in `pt`.
- If the source comment is already in English, the `pt` file keeps it as is (rule 1) and the
  `it`/`en` files still carry the comment in their language (`en` stays as the source).
- String literals, `print()` messages, log text and variable names are code, not comments:
  never translate them.
- Do not add comments the source does not have, and do not drop any.

A reviewer diffing the three files must see, inside every `<pre>`, only comment lines differ.

## Terms that have a settled translation

Use these; do not invent a synonym page by page.

| pt | it | en |
|---|---|---|
| ambiente virtual | ambiente virtuale | virtual environment |
| dependências | dipendenze | dependencies |
| variáveis de ambiente | variabili d'ambiente | environment variables |
| chave de API | chiave API | API key |
| banco de dados | database | database |
| busca semântica | ricerca semantica | semantic search |
| base vetorial | base vettoriale | vector store |
| fluxo de execução | flusso di esecuzione | execution flow |
| requisito | requisito | requirement |
| passo | passo | step |
| retorno | valore di ritorno | return value |
| tratamento de erros | gestione degli errori | error handling |
| registro (de log) | record | record |
| custo por token | costo per token | token cost |
| parsing de documentos | parsing di documenti | document parsing |
| geração de imagens | generazione di immagini | image generation |

## Register

The Portuguese sources address the reader directly in the imperative — "Crie um ambiente
virtual", "Certifique-se de estar na branch correta". Keep that:

- **it** — imperative, second person singular informal: "Crea un ambiente virtuale".
- **en** — imperative: "Create a virtual environment". No "you should", no "please", no
  "simply", no "just".

Do not add hedging the source does not have, and do not drop a caveat the source does
have. A translation that reads better than the original has usually lost something.

## `data-lead`

Translated like any other prose, and kept to one sentence in all three languages. If the
Portuguese lead is two clauses joined by a semicolon, keep the semicolon.

## When the source is ambiguous

Technical Portuguese is often ambiguous about who acts — "é gerado um log" hides the
subject. Translate the ambiguity rather than resolving it: `it` "viene generato un log",
`en` "a log is written". Do not invent the agent to make the English smoother.

If a sentence in the source is genuinely incomprehensible, translate it literally and flag
it in your report. Do not guess at what it meant and write that instead — rule 1 of the
skill applies to translation too.
