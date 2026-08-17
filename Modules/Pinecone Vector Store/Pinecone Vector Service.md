# Classe `PineconeVectorService`

## Visão Geral

A classe `PineconeVectorService` é um serviço responsável por transformar textos em vetores de alta dimensão para armazenamento e pesquisa eficiente em bancos de dados vetoriais, especificamente utilizando a infraestrutura do Pinecone. Ela resolve o problema de manipular, armazenar e buscar grandes volumes de texto processados em forma de embeddings, permitindo aplicações avançadas em processamento de linguagem natural, como busca semântica, recomendação e análise de similaridade.

Na prática, a classe divide o texto em partes menores (chunks), gera embeddings para essas partes usando modelos pré-treinados (por exemplo, da OpenAI), e salva esses vetores em namespaces organizados para posteriores buscas ou remoções. Ela suporta operações robustas como batch processing, rollback em caso de falhas e filtros para remoção condicional de documentos. Assim, é ideal para desenvolvedores que precisam estruturar bases de dados vetoriais escaláveis e confiáveis com funcionalidades avançadas de busca contextual.

## Fluxo de Execução

1. **Inicialização do Serviço:** Ao criar uma instância da classe, uma conexão com o cliente Pinecone é configurada (ou criada padrão), além do modelo de embeddings e configurações de chunking.

2. **Divisão do Texto:** Com o método `split_text`, um texto é fragmentado em pedaços menores usando tamanho e sobreposição configuráveis, de maneira que cada chunk faça sentido para processamento.

3. **Criação de Documentos:** Os chunks são convertidos em objetos `Document` enriquecidos com metadados, prontos para geração de vetores.

4. **Geração e Armazenamento de Vetores:** Utilizando `generate_vectors`, os chunks são transformados em embeddings, que são gravados no namespace principal, opcionalmente replicados no namespace global, com controle de batches e possibilidade de rollback caso alguma operação falhe.

5. **Consulta por Vetores Semelhantes:** Através de `document_search`, são feitas buscas por vetores similares a uma consulta textual, retornando documentos relevantes do namespace escolhido.

6. **Remoção Condicional:** O método `delete_documents` permite remover vetores específicos filtrados por metadados, garantindo controle fino sobre os dados armazenados.

## Tabela de Métodos da Classe

| Método            | Descrição                                                    |
|-------------------|--------------------------------------------------------------|
| `__init__`        | Inicializa a instância configurando cliente, modelo e parâmetros. |
| `split_text`      | Divide texto em chunks menores com tamanho e sobreposição configuráveis. |
| `build_documents` | Estático, cria lista de objetos Document a partir dos chunks e metadados. |
| `delete_documents`| Remove documentos do vetor filtrando por metadados no namespace indicado. |
| `document_search` | Pesquisa vetorial retornando documentos mais similares a uma consulta. |
| `generate_vectors`| Gera embeddings para texto, armazena nos vetores com controle de batch e rollback. |

## Pontos Importantes da Arquitetura e Insights

- **Integração com PineconeClient e LangChain:** A classe usa o `PineconeClient` para abstrair toda comunicação com o serviço de vetor, e `OpenAIEmbeddings` da LangChain para geração dos vetores, reforçando a modularidade e reutilização.

- **Uso de Decorators para Tracing:** A aplicação de um decorator `trace` nos métodos-chave permite instrumentar o código para logs estruturados, facilitando monitoramento e debug em produção.

- **Chunking Personalizável e Otimizado:** Utiliza configuração dinâmica para tamanho e sobreposição dos chunks, bem como separadores customizados, garantindo que o texto seja fragmentado em pedaços semanticamente coerentes para embeddings eficientes.

- **Robustez com Batch Processing e Rollback:** No método `generate_vectors`, documentos são adicionados em batches controlados, e um rollback é executado ao detectar erros, removendo documentos parcialmente adicionados para manter a consistência.

- **Namespaces Distintos:** A separação entre namespace principal e global permite organizar diferentes níveis de dados vetoriais, isolando contextos de uso e facilitando gerenciamento de permissões ou compartilhamentos.

# Descrição da Classe e Métodos

## Classe `PineconeVectorService`

### Descrição

Classe que provê serviços integrados para processamento de textos em dados vetoriais utilizando Pinecone, incluindo divisão de texto, geração de embeddings com modelo configurável, armazenamento em múltiplos namespaces e funcionalidades de busca e remoção de documentos por metadados. Facilita o trabalho com vector databases em projetos de NLP ao agregar operações comuns em uma interface única e extensível.

### Argumentos do Construtor

| Argumento            | Tipo                 | Descrição                                                       | Valor Padrão |
|----------------------|----------------------|-----------------------------------------------------------------|--------------|
| `vector_client`       | Optional[PineconeClient] | Cliente customizado para comunicação com Pinecone.              | None         |
| `embedding_model_name`| str                  | Nome do modelo de embedding para geração dos vetores.           | None         |
| `dimensions`          | int                  | Número de dimensões dos vetores no espaço embedding.             | None         |

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa o serviço configurando o cliente Pinecone, parâmetros de chunking, modelo de embeddings e cria os vetores correspondentes para os namespaces principal e global.

### Argumentos

- `vector_client` (Optional[PineconeClient]): Cliente Pinecone opcional para customizar conexão.
- `embedding_model_name` (str): Nome do modelo a ser utilizado para embeddings.
- `dimensions` (int): Dimensionalidade dos vetores finais.

### Retornos

- Não retorna valor.

### Raises

- Pode levantar exceções se a inicialização do cliente ou criação de vector store falhar.

### Exemplos

```python
service = PineconeVectorService(
    embedding_model_name="text-embedding-ada-002",
    dimensions=1536
)
```

---

### 2. `split_text`

### Descrição

Divide um texto longo em uma lista de chunks menores, respeitando tamanho máximo e sobreposição definidos, usando separadores personalizados para manter a coerência semântica.

### Argumentos

- `text` (str): Texto completo a ser fragmentado.
- `chunk_size` (int | None): Tamanho máximo de cada chunk, usa configuração padrão se None.
- `chunk_overlap` (int | None): Quantidade de sobreposição entre chunks consecutivos, usa configuração padrão se None.

### Retornos

- List[str]: Lista com os pedaços do texto fragmentado.

### Raises

- Nenhum específico.

### Exemplos

```python
chunks = service.split_text(
    "Um texto muito longo que precisa ser dividido em partes menores.",
    chunk_size=500,
    chunk_overlap=50
)
print(len(chunks))
```

---

### 3. `build_documents`

### Descrição

Método estático que recebe chunks e metadados, construindo uma lista de objetos `Document` para uso na geração de embeddings.

### Argumentos

- `chunks` (List[str]): Lista de textos fragmentados.
- `metadata` (Dict[str, Any]): Metadados a serem associados a cada documento.

### Retornos

- List[Document]: Lista de objetos Document prontos para processamento.

### Raises

- Nenhum.

### Exemplos

```python
docs = PineconeVectorService.build_documents(chunks, {"file_id": "1234"})
print(docs[0].metadata["file_id"])  # Saída: "1234"
```

---

### 4. `delete_documents`

### Descrição

Deleta documentos armazenados no vetor dentro do namespace especificado, filtrando-os por um campo de metadado (chave e valor), removendo seus vetores associados em batches.

### Argumentos

- `target_feature` (str): Nome do campo de metadado a ser filtrado.
- `target_id` (str): Valor do campo para identificação dos documentos a remover.
- `namespace` (str): Namespace onde a operação de remoção ocorrerá.

### Retornos

- dict: Informações com a quantidade de vetores deletados e namespace utilizado.

### Raises

- Pode levantar exceções se ocorrer erro na consulta ou deleção nos vetores.

### Exemplos

```python
result = service.delete_documents(
    target_feature="file_id",
    target_id="1234",
    namespace="main"
)
print(result["deleted_vectors"])
```

---

### 5. `document_search`

### Descrição

Realiza busca por similaridade vetorial baseada em consulta textual, retornando documentos mais relevantes do namespace indicado, podendo aplicar filtros adicionais.

### Argumentos

- `query` (str): Texto da consulta para busca semântica.
- `k` (int): Limite de resultados a retornar. Default = 3.
- `namespace` (str): Namespace para pesquisa. Se None, usa o principal.
- `filter` (dict): Filtros opcionais para restringir os resultados.

### Retornos

- dict: Estrutura com IDs dos documentos e seus metadados e conteúdos.

### Raises

- Pode lançar RuntimeError em caso de falha na busca.

### Exemplos

```python
results = service.document_search(
    query="Como funciona vector search?",
    k=5
)
print(list(results.keys()))
```

---

### 6. `generate_vectors`

### Descrição

Converte um texto completo em embeddings, dividindo em chunks, adicionando metadados e salvando os vetores no Pinecone em batch. Suporta salvar em namespace global e rollback automático caso alguma operação falhe.

### Argumentos

- `text` (str): Texto para geração de embeddings.
- `metadata` (dict): Metadados associados aos vetores criados.
- `save_global` (bool): Indica se deve salvar no namespace global também. Default False.
- `batch_size` (int | None): Número máximo de documentos por batch. Usa configuração padrão se None.

### Retornos

- dict: Estado da operação com status, mensagem, contagem de batches e IDs das chunks salvas.

### Raises

- Não propaga exceções direto, captura e retorna erro no dicionário de resposta.

### Exemplos

```python
response = service.generate_vectors(
    text="Conteúdo do documento a ser vetorizado.",
    metadata={"file_id": "file123"},
    save_global=True
)
print(response["status"])  # "success"
```

---

Essa documentação cobre os aspectos essenciais da classe `PineconeVectorService`, com detalhes que auxiliam desenvolvedores a entender seu funcionamento, integrações, limitações e modo de uso na construção de soluções com vetores e NLP.