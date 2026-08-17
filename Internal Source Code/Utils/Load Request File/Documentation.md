# Classe `LoadRequestFile`

## Visão Geral

A classe `LoadRequestFile` foi desenvolvida para facilitar o processo de carregamento e validação de arquivos enviados em requisições através do FastAPI. Ela garante que o arquivo recebido possua uma extensão e tipo MIME permitidos, além de verificar se seu tamanho está dentro de um limite configurado, evitando problemas como uploads indevidos ou arquivos muito grandes que possam comprometer o sistema.

Na prática, essa classe pode ser utilizada para controlar de forma segura quais arquivos uma aplicação aceita para processamento, protegendo o backend contra entradas inesperadas ou maliciosas. Por exemplo, pode ser usada em APIs onde usuários fazem upload de imagens, documentos ou outros arquivos, assegurando compliance com as regras definidas.

## Fluxo de Execução

1. Uma instância da classe é criada passando o objeto `UploadFile` da requisição e, opcionalmente, listas com extensões e tipos MIME permitidos, além do tamanho máximo permitido.
2. O método `load()` é chamado assincronamente para ler o conteúdo do arquivo da requisição.
3. Durante o carregamento, a classe calcula o tamanho do arquivo em bytes e megabytes e mantém uma cópia do conteúdo em um objeto `BytesIO`, facilitando acesso futuro.
4. Em sequência, o arquivo é validado contra as listas de extensões e tipos MIME permitidos, além de verificar se seu tamanho não excede o limite configurado.
5. Caso alguma validação falhe, uma exceção HTTP 400 é levantada com uma mensagem clara sobre o motivo.
6. Se todas as validações passarem, a instância com as informações e conteúdo do arquivo é retornada, pronta para uso posterior no fluxo da aplicação.

## Tabela de Métodos da Classe

| Método     | Descrição                                                  |
|------------|------------------------------------------------------------|
| `__init__` | Inicializa a instância com arquivo, configurações e dados básicos. |
| `load`     | Carrega o conteúdo do arquivo, calcula metadados e realiza validações. |
| `to_dict`  | Retorna um dicionário com informações do arquivo carregado. |

## Pontos Importantes da Arquitetura e Insights

- A classe encapsula completamente a lógica de carregamento e validação, promovendo reutilização e separação clara de responsabilidades.
- O uso do módulo `BytesIO` permite trabalhar com o conteúdo do arquivo em memória sem a necessidade de salvar no disco, aumentando a eficiência.
- O design usa validações específicas e levantam exceções HTTP diretamente, integrando-se facilmente ao fluxo de tratamento de erros do FastAPI.
- Ela depende de configurações externas para as extensões e MIME types permitidos, dando flexibilidade para ajustes sem alteração do código fonte.
- A arquitetura modular permite extensão simples, por exemplo, adicionando outras validações sem alterar a interface pública.

# Descrição da Classe e Métodos

## Classe `LoadRequestFile`

### Descrição

A `LoadRequestFile` representa um utilitário para manipular arquivos enviados via requisição HTTP com FastAPI. Ela é responsável por carregar o arquivo recebido, extrair informações como extensão, MIME type e tamanho, além de validar se o arquivo está dentro dos padrões permitidos configurados para o sistema.

### Argumentos do Construtor

| Argumento          | Tipo        | Descrição                                                  | Valor Padrão       |
|--------------------|-------------|------------------------------------------------------------|--------------------|
| `file`             | `UploadFile`| Arquivo enviado na requisição a ser carregado e validado. | Nenhum (obrigatório) |
| `allowed_extensions`| `list[str]` | Lista de extensões permitidas para validação.              | `ALLOWED_EXTENSIONS`|
| `allowed_mimetypes` | `list[str]` | Lista de tipos MIME permitidos para validação.              | `ALL_MIMETYPES`    |
| `max_size_mb`       | `float`     | Tamanho máximo permitido para o arquivo em megabytes.      | 10                 |

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa uma instância da classe com o arquivo recebido e as configurações de validação, preparando atributos para carregamento e validações futuras.

### Argumentos

- `file` (`UploadFile`): Arquivo enviado na requisição.
- `allowed_extensions` (`list[str]`): Extensões permitidas. Default: `ALLOWED_EXTENSIONS`.
- `allowed_mimetypes` (`list[str]`): MIME types permitidos. Default: `ALL_MIMETYPES`.
- `max_size_mb` (`float`): Tamanho máximo permitido (em MB). Default: 10.

### Retornos

- Não retorna valor.

### Raises

- Nenhum.

### Exemplos

```python
# Criar uma instância para validar arquivo recebido e configurar limites
loader = LoadRequestFile(file, max_size_mb=5)
```

---

### 2. `load`

### Descrição

Método assíncrono que carrega o conteúdo integral do arquivo, calcula seu tamanho em bytes e megabytes, armazena os dados em memória e realiza todas as validações estabelecidas (extensão, MIME type e tamanho).

### Argumentos

- Nenhum.

### Retornos

- `LoadRequestFile`: retorna a própria instância com dados carregados e validados.

### Raises

- `HTTPException`: se alguma validação falhar, com status 400 e mensagem informativa.

### Exemplos

```python
# Uso assíncrono: carregar e validar arquivo recebido na requisição
loader = await LoadRequestFile(file).load()
print(loader.to_dict())
# Exemplo de saída:
# {
#   "filename": "photo.jpg",
#   "extension": "jpg",
#   "mimetype": "image/jpeg",
#   "size_bytes": 152000,
#   "size_mb": 0.15
# }
```

---

### 3. `to_dict`

### Descrição

Gera um dicionário com os principais metadados do arquivo carregado, facilitando inspeção e eventual registro ou resposta à API.

### Argumentos

- Nenhum.

### Retornos

- `dict`: contendo `filename`, `extension`, `mimetype`, `size_bytes` e `size_mb` arredondado.

### Raises

- Nenhum.

### Exemplos

```python
# Obter informações resumidas sobre o arquivo carregado
info = loader.to_dict()
print(info["filename"])  # ex: "document.pdf"
print(info["size_mb"])   # ex: 2.45
```