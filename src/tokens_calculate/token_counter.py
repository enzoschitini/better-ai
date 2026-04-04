import tiktoken

class TokenCounter:
    """
    Classe para contar tokens em textos utilizando um codificador baseado em modelos da OpenAI.

    Args: 
    :param model (str): Define o nome do modelo para determinar a codificação de tokens, como "gpt-3.5-turbo".

    Methods:
            count(text): Conta o número de tokens no texto fornecido.
    """
    def __init__(self, model: str):
        try:
            self.encoder = tiktoken.encoding_for_model(model)
        except KeyError:
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def count(self, text: str) -> int:
        """
        Conta a quantidade de tokens presentes em um determinado texto utilizando o codificador do modelo.

        Args: 
        text (str): Texto que será convertido em tokens para contagem.

        Returns:
                int: Número total de tokens encontrados no texto.
        """
        return len(self.encoder.encode(text)) if text else 0
