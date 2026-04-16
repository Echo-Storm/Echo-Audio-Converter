#!/usr/bin/env python3
"""
Echo Audio Converter - Entry point
"""

import sys
import os

app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from PyQt6.QtWidgets import QApplication
from ui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Echo Audio Converter")
    app.setOrganizationName("EchoStorm")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
