# tools/eraser.py
from PyQt6.QtGui import QPen, QColor, QPainterPath
from items.aa_path_item import AAPathItem

class EraserTool:
    """Eraser = bielidlo, funguje rovnako ako PencilTool, len kreslí bielou farbou"""

    def mousePress(self, tm, event):
        view = tm.view
        scene_pos = view.mapToScene(event.position().toPoint())
        view.drawing = True

        path = QPainterPath()
        path.moveTo(scene_pos)
        # 🖌 Použitie AA z ToolManager
        tm.current_path_item = AAPathItem(path, use_aa=tm.antialiasing)
        # Biely štetec
        tm.current_path_item.setPen(QPen(QColor(255, 255, 255), tm.brush_size))
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