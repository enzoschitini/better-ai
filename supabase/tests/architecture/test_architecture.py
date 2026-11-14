"""Testes de arquitetura (T-004, T-109): fronteiras da constituição P1, P4, P5."""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parents[2] / "bai_supabase"
SDK_ROOTS = {"supabase", "postgrest", "storage3", "httpx", "supabase_auth", "supabase_functions", "realtime", "gotrue"}
STDLIB_OK = set(sys.stdlib_module_names)


def _py_files(sub: str = ""):
    base = PKG / sub if sub else PKG
    return [p for p in base.rglob("*.py")]


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.append(node.module)
    return out


def _rel(p: Path) -> str:
    return p.relative_to(PKG).as_posix()


def test_only_adapters_import_the_sdk():
    offenders = []
    for p in _py_files():
        if _rel(p).startswith("adapters/"):
            continue
        for mod in _imports(p):
            if mod.split(".")[0] in SDK_ROOTS:
                offenders.append(f"{_rel(p)} -> {mod}")
    assert not offenders, offenders


def test_never_imports_existing_project_code():
    offenders = []
    for p in list(_py_files()) + list(Path(__file__).resolve().parents[1].rglob("*.py")):
        for mod in _imports(p):
            if mod.split(".")[0] in {"src", "web_services", "web_app"}:
                offenders.append(f"{p.name} -> {mod}")
    assert not offenders, offenders


@pytest.mark.parametrize(
    "module,forbidden",
    [
        ("tables", {"bai_supabase.storage", "bai_supabase.facade", "bai_supabase.factories", "bai_supabase.adapters"}),
        ("storage", {"bai_supabase.tables", "bai_supabase.facade", "bai_supabase.factories", "bai_supabase.adapters"}),
        ("facade", {"bai_supabase.tables", "bai_supabase.storage", "bai_supabase.adapters", "bai_supabase.factories"}),
        ("contracts", {"bai_supabase.tables", "bai_supabase.storage", "bai_supabase.facade", "bai_supabase.adapters",
                       "bai_supabase.config", "bai_supabase.logging", "bai_supabase.resilience"}),
        ("errors", {"bai_supabase.tables", "bai_supabase.storage", "bai_supabase.facade", "bai_supabase.adapters",
                    "bai_supabase.config", "bai_supabase.logging", "bai_supabase.resilience", "bai_supabase.contracts"}),
    ],
)
def test_dependency_direction(module, forbidden):
    offenders = []
    for p in _py_files(module):
        for mod in _imports(p):
            if any(mod == f or mod.startswith(f + ".") for f in forbidden):
                offenders.append(f"{_rel(p)} -> {mod}")
    assert not offenders, offenders


def test_environment_is_read_only_in_the_source_module():
    offenders = []
    for p in _py_files():
        if _rel(p) == "config/sources.py":
            continue
        text = p.read_text(encoding="utf-8")
        mods = set(_imports(p))
        if "os.environ" in text or "getenv(" in text or {"dotenv"} & {m.split(".")[0] for m in mods}:
            offenders.append(_rel(p))
    assert not offenders, offenders


def test_no_global_settings_singleton():
    offenders = []
    for p in _py_files():
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id.lower() in {"settings", "config", "_settings", "_config"}:
                        offenders.append(f"{_rel(p)}:{t.id}")
    assert not offenders, offenders


def test_supabase_folder_does_not_shadow_the_sdk():
    """`import supabase` deve devolver o SDK, tanto da raiz do repo quanto de dentro de supabase/."""
    repo_root = Path(__file__).resolve().parents[3]
    for cwd in (repo_root, repo_root / "supabase"):
        out = subprocess.run(
            [sys.executable, "-c", "import supabase;print(supabase.__file__)"],
            cwd=cwd, capture_output=True, text=True, check=True,
        ).stdout.strip()
        assert "site-packages" in out.replace("\\", "/"), f"sombreado em {cwd}: {out}"
    assert not (repo_root / "supabase" / "__init__.py").exists()
