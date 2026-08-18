from b2_photo_manager.services.export_presets import (
    EXPORT_PRESETS,
    ExportFormat,
    ResizeMode,
    presets_by_name,
)


def test_required_presets_are_available() -> None:
    names = {preset.name for preset in EXPORT_PRESETS}

    assert {
        "Website",
        "Social Media",
        "E-Mail / klein",
        "Original",
        "Benutzerdefiniert",
    } <= names


def test_presets_have_supported_formats() -> None:
    assert {preset.output_format for preset in EXPORT_PRESETS} <= {
        ExportFormat.WEBP,
        ExportFormat.JPG,
    }


def test_presets_are_addressable_by_name() -> None:
    by_name = presets_by_name()

    assert by_name["Website"].target_size_kb == 500
    assert by_name["E-Mail / klein"].filename_prefix == "thumb"


def test_presets_normalize_to_new_size_model() -> None:
    by_name = presets_by_name()

    assert by_name["Website"].normalized().resize_mode == ResizeMode.BOUNDING_BOX
    assert by_name["Website"].normalized().max_width == 1800
    assert by_name["Website"].normalized().max_height == 1800
    assert by_name["Original"].normalized().resize_mode == ResizeMode.ORIGINAL
