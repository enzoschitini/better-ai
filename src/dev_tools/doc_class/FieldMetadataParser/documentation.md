# Classe `FieldMetadataParser`

## Visão Geral

A classe `FieldMetadataParser` foi criada para facilitar a interpretação de metadados de campos utilizados em modelos Pydantic. Seu principal propósito é analisar estruturas de dados que descrevem tipos, valores padrão, descrições e exemplos para campos, convertendo-os em componentes compatíveis com Pydantic, como tipos Python e especificações de campos.

Esta funcionalidade é muito útil para desenvolvedores que trabalham com definição dinâmica de modelos, onde os campos podem ser configurados a partir de dicionários ou informações externas, sem a necessidade de escrever manualmente cada campo em código estático. Com isso, a classe auxilia na construção automática de modelos robustos e documentados.

Por exemplo, em um sistema que consome especificações JSON para gerar modelos validados, essa classe pode interpretar a definição dos campos e fornecer as configurações necessárias para o Pydantic validar e documentar esses campos corretamente.

---

## Fluxo de Execução

1. **Inicialização:** Cria-se uma instância da classe `FieldMetadataParser` (não possui construtor especial, usa o padrão).

2. **Chamada de `parse`:** Recebe um valor que pode ser um dicionário representando metadados do campo.

3. **Verificação do valor:** O método `parse` verifica se o valor é um dicionário contendo a chave `"type"`. 

4. **Parsing de metadados:** Se for um dicionário válido, a função interna `_parse_metadata` é chamada para interpretar os dados.

5. **Mapeamento do tipo:** `_parse_metadata` chama `_map_type` para converter o nome do tipo string (ex: `"int"`) para o tipo Python correspondente (`int`).

6. **Criação do campo Pydantic:** É criado um objeto `Field` contendo as informações do campo, como valor padrão, descrição e exemplos, conforme disponível nos metadados.

7. **Resultado:** A tupla `(field_type, field_info)` é retornada, contendo o tipo Python e os metadados do campo para serem usados em criação dinâmica de modelos.

8. **Tratamento de erros:** Caso ocorra qualquer exceção durante o parsing, a exceção é capturada e relançada como `RuntimeError`, com uma mensagem padronizada e a descrição do erro.

---

## Tabela de Métodos da Classe

| Método  | Descrição                                               |
|---------|---------------------------------------------------------|
| `__init__` | Inicializador padrão da classe (implícito).          |
| `parse` | Analisa um valor para identificar metadados do campo e retorna tipo e infos. |
| `_parse_metadata` | Processa dicionário de metadados para criar tipo e campo Pydantic. |
| `_map_type` | Converte string de tipo para tipo Python correspondente. |

---

## Variáveis de Ambiente

Não há variáveis de ambiente utilizadas por esta classe.

---

## Pontos Importantes da Arquitetura e Insights

- **Encapsulamento:** A classe é bem encapsulada com métodos privados (_parse_metadata e _map_type) para tratar responsabilidades específicas, deixando o método `parse` limpo e claro.

- **Uso de Pydantic:** A integração com o Pydantic é feita criando dinamicamente objetos `Field` que transportam metainformação importante para validação e documentação.

- **Tratamento explícito de erros:** Captura e relança exceções promove clareza ao debug e evita erros silenciosos.

- **Extensibilidade:** O método `_map_type` pode ser facilmente estendido para suportar mais tipos ou até tipos personalizados.

- **Separação de responsabilidades:** A classe se dedica somente a interpretar metadados, evitando acoplamento com outras partes da aplicação, facilitando testes e manutenção.

---

# Descrição da Classe e Métodos

## Classe `FieldMetadataParser`

### Descrição

Classe responsável por analisar e interpretar metadados de campos para modelos Pydantic. Interpreta dicionários de configuração que descrevem o tipo do campo, valor padrão, descrições e exemplos, retornando tipos e configurações compatíveis para criação dinâmica de campos em modelos.

### Argumentos do Construtor

Nenhum argumento no construtor.

---

### 1. `parse`

### Descrição

Analisa um valor genérico e tenta extrair metadados de campo para Pydantic, retornando uma tupla com o tipo do campo e um objeto `Field` configurado. Retorna `None` se o valor não corresponder a uma estrutura de metadados.

### Argumentos

- `value` (Any): Valor que pode conter metadados para análise.

### Retornos

- `Tuple[Any, Any] | None`: Tupla com o tipo Python e objeto `Field` se o valor contiver metadados válidos; caso contrário, `None`.

### Raises

- `RuntimeError`: Lança em caso de falha ao analisar os metadados, com mensagem do erro original.

### Exemplos

```python
parser = FieldMetadataParser()

# Com dicionário válido
metadata = {
    "type": "int",
    "default": 10,
    "description": "Quantidade de itens",
    "example": 5
}

field_type, field_info = parser.parse(metadata)
# field_type será int
# field_info conterá informações do Field com default=10, descrição e exemplo [5]

# Com valor inválido
result = parser.parse("qualquer coisa")
# result será None
```

---

### 2. `_parse_metadata`

### Descrição

Método interno que converte dicionário de metadados em uma tupla com o tipo Python correspondente e um objeto `Field` configurado com as informações adicionais.

### Argumentos

- `value` (Dict[str, Any]): Dicionário com metadados do campo (tipo, default, descrição, exemplo).

### Retornos

- `Tuple[Any, Any]`: Tupla com tipo Python e campo Pydantic (`Field`).

### Raises

Nenhum diretamente (capturado no método `parse`).

### Exemplos

```python
props = {"type": "str", "default": "sem valor", "description": "Nome do usuário", "example": "Alice"}
tipo, campo = parser._parse_metadata(props)
# tipo: str
# campo: Field com detalhes correspondentes
```

---

### 3. `_map_type`

### Descrição

Converte o nome do tipo, recebido como string, para o tipo Python correspondente (ex: `"int"` para `int`). Caso o tipo não seja reconhecido, retorna o tipo genérico `Any`.

### Argumentos

- `type_name` (str): Nome do tipo em formato string.

### Retornos

- `type`: Tipo Python equivalente ou `Any` se não reconhecido.

### Raises

Nenhum.

### Exemplos

```python
parser._map_type("int")  # Retorna <class 'int'>
parser._map_type("float")  # Retorna <class 'float'>
parser._map_type("inexistente")  # Retorna typing.Any
```

---

Esta documentação fornece uma visão clara e prática da classe `FieldMetadataParser`, facilitando seu uso e compreensão por desenvolvedores que buscam gerar modelos dinâmicos e seguros com Pydantic.