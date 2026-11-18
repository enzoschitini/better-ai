from src.deep_agents.agent import agent, gateway
from src.deep_agents.model.metrics import RunReport
from src.deep_agents.utils.json_manager import extract_response_text, manage_result_json


def format_metrics(report: RunReport) -> str:
    """One compact line: always tokens in/out + time; extras only when relevant."""
    parts = [
        f"tokens in: {report.input_tokens}",
        f"out: {report.output_tokens}",
        f"tempo: {report.wall_time_s or 0:.1f}s",
    ]
    if report.n_calls > 1:
        parts.append(f"chamadas LLM: {report.n_calls}")
    if report.reasoning_tokens:
        parts.append(f"reasoning: {report.reasoning_tokens}")
    if report.cache_read_tokens:
        parts.append(f"cache: {report.cache_read_tokens}")
    if report.tool_runs:
        parts.append(f"ferramentas: {len(report.tool_runs)}")
    if report.cost_usd is not None:
        parts.append(f"custo: ${report.cost_usd:.4f}")
    if report.n_errors:
        parts.append(f"erros: {report.n_errors}")
    return "[" + " | ".join(parts) + "]"


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
            result, report = gateway.run_agent(agent, {"messages": messages})
        except Exception as e:
            messages.pop()  # drop the failed turn so the history stays consistent
            print(f"\n[erro] {e}\n")
            continue

        # The returned messages already contain the whole history + the new reply
        messages = result["messages"]
        manage_result_json(result)

        print(f"\nAgente: {extract_response_text(result)}")
        print(f"{format_metrics(report)}\n")


# python -m src.deep_agents.looping
if __name__ == "__main__":
    chat_loop()
