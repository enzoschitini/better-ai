import json
from src.utils.unique_id_factory import IDGenerator
import time

#print(IDGenerator.timestamp(prefix="log_"))

"""

"""

class ApplicationTracing:
    def __init__(self, 
                 log_id: str = None, 
                 flag: str = None, 
                 file_name: str = None,
                 save_logs: bool = False,
                 show_informations_messages: bool = False,
                 show_payloads: bool = False):

        self.log_id = log_id
        self.flag = flag
        self.file_name = file_name
        self.save_logs = save_logs
        self.show_informations_messages = show_informations_messages
        self.show_payloads = show_payloads
    
    def INFO(self, 
             func_name: str = None, 
             message: str = None,
             save_logs: bool = None,
             show_informations_messages: bool = None,
             show_payloads: bool = None):

        # fallback
        save_logs = self.save_logs if save_logs is None else save_logs
        show_informations_messages = (
            self.show_informations_messages 
            if show_informations_messages is None 
            else show_informations_messages
        )
        show_payloads = (
            self.show_payloads 
            if show_payloads is None 
            else show_payloads
        )

        print(
            f"{time.time()} | INFO | {func_name}() | {message} | {self.file_name} | {self.log_id}"
        )






logger = ApplicationTracing(log_id="log_1234", flag="Logging Test", file_name="tracing_core.py")
logger.INFO("create_user", "User created")



"""



    def DEBUG(self, 
             func_name:str = None, 
             message:str = None,
             save: bool = False):
        print(
            f"{time.time()} | INFO | {func_name}() | {message} | {self.file_name} | {self.log_id}"
        )

    def WARNING(self, 
             func_name:str = None, 
             message:str = None,
             save: bool = False):
        print(
            f"{time.time()} | INFO | {func_name}() | {message} | {self.file_name} | {self.log_id}"
        )

    def ERROR(self, 
             func_name:str = None, 
             message:str = None,
             save: bool = False):
        print(
            f"{time.time()} | INFO | {func_name}() | {message} | {self.file_name} | {self.log_id}"
        )

    def CRITICAL(self, 
             func_name:str = None, 
             message:str = None,
             save: bool = False):
        print(
            f"{time.time()} | INFO | {func_name}() | {message} | {self.file_name} | {self.log_id}"
        )
"""

# python -m src.tracing.tracing_core