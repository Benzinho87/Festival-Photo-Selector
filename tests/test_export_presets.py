from b2_photo_manager.services.export_presets import EXPORT_PRESETS, ExportFormat, presets_by_name


def test_required_presets_are_available() -> None:
    names = {preset.name for preset in EXPORT_PRESETS}

    assert {
        "Website",
        "Thumbnail",
        "Social Media",
        "Original verkleinert",
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
    assert by_name["Thumbnail"].filename_prefix == "thumb"
