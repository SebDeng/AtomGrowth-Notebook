"""Template list view with tree hierarchy"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QMenu, QMessageBox, QSplitter
)
from PySide6.QtCore import Signal, Qt

from atomgrowth.core.template_manager import TemplateManager
from atomgrowth.models.recipe import RecipeTemplate
from atomgrowth.ui.views.template_editor import TemplateEditorView
from atomgrowth.styles.colors import NotionColors
from atomgrowth.signals.app_signals import get_app_signals


class TemplateListView(QWidget):
    """
    Template list with tree hierarchy showing inheritance.
    Combined with editor in a split view.
    """

    def __init__(self, template_manager: TemplateManager, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.template_manager = template_manager
        self._signals = get_app_signals()

        self._setup_ui()
        self._connect_signals()
        self._refresh_tree()

    def _setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)

        # Splitter for list + editor
        splitter = QSplitter(Qt.Horizontal)

        # Left panel: Template list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 8, 0)

        # Header
        header = QHBoxLayout()
        title = QLabel("Templates")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {NotionColors.TEXT_PRIMARY};
        """)
        header.addWidget(title)
        header.addStretch()

        # New template button
        new_btn = QPushButton("+ New Template")
        new_btn.setObjectName("primaryButton")
        new_btn.clicked.connect(self._on_new_template)
        header.addWidget(new_btn)

        left_layout.addLayout(header)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {NotionColors.BACKGROUND};
                border: 1px solid {NotionColors.BORDER};
                border-radius: 8px;
            }}
            QTreeWidget::item {{
                padding: 8px 12px;
                border-radius: 6px;
            }}
            QTreeWidget::item:hover {{
                background-color: {NotionColors.BACKGROUND_HOVER};
            }}
            QTreeWidget::item:selected {{
                background-color: {NotionColors.SIDEBAR_ITEM_SELECTED};
                color: {NotionColors.PRIMARY};
            }}
        """)
        left_layout.addWidget(self.tree)

        splitter.addWidget(left_panel)

        # Right panel: Editor
        self.editor = TemplateEditorView(self.template_manager)
        self.editor.template_saved.connect(self._on_template_saved)
        splitter.addWidget(self.editor)

        # Set splitter sizes (30% list, 70% editor)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

    def _connect_signals(self):
        """Connect application signals"""
        self._signals.template_created.connect(self._refresh_tree)
        self._signals.template_modified.connect(self._refresh_tree)
        self._signals.template_deleted.connect(self._refresh_tree)

    def _refresh_tree(self):
        """Refresh the template tree"""
        self.tree.clear()

        # Build tree from root templates
        root_templates = self.template_manager.get_root_templates()

        for template in root_templates:
            item = self._create_tree_item(template)
            self.tree.addTopLevelItem(item)
            self._add_children(item, template.id)

        self.tree.expandAll()

    def _create_tree_item(self, template: RecipeTemplate) -> QTreeWidgetItem:
        """Create a tree item for a template"""
        item = QTreeWidgetItem([template.name])
        item.setData(0, Qt.UserRole, template.id)

        # Add child count indicator
        children = self.template_manager.get_children(template.id)
        if children:
            item.setText(0, f"{template.name} ({len(children)})")

        return item

    def _add_children(self, parent_item: QTreeWidgetItem, parent_id: str):
        """Recursively add child templates"""
        children = self.template_manager.get_children(parent_id)

        for child in children:
            item = self._create_tree_item(child)
            parent_item.addChild(item)
            self._add_children(item, child.id)

    def _show_context_menu(self, position):
        """Show context menu for template item"""
        item = self.tree.itemAt(position)
        if not item:
            return

        template_id = item.data(0, Qt.UserRole)
        template = self.template_manager.get_template(template_id)
        if not template:
            return

        menu = QMenu(self)

        # Edit action
        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(lambda: self._on_edit_template(template_id))

        # New child action
        new_child_action = menu.addAction("New Child Template")
        new_child_action.triggered.connect(lambda: self._on_new_child(template_id))

        menu.addSeparator()

        # Delete action
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self._on_delete_template(template_id))

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def _on_selection_changed(self):
        """Handle tree selection change"""
        items = self.tree.selectedItems()
        if items:
            template_id = items[0].data(0, Qt.UserRole)
            self.editor.load_template(template_id)
            self._signals.template_selected.emit(template_id)

    def _on_new_template(self):
        """Create a new root template"""
        self.editor.new_template()

    def _on_new_child(self, parent_id: str):
        """Create a new child template"""
        self.editor.new_template(parent_id)

    def _on_edit_template(self, template_id: str):
        """Edit an existing template"""
        self.editor.load_template(template_id)

    def _on_delete_template(self, template_id: str):
        """Delete a template"""
        template = self.template_manager.get_template(template_id)
        if not template:
            return

        # Confirm deletion
        result = QMessageBox.question(
            self,
            "Delete Template",
            f"Are you sure you want to delete '{template.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if result == QMessageBox.Yes:
            try:
                self.template_manager.delete_template(template_id)
                self._refresh_tree()
            except ValueError as e:
                QMessageBox.warning(self, "Cannot Delete", str(e))

    def _on_template_saved(self, template_id: str):
        """Handle template saved"""
        self._refresh_tree()

        # Select the saved template in tree
        self._select_template_in_tree(template_id)

    def _select_template_in_tree(self, template_id: str):
        """Select a template in the tree by ID"""
        def find_item(parent_item, tid):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                if child.data(0, Qt.UserRole) == tid:
                    return child
                found = find_item(child, tid)
                if found:
                    return found
            return None

        # Search top level items
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == template_id:
                self.tree.setCurrentItem(item)
                return
            found = find_item(item, template_id)
            if found:
                self.tree.setCurrentItem(found)
                return
