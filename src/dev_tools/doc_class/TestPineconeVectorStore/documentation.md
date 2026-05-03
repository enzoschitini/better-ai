# Classe `TestPineconeVectorStore`

## Visão Geral

A classe `TestPineconeVectorStore` oferece um conjunto de métodos para interagir de forma prática com uma base de dados vetorial gerenciada pela plataforma Pinecone. Ela encapsula operações comuns como inicialização do cliente, geração de embeddings vetoriais a partir de textos, busca por similaridade e exclusão de vetores baseados em filtros de metadados.

Esse conjunto de funcionalidades resolve o problema da complexidade no manuseio direto do Pinecone, fornecendo uma interface simples e pronta para operações típicas em casos de uso como busca semântica em documentos, organização de dados vetoriais e manutenção dos índices vetoriais.

Na prática, essa classe pode ser usada para indexar documentos, realizar buscas inteligentes por texto e manter a base de dados vetorial atualizada sem a necessidade manipular diretamente recursos mais baixos da API do Pinecone.

----------------------------

## Fluxo de Execução

1. **Inicialização do Cliente**  
   Chama-se `get_client()` para criar e configurar um cliente Pinecone com o índice e namespaces definidos (ou padrões). Esse cliente é armazenado internamente para uso nas próximas operações.

2. **Gerar e Salvar Embeddings**  
   Utilizando o método `embedding()`, insere textos (ou lê um arquivo exemplo) que serão processados para gerar vetores de embedding. Estes vetores são enviados para armazenamento no Pinecone junto com metadados associados para facilitar buscas futuras.

3. **Busca por Similaridade**  
   Executa-se `retriever()` para realizar buscas no Pinecone baseando-se em uma consulta textual e filtros aplicados sobre os metadados armazenados. O método retorna os vetores mais relevantes conforme a similaridade computada.

4. **Remoção de Vetores**  
   Por fim, com o método `delete()` é possível apagar vetores específicos filtrados por um metadado (como `source` ou `file_id`), garantindo a manutenção e limpeza do índice conforme necessidades.

----------------------------

## Tabela de Métodos da Classe

| Método       | Descrição                                                      |
|--------------|----------------------------------------------------------------|
| `__init__`   | Inicializa a classe com configurações para Pinecone e embeddings. |
| `get_client` | Inicializa e retorna o cliente Pinecone configurado.          |
| `retriever`  | Executa busca por similaridade no índice Pinecone com filtros.|
| `embedding`  | Gera e salva embeddings no Pinecone a partir de dado texto.   |
| `delete`     | Exclui vetores no Pinecone com base em filtros de metadados.  |

----------------------------

## Pontos Importantes da Arquitetura e Insights

- A classe utiliza composição ao instanciar objetos de outras classes especializadas (`PineconeClient`, `PineconeRetriever` e `PineconeEmbedding`), separando claramente responsabilidades.
- O uso de namespaces distintos (`main_namespace` e `global_namespace`) permite organizar vetores em diferentes "escopos" dentro do mesmo índice, facilitando a gestão.
- Manipulação de metadados em embeddings e filtros possibilita buscas e exclusões refinadas, aumentando a precisão e controle dos dados.
- Métodos implementam print com retorno JSON bem formatado para facilitar debug e conferência de resultados, muito útil em testes.
- Há suporte para fallback de parâmetros usando valores padrão, o que reduz a necessidade de configuração inicial.

----------------------------

# Descrição da Classe e Métodos

## Classe `TestPineconeVectorStore`

### Descrição

Classe para facilitar integração e testes com o Pinecone vector store, fornecendo métodos para conectar ao serviço, indexar vetores de texto, realizar buscas de similaridade e excluir vetores com base em metadados.

### Argumentos do Construtor

| Argumento            | Tipo   | Descrição                                            | Valor Padrão           |
|----------------------|--------|-----------------------------------------------------|-----------------------|
| `index_name`         | str    | Nome do índice Pinecone para conexão.               | `"backai-vectorstore"` |
| `main_namespace`     | str    | Namespace principal para armazenamento de vetores. | `"main_namespace"`    |
| `global_namespace`   | str    | Namespace global para armazenamento de vetores.    | `"global_namespace"`  |
| `embedding_model_name` | str  | Nome do modelo para geração de embeddings.          | `"text-embedding-3-large"` |
| `dimensions`         | int    | Dimensionalidade dos vetores de embedding.          | 3072                  |

---

### 1. `__init__`

### Descrição

Inicializa a instância da classe definindo nomes do índice, namespaces, modelo de embedding e dimensões dos vetores, com valores padrão caso não sejam fornecidos.

### Argumentos

- `index_name` (str): nome do índice Pinecone.
- `main_namespace` (str): namespace principal.
- `global_namespace` (str): namespace global.
- `embedding_model_name` (str): modelo para embeddings.
- `dimensions` (int): tamanho dos vetores.

### Retornos

Não retorna valor.

### Raises

Nenhum.

### Exemplos

```python
# Criar objeto com configurações padrão
tester = TestPineconeVectorStore()

# Criar objeto com parâmetros customizados
tester_custom = TestPineconeVectorStore(
    index_name="meu_indice",
    main_namespace="principal",
    embedding_model_name="modelo-custom",
    dimensions=1536
)
```

---

### 2. `get_client`

### Descrição

Inicializa e retorna um cliente Pinecone configurado com os índices e namespaces internos. Guarda internamente o cliente para reutilização.

### Argumentos

Nenhum.

### Retornos

- `PineconeClient`: objeto cliente configurado para interações com Pinecone.

### Raises

Nenhum.

### Exemplos

```python
cliente = tester.get_client()
# cliente pode ser usado para operações avançadas se necessário
```

---

### 3. `retriever`

### Descrição

Realiza uma busca por similaridade no índice Pinecone para recuperar os vetores/documentos mais relevantes com base no texto de consulta e filtros em metadados.

### Argumentos

- `query` (str): texto para busca de similaridade.
- `filter_search` (dict): filtros por metadados para refinar pesquisa.
- `k` (int): quantidade máxima de resultados a serem retornados.

### Retornos

- `list`: lista com os resultados mais semelhantes encontrados.

### Raises

Nenhum.

### Exemplos

```python
resultados = tester.retriever(
    query="Quais arquivos existem na base?",
    filter_search={"source": ["example_text.txt"]},
    k=3
)
for r in resultados:
    print(r["metadata"], r["score"])
```

---

### 4. `embedding`

### Descrição

Gera vetores de embedding para um texto fornecido (ou arquivo exemplo caso não informe nada) e salva esses vetores com metadados no Pinecone.

### Argumentos

- `embedding_content` (str): texto a ser embeddado.
- `embedding_metadata` (dict): metadados associados a esses vetores.

### Retornos

- `dict`: resposta do Pinecone confirmando o status do salvamento dos vetores.

### Raises

Nenhum.

### Exemplos

```python
response = tester.embedding(
    embedding_content="Este é um exemplo de texto para embedding.",
    embedding_metadata={"file_id": "file_001", "user_id": "user_01", "source": "input.txt"}
)
print(response["status"])
```

---

### 5. `delete`

### Descrição

Remove vetores do Pinecone filtrando por um campo específico de metadado e seu valor, dentro de um namespace.

### Argumentos

- `target_feature` (str): campo do metadado para filtro na deleção.
- `target_id` (str): valor do campo usado para selecionar os vetores.
- `namespace` (str): namespace para ação de deleção, usa principal se vazio.
- `features` (list): lista de campos de metadados considerados na deleção.

### Retornos

- `dict`: resposta do Pinecone indicando resultado da operação.

### Raises

Nenhum.

### Exemplos

```python
delete_response = tester.delete(
    target_feature="source",
    target_id="example_text.txt",
    namespace="main_namespace",
    features=["file_id", "source"]
)
print(delete_response)
```

----------------------------

Com esta documentação, desenvolvedores podem compreender rapidamente como usar a classe `TestPineconeVectorStore` para manipular vetores e metadados no Pinecone, facilitando a construção de sistemas com busca semântica.