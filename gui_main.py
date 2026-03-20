import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QFileDialog,
    QDockWidget, QPlainTextEdit, QLabel, QSlider, QWidget, QHBoxLayout
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

from image_view import ImageView
from tools import ToolManager
from shortcuts import register_shortcuts
from yolo_detector import YoloDetector
from items import YoloBox
from PyQt6.QtCore import QRectF

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO2 experimental")
        self.detector = YoloDetector("best.pt")

        # ---------- VIEW ----------
        self.view = ImageView()
        self.setCentralWidget(self.view)

        # ---------- LOG ----------
        self.log_panel = QPlainTextEdit()
        self.log_panel.setReadOnly(True)
        dock = QDockWidget("Log", self)
        dock.setWidget(self.log_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.log = lambda msg: self.log_panel.appendPlainText(msg)

        # ---------- TOOL MANAGER ----------
        self.tool_manager = ToolManager(self.view, log_callback=self.log)
        self.view.tool_manager = self.tool_manager
        self.tool_manager.set_tool(None)

        # ---------- TOOLBAR ----------
        tb = QToolBar("Tools")
        self.addToolBar(tb)

        def btn(name, func):
            act = QAction(name, self)
            act.triggered.connect(func)
            tb.addAction(act)

        btn("NONE", lambda: self.tool_manager.set_tool(None))
        btn("PENCIL", lambda: self.tool_manager.set_tool("PENCIL"))
        btn("ERASER", lambda: self.tool_manager.set_tool("ERASER"))
        btn("LINE", lambda: self.tool_manager.set_tool("LINE"))
        btn("POLYLINE", lambda: self.tool_manager.set_tool("POLYLINE"))
        btn("POLYCURVE", lambda: self.tool_manager.set_tool("POLYCURVE"))

        btn("UNDO", self.view.undo)
        btn("OPEN", self.open_image)
        btn("FIT", self.view.fit_image)

        # ---------- BRUSH SIZE ----------
        w = QWidget()
        l = QHBoxLayout()
        l.setContentsMargins(2,2,2,2)

        l.addWidget(QLabel("Brush"))
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(1)
        slider.setMaximum(20)
        slider.setValue(2)
        slider.valueChanged.connect(self.change_brush)

        l.addWidget(slider)
        w.setLayout(l)
        tb.addWidget(w)

        register_shortcuts(self)

    def change_brush(self, val):
        self.tool_manager.brush_size = val
        self.log(f"Brush size: {val}")

    def open_image(self):
        import cv2
        path, _ = QFileDialog.getOpenFileName(self, "Open", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        img = cv2.imread(path)
        if img is None:
            self.log("Failed to load image")
            return
        self.view.set_image(img)

        # -------- YOLO DETEKCIA --------
        detections = self.detector.detect(img)

        count = 0
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = det["label"]

            rect = QRectF(x1, y1, x2 - x1, y2 - y1)

            box = YoloBox(rect, label=label)
            self.view.scene.addItem(box)
            self.view.undo_stack.append(box)

            count += 1

        self.log(f"YOLO: {count} detections")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1300, 900)
    w.show()
    sys.exit(app.exec())