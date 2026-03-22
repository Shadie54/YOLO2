# utils/error_handler.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QSizePolicy, QApplication
)
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtCore import Qt
import os
import traceback
import sys

class ErrorDialog(QDialog):
    def __init__(self, error_type: str, error_msg: str, traceback_text: str):
        super().__init__()
        self.setWindowTitle(f"Error: {error_type}")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.resize(800, 500)

        # --- window icon (OS title bar) ---
        self.setWindowIcon(QIcon.fromTheme("dialog-error"))

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # --- hlavička s ikonou ---
        header_layout = QHBoxLayout()
        error_icon_label = QLabel()

        # --- bezpečné načítanie pixmapy ---
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(BASE_DIR, "assets", "icons", "error_cat.png")
        pixmap = QPixmap(icon_path)
        if pixmap.isNull():
            print(f"WARNING: Pixmap not loaded: {icon_path}")
        else:
            pixmap = pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            error_icon_label.setPixmap(pixmap)

        header_layout.addWidget(error_icon_label)

        # --- hlavička text ---
        header_label = QLabel(f"<b>{error_type}:</b> {error_msg}")
        header_label.setWordWrap(True)
        header_label.setFont(QFont("Arial", 12))
        header_label.setStyleSheet("color: #1E90FF;")  # pekná modrá farba
        header_layout.addWidget(header_label)

        layout.addLayout(header_layout)

        # --- stack trace ---
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(traceback_text)
        self.text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #dcdcdc;
                border: 1px solid #444;
                border-radius: 4px;
            }
        """)
        self.text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.text_edit)

        # --- tlačidlá ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        copy_btn = QPushButton("Copy")
        copy_btn.setToolTip("Copy full traceback to clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        btn_layout.addWidget(copy_btn)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())

# --- exception hook ---
def excepthook(exc_type, exc_value, exc_tb):
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    try:
        dlg = ErrorDialog(str(exc_type.__name__), str(exc_value), tb_text)
        dlg.exec()
    except Exception as e:
        print("Error in exception dialog:", e)
        print(tb_text)