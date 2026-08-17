# Classe `ExchangeRateService`

## Visão Geral

A classe `ExchangeRateService` é responsável por gerenciar as cotações do dólar americano, combinando a obtenção de dados atualizados da API do Banco Central do Brasil (BCB) com o armazenamento local desses registros para consultas futuras. Ela mantém um histórico limitado de cotações para otimização do banco de dados local, evitando o armazenamento excessivo de dados antigos.

Esse serviço é útil para aplicações que precisam da cotação do dólar atualizada, mas também precisam garantir acesso rápido a dados recentes mesmo em momentos de falha na API externa. Ao armazenar localmente e limitar os dados guardados, a classe traz uma solução eficiente e resiliente para sistemas que dependem dessa informação.

Na prática, a classe pode ser usada para obter a cotação do dólar em tempo real, com fallback automático no último valor disponível e persistência do dado para futuras consultas.

---

## Fluxo de Execução

1. Instancia-se um objeto da classe `ExchangeRateService`.
2. Chama-se o método `get_usd_rate()` para obter a cotação do dólar.
3. O método verifica se já existe um registro da cotação do dia no banco local.
4. Se o registro do dia já estiver disponível, retorna esse valor direto do banco.
5. Se não, consulta a cotação mais recente na API do BCB.
6. Se a API retornar um valor válido:
   - O valor é armazenado no banco local.
   - É aplicada uma regra para limitar o número de registros salvos (mantendo até 5 registros).
   - O valor é retornado.
7. Se a API falhar e houver dados anteriores no banco, retorna-se o último valor armazenado.
8. Se não houver dados, retorna-se um valor base default e armazena essa base localmente.
9. O banco local é sempre mantido com no máximo 5 registros, removendo os mais antigos quando necessário.
10. Em caso de erro durante o processo, é lançado um `RuntimeError`.

---

## Tabela de Métodos da Classe

| Método            | Descrição                                      |
|-------------------|------------------------------------------------|
| `__init__`        | Inicializa o serviço, configura banco local e datas. |
| `_get_bcb_rate`   | Busca a cotação mais recente do dólar na API do BCB. |
| `_get_last_db_record` | Obtém o último registro armazenado localmente.       |
| `_enforce_limit`  | Limita o número de registros salvos, deletando os antigos. |
| `get_usd_rate`    | Obtém a cotação do dólar com fallback e persistência. |

---

## Pontos Importantes da Arquitetura e Insights

- **Design baseado em fallback robusto:** O método `get_usd_rate` tenta priorizar dados atualizados, mas lida graciosamente com falhas na API externa usando dados locais ou uma base padrão.
- **Encapsulamento:** O uso de métodos privados (`_get_bcb_rate`, `_get_last_db_record`, `_enforce_limit`) segrega as responsabilidades dentro da classe, mantendo a interface limpa para o usuário.
- **Limitação do histórico:** Manter um limite máximo de registros evita crescimento descontrolado do banco local, o que é importante para desempenho e espaço.
- **Integração com outras classes:** A classe utiliza `DocumentStore` para persistência local e `BCBExchangeRateService` para integração com a API externa de cotação, demonstrando composição e separação de responsabilidades.
- **Uso do formato de data padronizado:** Datas são sempre armazenadas e comparadas no formato ISO `%Y-%m-%d`, garantindo consistência.
- **Tratamento de exceções:** Erros gerais são capturados e encapsulados em um `RuntimeError` para sinalizar falhas específicas nesse serviço.

---

# Descrição da Classe e Métodos

## Classe `ExchangeRateService`

### Descrição

Classe para gerenciar cotações do dólar americano. Busca cotações na API do Banco Central do Brasil, armazena localmente as informações, mantém um histórico limitado dos dados e oferece acesso à cotação atual com mecanismos de fallback para garantir a continuidade do serviço mesmo em caso de falhas externas.

---

### Métodos

---

### 1. `__init__`

### Descrição

Inicializa a instância do serviço, configurando o gerenciador de banco local, definindo uma base padrão de cotação e armazenando a data atual formatada.

### Argumentos

Nenhum.

### Retornos

Não retorna valor.

### Raises

Nenhum.

### Exemplos

```python
service = ExchangeRateService()
```

---

### 2. `_get_bcb_rate`

### Descrição

Recupera a cotação mais recente do dólar na API do Banco Central do Brasil utilizando o serviço `BCBExchangeRateService`.

### Argumentos

Nenhum.

### Retornos

- float: Valor da cotação mais recente do dólar obtida da API.

### Raises

Nenhum (assumido que erros são tratados externamente).

### Exemplos

```python
rate = service._get_bcb_rate()
print(rate)  # Exemplo esperado: 5.25
```

---

### 3. `_get_last_db_record`

### Descrição

Busca no banco local o registro mais recente de cotação do dólar. Retorna o registro de maior data, ou None se não houver registros.

### Argumentos

Nenhum.

### Retornos

- dict ou None: Dicionário com o registro mais recente ou None se banco vazio.

### Raises

Nenhum.

### Exemplos

```python
last_record = service._get_last_db_record()
if last_record:
    print(last_record["rate"])
else:
    print("Nenhum registro encontrado.")
```

---

### 4. `_enforce_limit`

### Descrição

Limita o número máximo de registros salvos no banco local ao valor especificado, removendo os registros mais antigos caso o limite seja ultrapassado.

### Argumentos

- limit (int): Número máximo de registros permitidos no banco. Padrão é 5.

### Retornos

Não retorna valor.

### Raises

Nenhum.

### Exemplos

```python
service._enforce_limit(limit=5)
# Garante que no banco existam no máximo 5 registros recentes.
```

---

### 5. `get_usd_rate`

### Descrição

Obtém a cotação atual do dólar americano. Verifica primeiro se a cotação do dia já está salva no banco local; caso contrário, tenta buscar na API do BCB. Se a API retornar dados, salva-os localmente limitando o histórico. Caso a API falhe, retorna o último valor salvo ou um valor base padrão. Trata erros gerais lançando `RuntimeError`.

### Argumentos

Nenhum.

### Retornos

- float: Cotação atual pronta para uso.

### Raises

- RuntimeError: Caso haja falha geral na obtenção ou armazenamento da cotação.

### Exemplos

```python
try:
    rate = service.get_usd_rate()
    print(f"Cotação do dólar: {rate}")
except RuntimeError:
    print("Não foi possível obter a cotação.")

# python -m src.tokens_calculate.exchange_rate
```

---

# Fim da documentação.