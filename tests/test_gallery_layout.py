from b2_photo_manager.services.gallery_layout import calculate_columns


def test_calculate_columns_uses_available_width() -> None:
    assert calculate_columns(1200, 264, 14) == 4


def test_calculate_columns_never_drops_below_minimum() -> None:
    assert calculate_columns(100, 264, 14) == 1
