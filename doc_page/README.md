# doc_page — o site da documentação

Site estático trilíngue (pt, en, it), gerado por um script Python sem nenhuma
dependência externa. Você escreve só o conteúdo; a moldura vem de um lugar só.

## Comandos

```bash
# gerar o site em dist/
python -m doc_page.builder build

# gerar só um idioma, enquanto escreve
python -m doc_page.builder build --langs pt

# verificar o resultado: links, hreflang, noindex, âncoras, assets, ícones
python -m doc_page.builder check

# servir dist/ como vai se comportar em produção (URL sem barra final inclusa)
python -m doc_page.builder serve          # http://localhost:8080
```

Nada a instalar: o build usa só a biblioteca padrão do Python 3.12.

## Onde fica cada coisa

```
doc_page/
├─ content/pt|en|it/     o conteúdo, um arquivo por página por idioma
├─ theme/                a moldura: layout.html, css/, js/
├─ assets/img|video/     mídia
├─ manifest.py           a árvore do menu
├─ site.toml             config do build
├─ builder/              o gerador
└─ dist/                 a saída (não versionada)
```

## Criar uma página

**1.** Adicione a linha no `manifest.py`, no lugar certo da árvore:

```python
folder("Agents", [
    folder("Utils", [
        page("Database"),
        page("Model Gateway"),
        page("Meu Módulo"),      # <- aqui
    ]),
]),
```

O rótulo que você escreve aqui é o que aparece no **menu**. A ordem da lista é
a ordem do menu e do prev/next.

**2.** Crie o fragmento em `content/pt/modules/agents/utils/meu-modulo.html`:

```html
<article
  data-title="MeuModulo"
  data-lead="Uma ou duas linhas dizendo o que é e para que serve.">
  <p>Parágrafo de abertura.</p>

  <h2>Título de seção</h2>
  <p>Texto com <code>código inline</code>.</p>
</article>
```

Só isso. Sem `<head>`, sem menu, sem rodapé — o build monta tudo em volta.

**3.** `python -m doc_page.builder build`

Se você errar o caminho ou esquecer a linha no manifest, o build falha dizendo
exatamente qual é o problema. Ele nunca gera um site silenciosamente errado.

## Regras do fragmento

| Atributo | |
| --- | --- |
| `data-title` | **obrigatório.** Vai no `<h1>` e no `<title>`. |
| `data-lead` | **obrigatório.** O resumo embaixo do título. Pode ficar vazio (`""`) enquanto não houver um bom. |
| `data-updated` | opcional, `AAAA-MM-DD`. Vai no `<lastmod>` do sitemap. |

- A raiz é um único `<article>`. Nada fora dele.
- Dentro, use os componentes do design system. O catálogo completo, com o HTML
  de cada um pronto para copiar, está em `theme/catalog/index.html` — abra no
  navegador, ou veja em `/_design-system/` no site gerado.
- Não escreva o índice "Nesta página": o `ds.js` monta a partir dos `h2`/`h3`.
- Não escreva `id` nos títulos: o build gera, com âncora clicável.
- Não pule de `h2` para `h4`. Só `h2` e `h3` têm estilo.

## Traduzir

Copie o arquivo para a árvore do idioma, no **mesmo caminho**, e traduza:

```bash
cp content/pt/modules/agents/utils/model-gateway.html \
   content/en/modules/agents/utils/model-gateway.html
```

Não existe arquivo de configuração de tradução. O build descobre o que está
traduzido pela existência do arquivo, então não há como o status mentir.

**Enquanto não houver tradução**, a página existe em `/en/` de todo jeito, com
a moldura em inglês, o corpo em português e um aviso no topo dizendo isso. Ela
sai como `noindex` com `canonical` para a versão portuguesa, e fica fora do
sitemap e da busca — então o Google nunca vê português anunciado como inglês.

Para ver o que falta num idioma:

```bash
diff <(cd content/pt && find . -name '*.html' | sort) \
     <(cd content/en && find . -name '*.html' | sort)
```

## Mudar o visual

| Quero mudar | Onde |
| --- | --- |
| Uma cor, fonte, raio | `theme/css/tokens.css` |
| A aparência de um componente | o arquivo dele em `theme/css/` |
| A moldura de todas as páginas | `theme/layout.html` |
| O comportamento de um componente | `theme/js/ds.js` |
| Menu, busca, troca de idioma | `theme/js/docs.js` |
| A ordem ou hierarquia do menu | `manifest.py` |

Depois de mexer em componente, atualize o catálogo. Ele é a documentação do
design system: se estiver diferente do código, está errado.

## Páginas sem conteúdo

Uma página prevista mas ainda não escrita leva `empty=True` no manifest:

```python
page("Context Builder", empty=True),
```

Ela não tem fragmento nenhum, aparece no menu com o badge "vazio", renderiza um
bloco explicando que o documento ainda não existe, e fica fora do sitemap e da
busca. Quando você escrever o conteúdo, crie o fragmento **e** tire o
`empty=True` — o build falha se os dois discordarem, nos dois sentidos.

## O que o build garante

`check` roda oito regras, todas por um motivo concreto:

1. **Links** — todo caminho interno resolve para um arquivo que existe.
2. **Rotas** — nenhuma rota de hash antiga, nenhuma referência a `doc/`.
3. **Estrutura** — cada página tem exatamente um `h1`, um `.prose`, um TOC e
   um diálogo de busca, e o script de tema é o primeiro do `<head>`.
4. **hreflang** — um alternate nunca aponta para página inexistente ou
   `noindex`.
5. **noindex** — todo espelho e toda vazia tem `canonical` coerente e está
   fora do sitemap.
6. **Busca** — toda página indexável aparece uma vez, e toda âncora do índice
   existe de verdade na página.
7. **Assets** — nada embarca sem ser referenciado, nada referenciado falta.
8. **Ícones** — todo `data-ico` existe no mapa do `ds.js`.

## Publicar

`dist/` é um site estático puro: diretório + `index.html`, sem nenhuma regra de
rewrite. Funciona em Railway static, GitHub Pages, Cloudflare Pages ou
`python -m http.server`.

Antes de publicar, ajuste `site_url` no `site.toml` — ele é usado no
`canonical`, no `hreflang` e no `sitemap.xml`. Se o site não ficar na raiz do
domínio, ajuste `base` também (ex: `base = "/docs"`).

Cache: tudo em `/assets/` e os `search-index.*.json` têm hash no nome e podem
ser `immutable` por um ano. O HTML fica `no-cache`.
