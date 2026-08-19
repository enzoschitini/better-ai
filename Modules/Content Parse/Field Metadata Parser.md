# Classe `FieldMetadataParser`

## Visão Geral

A classe `FieldMetadataParser` é responsável por interpretar metadados definidos em dicionários para campos de dados e convertê-los em tipos e campos compatíveis com a biblioteca Pydantic. Ela analisa informações como tipo do campo, obrigatoriedade, descrição, exemplos e restrições, gerando assim uma representação pronta para validação e uso em modelos Pydantic.

Esse processo é fundamental para sistemas que recebem esquemas de dados dinâmicos ou configurações externas e precisam construir modelos de validação de forma automatizada e consistente. Com essa classe, é possível transformar uma especificação JSON-like diretamente em tipos Pydantic, garantindo validação automática e documentação gerada a partir dos metadados.

Na prática, pode ser utilizada em frameworks de dados, importações dinâmicas de esquemas, ou qualquer aplicação que modele dados a partir de definições flexíveis.

## Fluxo de Execução

1. O método `parse` recebe um valor arbitrário que pode ser um metadado de campo ou não.
2. Verifica se o valor é um dicionário contendo a chave `"type"`, identificando-o como metadado válido para análise.
3. Caso seja metadado, delega para o método privado `_parse_metadata` que faz a transformacão detalhada.
4. `_parse_metadata` extrai o tipo informado e verifica se o campo é obrigatório (`required`).
5. Se o tipo for `"list"`, busca a definição do tipo dos itens (`items`), podendo gerar um tipo genérico ou um modelo aninhado para objetos complexos.
6. Mapeia o tipo string para o tipo Python correspondente, utilizando o método `_map_type`.
7. Se o campo não for obrigatório, o tipo é encapsulado em `Optional` para suportar ausência de valor.
8. Cria um `Field` do Pydantic com parâmetros como valor padrão, descrição, exemplos e restrições de tamanho.
9. Retorna uma tupla formada pelo tipo final e o objeto `Field` para uso diretamente em modelos Pydantic.
10. Caso o valor não seja um metadado reconhecido, retorna `None`.
11. Se houver erro no parsing, lança uma exceção do tipo `RuntimeError` com detalhes.

## Tabela de Métodos da Classe

| Método  | Descrição                                    |
|---------|----------------------------------------------|
| `__init__` | Não implementado explicitamente (construtor padrão) |
| `parse` | Analisa o valor e retorna tipo e Field para metadados ou None |
| `_parse_metadata` | Converte dicionário de metadados em tipo Pydantic e Field configurado |
| `_map_type` | Mapeia nome de tipo string para tipo Python correspondente |

## Variáveis de Ambiente

Nenhuma variável de ambiente é necessária para o funcionamento desta classe.

## Pontos Importantes da Arquitetura e Insights

- A classe utiliza encapsulamento, restringindo funções auxiliares ao escopo privado (`_parse_metadata` e `_map_type`).
- Utiliza criação dinâmica de modelos Pydantic (`create_model`) para representar tipos complexos aninhados (objetos dentro de listas), permitindo flexibilidade e extensibilidade.
- O parser interpreta uma estrutura JSON-like para produzir tipos anotados e informações completas para validação — facilitando integração com dados dinâmicos.
- Suporta atributos opcionais, valores padrões, descrições e exemplos, promovendo documentação automática via Pydantic.
- Tratamento explícito de erros com mensagens claras facilita depuração.
- O método `_map_type` é facilmente extensível para novos tipos, bastando adicionar ao dicionário.

# Descrição da Classe e Métodos

## Classe `FieldMetadataParser`

### Descrição

Classe para analisar metadados fornecidos em dicionários e transformá-los em tipos e campos configurados para uso com Pydantic. Facilita a criação dinâmica de modelos de validação a partir de especificações externas, interpretando tipos, obrigatoriedade e metadados descritivos.

### Argumentos do Construtor

Nenhum parâmetro no construtor.

### Métodos

---

### 1. `parse`

### Descrição

Recebe um valor qualquer e, se este for um dicionário que define metadados de campo (com a chave `"type"`), retorna uma tupla contendo o tipo Pydantic resultante e um objeto `Field` configurado com as propriedades. Caso contrário, retorna `None`.

### Argumentos

- `value` (Any): Valor para ser analisado como metadado de campo.

### Retornos

- `Tuple[Any, Any] | None`: Tupla com o tipo do campo e o objeto Field, ou `None` se não for metadado.

### Raises

- `RuntimeError`: Se ocorrer qualquer erro durante a análise dos metadados, é lançada uma exceção com mensagem explicativa.

### Exemplos

```python
# Metadado válido para um campo inteiro obrigatório
result = parser.parse({"type": "int", "required": True, "description": "Idade do usuário"})
# result será algo como (int, Field(..., description="Idade do usuário"))

# Metadado inválido ou não seguindo o padrão retorna None
result = parser.parse("apenas uma string")
# result será None
```

---

### 2. `_parse_metadata`

### Descrição

Método auxiliar privado que recebe um dicionário validado de metadados, extrai seu tipo, configurando o tipo e as propriedades do campo, especialmente tratando listas e objetos aninhados, retornando a tupla com o tipo Pydantic e o objeto `Field`.

### Argumentos

- `value` (Dict[str, Any]): Dicionário contendo as propriedades do campo, como tipo, exigência, exemplos, entre outros.

### Retornos

- `Tuple[Any, Any]`: Tupla com o tipo do campo e as informações de `Field`.

### Raises

- `ValueError`: Caso o tipo seja `"list"` e não contenha a definição obrigatória da chave `"items"`.

### Exemplos

```python
# Parse de um campo do tipo lista de inteiros não obrigatória
type_, field = parser._parse_metadata({
    "type": "list",
    "items": {"type": "int"},
    "required": False,
    "description": "Lista de números"
})
# type_ será Optional[List[int]]
# field conterá description e configurações

# Parse de um campo objeto aninhado dentro da lista
type_, field = parser._parse_metadata({
    "type": "list",
    "items": {
        "type": "object",
        "properties": {
            "nome": {"type": "str", "description": "Nome do item"}
        }
    }
})
# type_ será List[ModeloDinâmico]
# field configurado conforme descrito
```

---

### 3. `_map_type`

### Descrição

Mapeia um nome de tipo representado por uma string para o tipo Python correspondente, utilizado na modelagem Pydantic. Se o tipo não for reconhecido, retorna `Any` como fallback.

### Argumentos

- `type_name` (str): String representando o tipo, por exemplo, `"str"`, `"int"`, `"list"`.

### Retornos

- `tipo`: Tipo Python correspondente (ex: `str`, `int`, `list`) ou `Any` se não reconhecido.

### Exemplos

```python
if __name__ == "__main__":
    parser = FieldMetadataParser()

    test_cases = [
        {
            "input": {
                "type": "str",
                "description": "Nome do personagem",
                "example": "John"
            }
        },
        {
            "input": {
                "type": "int",
                "default": 10
            }
        },
        {
            "input": "valor simples"
        }
    ]

    for i, case in enumerate(test_cases, 1):
        result = parser.parse(case["input"])
        print(f"\nTeste {i}")
        print("Input:", case["input"])
        print("Output:", result)

# python -m src.content_parse.pydantic_shema
```
