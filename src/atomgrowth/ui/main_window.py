"""Main application window with Notion-style layout"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QStackedWidget, QSplitter, QFrame, QLineEdit,
    QStatusBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from atomgrowth.signals.app_signals import get_app_signals


class SidebarWidget(QWidget):
    """Notion-style sidebar with navigation"""

    navigation_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(220)
        self.setMaximumWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Inner container for border styling
        inner = QWidget()
        inner.setObjectName("sidebarInner")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 8, 0, 8)
        inner_layout.setSpacing(0)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setObjectName("searchBox")
        self.search_box.setPlaceholderText("Search...")
        inner_layout.addWidget(self.search_box)

        # Navigation section title
        nav_title = QLabel("WORKSPACE")
        nav_title.setObjectName("sidebarTitle")
        inner_layout.addWidget(nav_title)

        # Navigation list
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")

        # Add navigation items
        nav_items = [
            ("Templates", "templates"),
            ("Experiments", "experiments"),
            ("Samples", "samples"),
            ("Gallery", "gallery"),
        ]

        for label, key in nav_items:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, key)
            self.nav_list.addItem(item)

        self.nav_list.setCurrentRow(0)
        self.nav_list.currentItemChanged.connect(self._on_nav_changed)
        inner_layout.addWidget(self.nav_list)

        # Add stretch
        inner_layout.addStretch()

        # New item button
        self.new_btn = QPushButton("+ New")
        self.new_btn.setObjectName("newItemButton")
        inner_layout.addWidget(self.new_btn)

        layout.addWidget(inner)

    def _on_nav_changed(self, current, previous):
        if current:
            key = current.data(Qt.UserRole)
            self.navigation_changed.emit(key)
            get_app_signals().navigation_changed.emit(key)


class PlaceholderView(QWidget):
    """Placeholder view for development"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel(title)
        label.setStyleSheet("font-size: 24px; color: #9B9A97; font-weight: 500;")
        layout.addWidget(label)

        subtitle = QLabel("Coming soon...")
        subtitle.setStyleSheet("font-size: 14px; color: #B0B0B0;")
        layout.addWidget(subtitle)


class MainWindow(QMainWindow):
    """Main application window with Notion-style layout"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AtomGrowth-Notebook")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Central widget
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        # Main layout
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header bar
        header = self._create_header()
        main_layout.addWidget(header)

        # Content area with sidebar and main content
        content_area = QWidget()
        content_area.setObjectName("contentArea")
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        self.sidebar = SidebarWidget()
        self.sidebar.navigation_changed.connect(self._on_navigation_changed)
        content_layout.addWidget(self.sidebar)

        # Splitter for resizable content
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Main content stack
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentStack")

        # Add placeholder views for each section
        self.views = {
            "templates": PlaceholderView("Templates"),
            "experiments": PlaceholderView("Experiments"),
            "samples": PlaceholderView("Samples"),
            "gallery": PlaceholderView("Gallery"),
        }

        for key, view in self.views.items():
            self.content_stack.addWidget(view)

        splitter.addWidget(self.content_stack)
        content_layout.addWidget(splitter)

        main_layout.addWidget(content_area)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Connect signals
        self._connect_signals()

    def _create_header(self) -> QWidget:
        """Create the header bar"""
        header = QWidget()
        header.setObjectName("headerBar")
        header.setFixedHeight(52)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 16, 0)

        # Logo / App name
        logo_layout = QVBoxLayout()
        logo_layout.setSpacing(0)

        logo_label = QLabel("AtomGrowth-Notebook")
        logo_label.setObjectName("logoLabel")
        logo_layout.addWidget(logo_label)

        subtitle = QLabel("CVD Synthesis Manager")
        subtitle.setObjectName("logoSubtitle")
        logo_layout.addWidget(subtitle)

        layout.addLayout(logo_layout)

        # Spacer
        layout.addStretch()

        # Header buttons
        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("iconButton")
        layout.addWidget(settings_btn)

        return header

    def _connect_signals(self):
        """Connect application signals"""
        signals = get_app_signals()
        signals.status_message.connect(self._show_status_message)

    def _on_navigation_changed(self, view_name: str):
        """Handle navigation changes"""
        view_index = list(self.views.keys()).index(view_name)
        self.content_stack.setCurrentIndex(view_index)
        self.status_bar.showMessage(f"Viewing: {view_name.title()}")

    def _show_status_message(self, message: str, timeout: int):
        """Show a status bar message"""
        self.status_bar.showMessage(message, timeout)
