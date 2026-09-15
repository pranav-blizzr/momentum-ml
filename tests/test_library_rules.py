"""Enforces the library rules (README "Project rules" 4–7) automatically.

Scans every .py file under src/momentum_ml/ and fails if it imports a banned module
or calls a banned function. Runs with the rest of the tests: `pytest`.
"""
import ast
from pathlib import Path

import pytest

LIB = Path(__file__).resolve().parents[1] / "src" / "momentum_ml"

BANNED_MODULES = {
    # brokers and market data
    "ib_insync", "ib_async", "ibapi", "massive", "polygon", "databento", "benzinga",
    # network, database, files, environment
    "requests", "httpx", "urllib", "socket", "websocket", "websockets", "sqlite3",
    "dotenv", "shutil", "tempfile", "glob", "pickle",
    # concurrency and asynchronous code
    "asyncio", "threading", "multiprocessing", "concurrent",
    # research-only packages (runtime must be numpy + lightgbm)
    "pandas", "polars", "pyarrow", "sklearn", "optuna", "mlflow", "shap", "matplotlib",
}

BANNED_CALLS = {
    ("time", "time"), ("time", "time_ns"), ("time", "sleep"),
    ("datetime", "now"), ("datetime", "utcnow"), ("date", "today"),
    ("os", "getenv"), ("os", "environ"), ("random", "random"),
}
BANNED_BUILTINS = {"open", "input", "print"}

FILES = sorted(LIB.rglob("*.py")) if LIB.exists() else []


def _dotted(node: ast.AST) -> str:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in BANNED_MODULES:
                    found.append(f"line {node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] in BANNED_MODULES:
                found.append(f"line {node.lineno}: from {node.module} import ...")
            for alias in node.names:
                if (node.module, alias.name) in BANNED_CALLS:
                    found.append(f"line {node.lineno}: from {node.module} import {alias.name}")
        elif isinstance(node, ast.Attribute):
            dotted = _dotted(node)
            if any(dotted == f"{a}.{b}" or dotted.endswith(f".{a}.{b}") for a, b in BANNED_CALLS):
                found.append(f"line {node.lineno}: {dotted}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in BANNED_BUILTINS:
                found.append(f"line {node.lineno}: {node.func.id}()")
    return found


def test_library_folder_exists():
    assert LIB.exists(), f"expected library at {LIB}"


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(LIB)))
def test_library_file_follows_rules(path):
    problems = _violations(path)
    assert not problems, f"{path.relative_to(LIB)} breaks the library rules:\n  " + "\n  ".join(problems)
