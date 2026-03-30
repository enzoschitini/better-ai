import json
from src.text_parse.content_parsing_agent import ContentParsingAgent

text = """
Olá!
Seguem dados requisitados da pesquisa.
Dados do demandante e pesquisador
Data de Início:  16/03/2026
Demandante:  GABRIELLA ALVIM DOS SANTOS
Comunidade:  GESTÃO DE PORTFÓLIO E
CONTRATAÇÃO DE CONTA E CARTÃO
Pesquisador(a):  Aline Alves Costa
Pesquisador(es) Parceiro(s):  Campo não preenchido
Supt:  PRG PF
Wallet:  Shared PF (1) - Onboarding
Dados da pesquisa
NA75038
Usabilidade da jorna...
GABRIELLA ALVIM
Código da Pesquisa:  NA75038
Nome da Pesquisa:  Usabilidade da jornada de Grade
de cartões
Metodologia: ​LAB - Quali Ep.Mod de usabilidade
comum
Métrica:  Não se aplica
Número de Respostas:  6
Objetivo:  Compreender como os clientes entendem e
interpretam as ofertas de troca de cartão (upgrade,
downgrade e equalgrade). Queremos entender através
da pesquisa como os clientes interagem
espontaneamente com a jornada de troca de cartão e
seus recursos (comparador de cartões e tela de
checkout informativa).
Descrição do Projeto:  A squad de Grade de Cartão
está trabalhando na evolução da jornada de Troca de
Cartão. Com a nova experiência, buscamos construir
um motor de ofertas mais inteligente, em que as opções
apresentadas estejam alinhadas às necessidades de
cada cliente. Além disso, as mudanças na jornada têm
como objetivo facilitar a comparação entre os cartões e
apoiar a tomada de decisão, um ponto que hoje na
experiência AS IS gera dificuldade. Por isso, queremos
realizar um teste de usabilidade com clientes para
captar o entendimento do conteúdo e navegação da
jornada, para garantir uma experiência simples, mas
encantadora. Vamos explorar duas versões com
carrossel e sem e queremos entender qual versão é
mais intuitiva para o cliente.
Hipóteses/Suposições:  - Verificar se o carrossel de
ofertas é intuitivo - O cliente entende que está fazendo
um upgrade, equalgrade ou downgrade? - Os clientes
compreendem as mudanças que serão feitas na troca
de cartões? - Qual versão é mais intuitiva? a troca de
opções pelos botões ou através do carrossel?
Perfil do Público:  Person
Segmento do Público:  PF - Pessoa Física
Público Alvo:  - Clientes PF Personnalité - Clientes
cartonistas/correntistas que tenham cartão de crédito -
Focado em alta renda (que teria a possibilidade de
todas as ofertas de troca) - acima de 15k
Dados do fornecedor
Fornecedor:  EcGlobal
Foi usado Listagem:  Não
Fornecedor de Recrutamento:  Campo não
preenchido
-- DOCUMENTO EMITIDO POR PROCESSAMENTO AUTOMÁTICO --
"""

input_data = {
    "text": text,
    "task": "Se o código da pesquisa for NA75038, adicione -EC ao final do código."
}

output_data = {
  "research_code": {
    "type": "str",
    "description": "Código identificador da pesquisa"
  },
  "research_name": {
    "type": "str",
    "description": "Nome da pesquisa"
  },
  "methodology": {
    "type": "str",
    "description": "Metodologia utilizada na pesquisa"
  },
  "metric": {
    "type": "str",
    "description": "Métrica principal da pesquisa (se aplicável)"
  },
  "responses_count": {
    "type": "int",
    "description": "Número total de respostas coletadas"
  },
  "objective": {
    "type": "str",
    "description": "Objetivo principal da pesquisa",
  },
  "project_description": {
    "type": "str",
    "description": "Descrição detalhada do problema ou contexto da pesquisa"
  }
}

config_data = {
    "model_provider": "OpenAI",
    "model_id": "gpt-4.1-mini",
    "debug_mode": True,
    "instructions": "Extraia dados do texto",
    "description": "Leia o texto e extraia as informações relevantes conforme o esquema definido. Retorne um JSON estruturado com os dados extraídos. Caso não encontre alguma informação, retorne null para aquele campo."
}

"""
    "model_provider": "Groq",
    "model_id": "llama-3.3-70b-versatile",
    "model_provider": "OpenAI",
    "model_id": "gpt-4.1-mini",

# criar venv (se ainda não tiver)
python -m venv venv

# ativar
venv\Scripts\activate

# instalar tudo
pip install -r requirements.txt

# rodar o projeto
python -m uvicorn app.main:app --reload

"""


if __name__ == "__main__":
    agent_parser = ContentParsingAgent(
        input_data=input_data,
        output_data=output_data,
        config_data=config_data
    )
    content_parsed = agent_parser.run_agent()
    response = agent_parser.format_response(content_parsed)


# python -m src.text_parse.TestContentParsingAgent