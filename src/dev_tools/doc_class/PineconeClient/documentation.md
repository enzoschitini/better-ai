# Classe `PineconeClient`

## Visão Geral

A classe `PineconeClient` é um cliente unificado para facilitar a integração com o serviço Pinecone, utilizado para armazenamento e busca vetorial. Ela gerencia a configuração necessária para autenticar com as APIs OpenAI e Pinecone, inicializa os embeddings para vetorização, cria e gerencia os VectorStores e namespaces associados. 

Esse cliente resolve o problema comum de lidar individualmente com configuração, autenticação e criação de objetos Pinecone, centralizando essas responsabilidades em uma interface simples. Na prática, ela pode ser usada por desenvolvedores que precisam indexar e consultar dados vetoriais para aplicações de busca semântica, recomendação ou NLP, simplificando o processo de conexão com o Pinecone e OpenAI.

## Fluxo de Execução

1. **Inicialização do Cliente (`__init__`)**: recebe parâmetros opcionais ou lê variáveis de ambiente para configurar o índice, namespaces e modelo de embeddings. Valida se as chaves API estão disponíveis e lança exceções caso contrário.

2. **Carregamento das Credenciais e Configurações**: configura o nome do índice Pinecone, namespaces principal e global, e o modelo de embedding a ser usado, usando valores padrão da configuração ou entradas do usuário.

3. **Inicialização da Conexão com Pinecone (`_init_pinecone`)**: cria uma instância do cliente Pinecone autenticada com a chave fornecida e seleciona o índice configurado para operações.

4. **Inicialização do Modelo de Embeddings (`_init_embeddings`)**: instancia o modelo OpenAIEmbeddings, responsável por gerar vetores de texto para uso com Pinecone.

5. **Uso do Cliente para Obter Namespaces (`get_namespace`)**: resolve qual namespace utilizar, priorizando o valor especificado na chamada ou o principal configurado.

6. **Criação de um VectorStore Configurado (`create_vector_store`)**: constrói um objeto PineconeVectorStore ligado ao índice, namespace e modelo de embeddings, pronto para indexar ou buscar vetores.

## Tabela de Métodos da Classe

| Método               | Descrição                                         |
|----------------------|--------------------------------------------------|
| `__init__`           | Inicializa o cliente Pinecone com credenciais e configurações. |
| `_init_pinecone`     | Estabelece conexão com Pinecone e seleciona o índice. |
| `_init_embeddings`   | Inicializa o modelo de embeddings usado para vetorização. |
| `get_namespace`      | Resolve e retorna o namespace a ser utilizado.  |
| `create_vector_store`| Cria e retorna um PineconeVectorStore configurado para um namespace. |

## Pontos Importantes da Arquitetura e Insights

- **Centralização da Configuração e Inicialização**: a classe agrupa leitura de configurações (ambiente e defaults), verificação de credenciais e inicializações, promovendo maior segurança e clareza no bootstrap do cliente.

- **Uso de Decorator para Logging e Tratamento de Erros**: o decorator `trace` é aplicado em métodos críticos para padronizar a geração de logs informativos e captura de exceções, facilitando monitoramento.

- **Separação de Responsabilidades**: métodos internos (`_init_pinecone`, `_init_embeddings`) estão encapsulados e complementam a configuração feita no construtor, mantendo o construtor enxuto.

- **Integração com Outras Classes**: utiliza classes externas do Langchain para embeddings e vector stores (`OpenAIEmbeddings` e `PineconeVectorStore`) além de uma configuração customizada (`PineconeVectorStoreConfig`) e sistema de tracing interno (`ApplicationTracing`).

- **Flexibilidade de Parâmetros**: permite sobreposição de configurações padrão via argumentos no construtor e nos métodos, favorecendo reusabilidade e customização simples.

# Descrição da Classe e Métodos

## Classe `PineconeClient`

### Descrição

Responsável por gerir a conexão e operações básicas com o serviço Pinecone para armazenamento vetorial. Automatiza o carregamento das credenciais necessárias, inicializa o índice e embeddings, e abstrai a criação de stores e namespaces, facilitando o uso da base vetorial em aplicações.

### Argumentos do Construtor

| Argumento         | Tipo             | Descrição                                                | Valor Padrão |
|-------------------|------------------|----------------------------------------------------------|--------------|
| `index_name`      | `Optional[str]`  | Nome do índice Pinecone a ser usado                      | None         |
| `main_namespace`  | `Optional[str]`  | Namespace principal para operações vetoriais             | None         |
| `global_namespace`| `Optional[str]`  | Namespace global para operações                           | None         |
| `embedding_model` | `Optional[str]`  | Nome do modelo de embedding OpenAI para geração dos vetores | None      |

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa o cliente Pinecone, carregando credenciais, definindo configurações de índice e namespaces, e inicializando as conexões com Pinecone e o modelo de embeddings.

### Argumentos

- `index_name` (Optional[str]): nome do índice Pinecone.  
- `main_namespace` (Optional[str]): namespace principal.  
- `global_namespace` (Optional[str]): namespace global.  
- `embedding_model` (Optional[str]): nome do modelo para embeddings.  

### Retornos

- Não retorna valor.

### Raises

- `EnvironmentError`: se as chaves da API OpenAI ou Pinecone não forem encontradas.  
- `ValueError`: se o nome do índice não for informado ou configurado.

### Exemplos

```python
client = PineconeClient(
    index_name="meu_indice",
    main_namespace="namespace_principal",
    embedding_model="text-embedding-ada-002"
)
```

---

### 2. `_init_pinecone`

### Descrição

Estabelece a conexão com o serviço Pinecone utilizando a chave de API e seleciona o índice configurado para operações subsequentes.

### Argumentos

- Nenhum.

### Retornos

- Não retorna valor.

### Raises

- Pode propagar exceções relacionadas à conexão com Pinecone.

### Exemplos

```python
client._init_pinecone()  # Normalmente chamado dentro do construtor
```

---

### 3. `_init_embeddings`

### Descrição

Inicializa o modelo de embeddings a ser usado para gerar vetores a partir de textos. Pode receber um modelo específico ou usar o padrão configurado na inicialização do cliente.

### Argumentos

- `model_name` (Optional[str]): nome do modelo de embedding.  
- Se não informado, usa o modelo padrão configurado.

### Retornos

- Não retorna valor.

### Exemplos

```python
client._init_embeddings("text-embedding-ada-002")
```

---

### 4. `get_namespace`

### Descrição

Resolve qual namespace utilizar para uma operação, priorizando o que for explicitamente informado no parâmetro ou retornando o namespace principal configurado.

### Argumentos

- `namespace` (Optional[str]): namespace desejado.  

### Retornos

- `str`: o namespace efetivamente utilizado.

### Exemplos

```python
ns = client.get_namespace("namespace_especifico")
print(ns)  # "namespace_especifico"

ns = client.get_namespace()
print(ns)  # retorna o main_namespace configurado
```

---

### 5. `create_vector_store`

### Descrição

Cria e retorna uma instância de `PineconeVectorStore` configurada para um namespace e modelo de embeddings específicos, útil para ingestão e consultas vetoriais.

### Argumentos

- `namespace` (Optional[str]): namespace para uso no vetor store.  
- `embedding_model` (Optional[OpenAIEmbeddings]): modelo de embeddings a ser utilizado.  

### Retornos

- `PineconeVectorStore`: instância configurada do vector store.

### Exemplos

```python
vector_store = client.create_vector_store(namespace="minerais")
# Usa main_namespace e modelo padrão caso não informado

embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
vector_store_custom = client.create_vector_store(
    namespace="custom_ns", 
    embedding_model=embeddings
)
```