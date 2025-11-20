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
        Gera respostas baseadas em uma base de conhecimento específica.

        Use esta ferramenta quando o usuário fizer perguntas relacionadas a informações
        que estão armazenadas na base de conhecimento da aplicação, como documentos técnicos,
        guias internos, políticas, padrões ou qualquer conteúdo indexado no VectorStore.

        Parâmetros:
        - pergunta (str): Pergunta do usuário sobre o tema desejado.

        Funcionamento:
        1. A ferramenta busca no VectorStore os documentos mais relevantes usando busca semântica.
        2. Concatena o contexto desses documentos.
        3. Gera uma resposta contextualizada com base nesse conteúdo.

        Retorna:
        - Uma string contendo a resposta final gerada pela LLM, com base no contexto recuperado.
        """

        string_response = AnswerGenerationTool(pergunta=pergunta, AnswerGenerationDic=tool_dic["AnswerGenerationDic"])

        return tool_format_output("AnswerGeneration", string_response)

    # Usa locals() invece di globals(), perché le tool sono definite dentro questa funzione
    tools = [locals()[name] for name in selected_tools if name in locals()]

    tools_json = [convert_to_openai_function(tool) for tool in tools]
    logging.info("Tools configuradas")
    tool_run = {tool.name: tool for tool in tools}

    return tools, tools_json, tool_run