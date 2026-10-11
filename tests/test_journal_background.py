"""The fairy-night artwork is an opt-in History/Progress background."""

import base64
from io import BytesIO
from pathlib import Path
import re

from PIL import Image

from src import ui


def test_journal_background_is_lightweight_and_page_scoped(monkeypatch):
    markup = []
    monkeypatch.setattr(ui.st, "html", markup.append)

    ui.apply_journal_background()

    assert len(markup) == 1
    assert ".stApp:has(.erumaa-journal-background-marker)" in markup[0]
    assert "background-size: cover" in markup[0]
    assert "background-position: right top" in markup[0]
    assert "data:image/webp;base64," in markup[0]
    assert len(markup[0]) < 250_000
    assert (Path(__file__).resolve().parents[1] / "assets" / "fairy-night-history-progress.png").is_file()


def test_journal_background_webp_is_valid_from_another_working_directory(monkeypatch, tmp_path):
    """The asset path is rooted at src/ui.py, not Streamlit Cloud's cwd."""
    monkeypatch.chdir(tmp_path)
    ui._journal_background_uri.cache_clear()
    encoded = ui._journal_background_uri()
    match = re.fullmatch(r"data:image/webp;base64,([A-Za-z0-9+/=]+)", encoded)
    assert match is not None
    with Image.open(BytesIO(base64.b64decode(match.group(1)))) as image:
        assert image.format == "WEBP"
        assert image.width <= 1200
        assert image.height <= 800
