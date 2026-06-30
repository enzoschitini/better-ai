# Classe `RetrievalManager`

## Visão Geral

A classe `RetrievalManager` é uma ferramenta de gerenciamento de documentos recuperados, voltada para cenários de busca e análise de dados textuais. Ela facilita a filtragem de documentos baseada em scores (pontuações), a geração de contextos textuais compactos para uso em modelos de linguagem e a extração organizada de metadados de arquivos.

Em aplicações práticas, essa classe pode ser usada para controlar grandes volumes de documentos retornados em sistemas de recuperação da informação, garantindo que apenas os mais relevantes (com score acima de certo limiar ou acima da média) sejam considerados. Além disso, com a geração de contextos formatados, torna-se mais eficiente a federação desses conteúdos para LLMs ou outras análises textuais.

## Fluxo de Execução

1. **Inicialização:** Ao criar uma instância de `RetrievalManager`, você fornece uma lista de documentos, opcionalmente um score mínimo e se deseja que a filtragem por score seja feita automaticamente. Se a filtragem automática for ativada, a lista interna de documentos já estará pré-filtrada.

2. **Filtragem por Score:** Pode-se filtrar documentos para manter apenas aqueles cujo score seja maior ou igual ao score mínimo desejado, usando `get_by_score`.

3. **Filtragem pela Média:** Para refinamento, `filter_by_mean_score` permite filtrar um conjunto de chunks, mantendo só os que tenham score maior ou igual à média do conjunto.

4. **Geração de Contexto Compacto:** `generate_context` transforma os documentos em uma string formatada linha a linha, mostrando score e texto de forma compacta para facilitar seu uso.

5. **Extração de Metadados de Arquivos:** Por meio do método `get_files`, arquivos associados aos documentos são identificados e organizados para facilitar o acesso à sua identificação, nome, extensão e score máximo obtido.

## Tabela de Métodos da Classe

| Método           | Descrição                                              |
|------------------|-------------------------------------------------------|
| `__init__`       | Inicializa a instância com documentos e configurações |
| `get_by_score`   | Filtra documentos com score maior ou igual ao mínimo  |
| `filter_by_mean_score` | Filtra chunks com score maior ou igual à média     |
| `generate_context`| Gera string compacta de contexto estilo toon          |
| `get_files`      | Extrai e organiza metadados dos arquivos dos documentos|

## Pontos Importantes da Arquitetura e Insights

- **Imutabilidade parcial:** A classe altera sua lista interna de documentos somente se a filtragem automática for ativada, preservando o input inicial quando desejado.
- **Tratamento robusto de exceções:** Todos os métodos que fazem processamento crítico capturam exceções e levantam `RuntimeError` com mensagens claras para facilitar a depuração.
- **Estrutura de documentos flexível:** A classe assume que os documentos possuem um formato padrão com campos obrigatórios como 'text' e 'score', e campos opcionais 'metadata' com informações de arquivos — o que permite adaptação a diferentes fontes de dados.
- **Sem dependências externas:** Não usa outras classes auxiliares, o que torna o uso isolado e simples, apenas manipulando listas e dicionários.
- **Filtros distintos:** Com métodos distintos para filtragem por limiar fixo e filtragem por média, o gerenciamento fica mais flexível para diferentes critérios de relevância.

# Descrição da Classe e Métodos

## Classe `RetrievalManager`

### Descrição

Gerencia uma coleção de documentos textuais com pontuações associadas (scores), permitindo múltiplas operações importantes:

- Filtrar documentos com base em scores (fixos ou relativos à média do grupo).
- Criar uma representação textual compacta para integração com modelos de linguagem.
- Extrair metadados refinados para associação dos documentos a arquivos.

Serve para casos que envolvem recuperação e manipulação avançada de textos organizados por relevância.

### Argumentos do Construtor

| Argumento       | Tipo                   | Descrição                                                 | Valor Padrão |
|-----------------|------------------------|-----------------------------------------------------------|--------------|
| `docs`          | List[Dict[str, Any]]   | Lista de documentos com campos 'text', 'score' e opcional 'metadata' | -            |
| `score_min`     | float                  | Valor mínimo de score para filtro inicial de documentos  | 0.0          |
| `filter_by_score` | bool                  | Define se documentos serão filtrados por score na inicialização | False        |

### Métodos

---

### 1. `__init__`

### Descrição

Constrói o objeto `RetrievalManager` com uma lista de documentos e configurações opcionais para filtragem inicial por score mínimo.

### Argumentos

- docs (List[Dict[str, Any]]): documentos a gerenciar
- score_min (float): score mínimo para filtro inicial
- filter_by_score (bool): executa filtro automático se True

### Retornos

- Não retorna valor.

### Raises

- Não aplica.

### Exemplos

```python
rm = RetrievalManager(docs=documents, score_min=0.3, filter_by_score=True)
```

---

### 2. `get_by_score`

### Descrição

Filtra a lista de documentos para manter apenas aqueles cujo score seja maior ou igual ao score mínimo dado.

### Argumentos

- docs (List[Dict[str, Any]]): Lista opcional de documentos para filtrar. Se omitida, usa a lista interna.
- score_min (float): Score mínimo para filtragem.

### Retornos

- List[Dict[str, Any]]: lista filtrada de documentos.

### Raises

- RuntimeError: ao falhar filtro por score.

### Exemplos

```python
filtered_docs = rm.get_by_score(score_min=0.35)
```

---

### 3. `filter_by_mean_score`

### Descrição

Recebe uma lista de chunks (documentos), calcula a média dos scores e filtra para manter apenas os chunks com score maior ou igual a essa média.

### Argumentos

- chunks (list[dict[str, Any]]): lista de chunks com campo 'score'.

### Retornos

- list[dict[str, Any]]: lista filtrada ou vazia se input vazio.

### Raises

- RuntimeError: se ocorrer erro no cálculo ou filtragem.

### Exemplos

```python
chunks = [
    {"text": "A", "score": 0.5},
    {"text": "B", "score": 0.3},
    {"text": "C", "score": 0.7},
]
filtered = rm.filter_by_mean_score(chunks)
# filtered conterá chunks com score >= 0.5
```

---

### 4. `generate_context`

### Descrição

Gera uma string compacta no formato "Score: X | Content: texto" para cada documento, substituindo quebras de linha no texto por espaços para melhor formatação.

### Argumentos

- docs (List[Dict[str, Any]]): documentos a serem convertidos para contexto. Usa os internos da classe se omitido.

### Retornos

- str: string concatenada com documentos formatados linha a linha.

### Raises

- RuntimeError: em falha no processamento da string.

### Exemplos

```python
context_string = rm.generate_context()
print(context_string)
# Exemplo saída:
# Score: 0.38 | Content: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# Score: 0.36 | Content: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### 5. `get_files`

### Descrição

Extrai informações padronizadas de arquivos presentes nos metadados dos documentos, retornando uma lista de arquivos com id, nome, extensão e maior score associado.

### Argumentos

- docs (List[Dict[str, Any]]): lista de documentos para extrair metadados. Usa lista interna se omitido.

### Retornos

- List[Dict[str, Any]]: lista de dicionários representando arquivos filtrados pelo id e ordenados conforme último processamento.

### Raises

- RuntimeError: em caso de erro ao extrair metadados.

### Exemplos

```python
files_info = rm.get_files()
print(files_info)
# [
#   {"id": "cucinare", "name": "LESSICO per CUCINARE.pdf", "ext": "pdf", "score": 0.38},
#   {"id": "tenerezza", "name": "TENEREZZA.pdf", "ext": "pdf", "score": 0.36}
# ]
```

---

Esta documentação detalha o funcionamento prático da classe `RetrievalManager`, servindo de guia para desenvolvedores que precisam manipular documentos com métricas de relevância e metadados associados.