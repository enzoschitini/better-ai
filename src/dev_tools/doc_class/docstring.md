```python
class PlotCollector:
    """
    Colecionador de gráficos que intercepta a exibição padrão do Matplotlib, salva os gráficos em arquivos e/ou 
    mantém uma representação base64 para uso posterior. Permite o gerenciamento dos gráficos coletados.

    Args:
        output_dir (str): Diretório onde os arquivos de gráficos serão salvos. Default é "outputs".
        save (bool): Indica se os gráficos gerados devem ser salvos como arquivos PNG. Default é True.

    Methods:
        custom_show(): Substitui o método plt.show do Matplotlib para salvar o gráfico, gerar base64 e coletar dados.
        patch_matplotlib(): Aplica o patch para substituir plt.show pelo método custom_show deste coletor.
        reset(): Limpa a lista de gráficos coletados.
        get_graphs(): Retorna a lista dos gráficos coletados, contendo caminho do arquivo e base64 parcial.
    """

    def __init__(self, output_dir: str = "outputs", save: bool = True):
        """
        Inicializa a instância do coletor de gráficos, criando o diretório de saída caso necessário e configurando 
        se os gráficos devem ser salvos.

        Args:
            output_dir (str): Diretório para salvar os gráficos gerados. Default é "outputs".
            save (bool): Flag para indicar se os gráficos devem ser salvos em disco. Default é True.
        """

    def custom_show(self):
        """
        Método customizado que substitui a função padrão plt.show do Matplotlib. Ele salva o gráfico como PNG (se 
        configurado para salvar), gera uma string base64 para o gráfico e armazena essas informações na lista de gráficos.

        Returns:
            dict: Dicionário contendo 'file_path' com o caminho do arquivo salvo (ou None se não salvar) e 
                  'image_base64' com os primeiros 100 caracteres da imagem codificada em base64.

        Raises:
            IOError: Se houver falha ao salvar o arquivo de imagem.

        Examples:
            >>> collector = PlotCollector(save=True)
            >>> collector.patch_matplotlib()
            >>> plt.plot([1, 2, 3])
            >>> graph_data = plt.show()
            >>> print(graph_data['file_path'])
            'outputs/plot_abcdef123456.png'
        """

    def patch_matplotlib(self):
        """
        Substitui o método plt.show do Matplotlib pelo método custom_show desta classe, permitindo que todas as 
        chamadas de exibição de gráfico sejam interceptadas e registradas pelo coletor.

        Examples:
            >>> collector = PlotCollector()
            >>> collector.patch_matplotlib()
            >>> plt.plot([1, 2, 3])
            >>> plt.show()  # Agora usará custom_show implicitamente
        """

    def reset(self):
        """
        Limpa a lista interna de gráficos coletados, descartando todos os registros anteriores. Útil para reiniciar 
        o estado do coletor entre diferentes conjuntos de gráficos.

        Examples:
            >>> collector = PlotCollector()
            >>> collector.reset()  # Remove gráficos coletados anteriormente
        """

    def get_graphs(self):
        """
        Retorna a lista dos gráficos coletados até o momento. Cada elemento da lista é um dicionário contendo 
        informações parciais do gráfico, como caminho do arquivo salvo e string base64.

        Returns:
            list: Lista de dicionários com os dados dos gráficos coletados.

        Examples:
            >>> collector = PlotCollector()
            >>> graphs = collector.get_graphs()
            >>> print(graphs)
            [{'file_path': 'outputs/plot_...', 'image_base64': 'iVBORw0KGgoAAAANSUhEUgAAAEAAA...'}]
        """
```