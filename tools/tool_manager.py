from PyQt6.QtGui import QPen, QColor, QPainterPath
from PyQt6.QtWidgets import QGraphicsPathItem


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
        self.antialiasing = True  # default AA zapnuté

        # --- tools instances ---
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
            "TEXT": TextTool(),
        }

    # ---------- LOG ----------
    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    # ---------- TOOL ----------
    def set_tool(self, tool_name):
        if hasattr(self, "current_tool_obj") and getattr(self.current_tool_obj, "editing", False):
            self.current_tool_obj._finalize_text(self)

        self._clear_preview()
        self.current_tool = tool_name
        self.first_move_done = False
        self.current_tool_obj = self.tools.get(tool_name) if tool_name else None

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
        # odstráni staré preview
        for line in self.preview_lines:
            self.view.scene.removeItem(line)
        self.preview_lines.clear()

        # pridá nové preview
        item = QGraphicsPathItem(path_or_item) if not isinstance(path_or_item, QGraphicsPathItem) else path_or_item
        if not isinstance(path_or_item, QGraphicsPathItem):
            pen = QPen(QColor(0,0,0), self.brush_size)
            # renderovanie AA podľa nastavení
            if self.antialiasing:
                pen.setCosmetic(False)  # nech škáluje s zoomom a použije AA
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

    def set_antialiasing(self, value: bool):
        self.antialiasing = value