from PyQt6.QtGui import QPen, QColor, QPainterPath
from PyQt6.QtWidgets import QGraphicsPathItem
from PyQt6.QtCore import Qt

class ToolManager:
    def __init__(self, view, log_callback=None, antialiasing=True):
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

        # --- AA ---
        self.antialiasing = True

        # --- drag ---
        self._dragging_scene = False
        self._drag_start_pos = None

        # --- tools instances ---
        self.tools = self._init_tools()
        self.current_tool_obj = None

    def _init_tools(self):
        from .pencil import PencilTool
        from .eraser import EraserTool
        from .line import LineTool
        from .polyline import PolylineTool
        from .polycurve import PolycurveTool
        from .text import TextTool
        from .select import SelectTool

        return {
            "PENCIL": PencilTool(),
            "ERASER": EraserTool(),
            "LINE": LineTool(),
            "POLYLINE": PolylineTool(),
            "POLYCURVE": PolycurveTool(),
            "TEXT": TextTool(manager=self),
             "SELECT": SelectTool(self),

        }

    # ---------- LOG ----------
    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    # ---------- TOOL ----------
    def set_tool(self, tool_name):
        if getattr(self.current_tool_obj, "editing", False):
            self.current_tool_obj._finalize_text(self)

        self._clear_preview()
        self.current_tool = tool_name
        self.first_move_done = False
        self.current_tool_obj = self.tools.get(tool_name) if tool_name else None

        if tool_name is None:
            self.view.setDragMode(self.view.DragMode.ScrollHandDrag)
            self.view.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.view.setDragMode(self.view.DragMode.NoDrag)
            self.view.viewport().setCursor(Qt.CursorShape.CrossCursor)

        self.log(f"[Tool] Tool set to {tool_name if tool_name else 'MOUSE'}")

    # ---------- RESET ----------
    def reset(self):
        self._clear_preview()

    # ---------- MOUSE EVENTS ----------
    def mousePressEvent(self, event):
        if self.current_tool is None:
            self._start_scene_drag(event)
        elif self.current_tool_obj:
            self.current_tool_obj.mousePress(self, event)

    def mouseMoveEvent(self, event):
        if self.current_tool is None:
            self._update_scene_drag(event)
        elif self.current_tool_obj:
            self.current_tool_obj.mouseMove(self, event)

    def mouseReleaseEvent(self, event):
        if self.current_tool is None:
            self._end_scene_drag(event)
        elif self.current_tool_obj:
            self.current_tool_obj.mouseRelease(self, event)

    # ---------- SCENE DRAG HELPERS ----------
    def _start_scene_drag(self, event):
        self._dragging_scene = True
        self._drag_start_pos = event.position()
        self.view.viewport().setCursor(Qt.CursorShape.OpenHandCursor)

    def _update_scene_drag(self, event):
        if self._dragging_scene:
            # tu môžeš implementovať vlastný posun scény podľa myši
            self.view.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)

    def _end_scene_drag(self, event):
        self._dragging_scene = False
        self._drag_start_pos = None
        self.view.viewport().setCursor(Qt.CursorShape.ArrowCursor)


    # ---------- KEY EVENTS ----------
    def keyPressEvent(self, event):
        if getattr(self.current_tool_obj, "editing", False):
            if hasattr(self.current_tool_obj, "keyPress"):
                self.current_tool_obj.keyPress(self, event)
            return

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
        for line in self.preview_lines:
            self.view.scene.removeItem(line)
        self.preview_lines.clear()

        item = QGraphicsPathItem(path_or_item) if not isinstance(path_or_item, QGraphicsPathItem) else path_or_item
        if not isinstance(path_or_item, QGraphicsPathItem):
            pen = QPen(QColor(0,0,0), self.brush_size)
            if self.antialiasing:
                pen.setCosmetic(False)
            item.setPen(pen)

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
        self.view.viewport().setCursor(Qt.CursorShape.ArrowCursor)

    # ---------- ANTIALIASING ----------
    def set_antialiasing(self, value: bool):
        self.antialiasing = value