"""Dialog for creating a new template"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QPushButton
)
from PySide6.QtCore import Qt

from atomgrowth.core.template_manager import TemplateManager
from atomgrowth.styles.colors import NotionColors


class NewTemplateDialog(QDialog):
    """
    Simple dialog for creating a new template.
    Just captures name, description, and parent - full editing happens in editor.
    """

    def __init__(
        self,
        template_manager: TemplateManager,
        parent_id: Optional[str] = None,
        parent: Optional[QDialog] = None
    ):
        super().__init__(parent)

        self.template_manager = template_manager
        self._parent_id = parent_id
        self._created_template_id: Optional[str] = None

        self.setWindowTitle("New Template")
        self.setMinimumWidth(400)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Title
        title = QLabel("Create New Template")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {NotionColors.TEXT_PRIMARY};
        """)
        layout.addWidget(title)

        # Name field
        name_label = QLabel("Template Name:")
        layout.addWidget(name_label)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Standard MoS2 CVD")
        layout.addWidget(self.name_input)

        # Parent selector
        parent_label = QLabel("Inherit From:")
        layout.addWidget(parent_label)
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("(None - Base Template)", None)

        for template in self.template_manager.list_templates():
            self.parent_combo.addItem(template.name, template.id)

        # Set default parent if provided
        if self._parent_id:
            for i in range(self.parent_combo.count()):
                if self.parent_combo.itemData(i) == self._parent_id:
                    self.parent_combo.setCurrentIndex(i)
                    break

        layout.addWidget(self.parent_combo)

        # Description
        desc_label = QLabel("Description (optional):")
        layout.addWidget(desc_label)
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setPlaceholderText("Brief description of this template...")
        layout.addWidget(self.desc_input)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        create_btn = QPushButton("Create")
        create_btn.setObjectName("primaryButton")
        create_btn.clicked.connect(self._on_create)
        button_layout.addWidget(create_btn)

        layout.addLayout(button_layout)

    def _on_create(self):
        """Handle create button click"""
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return

        parent_id = self.parent_combo.currentData()
        description = self.desc_input.toPlainText()

        try:
            template = self.template_manager.create_template(
                name=name,
                parent_id=parent_id,
                description=description
            )
            self._created_template_id = template.id
            self.accept()
        except ValueError as e:
            # Show error somehow
            pass

    def get_created_template_id(self) -> Optional[str]:
        """Get the ID of the created template"""
        return self._created_template_id
