# =========================================
# IMPORTS
# =========================================
import time
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

from tools.tools import get_tools_config
from buffer_memory import save_chat_history
import warnings

from InitializeAgent import initialize_agent

# Ignora todos os warnings
warnings.filterwarnings("ignore")

# Ou apenas warnings específicos de UserWarning
warnings.filterwarnings("ignore", category=UserWarning)

load_dotenv()

# =========================================
# EXECUÇÃO DO AGENTE (STREAMING + TOOLS + MEMÓRIA)
# =========================================
def AgentAsk(input_text: str, session_id: str = None, streaming: bool = False):
    """Executa o chat com memória, tools e streaming opcional, tratando erros."""
    try:
        start = time.time()
        # Tool a serem usadas
        selected_tools = [
            "retorna_temperatura_atual"
            "busca_wikipedia",
            "data_analise",
            "AnswerGeneration",
            "fraciona_salario",
            "contador_de_historias"
        ]
        
        # Exemplos de parâmetros para as tools
        AnswerGenerationDic = {"filter_search": {"file_id": "file_id_01"}}
        fraciona_salario_dic = {"dataframe": "clienti", "user_id": "C002", "value": 1}

        tools, tools_json, tool_run = get_tools_config(selected_tools, fraciona_salario_dic, AnswerGenerationDic)
        # Vogliamo poter scegliere le funzioni da usare

        agent_executor, memory, session_id, handler = initialize_agent(
            session_id, tools, tools_json, tool_run, streaming=streaming
        )

        config = RunnableConfig(
            tags=["pipeline-curiosidade-historia"],
            metadata={
                "autor": "Enzo Schitini",
                "versao_pipeline": "2.0-mongo",
                "projeto": "Scituffy",
                "tipo_execucao": "produção"
            }
        )

        # Invoca o agente
        response = agent_executor.invoke({'input': input_text}, config)
        exec_time = round(time.time() - start, 2)
        print("\n")  # quebra de linha para o output

        # Salva histórico da sessão
        save_chat_history(session_id, memory)

        # Recupera texto completo (streaming ou não)
        final_text = handler.get_response() if streaming else response.get("output", "")

        

        # Caso tenha usado alguma tool
        if response.get("intermediate_steps"):
            tool_name = response["intermediate_steps"][0][0].tool
            tool_output = response["intermediate_steps"][0][1]

            return {
                "response": final_text,
                "tool": tool_name,
                "tool_output": tool_output,
                "session_id": session_id,
                "status": "success",
                "time": exec_time
            }

        # Caso não tenha usado nenhuma tool
        else:
            return {
                "response": final_text,
                "session_id": session_id,
                "status": "success",
                "time": exec_time
            }

    except Exception as e:
        # Retorna JSON de erro padronizado
        return {
            "message": "Desculpa! Não foi possivel responder a pergunta. Por favor tente novamente.",
            "session_id": session_id,
            "erro": e,
            "status": "error"
        }