# Classe `GeneratePydanticSchema`

## Visão Geral

A classe `GeneratePydanticSchema` foi desenvolvida para facilitar a criação dinâmica de modelos Pydantic a partir de dicionários Python aninhados. Em cenários onde dados complexos e estruturados são recebidos, como em APIs ou sistemas que lidam com diversas estruturas JSON, essa classe automatiza a geração de schemas Pydantic, usados para validação, conversão e documentação dessas estruturas.

O problema que a classe resolve é a necessidade manual e repetitiva de criar modelos Pydantic para cada estrutura de dado complexa, que muitas vezes varia em profundidade e formato. Ao utilizar esta classe, o desenvolvedor passa um dicionário de dados e recebe um modelo Pydantic que reflete exatamente a estrutura e tipos desses dados, incluindo schemas aninhados para objetos internos e listas.

Na prática, pode ser usada para validar dados de entrada, gerar exemplos para documentação automática ou construir interfaces adaptativas em sistemas que consomem dados dinâmicos.

## Fluxo de Execução

1. O usuário instancia a classe `GeneratePydanticSchema`, podendo opcionalmente informar um objeto `FieldMetadataParser` para customizar a extração de metadados dos campos.
2. O método `convert()` é chamado com um dicionário Python representando os dados a serem modelados e um nome raiz para o modelo (padrão "RootModel").
3. A classe analisa recursivamente cada chave e valor do dicionário:
   - Para campos escalares, determina o tipo básico.
   - Para dicionários aninhados, gera um novo modelo Pydantic com um nome automático único.
   - Para listas, analisa o tipo do primeiro elemento para definir o tipo dos itens na lista, gerando modelos para objetos se necessário.
4. Campos recebem metadados (descrição) gerados automaticamente ou pela análise do `metadata_parser`.
5. Todos os modelos gerados são armazenados internamente, podendo ser recuperados pelo método `get_models()`.
6. Em caso de erro durante a conversão, uma exceção `RuntimeError` é lançada com detalhes do erro.

## Tabela de Métodos da Classe

| Método    | Descrição                                                   |
|-----------|-------------------------------------------------------------|
| `__init__`| Inicializa a classe com um parser de metadados opcional.    |
| `convert` | Converte um dicionário em um modelo Pydantic raiz.           |
| `get_models` | Retorna todos os modelos Pydantic gerados até o momento.  |
| `_generate_name`| Gera nomes únicos para modelos aninhados.               |
| `_create_model` | Cria um modelo Pydantic a partir de campos definidos.   |
| `_resolve_type` | Deduz o tipo base do valor recebido.                     |
| `_parse_object` | Constrói recursivamente modelos Pydantic para objetos. |
| `_parse_field`  | Analisa o tipo e metadados de um campo individual.      |

## Pontos Importantes da Arquitetura e Insights

- A geração dinâmica aproveita o método `create_model` do Pydantic para criar classes em tempo de execução, facilitando a criação de modelos não conhecidos em tempo de codificação.
- O uso recursivo permite a criação de modelos aninhados que refletem a estrutura complexa dos dados de entrada.
- A contagem incremental garante nomes únicos para os modelos auxiliares, evitando colisões.
- A classe depende do `FieldMetadataParser` para enriquecer os campos com metadados, criando uma separação que favorece a personalização e extensibilidade da análise de campos.
- O tratamento específico para listas, com a tentativa de singularizar nomes (presumivelmente usando `inflector.singular_noun`), mostra atenção na nomenclatura dos modelos.
- Manejo cuidadoso das exceções durante parsing e conversão, registrando mensagem de erro e mantendo usabilidade ao expor erros claros ao usuário.
- Internamente, o armazenamento dos modelos em um dicionário permite consulta e reutilização posterior.

# Descrição da Classe e Métodos

## Classe `GeneratePydanticSchema`

### Descrição

Esta classe tem o papel de converter dicionários complexos e aninhados em modelos Pydantic programaticamente. Ela automatiza a geração de schemas de validação que refletem fielmente a estrutura dos dados de entrada, com suporte para campos aninhados, listas e a integração com um parser de metadados para aumentar a descrição dos campos.

Seu uso é indicado para cenários de validação dinâmica e construção de APIs ou sistemas que recebem dados JSON diversos e precisam de validação forte e explícita.

### Argumentos do Construtor

| Argumento        | Tipo                 | Descrição                                                   | Valor Padrão         |
|------------------|----------------------|-------------------------------------------------------------|---------------------|
| `metadata_parser` | `FieldMetadataParser` | Objeto para análise e extração de metadados de campos.      | Nova instância de `FieldMetadataParser` |

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa a instância da classe, definindo o parser de metadados e preparando o armazenamento interno para os modelos gerados.

### Argumentos

- `metadata_parser` (`FieldMetadataParser`): Parser opcional para extração de metadados.

### Retornos

- Não retorna valor.

### Raises

- Nenhum.

### Exemplos

```python
schema_generator = GeneratePydanticSchema()
```

---

### 2. `convert`

### Descrição

Recebe um dicionário Python e converte-o em um modelo Pydantic raiz, gerando automaticamente todos os modelos aninhados necessários para a validação completa da estrutura.

### Argumentos

- `data` (`Dict[str, Any]`): Dicionário de dados a ser convertido em modelo.
- `root_name` (`str`): Nome do modelo raiz a ser criado. Padrão é "RootModel".

### Retornos

- `Type[BaseModel]`: Modelo Pydantic gerado para o dicionário informado.

### Raises

- `RuntimeError`: Caso ocorra erro durante a conversão dos dados.

### Exemplos

```python
data = {
    "nome": "João",
    "idade": 30,
    "endereco": {
        "rua": "Av. Brasil",
        "numero": 100
    }
}

model = schema_generator.convert(data, root_name="Pessoa")
# model agora é uma classe Pydantic com campos nome, idade e endereco (que é outro modelo)
```

---

### 3. `get_models`

### Descrição

Retorna todos os modelos Pydantic criados até o momento, incluindo modelos aninhados gerados durante a conversão dos dados.

### Argumentos

Nenhum.

### Retornos

- `Dict[str, Type[BaseModel]]`: Dicionário com nomes dos modelos como chave e classes Pydantic como valor.

### Raises

Nenhum.

### Exemplos

```python
all_models = schema_generator.get_models()
# Pode acessar, por exemplo, all_models["Pessoa1"] para um modelo aninhado
```

---

### 4. `_generate_name`

### Descrição

Gera um nome único para modelos Pydantic aninhados, combinando uma base de nome com um contador incremental.

### Argumentos

- `base` (`str`): Nome base para o modelo.

### Retornos

- `str`: Nome gerado único, ex: "Endereco1".

### Raises

Nenhum.

### Exemplos

```python
nome = schema_generator._generate_name("endereco")
# "Endereco1"
```

---

### 5. `_create_model`

### Descrição

Cria um modelo Pydantic dinamicamente a partir de um nome e campos especificados, armazenando-o no dicionário interno.

### Argumentos

- `name` (`str`): Nome do modelo.
- `fields` (`Dict[str, Tuple[Any, Any]]`): Mapeamento de campos para tuplas (tipo, metadados).

### Retornos

- `Type[BaseModel]`: Modelo Pydantic criado.

### Raises

Nenhum.

### Exemplos

```python
fields = {
    "nome": (str, ...),
    "idade": (int, ...)
}

model = schema_generator._create_model("Pessoa", fields)
```

---

### 6. `_resolve_type`

### Descrição

Determina o tipo Pydantic básico de um valor Python simples.

### Argumentos

- `value` (`Any`): Valor cujo tipo deve ser deduzido.

### Retornos

- `Any`: Tipo Python correspondente (`str`, `bool`, `int`, `float`, `list`, `dict` ou `Any` como fallback).

### Raises

Nenhum.

### Exemplos

```python
t = schema_generator._resolve_type(10)   # int
t2 = schema_generator._resolve_type("hi") # str
```

---

### 7. `_parse_object`

### Descrição

Analisa um dicionário e cria um modelo Pydantic para ele, processando recursivamente todos os campos do objeto.

### Argumentos

- `obj` (`Dict[str, Any]`): Dicionário a ser parseado.
- `name` (`str`): Nome do modelo a ser criado.

### Retornos

- `Type[BaseModel]`: Modelo Pydantic criado para o objeto analisado.

### Raises

Nenhum.

### Exemplos

```python
model = schema_generator._parse_object({"a": 1, "b": "x"}, "SimpleModel")
```

---

### 8. `_parse_field`

### Descrição

Determina o tipo e metadados para um campo individual, tratando casos de dicionários, listas, valores escalares e aplicando análise personalizada via `metadata_parser`.

### Argumentos

- `key` (`str`): Nome do campo.
- `value` (`Any`): Valor do campo para dedução do tipo.

### Retornos

- `Tuple[Any, Any]`: Tupla com tipo do campo e instância `Field` contendo metadados para Pydantic.

### Raises

- `RuntimeError`: Se houver erro durante o parsing, encapsula o erro original.

### Exemplos

```python
field_type, field_info = schema_generator._parse_field("idade", 25)
# field_type: int
# field_info: Field(description="Auto-generated field for idade")
```

---

Essa documentação oferece um guia detalhado para programadores compreenderem e utilizarem a classe `GeneratePydanticSchema` de forma prática e eficiente, garantindo a geração rápida e correta de modelos Pydantic para validação e manipulação de dados complexos.