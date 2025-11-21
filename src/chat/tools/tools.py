import logging

from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.agents import tool

from src.chat.tools.retrieval import AnswerGenerationTool

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(filename)s - line: %(lineno)d - %(levelname)s - %(message)s'
)

def tool_format_output(name: str, response: str, parameters: dict = None):
    output = {
        "tool": name,
        "response": response
    }

    if parameters:
        for key, value in parameters.items():
            output[key] = value

    return output

def get_tools_config(selected_tools, tool_dic):
    logging.info("Configurando as tools")

    @tool
    def AnswerGeneration(pergunta: str):
        """
        Gera respostas baseadas na base de conhecimento interna da aplicação.

        Quando usar esta ferramenta:
        - Use sempre que o usuário fizer perguntas relacionadas a informações que
        possam estar na base de conhecimento (documentos técnicos, guias internos,
        políticas, padrões, materiais de treinamento, etc.).
        - Use também quando o agente não tiver uma resposta direta ou suficiente
        com base apenas no próprio conhecimento. 
        Ou seja: se a LLM não souber a resposta, deverá recorrer a esta tool
        para buscar no VectorStore.

        Funcionamento:
        1. A ferramenta realiza uma busca semântica no VectorStore pelos documentos
        mais relevantes à pergunta.
        2. Concatena o contexto recuperado.
        3. Gera uma resposta contextualizada com base no conteúdo encontrado.

        Parâmetros:
        - pergunta (str): Pergunta enviada pelo usuário.

        Retorna:
        - Uma string contendo a resposta final gerada pela LLM com base no contexto
        recuperado. Caso não haja informações suficientes na base, a resposta deve
        indicar isso claramente.
        """

        string_response = AnswerGenerationTool(pergunta=pergunta, AnswerGenerationDic=tool_dic["AnswerGenerationDic"])

        return tool_format_output("AnswerGeneration", string_response)

    # Usa locals() invece di globals(), perché le tool sono definite dentro questa funzione
    tools = [locals()[name] for name in selected_tools if name in locals()]

    tools_json = [convert_to_openai_function(tool) for tool in tools]
    logging.info("Tools configuradas")
    tool_run = {tool.name: tool for tool in tools}

    return tools, tools_json, tool_run