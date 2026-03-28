# Documentação Didática da Classe `PlotCollector`

## Introdução / Visão Geral

A classe `PlotCollector` é uma ferramenta para coletar gráficos gerados pelo Matplotlib interceptando a exibição padrão via `plt.show()`. Ao substituir o método padrão de exibição, ela permite salvar os gráficos em arquivos PNG e manter uma versão base64 codificada dos mesmos, facilitando o uso dos gráficos para outras aplicações, como exibição em páginas web, relatórios, ou análise posterior. Além disso, permite gerenciamento simples dos gráficos coletados, como limpar registros e acessar os dados armazenados.

---

## Fluxo de Execução

1. **Instanciação:** O usuário cria uma instância de `PlotCollector`, podendo configurar o diretório de saída e se os gráficos serão salvos como arquivos.
2. **Patch do Matplotlib:** O método `patch_matplotlib()` é chamado para substituir o `plt.show` padrão pelo método `custom_show` da classe.
3. **Geração do Gráfico:** O usuário gera seus gráficos normalmente com Matplotlib.
4. **Exibição/Coleta:** O método `plt.show()` agora invoca `custom_show()`, que:
   - Salva o gráfico em um arquivo PNG (se habilitado)
   - Captura a imagem em uma string base64 (apenas parte inicial)
   - Armazena esses dados internamente em uma lista de gráficos coletados
   - Retorna as informações do gráfico salvo e sua representação base64.
5. **Gerenciamento:** O usuário pode recuperar todos os gráficos coletados via `get_graphs()` e limpar o histórico com `reset()`.

---

## Tabela de Métodos da Classe

| Método             | Descrição                                                                                   |
|--------------------|---------------------------------------------------------------------------------------------|
| `__init__`          | Inicializa o coletor configurando diretório e flag para salvar os gráficos.                 |
| `custom_show`       | Substitui `plt.show`, salva gráfico como arquivo PNG, gera base64 e armazena dados.        |
| `patch_matplotlib`  | Aplica o patch para substituir `plt.show` pelo método `custom_show` deste coletor.         |
| `reset`             | Limpa a lista de gráficos coletados, reiniciando o estado do coletor.                       |
| `get_graphs`        | Retorna a lista atual de gráficos coletados, contendo informações dos arquivos e base64.   |

---

## Pontos Importantes da Arquitetura e Insights

- **Interceção via Monkey Patching:** A classe modifica dinamicamente o comportamento do Matplotlib substituindo `plt.show()` pelo método próprio para garantir que gráficos sejam automaticamente coletados sem que o usuário precise alterar o fluxo natural de chamadas.
- **Armazenamento Misto:** Ao guardar tanto o arquivo físico do gráfico quanto a base64 parcial, a classe combina persistência e flexibilidade para diferentes usos futuros.
- **Modularidade:** O método de patch pode ser chamado em tempo de execução, permitindo ativação controlada do coletor, sem alterar diretamente o código dos usuários.
- **Gerenciamento Simples:** Métodos como `reset()` e `get_graphs()` oferecem controle para manipular os dados recolhidos, ideal para uso em aplicações iterativas ou Jupyter notebooks.

---

# Descrição da Classe e Métodos

---

## Classe `PlotCollector`

### Descrição

A classe `PlotCollector` intercepta as chamadas para exibir gráficos Matplotlib, salva os gráficos como arquivos PNG (quando habilitado) e armazena uma representação base64 parcial para uso em outras partes do programa. Permite gerenciar os gráficos coletados ao longo da execução da aplicação.

### Argumentos do Construtor

| Argumento   | Tipo   | Descrição                                                  | Valor Padrão     |
|-------------|--------|------------------------------------------------------------|------------------|
| `output_dir`| string | Diretório onde os gráficos serão salvos.                   | `"outputs"`      |
| `save`      | bool   | Define se os gráficos serão salvos em disco como PNG.     | `True`           |

### Métodos

---

### 1. `__init__(self, output_dir: str = "outputs", save: bool = True)`

#### Descrição

Inicializa a instância do coletor. Garante que o diretório para salvar os gráficos exista e configura o flag para salvar ou não os gráficos.

#### Argumentos

- `output_dir` (str): Diretório destino para os arquivos PNG.
- `save` (bool): Ativa/desativa o salvamento dos gráficos em disco.

#### Retornos

- Não retorna valor.

#### Raises

- Pode levantar exceções relacionadas à criação de diretórios, caso falhe.

#### Exemplos

```python
collector = PlotCollector(output_dir="meus_graficos", save=True)
```

---

### 2. `custom_show(self)`

#### Descrição

Método que substitui `plt.show`, interceptando a exibição do gráfico. Salva o gráfico em arquivo PNG (se habilitado), gera a representação codificada em base64 (com parte inicial para evitar excesso de memória), e registra essas informações internamente. Retorna um dicionário com os dados coletados.

#### Argumentos

- Nenhum.

#### Retornos

- `dict`: Contém:
  - `'file_path'`: Caminho do arquivo salvo ou `None` se não salvar.
  - `'image_base64'`: String com os primeiros 100 caracteres da imagem codificada em base64.

#### Raises

- `IOError`: Em caso de falha na gravação do arquivo PNG.

#### Exemplos

```python
collector = PlotCollector(save=True)
collector.patch_matplotlib()
plt.plot([1, 2, 3])
graph_data = plt.show()  # Chama custom_show internamente
print(graph_data['file_path'])  # Exemplo: outputs/plot_a1b2c3d4.png
```

---

### 3. `patch_matplotlib(self)`

#### Descrição

Aplica o patch que substitui a função padrão `plt.show()` do Matplotlib pelo método `custom_show` desta classe. Assim, todas as chamadas para exibir gráficos passam a ser interceptadas e coletadas automaticamente.

#### Argumentos

- Nenhum.

#### Retornos

- Não retorna valor.

#### Exemplos

```python
collector = PlotCollector()
collector.patch_matplotlib()
plt.plot([1, 2, 3])
plt.show()  # Usa custom_show internamente após patch
```

---

### 4. `reset(self)`

#### Descrição

Limpa a lista interna que armazena os dados dos gráficos coletados, reiniciando o estado do coletor.

#### Argumentos

- Nenhum.

#### Retornos

- Não retorna valor.

#### Exemplos

```python
collector = PlotCollector()
collector.reset()  # Remove todos os registros anteriores
```

---

### 5. `get_graphs(self)`

#### Descrição

Retorna a lista completa dos gráficos coletados até o momento. Cada elemento é um dicionário com o caminho do arquivo salvo (se houver) e a string base64 parcial correspondente.

#### Argumentos

- Nenhum.

#### Retornos

- `list`: Lista de dicionários com as informações dos gráficos.

#### Exemplos

```python
collector = PlotCollector()
graphs = collector.get_graphs()
print(graphs)
# [
#   {
#     'file_path': 'outputs/plot_abc123.png',
#     'image_base64': 'iVBORw0KGgoAAAANSUhEUgAAAE...'
#   }
# ]
```

---

## Considerações Finais

A `PlotCollector` é útil para automação e análise que dependem da captura e armazenamento dos gráficos gerados pelo Matplotlib sem modificar o fluxo natural do código. O uso da base64 permite integração com sistemas web, notebooks e aplicações que não manipulam diretamente arquivos físicos, enquanto o salvamento em disco garante a persistência necessária para laudos, backups e compartilhamento.

Para maximizar sua eficiência, recomenda-se aplicar o patch do matplotlib nas fases iniciais do programa e utilizar `reset()` para limpar os dados quando necessário, garantindo a organização da coleta dos gráficos gerados por diferentes etapas da aplicação.