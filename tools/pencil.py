# tools/pencil.py
from PyQt6.QtGui import QPen, QColor, QPainterPath
from items.aa_path_item import AAPathItem
from .tools_base import BaseTool

class PencilTool:
    def mousePress(self, tm, event):
        view = tm.view
        scene_pos = view.mapToScene(event.position().toPoint())
        tm.view.drawing = True

        # 🖌 AA podľa nastavenia v ToolManager
        path = QPainterPath()
        path.moveTo(scene_pos)
        tm.current_path_item = AAPathItem(path, use_aa=tm.antialiasing)
        tm.current_path_item.setPen(QPen(QColor(0,0,0), tm.brush_size))
        view.scene.addItem(tm.current_path_item)

        tm.last_pos = scene_pos
        tm.first_move_done = False

    def mouseMove(self, tm, event):
        if not getattr(tm.view, "drawing", False) or not tm.current_path_item:
            return
        scene_pos = tm.view.mapToScene(event.position().toPoint())
        path = tm.current_path_item.path()
        path.moveTo(tm.last_pos)
        path.lineTo(scene_pos)
        tm.current_path_item.setPath(path)
        tm.last_pos = scene_pos

    def mouseRelease(self, tm, event):
        if tm.current_path_item:
            tm.view.undo_stack.append(tm.current_path_item)
            tm.current_path_item = None
        tm.view.drawing = False

    def keyPress(self, tm, event):
        pass