"""Catch page/helper mismatches before Streamlit loads a page in production."""

import ast
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("page", ("history", "progress"))
def test_redesigned_page_src_imports_resolve(page):
    """Execute the exact src.* import statements used by each page."""
    path = ROOT / "pages" / f"{page}.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or not (node.module or "").startswith("src."):
            continue
        statement = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
        try:
            exec(compile(statement, str(path), "exec"), {})
        except ImportError as exc:
            pytest.fail(f"{path.name} cannot import from {node.module}: {exc}")
