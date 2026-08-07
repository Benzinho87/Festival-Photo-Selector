from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout

from b2_photo_manager.models.photo import Photo


class TagDialog(QDialog):
    def __init__(self, photo: Photo, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Tags bearbeiten")

        self.input = QLineEdit(", ".join(sorted(photo.tags)))
        self.input.setPlaceholderText("z. B. Bühne, Publikum, DJ, Deko")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Tags durch Komma getrennt eingeben:"))
        layout.addWidget(self.input)
        layout.addWidget(buttons)

    def parsed_tags(self) -> set[str]:
        return {tag.strip() for tag in self.input.text().split(",") if tag.strip()}
