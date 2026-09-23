from streamlit.string_util import validate_icon_or_emoji


def test_all_navigation_icons_are_accepted_by_streamlit():
    icons = ("🏠", "✅", "🕘", "📈")
    for icon in icons:
        assert validate_icon_or_emoji(icon) == icon
