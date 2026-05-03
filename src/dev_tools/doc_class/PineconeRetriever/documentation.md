# Classe `PineconeRetriever`

## Visão Geral

A classe `PineconeRetriever` é uma implementação especializada para interagir com o serviço de busca vetorial Pinecone, facilitando a recuperação eficiente de documentos com base na similaridade de vetores e em filtros de metadados. Ela encapsula a conexão com o índice Pinecone e o modelo de embeddings, fornecendo métodos para realizar buscas por similaridade de texto e consultas paginadas complexas que filtram documentos conforme critérios específicos.

O principal problema que resolve é a abstração da complexidade da manipulação direta do Pinecone, tornando simples executar buscas vetoriais com filtros, além de garantir manejo adequado dos embeddings e paginação nos resultados. Na prática, pode ser utilizada para buscas inteligentes em grandes bases de documentos, sistemas de recomendação ou qualquer aplicação que dependa de recuperação semântica eficiente.

Por exemplo, imagine uma aplicação que precise localizar documentos relacionados a uma pergunta feita pelo usuário, filtrando por categorias ou outros metadados – esta classe facilita essa interação com Pinecone, cuidando desde a geração dos vetores até a extração dos documentos relevantes, sem a necessidade do usuário dominar o protocolo de consulta de Pinecone.

## Fluxo de Execução

1. **Inicialização do objeto `PineconeRetriever`**:  
   - Recebe uma instância opcional de `PineconeClient`. Se não fornecida, cria internamente uma nova instância padrão.  
   - Recupera configurações padrões, como tamanho do batch e dimensão do vetor.  
   - Inicializa conexões com o índice Pinecone e modelo de embeddings, bem como a namespace utilizada.

2. **Realização de busca por similaridade (`similarity_search`)**:  
   - Recebe o texto da consulta, número máximo de resultados (k) e um filtro opcional por metadados.  
   - Valida os parâmetros, convertendo o texto da consulta em um vetor de embedding usando o modelo associado.  
   - Constrói a query de filtro para Pinecone, compatível com busca por igualdade ou múltiplos valores (`$eq` e `$in`).  
   - Executa a consulta no índice, solicitando metadados para cada resultado.  
   - Formata os documentos retornados, removendo o campo "text" do metadata e calculando o score da similaridade.

3. **Recuperação de documentos por metadados (`get_all_docs_by_metadata`)**:  
   - Permite buscar todos os documentos que possuam determinado valor ou lista de valores em uma chave de metadata, lidando com grandes volumes via paginação automática.  
   - Define um vetor dummy (zero vector) para realizar a consulta, já que o foco é filtrar pelo metadata.  
   - Itera nas páginas de resultados até que não haja mais tokens de paginação, agregando os documentos.  
   - Retorna lista completa dos documentos encontrados, cada um com id, metadata e score.

## Tabela de Métodos da Classe

| Método              | Descrição                                                      |
|---------------------|----------------------------------------------------------------|
| `__init__`          | Inicializa o retriever com uma instância do cliente Pinecone. |
| `similarity_search`  | Realiza busca por similaridade vetorial com filtro opcional.  |
| `get_all_docs_by_metadata` | Recupera documentos filtrados por metadados com paginação. |

## Variáveis de Ambiente

Nenhuma variável de ambiente é utilizada diretamente nesta classe.

## Pontos Importantes da Arquitetura e Insights

- O uso do padrão *Dependency Injection* ao permitir receber um `PineconeClient` externo facilita testes e reutilização da conexão com Pinecone.  
- Internamente aplica encapsulamento forte, escondendo detalhes da configuração, geração de embeddings e do protocolo de consulta ao Pinecone.  
- O tratamento cuidadoso de exceções em todos os métodos garante que erros sejam facilmente identificados e informados adequadamente.  
- Suporta filtros no formato Pinecone (`$eq` e `$in`), o que amplia a expressividade de buscas sem aumentar a complexidade do usuário.  
- Implementa paginação explícita na consulta por metadados, habilitando trabalhar com índices muito grandes sem estourar memória.  
- Utiliza uma operação de embedding para consultas textuais que é offloaded ao cliente, mantendo o foco em orquestração do fluxo.  
- A classe depende de outras: `PineconeClient`, `PineconeVectorStoreConfig` e `ApplicationTracing`, seguindo um projeto modular.

# Descrição da Classe e Métodos

## Classe `PineconeRetriever`

### Descrição

Classe que gerencia a interação com o serviço Pinecone para realizar buscas vetoriais baseadas em embeddings de texto e filtros por metadados. Fornece métodos para busca de similaridade simples e recuperação paginada de documentos por metadados, utilizando configurações customizáveis para batch size, dimensão de vetores e namespace.

### Argumentos do Construtor

| Argumento | Tipo                    | Descrição                                            | Valor Padrão |
|-----------|-------------------------|-----------------------------------------------------|--------------|
| client    | Optional[PineconeClient] | Instância do cliente Pinecone para indexação e embedding. | None         |

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa o objeto `PineconeRetriever` configurando o cliente Pinecone, a configuração do vetor (dimensão e batch size), o índice e o namespace para consultas.

### Argumentos

- client (Optional[PineconeClient]): Cliente Pinecone customizado.  
- Se não fornecido, cria um novo cliente padrão.

### Retornos

- Não retorna valor.

### Raises

- RuntimeError: Caso a inicialização falhe por qualquer exceção.

### Exemplos

```python
retriever = PineconeRetriever()  # Cria retriever com configuração padrão
custom_client = PineconeClient(...)
retriever_custom = PineconeRetriever(custom_client)  # Usa client personalizado
```

---

### 2. `similarity_search`

### Descrição

Executa uma busca por similaridade vetorial com base em uma query textual, retornando os `k` documentos mais relevantes. Aceita filtros de metadados para refinar os resultados.

### Argumentos

- query (str): Texto da consulta para busca vetorial.  
- k (int): Quantidade máxima de resultados a retornar.  
- filter_search (Optional[Dict[str, Any]]): Dicionário com filtro para metadados (ex: `{"category": ["finance","tech"]}`).

### Retornos

- List[Dict[str, Any]]: Lista de documentos contendo `id`, `text`, `metadata` (sem o campo `text`) e `score` (similaridade).

### Raises

- ValueError: Se `query` estiver vazio ou `k` for menor ou igual a zero.  
- ValueError: Se o filtro `filter_search` for inválido.  
- RuntimeError: Se erro ocorrer na geração do embedding ou consulta Pinecone.

### Exemplos

```python
results = retriever.similarity_search(
    query="How to bake a cake?",
    k=3,
    filter_search={"category": "recipes"}
)
for doc in results:
    print(doc["id"], doc["score"])
```

---

### 3. `get_all_docs_by_metadata`

### Descrição

Obtém todos os documentos no índice Pinecone que contenham um valor específico ou conjunto de valores para uma chave de metadados, usando paginação para lidar com grandes volumes.

### Argumentos

- batch_size (int | None): Quantidade de documentos por página (padrão configurado).  
- dimension (int | None): Dimensão do vetor dummy usado na query (padrão configurado).  
- target_key (str): Chave do metadado para filtro (ex: "file_id").  
- target_value (Union[str, List[str]]): Valor ou lista de valores a buscar na chave.

### Retornos

- List[Dict[str, Any]]: Lista de documentos contendo `id`, `metadata` e `score`.

### Raises

- ValueError: Se `target_value` não for informado.  
- RuntimeError: Em caso de falha durante a consulta ao Pinecone.

### Exemplos

```python
all_pdfs = retriever.get_all_docs_by_metadata(
    batch_size=20,
    target_key="file_extension",
    target_value="pdf"
)
print(f"Found {len(all_pdfs)} PDF documents")
```

## Uso

```python
if __name__ == "__main__":
    import json

    pine_client = PineconeClient(
        index_name="backai-vectorstore",
        main_namespace="betterai-embeddings-dev",
    )

    retriver = PineconeRetriever(pine_client)

    # Similarity search
    similarity_results = retriver.similarity_search(
        query="What is the capital of France?",
        k=5
    )

    print("Similarity Search Results:")
    print(json.dumps(similarity_results, indent=2))

    # Metadata search
    metadata_results = retriver.get_all_docs_by_metadata(
        target_key="file_extension",
        target_value="pdf",
        batch_size=10
    )

    print("\nMetadata Search Results:")
    print(json.dumps(metadata_results, indent=2))

# python -m src.vector_store.pinecone.retriever
```

---

Esta documentação visa facilitar o entendimento e uso da classe `PineconeRetriever` em projetos que necessitem buscas vetoriais integradas ao Pinecone, com exemplos práticos e detalhes essenciais para integração transparente.