# Documentação da Classe `PineconeClient`

## Visão Geral

A classe `PineconeClient` é um cliente unificado que facilita a integração com os serviços da Pinecone e OpenAI para armazenamento e recuperação eficiente de vetores de embeddings. Seu propósito é abstrair a complexidade de carregar credenciais, inicializar conexões, configurar modelos de embeddings e manipular namespaces, permitindo ao desenvolvedor focar na lógica de negócio sem se preocupar com detalhes de infraestrutura.

Ela resolve o problema de gerenciar múltiplas configurações e inicializações necessárias para trabalhar com bancos de dados vetoriais Pinecone e modelos de embeddings OpenAI de forma simples, reutilizável e segura. Na prática, pode ser usada para criar "VectorStores" customizados que armazenam e buscam dados vetoriais segmentados por namespaces.

## Fluxo de Execução

1. Instancie a classe `PineconeClient`, opcionalmente passando parâmetros como nome do índice, namespaces e modelo de embeddings. Caso não passe, as configurações padrão ou do arquivo `.env` serão usadas.

2. Durante a inicialização (`__init__`), a classe carrega as chaves de API do ambiente, valida sua existência, resolve as configurações de índice e namespaces, e inicializa as conexões Pinecone e o modelo de embeddings OpenAI.

3. Utilize o método `create_vector_store` para criar uma instância de `PineconeVectorStore`. Você pode especificar um namespace e um modelo de embeddings diferentes do padrão, se desejar.

4. O `PineconeVectorStore` criado poderá ser usado para tarefas como ingestão de documentos, busca por similaridade, e gerenciamento dos dados vetoriais dentro do namespace escolhido.

## Tabela de Métodos da Classe

| Método                  | Descrição                                                    |
|-------------------------|--------------------------------------------------------------|
| `__init__`              | Inicializa o cliente, carrega configurações e autenticações |
| `_init_pinecone`        | Inicializa conexão com o Pinecone e instancia o índice       |
| `_init_embeddings`      | Inicializa o modelo de embeddings OpenAI                      |
| `get_namespace`         | Resolve o namespace a ser utilizado, preferindo input ou padrão |
| `create_vector_store`   | Cria um VectorStore configurado para operações de vetorização |

## Pontos Importantes da Arquitetura e Insights

- **Encapsulamento com Decoradores de Tracing:** Usa um decorador `trace` para padronizar logs e captura de erros em métodos importantes. Isso mantém o código limpo e garante rastreabilidade consistente.

- **Configuração por Variáveis de Ambiente e Defaults:** Permite flexibilidade na parametrização usando valores passados explicitamente, ambiente `.env`, ou configuração padrão, facilitando deploy em múltiplos ambientes.

- **Separação Clara entre Inicializações Internas e API Pública:** Métodos com underscore (`_init_pinecone`, `_init_embeddings`) são internos, e os públicos expõem apenas as operações necessárias para consumo.

- **Dependência em Outras Classes:** Utiliza `PineconeVectorStoreConfig` para obter configurações padrão, `OpenAIEmbeddings` para embeddings, `pinecone.Pinecone` para conexão Pinecone e `PineconeVectorStore` para operações vetoriais.

- **Design para Flexibilidade de Namespace:** Suporta namespaces diferenciados para escopo principal e global, possibilitando segmentação refinada dos dados.

---

# Descrição da Classe e Métodos

## Classe `PineconeClient`

### Descrição

A `PineconeClient` é a camada de abstração responsável por gerenciar a conexão e configurações necessárias para trabalhar com o Pinecone e suas integrações de embeddings com OpenAI. Ela centraliza carregamento de credenciais, criação do índice e inicialização dos modelos, além de fornecer interface para criação de `VectorStores` configurados para diferentes namespaces e modelos.

### Argumentos do Construtor

| Argumento         | Tipo           | Descrição                                                                                      | Valor Padrão |
|-------------------|----------------|------------------------------------------------------------------------------------------------|--------------|
| `index_name`      | Optional[str]  | Nome do índice Pinecone a ser utilizado. Se `None`, tenta pegar de `.env` ou configuração padrão. | None         |
| `main_namespace`  | Optional[str]  | Namespace principal para operações. Se `None`, tenta pegar de `.env` ou configuração padrão.      | None         |
| `global_namespace`| Optional[str]  | Namespace global para operações. Se `None`, tenta pegar de `.env` ou configuração padrão.         | None         |
| `embedding_model` | Optional[str]  | Nome do modelo de embeddings OpenAI a ser utilizado. Se `None`, tenta pegar de `.env` ou configuração padrão.| None |

### Métodos

---

### 1. `__init__`

#### Descrição

Inicializa o cliente Pinecone carregando credenciais da OpenAI e Pinecone, resolvendo nomes de índice e namespaces com prioridade para parâmetros explícitos, ambiente ou configurações padrão. Também inicializa conexões com Pinecone e o modelo de embeddings escolhido.

#### Argumentos

- `index_name` (Optional[str]): nome do índice Pinecone.
- `main_namespace` (Optional[str]): namespace padrão para operações.
- `global_namespace` (Optional[str]): namespace global para operações.
- `embedding_model` (Optional[str]): nome do modelo de embeddings OpenAI.

#### Retornos

- Não retorna valor.

#### Raises

- `EnvironmentError`: se as chaves API não estiverem definidas.
- `ValueError`: se o nome do índice não for fornecido/definido.

#### Exemplos

```python
client = PineconeClient(
    index_name="my-index",
    main_namespace="default-namespace",
    embedding_model="text-embedding-3-small"
)
```

---

### 2. `_init_pinecone`

#### Descrição

Método interno que conecta ao Pinecone usando a API Key e instancia o índice para operações vetoriais.

#### Argumentos

- Nenhum.

#### Retornos

- Não retorna valor.

#### Exemplos

```python
# Chamado automaticamente na inicialização do cliente
client._init_pinecone()
```

---

### 3. `_init_embeddings`

#### Descrição

Método interno que inicializa a instância de embeddings da OpenAI, podendo receber um nome de modelo alternativo.

#### Argumentos

- `model_name` (Optional[str]): nome do modelo de embeddings. Se None, usa o padrão do cliente.

#### Retornos

- Não retorna valor.

#### Exemplos

```python
client._init_embeddings(model_name="text-embedding-3-small")
```

---

### 4. `get_namespace`

#### Descrição

Resolve e retorna o namespace a ser usado, preferindo o valor passado como argumento, com fallback para o namespace principal configurado.

#### Argumentos

- `namespace` (Optional[str]): namespace desejado.

#### Retornos

- `str`: namespace resolvido.

#### Exemplos

```python
ns = client.get_namespace()  # Retorna o namespace principal
ns_custom = client.get_namespace("custom-namespace")  # Retorna "custom-namespace"
```

---

### 5. `create_vector_store`

#### Descrição

Cria e retorna uma instância de `PineconeVectorStore`, configurada para usar um namespace e modelo de embeddings específicos, com fallback para os padrões do cliente.

#### Argumentos

- `namespace` (Optional[str]): namespace onde o VectorStore irá operar.
- `embedding_model` (Optional[OpenAIEmbeddings]): modelo de embeddings para ser usado no VectorStore.

#### Retornos

- `PineconeVectorStore`: instância configurada para manipulação vetorial.

#### Exemplos

```python
vector_store = client.create_vector_store()
vector_store_custom = client.create_vector_store(namespace="custom-ns")

# Usando um modelo de embeddings personalizado
custom_embedding = OpenAIEmbeddings(model="text-embedding-large")
vector_store_custom_model = client.create_vector_store(
    embedding_model=custom_embedding
)
```

---

# Exemplos Práticos de Uso

```python
# Instancia o cliente com configurações padrões do ambiente
client = PineconeClient()

# Cria um VectorStore para o namespace padrão
default_store = client.create_vector_store()

# Cria um VectorStore para um namespace personalizado
custom_store = client.create_vector_store(namespace="finance_docs")

# Obtém o namespace resolvido para uso
ns = client.get_namespace()

# Usa o VectorStore para adicionar ou buscar vetores (exemplo com PineconeVectorStore)
custom_store.add_texts(["Documento importante sobre finanças"], ids=["doc1"])
results = custom_store.similarity_search("consultoria financeira")
```

Esta documentação detalhada e organizada ajudará desenvolvedores a entender e utilizar a classe `PineconeClient` de forma rápida, eficiente e segura.