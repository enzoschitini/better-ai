# Classe `PineconeEmbedding`

## Visão Geral

A classe `PineconeEmbedding` é uma implementação focada em facilitar o trabalho com vetores de embeddings baseados na biblioteca Pinecone, muito utilizada para armazenar e buscar vetores em alta escala. Ela oferece funcionalidades para dividir textos em pedaços menores, transformar esses pedaços em documentos estruturados com metadados, gerar vetores de embeddings a partir dos textos e gerenciar o armazenamento desses vetores em índices Pinecone.

Este serviço é ideal para aplicações que lidam com grandes volumes de dados textuais e precisam realizar buscas semânticas ou recomendações baseadas em embeddings. O uso típico envolve o processamento de texto bruto, geração de embeddings via OpenAI, armazenamento organizado e eficiente desses vetores, além da possibilidade de manutenção via remoção de vetores específicos.

## Fluxo de Execução

1. **Inicialização da Classe**: A classe é instanciada com um cliente Pinecone customizado ou padrão, configurando modelos de embedding, tamanhos de chunk, namespaces, e outros parâmetros de configuração carregados via ambiente ou arquivos.

2. **Geração de Vetores**:
    - Recebe um texto completo e metadados associados (ex: `file_id`).
    - O texto é dividido em pedaços menores respeitando limites de tamanho e sobreposição.
    - Cada pedaço vira um documento com metadados.
    - Os documentos são transformados em vetores embeddings por lotes (batch).
    - Os vetores são salvos no namespace principal do Pinecone, com opcional salvamento no namespace global para reutilização.

3. **Deleção de Vetores**:
    - Possibilita apagar vetores do Pinecone filtrando por um campo metadata e valor, no namespace especificado.
    - Handle de deleções em lotes para eficiência.
    - Garante rollback e logging para evitar inconsistências em caso de falhas.

4. **Monitoramento e Logs**:
    - Integração com sistema de tracing (`ApplicationTracing`) para debug detalhado das etapas.
    - Tratamento de exceções cuidadoso para informar erros ocorridos no processo.

## Tabela de Métodos da Classe

| Método           | Descrição                                      |
|------------------|------------------------------------------------|
| `__init__`       | Inicializa o serviço, configura cliente e parâmetros. |
| `embedding_document`| Cria e salva embeddings de texto dividido em chunks. |
| `delete_documents`| Deleta vetores no Pinecone com base em filtros metadata. |
| `split_text`     | Divide um texto longo em múltiplos pedaços.   |
| `build_documents` | Cria objetos Document com conteúdo e metadados. (método estático) |
| `generate_embeddings` | Gera as representações vetoriais a partir de textos.|

## Variáveis de Ambiente

- `OPENAI_EMBEDDING_MODEL`: Define o modelo de embedding da OpenAI a ser utilizado para gerar os vetores em caso de não fornecimento explícito.

## Pontos Importantes da Arquitetura e Insights

- **Herança e Reuso**: `PineconeEmbedding` herda de `EmbeddingHelpers`, separando a lógica de manipulação de texto e geração de embeddings do fluxo mais alto de armazenamento e gerenciamento.

- **Batching Inteligente**: A geração e deleção de embeddings são processadas em lotes configuráveis para balancear performance e uso de recursos.

- **Namespaces Separados**: A distinção entre namespace principal e global permite organização dos dados, possibilitando cenários de escopo isolado e compartilhado.

- **Logging e Tracing Profundos**: Integração com sistema de tracing customizado que possibilita depuração granular e monitoramento detalhado das operações.

- **Tratamento Robusto de Erros**: Rolback explícito em caso de falhas na inserção em lote garante a consistência do índice Pinecone.

- **Uso de OpenAIEmbeddings**: Abstração da geração dos embeddings via modelo OpenAI que pode ser trocado facilmente via variável de ambiente ou argumento.

- **Dependências Externas**: A classe depende da implementação de cliente Pinecone (`PineconeClient`), configuração (`PineconeVectorStoreConfig`) e da biblioteca LangChain para manipulação de documentos e embeddings.

---

# Descrição da Classe e Métodos

## Classe `PineconeEmbedding`

### Descrição

Classe para gerenciar a criação, armazenamento, e remoção de embeddings textuais utilizando Pinecone como serviço de vector search. Ela divide textos em pedaços, gera embeddings via OpenAI, e permite persistir esses vetores em namespaces configuráveis, facilitando integrações em sistemas que demandam busca semântica.

### Argumentos do Construtor

| Argumento           | Tipo               | Descrição                                                       | Valor Padrão  |
|---------------------|--------------------|----------------------------------------------------------------|---------------|
| `vector_client`      | Optional[PineconeClient] | Cliente Pinecone customizado para operações de vetor. Se não fornecido, cria um padrão. | None          |
| `embedding_model_name` | str               | Nome do modelo de embedding usado. Se None, busca variável ambiente `OPENAI_EMBEDDING_MODEL` ou padrão da config. | None          |
| `dimensions`        | int                | Dimensionalidade dos vetores, se não informado usa configuração padrão. | None          |

---

### 1. `__init__`

### Descrição

Inicializa o serviço de embeddings, configurando cliente Pinecone, parâmetros como chunk size, namespaces, modelo de embedding, e cria stores Pinecone globais e principais.

### Argumentos

- `vector_client` (Optional[PineconeClient]): cliente Pinecone para operações.
- `embedding_model_name` (str): nome do modelo de embedding.
- `dimensions` (int): dimensão dos vetores.

### Retornos

- Nenhum.

### Raises

- RuntimeError: Em falhas durante a inicialização.

### Exemplos

```python
service = PineconeEmbedding()
# ou com cliente customizado e modelo definido
service_custom = PineconeEmbedding(
    vector_client=my_pinecone_client,
    embedding_model_name="text-embedding-ada-002",
    dimensions=1536
)
```

---

### 2. `embedding_document`

### Descrição

Processa texto longo, divide em chunks, cria documentos associando metadados, gera embeddings para esses chunks em batches, e salva os vetores no Pinecone. Pode salvar cópias no namespace global para reaproveitamento.

### Argumentos

- `text` (str): texto completo para gerar vetores.
- `metadata` (dict): metadados para associar aos documentos vetoriais.
- `save_global` (bool): flag para salvar vetores também no namespace global.
- `batch_size` (int | None): tamanho do lote para geração dos embeddings.

### Retornos

- dict: Resultado com status, mensagens, e informações detalhadas sobre embeddings salvos, incluindo ids e contagem.

### Raises

- Não diretamente, erros são capturados e reportados no retorno com rollback.

### Exemplos

```python
response = service.embedding_document(
    text="Um texto muito longo que precisa ser dividido e vetorizado...",
    metadata={"file_id": "doc_001"},
    save_global=True,
    batch_size=50
)
if response["status"] == "success":
    print(f"Vetores salvos, batches: {response['embedding_informations']['batch_count']}")
else:
    print("Erro:", response["message"])
```

---

### 3. `delete_documents`

### Descrição

Remove vetores do índice Pinecone filtrando pelo valor de um campo metadata, dentro do namespace especificado. Executa deleções em batches para performance e segurança.

### Argumentos

- `target_feature` (str): campo metadata usado para filtro (ex: "file_id").
- `target_id` (str): valor que identifica os vetores para deletar.
- `namespace` (str): namespace Pinecone para executar a remoção.
- `features` (list): lista opcional de features válidas para validação do filtro.

### Retornos

- dict: Informações sobre quantidade de vetores deletados e namespace.

### Raises

- ValueError: se o `target_feature` não estiver dentro da lista `features` quando fornecida.
- RuntimeError: em caso de erro durante a remoção.

### Exemplos

```python
result = service.delete_documents(
    target_feature="file_id",
    target_id="doc_001",
    namespace="embedding_file"
)
print(f"Vectors deleted: {result['deleted_vectors']}")
```

---

### 4. `split_text`

### Descrição

Divide um texto em múltiplos pedaços menores, respeitando limites de tamanho e sobreposição para facilitar o processamento e geração de embeddings.

### Argumentos

- `text` (str): texto a ser dividido.
- `chunk_size` (int | None): tamanho desejado do chunk (opcional).
- `chunk_overlap` (int | None): sobreposição entre chunks (opcional).

### Retornos

- List[str]: lista com os pedaços de texto gerados.

### Raises

- RuntimeError: se falhar ao dividir o texto.

### Exemplos

```python
chunks = service.split_text("Texto muito longo...", chunk_size=200, chunk_overlap=40)
print(f"Quantidade de chunks gerados: {len(chunks)}")
```

---

### 5. `build_documents` (método estático)

### Descrição

Cria objetos Document (da LangChain) a partir de pedaços de texto, associando um dicionário de metadados a cada documento.

### Argumentos

- `chunks` (List[str]): lista de textos fragmentados.
- `metadata` (Dict[str, Any]): metadados para anexar em cada documento.

### Retornos

- List[Document]: lista de documentos prontos para ingesta.

### Raises

- RuntimeError: se falhar ao construir os Document.

### Exemplos

```python
documents = PineconeEmbedding.build_documents(
    ["texto 1", "texto 2"],
    {"file_id": "abc123", "created_at": "2024-06-01"}
)
for doc in documents:
    print(doc.metadata)
```

---

### 6. `generate_embeddings`

### Descrição

Gera os embeddings vetoriais para uma lista de textos, utilizando o modelo configurado.

### Argumentos

- `texts` (List[str]): lista de frases ou documentos para transformar em vetores.

### Retornos

- List[List[float]]: lista de vetores numéricos correspondentes aos textos.

### Raises

- RuntimeError: se ocorrer erro na geração dos embeddings.

### Exemplos

```python
embeddings = service.generate_embeddings([
    "primeiro texto",
    "segundo texto"
])
print(f"Embedding do primeiro texto tem dimensão {len(embeddings[0])}")
```

---

# Exemplo de uso completo

```python
pine_client = PineconeClient(index_name="exemplo-index", main_namespace="embeddings")
service = PineconeEmbedding(vector_client=pine_client, embedding_model_name="text-embedding-ada-002")

texto = "Este é um exemplo de texto que será dividido, embeddado e armazenado."

response = service.embedding_document(
    text=texto,
    metadata={"file_id": "exemplo_12345"},
    save_global=True
)

if response['status'] == "success":
    print("Embeddings gerados e salvos com sucesso!")
else:
    print("Falha ao salvar embeddings:", response["message"])
```

---

Essa documentação detalha o funcionamento do `PineconeEmbedding`, destacando seu uso prático, os métodos disponíveis e dicas para integração eficiente com sistemas de vetorização baseados em Pinecone e OpenAI.