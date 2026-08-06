from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from src.export.image_exporter import extension_for, export_image
from src.export.presets import PRESETS
from src.models.photo import Photo


class ExportDialog(QDialog):
    def __init__(self, photos: list[Photo], parent=None):
        super().__init__(parent)
        self.photos = [photo for photo in photos if photo.selected]

        self.setWindowTitle("Ausgewählte Fotos exportieren")
        self.resize(560, 430)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(PRESETS.keys())
        self.preset_combo.currentTextChanged.connect(self.update_preset_summary)

        self.prefix_edit = QLineEdit("electric-residence-2026")

        self.start_number_spin = QSpinBox()
        self.start_number_spin.setRange(0, 9999)
        self.start_number_spin.setValue(1)

        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)

        choose_output_button = QPushButton("Ordner wählen")
        choose_output_button.clicked.connect(self.choose_output)

        output_row = QHBoxLayout()
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(choose_output_button)

        form = QFormLayout()
        form.addRow("Preset:", self.preset_combo)
        form.addRow("Dateipräfix:", self.prefix_edit)
        form.addRow("Startnummer:", self.start_number_spin)
        form.addRow("Ausgabeordner:", output_row)

        self.preset_summary = QLabel()
        self.preset_summary.setWordWrap(True)
        self.preset_summary.setTextInteractionFlags(
            self.preset_summary.textInteractionFlags()
            | self.preset_summary.textInteractionFlags().TextSelectableByMouse
        )

        summary_box = QGroupBox("Preset-Übersicht")
        summary_layout = QVBoxLayout(summary_box)
        summary_layout.addWidget(self.preset_summary)

        cancel_button = QPushButton("Abbrechen")
        cancel_button.clicked.connect(self.reject)

        export_button = QPushButton("Export starten")
        export_button.clicked.connect(self.run_export)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(cancel_button)
        buttons.addWidget(export_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(summary_box)
        layout.addStretch()
        layout.addLayout(buttons)

        self.update_preset_summary()

    def choose_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Ausgabeordner auswählen",
            str(Path.home() / "Pictures"),
        )
        if folder:
            self.output_edit.setText(folder)

    def update_preset_summary(self) -> None:
        preset = PRESETS[self.preset_combo.currentText()]

        if preset.crop and preset.width and preset.height:
            dimensions = f"{preset.width} × {preset.height} px"
            resize_mode = "Fester Zuschnitt"
        else:
            dimensions = f"Längste Kante: {preset.max_edge} px"
            resize_mode = "Seitenverhältnis bleibt erhalten"

        extension = extension_for(preset)
        example_number = self.start_number_spin.value()
        example_name = (
            f"{self.prefix_edit.text().strip() or 'festival'}"
            f"{preset.filename_suffix}-{example_number:03d}{extension}"
        )

        self.preset_summary.setText(
            f"<b>Format:</b> {preset.format}<br>"
            f"<b>Auflösung:</b> {dimensions}<br>"
            f"<b>Skalierung:</b> {resize_mode}<br>"
            f"<b>Maximale Dateigröße:</b> {preset.max_file_size_kb} KB je Bild<br>"
            f"<b>Qualitätsbereich:</b> {preset.start_quality} bis "
            f"{preset.min_quality}<br>"
            f"<b>Ausgewählte Fotos:</b> {len(self.photos)}<br>"
            f"<b>Beispieldatei:</b> {example_name}"
        )

    def run_export(self) -> None:
        output_text = self.output_edit.text().strip()
        prefix = self.prefix_edit.text().strip()

        if not output_text:
            QMessageBox.warning(
                self,
                "Ausgabeordner fehlt",
                "Bitte wähle einen Ausgabeordner.",
            )
            return

        if not prefix:
            QMessageBox.warning(
                self,
                "Dateipräfix fehlt",
                "Bitte gib ein Dateipräfix ein.",
            )
            return

        preset = PRESETS[self.preset_combo.currentText()]
        output_dir = Path(output_text)
        start_number = self.start_number_spin.value()

        progress = QProgressDialog(
            "Fotos werden exportiert …",
            "Abbrechen",
            0,
            len(self.photos),
            self,
        )
        progress.setWindowTitle("Export")
        progress.setMinimumDuration(0)

        exported = 0
        failed: list[str] = []

        for offset, photo in enumerate(self.photos):
            progress.setValue(offset)
            if progress.wasCanceled():
                break

            number = start_number + offset
            filename = (
                f"{prefix}{preset.filename_suffix}-{number:03d}"
                f"{extension_for(preset)}"
            )

            try:
                export_image(photo.path, output_dir / filename, preset)
                exported += 1
            except Exception as exc:
                failed.append(f"{photo.path.name}: {exc}")

        progress.setValue(len(self.photos))

        message = f"{exported} Fotos wurden exportiert."
        if failed:
            message += f"\n\n{len(failed)} Dateien konnten nicht exportiert werden."

        QMessageBox.information(self, "Export abgeschlossen", message)
        if exported:
            self.accept()
