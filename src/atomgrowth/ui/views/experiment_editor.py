"""Experiment editor view for viewing and editing experiment details"""

from pathlib import Path
from typing import Optional, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QScrollArea, QFrame, QFileDialog,
    QMessageBox, QDoubleSpinBox, QSpinBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from atomgrowth.core.experiment_manager import ExperimentManager
from atomgrowth.core.template_manager import TemplateManager
from atomgrowth.models.experiment import Experiment
from atomgrowth.signals.app_signals import get_app_signals
from atomgrowth.styles.colors import NotionColors
from atomgrowth.ui.widgets.image_drop_zone import ImageDropZone
from atomgrowth.ui.dialogs.image_preview_dialog import ImagePreviewDialog


class ParameterField(QWidget):
    """A single parameter field with inherited value display and override capability."""

    value_changed = Signal(str, object)  # field_path, new_value

    def __init__(
        self,
        label: str,
        field_path: str,
        field_type: str = "float",  # float, int, str
        unit: str = "",
        min_val: float = 0,
        max_val: float = 10000,
        decimals: int = 1,
        parent=None
    ):
        super().__init__(parent)
        self.field_path = field_path
        self.field_type = field_type
        self._inherited_value: Any = None
        self._is_overridden = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Label
        self.label = QLabel(label)
        self.label.setFixedWidth(120)
        self.label.setStyleSheet(f"font-size: 13px; color: {NotionColors.TEXT_SECONDARY};")
        layout.addWidget(self.label)

        # Input field
        if field_type == "float":
            self.input = QDoubleSpinBox()
            self.input.setRange(min_val, max_val)
            self.input.setDecimals(decimals)
            self.input.valueChanged.connect(self._on_value_changed)
        elif field_type == "int":
            self.input = QSpinBox()
            self.input.setRange(int(min_val), int(max_val))
            self.input.valueChanged.connect(self._on_value_changed)
        else:
            self.input = QLineEdit()
            self.input.textChanged.connect(self._on_value_changed)

        self.input.setFixedWidth(100)
        self._apply_input_style(False)
        layout.addWidget(self.input)

        # Unit label
        if unit:
            unit_label = QLabel(unit)
            unit_label.setStyleSheet(f"font-size: 12px; color: {NotionColors.TEXT_TERTIARY};")
            layout.addWidget(unit_label)

        # Inherited value indicator
        self.inherited_label = QLabel()
        self.inherited_label.setStyleSheet(f"font-size: 11px; color: {NotionColors.TEXT_TERTIARY}; font-style: italic;")
        layout.addWidget(self.inherited_label)

        # Reset button (to revert to inherited value)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFixedSize(50, 24)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.clicked.connect(self._on_reset)
        self.reset_btn.setVisible(False)
        self.reset_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {NotionColors.BORDER};
                border-radius: 4px;
                font-size: 11px;
                color: {NotionColors.TEXT_TERTIARY};
            }}
            QPushButton:hover {{
                background-color: {NotionColors.BACKGROUND_HOVER};
            }}
        """)
        layout.addWidget(self.reset_btn)

        layout.addStretch()

    def _apply_input_style(self, is_overridden: bool):
        """Apply styling based on override state."""
        if is_overridden:
            border_color = NotionColors.PRIMARY
            bg_color = NotionColors.PRIMARY_LIGHT
        else:
            border_color = NotionColors.BORDER
            bg_color = NotionColors.BACKGROUND

        self.input.setStyleSheet(f"""
            QDoubleSpinBox, QSpinBox, QLineEdit {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
            }}
            QDoubleSpinBox:focus, QSpinBox:focus, QLineEdit:focus {{
                border-color: {NotionColors.PRIMARY};
            }}
        """)

    def set_inherited_value(self, value: Any):
        """Set the inherited value from template."""
        self._inherited_value = value
        self.inherited_label.setText(f"(template: {value})")

    def set_value(self, value: Any, is_override: bool = False):
        """Set the current value."""
        self._is_overridden = is_override
        self.input.blockSignals(True)

        if self.field_type == "float":
            self.input.setValue(float(value) if value is not None else 0.0)
        elif self.field_type == "int":
            self.input.setValue(int(value) if value is not None else 0)
        else:
            self.input.setText(str(value) if value is not None else "")

        self.input.blockSignals(False)
        self._apply_input_style(is_override)
        self.reset_btn.setVisible(is_override)

    def get_value(self) -> Any:
        """Get the current value."""
        if self.field_type in ("float", "int"):
            return self.input.value()
        else:
            return self.input.text()

    def is_overridden(self) -> bool:
        """Check if value is overridden from template."""
        return self._is_overridden

    def _on_value_changed(self):
        """Handle value change."""
        current = self.get_value()
        # Check if different from inherited
        if current != self._inherited_value:
            self._is_overridden = True
            self._apply_input_style(True)
            self.reset_btn.setVisible(True)
        self.value_changed.emit(self.field_path, current)

    def _on_reset(self):
        """Reset to inherited value."""
        if self._inherited_value is not None:
            self.set_value(self._inherited_value, False)
            self._is_overridden = False
            self.value_changed.emit(self.field_path, None)  # None means remove override


class ExperimentEditorView(QWidget):
    """
    Editor view for a single experiment.

    Features:
    - Display and edit experiment info
    - Parameter override from template
    - Image drop zone for optical images
    - Raman file list
    - Notes/observations text area
    """

    experiment_saved = Signal(str)  # experiment_id

    def __init__(
        self,
        experiment_manager: ExperimentManager,
        template_manager: TemplateManager,
        images_dir: Optional[Path] = None,
        parent=None
    ):
        super().__init__(parent)
        self.experiment_manager = experiment_manager
        self.template_manager = template_manager
        self.images_dir = images_dir
        self._current_experiment: Optional[Experiment] = None
        self._signals = get_app_signals()
        self._param_fields: dict[str, ParameterField] = {}

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {NotionColors.BACKGROUND};
            }}
        """)

        content = QWidget()
        content.setStyleSheet(f"background-color: {NotionColors.BACKGROUND};")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(32, 24, 32, 24)
        self.content_layout.setSpacing(24)

        # Placeholder when no experiment selected
        self.placeholder = QLabel("Select an experiment to view details")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet(f"""
            font-size: 16px;
            color: {NotionColors.TEXT_TERTIARY};
            padding: 60px;
        """)
        self.content_layout.addWidget(self.placeholder)

        # Parameters section (editable)
        self.params_section = self._create_params_section()
        self.params_section.setVisible(False)
        self.content_layout.addWidget(self.params_section)

        # Images section
        self.image_drop_zone = ImageDropZone(images_dir=self.images_dir)
        self.image_drop_zone.images_dropped.connect(self._on_images_dropped)
        self.image_drop_zone.image_clicked.connect(self._on_image_clicked)
        self.image_drop_zone.setVisible(False)
        self.content_layout.addWidget(self.image_drop_zone)

        # Raman section
        self.raman_section = self._create_raman_section()
        self.raman_section.setVisible(False)
        self.content_layout.addWidget(self.raman_section)

        # Notes section
        self.notes_section = self._create_notes_section()
        self.notes_section.setVisible(False)
        self.content_layout.addWidget(self.notes_section)

        self.content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # Footer with save button
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """Create the header with experiment name and date."""
        header = QWidget()
        header.setObjectName("experimentEditorHeader")
        header.setStyleSheet(f"""
            QWidget#experimentEditorHeader {{
                background-color: {NotionColors.BACKGROUND};
                border-bottom: 1px solid {NotionColors.BORDER};
            }}
        """)
        header.setFixedHeight(80)

        layout = QVBoxLayout(header)
        layout.setContentsMargins(32, 16, 32, 16)
        layout.setSpacing(4)

        # Name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Experiment name")
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background: transparent;
                font-size: 24px;
                font-weight: 600;
                color: {NotionColors.TEXT_PRIMARY};
                padding: 0;
            }}
            QLineEdit:focus {{
                background-color: {NotionColors.BACKGROUND_HOVER};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        layout.addWidget(self.name_input)

        # Date and template info
        self.info_label = QLabel()
        self.info_label.setStyleSheet(f"""
            font-size: 13px;
            color: {NotionColors.TEXT_SECONDARY};
        """)
        layout.addWidget(self.info_label)

        return header

    def _create_params_section(self) -> QWidget:
        """Create the editable parameters section."""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {NotionColors.SIDEBAR_BG};
                border: 1px solid {NotionColors.BORDER};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(section)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Section title
        title_row = QHBoxLayout()
        title = QLabel("CVD Parameters")
        title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {NotionColors.TEXT_PRIMARY};
        """)
        title_row.addWidget(title)

        # Template name
        self.template_name_label = QLabel()
        self.template_name_label.setStyleSheet(f"""
            font-size: 12px;
            color: {NotionColors.TEXT_TERTIARY};
        """)
        title_row.addWidget(self.template_name_label)
        title_row.addStretch()

        layout.addLayout(title_row)

        # Temperature section
        temp_title = QLabel("Temperature")
        temp_title.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {NotionColors.SECTION_TEMPERATURE};
            margin-top: 8px;
        """)
        layout.addWidget(temp_title)

        self._param_fields["temperature.peak_temp"] = ParameterField(
            "Peak Temp", "temperature.peak_temp", "float", "°C", 0, 1200, 0
        )
        layout.addWidget(self._param_fields["temperature.peak_temp"])

        self._param_fields["temperature.peak_hold_time"] = ParameterField(
            "Hold Time", "temperature.peak_hold_time", "float", "min", 0, 120, 0
        )
        layout.addWidget(self._param_fields["temperature.peak_hold_time"])

        self._param_fields["temperature.ramp_rate_2"] = ParameterField(
            "Ramp Rate", "temperature.ramp_rate_2", "float", "°C/min", 0, 50, 1
        )
        layout.addWidget(self._param_fields["temperature.ramp_rate_2"])

        # Gas Flow section
        gas_title = QLabel("Gas Flow")
        gas_title.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {NotionColors.SECTION_GAS_FLOW};
            margin-top: 8px;
        """)
        layout.addWidget(gas_title)

        self._param_fields["gas_flow.ar_flow"] = ParameterField(
            "Ar Flow", "gas_flow.ar_flow", "float", "sccm", 0, 500, 0
        )
        layout.addWidget(self._param_fields["gas_flow.ar_flow"])

        self._param_fields["gas_flow.h2_flow"] = ParameterField(
            "H2 Flow", "gas_flow.h2_flow", "float", "sccm", 0, 100, 0
        )
        layout.addWidget(self._param_fields["gas_flow.h2_flow"])

        # Precursor section
        precursor_title = QLabel("Precursor")
        precursor_title.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {NotionColors.SECTION_PRECURSOR};
            margin-top: 8px;
        """)
        layout.addWidget(precursor_title)

        self._param_fields["precursor.moo3_amount"] = ParameterField(
            "MoO3", "precursor.moo3_amount", "float", "mg", 0, 100, 1
        )
        layout.addWidget(self._param_fields["precursor.moo3_amount"])

        self._param_fields["precursor.s_amount"] = ParameterField(
            "Sulfur", "precursor.s_amount", "float", "mg", 0, 500, 0
        )
        layout.addWidget(self._param_fields["precursor.s_amount"])

        # Connect all fields
        for field in self._param_fields.values():
            field.value_changed.connect(self._on_param_changed)

        return section

    def _create_raman_section(self) -> QWidget:
        """Create the Raman files section."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Title with add button
        title_row = QHBoxLayout()
        title = QLabel("Raman Files")
        title.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 600;
            color: {NotionColors.TEXT_PRIMARY};
        """)
        title_row.addWidget(title)
        title_row.addStretch()

        add_btn = QPushButton("+ Add")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._on_add_raman_clicked)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {NotionColors.PRIMARY};
                font-size: 13px;
                font-weight: 500;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background-color: {NotionColors.BACKGROUND_HOVER};
                border-radius: 4px;
            }}
        """)
        title_row.addWidget(add_btn)

        layout.addLayout(title_row)

        # File list
        self.raman_list = QWidget()
        self.raman_list_layout = QVBoxLayout(self.raman_list)
        self.raman_list_layout.setContentsMargins(0, 0, 0, 0)
        self.raman_list_layout.setSpacing(4)
        layout.addWidget(self.raman_list)

        # Placeholder
        self.raman_placeholder = QLabel("No Raman files added")
        self.raman_placeholder.setStyleSheet(f"""
            font-size: 13px;
            color: {NotionColors.TEXT_TERTIARY};
            padding: 16px;
        """)
        self.raman_list_layout.addWidget(self.raman_placeholder)

        return section

    def _create_notes_section(self) -> QWidget:
        """Create the notes/observations section."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("Notes & Observations")
        title.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 600;
            color: {NotionColors.TEXT_PRIMARY};
        """)
        layout.addWidget(title)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Add your experiment notes here...")
        self.notes_edit.setMinimumHeight(150)
        self.notes_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {NotionColors.SIDEBAR_BG};
                border: 1px solid {NotionColors.BORDER};
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                color: {NotionColors.TEXT_PRIMARY};
            }}
            QTextEdit:focus {{
                border-color: {NotionColors.PRIMARY};
            }}
        """)
        layout.addWidget(self.notes_edit)

        return section

    def _create_footer(self) -> QWidget:
        """Create the footer with save button."""
        footer = QWidget()
        footer.setObjectName("experimentEditorFooter")
        footer.setStyleSheet(f"""
            QWidget#experimentEditorFooter {{
                background-color: {NotionColors.SIDEBAR_BG};
                border-top: 1px solid {NotionColors.BORDER};
            }}
        """)
        footer.setFixedHeight(64)

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(32, 0, 32, 0)

        layout.addStretch()

        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.setFixedSize(100, 36)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self._on_save)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {NotionColors.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {NotionColors.PRIMARY_HOVER};
            }}
        """)
        layout.addWidget(self.save_btn)

        return footer

    # ==================== Public Methods ====================

    def load_experiment(self, experiment_id: str):
        """Load an experiment for editing."""
        experiment = self.experiment_manager.get_experiment(experiment_id)
        if not experiment:
            return

        self._current_experiment = experiment

        # Show all sections
        self.placeholder.setVisible(False)
        self.params_section.setVisible(True)
        self.image_drop_zone.setVisible(True)
        self.raman_section.setVisible(True)
        self.notes_section.setVisible(True)

        # Update header
        self.name_input.setText(experiment.name)

        # Format date
        date_str = experiment.created_at[:10] if experiment.created_at else "Unknown date"
        self.info_label.setText(f"Created: {date_str}")

        # Load template and populate parameter fields
        template = self.template_manager.get_template(experiment.template_id)
        if template:
            self.template_name_label.setText(f"(based on: {template.name})")
            resolved = self.template_manager.resolve_template(template.id)

            # Set inherited values and current values for each field
            for field_path, field in self._param_fields.items():
                # Get inherited value from template
                inherited = self.template_manager._get_field_value(resolved, field_path)
                field.set_inherited_value(inherited)

                # Check if overridden in experiment
                if field_path in experiment.overrides:
                    field.set_value(experiment.overrides[field_path], is_override=True)
                else:
                    field.set_value(inherited, is_override=False)
        else:
            self.template_name_label.setText("(template not found)")

        # Update images
        self.image_drop_zone.set_images(experiment.optical_images)

        # Update raman files
        self._refresh_raman_list()

        # Update notes
        self.notes_edit.setText(experiment.notes or "")

    def clear(self):
        """Clear the editor."""
        self._current_experiment = None
        self.placeholder.setVisible(True)
        self.params_section.setVisible(False)
        self.image_drop_zone.setVisible(False)
        self.raman_section.setVisible(False)
        self.notes_section.setVisible(False)
        self.name_input.clear()
        self.info_label.clear()
        self.notes_edit.clear()

    # ==================== Event Handlers ====================

    def _on_param_changed(self, field_path: str, value: Any):
        """Handle parameter value change."""
        if not self._current_experiment:
            return

        if value is None:
            # Remove override
            self._current_experiment.remove_override(field_path)
        else:
            # Get inherited value to check if actually different
            template = self.template_manager.get_template(self._current_experiment.template_id)
            if template:
                resolved = self.template_manager.resolve_template(template.id)
                inherited = self.template_manager._get_field_value(resolved, field_path)
                if value != inherited:
                    self._current_experiment.set_override(field_path, value)
                else:
                    self._current_experiment.remove_override(field_path)

    def _on_images_dropped(self, paths: list[Path]):
        """Handle dropped image files."""
        if not self._current_experiment:
            return

        for path in paths:
            try:
                self.experiment_manager.add_image_to_experiment(
                    self._current_experiment.id,
                    path
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add image: {e}")

        # Refresh the display
        experiment = self.experiment_manager.get_experiment(self._current_experiment.id)
        if experiment:
            self._current_experiment = experiment
            self.image_drop_zone.set_images(experiment.optical_images)

    def _on_image_clicked(self, image_path: str):
        """Handle image thumbnail click - open preview."""
        if not self._current_experiment:
            return

        images = self._current_experiment.optical_images
        try:
            index = images.index(image_path)
        except ValueError:
            index = 0

        dialog = ImagePreviewDialog(
            image_paths=images,
            images_dir=self.images_dir,
            initial_index=index,
            parent=self
        )
        dialog.exec()

    def _on_add_raman_clicked(self):
        """Handle add raman button click."""
        if not self._current_experiment:
            return

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Raman Files",
            "",
            "All Files (*.*)"
        )

        for file_path in file_paths:
            try:
                self.experiment_manager.add_raman_to_experiment(
                    self._current_experiment.id,
                    Path(file_path)
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add file: {e}")

        # Refresh
        experiment = self.experiment_manager.get_experiment(self._current_experiment.id)
        if experiment:
            self._current_experiment = experiment
            self._refresh_raman_list()

    def _refresh_raman_list(self):
        """Refresh the Raman files list display."""
        # Clear existing items (except placeholder)
        while self.raman_list_layout.count() > 1:
            item = self.raman_list_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        if not self._current_experiment or not self._current_experiment.raman_files:
            self.raman_placeholder.setVisible(True)
            return

        self.raman_placeholder.setVisible(False)

        for file_path in self._current_experiment.raman_files:
            item = QLabel(f"  {Path(file_path).name}")
            item.setStyleSheet(f"""
                font-size: 13px;
                color: {NotionColors.TEXT_SECONDARY};
                padding: 8px 12px;
                background-color: {NotionColors.SIDEBAR_BG};
                border-radius: 4px;
            """)
            self.raman_list_layout.addWidget(item)

    def _on_save(self):
        """Save the experiment."""
        if not self._current_experiment:
            return

        # Update from UI
        self._current_experiment.name = self.name_input.text().strip()
        self._current_experiment.notes = self.notes_edit.toPlainText()

        # Validate
        if not self._current_experiment.name:
            QMessageBox.warning(self, "Validation Error", "Experiment name is required.")
            return

        # Save
        self.experiment_manager.update_experiment(self._current_experiment)
        self.experiment_manager.save()

        self._signals.status_message.emit("Experiment saved", 3000)
        self.experiment_saved.emit(self._current_experiment.id)
