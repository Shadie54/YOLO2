from PyQt6.QtGui import QPen, QColor, QPainterPath, QCursor
from PyQt6.QtCore import Qt
from items.aa_path_item import AAPathItem

class PencilTool:
    """Pencil tool – kreslenie čiernou farbou s kruhovým indikátorom"""

    def mousePress(self, tm, event):
        view = tm.view
        scene_pos = view.mapToScene(event.position().toPoint())
        view.drawing = True

        # Path
        path = QPainterPath()
        path.moveTo(scene_pos)
        tm.current_path_item = AAPathItem(path, use_aa=tm.antialiasing)

        # Pen s kruhovým brush
        pen = QPen(QColor(0, 0, 0), tm.brush_size)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        tm.current_path_item.setPen(pen)

        view.scene.addItem(tm.current_path_item)
        tm.last_pos = scene_pos
        tm.first_move_done = False

        self.update_cursor_circle(tm)

    def mouseMove(self, tm, event):
        if not getattr(tm.view, "drawing", False) or not tm.current_path_item:
            return
        scene_pos = tm.view.mapToScene(event.position().toPoint())
        path = tm.current_path_item.path()
        path.moveTo(tm.last_pos)
        path.lineTo(scene_pos)
        tm.current_path_item.setPath(path)
        tm.last_pos = scene_pos

        self.update_cursor_circle(tm)

    def mouseRelease(self, tm, event):
        if tm.current_path_item:
            tm.view.undo_stack.append(tm.current_path_item)
            tm.current_path_item = None
        tm.view.drawing = False
        if hasattr(tm, "cursor_circle"):
            tm.cursor_circle.setVisible(False)

    # ---------------- kruhový indikátor ----------------
    def update_cursor_circle(self, tm):
        from PyQt6.QtWidgets import QGraphicsEllipseItem
        from PyQt6.QtGui import QPen
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QCursor

        view = tm.view

        # ❌ Skúsiť použiť existujúci
        try:
            if hasattr(tm, "cursor_circle") and tm.cursor_circle is not None:
                tm.cursor_circle.scene()  # zistí, či objekt ešte existuje
            else:
                raise RuntimeError
        except RuntimeError:
            # ❌ neexistuje alebo bol zmazaný → vytvoríme nový
            tm.cursor_circle = QGraphicsEllipseItem()
            tm.cursor_circle.setZValue(9999)
            pen = QPen(Qt.GlobalColor.black)
            pen.setWidth(1)
            tm.cursor_circle.setPen(pen)
            tm.cursor_circle.setBrush(Qt.GlobalColor.transparent)
            view.scene.addItem(tm.cursor_circle)

        # 🟢 nastavíme kruh na kurzor
        pos = view.mapToScene(view.mapFromGlobal(QCursor.pos()))
        r = tm.brush_size / 2
        tm.cursor_circle.setRect(pos.x() - r, pos.y() - r, tm.brush_size, tm.brush_size)
        tm.cursor_circle.setVisible(True)