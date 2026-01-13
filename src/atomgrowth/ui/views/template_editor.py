"""Template editor view with all CVD parameter sections"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox,
    QFrame, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Signal, Qt

from atomgrowth.models.recipe import RecipeTemplate
from atomgrowth.core.template_manager import TemplateManager
from atomgrowth.ui.widgets.parameter_field import (
    InheritableParameterField, ParameterSection
)
from atomgrowth.styles.colors import NotionColors
from atomgrowth.signals.app_signals import get_app_signals


class TemplateEditorView(QWidget):
    """
    Full template editor with all CVD parameter sections.

    Features:
    - Header with template name, description, parent selector
    - Parameter sections: Temperature, Gas Flow, Precursor, Substrate
    - Each parameter shows inherited vs. overridden state
    - Save/Cancel buttons
    """

    template_saved = Signal(str)  # template_id

    def __init__(self, template_manager: TemplateManager, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.template_manager = template_manager
        self._current_template: Optional[RecipeTemplate] = None
        self._signals = get_app_signals()

        self._setup_ui()

    def _setup_ui(self):
        """Setup the editor UI"""
        self.setObjectName("templateEditor")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Scroll area for parameters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        # Parameters container
        params_widget = QWidget()
        params_widget.setStyleSheet(f"background-color: {NotionColors.BACKGROUND_SECONDARY};")
        self._params_layout = QVBoxLayout(params_widget)
        self._params_layout.setContentsMargins(20, 20, 20, 20)
        self._params_layout.setSpacing(16)

        # Create parameter sections
        self._create_temperature_section()
        self._create_gas_flow_section()
        self._create_precursor_section()
        self._create_substrate_section()

        # Add stretch at bottom
        self._params_layout.addStretch()

        scroll.setWidget(params_widget)
        layout.addWidget(scroll)

        # Footer with buttons
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """Create the header with name, description, parent selector"""
        header = QFrame()
        header.setObjectName("templateEditorHeader")
        header.setStyleSheet(f"""
            QFrame#templateEditorHeader {{
                background-color: {NotionColors.BACKGROUND};
                border-bottom: 1px solid {NotionColors.BORDER};
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(header)
        layout.setSpacing(12)

        # Title row
        title_row = QHBoxLayout()
        title_label = QLabel("Template Editor")
        title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {NotionColors.TEXT_PRIMARY};
        """)
        title_row.addWidget(title_label)
        title_row.addStretch()
        layout.addLayout(title_row)

        # Name input
        name_row = QHBoxLayout()
        name_label = QLabel("Name:")
        name_label.setMinimumWidth(100)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Template name...")
        name_row.addWidget(name_label)
        name_row.addWidget(self.name_input)
        layout.addLayout(name_row)

        # Parent template selector
        parent_row = QHBoxLayout()
        parent_label = QLabel("Inherits from:")
        parent_label.setMinimumWidth(100)
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("(None - Base Template)", None)
        self.parent_combo.currentIndexChanged.connect(self._on_parent_changed)
        parent_row.addWidget(parent_label)
        parent_row.addWidget(self.parent_combo)
        layout.addLayout(parent_row)

        # Description
        desc_label = QLabel("Description:")
        layout.addWidget(desc_label)
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setPlaceholderText("Optional description...")
        layout.addWidget(self.desc_input)

        return header

    def _create_footer(self) -> QWidget:
        """Create footer with save/cancel buttons"""
        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {NotionColors.BACKGROUND};
                border-top: 1px solid {NotionColors.BORDER};
                padding: 12px 20px;
            }}
        """)

        layout = QHBoxLayout(footer)
        layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(cancel_btn)

        # Save button
        save_btn = QPushButton("Save Template")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._on_save)
        layout.addWidget(save_btn)

        return footer

    def _create_temperature_section(self):
        """Create temperature profile parameter section"""
        section = ParameterSection(
            "Temperature Profile",
            color=NotionColors.SECTION_TEMPERATURE
        )

        fields = [
            ("temperature.ramp_rate_1", "Ramp Rate 1", "float", "°C/min", 1, 50, 1),
            ("temperature.hold_temp_1", "Hold Temp 1", "float", "°C", 0, 1000, 0),
            ("temperature.hold_time_1", "Hold Time 1", "float", "min", 0, 120, 1),
            ("temperature.ramp_rate_2", "Ramp Rate 2", "float", "°C/min", 1, 50, 1),
            ("temperature.peak_temp", "Peak Temperature", "float", "°C", 400, 1000, 0),
            ("temperature.peak_hold_time", "Peak Hold Time", "float", "min", 0, 120, 1),
            ("temperature.cooling_method", "Cooling Method", "choice", "", None, None, None),
            ("temperature.controlled_cool_rate", "Cool Rate", "float", "°C/min", 1, 50, 1),
        ]

        for field_path, label, ftype, unit, min_v, max_v, dec in fields:
            if ftype == "choice":
                field = InheritableParameterField(
                    field_path, label, ftype,
                    choices=["natural", "controlled", "quench"]
                )
            else:
                field = InheritableParameterField(
                    field_path, label, ftype, unit,
                    min_val=min_v, max_val=max_v, decimals=dec
                )
            field.value_changed.connect(self._on_field_changed)
            field.inheritance_changed.connect(self._on_inheritance_changed)
            section.add_field(field)

        self._params_layout.addWidget(section)
        self._temp_section = section

    def _create_gas_flow_section(self):
        """Create gas flow parameter section"""
        section = ParameterSection(
            "Gas Flow",
            color=NotionColors.SECTION_GAS_FLOW
        )

        fields = [
            ("gas_flow.ar_flow", "Ar Flow", "float", "sccm", 0, 500, 1),
            ("gas_flow.h2_flow", "H₂ Flow", "float", "sccm", 0, 100, 1),
            ("gas_flow.total_flow", "Total Flow", "float", "sccm", 0, 500, 1),
        ]

        for field_path, label, ftype, unit, min_v, max_v, dec in fields:
            field = InheritableParameterField(
                field_path, label, ftype, unit,
                min_val=min_v, max_val=max_v, decimals=dec
            )
            field.value_changed.connect(self._on_field_changed)
            field.inheritance_changed.connect(self._on_inheritance_changed)
            section.add_field(field)

        self._params_layout.addWidget(section)
        self._gas_section = section

    def _create_precursor_section(self):
        """Create precursor setup parameter section"""
        section = ParameterSection(
            "Precursor Setup",
            color=NotionColors.SECTION_PRECURSOR
        )

        fields = [
            ("precursor.moo3_amount", "MoO₃ Amount", "float", "mg", 0, 50, 1),
            ("precursor.s_amount", "S Amount", "float", "mg", 0, 500, 1),
            ("precursor.moo3_position", "MoO₃ Position", "float", "cm", -30, 30, 1),
            ("precursor.s_position", "S Position", "float", "cm", -30, 30, 1),
            ("precursor.moo3_boat_material", "MoO₃ Boat", "choice", "", None, None, None),
            ("precursor.s_boat_material", "S Boat", "choice", "", None, None, None),
        ]

        for field_path, label, ftype, unit, min_v, max_v, dec in fields:
            if ftype == "choice":
                field = InheritableParameterField(
                    field_path, label, ftype,
                    choices=["alumina", "quartz", "graphite"]
                )
            else:
                field = InheritableParameterField(
                    field_path, label, ftype, unit,
                    min_val=min_v, max_val=max_v, decimals=dec
                )
            field.value_changed.connect(self._on_field_changed)
            field.inheritance_changed.connect(self._on_inheritance_changed)
            section.add_field(field)

        self._params_layout.addWidget(section)
        self._precursor_section = section

    def _create_substrate_section(self):
        """Create substrate info parameter section"""
        section = ParameterSection(
            "Substrate",
            color=NotionColors.SECTION_SUBSTRATE
        )

        fields = [
            ("substrate.material", "Material", "choice", "", None, None, None),
            ("substrate.oxide_thickness", "Oxide Thickness", "float", "nm", 0, 1000, 0),
            ("substrate.prep_method", "Prep Method", "choice", "", None, None, None),
            ("substrate.orientation", "Orientation", "str", "", None, None, None),
            ("substrate.size", "Size", "str", "", None, None, None),
        ]

        for field_path, label, ftype, unit, min_v, max_v, dec in fields:
            if field_path == "substrate.material":
                field = InheritableParameterField(
                    field_path, label, ftype,
                    choices=["SiO2/Si", "Sapphire", "Quartz", "Mica", "hBN"]
                )
            elif field_path == "substrate.prep_method":
                field = InheritableParameterField(
                    field_path, label, ftype,
                    choices=["piranha", "O2_plasma", "acetone_IPA", "sonication", "none"]
                )
            elif ftype == "float":
                field = InheritableParameterField(
                    field_path, label, ftype, unit,
                    min_val=min_v, max_val=max_v, decimals=dec
                )
            else:
                field = InheritableParameterField(
                    field_path, label, ftype, unit
                )
            field.value_changed.connect(self._on_field_changed)
            field.inheritance_changed.connect(self._on_inheritance_changed)
            section.add_field(field)

        self._params_layout.addWidget(section)
        self._substrate_section = section

    # ==================== Public API ====================

    def load_template(self, template_id: str):
        """Load a template for editing"""
        template = self.template_manager.get_template(template_id)
        if not template:
            return

        self._current_template = template

        # Update header fields
        self.name_input.setText(template.name)
        self.desc_input.setText(template.description)

        # Update parent combo
        self._refresh_parent_combo()
        if template.parent_template_id:
            for i in range(self.parent_combo.count()):
                if self.parent_combo.itemData(i) == template.parent_template_id:
                    self.parent_combo.setCurrentIndex(i)
                    break

        # Load parameter values
        self._load_parameter_values()

    def new_template(self, parent_id: Optional[str] = None):
        """Start editing a new template"""
        self._current_template = RecipeTemplate(name="New Template")
        if parent_id:
            self._current_template.parent_template_id = parent_id

        self.name_input.setText("")
        self.desc_input.setText("")

        self._refresh_parent_combo()
        if parent_id:
            for i in range(self.parent_combo.count()):
                if self.parent_combo.itemData(i) == parent_id:
                    self.parent_combo.setCurrentIndex(i)
                    break

        self._load_parameter_values()

    def _refresh_parent_combo(self):
        """Refresh the parent template dropdown"""
        current_data = self.parent_combo.currentData()
        self.parent_combo.clear()
        self.parent_combo.addItem("(None - Base Template)", None)

        for template in self.template_manager.list_templates():
            # Don't show current template as an option
            if self._current_template and template.id == self._current_template.id:
                continue
            self.parent_combo.addItem(template.name, template.id)

        # Restore selection
        for i in range(self.parent_combo.count()):
            if self.parent_combo.itemData(i) == current_data:
                self.parent_combo.setCurrentIndex(i)
                break

    def _load_parameter_values(self):
        """Load parameter values into all fields"""
        if not self._current_template:
            return

        # Get resolved values (with inheritance)
        if self._current_template.id in [t.id for t in self.template_manager.list_templates()]:
            resolved = self.template_manager.resolve_template(self._current_template.id)
        else:
            resolved = self._current_template

        # Load all sections
        for section in [self._temp_section, self._gas_section,
                        self._precursor_section, self._substrate_section]:
            for field_path, field in section.get_all_fields().items():
                value, source_id = self.template_manager.get_effective_value(
                    self._current_template.id, field_path
                ) if self._current_template.id in [t.id for t in self.template_manager.list_templates()] else (
                    self.template_manager._get_field_value(resolved, field_path), None
                )

                source_name = None
                if source_id:
                    source_template = self.template_manager.get_template(source_id)
                    source_name = source_template.name if source_template else None

                field.set_inherited_value(value, source_name)

    # ==================== Event Handlers ====================

    def _on_parent_changed(self, index):
        """Handle parent template selection change"""
        if self._current_template:
            self._current_template.parent_template_id = self.parent_combo.currentData()
            self._load_parameter_values()

    def _on_field_changed(self, field_path: str, value):
        """Handle parameter field value change"""
        if self._current_template:
            self.template_manager._set_field_value(self._current_template, field_path, value)

    def _on_inheritance_changed(self, field_path: str, is_inherited: bool):
        """Handle inheritance toggle"""
        pass  # For now, the field handles its own state

    def _on_save(self):
        """Save the current template"""
        if not self._current_template:
            return

        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Template name is required.")
            return

        self._current_template.name = name
        self._current_template.description = self.desc_input.toPlainText()
        self._current_template.parent_template_id = self.parent_combo.currentData()

        # Collect overridden values from fields
        for section in [self._temp_section, self._gas_section,
                        self._precursor_section, self._substrate_section]:
            for field_path, field in section.get_all_fields().items():
                if field.is_overridden():
                    value = field.get_value()
                    self.template_manager._set_field_value(
                        self._current_template, field_path, value
                    )

        # Save to manager
        if self._current_template.id in [t.id for t in self.template_manager.list_templates()]:
            self.template_manager.update_template(self._current_template)
        else:
            # It's a new template - add it
            self.template_manager._templates[self._current_template.id] = self._current_template
            self._signals.template_created.emit(self._current_template.id)

        self.template_saved.emit(self._current_template.id)
        self._signals.status_message.emit(f"Template '{name}' saved", 3000)

    def _on_cancel(self):
        """Cancel editing"""
        # Could emit a signal or just reload the original
        if self._current_template:
            self.load_template(self._current_template.id)
