# **Gerador de Conteúdo com IA · O Boticário**

---

Geração de conteúdo de marca em escala — sem perder identidade e sem inventar informação.

> *Projeto independente, de caráter demonstrativo e educacional, sem vínculo oficial com o Grupo O Boticário. Os catálogos foram usados apenas como base de conhecimento para o estudo.*
> 

## O problema

Marcas precisam produzir muito conteúdo (posts, descrições, campanhas) com rapidez, mas dois obstáculos travam o uso de IA generativa nesse cenário:

- **Tom fora da marca** — modelos genéricos escrevem "bonito", mas não soam como a marca.
- **Alucinação** — a IA descreve produtos que não conhece, criando informações falsas.

Este projeto resolve os dois: cada texto nasce **ancorado em uma base real** de **catálogos do Grupo O Boticário**, então o resultado é fiel à marca e aos produtos — com a agilidade da IA.

---

## Como funciona

O gerador usa uma arquitetura chamada RAG (Retrieval-Augmented Generation), que combina uma base de conhecimento própria com um modelo de linguagem. O funcionamento acontece em duas etapas.

!fluxo_rag_gerador_conteudo_v2.png

### Como funciona por trás dos panos (geração)

A cada pedido, o sistema monta dinamicamente uma série de prompts. O conteúdo desses prompts muda conforme as configurações escolhidas pelo usuário, combinadas com system prompts fixos que definem o comportamento e o tom da marca. Junto vai um schema Pydantic, que descreve o formato exato que a resposta deve ter — é o que garante uma saída estruturada e previsível, em vez de texto solto.

Em seguida é feita a busca semântica no Pinecone, recuperando os trechos mais relevantes dos catálogos para servir de contexto. O modelo então gera a quantidade de conteúdos que o usuário pediu (X itens). A resposta passa por um output parser baseado no mesmo schema Pydantic, que valida e transforma tudo em uma lista de objetos JSON — um por conteúdo gerado.

### 1. Indexação (feita uma vez)

---

A primeira é a indexação, feita uma única vez. Os PDFs de catálogos são processados: o texto é extraído de cada arquivo, quebrado em trechos menores (chunks) e convertido em embeddings — representações numéricas (vetores) que capturam o significado do texto. Esses vetores ficam armazenados no Pinecone, uma vector store que permite busca por similaridade de significado, e não apenas por palavra-chave.

Os catálogos em PDF são processados e transformados em uma base de conhecimento consultável:

1. **Extração** — o texto é lido de cada um dos PDFs.
2. **Chunking** — o conteúdo é dividido em trechos menores.
3. **Embeddings** — cada trecho vira um vetor que representa seu *significado*.
4. **Armazenamento** — os vetores são indexados no **Pinecone** (vector store).

### 2. Geração (a cada pedido)

---

A segunda é a geração, que roda a cada pedido. Quando você digita um objetivo (por exemplo, "post para Instagram sobre um perfume amadeirado"), essa instrução também vira um vetor e é comparada com a base no Pinecone. O sistema recupera os trechos mais relevantes dos catálogos e os entrega ao modelo de linguagem junto com as regras de tom e identidade da marca. O modelo então escreve o conteúdo final ancorado em informações reais dos produtos, evitando invenções e mantendo consistência.

1. **Prompts dinâmicos** — o sistema monta os prompts em tempo real, combinando as **configurações do usuário**, **system prompts** de marca e um **schema Pydantic** que define o formato exato da saída.
2. **Busca semântica** — recupera do Pinecone os trechos mais relevantes por *significado*, não por palavra-chave.
3. **Geração em lote** — o modelo gera a quantidade de conteúdos pedida pelo usuário (N itens).
4. **Output parser** — valida a resposta com o mesmo schema Pydantic e a converte em uma **lista de JSONs**.
5. **Renderização** — o front em **Streamlit** percorre a lista e formata cada item em **Markdown**.

---

## Decisões de engenharia que fazem diferença

Isto não é "uma chamada de LLM com um prompt bonito". É um pipeline de produção com escolhas deliberadas:

- **Base de conhecimento própria (RAG).** A busca semântica no Pinecone entende intenção: peça *"um perfume amadeirado para o dia a dia"* e o sistema recupera os produtos certos mesmo que essas palavras exatas não estejam no catálogo. É isso que **elimina a alucinação** e garante fidelidade à marca.
- **Saída estruturada e confiável (Pydantic nas duas pontas).** O mesmo schema **instrui** o modelo *e* **valida** a resposta. Isso transforma o texto imprevisível de uma LLM em **dados garantidos**, sempre no mesmo formato — a diferença entre um protótipo frágil e um sistema reaproveitável.
- **Prompts orientados a configuração.** Os prompts se montam a partir das opções do usuário + system prompts de marca. O mesmo motor atende objetivos, formatos e tons diferentes **sem reescrever código**.
- **Geração em lote.** O usuário pede N variações e recebe N conteúdos já validados, prontos para escolher — pensado para uso real, não para uma demo de uma frase.

---

## Sobre os dados

A base foi construída a partir de catálogos de produtos do Grupo O Boticário, cobrindo perfumaria, maquiagem, cuidados com a pele e cabelo, entre outras categorias. Esse material traz nomes de produtos, descrições, notas olfativas, benefícios e linguagem de marca — exatamente o tipo de informação que o gerador precisa para produzir textos alinhados e específicos, em vez de genéricos.

Ao indexar esse conteúdo em uma vector store, o sistema consegue "entender" o portfólio: ao pedir um post sobre um perfume floral, ele busca semanticamente os produtos e descrições que combinam com esse conceito, mesmo que a palavra exata não apareça no seu pedido. É isso que dá precisão e fidelidade à marca ao conteúdo gerado.

---

## Stack

| Camada | Tecnologia |
| --- | --- |
| Modelo de linguagem | LLM (via API) |
| Recuperação | Pinecone (vector store) |
| Estrutura de dados | Pydantic (schema + validação) |
| Interface | Streamlit |
| Fonte de dados | Catálogos |

---

Em resumo: capacidade de tirar LLMs do *"brinquedo de prompt"* e colocá-las dentro de um produto que uma marca poderia usar de verdade.