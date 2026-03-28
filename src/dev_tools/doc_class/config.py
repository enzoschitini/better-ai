from dataclasses import dataclass, field

@dataclass
class AgentConfig:
    model_id: str = "gpt-4.1-mini"
    path: str = "src/dev_tools/doc_class"

@dataclass
class GenereteDocStringConfig:
    instructions: str = """

    Analise cuidadosamente a classe e seus metodos. Documente tudo com docstring seguindo o template:

    Para a classe:

    DESCRIÇÃO DA CLASSE (UM POUCO MAIS DE UMA FRASE)

    Args: 
    parm_example (str): Explica o que é em uma frase (Se tiver um Default coloqur Default é "blablabla"

    Methods:
            generate_post(topic): Explica o metodo em uma frase

    Para metodos de uma classe:

    DESCRIÇÃO DA FUNÇÂO DO METODO (UM POUCO MAIS DE UMA FRASE)

    Args: 
    parm_example (str): Explica o que é em uma frase (Se tiver um Default coloqur Default é "blablabla"

    Returns:
            str: O conteúdo formatado em Markdown pronto para publicação.

    Raises:
            ValueError: Se o 'theme' for uma string vazia ou apenas espaços.
            ConnectionError: Se o serviço externo de geração estiver offline.

    Examples:
            >>> tool = BaseAgentTools(parm_example="journalistic")
            >>> tool.generate_blog_post("Inteligência Artificial na Educação")
            '# O Impacto da IA...'

    """

    description: str = """

    """

@dataclass
class GenereteDocClassConfig:
    instructions: str = """

    Gere uma documentação didatica da classe.



    Comece com uma intrudução/visão geral

    Depois explique o fluxo de execução

    Monte uma tabela listando todos os metodos da classe e explicando brevemente cada um

    Mensione pontos importantes da arquitetura e insights

    E explique a classe e seus métodos seguindo o seguinte template:



    Classe XXXX



    Descrição



    Argomentos 



    Metodos



    1. Metodo 1

    Descrição 



    Argomentos



    Retornos 



    Raises



    Exemplos

    """

    description: str = """

    """