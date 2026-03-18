# gui_main.py
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QToolBar, QFileDialog, QDockWidget, QPlainTextEdit
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

from image_view import ImageView
from tools import ToolManager
from shortcuts import register_shortcuts


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO2 experimental")

        # ---------- UI ----------
        self._setup_ui()

        # ---------- Tools ----------
        self.tool_manager = ToolManager(self.view, log_callback=self.log)
        self.view.tool_manager = self.tool_manager

        # ---------- Register shortcuts ----------
        register_shortcuts(self)

    # ---------- UI SETUP ----------
    def _setup_ui(self):
        # Central widget
        self.view = ImageView()
        self.setCentralWidget(self.view)

        # Log panel
        self.log_panel = QPlainTextEdit()
        self.log_panel.setReadOnly(True)
        dock = QDockWidget("Log", self)
        dock.setWidget(self.log_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        self.log = lambda msg: self.log_panel.appendPlainText(msg)

        # Toolbar
        self.toolbar = QToolBar("Tools")
        self.addToolBar(self.toolbar)
        self._setup_toolbar()

    # ---------- Toolbar ----------
    def _setup_toolbar(self):
        """Tool buttons (shortcuts only for B/L/P/V/E, others via QShortcut)"""
        def add_action(name, tool_name=None, callback=None):
            act = QAction(name, self)
            if callback:
                act.triggered.connect(callback)
            elif tool_name:
                act.triggered.connect(lambda: self.tool_manager.set_tool(tool_name))
            self.toolbar.addAction(act)
            return act

        # ---------- TOOL BUTTONS ----------
        add_action("BOX", tool_name="BOX")
        add_action("LINE", tool_name="LINE")
        add_action("POLYLINE", tool_name="POLYLINE")
        add_action("POLYCURVE", tool_name="POLYCURVE")
        add_action("ERASER", tool_name="ERASER")

        # ---------- ACTIONS WITHOUT TOOLBAR SHORTCUTS ----------
        add_action("UNDO", callback=lambda: self.view.undo())
        add_action("OPEN", callback=self.open_image)
        add_action("FIT IMAGE", callback=self.view.fit_image)

    # ---------- Open image ----------
    def open_image(self):
        import cv2
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        img = cv2.imread(path)
        if img is None:
            self.log("Failed to load image")
            return
        self.view.set_image(img)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1300, 900)
    window.show()
    sys.exit(app.exec())