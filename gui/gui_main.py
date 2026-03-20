# gui/gui_main.py
import sys, os, cv2
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QFileDialog,
    QDockWidget, QPlainTextEdit, QLabel, QSlider, QWidget, QHBoxLayout,

)
from PyQt6.QtGui import QIcon, QImage, QPainter,QAction, QActionGroup
from PyQt6.QtCore import Qt, QSize

from gui.image_view import ImageView
from gui.shortcuts import register_shortcuts
from tools.tool_manager import ToolManager
from yolo.yolo_detector import YoloDetector
from items.items import YoloBox, BezierPoint


def icon(path):
    return QIcon(path) if os.path.exists(path) else QIcon()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO2 experimental")
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ICON_DIR = os.path.join(BASE_DIR, "assets", "icons")
        MODEL_PATH = os.path.join(BASE_DIR, "models", "best.pt")

        # ---------- YOLO DETECTOR ----------
        self.detector = YoloDetector(MODEL_PATH)

        # ---------- VIEW ----------
        self.view = ImageView()
        self.setCentralWidget(self.view)

        # ---------- LOG ----------
        self.log_panel = QPlainTextEdit()
        self.log_panel.setReadOnly(True)
        dock_log = QDockWidget("Log", self)
        dock_log.setWidget(self.log_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_log)
        self.log = lambda msg: self.log_panel.appendPlainText(msg)

        # ---------- TOOL MANAGER ----------
        self.tool_manager = ToolManager(self.view, log_callback=self.log)
        self.view.tool_manager = self.tool_manager
        self.tool_manager.set_tool(None)

        # ---------- PANELS ----------

        # Actions panel: Open Folder, Settings, YOLO, Save
        actions_tb = QToolBar("Actions")
        actions_tb.setIconSize(QSize(48, 48))
        actions_tb.setMovable(True)
        actions_tb.setFloatable(True)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, actions_tb)

        open_folder_act = QAction(icon(os.path.join(ICON_DIR, "open.png")), "Open Folder", self)
        open_folder_act.triggered.connect(self.open_folder)
        actions_tb.addAction(open_folder_act)

        settings_act = QAction(icon(os.path.join(ICON_DIR, "settings.png")), "Settings", self)
        settings_act.triggered.connect(lambda: self.log("Settings clicked"))
        actions_tb.addAction(settings_act)

        yolo_act = QAction(icon(os.path.join(ICON_DIR, "yolo.png")), "YOLO Detect", self)
        yolo_act.triggered.connect(lambda: self.log("YOLO Detect clicked"))
        actions_tb.addAction(yolo_act)

        save_act = QAction(icon(os.path.join(ICON_DIR, "save.png")), "Save", self)
        save_act.triggered.connect(self.save_image)
        actions_tb.addAction(save_act)

        # ---------- Draw Tools panel ----------
        draw_tb = QToolBar("Draw Tools")
        draw_tb.setIconSize(QSize(48, 48))
        draw_tb.setMovable(True)
        draw_tb.setFloatable(True)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, draw_tb)

        tool_group = QActionGroup(self)
        tool_group.setExclusive(True)

        def tool_btn(icon_name, label, tool_name=None, shortcut=None, func=None):
            act = QAction(icon(os.path.join(ICON_DIR, icon_name)), label, self)
            act.setCheckable(True)
            if func:
                act.triggered.connect(func)
            elif tool_name is not None:
                act.triggered.connect(lambda: self.tool_manager.set_tool(tool_name))
            else:
                act.triggered.connect(lambda: self.tool_manager.set_tool(None))
            if shortcut:
                act.setToolTip(f"{label} ({shortcut})")
            tool_group.addAction(act)
            draw_tb.addAction(act)
            return act

        tool_btn("mouse.png", "None", None)
        tool_btn("pencil.png", "Pencil", "PENCIL", "C")
        tool_btn("line.png", "Line", "LINE", "L")
        tool_btn("polyline.png", "Polyline", "POLYLINE", "P")
        tool_btn("polycurve.png", "Polycurve", "POLYCURVE", "V")
        tool_btn("text.png", "Text", None)

        fit_act = QAction(icon(os.path.join(ICON_DIR, "fit_zoom.png")), "Fit Image", self)
        fit_act.triggered.connect(self.view.fit_image)
        draw_tb.addAction(fit_act)

        undo_act = QAction(icon(os.path.join(ICON_DIR, "undo.png")), "Undo", self)
        undo_act.triggered.connect(self.view.undo)
        draw_tb.addAction(undo_act)

        tool_group.actions()[0].setChecked(True)

        # ---------- Brush Panel ----------
        brush_tb = QToolBar("Brush")
        brush_tb.setIconSize(QSize(48, 48))
        brush_tb.setMovable(True)
        brush_tb.setFloatable(True)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, brush_tb)

        # Slider widget
        brush_widget = QWidget()
        brush_layout = QHBoxLayout()
        brush_layout.setContentsMargins(2, 2, 2, 2)

        self.brush_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_slider.setMinimum(1)
        self.brush_slider.setMaximum(20)
        self.brush_slider.setValue(2)

        # Plávajúci indikátor
        self.brush_indicator = QLabel("", self)
        self.brush_indicator.setStyleSheet(
            "background-color: rgba(0,0,0,180); color: white; font-weight: bold; padding: 2px; border-radius: 4px;"
        )
        self.brush_indicator.setVisible(False)

        def show_brush_indicator(val):
            self.tool_manager.brush_size = val

            slider_geo = self.brush_slider.geometry()
            global_pos = self.brush_slider.mapToGlobal(slider_geo.topLeft())
            local_pos = self.mapFromGlobal(global_pos)

            if self.brush_slider.orientation() == Qt.Orientation.Horizontal:
                x = local_pos.x() + int((val-1)/(self.brush_slider.maximum()-1) * slider_geo.width()) - 15
                y = local_pos.y() - 30
            else:
                x = local_pos.x() + slider_geo.width() + 10
                y = local_pos.y() + slider_geo.height() - int((val-1)/(self.brush_slider.maximum()-1) * slider_geo.height()) - 15

            self.brush_indicator.setText(str(val))
            self.brush_indicator.move(x, y)
            self.brush_indicator.adjustSize()
            self.brush_indicator.setVisible(True)

        def hide_brush_indicator():
            self.brush_indicator.setVisible(False)

        self.brush_slider.valueChanged.connect(show_brush_indicator)
        self.brush_slider.sliderReleased.connect(hide_brush_indicator)

        brush_layout.addWidget(self.brush_slider)
        brush_widget.setLayout(brush_layout)
        brush_tb.addWidget(brush_widget)

        def update_brush_orientation():
            if brush_tb.orientation() == Qt.Orientation.Horizontal:
                self.brush_slider.setOrientation(Qt.Orientation.Horizontal)
            else:
                self.brush_slider.setOrientation(Qt.Orientation.Vertical)
        brush_tb.orientationChanged.connect(update_brush_orientation)
        update_brush_orientation()

        # ---------- Shortcuts ----------
        register_shortcuts(self)

        # ---------- Navigation Panel ----------
        nav_tb = QToolBar("Navigation")
        nav_tb.setIconSize(QSize(48, 48))
        nav_tb.setMovable(True)
        nav_tb.setFloatable(True)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, nav_tb)

        self.nav_label = QLabel("0/0")
        prev_act = QAction(icon(os.path.join(ICON_DIR, "left.png")), "Previous", self)
        next_act = QAction(icon(os.path.join(ICON_DIR, "right.png")), "Next", self)
        prev_act.triggered.connect(self.go_previous_image)
        next_act.triggered.connect(self.go_next_image)
        nav_tb.addAction(prev_act)
        nav_tb.addWidget(self.nav_label)
        nav_tb.addAction(next_act)

    # ---------- Open Folder ----------
    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", "")
        if not folder:
            return

        self.image_list = sorted([
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ])
        if not self.image_list:
            self.log("No images found in folder")
            return

        self.current_image_idx = 0
        self.show_current_image()
        self.log(f"Opened folder: {folder} ({len(self.image_list)} images)")

    # ---------- Show Image ----------
    def show_current_image(self):
        if not hasattr(self, "image_list") or not self.image_list:
            return
        path = self.image_list[self.current_image_idx]
        img = cv2.imread(path)
        if img is None:
            self.log(f"Failed to load image: {path}")
            return
        self.view.set_image(img)
        self.nav_label.setText(f"{self.current_image_idx+1}/{len(self.image_list)}")

    # ---------- Navigation ----------
    def go_previous_image(self):
        if hasattr(self, "current_image_idx") and self.current_image_idx > 0:
            self.current_image_idx -= 1
            self.show_current_image()

    def go_next_image(self):
        if hasattr(self, "current_image_idx") and self.current_image_idx < len(self.image_list)-1:
            self.current_image_idx += 1
            self.show_current_image()

    # ---------- Save ----------
    def save_image(self):
        if not hasattr(self, "image_list") or not self.image_list:
            self.log("No image to save")
            return

        path = self.image_list[self.current_image_idx]
        folder = os.path.dirname(path)
        base_folder = os.path.basename(folder)
        save_folder = os.path.join(folder, base_folder)
        os.makedirs(save_folder, exist_ok=True)

        img_rect = self.view.scene.sceneRect()
        image = QImage(int(img_rect.width()), int(img_rect.height()), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.white)
        painter = QPainter(image)
        self.view.scene.render(painter)
        painter.end()

        base_name = os.path.basename(path)
        save_path = os.path.join(save_folder, base_name)
        image.save(save_path)
        self.log(f"Saved annotated image to {save_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1300, 900)
    w.show()
    sys.exit(app.exec())