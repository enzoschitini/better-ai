# tracing_core.py

import logging
import json
from typing import Dict, Any


# =========================
# LOGGER CONFIGURATION
# =========================
def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # evita duplicação de handlers

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # Handler arquivo
    file_handler = logging.FileHandler("app.log")
    file_handler.setFormatter(formatter)

    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger("TracingCore")


# =========================
# CORE FUNCTION
# =========================
def process_user_data(user: Dict[str, Any]) -> float | None:
    logger.info("Start processing user", extra={"user": user})

    try:
        logger.debug(f"Payload received: {json.dumps(user)}")
        logger.warning("d")

        if "age" not in user:
            logger.warning("Missing age field", extra={"user": user})

        result = user["income"] / user["age"]

        logger.info("Processing finished successfully", extra={"result": result})
        return result

    except KeyError as e:
        logger.error(
            "Missing required field",
            extra={"error": str(e), "user": user},
            exc_info=True
        )

    except Exception as e:
        logger.critical(
            "Unexpected error",
            extra={"error": str(e), "user": user},
            exc_info=True
        )

    return None


# =========================
# ENTRYPOINT
# =========================
def main():
    users = [
        {"name": "Enzo", "age": 25, "income": 5000},
        {"name": "Maria", "age": 10, "income": 3000},
        {"name": "João", "age": 10, "income": 4000},
    ]

    for user in users:
        process_user_data(user)


if __name__ == "__main__":
    main()