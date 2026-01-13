"""Application setup and initialization"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from atomgrowth.styles.theme import ThemeManager


def create_app() -> QApplication:
    """Create and configure the QApplication instance."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("AtomGrowth-Notebook")
    app.setOrganizationName("AtomGrowth")
    app.setOrganizationDomain("atomgrowth.local")

    # Apply Notion-style light theme
    ThemeManager.apply_light_theme(app)

    return app
