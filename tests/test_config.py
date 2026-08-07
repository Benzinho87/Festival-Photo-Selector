from b2_photo_manager.config import CONFIG


def test_config_version() -> None:
    assert CONFIG.version == "0.2.1.1"
