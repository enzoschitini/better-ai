import os
import shutil

def limpar_pycache(diretorio_raiz="."):
    """Remove todas as pastas __pycache__ do projeto."""
    total_removidas = 0
    for raiz, dirs, _ in os.walk(diretorio_raiz):
        for d in dirs:
            if d == "__pycache__":
                caminho = os.path.join(raiz, d)
                try:
                    shutil.rmtree(caminho)
                    #print(f"🗑️  Removido: {caminho}")
                    total_removidas += 1
                except Exception as e:
                    #print(f"⚠️ Clean  Erro ao remover {caminho}: {e}")
                    pass
    if total_removidas == 0:
        #print("✅ Nenhuma pasta __pycache__ encontrada.")
        pass
    else:
        #print(f"✨ Limpeza concluída! {total_removidas} pastas __pycache__ removidas.")
        pass

if __name__ == "__main__":
    limpar_pycache()
