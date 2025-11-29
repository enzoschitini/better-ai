import logging

logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
)

logging.info("Funcionando!")
