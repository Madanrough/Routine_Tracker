from io import BytesIO

from PIL import Image

from src.celebrations import generate_achievement_card


def test_achievement_card_is_phone_friendly_png():
    data = generate_achievement_card(87)
    image = Image.open(BytesIO(data))
    assert image.format == "PNG"
    assert image.size == (1080, 1350)

