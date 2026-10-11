"""Catch page/helper mismatches before Streamlit loads a page in production."""

import ast
from pathlib import Path

import pytest
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("page", ("home", "today", "history", "progress"))
def test_page_src_imports_resolve(page):
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


def test_home_today_artwork_is_bundled():
    """Both redesigned pages need this asset before their UI can render."""
    artwork = ROOT / "assets" / "home-fairy-twilight.png"
    assert artwork.is_file()
    with Image.open(artwork) as image:
        assert image.format == "PNG"
