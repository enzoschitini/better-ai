# Classe `WebServiceAPI`

## Visão Geral

A classe `WebServiceAPI` atua como um invólucro configurável para criar e gerenciar uma aplicação FastAPI. Seu propósito é simplificar o processo de inicialização da aplicação web, configurar middlewares essenciais, registrar rotas padrão e integrar automaticamente roteadores adicionais de forma dinâmica a partir de pacotes Python.

Ela resolve o problema de repetição e dispersão de configurações comuns em APIs FastAPI, reunindo em um só lugar toda a configuração inicial, middleware CORS, rotas básicas de saúde e autenticação, além de facilitar a extensão da API com roteadores externos. Na prática, ela pode ser usada para acelerar o desenvolvimento de APIs RESTful, garantindo uma base consistente e permitindo integração modular e testes facilitados.

A classe é especialmente útil em projetos que desejam manter uma arquitetura limpa e escalável, com logs claros do ciclo de vida da aplicação e controle centralizado da configuração via dicionário e variáveis de ambiente.

## Fluxo de Execução

1. **Instanciação da classe**  
   O desenvolvedor cria uma instância de `WebServiceAPI`, opcionalmente passando um dicionário de configurações personalizado. Se nenhum dicionário for passado, é usado um padrão pelo import `CONFIG`.

2. **Inicialização da aplicação com `initialize()`**  
   Ao chamar o método `initialize()`, a aplicação FastAPI é criada com configurações de nome, descrição, versão, gerenciamento do ciclo de vida e middlewares CORS configurados, além das rotas padrão (`/health`, `/`, `/health-authorization`) sendo registradas.

3. **Inclusão de roteadores adicionais**  
   Após inicializar a aplicação, o desenvolvedor pode incluir roteadores adicionais utilizando os métodos `include_routers()` ou `test_routers()` passando listas de routers FastAPI. Cada inclusão é logada para facilitar o rastreamento.

4. **Descoberta dinâmica de roteadores**  
   Caso deseje, pode-se usar o método `collect_routers(package_name)` para carregar dinamicamente roteadores que estejam definidos em módulos de determinado pacote, permitindo extensibilidade modular.

5. **Obtenção da instância FastAPI**  
   Finalmente, para executar ou manipular a aplicação fora da classe, o método `get_app()` retorna a instância FastAPI já inicializada.

6. **Execução e log do ciclo de vida**  
   No momento da inicialização da aplicação, um banner e informações importantes são exibidos nos logs. Também são registrados os eventos de desligamento da aplicação.

## Tabela de Métodos da Classe

| Método          | Descrição                                               |
|-----------------|---------------------------------------------------------|
| `__init__`      | Inicializa a classe com configurações e prepara logger  |
| `initialize`    | Cria e configura a aplicação FastAPI                     |
| `include_routers` | Adiciona roteadores à aplicação após inicialização     |
| `test_routers`  | Adiciona roteadores à aplicação para fins de teste       |
| `collect_routers` | Descobre e importa roteadores de um pacote dinamicamente |
| `get_app`       | Retorna a instância FastAPI inicializada                  |

## Variáveis de Ambiente

- `DOMAIN`: Define o domínio base da aplicação, usado para exibir URLs e documentação. Caso não definida, assume `"http://localhost:8000"`.

## Pontos Importantes da Arquitetura e Insights

- A classe encapsula a configuração do FastAPI com base em um dicionário externo, facilitando a parametrização sem alterar código.
- Uso do `asynccontextmanager` para controlar o ciclo de vida da aplicação FastAPI, com logs claros no startup e shutdown.
- Inclusão dinâmica de roteadores com `collect_routers` utiliza introspecção via `pkgutil` e `importlib`, permitindo modularização de APIs.
- Separação clara entre configuração básica (middleware, rotas default) e expansão por rotas adicionais.
- O logger padrão é vinculado ao servidor `uvicorn`, garantindo integração com logs de runtime do ASGI.
- As rotas default incluem uma rota de autorização que depende de uma validação via API Key, usando o método estático `Authorization.validate_api_key`.

# Descrição da Classe e Métodos

## Classe `WebServiceAPI`

### Descrição

Esta classe representa um wrapper configurável para aplicações FastAPI, permitindo inicializar uma API web com base em configurações externas, adicionar middlewares e rotas padrões, gerenciar o ciclo de vida da aplicação e ampliar a API por meio da inclusão dinâmica de roteadores provenientes de pacotes Python.

### Argumentos do Construtor

| Argumento | Tipo | Descrição                      | Valor Padrão |
|-----------|------|-------------------------------|--------------|
| `config`  | dict | Dicionário com configurações para o serviço web | `CONFIG`     |

---

### 1. `__init__`

#### Descrição

Inicializa a classe, definindo configurações, logger e domínio base para a aplicação.

#### Argumentos

- `config` (dict): configurações para a API.

#### Retornos

- Não retorna valor.

#### Raises

- Nenhum.

#### Exemplos

```python
ws_api = WebServiceAPI()  # Usa CONFIG padrão
ws_api_custom = WebServiceAPI(config=my_config_dict)
```

---

### 2. `initialize`

#### Descrição

Cria e configura uma instância FastAPI com título, descrição, versão e o ciclo de vida definido. Adiciona middleware CORS e registra rotas padrão para health check e rota raiz.

#### Argumentos

- Nenhum.

#### Retornos

- FastAPI: instância da aplicação FastAPI inicializada.

#### Raises

- Nenhum.

#### Exemplos

```python
app = ws_api.initialize()
# app agora está pronta para uso em um servidor ASGI
```

---

### 3. `include_routers`

#### Descrição

Inclui uma lista de roteadores FastAPI na aplicação, garantindo que a aplicação já tenha sido inicializada. Faz log da inclusão de cada roteador.

#### Argumentos

- `routers` (list): lista de objetos router do FastAPI.

#### Retornos

- Não retorna valor.

#### Raises

- RuntimeError: se a aplicação não estiver inicializada.

#### Exemplos

```python
ws_api.include_routers([user_router, product_router])
```

---

### 4. `test_routers`

#### Descrição

Similar a `include_routers`, inclui uma lista de roteadores para possivelmente teste ou uso ad-hoc, com logging da inclusão.

#### Argumentos

- `routers` (list): lista de routers para incluir.

#### Retornos

- Não retorna valor.

#### Raises

- RuntimeError: se a aplicação não estiver inicializada.

#### Exemplos

```python
ws_api.test_routers([test_router])
```

---

### 5. `collect_routers`

#### Descrição

Descobre e importa dinamicamente todos os roteadores chamados `router` dentro dos módulos do pacote informado, retornando-os numa lista.

#### Argumentos

- `package_name` (str): nome do pacote (dotted path) onde procurar módulos com routers.

#### Retornos

- list: lista de instâncias de roteadores FastAPI encontrados.

#### Raises

- Nenhum.

#### Exemplos

```python
routers = ws_api.collect_routers("src.api.v1")
# Retorna todos os routers em src/api/v1/*
```

---

### 6. `get_app`

#### Descrição

Retorna a instância FastAPI inicializada para ser usada externamente.

#### Argumentos

- Nenhum.

#### Retornos

- FastAPI: instância FastAPI.

#### Raises

- RuntimeError: se chamada antes da inicialização da aplicação.

#### Exemplos

```python
app = ws_api.get_app()
```

---

**Exemplos práticos completos:**

```python
ws_api = WebServiceAPI()
app = ws_api.initialize()

routers = ws_api.collect_routers("src.api.v1")
ws_api.include_routers(routers)

# Agora app está pronto para ser executado
```

Outro exemplo simplificado:

```python
ws_api = WebServiceAPI()
ws_api.initialize()

ws_api.include_routers([user_router])

app = ws_api.get_app()
```

---

A documentação acima provê detalhes essenciais para a compreensão, extensão e uso prático da classe `WebServiceAPI` em projetos reais, facilitando o desenvolvimento de APIs modulares e bem configuradas com FastAPI.