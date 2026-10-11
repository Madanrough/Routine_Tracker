"""The fairy-night artwork is an opt-in History/Progress background."""

from pathlib import Path

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
