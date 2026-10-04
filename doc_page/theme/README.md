# BetterAI Docs — Design System

Os tokens, componentes e regras que mantêm todas as páginas da documentação com o mesmo visual. Serve para criar páginas novas e para atualizar as existentes sem sair do padrão.

Abra `index.html` para ver o catálogo. Ele usa os próprios componentes, então o que está lá é o que as páginas entregam.

## O que tem aqui

```
design-system/
├─ index.html                  catálogo visual: cores, tipografia, componentes e regras
├─ templates/
│  └─ page-template.html       página completa para copiar e preencher
├─ css/
│  ├─ design-system.css        ponto de entrada: importe só este arquivo
│  ├─ tokens.css               cores, fontes, raios e sombra (claro e escuro)
│  ├─ base.css                 reset e regras globais
│  ├─ layout.css               cabeçalho, abas, menu lateral, índice da página
│  ├─ content.css              artigo e todos os componentes de conteúdo
│  ├─ search.css               diálogo de busca
│  ├─ responsive.css           ajustes por largura de tela
│  └─ catalog.css              só do catálogo; não leve para as páginas
└─ js/
   └─ ds.js                    comportamento dos componentes, sem dependências
```

## Criar uma página nova

1. Copie `templates/page-template.html` para o lugar da nova página.
2. Ajuste os caminhos de `css/design-system.css`, `js/ds.js` e do logo.
3. Troque o título, a categoria, o resumo e o conteúdo de `<div class="prose">`.
4. Atualize o menu lateral e marque a página atual com `aria-current="page"`.
5. Confira no catálogo se cada bloco que você usou segue o mesmo HTML.

O índice "Nesta página" é montado sozinho a partir dos `h2` e `h3`. Não escreva ele à mão.

## Atualizar o visual

Mude o visual no lugar certo e todas as páginas acompanham:

| Quero mudar | Onde |
| --- | --- |
| Uma cor, fonte, raio ou sombra | `css/tokens.css` |
| A aparência de um componente | O arquivo do componente em `css/` |
| A moldura de todas as páginas | `templates/page-template.html` e `css/layout.css` |
| O comportamento de um componente | `js/ds.js` |

Depois de qualquer mudança, atualize o catálogo (`index.html`) e, se o HTML do componente mudou, o template. O catálogo é a documentação do design system: se ele estiver diferente do código, ele está errado.

## Tokens

Toda cor, fonte e raio vem de uma variável. Cada cor tem um valor para o tema claro e outro para o escuro, e o tema escuro vale quando `<html>` tem `data-theme="dark"`.

| Grupo | Variáveis | Uso |
| --- | --- | --- |
| Neutros | `--bg`, `--ink`, `--ink-2`, `--ink-3`, `--ink-4` | Fundo e texto, do mais forte ao mais discreto |
| Linhas e fundos | `--line`, `--line-soft`, `--fill`, `--fill-soft` | Bordas, divisores e preenchimentos suaves |
| Marca | `--primary`, `--primary-fill`, `--accent`, `--cta`, `--cta-hover` | Item ativo, links, botão principal |
| Avisos | `--info-*`, `--tip-*`, `--warn-*`, `--danger-*`, `--note-*` | Fundo (`-bg`), borda (`-bd`) e ícone (`-ic`) de cada tipo |
| Código | `--code-bg`, `--code-ink`, `--t-k`, `--t-s`, `--t-n`, `--t-f`, `--t-c` | Bloco de código e realce de sintaxe |
| Fontes | `--font-head`, `--font-body`, `--font-mono` | Geist, Inter e IBM Plex Mono |
| Raios | `--radius-xs` (6), `-sm` (10), `-md` (12), `-lg` (16), `-pill` | Quanto maior a peça, maior o raio |

### Tipografia

| Papel | Fonte | Tamanho / linha |
| --- | --- | --- |
| Título da página (`.page-title`) | Geist 600 | 36 / 40 px |
| Resumo (`.lead`) | Inter 400 | 18 / 28 px |
| Título de seção (`h2`) | Geist 600 | 24 / 32 px |
| Subtítulo (`h3`) | Geist 600 | 20 / 28 px |
| Texto | Inter 400 | 16 / 28 px |
| Tabela e interface | Inter 400 e 500 | 14 / 22 px |
| Código | IBM Plex Mono 400 | 14 / 24 px |

A coluna de leitura tem no máximo 46 rem (cerca de 70 caracteres por linha).

## Componentes

Todos estão no catálogo, com o HTML pronto para copiar (botão "Ver HTML" abaixo de cada exemplo).

- **Navegação:** botões (`.btn-cta`, `.btn-soft`, `.icon-btn`, `.fb-btn`), seletor de idioma (`.lang`), menu lateral (`.side-*`), abas de área (`.tabs-row`), busca (`.search`)
- **Conteúdo:** cabeçalho da página, texto (`.prose`), código (`.code`), tabelas (`.table-wrap`), avisos (`.callout`), cartões (`.card`), endpoint (`.endpoint`), accordion (`details`), moldura de mídia (`.frame`), página em branco (`.empty`), fim da página (`.feedback`, `.pager`)

### Contrato do HTML

O `ds.js` completa o HTML a partir de atributos. Escreva só isto e ele cuida do resto:

| Escreva | O script faz |
| --- | --- |
| `<i data-ico="chevron"></i>` | Troca por um ícone SVG com as mesmas classes |
| `<span class="card-icon" data-ico="boxes"></span>` | Coloca o ícone dentro do elemento |
| `<div class="callout" data-kind="warn">` | Insere o ícone do tipo de aviso |
| `<div class="code" data-tabs>` com `.code-tab` e vários `<pre>` | Liga cada aba ao seu bloco |
| `<button class="copy"></button>` | Põe o ícone e copia o código visível |
| `<button data-theme-toggle>` | Alterna claro e escuro e guarda a escolha |
| `<button data-menu-toggle>` | Abre e fecha o menu lateral no celular |
| `<button data-open-search>` | Abre a busca (também `Ctrl K` e `/`) |
| `<aside id="toc" data-toc>` | Monta "Nesta página" e acompanha a rolagem |

Ícones disponíveis: veja `DS.icons` no console ou o objeto `ICON` em `js/ds.js`. Para um ícone novo, adicione o caminho lá, com traço de 1,75 px em uma grade de 24.

Ao escolher um idioma, o menu dispara o evento `ds:lang` no `document` com o código (`en`, `it`, `pt`). A troca do conteúdo é responsabilidade do site:

```js
document.addEventListener('ds:lang', e => setLanguage(e.detail));
```

## Regras

**Faça**

- Comece pelo template e troque só o conteúdo.
- Use variáveis de `tokens.css` para toda cor, raio e fonte.
- Escreva títulos em frase, com maiúscula só na primeira letra.
- Dê um resumo a toda página de conteúdo.
- Escolha o tipo de aviso pelo efeito para quem lê.
- Escreva texto alternativo em toda imagem.

**Não faça**

- Escrever cor em hexadecimal ou `rgb()` dentro de uma página.
- Criar um componente parecido com um que já existe.
- Usar o índigo como fundo fora do botão principal.
- Pular níveis de título: `h2` vai direto para `h3`.
- Colocar mais de um botão principal na mesma área da tela.
- Estilizar com o atributo `style`, salvo valores de demonstração.

### Acessibilidade

O que o design system já garante, e que você mantém ao seguir o template:

- Link "Ir para o conteúdo" no início da página.
- Foco visível em todo elemento interativo.
- Página atual marcada com `aria-current="page"`, aba de código com `aria-selected`.
- Botões só com ícone sempre têm `aria-label`.
- Movimento reduzido: transições desligam com `prefers-reduced-motion`.
- Texto corrido (`--ink`, `--ink-2`, `--ink-3`), links e botão principal passam de 4,5:1 nos dois temas.

Pontos conhecidos, herdados do protótipo e ainda sem correção:

- `--ink-4` tem 2,6:1 no tema claro e 4,1:1 no escuro. Use só em ícones e detalhes decorativos, nunca em texto que a pessoa precisa ler.
- No tema claro, três cores do realce de código ficam abaixo de 4,5:1: `--t-s` (3,3:1), `--t-c` (3,2:1) e `--t-n` (3,0:1). Se o design system for revisado para acessibilidade, comece por elas.

### Telas

| Largura | O que muda |
| --- | --- |
| Acima de 1280 px | Três colunas: menu, artigo e índice da página |
| 1024 a 1279 px | O índice vira um bloco recolhido no topo do artigo |
| Abaixo de 1024 px | O menu vira gaveta e as abas de área passam para dentro dela |
| Abaixo de 640 px | Cartões e pager em uma coluna; some o botão "Copiar página" |

## Origem

Este design system foi extraído de `doc/site-prototype/index.html`, o protótipo aprovado. O protótipo ainda tem o próprio CSS embutido e não importa esta pasta; quando o site de verdade for construído, ele deve usar `css/design-system.css` e `js/ds.js` e deixar de ter estilo próprio.
