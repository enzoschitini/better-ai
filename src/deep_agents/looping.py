from src.deep_agents.agent import agent
from src.deep_agents.utils.json_manager import extract_response_text, manage_result_json


def chat_loop() -> None:
    """Interactive terminal chat. Keeps the conversation history between turns.

    Commands: /exit (or /quit) to leave, /clear to reset the conversation.
    The full JSON of the latest turn is saved to agent_result.json.
    """
    print("Deep Agent chat — digite /exit para sair, /clear para limpar o histórico.\n")
    messages: list = []

    while True:
        try:
            user_input = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo!")
            break

        if not user_input:
            continue
        if user_input.lower() in {"/exit", "/quit", "exit", "quit"}:
            print("Até logo!")
            break
        if user_input.lower() == "/clear":
            messages = []
            print("Histórico limpo.\n")
            continue

        messages.append({"role": "user", "content": user_input})
        try:
            result = agent.invoke({"messages": messages})
        except Exception as e:
            messages.pop()  # drop the failed turn so the history stays consistent
            print(f"\n[erro] {e}\n")
            continue

        # The returned messages already contain the whole history + the new reply
        messages = result["messages"]
        manage_result_json(result)

        print(f"\nAgente: {extract_response_text(result)}\n")


# python -m src.deep_agents.looping
if __name__ == "__main__":
    chat_loop()
