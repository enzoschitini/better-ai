# Classe `EmbeddingFile`

## Visão Geral

A classe `EmbeddingFile` gerencia todo o fluxo para processar o conteúdo de um arquivo e criar embeddings para armazenamento em um banco de dados vetorial Pinecone. Ela foi projetada para extrair o conteúdo textual de arquivos binários, preparar payloads para criação de embeddings, calcular o uso e custo de tokens, armazenar as embeddings no vector store, além de salvar metadados do processo e oferecer suporte a rollback em caso de falhas.

O principal problema que resolve é a automatização completa e robusta do processo de transformação de arquivos para uma representação vetorial capaz de ser pesquisada semanticamente. Essa classe pode ser usada na prática em sistemas de busca inteligente, motores de recomendação, ou em pipelines que necessitem indexar e buscar documentos por similaridade semântica, garantindo rastreabilidade e consistência.

---

## Fluxo de Execução

1. **Inicialização:** Cria uma instância da classe recebendo um `payload` que contém informações do job, arquivo, configurações do vector store e metadados opcionais. Normaliza o payload, valida dados essenciais e configura o cliente Pinecone.

2. **Extração de Conteúdo:** Usa `FileContentExtractor` para extrair o texto do arquivo, independente do formato, obtendo o conteúdo que servirá para embedding.

3. **Construção do Payload de Embedding:** Combina o conteúdo extraído com conteúdos adicionais gerados por um pipeline (se informado) via `AggregateEmbeddingContent`, e agrega metadados importantes.

4. **Cálculo do Uso e Custos:** Para cada parte do conteúdo preparado, calcula o total de tokens usados e custo aproximado com base no modelo de embedding, incluindo conversão para dólar usando taxa de câmbio atual.

5. **Armazenamento dos Embeddings:** Serializa o conteúdo de embedding em JSON e cria os vetores no banco Pinecone, unindo metadados e permitindo flags opcionais.

6. **Salvamento dos Metadados do Processo:** Persiste em banco NoSQL as informações do job, uso, respostas da embedding e arquivo, garantindo integridade e rastreabilidade. Se falhar, executa rollback no Pinecone.

7. **Finalização:** Retorna identificadores do job e arquivo para controle externo.

---

## Tabela de Métodos da Classe

| Método                 | Descrição                                               |
|------------------------|---------------------------------------------------------|
| `__init__`             | Inicializa a instância, valida payload e configura DB. |
| `_init_tracking`        | Inicializa o tracking do processo.                      |
| `_calculate_usage`      | Calcula tokens e custo para um conteúdo e modelo.       |
| `_get_vector_db`        | Configura cliente e serviço Pinecone.                   |
| `_rollback_vector_store`| Realiza rollback deletando embeddings em Pinecone.     |
| `extract_file_content`  | Extrai texto de arquivo pelo tipo e bytes.              |
| `build_embedding_payload` | Prepara conteúdo e metadados para embedding.          |
| `calculate_usage_summary` | Calcula resumo total do uso e custo do embedding.      |
| `store_embeddings`      | Gera e salva embeddings no vector store.                |
| `save_process_metadata` | Salva metadados do processo em banco documental.       |
| `run`                  | Executa todo o fluxo completo de embedding.             |

---

## Pontos Importantes da Arquitetura e Insights

- A classe utiliza composição com vários módulos externos especializados, como `PineconeClient` para banco vetorial, `FileContentExtractor` para parsing de arquivos variados, e serviços para cálculo de tokens e pricing, garantindo modularidade.

- O uso de deepcopy no payload evita efeitos colaterais externos, importante para evitar estados inconsistentes.

- Há um mecanismo de rollback específico para manter consistência no banco vetorial caso o salvamento dos metadados falhe, aumentando robustez.

- A separação das responsabilidades está bem definida: extração, preparação, cálculo, armazenamento e persistência documental.

- É utilizado um sistema interno de tracing para logs e monitoramento que auxilia no debug e manutenção.

- Configurações de vector store e pipeline são flexíveis e extensíveis via dicionários no payload, permitindo customização sem alterar o código.

---

# Descrição da Classe e Métodos

## Classe `EmbeddingFile`

### Descrição

Classe responsável por processar um arquivo binário, extrair e agregar conteúdo para criar embeddings vetoriais, calculando custos envolvidos e salvando toda a informação em bancos Pinecone e NoSQL. Opera com controle de rastreamento e rollback para garantir integridade.

### Argumentos do Construtor

| Argumento | Tipo                  | Descrição                                               | Valor Padrão |
|-----------|-----------------------|---------------------------------------------------------|--------------|
| payload   | `dict` ou `None`      | Dados necessários contendo job, arquivo, metadados e configurações para embedding. | None         |

---

### 1. `__init__`

#### Descrição

Inicializa a instância da classe, valida campos obrigatórios no payload, normaliza estruturas e configura o cliente do banco vetorial Pinecone com base nas configurações providas.

#### Argumentos

- `payload` (`dict` | `None`): Dicionário com informações do trabalho, arquivo, configurações e metadados.

#### Retornos

- Não retorna valor.

#### Raises

- `ValueError`: Se campos obrigatórios estiverem ausentes (ex. `job_id` ou campos em `file_info`).
- `RuntimeError`: Para qualquer erro genérico na inicialização.

#### Exemplos

```python
embedding = EmbeddingFile(payload={
    "job_id": "job_123",
    "file_info": {
        "name": "documento",
        "extension": "pdf",
        "bytes": b"%PDF-..."
    }
})
```

---

### 2. `_init_tracking`

#### Descrição

Inicializa o tracking para monitoramento do processo, adicionando o payload às informações rastreadas.

#### Argumentos

- Nenhum.

#### Retornos

- Não retorna valor.

#### Raises

- `RuntimeError`: Falha ao iniciar tracking.

#### Exemplos

```python
embedding._init_tracking()
```

---

### 3. `_calculate_usage`

#### Descrição

Calcula total de tokens e custo estimado do conteúdo fornecido conforme o modelo informado.

#### Argumentos

- `model` (`str`): Nome do modelo de embedding usado.
- `content` (`str`): Texto cujo uso deve ser calculado.

#### Retornos

- `dict`: Contém `caracter_count` (int), `tokens` (int) e `cost_usd` (str formatado).

#### Raises

- `RuntimeError`: Erro durante o cálculo.

#### Exemplos

```python
usage = embedding._calculate_usage("text-embedding-xyz", "Exemplo de texto para contar tokens")
print(usage)
# {'caracter_count': 31, 'tokens': 8, 'cost_usd': '0.000120'}
```

---

### 4. `_get_vector_db`

#### Descrição

Inicializa clientes e serviços para conexão com o banco vetorial Pinecone com parâmetros configurados.

#### Argumentos

- Nenhum.

#### Retornos

- Não retorna valor.

#### Raises

- `RuntimeError`: Falha ao configurar cliente Pinecone.

#### Exemplos

```python
embedding._get_vector_db()
```

---

### 5. `_rollback_vector_store`

#### Descrição

Executa rollback deletando embeddings referentes ao arquivo atual nos namespaces principal e global do Pinecone para manter consistência.

#### Argumentos

- Nenhum.

#### Retornos

- `dict`: Resultado detalhado da deleção nos dois namespaces.

#### Raises

- `RuntimeError`: Falha durante o rollback.

#### Exemplos

```python
resultado_rollback = embedding._rollback_vector_store()
print(resultado_rollback)
# {'main_namespace': True, 'global_namespace': True}
```

---

### 6. `extract_file_content`

#### Descrição

Extrai o conteúdo em texto do arquivo bruto, utilizando sua extensão para decidir o método de extração.

#### Argumentos

- `file_extension` (`str`): Extensão do arquivo (e.g., "pdf", "txt").
- `file_bytes` (`bytes`): Arquivo em bytes para extração.

#### Retornos

- `str`: Conteúdo textual extraído.

#### Raises

- `RuntimeError`: Qualquer falha na extração.

#### Exemplos

```python
texto = embedding.extract_file_content("pdf", b"%PDF-1.4 ...")
print(texto)
# "Este é o texto extraído do PDF"
```

---

### 7. `build_embedding_payload`

#### Descrição

Prepara o payload que será embeddado, combinando o conteúdo do arquivo com conteúdo adicional processado via pipeline se fornecido, e agrega metadados para o embedding.

#### Argumentos

- `identifiers` (`dict`): Identificadores do conteúdo, como `file_id`.
- `file_info` (`dict`): Informações do arquivo, nome e extensão.
- `file_content` (`str`): Texto extraído do arquivo.
- `embedding_metadata` (`dict`, opcional): Metadados adicionais.
- `pipeline` (`dict`, opcional): Configurações para geração de conteúdo extra.

#### Retornos

- `tuple`: `(prepared_content, prepared_metadata)`, onde `prepared_content` é o conteúdo combinado e `prepared_metadata` contém os metadados.

#### Raises

- `RuntimeError`: Falha na construção do payload.

#### Exemplos

```python
conteudo, metadados = embedding.build_embedding_payload(
    identifiers={"file_id": "abc123"},
    file_info={"name": "doc", "extension": "txt"},
    file_content="conteúdo extraído...",
    embedding_metadata={"author": "Maria"},
    pipeline={"steps": [...]}
)
```

---

### 8. `calculate_usage_summary`

#### Descrição

Calcula um resumo de uso com total de caracteres, tokens e custos para todo o conteúdo preparado em partes, usando o modelo indicado.

#### Argumentos

- `model` (`str`): Nome do modelo de embedding.
- `prepared_content` (`dict`): Conteúdos segregados para cálculo.

#### Retornos

- `dict`: Resumo com totais e, se aplicável, detalhamento das partes.

#### Raises

- `RuntimeError`: Falha no cálculo do resumo.

#### Exemplos

```python
summary = embedding.calculate_usage_summary("text-embedding-xyz", {"file_content": "texto", "extra": "adic."})
print(summary)
# {'total_caracter_count': 15, 'total_tokens': 4, 'total_cost_usd': '0.000060', 'exchange_rate': 5.2, 'parts': {...}}
```

---

### 9. `store_embeddings`

#### Descrição

Gera embeddings do conteúdo preparado e armazena na base Pinecone, adicionando metadados e flags se houver.

#### Argumentos

- `embedding_content` (`str`): JSON string contendo conteúdo para embedding.
- `embedding_metadata` (`dict`): Metadados associados para indexação.
- `flags` (`dict`, opcional): Flags adicionais a serem combinadas nos metadados.

#### Retornos

- `dict`: Resposta do serviço de armazenamento Pinecone.

#### Raises

- `RuntimeError`: Falha na criação ou armazenamento das embeddings.

#### Exemplos

```python
response = embedding.store_embeddings(
    embedding_content='{"file_content": "texto para embed"}',
    embedding_metadata={"file_id": "abc123", "file_name": "doc.txt"}
)
print(response)
```

---

### 10. `save_process_metadata`

#### Descrição

Salva os metadados do processo de embedding em um banco documental NoSQL. Em caso de falha, dispara rollback no Pinecone para evitar inconsistências.

#### Argumentos

- `usage_summary` (`dict`): Sumário de uso e custos calculados.
- `embed_response` (`dict`): Dados retornados pelo armazenamento dos embeddings.

#### Retornos

- `dict`: Resposta da operação de salvamento.

#### Raises

- `RuntimeError`: Falha ao salvar metadados, após tentar rollback.

#### Exemplos

```python
save_resp = embedding.save_process_metadata(usage_summary=summary, embed_response=response)
print(save_resp)
```

---

### 11. `run`

#### Descrição

Executa a sequência completa: extrai conteúdo, prepara payload, calcula uso, cria embeddings e salva metadados. Retorna identificadores do job para controle.

#### Argumentos

- Nenhum.

#### Retornos

- `dict`: Contendo `job_id` e `file_id`.

#### Raises

- `RuntimeError`: Qualquer erro durante o fluxo completo.

#### Exemplos

```python
result = embedding.run()
print(result)
# {'job_id': 'job_123', 'file_id': 'abc123'}
```

---

Esta documentação foi construída para facilitar a compreensão e implementação da classe `EmbeddingFile` em sistemas que exigem manipulação e indexação avançada de documentos via embeddings.