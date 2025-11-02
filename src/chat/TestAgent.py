from AgentAsk import AgentAsk
import json

#print("\n🤖 Chat ativo! (digite 'sair' para encerrar)\n")

# Cria uma sessão única para toda a conversa
session_id = None  
#session_id = "8a947fc2-f595-428b-876c-869edf1921a2"
#session_id = "1422232425262728229"

while True:
    user_input = input("Você: ")

    # Sai do loop se o usuário quiser encerrar
    if user_input.lower() in ["sair", "exit", "quit"]:
        print("👋 Encerrando o chat...")
        break

    try:
        # Passa o mesmo session_id para manter a memória
        business_id = "0010"  # Exemplo de business_id
        selected_tools = [
            "retorna_temperatura_atual",
            "busca_wikipedia",
            "data_analise",
            "AnswerGeneration",
            "fraciona_salario",
            "contador_de_historias"
        ]

        tool_dic = {
            "AnswerGenerationDic": {"filter_search": {"file_id": "file_id_01"}},
            "fraciona_salario_dic": {"dataframe": "clienti", "user_id": "C002", "value": 1}
        }

        resposta = AgentAsk(input_text=user_input, business_id=business_id,
                            metadata={"client_id": "1234"},
                            user_prompt="Você é um agente de IA",
                            temperature=0.5,
                            tool_kit=selected_tools, 
                            tool_dic=tool_dic, 
                            session_id=session_id,
                            streaming=False)

        # Atualiza o session_id (na primeira iteração ele é criado)
        session_id = resposta["session_id"]

        # Exibe a resposta formatada
        #print(f"Assistente: {resposta}\n")
        print(json.dumps(resposta, indent=4, ensure_ascii=False, default=str))

    except Exception as e:
        print(f"⚠️ TestAgent Erro: {e}\n")