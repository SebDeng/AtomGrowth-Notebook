#!/usr/bin/env python3
"""AtomGrowth-Notebook - CVD Synthesis Management Application"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from atomgrowth.app import create_app
from atomgrowth.ui.main_window import MainWindow


def main():
    """Main entry point"""
    app = create_app()

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
