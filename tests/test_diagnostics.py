from b2_photo_manager import __version__
from b2_photo_manager.ui.diagnostics_dialog import diagnostics_text


def test_diagnostics_text_contains_runtime_basics() -> None:
    text = diagnostics_text()

    assert __version__ in text
    assert "Python:" in text
    assert "PySide6:" in text
    assert "App-Daten:" in text
    assert "Cache:" in text
    assert "Logs:" in text
