# Classe `JsonToPydantic`

## Visão Geral

A classe `JsonToPydantic` foi desenvolvida para facilitar a conversão dinâmica de dicionários JSON em modelos Pydantic com tipagem automática dos campos. Esse processo é bastante útil quando se trabalha com dados JSON não estruturados ou variáveis, e há necessidade de validar e manipular esses dados utilizando a robustez que o Pydantic oferece.

Basicamente, a classe permite transformar um JSON arbitrário em uma classe Pydantic gerada em tempo de execução, inferindo os tipos básicos dos valores (como string, inteiro, float, booleano, listas e dicionários). Isso simplifica workflows que envolvem validação de dados, testes ou manipulação onde o esquema JSON não está previamente definido.

Na prática, basta criar uma instância de `JsonToPydantic`, passar o JSON como dicionário para os métodos da classe, e obter modelos e instâncias tipadas automaticamente, prontos para validação e acesso facilitado aos dados.

## Fluxo de Execução

1. Instancia a classe `JsonToPydantic`, opcionalmente passando um nome para o modelo Pydantic que será criado (`model_name`).

2. Chama o método `build_model` passando um dicionário JSON para criar um modelo Pydantic dinâmico. Este método infere os tipos dos campos baseando-se nos valores do dicionário.

3. Utiliza o método `parse` para criar uma instância do modelo Pydantic previamente gerado, preenchida com os dados do dicionário JSON.

4. Caso qualquer etapa falhe (inferência de tipos, construção do modelo, instanciamento), a classe lança exceções do tipo `RuntimeError` para indicar erros explicativos.

## Tabela de Métodos da Classe

| Método    | Descrição                                                      |
|-----------|---------------------------------------------------------------|
| `__init__`| Inicializa a classe definindo o nome do modelo Pydantic.      |
| `_infer_type` | Identifica o tipo Python de um valor para tipagem do campo.  |
| `build_model`| Cria dinamicamente um modelo Pydantic com base no dicionário.|
| `parse`   | Cria uma instância do modelo preenchida com os dados JSON.    |

## Pontos Importantes da Arquitetura e Insights

- A classe utiliza a biblioteca `pydantic` para criar modelos dinamicamente (`create_model`) e para validação robusta dos dados.
- A inferência feita pelo método `_infer_type` cobre tipos comuns do Python e retorna `Any` quando o tipo não é claramente identificado.
- O uso de exceções do tipo `RuntimeError` com mensagens específicas facilita o entendimento de possíveis falhas no fluxo.
- A classe não depende de variáveis de ambiente externas para funcionar.
- A abordagem adotada facilita a criação de esquemas dinâmicos, útil para sistemas que consomem JSONs com estrutura variável ou desconhecida na fase de desenvolvimento.

# Descrição da Classe e Métodos

## Classe `JsonToPydantic`

### Descrição

Classe para criação dinâmica de modelos Pydantic a partir de dicionários JSON, permitindo validação e tipagem automática dos campos conforme os dados recebidos.

### Argumentos do Construtor

| Argumento   | Tipo   | Descrição                               | Valor Padrão    |
|-------------|--------|---------------------------------------|-----------------|
| model_name  | str    | Nome do modelo Pydantic criado        | "DynamicModel"  |

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa o objeto definindo o nome do modelo Pydantic que será criado dinamicamente.

### Argumentos

- model_name (str): Nome do modelo Pydantic (opcional).

### Retornos

- Não retorna valor.

### Raises

- Nenhum.

### Exemplos

```python
converter = JsonToPydantic()  # modelo padrão "DynamicModel"
converter_custom = JsonToPydantic("MeuModelo")
```

---

### 2. `_infer_type`

### Descrição

Identifica o tipo Python correspondente ao valor fornecido para definir o tipo do campo no modelo.

### Argumentos

- value (Any): Valor para ser analisado e tipado.

### Retornos

- Type: Tipo Python correspondente (str, int, float, bool, list, dict ou Any).

### Raises

- RuntimeError: Caso ocorra erro durante a inferência do tipo.

### Exemplos

```python
tipo = converter._infer_type("texto")  # retorna <class 'str'>
tipo = converter._infer_type(123)      # retorna <class 'int'>
```

---

### 3. `build_model`

### Descrição

Constrói e retorna um modelo Pydantic gerado dinamicamente com campos e tipos baseados no dicionário JSON fornecido.

### Argumentos

- data (Dict[str, Any]): Dicionário com dados para inferência do modelo.

### Retornos

- Type[BaseModel]: Classe do modelo Pydantic criado.

### Raises

- RuntimeError: Caso ocorra erro durante a criação do modelo.

### Exemplos

```python
modelo = converter.build_model({"nome": "Ana", "idade": 30})
# Retorna um modelo equivalente a:
# class DynamicModel(BaseModel):
#     nome: str
#     idade: int
```

---

### 4. `parse`

### Descrição

Gera um modelo Pydantic a partir dos dados e retorna uma instância preenchida com esses dados.

### Argumentos

- data (Dict[str, Any]): Dicionário JSON a ser convertido em instância do modelo.

### Retornos

- BaseModel: Instância do modelo Pydantic com os dados validados.

### Raises

- RuntimeError: Caso ocorra falha na criação ou validação da instância.

### Exemplos

```python
if __name__ == "__main__":
    data = {
        "text": "A empresa TechNova está crescendo rapidamente.",
        "task": "Se o nome da empresa for TechNova, troque por BetterAI"
    }
    parser = JsonToPydantic("ResearchRequest")
    request = parser.parse(data)
    
    print(request)
    print(type(request))

# python -m src.content_parse.pydantic_shema
```

---

## Mapeamento formas de schema

### 1. Entradas aceitas pela rota

Formato do request: `multipart/form-data`.

Campos:

- `job_id` (obrigatório): `str`
- `metadata` (obrigatório): `str` contendo JSON válido
- `document_schema` (obrigatório): `str` contendo JSON válido
- `file` (obrigatório): arquivo
- `config` (opcional): `str` contendo JSON válido

Regras de arquivo nesta rota:

- Extensões permitidas: `txt`, `md`, `pdf`, `docx`
- Tamanho máximo: `50 MB`

Erros comuns de entrada:

- `Invalid JSON in metadata`
- `Invalid JSON in schema`
- `Invalid JSON in config`

### 2. Importante: quem interpreta o `document_schema`

- `document_schema` **não** é convertido por `JsonToPydantic`.
- Na rota, ele é convertido por `GeneratePydanticSchema` + `FieldMetadataParser`.
- `JsonToPydantic` é usado no agente para `input_data` e `config_data`.

### 3. Todas as formas de `document_schema` aceitas na prática

#### 3.1 Campo declarativo simples

```json
{
    "summary": {
        "type": "str",
        "description": "Resumo do conteúdo do arquivo"
    }
}
```

#### 3.2 Campo declarativo com `required`, `default`, `example`

```json
{
    "title": {
        "type": "str",
        "required": true,
        "description": "Título principal",
        "example": "Relatório de Q2"
    },
    "confidence": {
        "type": "float",
        "required": false,
        "default": 0.0,
        "description": "Confianca da extração"
    }
}
```

#### 3.3 Campo declarativo com validação de tamanho

```json
{
    "abstract": {
        "type": "str",
        "description": "Resumo detalhado",
        "min_length": 20,
        "max_length": 500
    }
}
```

#### 3.4 Lista declarativa de primitivos

```json
{
    "keywords": {
        "type": "list",
        "items": {
            "type": "str"
        },
        "description": "Palavras-chave"
    }
}
```

#### 3.5 Lista declarativa de objetos

```json
{
    "entities": {
        "type": "list",
        "items": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "str",
                    "description": "Nome"
                },
                "category": {
                    "type": "str",
                    "description": "Categoria"
                },
                "score": {
                    "type": "float",
                    "description": "Pontuação"
                }
            }
        }
    }
}
```

#### 3.6 Inferência automática por exemplo (sem `type`)

```json
{
    "summary": "texto exemplo",
    "score": 0.98,
    "approved": true
}
```

#### 3.7 Inferência de objeto aninhado

```json
{
    "invoice": {
        "number": "INV-001",
        "total": 199.9,
        "paid": false
    }
}
```

#### 3.8 Inferência de lista de objetos

```json
{
    "items": [
        {
            "sku": "A-1",
            "quantity": 2,
            "unit_price": 49.9
        }
    ]
}
```

#### 3.9 Inferência com lista vazia

```json
{
    "items": []
}
```

Nesse caso, o tipo vira lista genérica.

#### 3.10 Schema híbrido (declarativo + inferência no mesmo payload)

```json
{
    "summary": {
        "type": "str",
        "description": "Resumo final"
    },
    "stats": {
        "pages": 12,
        "language": "pt-BR"
    }
}
```

### 4. Mapeamento de tipos no modo declarativo

Valores reconhecidos em `type`:

- `str`
- `int`
- `float`
- `bool`
- `list`
- `dict`

Se o tipo não for reconhecido, cai em `Any`.

### 5. Regras e limitações importantes

1. Se o campo é `dict` e possui chave `type`, ele é tratado como metadado declarativo.
2. Para `type = "list"`, `items` é obrigatório.
3. Lista de objetos declarativa exige `items.type = "object"` com `properties`.
4. Campos sem `required` são opcionais por padrão.
5. O parser aceita estrutura híbrida, misturando campos declarativos e inferidos.

