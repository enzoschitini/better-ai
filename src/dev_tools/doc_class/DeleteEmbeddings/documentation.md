# Classe `DeleteEmbeddings`

## Visão Geral

A classe `DeleteEmbeddings` foi desenvolvida para gerenciar a exclusão de *embeddings* armazenados em um banco de dados vetorial (vector database). Ela permite remover entradas específicas conforme chaves e valores alvos fornecidos, garantindo controle refinado sobre os dados que devem ser eliminados. Essa classe é especialmente útil em sistemas que armazenam representações vetoriais para buscas semânticas, onde a manutenção da base atualizada é crucial.

Ela resolve o problema de otimizar a limpeza e manutenção dos dados vetoriais, possibilitando exclusão seletiva em múltiplos namespaces, inclusive um escopo global, com segurança e validação dos alvos que podem ser impactados. Na prática, um desenvolvedor pode utilizá-la para apagar dados relacionados a bases de conhecimento específicas, mantendo a integridade dos dados em outros contextos.

---

## Fluxo de Execução

1. **Inicialização**: A classe é instanciada com configurações do banco vetorial (opcional). Se nenhuma configuração é passada, valores padrões são carregados da configuração geral.

2. **Validação dos Alvos**: Antes de qualquer exclusão, as chaves alvo (target keys) são validadas para garantir que estão dentro dos limites permitidos, evitando exclusão fora do escopo desejado.

3. **Estabelecer Conexão**: A conexão com o banco de dados vetorial é criada, inicializando os clientes necessários para realizar as operações.

4. **Execução da Exclusão**: Para cada par chave-valor alvo, realiza a exclusão nos namespaces configurados (principal e, opcionalmente, global), coletando eventos que detalham os vetores deletados.

5. **Agregação dos Resultados**: Os eventos são agregados por namespace, somando quantidades de vetores deletados e preparando um resumo.

6. **Retorno do Resultado**: Ao final, um dicionário é retornado com o sucesso da operação, total de vetores deletados e detalhes por namespace.

---

## Tabela de Métodos da Classe

| Método            | Descrição                                                       |
|-------------------|----------------------------------------------------------------|
| `__init__`        | Inicializa a classe com configurações do banco vetorial.       |
| `delete`          | Executa o processo completo de exclusão conforme chaves e valores. |
| `_get_vector_db`  | Estabelece a conexão com o banco de dados vetorial.            |
| `_validate_targets`| Valida se as chaves alvo estão dentro dos limites permitidos.  |
| `_delete_from_namespaces` | Realiza a exclusão em namespaces configurados.           |
| `_aggregate_events`| Agrega eventos de exclusão por namespace.                      |

---

## Variáveis de Ambiente

Não há variáveis de ambiente diretamente utilizadas por esta classe. As configurações do banco de dados vetorial são obtidas via objeto de configuração `GetConfig`.

---

## Pontos Importantes da Arquitetura e Insights

- **Design Modular e Privado**: A classe utiliza métodos privados para organizar as etapas (validação, conexão, exclusão, agregação), garantindo coesão e clareza no fluxo.

- **Injeção de Configuração**: Permite sobrepor configurações padrão, facilitando o uso em múltiplos ambientes e testes.

- **Traces e Logs**: Integração com sistema de *tracing* (`ApplicationTracing`) para registro detalhado das ações, útil para auditoria e debugging.

- **Manuseio de Múltiplos Namespaces**: A classe suporta exclusão em namespaces distintos, incluindo um escopo global opcional, o que indica flexibilidade para cenários mais complexos de armazenamento.

- **Tratamento Robusto de Erros**: Exceções são capturadas e relançadas com mensagens claras, mantendo o controle do fluxo e a transparência dos erros.

- **Uso de Classes Externas**: Depende das classes `GetConfig`, `VectorDBConnection` e `ApplicationTracing`, o que indica integração com módulos de configuração, acesso a banco e sistema de logs/tracing.

---

# Descrição da Classe e Métodos

## Classe `DeleteEmbeddings`

### Descrição

Classe responsável por gerenciar a exclusão seletiva de embeddings em um banco vetorial, com suporte para múltiplos namespaces e validação rigorosa das chaves alvo para garantir exclusões seguras e controladas.

### Argumentos do Construtor

| Argumento           | Tipo  | Descrição                                                       | Valor Padrão |
|---------------------|-------|-----------------------------------------------------------------|--------------|
| `vector_db_settings`| dict  | Configurações para conexão com o banco vetorial. Se não informado, usa padrões da configuração global. | `None`       |

---

### 1. `__init__`

### Descrição

Inicializa a instância da classe definindo as configurações do banco vetorial a partir dos padrões e configurando variáveis internas para conexão futura.

### Argumentos

- `vector_db_settings` (dict): Configurações personalizadas para o banco vetorial.

### Retornos

- Não retorna valor.

### Raises

- Nenhum.

### Exemplos

```python
# Instancia com configurações padrão
de = DeleteEmbeddings()

# Instancia com configuração personalizada
custom_settings = {"index_name": "my_index", "main_namespace": "app_main"}
de_custom = DeleteEmbeddings(vector_db_settings=custom_settings)
```

---

### 2. `_get_vector_db`

### Descrição

Estabelece a conexão com o banco de dados vetorial utilizando as configurações atuais da instância, configurando os atributos internos de cliente e serviço para operações futuras.

### Argumentos

- Nenhum.

### Retornos

- Não retorna valor.

### Raises

- `RuntimeError`: caso não seja possível estabelecer conexão com o banco vetorial.

### Exemplos

```python
# Uso interno para garantir conexão antes das operações
delete_embeddings._get_vector_db()
```

---

### 3. `_validate_targets`

### Descrição

Verifica se as chaves alvo para exclusão estão dentro das chaves permitidas para limitar o escopo da operação, gerando erro em caso negativo.

### Argumentos

- `target_keys` (list): Lista de nomes de chaves alvo para validação.
- `targets_to_limit` (list ou None): Lista de chaves permitidas para exclusão. Se None, não aplica restrição.

### Retornos

- Não retorna valor.

### Raises

- `ValueError`: se nenhum valor de `target_keys` estiver contido em `targets_to_limit`.

### Exemplos

```python
# Valida que "knowledge_base_id" está entre os alvos permitidos
_delete._validate_targets(["knowledge_base_id"], ["knowledge_base_id"])

# Levanta erro se sem correspondência
# _delete._validate_targets(["user_id"], ["knowledge_base_id"])  # ValueError
```

---

### 4. `_delete_from_namespaces`

### Descrição

Realiza a exclusão dos documentos que possuem uma chave e valor alvo nos namespaces principal e, opcionalmente, no namespace global, retornando eventos detalhados.

### Argumentos

- `target_name` (str): Nome da chave alvo para exclusão.
- `target_value` (str): Valor associado para filtrar documentos a excluir.
- `main_ns` (str): Namespace principal onde será feita a exclusão.
- `global_ns` (str): Namespace global para exclusão opcional.
- `save_global` (bool): Define se também deve excluir no namespace global.

### Retornos

- `list`: Lista de eventos com detalhes da exclusão em cada namespace.

### Raises

- Nenhum diretamente (exceções internas seriam propagadas).

### Exemplos

```python
events = delete_embeddings._delete_from_namespaces(
    "knowledge_base_id", "kb_001", "main_ns", "global_ns", True
)
# events contém detalhes de vetores deletados em cada namespace
```

---

### 5. `_aggregate_events`

### Descrição

Agrega uma lista de eventos de exclusão, somando quantidades e organizando por namespace para facilitar análise e estruturação do resultado.

### Argumentos

- `events` (list): Lista de eventos individuais de exclusão.

### Retornos

- `list`: Lista agregada por namespace contendo totais e itens detalhados.

### Raises

- Nenhum.

### Exemplos

```python
aggregated = delete_embeddings._aggregate_events(events)
# aggregated terá estrutura resumida por namespaces
```

---

### 6. `delete`

### Descrição

Método público principal que orquestra toda a operação de exclusão: valida os alvos, conecta ao banco, executa exclusões em todos os pares chave-valor, agrega e retorna os resultados consolidados.

### Argumentos

- `target_keys` (list): Lista de nomes das chaves para exclusão.
- `target_values` (list): Lista de valores correspondentes para filtrar exclusões.
- `targets_to_limit` (list ou None): Lista opcional para restringir as chaves que podem ser usadas para exclusão.

### Retornos

- `dict`: Dicionário contendo:
    - `success` (bool): Indica sucesso da operação.
    - `summary` (dict): Resumo com total de vetores deletados e quantidades de namespaces impactados.
    - `deleted_by_namespace` (list): Listagem detalhada por namespace.

### Raises

- `ValueError`: Se as chaves alvo não estiverem permitidas.
- `RuntimeError`: Se falhar conexão ou operação no banco vetorial.

## Uso

```python
if __name__ == "__main__":
    import json

    payload = {
        "vector_db_settings": {
            "index_name": "my_index",
            "embedding_model": "text-embedding-3-small",
            "main_namespace": "main_ns",
            "global_namespace": "global_ns",
        },
        "target_keys": ["knowledge_base_id"],
        "target_values": ["kb_12345"],
        "targets_to_limit": ["knowledge_base_id"]
    }

    delete_embeddings = DeleteEmbeddings()
    result = delete_embeddings.delete(
        target_keys=payload["target_keys"],
        target_values=payload["target_values"],
        targets_to_limit=payload["targets_to_limit"]
    )

    print(json.dumps(result, indent=2))


# python -m src.embedding.modules.delete_embeddings
```

### Output:

```python
{
  "success": true,
  "summary": {
    "total_deleted_vectors": 12,
    "namespaces_count": 2
  },
  "deleted_by_namespace": [
    {
      "namespace": "main_ns",
      "deleted_vectors": 6,
      "items": [
        {
          "target_name": "knowledge_base_id",
          "target_value": "kb_12345",
          "deleted_vectors": 6
        }
      ]
    },
    {
      "namespace": "global_ns",
      "deleted_vectors": 6,
      "items": [
        {
          "target_name": "knowledge_base_id",
          "target_value": "kb_12345",
          "deleted_vectors": 6
        }
      ]
    }
  ]
}
```


---

Este documento oferece um guia estruturado e didático para a compreensão e utilização da classe `DeleteEmbeddings`, facilitando sua integração e uso correto em projetos que trabalham com exclusão seletiva de embeddings em banco de dados vetoriais.