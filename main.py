#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
作文小工具 — 跨平台桌面应用 (Windows / macOS / Linux)
依赖: PyQt6
运行: python main.py
"""

import sys
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("作文小工具")
    app.setApplicationDisplayName("作文小工具")

    # 适配高分屏
    app.setStyle("Fusion")

    window = MainWindow()
    window.load_session()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
