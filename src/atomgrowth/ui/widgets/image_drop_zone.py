"""Image drop zone widget with thumbnail grid display"""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QMouseEvent

from atomgrowth.styles.colors import NotionColors


class ImageThumbnail(QFrame):
    """A clickable image thumbnail widget."""

    clicked = Signal(str)  # Emits image path
    delete_requested = Signal(str)  # Emits image path

    def __init__(self, image_path: str, full_path: Path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.full_path = full_path

        self.setObjectName("imageThumbnail")
        self.setFixedSize(120, 120)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(112, 90)
        layout.addWidget(self.image_label)

        # Filename label
        self.name_label = QLabel(Path(image_path).name[:15])
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet(f"font-size: 10px; color: {NotionColors.TEXT_SECONDARY};")
        layout.addWidget(self.name_label)

        # Load thumbnail
        self._load_thumbnail()

        # Apply styling
        self.setStyleSheet(f"""
            QFrame#imageThumbnail {{
                background-color: {NotionColors.BACKGROUND};
                border: 1px solid {NotionColors.BORDER};
                border-radius: 8px;
            }}
            QFrame#imageThumbnail:hover {{
                border-color: {NotionColors.PRIMARY};
                background-color: {NotionColors.BACKGROUND_HOVER};
            }}
        """)

    def _load_thumbnail(self):
        """Load and display the thumbnail."""
        if self.full_path.exists():
            pixmap = QPixmap(str(self.full_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    112, 90,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled)
            else:
                self.image_label.setText("Invalid")
        else:
            self.image_label.setText("Not found")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.image_path)
        super().mousePressEvent(event)


class ImageDropZone(QWidget):
    """
    A drop zone widget that accepts image files and displays thumbnails.

    Signals:
        images_dropped: Emitted when images are dropped (list of Path objects)
        image_clicked: Emitted when a thumbnail is clicked (image path string)
        image_delete_requested: Emitted when delete is requested (image path string)
    """

    images_dropped = Signal(list)  # List of Path objects
    image_clicked = Signal(str)    # Image path (relative)
    image_delete_requested = Signal(str)

    # Supported image formats
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.gif'}

    def __init__(self, images_dir: Optional[Path] = None, parent=None):
        super().__init__(parent)
        self.images_dir = images_dir
        self._image_paths: list[str] = []

        self.setAcceptDrops(True)
        self.setMinimumHeight(150)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Section title
        title = QLabel("Optical Images")
        title.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 600;
            color: {NotionColors.TEXT_PRIMARY};
        """)
        layout.addWidget(title)

        # Drop zone frame
        self.drop_frame = QFrame()
        self.drop_frame.setObjectName("dropZone")
        self.drop_frame.setMinimumHeight(140)
        drop_layout = QVBoxLayout(self.drop_frame)
        drop_layout.setContentsMargins(12, 12, 12, 12)

        # Placeholder (shown when no images)
        self.placeholder = QLabel("Drag & drop images here")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet(f"""
            font-size: 14px;
            color: {NotionColors.TEXT_TERTIARY};
            padding: 40px;
        """)
        drop_layout.addWidget(self.placeholder)

        # Scroll area for thumbnails
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVisible(False)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # Grid container for thumbnails
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(8)
        self.scroll_area.setWidget(self.grid_container)

        drop_layout.addWidget(self.scroll_area)

        layout.addWidget(self.drop_frame)

        # Apply drop zone styling
        self._update_drop_zone_style(False)

    def _update_drop_zone_style(self, is_drag_over: bool):
        """Update the drop zone visual style."""
        if is_drag_over:
            self.drop_frame.setStyleSheet(f"""
                QFrame#dropZone {{
                    background-color: {NotionColors.PRIMARY}15;
                    border: 2px dashed {NotionColors.PRIMARY};
                    border-radius: 8px;
                }}
            """)
        else:
            self.drop_frame.setStyleSheet(f"""
                QFrame#dropZone {{
                    background-color: {NotionColors.SIDEBAR_BG};
                    border: 2px dashed {NotionColors.BORDER};
                    border-radius: 8px;
                }}
            """)

    def set_images(self, image_paths: list[str]):
        """Set the images to display."""
        self._image_paths = image_paths
        self._refresh_thumbnails()

    def _refresh_thumbnails(self):
        """Refresh the thumbnail grid."""
        # Clear existing thumbnails
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._image_paths:
            self.placeholder.setVisible(True)
            self.scroll_area.setVisible(False)
            return

        self.placeholder.setVisible(False)
        self.scroll_area.setVisible(True)

        # Add thumbnails in a grid (3 columns)
        columns = 3
        for i, image_path in enumerate(self._image_paths):
            row = i // columns
            col = i % columns

            # Get full path
            if self.images_dir:
                full_path = self.images_dir / image_path
            else:
                full_path = Path(image_path)

            thumbnail = ImageThumbnail(image_path, full_path)
            thumbnail.clicked.connect(self.image_clicked.emit)
            self.grid_layout.addWidget(thumbnail, row, col)

        # Add spacer at the end
        self.grid_layout.setRowStretch(len(self._image_paths) // columns + 1, 1)

    # ==================== Drag and Drop ====================

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter - accept if it contains image files."""
        if event.mimeData().hasUrls():
            # Check if any URL is an image
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    path = Path(url.toLocalFile())
                    if path.suffix.lower() in self.SUPPORTED_FORMATS:
                        event.acceptProposedAction()
                        self._update_drop_zone_style(True)
                        return
        event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave - reset styling."""
        self._update_drop_zone_style(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        """Handle drop - emit signal with dropped image paths."""
        self._update_drop_zone_style(False)

        if event.mimeData().hasUrls():
            image_paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    path = Path(url.toLocalFile())
                    if path.suffix.lower() in self.SUPPORTED_FORMATS:
                        image_paths.append(path)

            if image_paths:
                event.acceptProposedAction()
                self.images_dropped.emit(image_paths)
                return

        event.ignore()
