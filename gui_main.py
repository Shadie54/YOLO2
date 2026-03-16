#gui_main.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QFileDialog,
    QDockWidget, QPlainTextEdit
)
from PyQt6.QtGui import QKeySequence, QAction
from PyQt6.QtCore import Qt

from image_view import ImageView
from tools import ToolManager
from shortcuts import register_shortcuts


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO2 experimental")

        # ---------- Central widget ----------
        self.view = ImageView()
        self.setCentralWidget(self.view)

        # ---------- Log panel ----------
        self.log_panel = QPlainTextEdit()
        self.log_panel.setReadOnly(True)
        dock = QDockWidget("Log", self)
        dock.setWidget(self.log_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        self.log = lambda msg: self.log_panel.appendPlainText(msg)

        # ---------- Tool manager ----------
        self.tool_manager = ToolManager(self.view, log_callback=self.log)
        self.view.tool_manager = self.tool_manager

        # ---------- Toolbar ----------
        self.toolbar = QToolBar("Tools")
        self.addToolBar(self.toolbar)

        def add_action(name, key_sequence=None, tool_name=None, callback=None):
            act = QAction(name, self)
            if key_sequence:
                act.setShortcut(QKeySequence(key_sequence))
            if callback:
                act.triggered.connect(callback)
            elif tool_name:
                act.triggered.connect(lambda: self.tool_manager.set_tool(tool_name))
            self.toolbar.addAction(act)
            return act

        # Toolbar tlačidlá (bez CURVE)
        add_action("BOX", "B", tool_name="BOX")
        add_action("LINE", "L", tool_name="LINE")
        add_action("POLYLINE", "P", tool_name="POLYLINE")
        add_action("POLYCURVE", "V", tool_name="POLYCURVE")
        add_action("ERASER", "E", tool_name="ERASER")
        add_action("UNDO", "Ctrl+Z", callback=self.view.undo)
        add_action("OPEN", "O", callback=self.open_image)
        add_action("FIT IMAGE", "Space", callback=self.view.fit_image)

        # ---------- Register shortcuts ----------
        register_shortcuts(self)

        #self.view.mousePressEvent = self.tool_manager.mousePressEvent
        #self.view.mouseMoveEvent = self.tool_manager.mouseMoveEvent
        #self.view.mouseReleaseEvent = self.tool_manager.mouseReleaseEvent
        #self.view.keyPressEvent = self.tool_manager.keyPressEvent

    # ---------- Open image ----------
    def open_image(self):
        import cv2
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if not path:
            return
        img = cv2.imread(path)
        if img is None:
            self.log("Failed to load image")
            return
        self.view.set_image(img)

    # ---------- Wrappers ----------
    def wrap_mouse_event(self, original_func, tool_func):
        def wrapped(event):
            tool_func(event)
            original_func(event)
        return wrapped

    def wrap_key_event(self, original_func, tool_func):
        def wrapped(event):
            tool_func(event)
            original_func(event)
        return wrapped


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1300, 900)
    window.show()
    sys.exit(app.exec())