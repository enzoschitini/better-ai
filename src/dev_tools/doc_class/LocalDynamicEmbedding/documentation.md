# Classe `LocalDynamicEmbedding`

## Visão Geral

A classe `LocalDynamicEmbedding` oferece uma pipeline local para o processamento de textos, onde o texto é dividido em pedaços (chunks), cada pedaço é convertido em um vetor de embedding, e esses vetores são armazenados para posterior recuperação por similaridade. Essa pipeline suporta diferentes provedores de embeddings, incluindo provedores reais (como OpenAI e Huggingface) e embeddings falsos para teste, facilitando a experimentação sem necessidade de APIs externas.

O principal problema resolvido é o de trabalhar com textos longos para tarefas de recuperação e busca sem depender exclusivamente de serviços externos, otimizando a divisão do texto e o cálculo dos embeddings de forma modular e configurável. Além disso, fornece uma API fluente que permite configurar passo a passo o provedor de embeddings, o splitter de texto, e a quantidade de resultados recuperados.

Na prática, ela pode ser usada para criar sistemas de busca local em documentos, chatbots que precisam entender documentos ou bases de conhecimento, e para prototipagem rápida, onde se deseja trocar facilmente o provedor de embeddings ou parâmetros de chunking.

---

## Fluxo de Execução

1. **Configuração do pipeline**: Inicialmente, o usuário cria uma instância de `LocalDynamicEmbedding` e configura os componentes necessários usando o modelo fluente:
   - Define o provedor de embeddings com `with_provider()` ou métodos convenientes como `from_openai_embeddings()`.
   - Ajusta o splitter de texto com `with_splitter()`.
   - Configura quantos resultados quer recuperar com `with_top_k()`.
   
2. **Processamento do texto**: O método `process_text(texto)` recebe um texto de entrada, o divide em chunks baseados nos parâmetros definidos, gera embeddings para cada chunk e armazena tudo em um índice vetorial FAISS em memória.

3. **Recuperação de informação**: Com o índice criado, chama-se `retrieve(query)` para buscar os chunks mais similares à consulta, retornando os textos, metadados, scores de similaridade, e opcionalmente os vetores de embedding.

4. **Gerenciamento e consulta dos chunks**: O usuário pode acessar os chunks armazenados via propriedades e métodos como `chunks`, `get_chunks()` ou `get_chunk(index)` para explorar o conteúdo e os vetores.

5. **Reconfiguração e limpeza**: Caso deseje modificar a configuração ou resetar o pipeline, `clear()` limpa o estado, permitindo reconfigurações sem criar nova instância.

---

## Tabela de Métodos da Classe

| Método                 | Descrição                                          |
|------------------------|----------------------------------------------------|
| `__init__`             | Construtor que inicializa parâmetros e estado.    |
| `with_embeddings`      | Define instância customizada de embeddings.        |
| `with_fake_embeddings` | Configura o uso de embeddings falsos.              |
| `with_provider`        | Configura o provedor de embeddings por nome.       |
| `with_splitter`        | Ajusta parâmetros do splitter (chunk size, overlap).|
| `with_top_k`           | Define a quantidade de resultados na recuperação.  |
| `from_provider`        | Instancia a classe com provedor de embeddings.     |
| `from_openai_embeddings`| Cria instância com embeddings OpenAI.              |
| `from_huggingface_embeddings`| Cria instância com embeddings Huggingface.     |
| `from_fake_embeddings` | Cria instância com embeddings falsos.              |
| `process_text`         | Processa o texto, dividindo, calculando embeddings e armazenando.|
| `retrieve`             | Recupera os chunks mais relevantes para uma consulta.|
| `as_retriever`         | Retorna um objeto para realizar buscas externas.   |
| `chunks`               | Propriedade que retorna lista de chunks armazenados.|
| `get_chunks`           | Retorna chunks em forma de dicionários.            |
| `get_chunk`            | Retorna um chunk específico pelo índice.           |
| `total_chunks`         | Retorna a quantidade total de chunks armazenados.  |
| `clear`                | Limpa o estado para nova configuração ou reuso.    |

---

## Pontos Importantes da Arquitetura e Insights

- **Builder Pattern / Fluent API**: A classe adota um padrão builder para configuração fluente, permitindo que o usuário configure o pipeline passo a passo antes do processamento, o que aumenta a flexibilidade na construção do fluxo.

- **Lazy Initialization**: Componentes como embeddings e splitter são inicializados somente quando necessários, permitindo mudanças e configurações antes do processamento ser efetivado.

- **Separação de Responsabilidades**: A criação de embeddings é delegada à `EmbeddingFactory`, que abstrai diferentes provedores (OpenAI, Huggingface, fake), facilitando extensões e manutenções.

- **Indexação Local com FAISS**: Armazena os embeddings em um índice FAISS local para busca rápida em memória, o que é eficiente para protótipos e aplicações em menor escala sem infraestrutura externa.

- **Gerenciamento de Estado e Guard Rails**: Após o processamento (`process_text`), a reconfiguração dos principais componentes é bloqueada para evitar inconsistências, e o `clear()` permite resetar a pipeline.

- **Classe Auxiliar `Chunk`**: Representa cada pedaço do texto com seu conteúdo, índice, metadados e vetor de embedding, facilitando o acesso às informações de forma estruturada.

- **Inspeção Completa dos Chunks**: Cada chunk permite acessar facilmente seu texto, metadata, vetor de embedding, comprimento em caracteres e dimensão do embedding, atendendo necessidades de depuração e análise.

- **Uso de .env e dotenv**: Carrega variáveis de ambiente para autenticações (ex: OpenAI), embora essa responsabilidade fique nas bibliotecas de embeddings.

---

# Descrição da Classe e Métodos

## Classe `LocalDynamicEmbedding`

### Descrição

Classe para montar uma pipeline local de chunking, geração de embeddings e recuperação via busca por similaridade. Possui suporte a múltiplos provedores de embeddings configurados via API fluente, possibilita ajustar como o texto é dividido e como os resultados são selecionados, operando localmente com FAISS para indexação e busca.

Permite processar textos longos dividindo-os em pedaços, calcular embeddings para cada pedaço, armazenar esses vetores e recuperá-los com consultas, tudo de forma modular e reaproveitável.

### Argumentos do Construtor

| Argumento      | Tipo                | Descrição                                                                  | Valor Padrão          |
|----------------|---------------------|----------------------------------------------------------------------------|----------------------|
| embeddings     | Optional[Embeddings]| Instância customizada do objeto de embeddings a ser utilizado.            | None (usa fake interno)|
| size           | int                 | Dimensão do vetor de embedding (usada para fake embeddings).               | 384                  |
| chunk_size     | int                 | Número máximo de caracteres por pedaço ao dividir o texto.                 | 500                  |
| chunk_overlap  | int                 | Quantidade de sobreposição entre pedaços para manter contexto.             | 50                   |
| top_k          | int                 | Número de resultados superiores a serem retornados na recuperação.         | 4                    |
| separators     | Optional[List[str]] | Lista de separadores usados para divisão do texto (ex: "\n\n", "\n", etc.)| Lista padrão definida |

---

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa o pipeline com os parâmetros de chunking, embeddings e recuperação, configurando estado inicial e preparando atributos para lazy loading.

### Argumentos

- embeddings (Optional[Embeddings]): Instância de embeddings personalizada, opcional.
- size (int): Tamanho do vetor de embedding para fake embeddings.
- chunk_size (int): Tamanho máximo do chunk.
- chunk_overlap (int): Sobreposição entre chunks.
- top_k (int): Quantidade de resultados a retornar.
- separators (Optional[List[str]]): Separadores usados para dividir o texto.

### Retornos

- Não retorna valor (None).

### Raises

- Não especificados.

### Exemplos

```python
pipeline = LocalDynamicEmbedding(chunk_size=1000, top_k=3)
```

---

### 2. `with_embeddings`

### Descrição

Define uma instância personalizada de embeddings para a pipeline antes de qualquer processamento.

### Argumentos

- embeddings (Embeddings): Instância de embeddings a ser usada.

### Retornos

- LocalDynamicEmbedding: Retorna self para permitir encadeamento de chamadas.

### Raises

- RuntimeError: Caso seja chamada após iniciar o processamento ou embeddings invalidas.

### Exemplos

```python
pipeline = LocalDynamicEmbedding().with_embeddings(custom_embeddings)
```

---

### 3. `with_fake_embeddings`

### Descrição

Configura o pipeline para utilizar embeddings falsos, com possibilidade de definição do tamanho do vetor.

### Argumentos

- size (Optional[int]): Tamanho da dimensão dos embeddings falsos.

### Retornos

- LocalDynamicEmbedding: Retorna self para encadeamento.

### Raises

- RuntimeError: Se o tamanho for inválido ou ocorrer erro interno.

### Exemplos

```python
pipeline = LocalDynamicEmbedding().with_fake_embeddings(size=128)
```

---

### 4. `with_provider`

### Descrição

Configura o provedor de embeddings pelo nome e parâmetros específicos (ex: "openai", "huggingface", "fake").

### Argumentos

- provider (str): Nome do provedor.
- **kwargs: Parâmetros adicionais para o provedor.

### Retornos

- LocalDynamicEmbedding: Retorna self para encadeamento.

### Raises

- RuntimeError: Se o provedor não puder ser configurado ou instanciado.

### Exemplos

```python
pipeline = LocalDynamicEmbedding().with_provider("openai", model="text-embedding-3-large")
```

---

### 5. `with_splitter`

### Descrição

Configura os parâmetros do splitter de texto: tamanho do chunk, sobreposição entre chunks e separadores.

### Argumentos

- chunk_size (Optional[int]): Tamanho máximo do chunk.
- chunk_overlap (Optional[int]): Sobreposição entre chunks.
- separators (Optional[List[str]]): Separadores usados para divisão.

### Retornos

- LocalDynamicEmbedding: Retorna self para encadeamento.

### Raises

- RuntimeError: Se chamada após começar a processar texto.

### Exemplos

```python
pipeline = LocalDynamicEmbedding().with_splitter(chunk_size=1000, chunk_overlap=100)
```

---

### 6. `with_top_k`

### Descrição

Define quantos resultados top serão retornados nas buscas.

### Argumentos

- top_k (int): Número de top resultados.

### Retornos

- LocalDynamicEmbedding: Retorna self para encadeamento.

### Raises

- Não.

### Exemplos

```python
pipeline = LocalDynamicEmbedding().with_top_k(10)
```

---

### 7. `from_provider`

### Descrição

Membro de classe que cria uma instância pré-configurada para um provedor qualquer com parâmetros de splitter e top_k.

### Argumentos

- provider (str): Nome do provedor.
- chunk_size (int): Tamanho do chunk.
- chunk_overlap (int): Sobreposição dos chunks.
- top_k (int): Quantidade de resultados a retornar.
- separators (Optional[List[str]]): Separadores para divisão.
- **provider_kwargs: Argumentos para criação do provedor.

### Retornos

- LocalDynamicEmbedding: Instância configurada.

### Raises

- Não documentado.

### Exemplos

```python
pipeline = LocalDynamicEmbedding.from_provider("huggingface", model="all-MiniLM-L6-v2")
```

---

### 8. `from_openai_embeddings`

### Descrição

Cria instancia com embeddings OpenAI já configurado, pode customizar modelo e parâmetros de chunk.

### Argumentos

- model (str): Modelo OpenAI.
- chunk_size (int): Tamanho do chunk.
- chunk_overlap (int): Sobreposição dos chunks.
- top_k (int): Número de resultados.
- separators (Optional[List[str]]): Separadores.
- **kwargs: Parâmetros extras para o provider.

### Retornos

- LocalDynamicEmbedding: Instância configurada OpenAI.

### Exemplos

```python
pipeline = LocalDynamicEmbedding.from_openai_embeddings(model="text-embedding-3-large")
```

---

### 9. `from_huggingface_embeddings`

### Descrição

Cria instância configurada para usar embeddings Huggingface.

### Argumentos

- model (str): Modelo Huggingface.
- chunk_size (int), chunk_overlap (int), top_k (int), separators (Optional[List[str]]), **kwargs.

### Retornos

- LocalDynamicEmbedding: Instância configurada Huggingface.

### Exemplos

```python
pipeline = LocalDynamicEmbedding.from_huggingface_embeddings()
```

---

### 10. `from_fake_embeddings`

### Descrição

Cria instância para uso de embeddings falsos, com tamanho parametrizado.

### Argumentos

- size (int): Tamanho dos embeddings fake.
- chunk_size (int), chunk_overlap (int), top_k (int), separators (Optional[List[str]]).

### Retornos

- LocalDynamicEmbedding: Instância configurada com embeddings fake.

### Exemplos

```python
pipeline = LocalDynamicEmbedding.from_fake_embeddings(size=256)
```

---

### 11. `process_text`

### Descrição

Processa um texto, dividindo em chunks, calculando embeddings, armazenando chunks e adicionando ao índice FAISS.

### Argumentos

- text (str): Texto a processar (não pode ser vazio).
- metadata (Optional[dict]): Metadados associados ao texto.

### Retornos

- int: Quantidade de chunks criados.

### Raises

- RuntimeError: Se texto vazio ou erro no processamento.

### Exemplos

```python
num_chunks = pipeline.process_text("Texto extenso a ser processado", metadata={"source": "documento"})
print(f"{num_chunks} chunks criados.")
```

---

### 12. `retrieve`

### Descrição

Realiza busca por similaridade no índice retornando os melhores chunks para uma consulta.

### Argumentos

- query (str): Consulta para busca.
- top_k (Optional[int]): Quantidade máxima de resultados (override do definido).
- include_embedding (bool): Se inclui vetores de embedding no resultado.

### Retornos

- List[Dict]: Lista de resultados com conteúdo, score, metadados, e opcionalmente embedding.

### Raises

- RuntimeError: Se ainda não processou texto.

### Exemplos

```python
resultados = pipeline.retrieve("consulta de teste", top_k=3, include_embedding=True)
for r in resultados:
    print(r["content"], r["score"])
```

---

### 13. `as_retriever`

### Descrição

Retorna um objeto `VectorStoreRetriever` configurado para fazer consultas ao índice.

### Argumentos

- **kwargs: Parâmetros adicionais para configuração do retriever.

### Retornos

- VectorStoreRetriever: Objeto para realizar consultas.

### Raises

- RuntimeError: Se pipeline não estiver processada.

### Exemplos

```python
retriever = pipeline.as_retriever()
docs = retriever.get_relevant_documents("consulta")
```

---

### 14. `chunks`

### Descrição

Propriedade que retorna a lista com todos os objetos `Chunk` armazenados.

### Argumentos

- Nenhum.

### Retornos

- List[Chunk]: Lista dos chunks.

### Exemplos

```python
for chunk in pipeline.chunks:
    print(chunk.content)
```

---

### 15. `get_chunks`

### Descrição

Retorna todos os chunks como dicionários, com opção de incluir os embeddings.

### Argumentos

- include_embedding (bool): Define se o vetor embedding deve ser incluído.

### Retornos

- List[dict]: Lista de dicionários representando chunks.

### Exemplos

```python
chunks_data = pipeline.get_chunks(include_embedding=False)
```

---

### 16. `get_chunk`

### Descrição

Obtém um chunk específico pelo índice.

### Argumentos

- index (int): Índice do chunk desejado.

### Retornos

- Optional[Chunk]: O chunk correspondente, ou None se não existir.

### Exemplos

```python
chunk = pipeline.get_chunk(0)
print(chunk.content if chunk else "Chunk não encontrado")
```

---

### 17. `total_chunks`

### Descrição

Propriedade que retorna o total de chunks processados e armazenados.

### Argumentos

- Nenhum.

### Retornos

- int: Quantidade total de chunks.

---

### 18. `clear`

### Descrição

Limpa todo o estado da pipeline, incluindo chunks e índice, permitindo reconfiguração.

### Argumentos

- Nenhum.

### Retornos

- LocalDynamicEmbedding: Retorna self para encadeamento.

### Exemplos

```python
pipeline.clear()
```

---

# Classe Auxiliar `Chunk`

### Descrição

Representa um pedaço (chunk) do texto original com seu conteúdo, metadados e vetor de embedding, permitindo fácil inspeção dos dados gerados no pipeline.

### Argumentos do Construtor

| Argumento | Tipo       | Descrição                          | Valor Padrão |
|-----------|------------|----------------------------------|--------------|
| index     | int        | Índice do chunk no texto original|              |
| content   | str        | Conteúdo de texto do chunk       |              |
| metadata  | dict       | Metadados associados             |              |
| embedding | List[float]| Vetor de embedding do chunk      | []           |

### Propriedades

- `length`: Retorna número de caracteres no conteúdo do chunk.
- `dim`: Retorna dimensão do vetor de embedding.

### Métodos

- `to_dict(include_embedding=True)`: Retorna dicionário representando o chunk, incluindo embeddings opcionalmente.

### Exemplos

```python
chunk = Chunk(0, "Olá mundo", {"source": "doc1"}, [0.1, 0.2, 0.3])
print(chunk.length)  # 9
print(chunk.to_dict(include_embedding=False))  # {'index': 0, 'content': 'Olá mundo', ...}
```

---

Dessa forma, a `LocalDynamicEmbedding` oferece uma pipeline modular, configurável e eficiente para lidar com embeddings locais em texto, sendo ideal para desenvolvedores que buscam controle total do fluxo de pré-processamento e recuperação, além de facilitar trocas rápidas entre provedores de embeddings e ajustes nos parâmetros de chunking.