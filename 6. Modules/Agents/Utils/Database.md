# Classe `Database`

## Visão Geral

A classe `Database` atua como uma **fábrica de conexão** com bancos de dados, fornecendo uma interface unificada para conectar-se tanto a um banco SQLite local quanto a um banco Postgres hospedado no Supabase. Ela abstrai detalhes de configuração e escolhas de implementação, permitindo que o desenvolvedor selecione o tipo de banco apenas passando parâmetros simples, sem precisar lidar com configurações complexas.

Esse design é útil quando você tem ambientes diversos, como desenvolvimento local e produção na nuvem, e deseja uma forma consistente e elegante de inicializar conexões com diferentes bancos de dados, mantendo o restante da aplicação desacoplado da camada de persistência.

## Fluxo de Execução

1. Ao instanciar a classe `Database`, você chama seu construtor (na verdade usa o método `__new__` customizado).
2. O parâmetro `local` decide se a conexão será com SQLite local (`local=True`) ou Supabase Postgres (`local=False`).
3. Se for local, chama-se o método `_local_database`, que constrói a conexão do tipo `SqliteDb` usando o arquivo `.db`.
4. Caso contrário, chama-se `_supabase` que cria a conexão do tipo `PostgresDb`, montando a URL do banco usando variáveis de ambiente ou parâmetro passado.
5. Métodos estáticos auxiliares geram nomes de schema, caminhos ou URLs conforme parâmetros e padrões internos.
6. Por fim, o objeto da respectiva classe de banco de dados (`SqliteDb` ou `PostgresDb`) é retornado, pronto para uso.

## Tabela de Métodos da Classe

| Método          | Descrição                                            |
|-----------------|-----------------------------------------------------|
| `__new__`       | Controla a criação do objeto, decide qual banco usar|
| `_get_schema_name` | Retorna o nome do schema para Postgres             |
| `_get_database_local_storage` | Construção do caminho do arquivo SQLite     |
| `_get_database_url` | Gera ou retorna a URL do banco Postgres           |
| `_supabase`     | Cria e configura o objeto de conexão Postgres       |
| `_local_database` | Cria e configura o objeto de SQLite                 |

## Variáveis de Ambiente

- `SUPABASE_PROJECT_HOST`: Host do projeto Supabase para construção da URL de conexão.
- `SUPABASE_DATABASE_PASSWORD`: Senha do banco Postgres do Supabase.

## Pontos Importantes da Arquitetura e Insights

- Usa o método mágico `__new__` para implementar o padrão de **Factory**, retornando diferentes tipos de objetos conforme parâmetros.
- O encapsulamento garante que detalhes específicos do banco (URLs, nomes de tabelas) ficam centralizados, facilitando manutenção.
- Os métodos estáticos são usados para lógica de composição de strings, separando responsabilidades.
- A classe depende das classes `SqliteDb` e `PostgresDb`, que representam as conexões efetivas aos bancos.
- Variáveis de ambiente são usadas para manter dados sensíveis fora do código, seguindo boas práticas.
- Permite injeção de parâmetros para maior flexibilidade (ex: nome do banco, URL customizada).

# Descrição da Classe e Métodos

## Classe `Database`

### Descrição

Classe fábrica para facilitar a conexão com bancos SQLite locais ou Supabase Postgres, abstraindo a complexidade de configuração e conexão.

### Argumentos do Construtor

| Argumento      | Tipo                | Descrição                                                   | Valor Padrão |
|----------------|---------------------|-------------------------------------------------------------|--------------|
| `local`        | `bool`              | Define se conecta localmente (SQLite), caso contrário Supabase Postgres | False        |
| `database_name` | `str | None`       | Nome do banco ou schema, opcional                            | None         |
| `database_url` | `str | None`        | URL completa para conexão remota, opcional                  | None         |

### Métodos

---

### 1. `__new__`

### Descrição

Método especial que controla a criação da instância da classe. Decide, conforme parâmetros, se será criado um objeto `SqliteDb` para banco local ou `PostgresDb` para Supabase.

### Argumentos

- `local` (bool): indica uso local ou remoto.
- `database_name` (str | None): nome do banco/schema.
- `database_url` (str | None): URL do banco remoto.

### Retornos

- `SqliteDb` ou `PostgresDb`: objeto configurado para interagir com o banco correspondente.

### Raises

Nenhum.

### Exemplos

```python
# Conecta a banco SQLite local padrão
db_local = Database(local=True)

# Conecta a banco Supabase com nome específico
db_supabase = Database(local=False, database_name="test_schema")
```

---

### 2. `_get_schema_name`

### Descrição

Retorna o nome do schema para conexão Postgres, usando o nome passado ou o default "agent_db".

### Argumentos

- `database_name` (str | None): nome do schema.

### Retornos

- `str`: nome do schema a ser usado.

### Raises

Nenhum.

### Exemplos

```python
Database._get_schema_name("prod_schema")  # Retorna "prod_schema"
Database._get_schema_name(None)           # Retorna "agent_db"
```

---

### 3. `_get_database_local_storage`

### Descrição

Monta o caminho do arquivo `.db` para o banco SQLite local conforme o nome fornecido.

### Argumentos

- `database_name` (str | None): nome do arquivo sem extensão.

### Retornos

- `str`: caminho completo do arquivo SQLite.

### Raises

Nenhum.

### Exemplos

```python
Database._get_database_local_storage("testdb")  # "src/agents/database/testdb.db"
Database._get_database_local_storage(None)      # "src/agents/database/agno.db"
```

---

### 4. `_get_database_url`

### Descrição

Retorna a URL de conexão para o banco Postgres do Supabase. Usa a URL passada, se fornecida, ou constrói a partir das variáveis de ambiente.

### Argumentos

- `database_url` (str | None): URL completa opcional.

### Retornos

- `str`: URL de conexão ao banco.

### Raises

Nenhum.

### Exemplos

```python
# Usando URL direta
Database._get_database_url("postgresql://user:pass@host:5432/db")

# Usando ENV-SUPABASE_PROJECT_HOST e SUPABASE_DATABASE_PASSWORD
Database._get_database_url(None)  # Exemplo: "postgresql://postgres:password@db.projecthost:5432/postgres"
```

---

### 5. `_supabase`

### Descrição

Cria uma instância de `PostgresDb` configurada para Supabase, com nome do schema e URL definidos.

### Argumentos

- `database_url` (str | None): URL da conexão remota.
- `database_name` (str | None): nome do schema.

### Retornos

- `PostgresDb`: objeto configurado para uso com Supabase.

### Raises

Nenhum.

### Exemplos

```python
db = Database._supabase(database_url=None, database_name="my_schema")
# db é uma instância de PostgresDb pronta para manipular o banco remoto
```

---

### 6. `_local_database`

### Descrição

Cria uma instância de `SqliteDb` configurada para uso local, definindo o caminho do arquivo .db e tabelas.

### Argumentos

- `database_name` (str | None): nome do arquivo do banco local.

### Retornos

- `SqliteDb`: objeto configurado para banco SQLite local.

### Raises

Nenhum.

### Exemplos

```python
db = Database._local_database(database_name="localdb")
# db é uma instância de SqliteDb pronta para manipulação local
```

---

Essa documentação fornece uma visão completa e didática da classe `Database`, facilitando seu entendimento e uso prático.