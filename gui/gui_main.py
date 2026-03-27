import sys, os, cv2
import numpy as np
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QToolBar, QFileDialog, QDockWidget, QPlainTextEdit,
    QLabel, QSlider, QWidget, QBoxLayout, QHBoxLayout, QVBoxLayout,
    QFontComboBox, QSpinBox, QPushButton, QFrame
)
from PyQt6.QtGui import QIcon, QImage, QPainter, QAction, QActionGroup, QFont
from PyQt6.QtCore import Qt, QSize, QRectF, QSettings
from gui.image_view import ImageView
from gui.shortcuts import register_shortcuts
from tools.tool_manager import ToolManager
from items.items import YoloBox
from utils.settings import SettingsDialog
from utils.error_handler import excepthook
sys.excepthook = excepthook  # <<< tu ho nastavíš, pred MainWindow

# --------------------------------
# --- Utility functions ---
# --------------------------------
def icon(path):
    path = str(path)
    return QIcon(path) if os.path.exists(path) else QIcon()

def load_image_unicode(path):
    try:
        with open(path, "rb") as f:
            bytes_array = bytearray(f.read())
        img_np = np.asarray(bytes_array, dtype=np.uint8)
        return cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"Failed to load image {path}: {e}")
        return None

# --------------------------------
# --- Main Window ---
# --------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO2 experimental")

        # --------------------------
        # --- Directories & Icons ---
        # --------------------------
        BASE_DIR = Path(__file__).resolve().parent.parent
        ICON_DIR = BASE_DIR / "assets" / "icons"
        MODEL_PATH = BASE_DIR / "models" / "best.pt"
        self.setWindowIcon(QIcon(str(ICON_DIR / "yolocat.ico")))

        # --------------------------
        # --- Settings & YOLO ---
        # --------------------------
        self.settings = {
            "overwrite_original": False,
            "custom_folder": "",
            "antialiasing": True,
        }
        from yolo.yolo_detector import YoloDetector
        self.detector = YoloDetector(str(MODEL_PATH))

        # --------------------------
        # --- Central ImageView ---
        # --------------------------
        self.view = ImageView()
        self.setCentralWidget(self.view)

        # --------------------------
        # --- Log Panel ---
        # --------------------------
        self.init_log_panel()

        # --------------------------
        # --- Tool Manager ---
        # --------------------------
        self.tool_manager = ToolManager(self.view, log_callback=self.log)
        self.view.tool_manager = self.tool_manager
        self.tool_manager.set_tool(None)

        # --------------------------
        # --- Toolbars ---
        # --------------------------
        ICON_SIZE = QSize(48, 48)
        self.init_actions_toolbar(ICON_DIR, ICON_SIZE)
        self.init_draw_toolbar(ICON_DIR, ICON_SIZE)
        self.init_brush_toolbar(ICON_SIZE)
        self.init_navigation_toolbar(ICON_DIR, ICON_SIZE)

        # --------------------------
        # --- Panels (Draggable) ---
        # --------------------------
        self.init_text_panel(ICON_DIR)
        self.init_dash_panel()

        # --------------------------
        # --- Shortcuts ---
        # --------------------------
        register_shortcuts(self)

        # --------------------------
        # --- Restore window geometry ---
        # --------------------------
        self.restore_window_geometry()


    # =========================
    # Log Panel
    # =========================
    def init_log_panel(self):
        self.log_panel = QPlainTextEdit()
        self.log_panel.setReadOnly(True)
        dock_log = QDockWidget("Log", self)
        dock_log.setWidget(self.log_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_log)
        self.log = lambda msg: self.log_panel.appendPlainText(msg)


    # =========================
    # Toolbars
    # =========================
    def init_actions_toolbar(self, ICON_DIR, ICON_SIZE):
        # Open, Settings, YOLO, Save
        actions_tb = QToolBar("Actions")
        actions_tb.setObjectName("actions_toolbar")
        actions_tb.setIconSize(ICON_SIZE)
        actions_tb.setMovable(True)
        actions_tb.setFloatable(True)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, actions_tb)

        # --- Open Folder ---
        open_folder_act = QAction(icon(str(ICON_DIR / "open.png")), "Open Folder", self)
        open_folder_act.setToolTip("Open Folder (Ctrl+O)")
        open_folder_act.triggered.connect(self.open_folder)
        actions_tb.addAction(open_folder_act)

        # --- Settings ---
        settings_act = QAction(icon(str(ICON_DIR / "settings.png")), "Settings", self)
        settings_act.setToolTip("Settings")
        settings_act.triggered.connect(self.open_settings)
        actions_tb.addAction(settings_act)

        # --- YOLO ---
        self.yolo_auto = False
        yolo_icon_path = ICON_DIR / "yolo.png"
        yolo_auto_icon_path = ICON_DIR / "yolo_auto.png"
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
        save_act = QAction(icon(str(ICON_DIR / "save.png")), "Save", self)
        save_act.setToolTip("Save annotated image")
        save_act.triggered.connect(self.save_image)
        actions_tb.addAction(save_act)


    def init_draw_toolbar(self, ICON_DIR, ICON_SIZE):
        draw_tb = QToolBar("Draw Tools")
        draw_tb.setObjectName("draw_toolbar")
        draw_tb.setIconSize(ICON_SIZE)
        draw_tb.setMovable(True)
        draw_tb.setFloatable(True)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, draw_tb)

        self.tool_actions = {}
        tool_group = QActionGroup(self)
        tool_group.setExclusive(True)

        def tool_btn(icon_name, label, tool_name=None, func=None, tooltip=None):
            act = QAction(icon(str(ICON_DIR / icon_name)), label, self)
            act.setCheckable(True)

            def handler():
                if func:
                    func()
                    return
                self.tool_manager.set_tool(tool_name)
                for a in tool_group.actions():
                    a.setChecked(a == act)
                self.update_text_panel_visibility(tool_name)
                self.update_dash_panel_visibility(tool_name)

            act.triggered.connect(handler)
            if tooltip:
                act.setToolTip(tooltip)

            tool_group.addAction(act)
            draw_tb.addAction(act)
            self.tool_actions[label] = act
            return act

        # --- Tool buttons ---
        tool_btn("mouse.png", "Mouse", None, tooltip="Mouse (M)")
        tool_btn("select.png", "Select", "SELECT", tooltip="Copy Select (S)")
        tool_btn("pencil.png", "Pencil", "PENCIL", tooltip="Pencil (C)")
        tool_btn("line.png", "Line", "LINE", tooltip="Line (L)")
        tool_btn("line_dashed.png", "Polyline_dashed", "POLYLINE_DASHED", tooltip="POLYLINE_DASHED (X)")
        tool_btn("polyline.png", "Polyline", "POLYLINE", tooltip="Polyline (P)")
        tool_btn("polycurve.png", "Polycurve", "POLYCURVE", tooltip="Polycurve (V)")
        tool_btn("eraser.png", "Eraser", "ERASER", tooltip="Guma (E)")
        tool_btn("text.png", "Text", "TEXT", tooltip="Text (T)")

        # --- Undo ---
        undo_act = QAction(icon(str(ICON_DIR / "undo.png")), "Undo", self)
        undo_act.setToolTip("Undo last action (Ctrl+Z)")
        undo_act.triggered.connect(self.view.undo)
        draw_tb.addAction(undo_act)


    def init_brush_toolbar(self, ICON_SIZE):
        self.brush_tb = QToolBar("Brush")
        self.brush_tb.setObjectName("brush_toolbar")
        self.brush_tb.setIconSize(ICON_SIZE)
        self.brush_tb.setMovable(True)
        self.brush_tb.setFloatable(True)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.brush_tb)

        self.brush_widget = QWidget()
        direction = QBoxLayout.Direction.TopToBottom if self.brush_tb.orientation() == Qt.Orientation.Vertical else QBoxLayout.Direction.LeftToRight
        self.brush_layout = QBoxLayout(direction)
        self.brush_layout.setContentsMargins(2, 2, 2, 2)
        self.brush_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        self.brush_slider = QSlider(
            Qt.Orientation.Vertical if self.brush_tb.orientation() == Qt.Orientation.Vertical else Qt.Orientation.Horizontal)
        self.brush_slider.setMinimum(1)
        self.brush_slider.setMaximum(20)
        self.brush_slider.setValue(self.tool_manager.brush_size)

        self.brush_indicator = QLabel(str(self.brush_slider.value()), self)
        self.brush_indicator.setStyleSheet(
            "background-color: rgba(0,0,0,180); color: white; font-weight: bold; padding: 2px; border-radius: 4px;"
        )

        self.brush_slider.valueChanged.connect(self._on_brush_changed)
        self.brush_layout.addWidget(self.brush_slider)
        self.brush_layout.addWidget(self.brush_indicator)
        self.brush_widget.setLayout(self.brush_layout)
        self.brush_tb.addWidget(self.brush_widget)
        self.brush_tb.orientationChanged.connect(self._on_toolbar_orientation_changed)


    def init_navigation_toolbar(self, ICON_DIR, ICON_SIZE):
        nav_tb = QToolBar("Navigation")
        nav_tb.setObjectName("nav_toolbar")
        nav_tb.setIconSize(ICON_SIZE)
        nav_tb.setMovable(True)
        nav_tb.setFloatable(True)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, nav_tb)

        self.nav_label = QLabel("0/0")
        self.nav_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nav_label.setMinimumWidth(50)

        prev_act = QAction(icon(str(ICON_DIR / "left.png")), "Previous", self)
        next_act = QAction(icon(str(ICON_DIR / "right.png")), "Next", self)
        prev_act.triggered.connect(self.go_previous_image)
        next_act.triggered.connect(self.go_next_image)

        label_widget = QWidget()
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_layout.addWidget(self.nav_label)
        label_widget.setLayout(label_layout)

        nav_tb.addAction(prev_act)
        nav_tb.addWidget(label_widget)
        nav_tb.addAction(next_act)
# =========================
# --- Drag Panels (Draggable) ---
# =========================
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

    def mousePressEventDashPanel(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_start_pos = event.globalPosition().toPoint() - self.dash_panel.pos()

    def mouseMoveEventDashPanel(self, event):
        if getattr(self, "_drag_active", False):
            new_pos = event.globalPosition().toPoint() - self._drag_start_pos
            self.dash_panel.move(new_pos)

    def mouseReleaseEventDashPanel(self, event):
        self._drag_active = False


# =========================
# --- Text Tool Panel ---
# =========================
    def init_text_panel(self, ICON_DIR):
        self.text_panel = QWidget(self, flags=Qt.WindowType.Tool)
        self.text_panel.setWindowTitle("Text Tool")
        self.text_panel.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.text_panel.setVisible(False)

        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Font/Size/Style
        self.font_box = QFontComboBox()
        self.font_box.setCurrentFont(QFont("Arial"))
        self.size_box = QSpinBox()
        self.size_box.setRange(6, 200)
        self.size_box.setValue(25)
        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)

        for w in [self.font_box, self.size_box, self.bold_btn, self.italic_btn]:
            layout.addWidget(w)

        # Layer buttons
        self.bring_forward_btn = QPushButton()
        self.send_backward_btn = QPushButton()
        layout.addWidget(self.bring_forward_btn)
        layout.addWidget(self.send_backward_btn)

        self.text_panel.setLayout(layout)

        # Connect signals
        self.font_box.currentFontChanged.connect(
            lambda f: self.tool_manager.current_tool_obj.set_font(f)
            if self.tool_manager.current_tool_obj else None
        )
        self.size_box.valueChanged.connect(
            lambda s: self.tool_manager.current_tool_obj.set_size(s)
            if self.tool_manager.current_tool_obj else None
        )
        self.bold_btn.clicked.connect(
            lambda: self.tool_manager.current_tool_obj.set_bold(self.bold_btn.isChecked())
            if self.tool_manager.current_tool_obj else None
        )
        self.italic_btn.clicked.connect(
            lambda: self.tool_manager.current_tool_obj.set_italic(self.italic_btn.isChecked())
            if self.tool_manager.current_tool_obj else None
        )

        # Drag
        self.text_panel.mousePressEvent = self.mousePressEventTextPanel
        self.text_panel.mouseMoveEvent = self.mouseMoveEventTextPanel
        self.text_panel.mouseReleaseEvent = self.mouseReleaseEventTextPanel

    def bring_text_forward(self):
        tool = getattr(self.tool_manager.current_tool_obj, "text_item", None)
        if tool:
            tool.setZValue(tool.zValue() + 1)

    def send_text_backward(self):
        tool = getattr(self.tool_manager.current_tool_obj, "text_item", None)
        if tool:
            new_z = max(0, tool.zValue() - 1)
            tool.setZValue(new_z)

    def update_text_panel_visibility(self, tool_name):
        if tool_name == "TEXT":
            self.text_panel.setVisible(True)
            offset_y = 100
            center_x = self.view.geometry().left() + self.view.width() // 2 - self.text_panel.width() // 2
            self.text_panel.move(center_x, self.view.geometry().top() + offset_y)
        else:
            self.text_panel.setVisible(False)


# =========================
# --- Polyline Dashed Panel ---
# =========================
    def init_dash_panel(self):
        self.dash_panel = QWidget(self, flags=Qt.WindowType.Tool)
        self.dash_panel.setWindowTitle("Dash Settings")
        self.dash_panel.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.dash_panel.setVisible(False)

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        label_width = 100

        def make_row(name, min_val, max_val, default_val, setter_attr):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(6)
            label = QLabel(name)
            label.setFixedWidth(label_width)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(default_val)

            value_label = QLabel(str(default_val))
            value_label.setFixedWidth(30)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value_label.setStyleSheet(
                "background-color: rgba(0,0,0,180); color: white; font-weight: bold; padding: 2px; border-radius: 4px;"
            )

            def on_change(val):
                setattr(self.tool_manager, setter_attr, val)
                value_label.setText(str(val))
                if self.tool_manager.current_tool == "POLYLINE_DASHED" and self.tool_manager.current_poly_points:
                    path = self.tool_manager.create_standard_path(self.tool_manager.current_poly_points)
                    item = self.tool_manager.current_tool_obj._make_dashed_item(self.tool_manager, path)
                    self.tool_manager._update_preview(item)

            slider.valueChanged.connect(on_change)
            row_layout.addWidget(label)
            row_layout.addWidget(slider)
            row_layout.addWidget(value_label)
            return row_layout, slider

        seg_layout, self.segment_slider = make_row("Dĺžka čiary", 1, 100, self.tool_manager.dash_segment, "dash_segment")
        gap_layout, self.gap_slider = make_row("Dĺžka medzery", 0, 100, self.tool_manager.dash_gap, "dash_gap")
        layout.addLayout(seg_layout)
        layout.addLayout(gap_layout)

        self.dash_panel.setLayout(layout)

        # Drag like text panel
        self.dash_panel.mousePressEvent = self.mousePressEventDashPanel
        self.dash_panel.mouseMoveEvent = self.mouseMoveEventDashPanel
        self.dash_panel.mouseReleaseEvent = self.mouseReleaseEventDashPanel

    def set_dash_segment(self, val):
        self.tool_manager.dash_segment = val
        self._refresh_dashed_preview()

    def set_dash_gap(self, val):
        self.tool_manager.dash_gap = val
        self._refresh_dashed_preview()

    def _refresh_dashed_preview(self):
        tm = self.tool_manager
        tool = tm.current_tool_obj
        if tm.current_tool == "POLYLINE_DASHED" and len(tm.current_poly_points) > 1:
            path = tm.create_standard_path(tm.current_poly_points)
            if hasattr(tool, "_make_dashed_item"):
                tm._update_preview(tool._make_dashed_item(tm, path))

    def update_dash_panel_visibility(self, tool_name):
        if tool_name == "POLYLINE_DASHED":
            self.dash_panel.setVisible(True)
            offset_y = 160
            center_x = self.view.geometry().left() + self.view.width() // 2 - self.dash_panel.width() // 2
            self.dash_panel.move(center_x, self.view.geometry().top() + offset_y)
        else:
            self.dash_panel.setVisible(False)


# =========================
# --- Image Folder / Navigation ---
# =========================
    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Folder", "")
        if not folder:
            return
        folder_path = Path(folder)
        self.image_list = sorted([str(f) for f in folder_path.iterdir() if f.suffix.lower() in {".png", ".jpg", ".jpeg"}])
        if not self.image_list:
            self.log("No images found in folder")
            return
        self.current_image_idx = 0
        self.show_current_image()
        self.log(f"Opened folder: {folder} ({len(self.image_list)} images)")

    def show_current_image(self):
        if self.tool_manager.current_tool_obj:
            self.tool_manager.set_tool(None)
            self.update_tool_highlight()
        self.view.scene.clear()
        if not hasattr(self, "image_list") or not self.image_list:
            return
        path = self.image_list[self.current_image_idx]
        img = load_image_unicode(path)
        if img is None:
            self.log(f"Failed to load image: {path}")
            return
        self.view.set_image(img)
        self.nav_label.setText(f"{self.current_image_idx + 1}/{len(self.image_list)}")
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


# =========================
# --- Save Image ---
# =========================
    def save_image(self):
        if not hasattr(self, "image_list") or not self.image_list:
            self.log("No image to save")
            return
        path = Path(self.image_list[self.current_image_idx])
        folder = path.parent
        save_mode = self.settings.get("save_mode", "subfolder")
        if save_mode == "origin":
            save_folder = folder
        elif save_mode == "subfolder":
            save_folder = folder / folder.name
            save_folder.mkdir(exist_ok=True)
        elif save_mode == "custom":
            save_folder = Path(self.settings.get("custom_folder", folder))
            save_folder.mkdir(exist_ok=True)
        else:
            save_folder = folder / "annotated"
            save_folder.mkdir(exist_ok=True)
        save_path = save_folder / path.name

        # Hide YOLO boxes
        hidden_items = []
        for item in self.view.scene.items():
            if isinstance(item, YoloBox):
                hidden_items.append(item)
                item.setOpacity(0)

        # Render
        img_rect = self.view.scene.sceneRect()
        image = QImage(int(img_rect.width()), int(img_rect.height()), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.white)
        painter = QPainter(image)
        self.view.scene.render(painter)
        painter.end()

        # Restore YOLO boxes
        for item in hidden_items:
            item.setOpacity(1)

        # Save
        ext = save_path.suffix.lower()
        if ext in [".jpg", ".jpeg"]:
            image.save(str(save_path), "JPEG", quality=100)
        else:
            image.save(str(save_path))

        self.log(f"Uložené do: {save_path}")


# =========================
# --- YOLO Detection ---
# =========================
    def run_yolo_on_current_image(self):
        if not hasattr(self, "image_list") or not self.image_list:
            return
        path = self.image_list[self.current_image_idx]
        img = load_image_unicode(path)
        if img is None:
            self.log(f"Failed to load image: {path}")
            return

        detections = self.detector.detect(img)
        count = 0
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = det["label"]
            if label.lower() == "foto":
                width = x2 - x1
                height = y2 - y1
                new_width = width * 2.4
                x2 = x1 + new_width
            rect = QRectF(x1, y1, x2 - x1, y2 - y1)
            box = YoloBox(rect, label, self.view.scene)
            self.view.scene.addItem(box)
            count += 1
        self.log(f"YOLO: {count} detections")


# =========================
# --- Brush ---
# =========================
    def _on_brush_changed(self, val):
        self.tool_manager.brush_size = val
        self.brush_indicator.setText(str(val))

    def _on_toolbar_orientation_changed(self, orientation):
        if orientation == Qt.Orientation.Vertical:
            self.brush_slider.setOrientation(Qt.Orientation.Vertical)
            self.brush_layout.setDirection(QBoxLayout.Direction.TopToBottom)
        else:
            self.brush_slider.setOrientation(Qt.Orientation.Horizontal)
            self.brush_layout.setDirection(QBoxLayout.Direction.LeftToRight)


# =========================
# --- Helpers ---
# =========================
    def update_tool_highlight(self):
        current_tool = self.tool_manager.current_tool
        for label, act in self.tool_actions.items():
            tool_name = act.text().upper()
            if current_tool is None and tool_name == "MOUSE":
                act.setChecked(True)
            elif current_tool and tool_name == current_tool.upper():
                act.setChecked(True)
            else:
                act.setChecked(False)

    def open_settings(self):
        dlg = SettingsDialog(self, settings=self.settings, tool_manager=self.tool_manager)
        if dlg.exec():
            self.settings = dlg.get_settings()
            self.log(f"Settings updated: {self.settings}")

    def restore_window_geometry(self):
        settings = QSettings("YOLO2", "App")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = settings.value("windowState")
        if state:
            self.restoreState(state)

    def closeEvent(self, event):
        settings = QSettings("YOLO2", "App")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        super().closeEvent(event)


# =========================
# --- Run App ---
# =========================
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1300, 900)
    w.show()
    sys.exit(app.exec())