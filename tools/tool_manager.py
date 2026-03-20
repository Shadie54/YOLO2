# tools/tool_manager.py
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QColor, QPainterPath
from PyQt6.QtWidgets import QGraphicsPathItem
from items.items import BezierPoint, YoloBox
from .tools_helpers import TempPoint
import numpy as np

class ToolManager:
    def __init__(self, view, log_callback=None):
        self.view = view
        self.current_tool = None
        self.current_poly_points = []
        self.preview_lines = []
        self.log_callback = log_callback

        # pencil/eraser
        self.brush_size = 2
        self.current_path_item = None
        self.last_pos = None
        self.first_move_done = False

        # --- tools instances (late import to avoid circular) ---
        self.tools = self._init_tools()

    def _init_tools(self):
        from .pencil import PencilTool
        from .eraser import EraserTool
        from .line import LineTool
        from .polyline import PolylineTool
        from .polycurve import PolycurveTool
        from .text import TextTool
        return {
            "PENCIL": PencilTool(),
            "ERASER": EraserTool(),
            "LINE": LineTool(),
            "POLYLINE": PolylineTool(),
            "POLYCURVE": PolycurveTool(),
            "TEXT": TextTool(),  # pridáme text tool
        }

    # ---------- LOG ----------
    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    # ---------- TOOL ----------
    def set_tool(self, tool_name):
        # finish current pencil/eraser drawing
        if getattr(self.view, "drawing", False) and self.current_tool in ["PENCIL", "ERASER"]:
            if self.current_path_item:
                self.view.undo_stack.append(self.current_path_item)
                self.current_path_item = None
            self.view.drawing = False

        self._clear_preview()
        self.current_tool = tool_name
        self.first_move_done = False

        if tool_name is None:
            self.view.setDragMode(self.view.DragMode.ScrollHandDrag)
        else:
            self.view.setDragMode(self.view.DragMode.NoDrag)
        self.log(f"[Tool] Tool set to {tool_name if tool_name else 'NONE'}")

    # ---------- RESET ----------
    def reset(self):
        self._clear_preview()

    # ---------- MOUSE EVENTS ----------
    def mousePressEvent(self, event):
        if not self.view.pixmap_item or self.current_tool is None:
            return
        tool = self.tools.get(self.current_tool)
        if tool:
            tool.mousePress(self, event)

    def mouseMoveEvent(self, event):
        if not self.view.pixmap_item or self.current_tool is None:
            return
        tool = self.tools.get(self.current_tool)
        if tool:
            tool.mouseMove(self, event)

    def mouseReleaseEvent(self, event):
        if not self.view.pixmap_item or self.current_tool is None:
            return
        tool = self.tools.get(self.current_tool)
        if tool:
            tool.mouseRelease(self, event)

    # ---------- KEY EVENTS ----------
    def keyPressEvent(self, event):
        print(f"Key pressed: {event.key()}, current tool: {self.current_tool}")

        if self.current_tool == "TEXT":
            tool = self.tools.get("TEXT")
            if tool and hasattr(tool, "keyPress"):
                tool.keyPress(self, event)
            print("Text tool: shortcut ignored")
            return

        # ostatné tooly
        if self.current_tool is None:
            return
        tool = self.tools.get(self.current_tool)
        if tool and hasattr(tool, "keyPress"):
            tool.keyPress(self, event)

    # ---------- PATH HELPERS ----------
    def create_standard_path(self, points):
        if len(points) < 2:
            return QPainterPath(points[0].pos())
        path = QPainterPath(points[0].pos())
        for pt in points[1:]:
            path.lineTo(pt.pos())
        return path

    # ---------- UNDO ----------
    def add_to_undo(self, item):
        if item:
            self.view.undo_stack.append(item)

    # ---------- PREVIEW ----------
    def _update_preview(self, path_or_item):
        # remove old preview
        for line in self.preview_lines:
            self.view.scene.removeItem(line)
        self.preview_lines.clear()

        # add new preview
        item = QGraphicsPathItem(path_or_item) if not isinstance(path_or_item, QGraphicsPathItem) else path_or_item
        if not isinstance(path_or_item, QGraphicsPathItem):
            item.setPen(QPen(QColor(0,0,0), self.brush_size))
        self.view.scene.addItem(item)
        self.preview_lines.append(item)

    def _clear_preview(self):
        for pt in self.current_poly_points:
            self.view.scene.removeItem(pt)
        for line in self.preview_lines:
            self.view.scene.removeItem(line)
        self.current_poly_points.clear()
        self.preview_lines.clear()
        self.view.setDragMode(self.view.DragMode.ScrollHandDrag)

    def complete_text_tool(self):
        """Potvrdiť písaný text a vykresliť ho do scény."""
        if getattr(self, "text_edit_item", None):
            # pridáme do undo
            self.view.undo_stack.append(self.text_edit_item)
            # odstránime edit widget
            self.view.scene.removeItem(self.text_edit_item)
            self.text_edit_item = None
            self.set_tool(None)

    def cancel_text_tool(self):
        """Zrušiť písanie textu."""
        if getattr(self, "text_edit_item", None):
            self.view.scene.removeItem(self.text_edit_item)
            self.text_edit_item = None
            self.set_tool(None)