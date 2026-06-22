import json

from src.utils.unique_id_factory import IDGenerator

from src.agents.trend_radar.agent import BaseAgent
from src.agents.agent_executor import AgentExecutor

if __name__ == "__main__":
    # CLI
    runner = AgentExecutor.from_agent_class(
        agent_class=BaseAgent,
        params={
            "citys": ["Salvador", "São Paulo", "Rio de Janeiro"]
        },
        # session_id e user_id são opcionais — omita para usar os defaults
        # session_id=IDGenerator().uuid(),
        # user_id="user_01",
    )

    for chunk in runner.run_stream(ask="Traga 2 trends"):
        parsed = runner.parse(chunk)
        event_name = parsed.get("event")
        content = parsed.get("content", "")
        tool_name = parsed.get("tool_name")
        tool_payload = None

        if isinstance(chunk, dict):
            tool_payload = chunk.get("payload")

        if tool_payload is None:
            raw_chunk = parsed.get("raw")
            if isinstance(raw_chunk, dict):
                tool_payload = raw_chunk.get("payload")

        if event_name and event_name != "RunContent":
            suffix = f" [{tool_name}]" if tool_name else ""
            print(f"\n[{event_name}]{suffix}")

        if content:
            print(content, end="", flush=True)
        
        if event_name and event_name == "ToolCallCompleted":
            print("\n[ToolPayload]")
            print(json.dumps(tool_payload or {}, ensure_ascii=False, indent=2))

    print()

    # JSON (alternativo)
    # runner.run_json()

    # AgentOS
    #runner.run_agent_os(id="trend_radar", name="Trend Radar")

# python -m src.agents.trend_radar.run