# Classe `PineconeClient`

## Visão Geral

A classe `PineconeClient` é uma abstração para gerenciar a conexão e as operações com o serviço Pinecone, que é uma solução de armazenamento e busca vetorial de alto desempenho. Ela facilita a integração com APIs externas (Pinecone e OpenAI), cuidando da configuração das chaves de API, definição de namespaces e inicialização do modelo de embeddings para trabalhar com vetores de texto.

Essa classe resolve o problema de configuração manual e repetitiva dessas integrações, fornecendo uma interface unificada e segura para criar e manipular stores vetoriais usando namespaces personalizados e modelos de embedding específicos. Na prática, ela pode ser usada para armazenar e buscar vetores gerados a partir de textos, o que é fundamental para sistemas como buscas semânticas, recomendação baseada em similaridade e NLP.

## Fluxo de Execução

1. **Inicialização do Cliente:**
   - Ao criar uma instância de `PineconeClient`, as chaves de API do OpenAI e Pinecone são carregadas das variáveis de ambiente.
   - São definidos `index_name`, `main_namespace` e `global_namespace` tanto pelos parâmetros do construtor quanto por variáveis de ambiente ou configuração padrão.
   - O modelo de embedding a ser usado é selecionado da mesma forma.
   - Inicializa internamente a conexão com Pinecone e o modelo de embedding OpenAI.

2. **Configuração das Conexões:**
   - `_init_pinecone` cria o cliente Pinecone e instancia o index especificado.
   - `_init_embeddings` inicializa o modelo de embedding OpenAI de acordo com a configuração.

3. **Resolução do Namespace:**
   - Método `get_namespace()` retorna o namespace a ser usado nas operações, priorizando um valor passado no método, caso seja fornecido, ou o namespace principal da instância.

4. **Criação da Vector Store:**
   - `create_vector_store()` monta a instância de `PineconeVectorStore`, associando o index e o modelo de embedding apropriados ao namespace desejado.
   - O objeto retornado permite realizar operações de similaridade vetorial.

## Tabela de Métodos da Classe

| Método              | Descrição                                                       |
|---------------------|----------------------------------------------------------------|
| `__init__`          | Inicializa cliente Pinecone, carregando configurações e chaves |
| `_init_pinecone`    | Estabelece conexão com Pinecone e instancia index              |
| `_init_embeddings`  | Inicializa o modelo de embedding OpenAI                         |
| `get_namespace`     | Retorna o namespace resolvido para operações                    |
| `create_vector_store` | Retorna uma instância configurada de PineconeVectorStore      |

## Variáveis de Ambiente

- `OPENAI_API_KEY`: Chave da API OpenAI para geração de embeddings.
- `PINECONE_API_KEY`: Chave da API Pinecone para acesso ao serviço.
- `PINECONE_INDEX_NAME`: Nome do índice Pinecone a ser utilizado.
- `PINECONE_NAMESPACE`: Namespace principal padrão para armazenar vetores.
- `PINECONE_GLOBAL_NAMESPACE`: Namespace global opcional para vetores compartilhados.
- `OPENAI_EMBEDDING_MODEL`: Nome do modelo de embedding OpenAI a ser usado.

## Pontos Importantes da Arquitetura e Insights

- A classe usa encapsulamento para ocultar detalhes de inicialização do Pinecone e do modelo de embedding.
- O uso de variáveis de ambiente com fallback para parâmetros do construtor aumenta flexibilidade e reutilização.
- O padrão de "injeção de dependência" está presente na criação do vector store, permitindo que embedding e namespace sejam sobrescritos na chamada.
- Integração com módulos externos especializados (`langchain_openai`, `langchain_pinecone`), evidenciando uso de composição.
- A classe utiliza um sistema de tracing customizado (`ApplicationTracing`) para facilitar debug e monitoramento, gerando logs detalhados em cada etapa.
- Separação clara entre configuração, inicialização e criação da vector store, favorecendo manutenção e testes.

# Descrição da Classe e Métodos

---

## Classe `PineconeClient`

### Descrição

Classe para controle e facilitação da conexão com o serviço Pinecone e gerenciamento dos vetores armazenados. Integra APIs do Pinecone e OpenAI para criar uma base vetorial customizada, que pode ser consultada ou atualizada a partir de modelos de embedding fornecidos. Permite configurar namespaces e modelos de forma flexível, simplificando operações vetoriais em aplicações.

### Argumentos do Construtor

| Argumento         | Tipo              | Descrição                                             | Valor Padrão |
|-------------------|-------------------|-------------------------------------------------------|--------------|
| `index_name`      | `Optional[str]`   | Nome do índice Pinecone a ser utilizado               | `None`       |
| `main_namespace`  | `Optional[str]`   | Namespace primário para armazenar vetores             | `None`       |
| `global_namespace`| `Optional[str]`   | Namespace global opcional para vetores compartilhados | `None`       |
| `embedding_model` | `Optional[str]`   | Nome do modelo OpenAI para embeddings                  | `None`       |

---

### 1. `__init__`

### Descrição

Inicializa o cliente Pinecone carregando as chaves de API, configurações, definindo os namespaces e modelo de embedding, além de estabelecer conexões.

### Argumentos

- `index_name` (Optional[str]): nome do índice Pinecone (opcional)
- `main_namespace` (Optional[str]): namespace primário (opcional)
- `global_namespace` (Optional[str]): namespace global (opcional)
- `embedding_model` (Optional[str]): nome do modelo OpenAI (opcional)

### Retornos

- Não retorna valor.

### Raises

- `EnvironmentError`: se as chaves de API não estiverem definidas.
- `ValueError`: se o `index_name` não for definido.
- `RuntimeError`: para falhas gerais de inicialização.

### Exemplos

```python
client = PineconeClient(index_name="meu_indice", main_namespace="app_namespace")
```

---

### 2. `_init_pinecone`

### Descrição

Estabelece conexão com o serviço Pinecone e instancia o índice com o nome configurado.

### Argumentos

- Nenhum.

### Retornos

- Não retorna valor.

### Exemplos

```python
client._init_pinecone()
# Internamente conecta ao Pinecone e configura o index para operações
```

---

### 3. `_init_embeddings`

### Descrição

Inicializa o modelo OpenAI para geração de embeddings, podendo usar um nome de modelo personalizado.

### Argumentos

- `model_name` (Optional[str]): nome do modelo de embedding (opcional)

### Retornos

- Não retorna valor.

### Exemplos

```python
client._init_embeddings("text-embedding-ada-002")
# Atualiza o modelo de embedding usado pelo cliente
```

---

### 4. `get_namespace`

### Descrição

Retorna o namespace a ser usado para operações, priorizando o argumento passado, ou retornando o principal configurado.

### Argumentos

- `namespace` (Optional[str]): namespace opcional substituto.

### Retornos

- `str`: namespace resolvido para uso.

### Exemplos

```python
ns = client.get_namespace()  # retorna o main_namespace configurado
ns2 = client.get_namespace("namespace_alternativo")  # retorna "namespace_alternativo"
```

---

### 5. `create_vector_store`

### Descrição

Cria e retorna uma instância `PineconeVectorStore` configurada com o índice, embedding e namespace selecionados.

### Argumentos

- `namespace` (Optional[str]): namespace para a store (opcional).
- `embedding_model` (Optional[OpenAIEmbeddings]): instância do modelo de embedding (opcional).

### Retornos

- `PineconeVectorStore`: objeto para manipulação do armazenamento vetorial.

### Exemplos

```python
vector_store = client.create_vector_store()
# Usa main_namespace e modelo configurado

vector_store_custom = client.create_vector_store(namespace="ns_custom")
# Cria store com namespace customizado
```

## Uso

```python
if __name__ == "__main__":
    client = PineconeClient()
    vector_store = client.create_vector_store()
    print("Pinecone Client initialized and VectorStore created successfully.")

# python -m src.vector_store.pinecone.client
```