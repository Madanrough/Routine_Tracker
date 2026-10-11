from contextlib import nullcontext

from streamlit.string_util import validate_icon_or_emoji

from src import ui


def test_all_navigation_icons_are_accepted_by_streamlit():
    icons = ("🏠", "✅", "🕘", "📈")
    for icon in icons:
        assert validate_icon_or_emoji(icon) == icon


def test_home_icon_navigation_keeps_real_routes_and_accessible_labels(monkeypatch):
    calls = []

    class FakeStreamlit:
        def container(self, *, key):
            calls.append(("container", key))
            return nullcontext()

        def columns(self, count, *, gap):
            assert count == 4
            assert gap == "small"
            return [nullcontext() for _ in range(count)]

        def page_link(self, page, *, label, icon, help, width):
            calls.append((page, label, icon, help, width))

    monkeypatch.setattr(ui, "st", FakeStreamlit())

    ui.render_primary_navigation(icon_only=True)

    assert calls == [
        ("container", "primary_navigation_home"),
        ("pages/home.py", "Home", ":material/home:", "Home", "stretch"),
        ("pages/today.py", "Today", ":material/event_available:", "Today", "stretch"),
        ("pages/history.py", "History", ":material/history:", "History", "stretch"),
        ("pages/progress.py", "Progress", ":material/monitoring:", "Progress", "stretch"),
    ]
    for _, _, icon, _, _ in calls[1:]:
        assert validate_icon_or_emoji(icon) == icon

    calls.clear()
    ui.render_primary_navigation()
    assert calls[0] == ("container", "primary_navigation")
    assert [item[0] for item in calls[1:]] == [
        "pages/home.py", "pages/today.py", "pages/history.py", "pages/progress.py"
    ]
