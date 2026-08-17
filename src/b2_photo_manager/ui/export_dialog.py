from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.export_presets import (
    ExportFormat,
    ExportPreset,
    FilenameMode,
    ResizeMode,
    presets_by_name,
)
from b2_photo_manager.services.photo_exporter import export_photos, exportable_photos
from b2_photo_manager.services.photo_metadata import format_file_size


class ExportDialog(QDialog):
    def __init__(self, photos: list[Photo], parent=None) -> None:
        super().__init__(parent)
        self.photos = photos
        self.presets = presets_by_name()
        self.settings = QSettings("B2", "Photo Manager")
        self.setWindowTitle("Fotos exportieren")
        self.setMinimumWidth(520)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(self.presets.keys())
        self.preset_combo.currentTextChanged.connect(self._apply_preset)

        self.favorites_only_check = QCheckBox("Nur Favoriten aus der Auswahl exportieren")
        self.favorites_only_check.stateChanged.connect(self._update_count)

        self.format_combo = QComboBox()
        self.format_combo.addItems(
            [ExportFormat.WEBP.value.upper(), ExportFormat.JPG.value.upper()]
        )

        self.resize_combo = QComboBox()
        self.resize_combo.addItem("Maximale Bildkante", ResizeMode.LONG_EDGE.value)
        self.resize_combo.addItem("Maximaler Rahmen", ResizeMode.BOUNDING_BOX.value)

        self.long_edge_spin = self._spinbox(1, 12000, " px")
        self.max_width_spin = self._spinbox(1, 12000, " px")
        self.max_height_spin = self._spinbox(1, 12000, " px")
        self.quality_spin = self._spinbox(1, 100)
        self.keep_metadata_check = QCheckBox("Metadaten behalten")
        self.prefix_edit = QLineEdit()
        self.filename_mode_combo = QComboBox()
        self.filename_mode_combo.addItem("Prefix + Nummer", FilenameMode.PREFIX_NUMBER.value)
        self.filename_mode_combo.addItem(
            "Original-Dateiname + Nummer", FilenameMode.ORIGINAL_NUMBER.value
        )
        self.include_photographer_check = QCheckBox("Fotograf / Urheber in Dateinamen aufnehmen")
        self.start_number_spin = self._spinbox(0, 999999)
        self.padding_spin = self._spinbox(1, 8)
        self.target_size_spin = self._spinbox(0, 50000, " KB")
        self.target_size_spin.setSpecialValueText("Kein Ziel")

        self.destination_edit = QLineEdit(str(Path.cwd() / "exports"))
        choose_destination_button = QPushButton("Zielordner wählen")
        choose_destination_button.clicked.connect(self._choose_destination)

        self.count_label = QLabel()
        self.progress = QProgressBar()
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.export_button = QPushButton("Export starten")
        self.export_button.clicked.connect(self._run_export)
        close_button = QPushButton("Schließen")
        close_button.clicked.connect(self.reject)

        destination_row = QHBoxLayout()
        destination_row.addWidget(self.destination_edit, 1)
        destination_row.addWidget(choose_destination_button)

        form = QFormLayout()
        form.addRow("Preset", self.preset_combo)
        form.addRow("", self.favorites_only_check)
        form.addRow("Format", self.format_combo)
        form.addRow("Skalierung", self.resize_combo)
        form.addRow("Max. Bildkante", self.long_edge_spin)
        form.addRow("Max. Breite", self.max_width_spin)
        form.addRow("Max. Höhe", self.max_height_spin)
        form.addRow("Qualität", self.quality_spin)
        form.addRow("", self.keep_metadata_check)
        form.addRow("Dateiname", self.filename_mode_combo)
        form.addRow("Datei-Prefix", self.prefix_edit)
        form.addRow("", self.include_photographer_check)
        form.addRow("Startnummer", self.start_number_spin)
        form.addRow("Führende Nullen", self.padding_spin)
        form.addRow("Zielgröße pro Bild", self.target_size_spin)
        form.addRow("Zielordner", destination_row)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(close_button)
        buttons.addWidget(self.export_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.count_label)
        layout.addLayout(form)
        layout.addWidget(self.progress)
        layout.addLayout(buttons)

        self._apply_preset(self.preset_combo.currentText())
        self._load_last_settings()

    def _spinbox(self, minimum: int, maximum: int, suffix: str = "") -> QSpinBox:
        spinbox = QSpinBox()
        spinbox.setRange(minimum, maximum)
        spinbox.setSuffix(suffix)
        return spinbox

    def _apply_preset(self, preset_name: str) -> None:
        preset = self.presets[preset_name]
        self.format_combo.setCurrentText(preset.output_format.value.upper())
        self.resize_combo.setCurrentIndex(
            self.resize_combo.findData(preset.resize_mode.value)
        )
        self.long_edge_spin.setValue(preset.long_edge or 1)
        self.max_width_spin.setValue(preset.max_width or 1)
        self.max_height_spin.setValue(preset.max_height or 1)
        self.quality_spin.setValue(preset.quality)
        self.keep_metadata_check.setChecked(preset.keep_metadata)
        self.prefix_edit.setText(preset.filename_prefix)
        self.filename_mode_combo.setCurrentIndex(
            self.filename_mode_combo.findData(preset.filename_mode.value)
        )
        self.include_photographer_check.setChecked(preset.include_photographer)
        self.start_number_spin.setValue(preset.start_number)
        self.padding_spin.setValue(preset.number_padding)
        self.target_size_spin.setValue(preset.target_size_kb or 0)
        self._update_count()

    def _selected_photos(self) -> list[Photo]:
        return exportable_photos(
            self.photos, favorites_only=self.favorites_only_check.isChecked()
        )

    def _update_count(self) -> None:
        selected = len(self._selected_photos())
        self.count_label.setText(f"{selected} Fotos bereit für den Export")
        self.export_button.setEnabled(selected > 0)

    def _choose_destination(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self, "Zielordner wählen", self.destination_edit.text()
        )
        if selected:
            self.destination_edit.setText(selected)

    def _preset_from_form(self) -> ExportPreset:
        resize_mode = ResizeMode(self.resize_combo.currentData())
        return ExportPreset(
            key="custom_runtime",
            name="Benutzerdefiniert",
            output_format=ExportFormat(self.format_combo.currentText().lower()),
            resize_mode=resize_mode,
            long_edge=self.long_edge_spin.value()
            if resize_mode == ResizeMode.LONG_EDGE
            else None,
            max_width=self.max_width_spin.value()
            if resize_mode == ResizeMode.BOUNDING_BOX
            else None,
            max_height=self.max_height_spin.value()
            if resize_mode == ResizeMode.BOUNDING_BOX
            else None,
            quality=self.quality_spin.value(),
            keep_metadata=self.keep_metadata_check.isChecked(),
            filename_prefix=self.prefix_edit.text(),
            filename_mode=FilenameMode(self.filename_mode_combo.currentData()),
            start_number=self.start_number_spin.value(),
            number_padding=self.padding_spin.value(),
            include_photographer=self.include_photographer_check.isChecked(),
            target_size_kb=self.target_size_spin.value() or None,
        )

    def _load_last_settings(self) -> None:
        preset_name = self.settings.value("export/last_preset", "", str)
        if preset_name in self.presets:
            self.preset_combo.setCurrentText(preset_name)
        destination = self.settings.value("export/last_destination", "", str)
        if destination:
            self.destination_edit.setText(destination)

    def _save_last_settings(self) -> None:
        self.settings.setValue("export/last_preset", self.preset_combo.currentText())
        self.settings.setValue("export/last_destination", self.destination_edit.text())

    def _run_export(self) -> None:
        photos = self._selected_photos()
        if not photos:
            QMessageBox.information(
                self,
                "Keine Fotos",
                "Es sind keine Fotos für den Export ausgewählt.",
            )
            return

        destination = Path(self.destination_edit.text()).expanduser()
        self.export_button.setEnabled(False)
        self.progress.setRange(0, len(photos))
        self.progress.setValue(0)

        summary = export_photos(
            photos,
            destination,
            self._preset_from_form(),
            progress_callback=lambda done, total, _path: self.progress.setValue(done),
        )
        self._save_last_settings()
        self.progress.setValue(len(photos))
        self.export_button.setEnabled(True)

        message = QMessageBox(self)
        message.setIcon(QMessageBox.Icon.Information)
        message.setWindowTitle("Export abgeschlossen")
        message.setText(
            f"{summary.successful_count} Fotos exportiert\n"
            f"{summary.error_count} Fehler\n"
            f"Gesamtgröße: {format_file_size(summary.total_size)}\n"
            f"Zielordner: {summary.destination_folder}"
        )
        message.setDetailedText(self._summary_details(summary))
        message.exec()

    def _summary_details(self, summary) -> str:
        rows = []
        for result in summary.results:
            if result.success and result.destination is not None:
                rows.append(
                    f"OK: {result.source.name} -> {result.destination.name} "
                    f"({format_file_size(result.bytes_written)})"
                )
            else:
                rows.append(f"FEHLER: {result.source.name} -> {result.error}")
        return "\n".join(rows)
