import json
import tiktoken
from datetime import datetime
import logging
from src.chat.utils.logging_utils import setup_logging

setup_logging()

def estimar_tokens_completos(
    system_prompt=None,
    chat_history=None,
    tools_json=None,
    tool_response=None,
    tool_tokens_used=0,
    model="gpt-4o-mini"
):
    """
    Retorna (total_tokens_est, detalhe_response)
    """

    logging.info(
        f"Iniciando estimativa de tokens | model={model}, "
        f"tool_tokens_used={tool_tokens_used}"
    )

    try:
        encoder = tiktoken.encoding_for_model(model)
        logging.info(f"Encoder carregado para modelo {model}")
    except Exception:
        logging.exception("Falha ao carregar encode do modelo.")
        raise

    try:
        # --- Normaliza e monta os textos de cada parte ---
        system_str = system_prompt or ""
        logging.debug(f"system_prompt tamanho={len(system_str)}")

        # Histórico de chat
        if chat_history:
            try:
                history_parts = [getattr(m, "content", str(m)) for m in chat_history]
                logging.info("chat_history processado a partir de objetos.")
            except Exception:
                history_parts = [str(m) for m in chat_history]
                logging.warning("chat_history convertido para string por fallback.")

            chat_history_str = "\n".join(history_parts)
            last_message = history_parts[-1]
        else:
            chat_history_str = ""
            last_message = ""

        # Ferramentas declaradas
        tools_str = ""
        if tools_json is not None:
            try:
                tools_str = json.dumps(tools_json, ensure_ascii=False)
            except Exception:
                tools_str = str(tools_json)
                logging.warning("tools_json convertido para texto por fallback.")

        # Resposta de ferramenta
        tool_response_str = tool_response or ""

        # Partições
        parts = {
            "system": system_str,
            "chat_history": chat_history_str,
            "tools": tools_str,
            "tool_response": tool_response_str
        }

        logging.info(f"Partes identificadas para cálculo: {list(parts.keys())}")

        # --- Cálculo de caracteres e tokens por parte ---
        tokens_by_part = {}
        chars_by_part = {}

        for k, text in parts.items():
            chars_by_part[k] = len(text)
            tokens_by_part[k] = len(encoder.encode(text)) if text else 0

            logging.debug(
                f"Parte={k} | chars={chars_by_part[k]} | tokens={tokens_by_part[k]}"
            )

        # --- Texto total do input ---
        full_input_text = "\n".join([p for p in parts.values() if p])
        input_tokens = len(encoder.encode(full_input_text)) if full_input_text else 0
        input_caracters = len(full_input_text)

        logging.info(
            f"Tokens totais de input (sem tool extra): {input_tokens} "
            f"| caracteres={input_caracters}"
        )

        # --- Soma final incluindo tool extra ---
        total_tokens = input_tokens + (tool_tokens_used or 0)

        # --- Última mensagem (output estimado) ---
        output_chars = len(last_message)
        output_tokens = len(encoder.encode(last_message)) if last_message else 0

        logging.info(
            f"Output estimado | chars={output_chars} | tokens={output_tokens}"
        )

        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # --- Estrutura final ---
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
                "caracters": output_chars,
                "tokens_estimated": output_tokens
            },
            "total": {
                "caracters": input_caracters + output_chars,
                "tokens_estimated": total_tokens
            }
            # "timestamp": timestamp
        }

        logging.info(
            f"Estimativa concluída | total_tokens={total_tokens} | timestamp={timestamp}"
        )

        return response

    except Exception:
        logging.exception("Erro inesperado durante a estimativa de tokens.")
        raise
