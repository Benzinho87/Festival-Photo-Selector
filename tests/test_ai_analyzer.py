from pathlib import Path

from PIL import Image, ImageDraw

from b2_photo_manager.services.ai.analyzer import PillowTechnicalAnalyzer


def test_people_score_varies_with_people_like_image_content(tmp_path: Path) -> None:
    plain = tmp_path / "plain.jpg"
    portrait_like = tmp_path / "portrait-like.jpg"

    Image.new("RGB", (160, 120), (40, 80, 160)).save(plain)
    image = Image.new("RGB", (160, 120), (35, 65, 120))
    draw = ImageDraw.Draw(image)
    draw.ellipse((55, 25, 105, 75), fill=(190, 125, 92))
    draw.rectangle((48, 72, 112, 112), fill=(160, 95, 72))
    image.save(portrait_like)

    analyzer = PillowTechnicalAnalyzer()
    plain_result = analyzer.analyze(plain)
    portrait_result = analyzer.analyze(portrait_like)

    assert plain_result.people.overall != portrait_result.people.overall
    assert portrait_result.people.overall > plain_result.people.overall
