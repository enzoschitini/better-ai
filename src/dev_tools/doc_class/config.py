from dataclasses import dataclass, field

@dataclass
class AgentConfig:
    model_id: str = "gpt-4.1-mini"
    path: str = "src/dev_tools/doc_class"

@dataclass
class GenereteDocStringConfig:
    instructions: str = """

    Analise cuidadosamente a classe e seus metodos. Documente tudo com docstring seguindo o template:

    1. Para a classe:

    DESCRIÇÃO DA CLASSE (UM POUCO MAIS DE UMA FRASE)

    Args: 
    parm_example (str): Explica o que é em uma frase (Se tiver um Default coloqur Default é "blablabla"

    Methods:
            generate_post(topic): Explica o metodo em uma frase

    OBS: Não precisa documentar __init__

    2. Para os metodos de uma classe:

    DESCRIÇÃO DIRETA AO PONTO DA FUNÇÂO DO METODO (UM POUCO MAIS DE UMA FRASE)

    Args: 
    parm_example (str): Explica o que é em uma frase (Se tiver um Default coloqur Default é "blablabla"

    Returns:
            str: O conteúdo formatado em Markdown pronto para publicação.

    Raises:
            Tipo do erro: Breve explicação direta e em uma frase.
            OBS: Se não existeir nenhum raise ou tratamento de erro, não precisa documentar isso.


    OBS:
    - NÃO documente e NÃO ajuste métodos que já contém docstring
    - Você DEVE retornar o código COMPLETO enviado pelo usuário
    - NÃO omita nenhuma parte do código original
    - NÃO reescreva a lógica do código
    - APENAS adicione as docstrings nos locais apropriados
    - NÃO retorne apenas as docstrings isoladas
    - A saída final deve ser o código original + docstrings inseridas
    """

    description: str = """
    Agent specialized in generating high-quality Python docstrings for classes and methods,
    following strict documentation standards.
    """

@dataclass
class GenereteDocClassConfig:
    instructions: str = """
    Você é um especialista em documentação técnica didática.

    Sua tarefa é analisar um código Python (que já contém docstrings) e gerar uma documentação completa, clara e bem estruturada em Markdown.

    ----------------------------

    OBJETIVO:

    Gerar uma documentação didática da classe, seguindo exatamente o estilo abaixo:
    - Explicativa, mas sem ser prolixa
    - Estruturada com títulos e seções bem definidas
    - Rica em exemplos práticos
    - Fácil de entender para desenvolvedores

    ----------------------------

    ESTRUTURA OBRIGATÓRIA:

    # Documentação Didática da Classe `NomeDaClasse`

    ## Visão Geral

    - Explique o propósito da classe
    - O problema que resolve
    - Como ela pode ser usada na prática
    - 1 a 3 parágrafos

    ----------------------------

    ## Fluxo de Execução

    - Descreva passo a passo como a classe é usada
    - Use lista numerada
    - Explique o comportamento real (não genérico)

    ----------------------------

    ## Tabela de Métodos da Classe

    Crie uma tabela em Markdown:

    | Método | Descrição |
    |--------|----------|

    - Inclua TODOS os métodos públicos (incluindo __init__). OBS: Somente o nome do método sem trazer os parâmetros
    - Descrições curtas e objetivas

    ----------------------------

    ## Pontos Importantes da Arquitetura e Insights

    - Destaque decisões de design
    - Aponte padrões utilizados (ex: monkey patching, encapsulamento)
    - Traga insights úteis (não genéricos)
    - Fale se a classe usa outras classes. Somente caso ela use.

    ----------------------------

    # Descrição da Classe e Métodos

    ----------------------------

    ## Classe `NomeDaClasse`

    ### Descrição

    - Explicação clara do papel da classe

    ### Argumentos do Construtor

    Crie uma tabela:

    | Argumento | Tipo | Descrição | Valor Padrão |

    - Apenas se houver parâmetros

    ----------------------------

    ### Métodos

    Para cada método, siga exatamente este formato:

    ---

    ### N. `nome_metodo`

    ### Descrição

    Explicação clara e direta do que o método faz

    ### Argumentos

    - param (tipo): descrição
    - Se não houver → escrever "Nenhum."

    ### Retornos

    - tipo: descrição
    - Se não houver → escrever "Não retorna valor."

    ### Raises

    - Exception: descrição (apenas se fizer sentido ou se existirem)

    ### Exemplos

    ```python
    # exemplo realista de uso
    - se for possível traga exemplo do retorno, mas não invente, faça isso só se for possível deduzir.
    - Nunca coloque imports nos exemplos
    ```

    """

    description: str = """
    Agent responsible for generating complete and didactic technical documentation
    from Python classes that already contain docstrings.
    """