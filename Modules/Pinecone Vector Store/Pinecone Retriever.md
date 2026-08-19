# Classe `PineconeRetriever`

## Visão Geral

A classe `PineconeRetriever` é um serviço especializado em operações de recuperação (retrieval) de vetores armazenados em um índice Pinecone. Ela serve como uma camada de abstração para facilitar buscas por similaridade vetorial e consultas baseadas em metadados, encapsulando a interação direta com o índice e o mecanismo de embeddings.

Este componente é crucial para aplicações que trabalham com dados vetoriais, como sistemas de recomendação, recuperação semântica ou análise de similaridade textual, pois garante uma API simples e segura para realizar consultas complexas no Pinecone. Pode ser utilizado em pipelines de processamento de linguagem natural, sistemas de busca ou qualquer aplicação que precise recuperar vetores próximos a partir de consultas textuais ou filtros por metadata.

## Fluxo de Execução

1. **Inicialização**: Cria uma instância do `PineconeRetriever`, recebendo opcionalmente um cliente Pinecone configurado. Caso não fornecido, um cliente padrão é criado internamente; durante essa fase, são inicializados componentes essenciais como índice, embeddings e namespace.

2. **Busca por Similaridade (`similarity_search`)**:
    - Recebe um texto de consulta, quantidade máxima de resultados (`k`) e filtros opcionais.
    - Valida os parâmetros e gera o embedding do texto.
    - Constrói filtros compatíveis com Pinecone para a consulta.
    - Executa a consulta vetorial no índice, recuperando vetores similares.
    - Normaliza e formata a resposta, retornando uma lista de documentos com texto, metadados e scores.

3. **Recuperação por Metadata (`get_all_docs_by_metadata`)**:
    - Aceita chave e valor (ou lista de valores) para filtro por metadata, além de parâmetros de paginação.
    - Utiliza um vetor "dummy" para satisfazer a API Pinecone que exige vetor, realizando a busca usando apenas o filtro.
    - Executa consultas paginadas para recuperar todos os vetores que satisfaçam o filtro.
    - Retorna uma lista completa dos vetores com metadados e ids, porém o score não possui significado semântico aqui.

## Tabela de Métodos da Classe

| Método                 | Descrição                                             |
|------------------------|------------------------------------------------------|
| `__init__`             | Inicializa o retriever configurando dependências.   |
| `similarity_search`    | Realiza busca por similaridade vetorial com filtro.  |
| `get_all_docs_by_metadata` | Recupera vetores por filtro de metadata paginadamente.|

## Pontos Importantes da Arquitetura e Insights

- **Separação de Responsabilidades**: A classe atua exclusivamente como serviço de consulta, desacoplando a lógica de embedding e comunicação com Pinecone via um cliente especializado.
- **Uso de Decorator para Tracing**: O decorator `@trace` é aplicado em métodos públicos para padronizar logging e captura de exceções, garantindo rastreabilidade e fácil debugging.
- **Normalização e Abstração**: Os resultados brutos do Pinecone são transformados para um formato uniforme consumido pela aplicação, escondendo complexidades do índice.
- **Paginação Explícita**: A recuperação por metadata implementa paginação manual para assegurar que todos os resultados são obtidos, contornando limitações da API Pinecone.
- **Filtro Dinâmico e Flexível**: Suporte para filtros simples a partir de um dicionário, traduzindo para operadores `$eq` e `$in` do Pinecone, facilitando buscas parametrizadas.
- **Dependências Utilizadas**: A classe utiliza `PineconeClient` (para acesso ao índice e embeddings) e `PineconeVectorStoreConfig` (para configurações de batch e dimensão).

# Descrição da Classe e Métodos

## Classe `PineconeRetriever`

### Descrição

O `PineconeRetriever` é responsável por realizar consultas eficientes e seguras em índices vetoriais gerenciados pelo Pinecone. Ele disponibiliza mecanismos tanto para buscas por similaridade textual, transformando texto em vetores e consultando o índice, quanto para recuperações baseadas em metadados, com paginação automática e filtragem compatível.

### Argumentos do Construtor

| Argumento | Tipo                 | Descrição                                                                                                                      | Valor Padrão |
|-----------|----------------------|--------------------------------------------------------------------------------------------------------------------------------|--------------|
| client    | Optional[PineconeClient] | Instância do cliente Pinecone já configurada com índice, embeddings e namespace; se omitido cria um cliente padrão automático. | None         |

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa uma instância do `PineconeRetriever`, configurando as dependências essenciais como índice, embeddings e namespace, usando o `PineconeClient` fornecido ou criando um padrão. Também carrega configurações como tamanho de lote (batch_size) e dimensão dos vetores.

### Argumentos

- client (Optional[PineconeClient]): Objeto cliente configurado; pode ser None.

### Retornos

- Não retorna valor.

### Raises

- ValueError: se o client for None e não puder ser criado o padrão.

### Exemplos

```python
# Criando retriever com cliente padrão
retriever = PineconeRetriever()

# Criando retriever com cliente customizado
client = PineconeClient()
retriever = PineconeRetriever(client)
```

---

### 2. `similarity_search`

### Descrição

Executa busca por similaridade vetorial a partir de um texto consulta, retornando os documentos mais similares no índice Pinecone, podendo aplicar filtros por metadata para restringir resultados.

### Argumentos

- query (str): Texto base para busca por similaridade.
- k (int): Número máximo de resultados retornados. Default: 5.
- filter_search (Optional[Dict[str, Any]]): Dicionário para filtro por metadata, ex: {"file_id": "abc"} ou {"file_id": ["abc", "def"]}.

### Retornos

- List[Dict[str, Any]]: Lista de dicionários contendo id, texto (campo 'text' dos metadados), demais metadados e score.

### Raises

- ValueError: Se query vazia ou k <= 0.
- RuntimeError: Falha na geração do embedding, consulta ou processamento dos resultados.

### Exemplos

```python
results = retriever.similarity_search(
    query="Como funciona o sistema de recomendação?",
    k=3,
    filter_search={"category": "tutorial"}
)

for doc in results:
    print(f"ID: {doc['id']}, Score: {doc['score']}")
    print(f"Texto: {doc['text']}")
```

---

### 3. `get_all_docs_by_metadata`

### Descrição

Recupera todos os vetores do índice Pinecone que correspondam a um filtro de metadata, realizando consultas paginadas. Essa função não faz busca por similaridade, usa vetor "dummy" como exigido pela API e retorna os resultados brutos filtrados.

### Argumentos

- batch_size (int | None): Limite de resultados por página. Controla memória e latência. Usa o valor configurado se None.
- dimension (int | None): Dimensão do vetor (necessária para criar vetor dummy). Usa o valor configurado se None.
- target_key (str): Chave de metadata para filtrar (ex: "file_id"). Default: "file_id".
- target_value (Union[str, List[str]]): Valor ou lista de valores para filtro.

### Retornos

- List[Dict[str, Any]]: Lista contendo id, metadata e score dos vetores que satisfazem o filtro.

### Raises

- ValueError: Se target_value for vazio.
- RuntimeError: Falha na recuperação paginada.

### Exemplos

```python
all_vectors = retriever.get_all_docs_by_metadata(
    batch_size=100,
    target_key="user_id",
    target_value=["user1", "user2"]
)

print(f"Total vetores recuperados: {len(all_vectors)}")
for vector in all_vectors:
    print(vector["id"], vector["metadata"])
```

---

Esta documentação fornece uma visão clara do funcionamento e uso do `PineconeRetriever`, detalhando seu papel, metodologia de consulta e exemplos práticos para integração em sistemas que utilizem Pinecone para vetores.