from PyQt6.QtGui import QPen, QColor, QPainterPath
from PyQt6.QtWidgets import QGraphicsPathItem
from PyQt6.QtCore import Qt
from items.items import BezierPoint
from .tools_helpers import TempPoint  # pre kurzorový preview

class PolylineDashedTool:
    """Polyline Dashed Tool s presúvateľnými bodmi a live preview."""

    def mousePress(self, tm, event):
        view = tm.view
        scene_pos = view.mapToScene(event.position().toPoint())

        # --- PRAVÉ tlačidlo: odstrániť posledný bod ---
        if event.button() == Qt.MouseButton.RightButton:
            if tm.current_poly_points:
                last = tm.current_poly_points.pop()
                view.scene.removeItem(last)
                if len(tm.current_poly_points) > 1:
                    path = tm.create_standard_path(tm.current_poly_points)
                    tm._update_preview(self._make_dashed_item(tm, path))
                else:
                    tm._clear_preview()
            return

        # --- ĽAVÉ tlačidlo: pridanie bodu ---
        if event.button() != Qt.MouseButton.LeftButton:
            return

        # nepridávať bod tam, kde už je BezierPoint
        for item in view.scene.items(scene_pos):
            if isinstance(item, BezierPoint):
                return

        point = BezierPoint(scene_pos.x(), scene_pos.y(), parent_manager=tm)
        view.scene.addItem(point)
        tm.current_poly_points.append(point)

        # update preview
        if len(tm.current_poly_points) > 1:
            path = tm.create_standard_path(tm.current_poly_points)
            tm._update_preview(self._make_dashed_item(tm, path))

    def mouseMove(self, tm, event):
        if not tm.current_poly_points:
            return
        view = tm.view
        scene_pos = view.mapToScene(event.position().toPoint())

        # preview path (posledný bod = kurzor)
        temp_points = tm.current_poly_points + [TempPoint(scene_pos)]
        path = tm.create_standard_path(temp_points)
        tm._update_preview(self._make_dashed_item(tm, path))

    def mouseRelease(self, tm, event):
        pass  # Enter/ESC finalizujú

    def keyPress(self, tm, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.finish(tm)
        elif event.key() == Qt.Key.Key_Escape:
            tm._clear_preview()
            tm.current_poly_points.clear()

    def finish(self, tm):
        if len(tm.current_poly_points) < 2:
            tm._clear_preview()
            tm.current_poly_points.clear()
            return

        path = tm.create_standard_path(tm.current_poly_points)
        item = self._make_dashed_item(tm, path)
        tm.view.scene.addItem(item)
        tm.add_to_undo(item)

        tm._clear_preview()
        tm.current_poly_points.clear()  # pripravené na ďalšie kreslenie
        tm.view.setDragMode(tm.view.DragMode.NoDrag)
        tm.view.viewport().setCursor(Qt.CursorShape.CrossCursor)

    def _make_dashed_item(self, tm, path: QPainterPath) -> QGraphicsPathItem:
        """Vytvorí QGraphicsPathItem s dash pattern nezávislým od brush size."""
        item = QGraphicsPathItem()
        pen = QPen(QColor(0, 0, 0))
        pen.setWidth(tm.brush_size)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCosmetic(False)
        item.setPen(pen)

        dashed_path = QPainterPath()
        length_dash = tm.dash_segment
        length_gap = tm.dash_gap

        # rozdelíme path na jednotlivé segmenty
        for i in range(1, path.elementCount()):
            p1 = path.elementAt(i - 1)
            p2 = path.elementAt(i)

            dx = p2.x - p1.x
            dy = p2.y - p1.y
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist == 0:
                continue

            ux = dx / dist
            uy = dy / dist
            drawn = 0
            while drawn < dist:
                seg_len = min(length_dash, dist - drawn)
                start_x = p1.x + ux * drawn
                start_y = p1.y + uy * drawn
                end_x = start_x + ux * seg_len
                end_y = start_y + uy * seg_len
                dashed_path.moveTo(start_x, start_y)
                dashed_path.lineTo(end_x, end_y)
                drawn += seg_len + length_gap

        item.setPath(dashed_path)
        return item