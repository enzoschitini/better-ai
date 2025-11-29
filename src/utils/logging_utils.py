import logging

def setup_logging(log_file: str = "loggings/app.log"):
    """
    Inicializa o sistema de logs da aplicação.
    Evita duplicação de handlers mesmo que chamada várias vezes.
    """

    # Remove handlers existentes (evita logs duplicados)
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(filename)s - line: %(lineno)d - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
