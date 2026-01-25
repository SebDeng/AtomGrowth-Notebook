"""Image preview dialog for viewing images in full size"""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QKeyEvent

from atomgrowth.styles.colors import NotionColors


class ImagePreviewDialog(QDialog):
    """
    A dialog for previewing images in full size with navigation.

    Features:
    - Full size image display (scaled to fit)
    - Left/right navigation between images
    - Keyboard navigation (arrow keys)
    - Image info display (filename)
    """

    def __init__(
        self,
        image_paths: list[str],
        images_dir: Optional[Path] = None,
        initial_index: int = 0,
        parent=None
    ):
        super().__init__(parent)
        self.image_paths = image_paths
        self.images_dir = images_dir
        self.current_index = initial_index

        self.setWindowTitle("Image Preview")
        self.setMinimumSize(800, 600)
        self.resize(1000, 750)
        self.setModal(True)

        self._setup_ui()
        self._load_current_image()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with filename and close button
        header = QWidget()
        header.setStyleSheet(f"""
            background-color: {NotionColors.SIDEBAR_BG};
            border-bottom: 1px solid {NotionColors.BORDER};
        """)
        header.setFixedHeight(48)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        self.filename_label = QLabel()
        self.filename_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 500;
            color: {NotionColors.TEXT_PRIMARY};
        """)
        header_layout.addWidget(self.filename_label)

        header_layout.addStretch()

        # Image counter
        self.counter_label = QLabel()
        self.counter_label.setStyleSheet(f"""
            font-size: 13px;
            color: {NotionColors.TEXT_SECONDARY};
        """)
        header_layout.addWidget(self.counter_label)

        layout.addWidget(header)

        # Image area
        image_container = QWidget()
        image_container.setStyleSheet(f"background-color: {NotionColors.BACKGROUND};")
        image_layout = QHBoxLayout(image_container)
        image_layout.setContentsMargins(16, 16, 16, 16)

        # Left navigation button
        self.prev_btn = QPushButton("<")
        self.prev_btn.setFixedSize(40, 40)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.clicked.connect(self._show_previous)
        self.prev_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {NotionColors.SIDEBAR_BG};
                border: 1px solid {NotionColors.BORDER};
                border-radius: 20px;
                font-size: 18px;
                font-weight: bold;
                color: {NotionColors.TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                background-color: {NotionColors.BACKGROUND_HOVER};
                color: {NotionColors.TEXT_PRIMARY};
            }}
            QPushButton:disabled {{
                color: {NotionColors.BORDER};
            }}
        """)
        image_layout.addWidget(self.prev_btn)

        # Scrollable image area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignCenter)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollArea > QWidget > QWidget { background: transparent; }
        """)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")
        scroll.setWidget(self.image_label)

        image_layout.addWidget(scroll, 1)

        # Right navigation button
        self.next_btn = QPushButton(">")
        self.next_btn.setFixedSize(40, 40)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.clicked.connect(self._show_next)
        self.next_btn.setStyleSheet(self.prev_btn.styleSheet())
        image_layout.addWidget(self.next_btn)

        layout.addWidget(image_container, 1)

        # Footer with actions
        footer = QWidget()
        footer.setStyleSheet(f"""
            background-color: {NotionColors.SIDEBAR_BG};
            border-top: 1px solid {NotionColors.BORDER};
        """)
        footer.setFixedHeight(56)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 0, 16, 0)

        footer_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setObjectName("primaryButton")
        close_btn.setFixedSize(100, 36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet(f"""
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
        footer_layout.addWidget(close_btn)

        layout.addWidget(footer)

    def _load_current_image(self):
        """Load and display the current image."""
        if not self.image_paths:
            self.image_label.setText("No images")
            return

        image_path = self.image_paths[self.current_index]

        # Get full path
        if self.images_dir:
            full_path = self.images_dir / image_path
        else:
            full_path = Path(image_path)

        # Update labels
        self.filename_label.setText(Path(image_path).name)
        self.counter_label.setText(f"{self.current_index + 1} / {len(self.image_paths)}")

        # Load image
        if full_path.exists():
            pixmap = QPixmap(str(full_path))
            if not pixmap.isNull():
                # Scale to fit while maintaining aspect ratio
                # Get available size (approximate)
                max_width = self.width() - 150
                max_height = self.height() - 150

                scaled = pixmap.scaled(
                    max_width, max_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled)
            else:
                self.image_label.setText("Failed to load image")
        else:
            self.image_label.setText(f"File not found:\n{full_path}")

        # Update button states
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.image_paths) - 1)

    def _show_previous(self):
        """Show the previous image."""
        if self.current_index > 0:
            self.current_index -= 1
            self._load_current_image()

    def _show_next(self):
        """Show the next image."""
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self._load_current_image()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard navigation."""
        if event.key() == Qt.Key_Left:
            self._show_previous()
        elif event.key() == Qt.Key_Right:
            self._show_next()
        elif event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        """Reload image on resize to fit new size."""
        super().resizeEvent(event)
        self._load_current_image()
