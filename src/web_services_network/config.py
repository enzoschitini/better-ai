CONFIG = {
    "banner": """
    \033[1;36m╔═══════════════════════════════════════════════════════════════════════╗

        ██████╗ ███████╗████████╗████████╗███████╗██████╗      █████╗ ██╗ ✦
        ██╔══██╗██╔════╝╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗    ██╔══██╗██║
        ██████╔╝█████╗     ██║      ██║   █████╗  ██████╔╝    ███████║██║
        ██╔══██╗██╔══╝     ██║      ██║   ██╔══╝  ██╔══██╗    ██╔══██║██║
        ██████╔╝███████╗   ██║      ██║   ███████╗██║  ██║    ██║  ██║██║
        ╚═════╝ ╚══════╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝

    ╚═══════════════════════════════════════════════════════════════════════╝\033[0m

                        \033[1;32m✦ Where intelligence finds purpose. ✦\033[0m
    """,

    "app_name": "BetterAI Web Service Network",
    
    "description": """
    API para interação com o agente de IA BetterAI 🤖
    Permite o envio de mensagens e manutenção de contexto de sessão entre interações.
    https://github.com/enzoschitini/better-ai
    """,

    "version": "1.0.0",

    "origins": [
        "https://better-ai.up.railway.app",
        "https://better-ai-homol.up.railway.app",
        "https://better-ai-dev.up.railway.app",
        "http://localhost:8000",
    ],

    "allowed_methods": ["GET", "POST"],
    "allowed_headers": ["Authorization", "Content-Type"],
}