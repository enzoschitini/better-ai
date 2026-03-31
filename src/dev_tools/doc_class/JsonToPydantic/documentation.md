# Classe `JsonToPydantic`

## Visão Geral

A classe `JsonToPydantic` tem como objetivo facilitar a criação dinâmica de modelos Pydantic a partir de dicionários JSON comuns. Isso é especialmente útil quando não se tem um esquema pré-definido dos dados, mas deseja-se validar e manipular esses dados usando a robustez dos modelos Pydantic. A classe infere automaticamente os tipos dos campos presentes no JSON e gera um modelo correspondente.

Com `JsonToPydantic`, você pode validar rapidamente estruturas JSON arbitrárias, garantindo que os dados estejam corretos conforme os tipos inferidos, além de obter a segurança tipada durante o desenvolvimento. É ideal para aplicações que recebem dados dinâmicos e precisam manipulá-los de forma estruturada.

## Fluxo de Execução

1. **Inicialização:** Instancie a classe, opcionalmente definindo o nome do modelo dinâmico que será criado.

2. **Parse dos Dados:** Use o método `parse`, passando um dicionário JSON. 

3. **Inferência de Tipos:** Internamente, o método `_infer_type` é chamado para cada valor do dicionário, definindo seu tipo Python correspondente.

4. **Construção do Modelo:** A partir dessas inferências, `build_model` cria um modelo Pydantic dinâmico usando `create_model`.

5. **Instanciação e Validação:** O modelo é instanciado com os dados reais, realizando assim a validação e estruturando os dados conforme o modelo gerado.

6. **Resultado:** O método `parse` retorna a instância validada do modelo, pronta para uso.

## Tabela de Métodos da Classe

| Método     | Descrição                                    |
|------------|----------------------------------------------|
| `__init__` | Inicializa a classe com o nome do modelo.    |
| `_infer_type` | Infere o tipo Python de um valor fornecido. |
| `build_model` | Cria um modelo Pydantic dinâmico a partir de um dicionário. |
| `parse`     | Cria e instancia um modelo Pydantic com os dados, realizando validação. |

## Variáveis de Ambiente

Não há variáveis de ambiente necessárias para o funcionamento desta classe.

## Pontos Importantes da Arquitetura e Insights

- A classe utiliza o pacote `pydantic` para a criação dinâmica de modelos por meio da função `create_model`, que permite montar esquemas sob demanda.
- A inferência de tipos é simplificada, cobrindo os tipos básicos do Python — para casos mais complexos, como listas com tipos específicos ou dicionários aninhados, a inferência precisaria ser aprimorada.
- A classe isola a responsabilidade de inferir tipos e construir o modelo, respeitando o princípio de separação de responsabilidades.
- Em caso de erro em qualquer etapa, exceções genéricas são convertidas para `RuntimeError` com mensagens detalhadas, facilitando o tratamento externo.
- A utilização do `inflect` no código não está efetivamente aplicada na classe, indicando potencial para futuras funcionalidades, como pluralização ou manipulação de nomes.

# Descrição da Classe e Métodos

## Classe `JsonToPydantic`

### Descrição

Classe para converter um dicionário JSON em um modelo Pydantic dinâmico, inferindo automaticamente os tipos de cada campo. Permite validação e estruturação dos dados com base em um esquema gerado em tempo de execução.

### Argumentos do Construtor

| Argumento   | Tipo  | Descrição                                  | Valor Padrão   |
|-------------|-------|--------------------------------------------|----------------|
| `model_name`| str   | Nome do modelo Pydantic que será criado dinamicamente. | `"DynamicModel"`|

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa a instância da classe definindo o nome que o modelo Pydantic gerado terá.

### Argumentos

- `model_name` (str): Nome do modelo Pydantic dinamicamente criado. Default é `"DynamicModel"`.

### Retornos

- Não retorna valor.

### Raises

- Nenhum.

### Exemplos

```python
converter = JsonToPydantic(model_name="UsuarioModel")
```

---

### 2. `_infer_type`

### Descrição

Método interno que determina o tipo Python apropriado para um valor fornecido. Este método é fundamental para definir corretamente os tipos dos campos do modelo dinâmico.

### Argumentos

- `value` (Any): Valor do qual se deseja inferir o tipo.

### Retornos

- `Type`: Tipo Python inferido para o valor (exemplo: `str`, `int`, `float`, `bool`, `list`, `dict`, ou `Any`).

### Raises

- `RuntimeError`: Caso ocorra algum erro na inferência do tipo.

### Exemplos

```python
inf_type = converter._infer_type(10)      # retorna <class 'int'>
inf_type = converter._infer_type("texto") # retorna <class 'str'>
```

---

### 3. `build_model`

### Descrição

Cria um modelo Pydantic dinamicamente, baseando-se nos dados do dicionário e nos tipos inferidos de seus valores.

### Argumentos

- `data` (Dict[str, Any]): Dicionário contendo os dados que determinarão os campos do modelo.

### Retornos

- `Type[BaseModel]`: Classe do modelo Pydantic criada dinamicamente com os campos e tipos inferidos.

### Raises

- `RuntimeError`: Caso ocorram erros durante a construção do modelo.

### Exemplos

```python
data = {"nome": "João", "idade": 30, "ativo": True}
modelo = converter.build_model(data)
# `modelo` é uma subclasse de BaseModel com campos nome:str, idade:int, ativo:bool
```

---

### 4. `parse`

### Descrição

Gera o modelo Pydantic dinâmico e o instancia com os dados fornecidos, realizando validação e organização estruturada dos mesmos.

### Argumentos

- `data` (Dict[str, Any]): Dicionário de dados para popular o modelo.

### Retornos

- `BaseModel`: Instância do modelo Pydantic com os dados validados.

### Raises

- `RuntimeError`: Caso ocorra um erro durante a criação ou validação do modelo.

### Exemplos

```python
data = {"usuario": "alice", "pontos": 1500}
instance = converter.parse(data)
print(instance.usuario)  # saída: alice
print(instance.pontos)   # saída: 1500
```