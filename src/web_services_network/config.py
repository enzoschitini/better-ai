
CONFIG = {
    "app_name": "BetterAI Web Service Network",
    "description": """
    API para interação com o agente de IA BetterAI 🤖
    Permite o envio de mensagens e manutenção de contexto de sessão entre interações.
    """,
    "version": "1.0.0",
    "origins": [
        "https://better-ai.up.railway.app",
        "https://better-ai-homol.up.railway.app",
        "https://better-ai-dev.up.railway.app",
        "http://127.0.0.1:8000",
    ],
    "allowed_methods": ["GET", "POST"],
    "allowed_headers": ["Authorization", "Content-Type"],

    "banner": """
    \033[97m
    ╔═════════════════════════════════════════════════════════════════════════╗

        ██████╗ ███████╗████████╗████████╗███████╗██████╗      █████╗ ██╗ ✦
        ██╔══██╗██╔════╝╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗    ██╔══██╗██║
        ██████╔╝█████╗     ██║      ██║   █████╗  ██████╔╝    ███████║██║
        ██╔══██╗██╔══╝     ██║      ██║   ██╔══╝  ██╔══██╗    ██╔══██║██║
        ██████╔╝███████╗   ██║      ██║   ███████╗██║  ██║    ██║  ██║██║
        ╚═════╝ ╚══════╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝

    ╚═════════════════════════════════════════════════════════════════════════╝

                        ✦  Where intelligence finds purpose. ✦
    \033[0m
    """

}