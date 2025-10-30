import requests
import datetime

from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.agents import tool
from pydantic import BaseModel, Field #Importação atualizada

from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
import pandas as pd
from langchain_core.utils.function_calling import convert_to_openai_function

from retrieval import AnswerGenerationTool

import wikipedia
wikipedia.set_lang('pt')

import os
from dotenv import load_dotenv

load_dotenv()

def tool_format_output(name: str, response: str, parameters: dict = None):
    output = {
        "tool": name,
        "response": response
    }

    if parameters:
        for key, value in parameters.items():
            output[key] = value

    return output

def get_tools_config(selected_tools, fraciona_salario_dic, AnswerGenerationDic):
    class RetornTempArgs(BaseModel):
        latitude: float = Field(description='Latitude da localidade que buscamos a temperatura')
        longitude: float = Field(description='Longitude da localidade que buscamos a temperatura')


    @tool(args_schema=RetornTempArgs)
    def retorna_temperatura_atual(latitude: float, longitude: float):
        '''Retorna a temperatura atual para uma dada coordenada'''

        URL = 'https://api.open-meteo.com/v1/forecast'

        params = {
            'latitude': latitude,
            'longitude': longitude,
            'hourly': 'temperature_2m',
            'forecast_days': 1,
        }

        resposta = requests.get(URL, params=params)
        if resposta.status_code == 200:
            resultado = resposta.json()
            
            hora_agora = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
            lista_horas = [datetime.datetime.fromisoformat(temp_str) for temp_str in resultado['hourly']['time']]
            index_mais_prox = min(range(len(lista_horas)), key=lambda x: abs(lista_horas[x] - hora_agora))

            temp_atual = resultado['hourly']['temperature_2m'][index_mais_prox]
            return tool_format_output(retorna_temperatura_atual, f'{temp_atual}ºC')
        else:
            raise Exception(f'Request para API {URL} falhou: {resposta.status_code}')

    @tool
    def busca_wikipedia(query: str):
        """Faz busca no wikipedia e retorna resumos de páginas para a query"""
        titulos_paginas = wikipedia.search(query)
        resumos = []
        for titulo in titulos_paginas[:3]:
            try:
                wiki_page = wikipedia.page(title=titulo, auto_suggest=True)
                resumos.append(f'Título da página: {titulo}\nResumo: {wiki_page.summary}')
            except:
                pass
        if not resumos:
            return 'Busca não teve retorno'
        else:
            return tool_format_output(busca_wikipedia, '\n\n'.join(resumos))

    @tool
    def data_analise(query: str):
        """
        Executa análises de dados em um DataFrame do Titanic.
        
        Use esta ferramenta quando o usuário fizer perguntas sobre dados, estatísticas ou 
        quiser gerar código Python relacionado à análise de dados com pandas.

        Parâmetros:
        - query (str): A pergunta do usuário sobre o conjunto de dados (ex: "Qual a média de idade dos passageiros?").

        Retorna:
        - Uma resposta em texto com o resultado da análise, podendo incluir código, estatísticas ou explicações.
        """

        df = pd.read_csv(
            "https://raw.githubusercontent.com/pandas-dev/pandas/main/doc/data/titanic.csv"
        )

        chat = ChatOpenAI(model='gpt-3.5-turbo-0125')
        agent = create_pandas_dataframe_agent(
            chat,
            df,
            verbose=False,
            agent_type='tool-calling',
            allow_dangerous_code=True
        )

        response = agent.invoke({'input': query})
        return tool_format_output(data_analise, response["output"])

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

        string_response = AnswerGenerationTool(pergunta=pergunta, AnswerGenerationDic=AnswerGenerationDic)

        return tool_format_output("AnswerGeneration", string_response)

    @tool
    def fraciona_salario(divisao: int):
        """Executa operações matemáticas no salário"""

        df = pd.read_csv(f"LangChain Chat/ChatModel/{fraciona_salario_dic["dataframe"]}.csv")
        dic = df[df["ID"] == fraciona_salario_dic["user_id"]].to_dict()
        cliente = {col: val[fraciona_salario_dic["value"]] for col, val in dic.items()}

        return tool_format_output("fraciona_salario", float(cliente["Saldo"]) / float(divisao), {"user_id": id, "divisao": divisao})

    # === TOOL 2: Avalia o salário dividido ===
    @tool
    def avalia_salario(salario_dividido: float):
        """Compara o salário dividido com ranges e define uma nota."""

        if salario_dividido < 1000:
            nota = "D"
        elif salario_dividido < 3000:
            nota = "C"
        elif salario_dividido < 7000:
            nota = "B"
        else:
            nota = "A"

        return tool_format_output(
            "avalia_salario",
            nota,
            {"salario_dividido": salario_dividido, "faixas": "A≥7000, B≥3000, C≥1000, D<1000"}
        )

    # === TOOL 3: Define imposto justo ===
    @tool
    def define_imposto_justo(nota: str):
        """Define a taxa de imposto justa com base na nota do salário."""

        mapa_imposto = {
            "A": 0.27,  # 27%
            "B": 0.20,  # 20%
            "C": 0.12,  # 12%
            "D": 0.05   # 5%
        }

        taxa = mapa_imposto.get(nota.upper(), 0.0)

        return tool_format_output(
            "define_imposto_justo",
            f"{taxa * 100:.1f}%",
            {"nota": nota, "descricao": "Taxa proporcional ao poder aquisitivo"}
        )

    # Divida meu salario por 2 e defina o imposto dele

    @tool
    def contador_de_historias(tema: str) -> str:
        """
        Gera uma história curta baseada em um tema fornecido usando o modelo Groq.
        
        Parâmetros:
        -----------
        tema : str
            O tema ou tópico sobre o qual a história deve ser criada.

        Retorna:
        --------
        str
            A história gerada pelo modelo.
        """
        from langchain_groq import ChatGroq

        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("A chave da API do Groq não está definida. Defina GROQ_API_KEY no seu ambiente.")

        # Inicializa o chat com Groq
        chat = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.7,
            api_key=groq_api_key
        )

        # Mensagem enviada ao modelo
        prompt = f"Crie uma história curta sobre o seguinte tema: {tema}"

        try:
            response = chat.invoke([
                ("system", "Você é um contador de histórias criativo e divertido."),
                ("user", prompt)
            ])
            return tool_format_output(contador_de_historias, response.content, {"tema_entrada": tema})
        except Exception as e:
            return f"Erro ao gerar a história: {e}"

    # Usa locals() invece di globals(), perché le tool sono definite dentro questa funzione
    tools = [locals()[name] for name in selected_tools if name in locals()]

    #if not tools:
        #raise ValueError("❌ Nenhuma tool encontrada. Verifique os nomes em tool_names.")

    tools_json = [convert_to_openai_function(tool) for tool in tools]
    tool_run = {tool.name: tool for tool in tools}

    return tools, tools_json, tool_run