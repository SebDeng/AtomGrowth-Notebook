"""Experiment list view with date/template sorting options"""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QStackedWidget, QSplitter, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from atomgrowth.core.experiment_manager import ExperimentManager
from atomgrowth.core.template_manager import TemplateManager
from atomgrowth.models.experiment import Experiment
from atomgrowth.signals.app_signals import get_app_signals
from atomgrowth.styles.colors import NotionColors
from atomgrowth.ui.views.experiment_editor import ExperimentEditorView


class ExperimentListView(QWidget):
    """
    Main view for listing and managing experiments.

    Features:
    - Toggle between date-sorted list and template-grouped tree
    - Splitter layout with list on left, editor on right
    - New experiment button
    """

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
        self._signals = get_app_signals()

        self._view_mode = "date"  # "date" or "template"

        self._setup_ui()
        self._connect_signals()
        self._refresh_list()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        # Left panel - list
        left_panel = QWidget()
        left_panel.setMinimumWidth(280)
        left_panel.setMaximumWidth(400)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # List header with view toggle
        list_header = self._create_list_header()
        left_layout.addWidget(list_header)

        # Stacked widget for different views
        self.view_stack = QStackedWidget()

        # Date-sorted list view
        self.date_list = QListWidget()
        self.date_list.setObjectName("experimentList")
        self.date_list.itemSelectionChanged.connect(self._on_date_list_selection_changed)
        self.date_list.setStyleSheet(f"""
            QListWidget#experimentList {{
                background-color: {NotionColors.SIDEBAR_BG};
                border: none;
                border-right: 1px solid {NotionColors.BORDER};
                outline: none;
            }}
            QListWidget::item {{
                padding: 12px 16px;
                border-bottom: 1px solid {NotionColors.BORDER};
            }}
            QListWidget::item:selected {{
                background-color: {NotionColors.SIDEBAR_ITEM_SELECTED};
            }}
            QListWidget::item:hover {{
                background-color: {NotionColors.BACKGROUND_HOVER};
            }}
        """)
        self.view_stack.addWidget(self.date_list)

        # Template-grouped tree view
        self.template_tree = QTreeWidget()
        self.template_tree.setObjectName("experimentTree")
        self.template_tree.setHeaderHidden(True)
        self.template_tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        self.template_tree.setStyleSheet(f"""
            QTreeWidget#experimentTree {{
                background-color: {NotionColors.SIDEBAR_BG};
                border: none;
                border-right: 1px solid {NotionColors.BORDER};
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 8px 12px;
            }}
            QTreeWidget::item:selected {{
                background-color: {NotionColors.SIDEBAR_ITEM_SELECTED};
            }}
            QTreeWidget::item:hover {{
                background-color: {NotionColors.BACKGROUND_HOVER};
            }}
        """)
        self.view_stack.addWidget(self.template_tree)

        left_layout.addWidget(self.view_stack)

        # New experiment button
        new_btn_container = QWidget()
        new_btn_container.setStyleSheet(f"""
            background-color: {NotionColors.SIDEBAR_BG};
            border-right: 1px solid {NotionColors.BORDER};
        """)
        new_btn_layout = QHBoxLayout(new_btn_container)
        new_btn_layout.setContentsMargins(12, 12, 12, 12)

        self.new_btn = QPushButton("+ New Experiment")
        self.new_btn.setCursor(Qt.PointingHandCursor)
        self.new_btn.clicked.connect(self._on_new_experiment)
        self.new_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {NotionColors.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {NotionColors.PRIMARY_HOVER};
            }}
        """)
        new_btn_layout.addWidget(self.new_btn)

        left_layout.addWidget(new_btn_container)

        splitter.addWidget(left_panel)

        # Right panel - editor
        self.editor = ExperimentEditorView(
            experiment_manager=self.experiment_manager,
            template_manager=self.template_manager,
            images_dir=self.images_dir
        )
        self.editor.experiment_saved.connect(self._refresh_list)
        splitter.addWidget(self.editor)

        # Set initial sizes (30% / 70%)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

    def _create_list_header(self) -> QWidget:
        """Create the list header with view toggle buttons."""
        header = QWidget()
        header.setStyleSheet(f"""
            background-color: {NotionColors.SIDEBAR_BG};
            border-bottom: 1px solid {NotionColors.BORDER};
            border-right: 1px solid {NotionColors.BORDER};
        """)
        header.setFixedHeight(48)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(4)

        # Title
        title = QLabel("Experiments")
        title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {NotionColors.TEXT_PRIMARY};
        """)
        layout.addWidget(title)

        layout.addStretch()

        # View toggle buttons
        self.date_btn = QPushButton("Date")
        self.date_btn.setCheckable(True)
        self.date_btn.setChecked(True)
        self.date_btn.setCursor(Qt.PointingHandCursor)
        self.date_btn.clicked.connect(lambda: self._set_view_mode("date"))

        self.template_btn = QPushButton("Template")
        self.template_btn.setCheckable(True)
        self.template_btn.setCursor(Qt.PointingHandCursor)
        self.template_btn.clicked.connect(lambda: self._set_view_mode("template"))

        toggle_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                padding: 4px 8px;
                font-size: 12px;
                color: {NotionColors.TEXT_SECONDARY};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {NotionColors.BACKGROUND_HOVER};
            }}
            QPushButton:checked {{
                background-color: {NotionColors.BACKGROUND_HOVER};
                color: {NotionColors.TEXT_PRIMARY};
                font-weight: 500;
            }}
        """
        self.date_btn.setStyleSheet(toggle_style)
        self.template_btn.setStyleSheet(toggle_style)

        layout.addWidget(self.date_btn)
        layout.addWidget(self.template_btn)

        return header

    def _connect_signals(self):
        """Connect to app signals."""
        self._signals.experiment_created.connect(self._refresh_list)
        self._signals.experiment_modified.connect(self._refresh_list)
        self._signals.experiment_deleted.connect(self._refresh_list)

    def _set_view_mode(self, mode: str):
        """Switch between date and template view modes."""
        self._view_mode = mode
        self.date_btn.setChecked(mode == "date")
        self.template_btn.setChecked(mode == "template")

        if mode == "date":
            self.view_stack.setCurrentWidget(self.date_list)
        else:
            self.view_stack.setCurrentWidget(self.template_tree)

        self._refresh_list()

    def _refresh_list(self):
        """Refresh the experiment list/tree."""
        if self._view_mode == "date":
            self._refresh_date_list()
        else:
            self._refresh_template_tree()

    def _refresh_date_list(self):
        """Refresh the date-sorted list."""
        self.date_list.clear()

        experiments = self.experiment_manager.list_experiments_by_date()

        for exp in experiments:
            # Format: "Name - Date"
            date_str = exp.created_at[:10] if exp.created_at else ""
            item = QListWidgetItem(f"{exp.name}\n{date_str}")
            item.setData(Qt.UserRole, exp.id)
            self.date_list.addItem(item)

    def _refresh_template_tree(self):
        """Refresh the template-grouped tree."""
        self.template_tree.clear()

        grouped = self.experiment_manager.list_experiments_by_template()

        for template_id, experiments in grouped.items():
            # Get template name
            template = self.template_manager.get_template(template_id)
            template_name = template.name if template else "Unknown Template"

            # Create template parent item
            parent_item = QTreeWidgetItem([f"{template_name} ({len(experiments)})"])
            parent_item.setData(0, Qt.UserRole, None)  # No experiment ID for parent
            parent_item.setExpanded(True)

            # Add experiments as children
            for exp in experiments:
                date_str = exp.created_at[:10] if exp.created_at else ""
                child_item = QTreeWidgetItem([f"{exp.name} - {date_str}"])
                child_item.setData(0, Qt.UserRole, exp.id)
                parent_item.addChild(child_item)

            self.template_tree.addTopLevelItem(parent_item)

    def _on_date_list_selection_changed(self):
        """Handle selection change in date list."""
        items = self.date_list.selectedItems()
        if items:
            experiment_id = items[0].data(Qt.UserRole)
            if experiment_id:
                self.editor.load_experiment(experiment_id)
                self._signals.experiment_selected.emit(experiment_id)

    def _on_tree_selection_changed(self):
        """Handle selection change in template tree."""
        items = self.template_tree.selectedItems()
        if items:
            experiment_id = items[0].data(0, Qt.UserRole)
            if experiment_id:
                self.editor.load_experiment(experiment_id)
                self._signals.experiment_selected.emit(experiment_id)
            else:
                # Template parent selected, clear editor
                self.editor.clear()

    def _on_new_experiment(self):
        """Handle new experiment button click."""
        from atomgrowth.ui.dialogs.new_experiment_dialog import NewExperimentDialog

        dialog = NewExperimentDialog(
            template_manager=self.template_manager,
            parent=self
        )

        if dialog.exec():
            template_id = dialog.get_selected_template_id()
            name = dialog.get_experiment_name()

            if template_id and name:
                try:
                    experiment = self.experiment_manager.create_experiment(
                        name=name,
                        template_id=template_id
                    )
                    self.experiment_manager.save()
                    self._refresh_list()
                    self.editor.load_experiment(experiment.id)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to create experiment: {e}")
