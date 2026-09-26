from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.runtime_paths import application_dir, prepare_data_directory, resource_path


if __name__ == "__main__":
    app = QApplication(sys.argv)
    root = application_dir()
    prepare_data_directory()
    window = MainWindow(root, icon_path=resource_path("app.ico"))
    window.show()
    sys.exit(app.exec())
