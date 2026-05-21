# Classe `CurlCompiler`

## Visão Geral

A classe `CurlCompiler` foi criada para facilitar a interpretação e execução programática de comandos `curl` no ambiente Python, utilizando a biblioteca `requests`. Ela resolve o problema de automatizar requisições HTTP que seriam normalmente feitas via terminal, permitindo o parsing detalhado do comando `curl` para identificar método HTTP, cabeçalhos, autenticação, corpo da requisição e URL. 

Na prática, esta classe permite que desenvolvedores peguem qualquer comando `curl` e:
- obtenham seus componentes de forma estruturada (método, headers, dados),
- executem a requisição HTTP diretamente via código Python,
- imprimam as respostas de forma legível,
- gerem snippets Python equivalentes para reaproveitamento.

Isso é especialmente útil em cenários de testes de APIs, integração de sistemas ou quando o comando `curl` é gerado por outras ferramentas e precisa ser utilizado programaticamente.

---

## Fluxo de Execução

1. **Inicialização do objeto**: Cria-se uma instância da classe `CurlCompiler`, podendo definir timeout e se a verificação SSL está ativa ou não.
2. **Compilar comando curl**: Ao passar o comando `curl` como string ao método `compile`, ele será quebrado em tokens para extrair método HTTP, headers, body, autenticação e URL.
3. **Validação da compilação**: O comando é validado para garantir que possua URL e método HTTP válidos.
4. **Execução da requisição**: Usando o método `execute`, a classe compila o comando e dispara a requisição HTTP com base nos dados extraídos.
5. **Tratar resposta**: A resposta HTTP recebida pode ser convertida em dicionário para manipulações via `response_to_dict`, impressa de forma formatada com `pretty_print_response` ou inspecionada manualmente.
6. **Geração de código Python**: Pode-se gerar um snippet em Python equivalente ao comando `curl` com `generate_python_code` para reutilização ou documentação.

---

## Tabela de Métodos da Classe

| Método                | Descrição                                                          |
|-----------------------|-------------------------------------------------------------------|
| `__init__`            | Inicializa a classe com configurações de timeout e verificação SSL|
| `compile`             | Parseia o comando curl e devolve seus componentes em um dicionário|
| `execute`             | Compila e executa o comando curl, devolvendo a resposta HTTP      |
| `call_endpoint`       | Executa a requisição HTTP com parâmetros definidos manualmente    |
| `response_to_dict`    | Converte response `requests` em dicionário para fácil manipulação |
| `pretty_print_response`| Imprime a resposta HTTP formatada para leitura                    |
| `get_domain`          | Extrai o domínio de uma URL fornecida                              |
| `generate_python_code` | Gera código Python equivalente ao comando curl                    |

---

## Pontos Importantes da Arquitetura e Insights

- A classe usa parsing lexical via `shlex` para lidar corretamente com strings e espaços no comando `curl`.
- Implementa um encapsulamento claro: parsing, execução, manipulação da resposta e geração de código ficam separados em métodos.
- A decisão de definir automaticamente o método POST caso contenha body em um comando originalmente GET é prática comum e facilita o uso.
- Utiliza a biblioteca `requests` diretamente para execução, garantindo compatibilidade e robustez.
- O método `compile` cobre as opções principais do curl (método, headers, auth básica, dados) e é extensível.
- A geração de código Python permite integrar comandos curl externos rapidamente sem retrabalho manual.

---

# Descrição da Classe e Métodos

## Classe `CurlCompiler`

### Descrição

Classe que permite interpretar comandos `curl` para executar requisições HTTP via Python, facilitando automação, testes e integração de APIs. Faz parsing completo do comando para recuperar método, URL, cabeçalhos, autenticação e dados, e executar o chamado usando a biblioteca `requests`. Também possibilita manipulação fácil e exibição da resposta.

### Argumentos do Construtor

| Argumento   | Tipo  | Descrição                                  | Valor Padrão |
|-------------|-------|--------------------------------------------|--------------|
| timeout     | int   | Tempo limite em segundos para as requisições HTTP | 30           |
| verify_ssl  | bool  | Define se a verificação de certificado SSL é feita | True          |

---

### 1. `__init__`

#### Descrição

Inicializa o objeto `CurlCompiler` configurando o timeout para requisições HTTP e se a verificação SSL deve ser feita.

#### Argumentos

- timeout (int): tempo máximo em segundos para a requisição (default 30).
- verify_ssl (bool): ativa/desativa verificação SSL (default True).

#### Retornos

- Não retorna valor.

#### Raises

- Não se aplica.

#### Exemplos

```python
client = CurlCompiler(timeout=10, verify_ssl=False)
```

---

### 2. `compile`

#### Descrição

Recebe um comando `curl` (string), faz o parsing completo para extrair método HTTP, URL, headers, autenticação e corpo da requisição. Retorna um dicionário estruturado com essas informações prontas para consumo.

#### Argumentos

- curl_command (str): string contendo o comando curl completo.

#### Retornos

- dict: dicionário contendo chaves `method`, `url`, `headers`, `params`, `data`, `json`, `auth`.

#### Raises

- ValueError: se o comando não iniciar com "curl" ou se não contiver URL/metodo HTTP válidos.

#### Exemplos

```python
curl = 'curl -X POST https://api.exemplo.com -H "Content-Type: application/json" -d \'{"key":"value"}\''
compiled = client.compile(curl)
print(compiled['method'])  # "POST"
print(compiled['url'])     # "https://api.exemplo.com"
print(compiled['json'])    # {"key": "value"}
```

---

### 3. `execute`

#### Descrição

Compila o comando `curl` e executa a requisição HTTP retornando o objeto `requests.Response`.

#### Argumentos

- curl_command (str): comando curl a ser executado.

#### Retornos

- requests.Response: resposta recebida do servidor.

#### Raises

- Propaga exceções da compilação e da execução HTTP (ex: ValueError, requests exceptions).

#### Exemplos

```python
response = client.execute('curl -X GET https://httpbin.org/get')
print(response.status_code)  # 200
print(response.text)         # Conteúdo da resposta
```

---

### 4. `call_endpoint`

#### Descrição

Executa uma chamada HTTP direta usando parâmetros explícitos (método, url, headers, body, autenticação).

#### Argumentos

- method (str): método HTTP ('GET', 'POST', etc.)
- url (str): URL do endpoint
- headers (dict, opcional): headers HTTP
- data (qualquer, opcional): corpo da requisição em formato raw/texto
- json_data (qualquer, opcional): corpo da requisição em JSON serializável
- auth (tuple, opcional): par (username, password) para autenticação básica

#### Retornos

- requests.Response: resposta da requisição HTTP.

#### Raises

- Propaga exceções do requests.

#### Exemplos

```python
resp = client.call_endpoint(
    method='POST',
    url='https://api.exemplo.com',
    headers={'Content-Type': 'application/json'},
    json_data={'msg': 'oi'}
)
print(resp.status_code)
```

---

### 5. `response_to_dict`

#### Descrição

Converte o objeto `requests.Response` em dicionário contendo status, headers, corpo (JSON ou texto) e flag de sucesso.

#### Argumentos

- response (requests.Response): objeto de resposta HTTP.

#### Retornos

- dict: dicionário contendo as chaves `status_code`, `headers`, `body`, `success`.

#### Raises

- Não se aplica.

#### Exemplos

```python
resp_dict = client.response_to_dict(response)
print(resp_dict['status_code'])  # Exemplo: 200
print(resp_dict['body'])         # Conteúdo da resposta
```

---

### 6. `pretty_print_response`

#### Descrição

Imprime de forma formatada e legível os detalhes da resposta HTTP, incluindo status, headers e corpo.

#### Argumentos

- response (requests.Response): resposta HTTP a ser impressa.

#### Retornos

- None

#### Raises

- Não se aplica.

#### Exemplos

```python
client.pretty_print_response(response)
# Status: 200
# Headers: { ... }
# Body: { ... }
```

---

### 7. `get_domain`

#### Descrição

Extrai o domínio (host) a partir de uma URL completa.

#### Argumentos

- url (str): URL da qual extrair o domínio.

#### Retornos

- str: domínio extraído, por exemplo, "httpbin.org".

#### Raises

- Não se aplica.

#### Exemplos

```python
domain = client.get_domain("https://httpbin.org/post")
print(domain)  # httpbin.org
```

---

### 8. `generate_python_code`

#### Descrição

Gera um snippet de código Python usando `requests` que implementa o mesmo comportamento do comando `curl` recebido.

#### Argumentos

- curl_command (str): comando curl para ser convertido.

#### Retornos

- str: código Python formatado e indentado.

#### Raises

- Propaga erros da compilação do comando curl.

#### Exemplos

```python
code = client.generate_python_code('curl -X POST https://api.exemplo.com -H "Content-Type: application/json" -d \'{"key":"value"}\'')
print(code)
```

Exemplo esperado do output:

```python

# =========================================================
# EXEMPLO DE USO
# =========================================================

if __name__ == "__main__":

    curl = '''
    curl -X POST "https://httpbin.org/post" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer TOKEN_123" \
    -d '{"message":"hello world","value":123}'
    '''

    curl = '''
    curl --location --request POST 'http://localhost:8000/embedding'
    '''

    client = CurlCompiler(timeout=15)

    # Compilar CURL
    compiled = client.compile(curl)

    print("\nCURL COMPILADO:")
    print(json.dumps(compiled, indent=4, ensure_ascii=False))

    # Executar
    response = client.execute(curl)

    # Mostrar resposta
    client.pretty_print_response(response)

    # Gerar código equivalente
    print("\nCÓDIGO PYTHON GERADO:\n")
    print(client.generate_python_code(curl))
```
---

Esta documentação fornece uma visão completa e didática do funcionamento da classe `CurlCompiler` e seus principais métodos, habilitando desenvolvedores a utilizá-la de forma eficiente para parsing e execução automatizada de comandos `curl` em Python.