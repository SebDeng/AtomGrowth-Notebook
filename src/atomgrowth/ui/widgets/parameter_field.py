"""Inheritable parameter field widget - the key UI innovation"""

from typing import Any, Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox,
    QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from atomgrowth.styles.colors import NotionColors


class InheritableParameterField(QWidget):
    """
    A parameter field that can be inherited or overridden.

    States:
    1. Inherited: Shows grayed value, source badge, lock icon
    2. Overridden: Shows editable value, "Modified" badge, unlock icon

    The widget displays:
    - Field label
    - Value input (type-dependent: spinbox, text, dropdown)
    - Unit label (optional)
    - Inheritance badge showing source
    - Lock/unlock toggle button
    """

    # Signals
    value_changed = Signal(str, object)      # (field_path, new_value)
    inheritance_changed = Signal(str, bool)  # (field_path, is_inherited)

    def __init__(
        self,
        field_path: str,
        label: str,
        field_type: str = "float",  # float, int, str, choice
        unit: str = "",
        choices: Optional[list[str]] = None,
        min_val: float = 0,
        max_val: float = 10000,
        decimals: int = 1,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        self.field_path = field_path
        self.field_type = field_type
        self._is_inherited = True
        self._inherited_value: Any = None
        self._inherited_source: Optional[str] = None
        self._current_value: Any = None

        self._setup_ui(label, unit, choices, min_val, max_val, decimals)
        self._apply_inherited_style()

    def _setup_ui(
        self,
        label: str,
        unit: str,
        choices: Optional[list[str]],
        min_val: float,
        max_val: float,
        decimals: int
    ):
        """Setup the widget UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Label
        self.label_widget = QLabel(label)
        self.label_widget.setMinimumWidth(120)
        self.label_widget.setStyleSheet(f"color: {NotionColors.TEXT_PRIMARY};")
        layout.addWidget(self.label_widget)

        # Value input (type-dependent)
        self.input_widget = self._create_input(choices, min_val, max_val, decimals)
        self.input_widget.setMinimumWidth(100)
        self.input_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.input_widget)

        # Unit label (if provided)
        if unit:
            unit_label = QLabel(unit)
            unit_label.setStyleSheet(f"color: {NotionColors.TEXT_SECONDARY};")
            layout.addWidget(unit_label)

        # Inheritance badge
        self.badge = QLabel()
        self.badge.setMinimumWidth(80)
        self.badge.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.badge)

        # Lock/unlock button
        self.lock_btn = QPushButton()
        self.lock_btn.setFixedSize(28, 28)
        self.lock_btn.setCursor(Qt.PointingHandCursor)
        self.lock_btn.clicked.connect(self._toggle_inheritance)
        self.lock_btn.setToolTip("Click to override inherited value")
        layout.addWidget(self.lock_btn)

    def _create_input(
        self,
        choices: Optional[list[str]],
        min_val: float,
        max_val: float,
        decimals: int
    ) -> QWidget:
        """Create the appropriate input widget based on field type"""
        if self.field_type == "choice" and choices:
            widget = QComboBox()
            widget.addItems(choices)
            widget.currentTextChanged.connect(self._on_value_changed)
            return widget

        elif self.field_type == "int":
            widget = QSpinBox()
            widget.setRange(int(min_val), int(max_val))
            widget.valueChanged.connect(self._on_value_changed)
            return widget

        elif self.field_type == "float":
            widget = QDoubleSpinBox()
            widget.setRange(min_val, max_val)
            widget.setDecimals(decimals)
            widget.valueChanged.connect(self._on_value_changed)
            return widget

        else:  # str
            widget = QLineEdit()
            widget.textChanged.connect(self._on_value_changed)
            return widget

    def _on_value_changed(self, value):
        """Handle value changes from input widget"""
        if not self._is_inherited:
            self._current_value = value
            self.value_changed.emit(self.field_path, value)

    def _toggle_inheritance(self):
        """Toggle between inherited and overridden state"""
        if self._is_inherited:
            # Switch to override mode
            self._is_inherited = False
            self._current_value = self._inherited_value
            self._apply_overridden_style()
            self.input_widget.setEnabled(True)
            self.lock_btn.setToolTip("Click to revert to inherited value")
        else:
            # Revert to inherited
            self._is_inherited = True
            self._set_input_value(self._inherited_value)
            self._apply_inherited_style()
            self.input_widget.setEnabled(False)
            self.lock_btn.setToolTip("Click to override inherited value")

        self.inheritance_changed.emit(self.field_path, self._is_inherited)

    def _apply_inherited_style(self):
        """Apply visual style for inherited state"""
        self.setObjectName("inheritedField")

        # Gray out input
        self.input_widget.setEnabled(False)
        self.input_widget.setStyleSheet(f"""
            background-color: {NotionColors.INHERITED_BG};
            color: {NotionColors.INHERITED};
            border: 1px solid {NotionColors.BORDER};
        """)

        # Badge shows source
        source_text = self._inherited_source or "Default"
        self.badge.setText(source_text)
        self.badge.setObjectName("inheritedBadge")
        self.badge.setStyleSheet(f"""
            background-color: {NotionColors.INHERITED_BG};
            color: {NotionColors.INHERITED};
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 11px;
        """)

        # Lock icon (using text for now, could use actual icon)
        self.lock_btn.setText("🔒")
        self.lock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {NotionColors.INHERITED_BG};
                border: 1px solid {NotionColors.BORDER};
                border-radius: 4px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {NotionColors.BACKGROUND_HOVER};
                border-color: {NotionColors.PRIMARY};
            }}
        """)

    def _apply_overridden_style(self):
        """Apply visual style for overridden state"""
        self.setObjectName("overriddenField")

        # Enable and highlight input
        self.input_widget.setEnabled(True)
        self.input_widget.setStyleSheet(f"""
            background-color: {NotionColors.OVERRIDDEN_BG};
            color: {NotionColors.OVERRIDDEN};
            border: 1px solid {NotionColors.PRIMARY};
            font-weight: 600;
        """)

        # Badge shows "Modified"
        self.badge.setText("Modified")
        self.badge.setObjectName("modifiedBadge")
        self.badge.setStyleSheet(f"""
            background-color: {NotionColors.OVERRIDDEN_BG};
            color: {NotionColors.OVERRIDDEN};
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 600;
        """)

        # Unlock icon
        self.lock_btn.setText("🔓")
        self.lock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {NotionColors.OVERRIDDEN_BG};
                border: 1px solid {NotionColors.PRIMARY};
                border-radius: 4px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {NotionColors.PRIMARY_LIGHT};
            }}
        """)

    def _set_input_value(self, value: Any):
        """Set the input widget value without triggering signals"""
        if isinstance(self.input_widget, QComboBox):
            self.input_widget.blockSignals(True)
            idx = self.input_widget.findText(str(value))
            if idx >= 0:
                self.input_widget.setCurrentIndex(idx)
            self.input_widget.blockSignals(False)

        elif isinstance(self.input_widget, (QSpinBox, QDoubleSpinBox)):
            self.input_widget.blockSignals(True)
            self.input_widget.setValue(value)
            self.input_widget.blockSignals(False)

        elif isinstance(self.input_widget, QLineEdit):
            self.input_widget.blockSignals(True)
            self.input_widget.setText(str(value))
            self.input_widget.blockSignals(False)

    def get_input_value(self) -> Any:
        """Get current value from input widget"""
        if isinstance(self.input_widget, QComboBox):
            return self.input_widget.currentText()
        elif isinstance(self.input_widget, (QSpinBox, QDoubleSpinBox)):
            return self.input_widget.value()
        elif isinstance(self.input_widget, QLineEdit):
            return self.input_widget.text()
        return None

    # ==================== Public API ====================

    def set_inherited_value(self, value: Any, source: Optional[str] = None):
        """Set the inherited value and source template name"""
        self._inherited_value = value
        self._inherited_source = source
        self._set_input_value(value)

        if self._is_inherited:
            self._apply_inherited_style()

    def set_override_value(self, value: Any):
        """Set an override value (switches to override mode)"""
        self._is_inherited = False
        self._current_value = value
        self._set_input_value(value)
        self._apply_overridden_style()
        self.input_widget.setEnabled(True)

    def get_value(self) -> Any:
        """Get the current effective value"""
        if self._is_inherited:
            return self._inherited_value
        return self.get_input_value()

    def is_inherited(self) -> bool:
        """Check if field is in inherited state"""
        return self._is_inherited

    def is_overridden(self) -> bool:
        """Check if field is overridden"""
        return not self._is_inherited

    def revert_to_inherited(self):
        """Revert to inherited value"""
        if not self._is_inherited:
            self._toggle_inheritance()


class ParameterSection(QFrame):
    """
    A collapsible section containing multiple parameter fields.
    Used to group related parameters (Temperature, Gas Flow, etc.)
    """

    def __init__(
        self,
        title: str,
        color: str = NotionColors.PRIMARY,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)

        self.setObjectName("parameterSection")
        self.setStyleSheet(f"""
            QFrame#parameterSection {{
                background-color: {NotionColors.BACKGROUND};
                border: 1px solid {NotionColors.BORDER};
                border-left: 3px solid {color};
                border-radius: 8px;
                margin: 4px 0;
            }}
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 8, 12, 8)
        self._layout.setSpacing(4)

        # Header
        header = QLabel(title)
        header.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 600;
            color: {color};
            padding: 4px 0;
        """)
        self._layout.addWidget(header)

        # Fields container
        self._fields_container = QWidget()
        self._fields_layout = QVBoxLayout(self._fields_container)
        self._fields_layout.setContentsMargins(0, 0, 0, 0)
        self._fields_layout.setSpacing(2)
        self._layout.addWidget(self._fields_container)

        self._fields: dict[str, InheritableParameterField] = {}

    def add_field(self, field: InheritableParameterField):
        """Add a parameter field to this section"""
        self._fields_layout.addWidget(field)
        self._fields[field.field_path] = field

    def get_field(self, field_path: str) -> Optional[InheritableParameterField]:
        """Get a field by its path"""
        return self._fields.get(field_path)

    def get_all_fields(self) -> dict[str, InheritableParameterField]:
        """Get all fields in this section"""
        return self._fields
