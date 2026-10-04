# Estrutura do `doc_page/` — site de documentação estático, trilíngue

## Contexto

A documentação hoje vive em `doc/` como 20 `.md` + 38 `.ipynb`, e existe um protótipo HTML aprovado (`doc/site-prototype/index.html`) cujo conteúdo é **falso**: apenas 4 das 61 páginas têm conteúdo real, e o protótipo nunca foi conectado aos 47 documentos de verdade. O design system já foi extraído para `doc/design-system/`, mas o protótipo não o usa.

O objetivo é um site de verdade: tudo em HTML, sem `.ipynb` nem `.md`, cada documento em português, inglês e italiano, servido como site estático.

**O problema que define a arquitetura:** 56 páginas × 3 idiomas = **183 páginas**, e o `page-template.html` atual é feito para *copiar por página*, com o passo 4 do README mandando "atualize o menu lateral à mão". Mudar um item do menu seriam 183 edições. Por isso o chrome precisa vir de um lugar só, e existe um gerador.

Três descobertas que mudam o trabalho:

1. **Todos os 38 notebooks são 100% células markdown** — 75 células markdown, zero células de código, zero outputs, em toda a árvore. São markdown disfarçado: a conversão é mecânica e um único pipeline cobre 100% do acervo.
2. **`Acquarello.ipynb` tem 10 URLs `lh3.googleusercontent.com`** (verificado: 10 em Acquarello, 0 em Content Generator). São URLs de sessão do Google Drive, já expiradas ou expirando. Migrar com elas intactas publica 10 imagens quebradas na página vitrine.
3. **Não existe nenhuma regra `h4`/`h5`/`h6` no CSS** (verificado: só `.prose h2` e `.prose h3` em `content.css:19-20`). Todo `h4+` do acervo renderiza sem estilo hoje.

## Decisões fechadas

| Decisão | Escolha |
| --- | --- |
| Geração | Gerador em Python, **stdlib only** em regime permanente. Sem Node. |
| Acervo atual | Converter os 47 docs agora; `doc/` é aposentado. |
| Publicação | Host estático, URLs limpas (diretório + `index.html`). |
| URLs i18n | Prefixo `/pt/` `/en/` `/it/` + hreflang. |
| Idiomas no lançamento | **Os 3**, com espelho + `noindex` + `canonical` onde falta tradução. A forma da URL precisa estar estável antes de qualquer link externo. |
| Contraste | **Corrigir** as 4 falhas WCAG no mesmo trabalho (só `tokens.css`). |
| Rótulos do menu | **Como no protótipo**: menu vem do `manifest.py` (`Model Gateway`), título da página vem do `data-title` do fragmento (`ModelGateway`). |

---

## 1. Estrutura de `doc_page/`

```
doc_page/
├─ site.toml                  config do build (tomllib, stdlib): site_url, base,
│                             github_repo/branch, langs, default_lang
├─ manifest.py                FONTE ÚNICA da estrutura: árvore, ordem, slugs, ícones
├─ __init__.py
│
├─ content/                   fragmentos HTML autorais, um arquivo por página
│  ├─ pt/
│  │  ├─ index.html                              corpo da home
│  │  ├─ getting-started/quickstart.html
│  │  ├─ modules/agents/utils/model-gateway.html
│  │  └─ …                                       45 fragmentos de folha
│  ├─ en/                     mesma forma, esparso. Presença = "traduzido".
│  └─ it/
│
├─ theme/                     `git mv` de doc/design-system — a ÚNICA cópia
│  ├─ README.md               contrato do design system, inalterado
│  ├─ css/                    inalterado (entrada @import + 7 parciais)
│  ├─ js/ds.js                inalterado
│  ├─ js/docs.js              NOVO: o que o ds.js deliberadamente não faz
│  ├─ layout.html             NOVO: o layout, derivado do page-template.html
│  ├─ partials/               NOVO: overview-body, empty, 404-body
│  ├─ templates/page-template.html   mantido como referência de autoria
│  └─ catalog/index.html      `git mv` de design-system/index.html
│
├─ assets/
│  ├─ img/                    só as imagens efetivamente referenciadas
│  └─ video/acquarello.mp4    `git mv` de doc/Streamlit Applications/videos/
│
├─ builder/                   o gerador — stdlib only
│  ├─ __main__.py   cli: build | check | serve
│  ├─ settings.py   site.toml → dataclass congelada
│  ├─ slugs.py      slug(), fold() — portes do protótipo
│  ├─ model.py      dataclasses Page / Area / Node
│  ├─ tree.py       manifest → lista plana, urls, prev/next, crumbs, títulos
│  ├─ fragment.py   parse <article data-*> → (meta, body)
│  ├─ highlight.py  porte do tokenizador RULES do protótipo
│  ├─ nav.py        HTML das abas + menu lateral, por página
│  ├─ render.py     layout, cabeçalho do artigo, pager, linha de fonte, hreflang
│  ├─ strings.py    porte do I18N (chrome), com pt como fallback
│  ├─ searchindex.py
│  ├─ assets.py     concat+hash de css/js, cópia de mídia, dimensão de PNG
│  ├─ seo.py        sitemap.xml, robots.txt, redirect raiz, 404
│  └─ check.py      verificador fim a fim
│
├─ tools/migrate_doc.py       USO ÚNICO. Precisa de markdown-it-py. Mantido, congelado.
│
└─ dist/                      saída do build — .gitignored
   ├─ index.html              redirect com sniff de idioma → /pt/
   ├─ 404.html  robots.txt  sitemap.xml
   ├─ assets/css/ds.<hash>.css   assets/js/docs.<hash>.js   assets/img/  assets/video/
   ├─ _design-system/index.html  o catálogo, noindex
   └─ pt/ | en/ | it/
      ├─ index.html                                    → /pt/
      ├─ modules/index.html                            → /pt/modules/
      ├─ modules/agents/utils/model-gateway/index.html  → /pt/modules/…/model-gateway/
      ├─ search-index.<hash>.json
      └─ structure.json
```

**URLs limpas = diretório + `index.html`, não `pagina.html`.** É a escolha que faz `/pt/modules/x/` resolver em *qualquer* host estático sem nenhuma regra de rewrite — inclusive `python -m http.server`, Railway static e GitHub Pages. Sem `_redirects`, sem config específica de host.

**`theme/` é `git mv`, não cópia.** `doc/` vai ser aposentado; duas cópias do CSS divergem em uma semana. O catálogo desce um nível, então seus três links precisam de um ajuste (verificado em `design-system/index.html:16,17,529`): `css/…` → `../css/…`, `js/ds.js` → `../js/ds.js`.

## 2. Formato do fragmento

Raiz `<article>` com os metadados nos próprios atributos. **Obrigatórios:** `data-title`, `data-lead`. **Opcionais:** `data-updated`, `data-eyebrow`, `data-noindex`.

```html
<article
  data-title="ModelGateway"
  data-lead="Fábrica unificada de modelos: uma única chamada para Anthropic, Google, Groq e OpenAI."
  data-updated="2026-10-04">
  <p>A classe <code>ModelGateway</code> atua como uma fábrica…</p>
  <h2>Fluxo de execução</h2>
  …
</article>
```

O build lê os atributos como metadado e usa o **HTML interno verbatim** como conteúdo do `.prose`.

Por que não as alternativas: *front-matter em comentário HTML* é sintaxe inventada que nenhuma ferramenta valida — um typo falha em silêncio, enquanto um atributo malformado é pego pelo `html.parser` e por qualquer editor. *JSON ao lado* reintroduz exatamente a divergência declarado-vs-real que o resto do desenho existe para evitar: renomeie o html e o json fica órfão, e viram 2 arquivos por página.

`fragment.py` falha o build se a raiz não for `<article>` ou se um `<` aparecer dentro da tag de abertura (atributo não escapado).

## 3. `manifest.py` — fonte única da estrutura

Módulo Python **declarativo**: literais e dois helpers, sem lógica. Escolhido sobre JSON/YAML porque os dados **já existem como código** no protótipo (`AREAS`, linha ~1446, com os helpers `md`/`nb`/`blank`/`dir`), então é transliteração mecânica; porque JSON não aceita comentários e esta árvore tem 11 páginas deliberadamente vazias e 2 typos preservados (`Storage Menage Repository`, `Storage Menager`) que precisam de um `# sic` ao lado; e porque YAML exigiria dependência que o repo não tem.

```python
def page(title, *, slug=None, empty=False):   ...
def folder(title, kids, *, slug=None):        ...

AREAS = [
  {"t": "Getting Started", "icon": "bolt", "slug": "getting-started",
   "titles": {"pt": "Primeiros passos", "en": "Getting Started", "it": "Primi passi"},
   "kids": [page("Quickstart"), page("Dependences"), page("Licence")]},
  {"t": "Modules", "icon": "boxes", "slug": "modules",
   "titles": {"pt": "Módulos", "en": "Modules", "it": "Moduli"},
   "kids": [
     folder("Agents", [folder("Utils", [page("Database"), page("Model Gateway")])]),
     folder("Deep Research", [folder("Tavily Research", [
        page("Context Builder", empty=True), page("Tavily Core", empty=True)])]),
     …]},
  …
]
POPULAR = ["getting-started/quickstart", "modules/agents/utils/model-gateway", …]
```

**O manifest NÃO guarda:** títulos de página por idioma, leads, datas, caminhos de origem, status de tradução, conteúdo. O `file=` do protótipo desaparece — `1. Quickstart.ipynb` era nome de *origem*, e o prefixo numérico codificava ordem, que agora a ordem da lista carrega.

**Status de tradução é derivado, nunca declarado:** `page.translations = {l for l in LANGS if (content/l/<slug>.html).exists()}`.

Três validações fatais em `tree.py`, que é o que faz a promessa de "não pode divergir" valer de fato:

1. `empty=True` **e** `content/pt/<slug>.html` existe → erro. Sem isso a flag passa a mentir no instante em que alguém escreve o conteúdo.
2. `empty=False` e não há fragmento pt → erro. Pega página declarada e nunca escrita.
3. `icon` fora do mapa `ICON` do `ds.js` → erro. `assets.py` extrai as chaves válidas do próprio `ds.js` por regex, então o conjunto nunca é duplicado.

Contrapartida de usar `.py`: não é legível por outras ferramentas. Resolvido emitindo `dist/<lang>/structure.json` em todo build — quem quiser a árvore como dado recebe, gerada, nunca mantida à mão.

## 4. O builder

**Invocação:** `uv run python -m doc_page.builder build`. Pacote em `doc_page/builder/`, **não** em `src/` — `src/` é a aplicação FastAPI/Streamlit, e o gerador de docs não faz parte do produto entregue nem deve ser importável como `src.*`. Sem entrada em `[project.scripts]`, pelo mesmo motivo.

Subcomandos `build`, `check`, `serve [--watch]`; flags `--langs`, `--base`, `--missing-translation {mirror,omit}`, `--no-video`, `--strict`.

**Dependências em regime permanente: nenhuma.** `tomllib`, `html.parser`, `re`, `json`, `hashlib`, `pathlib`, `struct`, `http.server`, `xml.sax.saxutils` — tudo stdlib no Python 3.12. `markdown-it-py` entra **só** como grupo opcional `docs` no `pyproject.toml`, usado pela migração de uso único, para nunca entrar na resolução da aplicação.

**Encoding:** todo `open`/`read_text`/`write_text` passa `encoding="utf-8"` e a CLI faz `sys.stdout.reconfigure(encoding="utf-8")`. O default do Windows aqui é cp1252 e quebra com `UnicodeEncodeError` no primeiro `🎨` — já reproduzido durante a exploração.

Fases, em ordem: settings → manifest+validação → varredura de fragmentos → resolução da árvore (urls, prev/next, crumbs, títulos, traduções) → assets (concat/hash/mídia) → render por página × idioma → índice de busca → SEO → check.

## 5. O que o gerador supre e o `ds.js` não

O `ds.js` fica **intacto**. Ele já faz ícones, abas de código, copiar, tema, gaveta mobile, `.side-folder`, `--top`, abrir/fechar a busca com `Ctrl K` / `/` / `Esc`, e montar o TOC. Ele deliberadamente **não** faz: geração do menu, índice/ranking/render da busca, roteamento, i18n, realce de sintaxe. É exatamente essa lista que o gerador preenche.

**Menu (`nav.py`)** — porte de `renderTabs`/`renderNav`/`nodeHtml`/`pageLink`, com o trabalho de runtime do `markActive` resolvido no build: a folha atual recebe `aria-current="page"`, e cada `.side-folder` ancestral sai com `aria-expanded="true"` e seu `<ul class="side-sub">` **sem** `hidden`. O handler de clique do `ds.js` então simplesmente funciona, sem JS para abrir o galho ativo.

Os ícones saem como `<i class="chev" data-ico="chevron">`, nunca SVG pré-renderizado — o `icons()` do `ds.js` troca pelo SVG real, então os 24 caminhos de ícone continuam existindo em um lugar só.

**Linha de fonte** — o protótipo emite `Fonte: doc/Modules/Agents/Utils/Model Gateway.md`. Depois da aposentadoria de `doc/` esse caminho é mentira. Passa a ser link para o fragmento no GitHub, montado do `site.toml`; o `.edit` do `.feedback` vira a URL `/edit/` correspondente.

**Troca de idioma (`theme/js/docs.js`)** — o `ds.js` dispara `ds:lang` e deixa a resposta para o site. Num site estático multipágina a resposta certa é navegar, e a parte não óbvia é que uma página espelho precisa levar para a página que de fato tem conteúdo. Daí `window.DOCS.alt` ser gerado por página:

```html
<script>window.DOCS={lang:"pt",base:"",
  alt:{pt:"/pt/modules/agents/utils/model-gateway/",
       en:"/en/modules/agents/utils/model-gateway/",
       it:"/it/modules/agents/utils/model-gateway/"},
  index:"/pt/search-index.a1b2c3d4.json"};</script>
```

Esses ~300 bytes inline são o único JS inline além do script anti-FOUC, e substituem todo o runtime de i18n do protótipo.

**Realce de sintaxe: no build.** Zero JS e zero CPU no cliente, código realçado antes de qualquer JS rodar, e as classes `.t-k/.t-s/.t-n/.t-f/.t-c` já estão estilizadas em `content.css`. São as mesmas 4 regexes do protótipo (python, bash, json, env), que cobrem 99,6% das cercas do acervo. Dois detalhes do porte: passar `re.ASCII`, porque `\w` em Python é Unicode-aware e engoliria acentos nos grupos de nome de função; e os lookbehinds `(?<=\s)` do bash funcionam como estão, porque são de largura fixa.

## 6. Busca

Índice gerado no build, **por idioma**, carregado sob demanda. Corrige a fraqueza do protótipo, que indexa só títulos e migalhas — **nunca o corpo**.

Forma: dois arrays, com seções referenciando páginas por índice inteiro para não repetir a migalha 20× por página.

```json
{"v":1,"lang":"pt",
 "p":[["modules/agents/utils/model-gateway","/pt/modules/…/","ModelGateway","Modules / Agents / Utils",1]],
 "s":[[0,"fluxo-de-execucao","Fluxo de execução","instanciar a classe modelgateway…"]],
 "popular":[0,7,31,54]}
```

`p` = `[id, url, título, migalhas, ordem]`; `s` = `[índice da página, âncora, texto do título, texto do corpo]`. O corpo é o texto puro entre um título e o próximo, já `fold()`ado e com espaços colapsados **no build** — o cliente nunca normaliza 300 KB na primeira tecla.

Propriedade que vale explorar: `fold()` é NFD + remoção de diacríticos + lowercase, logo **preserva o comprimento**, e os offsets do `<mark>` valem nos dois textos. Guardar só os primeiros 240 caracteres de cada seção como texto de exibição e casar contra o folded completo.

Tamanho medido contra o acervo real: ~360 KB sem compressão, **~95-110 KB em gzip**. Grande demais para carregar junto da página, certo para carregar sob demanda — no primeiro de: abrir o diálogo, ou `pointerenter`/`focus` no `[data-open-search]` (prefetch, então quando o diálogo pinta o fetch normalmente já terminou). Com nome hasheado, é `immutable` para sempre.

Ranking: as faixas do protótipo, estendidas para o corpo — título startsWith 0, título includes 1, seção startsWith 2, seção includes 3, migalha 4, corpo 5; mais o `+0.5` de penalidade para seções e `ordem/1000` como desempate estável. Teto de 12 resultados e **no máximo 3 seções por página**, para uma página longa não inundar a lista. Páginas vazias e espelhos ficam fora do índice.

## 7. i18n

**Strings do chrome resolvidas no build.** Com URL por idioma cada página já é monolíngue, então a varredura `[data-i]`/`[data-ia]`/`[data-ip]` do protótipo é custo puro: manda os três idiomas para todo visitante e pisca o idioma errado antes do JS rodar. Resolver no build dá **zero JavaScript de i18n**, `<html lang>` correto desde o primeiro byte e nenhum flash de texto.

`strings.py` é porte direto do `I18N`, guardando suas duas melhores propriedades: valores podem ser string **ou callable** (interpolação), e **pt é o fallback**. String ausente sem fallback pt é **erro de build**, não `undefined` silencioso.

**Títulos — fechando a lacuna.** O protótipo nunca traduz títulos; eles vêm dos nomes de pasta em inglês. Cadeia de três passos:

1. **Títulos de área** vêm do `titles` do manifest, por idioma. 4 áreas × 3 idiomas = 12 strings; são a linha de abas e o seletor do menu, o único lugar onde o rótulo traduzido importa de verdade.
2. **Rótulo de folha no menu** vem do `manifest.py` (decisão fechada: preserva o menu aprovado, `Model Gateway`).
3. **Título da página** (`<h1>`) vem do `data-title` do fragmento daquele idioma (`ModelGateway`), com fallback para pt e, por último, o nome estrutural.

Rótulos de pasta (`Agents`, `Utils`, `Content Parsing Agent`) ficam **sem tradução, deliberadamente**: são nomes de estrutura de código que casam com os diretórios de `src/`, e traduzir quebraria o mapa mental entre doc e fonte. O schema aceita um `titles=` em `folder()` se isso mudar.

**Política de tradução faltante: espelho + `noindex` + `canonical`.** Para uma página sem fragmento `en`, gera `/en/<path>/` com chrome **todo em inglês** (nav, abas, pager, busca, rodapé — é a maior parte do valor percebido e sai de graça), corpo em pt, o callout `untranslated` que o protótipo já tem escrito como primeiro filho do `.prose`, `canonical` → pt, `robots: noindex, follow`, **nenhum** `hreflang="en"` em lugar nenhum, e exclusão do sitemap e do índice de busca.

Isso é hreflang-correto **por causa** do `noindex`: nunca se declara `hreflang="en"` para uma página servindo português, então não há mentira para o Google; e o `noindex` mantém o espelho fora do índice, sem exposição a conteúdo duplicado. A alternativa (omitir `/en/`) também é correta mas pior para quem lê: o seletor de idioma ou dá link morto ou devolve para `/pt/`, e perde-se o chrome traduzido.

**Realidade do lançamento, dita com clareza:** como não existe conteúdo en/it, no dia 1 todas as 56 folhas de `/en/` e `/it/` são espelhos — 183 páginas, das quais ~112 são espelhos `noindex` e ~33 são stubs de página vazia. Só a home e as 4 visões gerais de área são genuinamente trilíngues (as visões gerais são geradas do manifest, então são tradução real). ~4,5 MB de HTML, trivial para host estático.

## 8. Migração de uso único

`doc_page/tools/migrate_doc.py`. Lê `doc/` + `manifest.py`, escreve `content/pt/**`. Idempotente, com `--dry-run` e relatório por arquivo. **Mantido no repo**, congelado, com cabeçalho dizendo a data em que rodou e contra qual árvore — é o único registro de como 47 arquivos viraram 46 fragmentos, e jogá-lo fora tornaria a migração irrevisável depois.

O manifest não carrega mais `file=`, então a migração usa um dict `SOURCES` que vive **só** no script, mapeando slug → caminho real em `doc/`. É ele que guarda os prefixos numéricos e os dois typos preservados; morre com o script.

**Notebook → markdown** (verificado correto para todos os 38: zero células de código):

```python
def nb_markdown(path):
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = [c for c in nb["cells"] if c["cell_type"] == "markdown"]
    return "\n\n".join("".join(c["source"]).rstrip() for c in cells)
```

**`markdown-it-py`** é a escolha por um motivo concreto: os únicos 8 links entre documentos do acervo usam a forma com ângulos `](<../Getting Started/1. Quickstart.ipynb>)`, que o CommonMark trata corretamente. A reescrita é por token, não por regex sobre HTML.

**Mapeamento para o vocabulário do design system** — markdown→HTML cru não produz nenhuma das classes, então cada uma é explícita:

| Markdown | Emitido |
| --- | --- |
| cerca ` ```python ` | `<div class="code plain" data-lang="python">` + `code-body` + `<pre><code>` + `<button class="copy floating">` — igual ao bloco "Simples" do catálogo |
| tabela | envolvida em `<div class="table-wrap">` |
| `> citação` | `<div class="callout" data-kind="note">`, com sniff de `**Nota:**`/`**Atenção:**`/`[!WARNING]` para escolher a variante. Quase no-op: só `doc/README.md` tem citações |
| `![alt](x.png)` sozinho num parágrafo | `<figure class="frame">` + `loading="lazy" decoding="async"` + `width`/`height` reais + `<figcaption>` |
| `![](badge-url)` entre irmãos | fica `<img>` inline — os badges do shields.io são ornamento, não figura |
| `<video src="videos/x.mp4">` | `<figure class="frame"><video preload="none" poster=…>` |
| `---` | **descartado** — não há regra de `<hr>` no CSS |
| `# h1` do 2º em diante | rebaixado para `h2` |
| `#### h4`, `##### h5` | **rebaixados para `h3`** — verificado que `h4+` é literalmente sem estilo hoje; o rebaixe também conserta o salto de nível `## 1. …` → `####`, que senão produz um TOC quebrado |
| `[t](<../X/Y.ipynb>)` | reescrito para a URL do site via mapa origem→slug. 8 links. Não resolvido = erro de build |

Os `.ipynb` de `Streamlit Applications` já contêm **HTML do design system escrito à mão** (`<div class="callout" data-kind="warn">`, `<div class="code" data-tabs>`) e `<video>` cru — a migração precisa **passar isso adiante**, não re-escapar. Daí `MarkdownIt("commonmark", {"html": True})`.

**Título e lead.** Primeiro `^# ` → `data-title`, removido do corpo, com emoji inicial retirado (`# 🎨 Acquarello` → `Acquarello`) e marcação inline desfeita (atributo não aceita markup). Lead = primeiro parágrafo simples depois do h1 com ≤300 caracteres; se não houver, `data-lead=""` e a página entra em `TODO-lead` no relatório (esperados ~6, as páginas com badges). Lead errado gerado automaticamente é pior que lead vazio — essas 6 frases se escrevem à mão.

Um conserto de dado: `Modules/Embedding/Embedding Module.ipynb` tem o h1 obsoleto `# Classe TestPineconeVectorStore`. O script **reporta** o desencontro com o manifest em vez de propagar em silêncio.

**As 10 imagens efêmeras — decidir antes de rodar.** Ordem de preferência: (1) `--fetch-remote` baixa agora, enquanto alguma ainda resolve, para `assets/img/` com nome slugificado, reportando OK/FALHOU por URL; (2) para as que falharem, emitir `<div class="frame frame-missing">` — componente que **já existe** em `content.css` exatamente para esse caso — com a URL original em comentário HTML para recuperação; (3) re-capturar a tela à mão depois.

**As 11 páginas vazias não geram fragmento.** São `empty=True` no manifest e o build renderiza o bloco `.empty` (porte do `emptyHtml`, usando as classes existentes), mais o `.badge` no menu, `noindex`, e exclusão de sitemap e busca.

**Caminhos de asset** passam a ser absolutos com prefixo `{BASE}` — `/assets/img/logo-icon.png`, nunca `../../../images/Logo.png`. Isso mata a inconsistência de caminho relativo que já existe hoje entre protótipo, catálogo e template. Só mídia **referenciada** é copiada: `images/` tem 9,2 MB e o chrome usa um arquivo de 108 KB; copiar a pasta embarcaria `Logo_Text.png` (3,5 MB) por nada.

## 9. Otimização

**CSS.** A cadeia de `@import` é o pior ponto da entrega atual: 7 idas e voltas em série, todas bloqueando render, e o `@import` das fontes está *dentro* de um stylesheet, então o navegador não consegue nem descobri-lo antes de parsear `design-system.css`. O build lê o `design-system.css`, **deriva a ordem das próprias linhas `@import`** (nunca duplica a ordem em Python — ela é lida do arquivo que o README define como autoritativo, logo não pode divergir; e `catalog.css` sai automaticamente porque não é importado, que é precisamente por que ele foi deixado de fora), concatena em `ds.<sha8>.css`, e tira as fontes para `<head>` com `preconnect` + `<link>` paralelos. **2 requisições bloqueantes em vez de 8**, ~26 KB.

**JS.** `ds.js` + `docs.js` concatenados em `docs.<sha8>.js`, com `<script defer>` no `<head>`. O `ds.js` é IIFE autocontido e já trata os dois casos de `readyState`, então `defer` não muda nada no comportamento. Uma requisição, ~16 KB, não bloqueante.

**Vídeo.** `git mv` dos 2 mp4 (os bytes já estão no histórico) e servir com `preload="none"` + `poster`. Com `preload="none"` quem não aperta play baixa **zero** byte de vídeo, o que tira os 9,6 MB do peso de página — sobra só tamanho de repo e tempo de deploy. Recompressão e geração de poster ficam como passo manual opcional, porque dependem de ffmpeg, que não é dependência Python.

**Cache.** `sha256(conteúdo)[:8]` no nome de CSS, JS e de cada `search-index.json`. Tudo sob `/assets/` fica `immutable` por um ano; HTML fica `no-cache`. O hash do índice chega ao cliente pelo `window.DOCS.index`, sem requisição extra.

**Anti-FOUC.** O script de 8 linhas do `page-template.html` fica **inline, verbatim, primeiro no `<head>`**, antes dos links de CSS — é isso que o faz funcionar, e está marcado "Não remova" no template por bom motivo. Acrescentar `<meta name="color-scheme" content="light dark">` logo depois.

**Imagens sem CLS.** `loading="lazy" decoding="async"` em todo `.prose img` (nada no `.prose` está acima da dobra) com `width`/`height` reais. Ler dimensão de PNG não precisa de dependência — o IHDR está em offset fixo:

```python
def png_size(p):
    b = p.read_bytes()[:24]
    return struct.unpack(">II", b[16:24]) if b[:8] == b"\x89PNG\r\n\x1a\n" else None
```

**Contraste (decidido: corrigir).** 4 valores em `tokens.css`, zero mudança de HTML: `--ink-4` de 2,6:1 para ~4,6:1, e os três tokens de sintaxe do tema claro (`--t-s` 3,3:1, `--t-c` 3,2:1, `--t-n` 3,0:1) um passo mais escuros. Reconferir o catálogo depois e atualizar a seção de acessibilidade do `theme/README.md`, que hoje documenta essas falhas como dívida conhecida.

**SEO.** `sitemap.xml` com URLs absolutas e `<xhtml:link rel="alternate">` por tradução real + `x-default` → pt, excluindo espelhos, vazias e catálogo. `robots.txt` liberando tudo menos `/_design-system/`. `404.html` com chrome completo. `dist/index.html` é a única opção honesta num host estático puro — redirect no cliente, com sniff de `navigator.languages`, `<meta http-equiv="refresh">` de reserva e links visíveis para os três idiomas para quem não tem JS.

## 10. Ordem de execução

Cada passo deixa o repo funcionando.

| # | Passo | Verificação |
| --- | --- | --- |
| 1 | `git mv doc/design-system doc_page/theme`; mover o catálogo para `theme/catalog/index.html` e ajustar seus 3 links (`../css/`, `../js/`) | abrir o catálogo: as 27 seções renderizam, tema alterna |
| 2 | `git mv` dos 2 mp4 para `assets/video/`; copiar e slugificar as imagens referenciadas | os vídeos tocam do novo caminho |
| 3 | Escrever `manifest.py` transliterando `AREAS` (protótipo, ~linha 1446) | script descartável imprime os 61 ids; **diff contra os ids do protótipo tem de ser idêntico** |
| 4 | `builder/` fases 0-2 (settings, manifest, tree). Sem render ainda | `check --tree-only` lista 61 páginas/idioma com url, prev/next e crumbs |
| 5 | `uv add --optional docs markdown-it-py`; rodar `migrate_doc.py --dry-run`, ler o relatório, corrigir mapeamentos, rodar de verdade | 45 fragmentos + home em `content/pt/`; relatório com ~6 TODO-lead, 1 título divergente, 10 resultados de imagem remota |
| 6 | Resolver à mão os itens do relatório: os ~6 leads, o título do `Embedding Module`, as 10 imagens efêmeras | relatório limpo |
| 7 | `theme/layout.html` a partir do `page-template.html` + os 3 partials; `render.py`, `nav.py`, `highlight.py`, `strings.py` | build `--langs pt`; abrir `dist/pt/modules/agents/utils/model-gateway/` lado a lado com a mesma página do protótipo |
| 8 | `assets.py` + `seo.py` + correção dos tokens de contraste | `check` passa; view-source mostra 2 CSS + 1 JS |
| 9 | `searchindex.py` + a busca do `docs.js` | `Ctrl K`, buscar `gateway`, `embedding`, e **um termo que só existe no corpo** — nunca funcionou no protótipo |
| 10 | Ligar en/it + navegação de idioma | trocar idioma numa página profunda: cai na mesma página, chrome em inglês, callout `untranslated`, `noindex` + `canonical` presentes |
| 11 | Deploy | — |
| 12 | `git rm -r doc/` em **commit separado** | o commit de aposentadoria é revertível sozinho |

**`doc/site-prototype/index.html` fica até o passo 7 passar.** Não é só referência visual: é o único lugar onde o corpo da home (`homeBody()`), o gerador de visão geral (`overviewHtml()`), a tabela `I18N` e o bloco `emptyHtml` existem como código funcionando, e os quatro precisam ser portados. Mover para `doc_page/reference/site-prototype.html` durante a transição e apagar no mesmo commit que aposenta `doc/`.

`doc/README.md` (13 KB) **não está em `AREAS`** — o protótipo só o usa como string de fallback. Recomendação: dobrar sua prosa útil no `content/pt/index.html` junto do `homeBody()` do protótipo, sem dar URL própria.

## 11. Verificação

`python -m doc_page.builder check` percorre `dist/` e falha apontando arquivo e linha:

1. **Integridade de link** — todo `href`/`src` com `{BASE}/` resolve para arquivo real. Pega numa passada toda a classe de bug que os caminhos relativos atuais já têm.
2. **Sem roteamento obsoleto** — zero `href="#/"` (as rotas de hash do protótipo) e zero `doc/` como caminho na saída.
3. **Estrutura** — por página: um `<h1 class="page-title">`, um `.lead` (exceto vazias), um `.prose`, um `<aside data-toc>`, um `<dialog id="search">`, e o script de tema como primeiro `<script>`.
4. **Reciprocidade de hreflang** — se `/pt/x/` declara `hreflang="en"`, então `/en/x/` existe, declara a volta, e **não** é `noindex`. É o check que torna a política de espelho confiável.
5. **Coerência de `noindex`** — todo espelho e toda página vazia é `noindex`, tem `canonical` apontando para página que *não* é noindex, e está ausente do sitemap e da busca.
6. **Cobertura da busca** — toda página real aparece no índice do seu idioma exatamente uma vez, e toda âncora em `s` existe como `id` real na página. Pega divergência índice↔âncora, que de outro modo só aparece quando alguém clica.
7. **Higiene de asset** — todo arquivo em `dist/assets/` é referenciado por ao menos uma página (nenhum `Logo_Text.png` de 3,5 MB pegando carona), e todo asset referenciado existe.
8. **Ícones** — todo `data-ico="x"` tem `x` no mapa `ICON` do `ds.js`.

Mais uma passada manual que nenhum checker substitui: `python -m doc_page.builder serve` (subclasse de `http.server` que mapeia `/x/` → `/x/index.html`, para URL sem barra final se comportar como em produção) e, nos 4 breakpoints documentados (>1280 três colunas, 1024-1279 TOC inline, <1024 gaveta, <640 uma coluna), conferir gaveta + scrim, persistência do tema entre navegações, `Ctrl K` e `/`, abas de código e botão copiar, scroll-spy do TOC, e a troca de idioma a partir de página profunda. São as 8 coisas que o `ds.js` controla, e as que uma mudança no gerador quebra em silêncio.

## 12. Fora de escopo, registrado

- **Rótulos de pasta sem tradução** (`Agents`, `Utils`) — deliberado, para manter o mapa doc↔`src/`. O schema aceita mudar.
- **Recompressão dos mp4 e geração de poster** — precisa de ffmpeg, não cabe no build Python. `ffmpeg -crf 30 -vf scale=1280:-2 -movflags +faststart` costuma levar 6 MB para ~1,5 MB.
- **Auto-hospedar as fontes** (woff2 subsetado em `assets/fonts/`) — maior ganho restante, ~200 ms de RTT, mas é tarefa separada.
