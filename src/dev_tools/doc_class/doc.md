# Documentação Didática da Classe `PlotCollector`

## Visão Geral

A classe `PlotCollector` foi projetada para facilitar a coleta, armazenamento e salvamento de gráficos gerados com a biblioteca `matplotlib`. Normalmente, gráficos são exibidos via `plt.show()` e descartados em seguida. Com o `PlotCollector`, é possível interceptar essa exibição padrão para:

- Salvar os gráficos como arquivos de imagem em disco, em um diretório configurável.
- Armazenar representações base64 das imagens para uso em outros contextos (como exibição em interfaces web).
- Manter um registro de todos os gráficos coletados durante a execução.
- Substituir automaticamente o método padrão `plt.show()` para que a coleta ocorra sem necessidade de alterações extensas no código que gera gráficos.

Isso é especialmente útil para casos em que se desejam capturar e salvar todos os gráficos gerados em scripts complexos, gerar conteúdos para posts ou documentos, ou integrar gráficos em sistemas que não suportam a exibição gráfica tradicional.

---

## Fluxo de Execução

1. **Inicialização**: Ao criar uma instância do `PlotCollector`, definem-se o diretório de saída e se os arquivos devem ser salvos de fato.

2. **Interceptação do plt.show()**: Chamando `patch_matplotlib()`, o método padrão `plt.show()` do `matplotlib` é sobrescrito pelo método customizado da classe, que realiza o salvamento e armazenamento em base64.

3. **Geração dos gráficos**: Durante o código que gera gráficos, qualquer chamada a `plt.show()` é automaticamente interceptada e o gráfico é salvo e armazenado.

4. **Consulta dos gráficos coletados**: Pode-se consultar todos os gráficos coletados via `get_graphs()`.

5. **Limpeza**: A lista de gráficos pode ser resetada com `reset()` para começar uma nova coleta limpa.

---

## Tabela de Métodos da Classe

| Método             | Descrição Breve                                            |
|--------------------|------------------------------------------------------------|
| `__init__`         | Inicializa a classe, configura diretório e opção de salvar.|
| `custom_show`      | Substituto do `plt.show()` que salva e armazena o gráfico. |
| `patch_matplotlib` | Substitui `plt.show()` pela versão customizada.             |
| `reset`            | Limpa os dados internos dos gráficos coletados.             |
| `get_graphs`       | Retorna a lista com dados dos gráficos coletados.            |

---

## Pontos Importantes da Arquitetura e Insights

- **Interceptação do plt.show()**: Ao substituir globalmente o método `plt.show()` do matplotlib, a classe consegue capturar todos os gráficos exibidos sem necessidade que o usuário altere suas chamadas de plotagem.

- **Armazenamento em Base64** permite integração direta com web, notebooks e outras interfaces que aceitam imagens em formato texto.

- **Separação de responsabilidades**: O método `custom_show` encapsula a lógica de salvar e coletar, enquanto `patch_matplotlib` controla a substituição do comportamento padrão, mantendo o código organizado.

- **Flexibilidade**: O usuário pode optar por salvar ou não os gráficos em disco, funcionando tanto para geração de arquivos reais quanto para uso apenas em memória.

---

# Documentação Detalhada da Classe `PlotCollector`

## Classe PlotCollector

### Descrição

Classe para coletar gráficos gerados pelo matplotlib. Substitui o método padrão de exibição `plt.show()` por um que efetua o salvamento em disco (opcional) e armazena imagens em base64. Mantém um registro interno dos gráficos coletados para consulta posterior.

### Argumentos

- `output_dir (str)`: Diretório onde as imagens dos gráficos serão salvas. Default: `"outputs"`.
- `save (bool)`: Indicador para salvar (True) ou não (False) os gráficos em disco. Default: `True`.

### Métodos

---

#### 1. `__init__(output_dir: str = "outputs", save: bool = True)`

##### Descrição

Inicializa o coletor de gráficos, configurando o diretório de saída e se os gráficos devem ser salvos em disco. Cria o diretório se este não existir, e prepara a lista interna para armazenar metadados dos gráficos.

##### Argumentos

- `output_dir (str)`: Caminho da pasta onde serão salvos os gráficos.
- `save (bool)`: Define se os gráficos serão salvos em disco.

##### Retornos

- None

##### Raises

- Possíveis exceções decorrentes da criação de diretórios.

##### Exemplos

```python
collector = PlotCollector(output_dir='meus_graficos', save=True)
```

---

#### 2. `custom_show()`

##### Descrição

Substitui o comportamento padrão de `plt.show()` para além da exibição do gráfico, salvar a imagem em disco (se habilitado), armazenar a imagem em formato base64 e registrar as informações do arquivo gerado.

##### Argumentos

- Nenhum.

##### Retornos

- `dict`: Dicionário com as chaves:
  - `"file_path"`: Caminho completo do arquivo salvo no sistema (ou `None` caso não salve arquivo).
  - `"base64_str"`: String representando o gráfico em base64 (capturada parcialmente para controle).

##### Raises

- Exceções relacionadas a problemas na escrita de arquivos ou captura da imagem.

##### Exemplos

```python
info = collector.custom_show()
print(info['file_path'])
print(info['base64_str'][:50])  # Mostra parte da string base64
```

---

#### 3. `patch_matplotlib()`

##### Descrição

Substitui o `matplotlib.pyplot.show` pelo método `custom_show` desta classe, garantindo que todas as chamadas `plt.show()` no código façam a coleta automática dos gráficos.

##### Argumentos

- Nenhum.

##### Retornos

- None

##### Raises

- Nenhum explícito.

##### Exemplos

```python
collector.patch_matplotlib()
# A partir daqui, todas chamadas plt.show() salvam e armazenam os gráficos automaticamente.
```

---

#### 4. `reset()`

##### Descrição

Limpa os dados internos, removendo todos os registros dos gráficos coletados anteriormente.

##### Argumentos

- Nenhum.

##### Retornos

- None.

##### Raises

- Nenhum.

##### Exemplos

```python
collector.reset()
```

---

#### 5. `get_graphs()`

##### Descrição

Retorna a lista completa com todos os dicionários de metadados dos gráficos coletados. Cada dicionário contém informações como caminho do arquivo salvo e string base64 da imagem.

##### Argumentos

- Nenhum.

##### Retornos

- `list`: Lista cuja cada entrada é um dicionário com informações de um gráfico coletado.

##### Raises

- Nenhum.

##### Exemplos

```python
graphs = collector.get_graphs()
for g in graphs:
    print(g['file_path'], g['base64_str'][:30])
```
---

## Considerações Finais

A `PlotCollector` fornece uma forma elegante e transparente de integrar o processo de coleta de gráficos gerados pelo matplotlib. Ela permite manter um fluxo de trabalho natural utilizando `plt.show()`, mas enriquecido com funcionalidades de armazenamento e integração em outros contextos.

Ao entender sua arquitetura e métodos, é possível adaptar a classe para necessidades específicas, como extensão para suportar outros formatos de imagem, integração com web frameworks, ou customização do salvamento.