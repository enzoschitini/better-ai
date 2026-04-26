ABOUT = """
# BetterAI 🚀

## Multiple AI Models, One Unified Back-end IA

BetterAI is a platform designed to make artificial intelligence **practical, scalable, and accessible** for real-world applications.

Instead of building complex AI infrastructure from scratch, BetterAI provides a solid foundation that allows teams to integrate intelligent capabilities directly into their systems, workflows, and products.

From document analysis to advanced data exploration, BetterAI enables organizations to transform data into **actionable intelligence**.
"""

MENU_ITEMS = {
    #"Get Help": "https://seusite.com/help",
    #"Report a bug": "https://seusite.com/bug",
    "About": ABOUT
}

PAGES = {
    "Applications": {
        "Introduction": {
            "Home": "home",
            "Idle": "idle",
        },
        "Vector Store": {
            "Embedding File": "embeddingfile",
            "Update Metadata": "update_metadata",
            "Delete Vectors": "delete_vectors",
            "Retriver": "retriver",
        },
        "Image Generation": {
            "Da-Vinci": "image_generation",
        }
    },
    "Web Services": {
        "Health": {
            "API_APP": "api_app",
            "Tutoriais": "tutoriais",
        }
    }
}

# streamlit run webapp.py