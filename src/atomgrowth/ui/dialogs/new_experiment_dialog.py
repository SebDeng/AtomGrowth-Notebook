"""Dialog for creating a new experiment"""

from typing import Optional
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QWidget
)
from PySide6.QtCore import Qt

from atomgrowth.core.template_manager import TemplateManager
from atomgrowth.styles.colors import NotionColors


class NewExperimentDialog(QDialog):
    """
    Dialog for creating a new experiment.

    User selects a template and enters experiment name.
    """

    def __init__(self, template_manager: TemplateManager, parent=None):
        super().__init__(parent)
        self.template_manager = template_manager
        self._selected_template_id: Optional[str] = None

        self.setWindowTitle("New Experiment")
        self.setMinimumWidth(450)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Title
        title = QLabel("Create New Experiment")
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 600;
            color: {NotionColors.TEXT_PRIMARY};
        """)
        layout.addWidget(title)

        # Form
        form = QWidget()
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(16)

        # Template selection
        template_label = QLabel("Template")
        template_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 500;
            color: {NotionColors.TEXT_SECONDARY};
        """)
        form_layout.addWidget(template_label)

        self.template_combo = QComboBox()
        self.template_combo.setMinimumHeight(40)
        self.template_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {NotionColors.BACKGROUND};
                border: 1px solid {NotionColors.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                color: {NotionColors.TEXT_PRIMARY};
            }}
            QComboBox:focus {{
                border-color: {NotionColors.PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {NotionColors.TEXT_SECONDARY};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {NotionColors.BACKGROUND};
                border: 1px solid {NotionColors.BORDER};
                selection-background-color: {NotionColors.BACKGROUND_HOVER};
            }}
        """)

        # Populate templates
        templates = self.template_manager.list_templates()
        for template in templates:
            self.template_combo.addItem(template.name, template.id)

        form_layout.addWidget(self.template_combo)

        # Experiment name
        name_label = QLabel("Experiment Name")
        name_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 500;
            color: {NotionColors.TEXT_SECONDARY};
        """)
        form_layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setMinimumHeight(40)
        # Default name with date
        default_name = f"Experiment {datetime.now().strftime('%Y-%m-%d')}"
        self.name_input.setText(default_name)
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {NotionColors.BACKGROUND};
                border: 1px solid {NotionColors.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                color: {NotionColors.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {NotionColors.PRIMARY};
            }}
        """)
        form_layout.addWidget(self.name_input)

        layout.addWidget(form)

        layout.addStretch()

        # Buttons
        button_row = QHBoxLayout()
        button_row.setSpacing(12)

        button_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 40)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {NotionColors.BACKGROUND};
                border: 1px solid {NotionColors.BORDER};
                border-radius: 6px;
                font-size: 14px;
                color: {NotionColors.TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                background-color: {NotionColors.BACKGROUND_HOVER};
                border-color: {NotionColors.TEXT_TERTIARY};
            }}
        """)
        button_row.addWidget(cancel_btn)

        create_btn = QPushButton("Create")
        create_btn.setFixedSize(100, 40)
        create_btn.setCursor(Qt.PointingHandCursor)
        create_btn.clicked.connect(self._on_create)
        create_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {NotionColors.PRIMARY};
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                color: white;
            }}
            QPushButton:hover {{
                background-color: {NotionColors.PRIMARY_HOVER};
            }}
        """)
        button_row.addWidget(create_btn)

        layout.addLayout(button_row)

    def _on_create(self):
        """Handle create button click."""
        if not self.name_input.text().strip():
            self.name_input.setFocus()
            return

        if self.template_combo.currentIndex() < 0:
            return

        self._selected_template_id = self.template_combo.currentData()
        self.accept()

    def get_selected_template_id(self) -> Optional[str]:
        """Get the selected template ID."""
        return self._selected_template_id

    def get_experiment_name(self) -> str:
        """Get the entered experiment name."""
        return self.name_input.text().strip()
