# Classe `JsonToPydantic`

## Visão Geral

A classe `JsonToPydantic` tem o propósito de converter um dicionário JSON simples em um modelo Pydantic dinâmico, inferindo automaticamente os tipos das propriedades a partir dos valores fornecidos. Isso facilita a criação rápida de modelos para validação de dados, principalmente quando a estrutura do JSON não é conhecida antecipadamente ou muda com frequência.

Essa classe resolve o problema de criar manualmente modelos Pydantic para dados que são recebidos em formato JSON com tipos variados, automatizando a geração do modelo e validando os dados de entrada. Na prática, é útil para prototipagem rápida ou para sistemas que recebem dados flexíveis e precisam garantir a conformidade dos tipos.

## Fluxo de Execução

1. Instancie a classe `JsonToPydantic`, opcionalmente definindo um nome para o modelo Pydantic a ser criado.
2. Use o método `parse()` passando o dicionário JSON para:
   - Internamente, a classe infere os tipos básicos de cada campo.
   - Um modelo Pydantic dinâmico é construído com esses campos e seus tipos.
   - O objeto do modelo é instanciado com os dados fornecidos e retornado, validando a conformidade.
3. Caso o tipo não seja básico, o tipo `Any` será utilizado como fallback.

## Tabela de Métodos da Classe

| Método        | Descrição                                              |
|---------------|-------------------------------------------------------|
| `__init__`    | Inicializa o conversor definindo o nome do modelo.    |
| `_infer_type` | Infere o tipo básico Python a partir do valor dado.   |
| `build_model` | Cria dinamicamente o modelo Pydantic a partir dos dados. |
| `parse`       | Constrói e instancia o modelo Pydantic com os dados.  |


## Pontos Importantes da Arquitetura e Insights

- A inferência de tipos é simples e cobre apenas tipos básicos do Python e coleções padrão (listas e dicionários).
- A criação do modelo usa o `create_model` do Pydantic, permitindo modelos dinâmicos em tempo de execução.
- Possui tratamento robusto de exceções para facilitar o diagnóstico de erros.
- Pode ser estendido para lidar com tipos mais complexos, válido para protótipos rápidos.

---

# Classe `FieldMetadataParser`

## Visão Geral

Esta classe é responsável por analisar valores de campos que podem conter metadados específicos para a criação de campos Pydantic detalhados, como tipo customizado, descrição, exemplos e valor default. Assim, permite enriquecer a definição do campo além da simples inferência do tipo.

É útil para integrar esquemas que já contenham esses metadados embutidos, facilitando a criação de modelos com documentação e exemplos automáticos, importantes para APIs e validação avançada.

## Fluxo de Execução

1. O método `parse` verifica se o valor é um dicionário com chave `"type"`.
2. Se sim, repassa para `_parse_metadata`.
3. `_parse_metadata` traduz o tipo textual em tipo Python usando um mapeamento.
4. Monta um objeto `Field` do Pydantic com propriedades como default, descrição e exemplos.
5. Retorna uma tupla com o tipo e o `Field` configurado para uso na construção do modelo.

## Tabela de Métodos da Classe

| Método        | Descrição                                                    |
|---------------|--------------------------------------------------------------|
| `parse`       | Verifica e retorna metadados do campo, ou None se não houver |
| `_parse_metadata` | Cria a tupla tipo e Field com base em dados fornecidos    |
| `_map_type`   | Mapeia string de tipo para tipo Python correspondente         |

## Pontos Importantes da Arquitetura e Insights

- Permite incorporar metadados detalhados para campos individualmente.
- Facilita a extensão para outros tipos customizados e validações específicas.
- Retorna `None` quando não detecta metadados, atuando como um parser opcional.
- Reutilizável por outras classes, como `GeneratePydanticSchema`.

---

# Classe `GeneratePydanticSchema`

## Visão Geral

`GeneratePydanticSchema` é uma classe avançada para criar modelos Pydantic complexos com suporte a estruturas de dados aninhadas e uso de metadados detalhados em campos. Ela processa dicionários JSON recursivamente, gerando modelos para objetos internos e listas, gerenciando nomes dinâmicos para modelos gerados.

Ideal para gerar esquemas Pydantic completos de JSONs aninhados, garantindo tipos corretos, documentação e exemplos via uso do `FieldMetadataParser`. Facilita a manutenção e validação de dados complexos de APIs REST ou outras fontes JSON.

## Fluxo de Execução

1. Instancie a classe opcionalmente com um parser de metadados customizado.
2. Use `convert` passando o dicionário e nome raiz para iniciar a conversão.
3. Para cada campo:
   - Tenta extrair metadados via parser.
   - Se for objeto, chama recursivamente para criar modelo aninhado.
   - Se for lista, analisa o primeiro item para identificar tipo ou cria lista de modelos aninhados.
   - Caso contrário, resolve tipo diretamente.
4. Cria modelos dinamicamente usando `create_model` e guarda-os em um dict interno.
5. Pode retornar o modelo raíz e fornece acesso a todos os modelos criados com `get_models()`.

## Tabela de Métodos da Classe

| Método          | Descrição                                                     |
|-----------------|---------------------------------------------------------------|
| `__init__`      | Inicializa com parser de metadados e estado interno.          |
| `convert`       | Converte o dicionário em um modelo Pydantic aninhado.         |
| `get_models`    | Retorna todos os modelos Pydantic criados internamente.       |
| `_generate_name`| Gera nomes únicos e legíveis para modelos aninhados.          |
| `_create_model` | Cria e armazena um modelo Pydantic com campos especificados.  |
| `_resolve_type` | Resolve tipo Python básico para valores simples.              |
| `_parse_object` | Processa dicionário criando campos e modelo para ele.         |
| `_parse_field`  | Analisa e retorna o tipo e Field para um campo individual.    |

## Pontos Importantes da Arquitetura e Insights

- Utiliza recursão para criar modelos aninhados automaticamente.
- Usa o pacote `inflect` para converter nomes plurais em singulares, melhorando a nomenclatura dos modelos aninhados.
- Gera nomes únicos para os modelos complementares para evitar conflitos.
- Suporta arrays heterogêneos e vazios, usando tipagem genérica quando necessário.
- Integra com `FieldMetadataParser` para enriquecer os campos com metadados.
- Armazena todos os modelos criados para fácil acesso e reutilização.
- Robustez no tratamento de exceções para rastreamento de erros durante a geração.

---

# Descrição da Classe e Métodos

## Classe `JsonToPydantic`

### Descrição

Classe para converter um dicionário JSON simples em um modelo Pydantic dinâmico, inferindo tipos básicos automaticamente e facilitando a validação dos dados.

### Argumentos do Construtor

| Argumento   | Tipo  | Descrição                         | Valor Padrão    |
|-------------|-------|----------------------------------|-----------------|
| model_name  | str   | Nome do modelo Pydantic gerado   | `"DynamicModel"` |

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa a classe definindo opcionalmente o nome do modelo Pydantic a ser criado.

### Argumentos

- model_name (str): nome do modelo, padrão "DynamicModel".

### Retornos

- Não retorna valor.

### Raises

- Nenhum.

### Exemplos

```python
converter = JsonToPydantic("MeuModelo")
```

---

### 2. `_infer_type`

### Descrição

Infere o tipo Python básico (str, int, float, bool, list, dict, Any) a partir do valor fornecido.

### Argumentos

- value (Any): valor do qual inferir o tipo.

### Retornos

- tipo: tipo Python inferido.

### Raises

- RuntimeError: em caso de erro na inferência.

### Exemplos

```python
tipo = converter._infer_type(123)  # int
tipo = converter._infer_type([1, 2])  # list
```

---

### 3. `build_model`

### Descrição

Cria dinamicamente o modelo Pydantic com campos inferidos a partir do dicionário fornecido.

### Argumentos

- data (Dict[str, Any]): dados para construir o modelo.

### Retornos

- Type[BaseModel]: classe do modelo Pydantic criada.

### Raises

- RuntimeError: em caso de erro na criação do modelo.

### Exemplos

```python
modelo = converter.build_model({"nome": "João", "idade": 30})
```

---

### 4. `parse`

### Descrição

Instancia e retorna o modelo Pydantic criado com os dados fornecidos, validando-os.

### Argumentos

- data (Dict[str, Any]): dados para serem validados e parseados.

### Retornos

- BaseModel: instância do modelo Pydantic com dados validados.

### Raises

- RuntimeError: em caso de erro durante parse.

### Exemplos

```python
obj = converter.parse({"nome": "Ana", "idade": 25})
print(obj.nome)  # Ana
```

---

## Classe `FieldMetadataParser`

### Descrição

Classe para analisar campos que contenham metadados explícitos (tipo, descrição, exemplo, default) para criação de campos Pydantic detalhados.

### Argumentos do Construtor

Nenhum.

### Métodos

---

### 1. `parse`

### Descrição

Recebe um valor e retorna uma tupla com tipo e `Field` configurado se o valor contiver metadados, ou None caso contrário.

### Argumentos

- value (Any): valor a ser analisado.

### Retornos

- Tuple[Any, Any] | None: tupla (tipo, Field) ou None.

### Raises

- RuntimeError: em caso de erro na análise.

### Exemplos

```python
metadata = parser.parse({"type": "str", "description": "Nome do usuário", "example": "João"})
# retorna (str, Field(...))
```

---

### 2. `_parse_metadata`

### Descrição

Método interno que cria o tipo e o campo Pydantic a partir do dicionário de metadados.

### Argumentos

- value (Dict[str, Any]): metadados do campo.

### Retornos

- Tuple[Any, Any]: tupla de tipo e Field do Pydantic.

### Raises

- Nenhum explicitamente.

### Exemplos

```python
tipo, field = parser._parse_metadata({"type": "int", "description": "Idade"})
```

---

### 3. `_map_type`

### Descrição

Converte o nome do tipo em string para o tipo Python correspondente.

### Argumentos

- type_name (str): nome textual do tipo.

### Retornos

- tipo Python correspondente ou Any se não mapeado.

### Raises

- Nenhum.

### Exemplos

```python
tipo = parser._map_type("bool")  # bool
```

---

## Classe `GeneratePydanticSchema`

### Descrição

Classe para geração avançada de modelos Pydantic complexos a partir de dados aninhados, suportando metadados, listas aninhadas e criação automática de múltiplos modelos.

### Argumentos do Construtor

| Argumento        | Tipo                  | Descrição                                   | Valor Padrão            |
|------------------|-----------------------|---------------------------------------------|------------------------|
| metadata_parser  | FieldMetadataParser     | Parser para metadados nos campos            | `FieldMetadataParser()` |

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa o gerador com um parser de metadados e prepara estrutura interna para armazenar modelos.

### Argumentos

- metadata_parser (FieldMetadataParser, opcional): parser para metadados.

### Retornos

- Não retorna valor.

### Raises

- Nenhum.

### Exemplos

```python
generator = GeneratePydanticSchema()
```

---

### 2. `convert`

### Descrição

Converte um dicionário JSON em um modelo Pydantic completo, gerando modelos aninhados quando necessário.

### Argumentos

- data (Dict[str, Any]): dados JSON para conversão.
- root_name (str): nome do modelo principal.

### Retornos

- Type[BaseModel]: modelo Pydantic raíz gerado.

### Raises

- RuntimeError: em caso de falha na conversão.

### Exemplos

```python
model = generator.convert({"nome": "Ana", "endereco": {"rua": "A", "numero": 10}}, "User")
```

---

### 3. `get_models`

### Descrição

Retorna o dicionário com todos os modelos Pydantic criados durante a conversão.

### Argumentos

- Nenhum.

### Retornos

- Dict[str, Type[BaseModel]]: modelos criados.

### Raises

- Nenhum.

### Exemplos

```python
all_models = generator.get_models()
```

---

### 4. `_generate_name`

### Descrição

Gera um nome para modelo baseado em base textual e numeral sequencial para evitar conflitos.

### Argumentos

- base (str): base do nome.

### Retornos

- str: nome único gerado.

### Raises

- Nenhum.

### Exemplos

```python
name = generator._generate_name("Endereco")  # Exemplo: "Endereco1"
```

---

### 5. `_create_model`

### Descrição

Cria um modelo Pydantic com nome e campos especificados, armazenando-o internamente.

### Argumentos

- name (str): nome do modelo.
- fields (Dict[str, Tuple[Any, Any]]): campos e tipos para o modelo.

### Retornos

- Type[BaseModel]: modelo criado.

### Raises

- Nenhum.

### Exemplos

```python
model = generator._create_model("User", {"nome": (str, ...), "idade": (int, ...)})
```

---

### 6. `_resolve_type`

### Descrição

Resolve tipo Python básico a partir de um valor dado, usado para tipagem automática.

### Argumentos

- value (Any): valor para inferir tipo.

### Retornos

- Tipo Python inferido ou `Any`.

### Raises

- Nenhum.

### Exemplos

```python
t = generator._resolve_type(3.14)  # float
```

---

### 7. `_parse_object`

### Descrição

Análise recursiva de um dicionário JSON, criando campos e um modelo Pydantic para ele.

### Argumentos

- obj (Dict[str, Any]): objeto JSON.
- name (str): nome do modelo a ser criado.

### Retornos

- Type[BaseModel]: modelo criado.

### Raises

- Nenhum explicitamente.

### Exemplos

```python
model = generator._parse_object({"id": 1, "nome": "Ana"}, "Pessoa")
```

---

### 8. `_parse_field`

### Descrição

Analisa um campo individualmente, tentando extrair metadados, criar modelos aninhados ou resolver tipos básicos, retornando tupla para criação do campo.

### Argumentos

- key (str): nome do campo.
- value (Any): valor do campo.

### Retornos

- Tuple[Any, Any]: tipo e objeto Field ou modelo aninhado.

### Raises

- RuntimeError: em caso de falha na análise.

### Exemplos

```python
field = generator._parse_field("idade", 30)
# retorna (int, Field(...))
```

---

# Fim da documentação técnica.