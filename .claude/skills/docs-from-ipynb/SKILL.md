---
name: docs-from-ipynb
description: Use when turning a file or folder from ipynb_contents/ into published pages under web_documentation/ - converts one source notebook or markdown file into the design system's markup and produces the pt, it and en versions. Trigger on "/docs-from-ipynb", "gerar a documentacao de <arquivo>", "publicar <conteudo> no site", or any request to turn ipynb_contents content into documentation pages.
---

# ipynb_contents -> web_documentation

One source file becomes three pages: `pt`, `it`, `en`. You write only the body of each
page. `scripts/build.py` assembles every page, the navigation, the pager, the language
switcher and the search index.

## Hard rules

1. **Convert, never rewrite.** Every paragraph, list item, table cell and code block in
   the source appears in the output with the same text. You change the *markup*, not the
   *words*. No invented sections, no dropped steps, no "improved" phrasing, no new
   examples. If the source is badly written, it stays badly written.
2. **One source file per run.** Three languages is already three times the work. When
   pointed at a folder, process one file and report what remains.
3. **Never hand-edit derived files.** `web_documentation/pages/`, `search-*.json` and
   `web_documentation/index.html` are build output. Your only writable target is
   `web_documentation/_content/`.
4. **Never touch `_design-system/`.** The CSS and JS there are the contract you write
   against, not output.

## Process

Create a todo per step.

### 1. Resolve the target

The argument is a path under `ipynb_contents/`, a file or a folder.

- **A file** -> that is the target.
- **A folder** -> list its files (`.ipynb` and `.md`, recursively), check which already
  have content in `web_documentation/_content/`, and take the first one that does not.
  Announce the full list and which one you picked.

Compute the page id the same way the build does: slug of
`[area, ...folders, title]`, where `title` is the file name without its extension and
without a leading `N. ` ordering prefix.

```
ipynb_contents/Getting Started/1. Quickstart.ipynb
  -> getting-started/quickstart
  -> web_documentation/_content/getting-started--quickstart.pt.html
```

Run `python .claude/skills/docs-from-ipynb/scripts/build.py --page-id "<path>"` to get
the id without guessing at the slug rules.

### 2. Read the source

For `.ipynb`, the text is the concatenation of the markdown cells in order; these
notebooks carry no code cells, and if one does, its source becomes a code block. For
`.md`, the file is the text.

If the file is 0 bytes, there is nothing to author. Say so, run the build (the page
renders the design system's "em branco" state by itself) and stop.

### 3. Write the Portuguese body

Write `web_documentation/_content/<page-id>.pt.html`.

**Read `reference/markup-contract.md` before writing this file.** It is the full list of
what you may emit and what each construct turns into. The build rejects anything outside
that vocabulary, so guessing costs you a round trip.

The shape:

```html
<page data-lead="One sentence, from the source's opening paragraph.">
  <h2>...</h2>
  <p>...</p>
</page>
```

The source's `# Title` heading does not go in the body - the build renders the title from
the tree. Its opening paragraph becomes `data-lead`. Everything after it is the body,
with `###` mapping to `<h2>` and `####` to `<h3>` (the page title owns `<h1>`).

### 4. Translate

Write `<page-id>.it.html` and `<page-id>.en.html`. **Read `reference/translation.md`
first.** Same markup, same structure, same anchors - only the prose changes. Code,
identifiers, commands, environment variable names and file paths are never translated.

### 5. Build

```
python .claude/skills/docs-from-ipynb/scripts/build.py
```

The first run also moves the mocked SPA to `web_documentation/_prototype.html`, writes
`web_documentation/_build/site.config.json` and generates every page in the tree - pages
without content render the "em branco" state, so the navigation and the pager are
complete from the start.

### 6. Verify before claiming anything

The build prints one line per written file and a summary. Confirm, in its output:

- the three pages for your page id are listed as `content` (not `empty` or `fallback`),
- `errors: 0`,
- the summary's page count went up by nothing unexpected.

If the build reports a validation error, fix the `_content` file - do not fix the page in
`pages/`, it will be overwritten.

Then run `python .claude/skills/docs-from-ipynb/scripts/build.py --check`, which
re-renders into a temporary directory and diffs against `pages/` - it must report no
drift. This catches a `_content` file that only renders correctly by accident.

### 7. Report

State: the source file, the page id, the three paths written, and - when the target was a
folder - which files in it are still unprocessed.

## What the build owns, so you do not

Navigation, area tabs, breadcrumb, pager order, `window.DOCS`, the language switcher's
alternate URLs, heading anchors, syntax highlighting, `.table-wrap`, the `.code`
scaffolding, the search index, the area overview pages, the home page and the language
dispatcher at `web_documentation/index.html`.

If you find yourself writing any of that by hand, stop - you are editing derived output.

## Red flags

| Thought | Reality |
|---|---|
| "The source's wording is clumsy, I'll tidy it" | Rule 1. Convert, do not rewrite. |
| "This folder only has four files, I'll do them all" | Rule 2. One per run. |
| "The page looks wrong, I'll patch `pages/...`" | Derived. Fix `_content/` and rebuild. |
| "I'll add a section explaining the module better" | The source decides what the page says. |
| "`<div class="grid">` should work, it's just HTML" | The contract is an allowlist. The build will reject it. |
| "The build printed a lot, it probably worked" | Read the summary. `errors: 0` or it did not. |
