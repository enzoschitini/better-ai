# Classe `BCBExchangeRateService`

## Visão Geral

A classe `BCBExchangeRateService` oferece um serviço para consultar a cotação do dólar em relação ao real diretamente da API oficial do Banco Central do Brasil (BCB). Este serviço é útil para desenvolvimento de aplicações financeiras, sistemas de câmbio, análise econômica e situações onde é necessário obter taxas de câmbio atualizadas de forma automática e programática.

A principal funcionalidade da classe é permitir a busca da taxa de câmbio do dólar para datas específicas, além de facilitar a recuperação da melhor cotação disponível dentro de um intervalo de dias passados, começando pela data atual. Isso garante flexibilidade para captar valores mesmo quando não há cotação em dias recentes, por exemplo, fins de semana ou feriados.

Na prática, um desenvolvedor pode instanciar a classe e chamar o método `get_latest_rate`, definindo quantos dias anteriores considerar na busca da cotação. O método retorna a melhor taxa e a data correspondente, facilitando integrações rápidas com dados oficiais.

---

## Fluxo de Execução

1. **Inicialização:** O usuário cria uma instância de `BCBExchangeRateService`, podendo definir um tempo limite (timeout) para as requisições HTTP (padrão 10 segundos).
2. **Chamada do método `get_latest_rate`:** Este método recebe um parâmetro opcional `max_days_back` que define a quantidade de dias anteriores para buscar a cotação.
3. **Busca iterativa:** Para cada dia, começando pelo atual e retrocedendo até `max_days_back`, o método faz uma requisição GET na API do BCB usando o formato de URL construído para aquela data.
4. **Processamento da resposta:** Se a API devolve dados válidos, o método extrai a cotação de venda e a data daquela cotação.
5. **Comparação e seleção:** A cada cotação obtida, verifica se é a melhor (mais recente) encontrada até então e armazena essa informação.
6. **Atraso entre requisições:** Há um pequeno delay de 0,2 segundos entre cada tentativa para não sobrecarregar a API.
7. **Retorno do resultado:** Após percorrer os dias, retorna um dicionário com o valor da melhor cotação encontrada e sua respectiva data. Se ocorrer algum erro, retorna valores `None`.
8. **Logs:** O processo imprime no console detalhes das tentativas, sucessos, falhas e resultado final.

---

## Tabela de Métodos da Classe

| Método        | Descrição                                               |
|---------------|---------------------------------------------------------|
| `__init__`    | Inicializa a instância definindo o timeout das requisições. |
| `_build_url`  | Monta a URL da API para uma data específica.             |
| `_fetch_rate_for_date` | Realiza a requisição HTTP para obter a cotação de uma data.   |
| `get_latest_rate` | Busca a melhor cotação disponível dentro do intervalo definido. |

---

## Variáveis de Ambiente

Não há variáveis de ambiente utilizadas para o funcionamento desta classe.

---

## Pontos Importantes da Arquitetura e Insights

- **Encapsulamento:** A classe separa explicitamente a construção da URL (`_build_url`) e a obtenção dos dados (`_fetch_rate_for_date`) como métodos privados, mantendo a API pública limpa.
- **Robustez:** O código trata exceções em vários pontos para evitar que falhas em requisições comprometam a operação geral.
- **Respeito à API:** Uso de delays entre requisições evita sobrecarregar o serviço do BCB.
- **Dependência externa:** Utiliza a biblioteca `requests` para comunicação HTTP, garantindo facilidade e robustez nas chamadas.
- **Boa prática temporal:** Usa datas em UTC e formata data para o padrão esperado pela API.
- **Retorno estruturado:** Confere a consumibilidade by retornando um dicionário com `rate` e `date`, facilitando integrações.

---

# Descrição da Classe e Métodos

## Classe `BCBExchangeRateService`

### Descrição

Esta classe é responsável por consultar cotações do dólar americano frente ao real brasileiro diretamente da API oficial do Banco Central do Brasil. Permite tanto consultar valores para datas específicas quanto buscar a melhor cotação dentro de um período, facilitando aplicações financeiras que necessitam de dados atualizados e confiáveis.

### Argumentos do Construtor

| Argumento | Tipo | Descrição                          | Valor Padrão |
|-----------|-------|----------------------------------|--------------|
| `timeout` | int   | Tempo máximo em segundos para requisições HTTP | 10           |

---

### 1. `__init__`

### Descrição

Inicializa uma instância do serviço definindo o tempo máximo para respostas das requisições HTTP realizadas à API do BCB.

### Argumentos

- `timeout` (int): tempo limite em segundos para requisições.

### Retornos

- Não retorna valor.

### Raises

- Nenhum.

### Exemplos

```python
service = BCBExchangeRateService(timeout=5)  # Timeout menor para conexões lentas
```

---

### 2. `_build_url`

### Descrição

Método privado que constrói a URL de consulta da API do Banco Central para uma data específica, formatando a data no padrão exigido.

### Argumentos

- `date` (datetime): data que será consultada na API.

### Retornos

- `str`: URL formatada para realizar a consulta.

### Raises

- Nenhum.

### Exemplos

```python
from datetime import datetime
service = BCBExchangeRateService()
url = service._build_url(datetime(2024, 6, 10))
print(url)
# Exemplo de saída:
# https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='06-10-2024'&$top=1&$format=json
```

---

### 3. `_fetch_rate_for_date`

### Descrição

Método privado que tenta buscar a cotação do dólar para uma data específica utilizando a API do Banco Central. Retorna a cotação de venda e a data da cotação caso sucesso.

### Argumentos

- `date` (datetime): data para a qual a cotação será consultada.

### Retornos

- `(float, datetime)`: uma tupla contendo o valor da cotação (float) e a data da cotação (datetime).
- `(None, None)`: caso não seja possível obter a cotação por erro ou ausência de dados.

### Raises

- Nenhum explicitamente, mas possíveis exceções são capturadas internamente.

### Exemplos

```python
service = BCBExchangeRateService()
rate, date = service._fetch_rate_for_date(datetime(2024, 6, 10))
print(rate, date)
# Saída esperada (se houver cotação nessa data):
# 5.0892 2024-06-10 00:00:00
```

---

### 4. `get_latest_rate`

### Descrição

Busca a melhor cotação do dólar em relação ao real disponível nos últimos `max_days_back` dias a partir do momento da chamada, retornando o valor e a data da cotação mais recente encontrada.

### Argumentos

- `max_days_back` (int): número de dias anteriores para buscar a cotação (default: 5).

### Retornos

- `dict`: com as chaves:
  - `rate` (float ou None): melhor cotação encontrada.
  - `date` (datetime ou None): data dessa cotação.

### Raises

- Nenhum explicitamente, erros são tratados internamente.

### Exemplos

```python
service = BCBExchangeRateService()
result = service.get_latest_rate(3)
print(f"Cotação: {result['rate']} em {result['date']}")
# Saída possível:
# Cotação: 5.0892 em 2024-06-10 00:00:00

# python -m src.tokens_calculate.bcb
```

---

Assim, a classe `BCBExchangeRateService` é uma solução prática e confiável para obter cotações oficiais do dólar comercial, útil para qualquer sistema que necessite acesso facilitado e programático a esses dados.