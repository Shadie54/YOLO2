import sys, os, cv2, traceback
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QFileDialog,
    QDockWidget, QPlainTextEdit, QLabel, QSlider, QWidget,
    QHBoxLayout,QVBoxLayout, QFontComboBox, QSpinBox, QPushButton
)
from PyQt6.QtGui import QIcon, QImage, QPainter, QAction, QActionGroup, QFont
from PyQt6.QtCore import Qt, QSize, QRectF
from gui.image_view import ImageView
from gui.shortcuts import register_shortcuts
from tools.tool_manager import ToolManager
from items.items import YoloBox

from utils.error_handler import excepthook
sys.excepthook = excepthook  # <<< tu ho nastavíš, pred MainWindow

def icon(path):
    return QIcon(path) if os.path.exists(path) else QIcon()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO2 experimental")
        # ---------- Directories ----------
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ICON_DIR = os.path.join(BASE_DIR, "assets", "icons")
        MODEL_PATH = os.path.join(BASE_DIR, "models", "best.pt")

        # ---------- YOLO Detector ----------
        from yolo.yolo_detector import YoloDetector
        self.detector = YoloDetector(MODEL_PATH)

        # ---------- Central View ----------
        self.view = ImageView()
        self.setCentralWidget(self.view)

        # ---------- Log Panel ----------
        self.log_panel = QPlainTextEdit()
        self.log_panel.setReadOnly(True)
        dock_log = QDockWidget("Log", self)
        dock_log.setWidget(self.log_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_log)
        self.log = lambda msg: self.log_panel.appendPlainText(msg)

        # ---------- Tool Manager ----------
        self.tool_manager = ToolManager(self.view, log_callback=self.log)
        self.view.tool_manager = self.tool_manager
        self.tool_manager.set_tool(None)

        # ---------- Icon Size ----------
        ICON_SIZE = QSize(48, 48)

        # ---------- Toolbars ----------
        self.init_actions_toolbar(ICON_DIR, ICON_SIZE)
        self.init_draw_toolbar(ICON_DIR, ICON_SIZE)
        self.init_brush_toolbar(ICON_SIZE)
        self.init_navigation_toolbar(ICON_DIR, ICON_SIZE)

        # ---------- Text Tool Panel ----------
        self.init_text_panel()

        # ---------- Shortcuts ----------
        register_shortcuts(self)

    # ============================
    # Initialization of Toolbars
    # ============================
    def init_actions_toolbar(self, ICON_DIR, ICON_SIZE):
        actions_tb = QToolBar("Actions")
        actions_tb.setIconSize(ICON_SIZE)
        actions_tb.setMovable(True)
        actions_tb.setFloatable(True)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, actions_tb)

        # --- Open Folder ---
        open_folder_act = QAction(icon(os.path.join(ICON_DIR, "open.png")), "Open Folder", self)
        open_folder_act.setToolTip("Open Folder (Ctrl+O)")
        open_folder_act.triggered.connect(self.open_folder)
        actions_tb.addAction(open_folder_act)

        # --- Settings ---
        settings_act = QAction(icon(os.path.join(ICON_DIR, "settings.png")), "Settings", self)
        settings_act.setToolTip("Settings")
        settings_act.triggered.connect(lambda: self.log("Settings clicked"))
        actions_tb.addAction(settings_act)

        # --- YOLO ---
        self.yolo_auto = False
        yolo_icon_path = os.path.join(ICON_DIR, "yolo.png")
        yolo_auto_icon_path = os.path.join(ICON_DIR, "yolo_auto.png")
        yolo_act = QAction(icon(yolo_icon_path), "YOLO Detect", self)
        yolo_act.setToolTip("YOLO Detect / Auto toggle")
        actions_tb.addAction(yolo_act)

        def toggle_yolo():
            self.yolo_auto = not self.yolo_auto
            if self.yolo_auto:
                yolo_act.setIcon(icon(yolo_auto_icon_path))
                self.log("YOLO auto ON")
                if hasattr(self, "image_list") and self.image_list:
                    self.run_yolo_on_current_image()
            else:
                yolo_act.setIcon(icon(yolo_icon_path))
                self.log("YOLO auto OFF")
        yolo_act.triggered.connect(toggle_yolo)

        # --- Save ---
        save_act = QAction(icon(os.path.join(ICON_DIR, "save.png")), "Save", self)
        save_act.setToolTip("Save annotated image")
        save_act.triggered.connect(self.save_image)
        actions_tb.addAction(save_act)

    def init_draw_toolbar(self, ICON_DIR, ICON_SIZE):
        draw_tb = QToolBar("Draw Tools")
        draw_tb.setIconSize(ICON_SIZE)
        draw_tb.setMovable(True)
        draw_tb.setFloatable(True)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, draw_tb)

        self.tool_actions = {}
        tool_group = QActionGroup(self)
        tool_group.setExclusive(True)

        def tool_btn(icon_name, label, tool_name=None, func=None, tooltip=None):
            act = QAction(icon(os.path.join(ICON_DIR, icon_name)), label, self)
            act.setCheckable(True)
            if func:
                act.triggered.connect(func)
            elif tool_name:
                def wrapper():
                    self.tool_manager.set_tool(tool_name)
                    for a in tool_group.actions():
                        a.setChecked(a == act)
                    self.update_text_panel_visibility(tool_name)
                act.triggered.connect(wrapper)
            else:
                act.triggered.connect(lambda: self.tool_manager.set_tool(None))
            if tooltip:
                act.setToolTip(tooltip)
            tool_group.addAction(act)
            draw_tb.addAction(act)
            self.tool_actions[label] = act
            return act

        # --- Tool buttons ---
        tool_btn("mouse.png", "None", None, tooltip="Select/Move (None)")
        tool_btn("pencil.png", "Pencil", "PENCIL", tooltip="Pencil (C)")
        tool_btn("line.png", "Line", "LINE", tooltip="Line (L)")
        tool_btn("polyline.png", "Polyline", "POLYLINE", tooltip="Polyline (P)")
        tool_btn("polycurve.png", "Polycurve", "POLYCURVE", tooltip="Polycurve (V)")
        tool_btn("eraser.png", "Eraser", "ERASER", tooltip="Guma (E)")
        tool_btn("text.png", "Text", "TEXT", tooltip="Text (T)")

        # --- Undo ---
        undo_act = QAction(icon(os.path.join(ICON_DIR, "undo.png")), "Undo", self)
        undo_act.setToolTip("Undo last action (Ctrl+Z)")
        undo_act.triggered.connect(self.view.undo)
        draw_tb.addAction(undo_act)

    def init_brush_toolbar(self, ICON_SIZE):
        brush_tb = QToolBar("Brush")
        brush_tb.setIconSize(ICON_SIZE)
        brush_tb.setMovable(True)
        brush_tb.setFloatable(True)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, brush_tb)

        brush_widget = QWidget()
        brush_layout = QHBoxLayout()  # default horizontal

        # ak je toolbar vertikálny, použijeme vertical layout
        if brush_tb.orientation() == Qt.Orientation.Vertical:
            brush_layout = QVBoxLayout()
            brush_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        brush_layout.setContentsMargins(2, 2, 2, 2)

        self.brush_slider = QSlider(Qt.Orientation.Horizontal)
        if brush_tb.orientation() == Qt.Orientation.Vertical:
            self.brush_slider.setOrientation(Qt.Orientation.Vertical)

        self.brush_slider.setMinimum(1)
        self.brush_slider.setMaximum(20)
        self.brush_slider.setValue(self.tool_manager.brush_size)

        self.brush_indicator = QLabel(str(self.brush_slider.value()), self)
        self.brush_indicator.setStyleSheet(
            "background-color: rgba(0,0,0,180); color: white; font-weight: bold; padding: 2px; border-radius: 4px;"
        )
        self.brush_indicator.setVisible(True)
        self.brush_slider.valueChanged.connect(self._on_brush_changed)

        brush_layout.addWidget(self.brush_slider)
        brush_layout.addWidget(self.brush_indicator)
        brush_widget.setLayout(brush_layout)
        brush_tb.addWidget(brush_widget)

    def init_navigation_toolbar(self, ICON_DIR, ICON_SIZE):
        nav_tb = QToolBar("Navigation")
        nav_tb.setIconSize(ICON_SIZE)
        nav_tb.setMovable(True)
        nav_tb.setFloatable(True)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, nav_tb)

        self.nav_label = QLabel("0/0")
        prev_act = QAction(icon(os.path.join(ICON_DIR, "left.png")), "Previous", self)
        next_act = QAction(icon(os.path.join(ICON_DIR, "right.png")), "Next", self)
        prev_act.triggered.connect(self.go_previous_image)
        next_act.triggered.connect(self.go_next_image)
        nav_tb.addAction(prev_act)
        nav_tb.addWidget(self.nav_label)
        nav_tb.addAction(next_act)

    # ============================
    # Text Tool Panel
    # ============================
    def init_text_panel(self):
        self.text_panel = QWidget(self, flags=Qt.WindowType.Tool)
        self.text_panel.setWindowTitle("Text Tool")
        self.text_panel.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.text_panel.setVisible(False)

        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # --- Font/Size/Style ---
        self.font_box = QFontComboBox()
        self.font_box.setCurrentFont(QFont("Arial"))
        self.size_box = QSpinBox()
        self.size_box.setRange(6, 200)
        self.size_box.setValue(25)
        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        self.color_btn = QPushButton("Color")

        for w in [self.font_box, self.size_box, self.bold_btn, self.italic_btn, self.color_btn]:
            layout.addWidget(w)
        self.text_panel.setLayout(layout)

        # --- Connect to TextTool ---
        self.font_box.currentFontChanged.connect(
            lambda f: self.tool_manager.current_tool_obj.set_font(f) if self.tool_manager.current_tool_obj else None
        )
        self.size_box.valueChanged.connect(
            lambda s: self.tool_manager.current_tool_obj.set_size(s) if self.tool_manager.current_tool_obj else None
        )
        self.bold_btn.clicked.connect(
            lambda: self.tool_manager.current_tool_obj.set_bold(
                self.bold_btn.isChecked()) if self.tool_manager.current_tool_obj else None
        )
        self.italic_btn.clicked.connect(
            lambda: self.tool_manager.current_tool_obj.set_italic(
                self.italic_btn.isChecked()) if self.tool_manager.current_tool_obj else None
        )
        self.color_btn.clicked.connect(
            lambda: self.tool_manager.current_tool_obj.set_color() if self.tool_manager.current_tool_obj else None
        )

        # --- Drag panel ---
        self.text_panel.mousePressEvent = self.mousePressEventTextPanel
        self.text_panel.mouseMoveEvent = self.mouseMoveEventTextPanel
        self.text_panel.mouseReleaseEvent = self.mouseReleaseEventTextPanel

    def update_text_panel_visibility(self, tool_name):
        if tool_name == "TEXT":
            self.text_panel.setVisible(True)
            offset_y = 100  # upraviteľná pozícia
            center_x = self.view.geometry().left() + self.view.width() // 2 - self.text_panel.width() // 2
            self.text_panel.move(center_x, self.view.geometry().top() + offset_y)
        else:
            self.text_panel.setVisible(False)

    # ============================
    # Image Folder / Navigation
    # ============================
    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", "")
        if not folder:
            return
        self.image_list = sorted(
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        )
        if not self.image_list:
            self.log("No images found in folder")
            return
        self.current_image_idx = 0
        self.show_current_image()
        self.log(f"Opened folder: {folder} ({len(self.image_list)} images)")

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
        if self.yolo_auto:
            self.run_yolo_on_current_image()

    def go_previous_image(self):
        if hasattr(self, "current_image_idx") and self.current_image_idx > 0:
            self.current_image_idx -= 1
            self.show_current_image()

    def go_next_image(self):
        if hasattr(self, "current_image_idx") and self.current_image_idx < len(self.image_list)-1:
            self.current_image_idx += 1
            self.show_current_image()

    # ============================
    # Save Image
    # ============================
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

        save_path = os.path.join(save_folder, os.path.basename(path))
        ext = os.path.splitext(save_path)[1].lower()
        if ext in [".jpg", ".jpeg"]:
            image.save(save_path, "JPEG", quality=100)
        else:
            image.save(save_path)
        self.log(f"Saved annotated image to {save_path}")

    # ============================
    # YOLO Detection
    # ============================
    def run_yolo_on_current_image(self):
        if not hasattr(self, "image_list") or not self.image_list:
            return
        path = self.image_list[self.current_image_idx]
        img = cv2.imread(path)
        if img is None:
            self.log(f"Failed to load image: {path}")
            return

        detections = self.detector.detect(img)
        count = 0
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = det["label"]

            # --- rozšírenie boxu pre text "foto" ---
            if label.lower() == "foto":
                width = x2 - x1
                height = y2 - y1
                new_width = width * 2.4  # cca 2,4x pôvodnej šírky
                x2 = x1 + new_width

            rect = QRectF(x1, y1, x2 - x1, y2 - y1)
            box = YoloBox(rect, label, self.view.scene)
            self.view.scene.addItem(box)
            self.view.undo_stack.append(box)
            count += 1
        self.log(f"YOLO: {count} detections")

    # ============================
    # Brush
    # ============================
    def _on_brush_changed(self, val):
        self.tool_manager.brush_size = val
        self.brush_indicator.setText(str(val))

    # ============================
    # Drag Text Panel
    # ============================
    def mousePressEventTextPanel(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_start_pos = event.globalPosition().toPoint() - self.text_panel.pos()

    def mouseMoveEventTextPanel(self, event):
        if getattr(self, "_drag_active", False):
            new_pos = event.globalPosition().toPoint() - self._drag_start_pos
            self.text_panel.move(new_pos)

    def mouseReleaseEventTextPanel(self, event):
        self._drag_active = False

    def update_tool_highlight(self):
        # Pre všetky tool actions, zapnuté iba aktuálne
        if not hasattr(self, "tool_actions"):
            return
        current_tool = self.tool_manager.current_tool
        for label, act in self.tool_actions.items():
            if label == "None" and current_tool is None:
                act.setChecked(True)
            elif current_tool and act.text() == self.tool_manager.current_tool:
                act.setChecked(True)
            elif act.text() != "None":
                act.setChecked(False)

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    from gui.gui_main import MainWindow

    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1300, 900)
    w.show()
    sys.exit(app.exec())