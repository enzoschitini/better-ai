import json
import tiktoken
from datetime import datetime

def estimar_tokens_completos(
    system_prompt=None,
    chat_history=None,
    tools_json=None,
    tool_response=None,
    tool_tokens_used=0,
    model="gpt-4o-mini"
):
    """
    Retorna (total_tokens_est, detalhe_response) no formato:
    {
        "input": {
            "parts": {...},
            "combined": {...}
        },
        "output": {...},
        "total": {"caracters": ..., "tokens_estimated": ...}
    }
    """

    encoder = tiktoken.encoding_for_model(model)

    # --- Normaliza e monta os textos de cada parte ---
    system_str = system_prompt or ""

    if chat_history:
        try:
            history_parts = [getattr(m, "content", str(m)) for m in chat_history]
        except Exception:
            history_parts = [str(m) for m in chat_history]
        chat_history_str = "\n".join(history_parts)
        last_message = history_parts[-1]
    else:
        chat_history_str = ""
        last_message = ""

    tools_str = ""
    if tools_json is not None:
        try:
            tools_str = json.dumps(tools_json, ensure_ascii=False)
        except Exception:
            tools_str = str(tools_json)

    tool_response_str = tool_response or ""

    # ✅ Partições do input
    parts = {
        "system": system_str,
        "chat_history": chat_history_str,
        "tools": tools_str,
        "tool_response": tool_response_str
    }

    # --- Cálculo de caracteres e tokens por parte ---
    tokens_by_part = {}
    chars_by_part = {}
    for k, text in parts.items():
        chars_by_part[k] = len(text)
        tokens_by_part[k] = len(encoder.encode(text)) if text else 0

    # --- Texto completo do input ---
    full_input_text = "\n".join([p for p in parts.values() if p])
    input_tokens = len(encoder.encode(full_input_text)) if full_input_text else 0
    input_caracters = len(full_input_text)

    # --- Tokens totais incluindo extras ---
    total_tokens = input_tokens + (tool_tokens_used or 0)

    # --- Timestamp ---
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ✅ Estrutura final
    response = {
        "input": {
            "parts": {
                k: {
                    "caracters": chars_by_part[k],
                    "tokens_estimated": tokens_by_part[k]
                } for k in parts
            },
            "combined": {
                "caracters": input_caracters,
                "tokens_estimated": input_tokens
            }
        },
        "output": {
            "caracters": len(last_message),
            "tokens_estimated": len(encoder.encode(last_message)) if last_message else 0
        },
        "total": {
            "caracters": input_caracters + len(last_message),
            "tokens_estimated": total_tokens
        },
        "timestamp": timestamp
    }

    return response
