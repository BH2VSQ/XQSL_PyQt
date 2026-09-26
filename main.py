from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from app.main_window import MainWindow


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    app = QApplication(sys.argv)
    window = MainWindow(root)
    window.show()
    sys.exit(app.exec())
