import os
import shutil
from typing import List, Tuple


IGNORED_DIRS = {".git", ".venv", "venv", "env", "node_modules"}


def should_ignore_dir(dir_name: str) -> bool:
    """
    Decide se a pasta deve ser ignorada durante a varredura
    """
    return dir_name in IGNORED_DIRS


def remove_pycache_dirs(root: str, dirs: List[str]) -> int:
    """
    Remove diretórios __pycache__ dentro do nível atual
    Retorna a quantidade de pastas removidas
    """
    removed = 0

    for d in list(dirs):
        if d == "__pycache__":
            full_path = os.path.join(root, d)
            try:
                shutil.rmtree(full_path)
                print(f"[DIR REMOVED] {full_path}")
                removed += 1
                dirs.remove(d)  # evita descer em uma pasta que já foi removida
            except Exception as e:
                print(f"[ERROR] Failed to remove directory: {full_path} -> {e}")

    return removed


def remove_pyc_files(root: str, files: List[str]) -> int:
    """
    Remove arquivos .pyc no nível atual
    Retorna a quantidade de arquivos removidos
    """
    removed = 0

    for file in files:
        if file.endswith(".pyc"):
            full_path = os.path.join(root, file)
            try:
                os.remove(full_path)
                print(f"[FILE REMOVED] {full_path}")
                removed += 1
            except Exception as e:
                print(f"[ERROR] Failed to remove file: {full_path} -> {e}")

    return removed


def clean_python_cache(base_path: str) -> Tuple[int, int]:
    """
    Varre recursivamente o projeto removendo:
    - pastas __pycache__
    - arquivos .pyc

    Retorna:
    (quantidade_de_pastas_removidas, quantidade_de_arquivos_removidos)
    """
    removed_dirs = 0
    removed_files = 0

    for root, dirs, files in os.walk(base_path):
        # Remove pastas que não devem ser percorridas
        dirs[:] = [d for d in dirs if not should_ignore_dir(d)]

        removed_dirs += remove_pycache_dirs(root, dirs)
        removed_files += remove_pyc_files(root, files)

    return removed_dirs, removed_files


def main() -> None:
    """
    Ponto de entrada do script
    """
    project_root = os.getcwd()

    print("=" * 60)
    print(f"Python Cache Cleaner started at: {project_root}")
    print("=" * 60)

    removed_dirs, removed_files = clean_python_cache(project_root)

    print("\n" + "=" * 60)
    print("Cleanup completed successfully.")
    print(f"Total __pycache__ directories removed: {removed_dirs}")
    print(f"Total .pyc files removed: {removed_files}")
    print("=" * 60)


if __name__ == "__main__":
    main()
