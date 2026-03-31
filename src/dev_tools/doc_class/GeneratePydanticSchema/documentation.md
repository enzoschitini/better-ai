# Classe `GeneratePydanticSchema`

## Visão Geral

A classe `GeneratePydanticSchema` tem como propósito gerar esquemas Pydantic dinamicamente a partir de dados em formato de dicionário Python. Ela transforma estruturas de dados comuns em modelos `BaseModel` do Pydantic, inferindo tipos e descrições automaticamente, o que facilita a validação e documentação de APIs e dados.

Esse recurso é especialmente útil quando se trabalha com dados dinâmicos ou quando o esquema da informação não é conhecido antecipadamente, permitindo construir modelos robustos e tipados de forma programática e rápida, sem a necessidade de escrever manualmente várias classes.

Na prática, essa classe pode ser usada para converter payloads JSON (transformados em dicionários) em modelos Pydantic, que podem validar, documentar e utilizar esses dados de forma segura em aplicações Python.

## Fluxo de Execução

1. **Instanciação**: Crie um objeto `GeneratePydanticSchema`, opcionalmente passando um objeto `FieldMetadataParser` para ajudar na extração de metadados dos campos.
2. **Conversão de dados**: Chame o método `convert` passando um dicionário e um nome raiz para o modelo (`root_name`).
3. **Parsing Recursivo**: O método `_parse_object` itera sobre os campos do dicionário, chamando `_parse_field` para inferir tipos e metadados, construindo modelos aninhados para objetos e listas.
4. **Geração de modelos**: Modelos `BaseModel` do Pydantic são criados dinamicamente usando `create_model`, com nomes únicos gerados para modelos aninhados.
5. **Retorno do modelo principal**: O modelo Pydantic correspondente ao `root_name` é retornado para uso imediato.
6. **Consulta dos modelos gerados**: Através de `get_models`, é possível recuperar todos os modelos intermediários criados.

## Tabela de Métodos da Classe

| Método      | Descrição                                  |
|-------------|-------------------------------------------|
| `__init__`  | Inicializa o gerador, configurando parser de metadados. |
| `convert`   | Converte um dicionário num modelo Pydantic raiz. |
| `get_models`| Retorna todos os modelos criados até o momento. |
| `_generate_name` | Gera nomes únicos para modelos aninhados. |
| `_create_model`  | Cria e armazena um modelo Pydantic dinamicamente. |
| `_resolve_type`  | Inferência básica de tipos Python para Pydantic. |
| `_parse_object`  | Processa dicionário em campos de modelo. |
| `_parse_field`   | Analisa um campo para determinar tipo e metadados. |

## Pontos Importantes da Arquitetura e Insights

- **Geração dinâmica de classes**: A geração em tempo de execução de classes `BaseModel` via `create_model` permite lidar com dados dinâmicos e modelos aninhados sem definição estática.
- **Recursão e singularização**: Utiliza recursão para navegar em estruturas aninhadas e a biblioteca `inflect` para converter nomes de listas ao singular na criação de modelos filhos.
- **Extensibilidade com parser de metadados**: Permite a injeção de uma classe externa para melhorar a extração de metadados, conferindo flexibilidade para diferentes contextos.
- **Tratamento de erros robusto**: Envelopa erros com mensagens descritivas para facilitar debugging.
- **Integração com Pydantic**: Facilita o uso do Pydantic, um padrão para validação e serialização no ecossistema Python moderno.

# Descrição da Classe e Métodos

## Classe `GeneratePydanticSchema`

### Descrição

Classe responsavél por converter dicionários em modelos Pydantic dinâmicos, inferindo automaticamente os tipos de dados e criando modelos aninhados conforme necessário. Ela auxilia na criação de validações, documentação e manipulação segura de dados complexos, especialmente úteis para APIs ou sistemas que processam entradas JSON variáveis.

### Argumentos do Construtor

| Argumento       | Tipo                  | Descrição                                       | Valor Padrão |
|-----------------|-----------------------|------------------------------------------------|--------------|
| `metadata_parser`| `FieldMetadataParser`  | Parser para extrair metadados personalizados dos campos | `None`       |

---

### 1. `__init__`

### Descrição

Inicializa o objeto com um parser para metadados dos campos. Caso não seja fornecido, utiliza um parser padrão padrão (`FieldMetadataParser`).

### Argumentos

- `metadata_parser` (FieldMetadataParser): Parser opcional para metadados dos campos.

### Retornos

- Não retorna valor.

### Raises

- Nenhum.

### Exemplos

```python
generator = GeneratePydanticSchema()  # usa parser padrão
```

---

### 2. `convert`

### Descrição

Converte um dicionário Python em um modelo Pydantic do tipo `BaseModel` nomeado conforme `root_name`. Realiza parsing e criação recursiva dos campos e modelos aninhados.

### Argumentos

- `data` (Dict[str, Any]): Dicionário contendo os dados a serem convertidos.
- `root_name` (str): Nome base para o modelo principal gerado. Default: `"RootModel"`.

### Retornos

- `Type[BaseModel]`: Modelo Pydantic criado para o conjunto de dados fornecido.

### Raises

- `RuntimeError`: Se ocorrer erro durante a conversão, encapsula a exceção original.

### Exemplos

```python
data = {"name": "João", "age": 30}
model = generator.convert(data, root_name="User")
print(model.schema_json(indent=2))
```

---

### 3. `get_models`

### Descrição

Retorna todos os modelos Pydantic já gerados, incluindo modelos aninhados.

### Argumentos

- Nenhum.

### Retornos

- `Dict[str, Type[BaseModel]]`: Dicionário que mapeia nomes de modelos para suas classes `BaseModel`.

### Raises

- Nenhum.

### Exemplos

```python
models = generator.get_models()
for name, model_cls in models.items():
    print(name, model_cls)
```

---

### 4. `_generate_name`

### Descrição

Gera um nome único para models aninhados, incrementando um contador para evitar colisões.

### Argumentos

- `base` (str): Nome base para a construção do nome.

### Retornos

- `str`: Nome único gerado.

### Raises

- Nenhum.

### Exemplos

```python
name1 = generator._generate_name("item")  # e.g., "Item1"
name2 = generator._generate_name("item")  # e.g., "Item2"
```

---

### 5. `_create_model`

### Descrição

Utiliza a função `create_model` do Pydantic para criar um modelo dinâmico com os campos especificados e registra o modelo no dicionário interno.

### Argumentos

- `name` (str): Nome do modelo.
- `fields` (Dict[str, Tuple[Any, Any]]): Campos do modelo onde chave é nome do campo e valor é tupla `(tipo, metadados)`.

### Retornos

- `Type[BaseModel]`: Modelo Pydantic criado.

### Raises

- Nenhum.

### Exemplos

```python
fields = {"name": (str, ...), "age": (int, ...)}
model = generator._create_model("Person", fields)
```

---

### 6. `_resolve_type`

### Descrição

Função para transformar (inferir) o tipo Python básico a partir do valor fornecido, retornando o tipo correspondente para uso no Pydantic. Para objetos complexos retorna `dict` ou `list`, e para tipos desconhecidos retorna `Any`.

### Argumentos

- `value` (Any): Valor a ser avaliado.

### Retornos

- `type`: Tipo inferido (ex: `str`, `int`, `bool`, `list`, `dict`, `Any`).

### Raises

- Nenhum.

### Exemplos

```python
print(generator._resolve_type(10))      # <class 'int'>
print(generator._resolve_type([1, 2]))  # <class 'list'>
print(generator._resolve_type(None))    # typing.Any
```

---

### 7. `_parse_object`

### Descrição

Processa um dicionário para analisar cada campo e gerar um modelo Pydantic com os campos validados apropriadamente.

### Argumentos

- `obj` (Dict[str, Any]): Dicionário a ser convertido.
- `name` (str): Nome do modelo Pydantic a ser criado.

### Retornos

- `Type[BaseModel]`: Modelo criado para o objeto.

### Raises

- Nenhum.

### Exemplos

```python
data = {"field1": "value", "field2": 5}
model = generator._parse_object(data, "MyModel")
```

---

### 8. `_parse_field`

### Descrição

Analisa o campo individualmente para definir o tipo do dado para o Pydantic, criando modelos filhos para objetos (dicts) e listas que contenham dicionários, aplicando também os metadados extraídos via parser.

### Argumentos

- `key` (str): Nome do campo.
- `value` (Any): Valor usado para inferir tipo e metadados.

### Retornos

- `Tuple[Any, Any]`: Tupla cuja primeira posição é o tipo (ex: `int`, `List[NestedModel]`) e a segunda são metadados para o campo.

### Raises

- `RuntimeError`: Dispara se algum erro ocorrer durante o parsing do campo.

### Exemplos

```python
typ, meta = generator._parse_field("age", 42)
print(typ)      # <class 'int'>
print(meta)     # FieldInfo(description='Auto-generated field for age')

typ, meta = generator._parse_field("addresses", [{"street": "Avenida"}])
print(typ)      # typing.List[NestedModel1] (modelo gerado dinamicamente)
```

---

Essa documentação abrange o funcionamento detalhado da classe `GeneratePydanticSchema`, facilitando o uso e extensão por desenvolvedores para transformar dados dinâmicos em modelos Pydantic consistentes e validados.