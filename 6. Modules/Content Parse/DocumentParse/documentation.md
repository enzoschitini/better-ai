# Classe `DocumentParse`

## Visão Geral

A classe `DocumentParse` tem como objetivo orquestrar o pipeline completo de processamento de documentos, desde a extração do conteúdo bruto do arquivo até o salvamento dos dados processados em um banco de dados NoSQL. Ela é responsável por convergir diversas etapas fundamentais para transformar arquivos digitais em dados estruturados prontos para uso, automatizando o fluxo de parsing com validações, cálculos de custo e integração com sistemas de armazenamento.

Este componente é fundamental em sistemas que precisam interpretar documentos eletrônicos (como PDFs, TXT, etc.) e extrair informações específicas conforme um esquema pré-definido. Na prática, pode ser utilizada em pipelines de machine learning, APIs de conversão de documentos, e aplicações que dependem de extração automatizada de dados.

Com esta classe, o desenvolvedor pode enviar um job contendo um arquivo e suas configurações, e receber de volta os dados estruturados do documento com custos computacionais calculados, além de ter o resultado armazenado para futuras consultas.

----------------------------

## Fluxo de Execução

1. **Criação da instância da classe:** Inicialização com o job_id, metadata JSON, schema JSON, conteúdo do arquivo (em bytes), extensão do arquivo e configurações opcionais para parsing.

2. **Chamada do método `run()`:** Este método executa todo o fluxo interno, responsável por coordenar as etapas.

3. **Carregamento e validação dos dados:** O método privado `_load_schema_and_config()` desserializa os JSONs de metadata e schema, além de mesclar configurações padrão e customizadas.

4. **Extração do conteúdo do arquivo:** `_extract_file_content()` utiliza o `FileContentExtractor` para obter o texto bruto do arquivo conforme sua extensão.

5. **Parsing do conteúdo extraído:** `_parse_content()` invoca o `ContentParsingAgent`, que mapeia o texto extraído para a estrutura definida pelo schema.

6. **Cálculo dos custos:** `_calculate_costs()` determina o custo de processamento com base no modelo de linguagem usado e tokens consumidos, convertendo os valores para moeda local.

7. **Construção da resposta:** `_build_response()` cria o payload que será enviado pela API e o payload que será salvo no banco.

8. **Persistência dos resultados:** `_save()` salva os dados processados no banco NoSQL configurado.

9. **Retorno:** O `run()` retorna a resposta pronta para API contendo o conteúdo extraído e estruturado.

----------------------------

## Tabela de Métodos da Classe

| Método  | Descrição                                      |
|---------|-----------------------------------------------|
| `__init__` | Inicializa o job de parsing com dados e configurações fornecidas |
| `run`      | Executa o pipeline completo de parsing do documento |
| `_load_schema_and_config` | Valida e carrega metadata, schema e configuração JSON |
| `_extract_file_content` | Extrai o texto bruto do arquivo usando o extractor |
| `_parse_content`        | Roda o agente que formata o conteúdo conforme schema |
| `_calculate_costs`      | Calcula custos de tokens usados e converte valores |
| `_build_response`       | Monta payloads para API e banco de dados |
| `_save`                 | Persiste resultado processado no banco NoSQL |

----------------------------

## Variáveis de Ambiente

Nenhuma variável de ambiente explícita é requerida diretamente nesta classe. A configuração padrão e informações do banco são obtidas via `DocumentParseConfig`, que pode ter sua própria gestão de ENVs (não exibida aqui).

----------------------------

## Pontos Importantes da Arquitetura e Insights

- **Encapsulamento e separação clara de responsabilidades:** A classe organiza em métodos privados cada etapa do fluxo, facilitando manutenção e testes.

- **Uso de composição:** A classe utiliza outras classes para responsabilidades específicas, como `FileContentExtractor` para extração, `ContentParsingAgent` para parsing e `DocumentStore` para persistência, seguindo o princípio da responsabilidade única.

- **Tratamento robusto de erros:** Usa exceções HTTP para validar JSONs fornecidos, garantindo que o fluxo só segue com dados válidos.

- **Cálculo dinâmico de custos:** Integra com serviços externos para cálculo do custo baseado em tokens processados e conversão cambial atual, adequado para sistemas pagos por uso.

- **Flexibilidade na configuração:** Permite configuração customizada via JSON que é mesclada com a configuração padrão para adaptar o comportamento do parsing.

----------------------------

# Descrição da Classe e Métodos

## Classe `DocumentParse`

### Descrição

Classe que gerencia o processamento completo de documentos para extração de conteúdo estruturado. Recebe o conteúdo do arquivo, metadados, esquema e configurações. Executa a extração de texto, parsing segundo o schema, cálculo de custos operacionais e armazenamento do resultado processado. Fornece uma resposta pronta para uso por APIs.

### Argumentos do Construtor

| Argumento      | Tipo          | Descrição                                                  | Valor Padrão |
|----------------|---------------|------------------------------------------------------------|--------------|
| `job_id`       | str           | Identificador único do job de processamento                | -            |
| `metadata`     | dict/str JSON | Metadados associados ao documento (JSON string esperada)   | -            |
| `schema`       | str           | JSON string definindo o esquema dos dados esperados        | -            |
| `file_bytes`   | BytesIO       | Conteúdo binário do arquivo a ser processado                | -            |
| `file_extension` | str         | Extensão do arquivo (exemplo: '.pdf', '.txt')               | -            |
| `config`       | Optional[str] | JSON string contendo configuração customizada para parsing  | None         |

---

### 1. `__init__`

### Descrição

Inicializa o objeto `DocumentParse` com as informações essenciais para o processamento do documento, configurando parâmetros e carregando configurações padrão do sistema.

### Argumentos

- job_id (str): Identificador do job de processamento.
- metadata (dict/str): Metadados no formato JSON string.
- schema (str): Schema JSON para estruturação dos dados.
- file_bytes (BytesIO): Bytes do arquivo.
- file_extension (str): Extensão do arquivo.
- config (Optional[str]): Configuração customizada em JSON string (opcional).

### Retornos

- Não retorna valor.

### Raises

- Nenhum.

### Exemplos

```python
document_parse = DocumentParse(
    job_id="job123",
    metadata='{"author": "John Doe"}',
    schema='{"type": "object", "properties": {"title": {"type": "string"}}}',
    file_bytes=BytesIO(b"conteudo do arquivo"),
    file_extension=".txt",
    config=None
)
```

---

### 2. `run`

### Descrição

Executa o pipeline completo de processamento do documento, da validação dos dados à extração, parsing, cálculos e armazenamento, retornando o resultado final pronto para API.

### Argumentos

- Nenhum.

### Retornos

- dict: Resposta formatada para a API contendo o job_id e o conteúdo processado.

### Raises

- HTTPException: em caso de JSONs inválidos nos dados fornecidos.

### Exemplos

```python
response = document_parse.run()
print(response)
# Exemplo de saída:
# {
#   "job_id": "job123",
#   "content": {...dados extraídos e formatados...}
# }
```

---

### 3. `_load_schema_and_config`

### Descrição

Realiza o parsing e validação dos JSONs de metadata, schema e configuração, fundindo configuração padrão com a customizada quando fornecida.

### Argumentos

- Nenhum.

### Retornos

- Não retorna valor.

### Raises

- HTTPException: se a metadata, schema ou config forem JSONs inválidos.

### Exemplos

```python
document_parse._load_schema_and_config()
# Inicializa self.metadata_data, self.schema_data e self.config_data com os valores carregados.
```

---

### 4. `_extract_file_content`

### Descrição

Usa a classe `FileContentExtractor` para extrair o conteúdo textual bruto do arquivo com base em sua extensão.

### Argumentos

- Nenhum.

### Retornos

- Não retorna valor.

### Exemplos

```python
document_parse._extract_file_content()
print(document_parse.result_extract)
# Exemplo de saída:
# {'response': 'Texto extraído do arquivo'}
```

---

### 5. `_parse_content`

### Descrição

Executa o agente de parsing `ContentParsingAgent`, que processa o texto extraído e o estrutura conforme o schema esperado, preparando uma resposta formatada.

### Argumentos

- Nenhum.

### Retornos

- Não retorna valor.

### Exemplos

```python
document_parse._parse_content()
print(document_parse.agent_response)
# Exemplo:
# {'content': {...dados estruturados...}, 'metadata': {...informações de processamento...}}
```

---

### 6. `_calculate_costs`

### Descrição

Calcula o custo do processamento baseado nos tokens de entrada e saída usados pelo modelo, utilizando a taxa de câmbio atual para conversão em moeda local (BRL).

### Argumentos

- Nenhum.

### Retornos

- Não retorna valor.

### Exemplos

```python
document_parse._calculate_costs()
print(document_parse.input_cost, document_parse.output_cost, document_parse.rate)
# Valores numéricos representando os custos
```

---

### 7. `_build_response`

### Descrição

Monta os payloads que serão retornados pela API e salvos no banco, consolidando conteúdo extraído e informações de custo e processo.

### Argumentos

- Nenhum.

### Retornos

- Não retorna valor.

### Exemplos

```python
document_parse._build_response()
print(document_parse.api_response)
# {'job_id': 'job123', 'content': {...dados extraídos...}}
```

---

### 8. `_save`

### Descrição

Salva os dados processados no banco de dados NoSQL configurado, usando a classe `DocumentStore`.

### Argumentos

- Nenhum.

### Retornos

- Não retorna valor.

### Exemplos

```python
document_parse._save()
# Dados persistidos no banco conforme configuração automática da classe
```

## Use

```python

if __name__ == "__main__":
    # Exemplo de uso
    job_id = "job_123"
    metadata = {"user_id": "user_456"}

    schema = """
    {
      "summary": {
        "type": "str",
        "description": "Resumo do conteúdo do arquivo"
      }
    }
    """
    config = """
    {
      "model_provider": "OpenAI",
      "model_id": "gpt-4.1-mini",
      "debug_mode": true,
      "instructions": "Extraia dados do texto",
      "description": "Leia o texto e extraia as informações relevantes conforme o esquema definido. Retorne um JSON estruturado com os dados extraídos. Caso não encontre alguma informação, retorne null para aquele campo."
    }
    """

    with open("src\\text_parse\\module\\Endurance.pdf", "rb") as f:
        file_bytes = BytesIO(f.read())

    parser = DocumentParse(
        job_id=job_id,
        metadata=metadata,
        schema=schema,
        config=config,
        file_bytes=file_bytes,
        file_extension="pdf"
    )

    response = parser.run()

    print("\nResposta do parser:")
    print(json.dumps(response, indent=2))

# python -m src.content_parse.module.simple_file_parse
```

---

# Fim da documentação da classe `DocumentParse`.