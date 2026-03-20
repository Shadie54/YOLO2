# tools_polyline.py
from PyQt6.QtGui import QPen, QColor
from PyQt6.QtWidgets import QGraphicsPathItem
from items.items import BezierPoint
from tools.tools_helpers import TempPoint

class PolylineTool:
    """POLYLINE nástroj - jednoduché spojenie bodov do cesty"""

    def mousePress(self, tm, event):
        view = tm.view
        scene_pos = view.mapToScene(event.position().toPoint())

        if not view.pixmap_item:
            return

        from PyQt6.QtCore import Qt
        # Pravý klik = odstrániť posledný bod
        if event.button() == Qt.MouseButton.RightButton:
            if tm.current_poly_points:
                last_point = tm.current_poly_points.pop()
                view.scene.removeItem(last_point)
                tm.log(f"Removed point, remaining: {len(tm.current_poly_points)}")
                if tm.current_poly_points:
                    self.update_polyline(tm)
                else:
                    self._clear_preview(tm)
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        # nepridáva bod, ak už je BezierPoint na pozícii
        items_at_pos = view.scene.items(scene_pos)
        for item in items_at_pos:
            if isinstance(item, BezierPoint):
                return

        point = BezierPoint(scene_pos.x(), scene_pos.y(), parent_manager=tm)
        view.scene.addItem(point)
        tm.current_poly_points.append(point)
        tm.log(f"Added point, total points: {len(tm.current_poly_points)}")
        self.update_polyline(tm)

    def mouseMove(self, tm, event):
        view = tm.view
        if not tm.current_poly_points:
            return
        scene_pos = view.mapToScene(event.position().toPoint())
        temp_points = tm.current_poly_points + [TempPoint(scene_pos)]
        path = tm.create_standard_path(temp_points)
        self._update_preview(tm, path)

    def mouseRelease(self, tm, event):
        pass  # body sa finalizujú až klávesom Enter

    def keyPress(self, tm, event):
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QGraphicsPathItem

        if event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            if tm.current_poly_points:
                path = tm.create_standard_path(tm.current_poly_points)
                curve_item = QGraphicsPathItem(path)
                curve_item.setPen(QPen(QColor(0,0,0),2))
                tm.view.scene.addItem(curve_item)
                tm.view.undo_stack.append(curve_item)
            self._clear_preview(tm)

        elif event.key() == Qt.Key.Key_Escape:
            self._clear_preview(tm)

    # ---------------- HELPERS ----------------
    def update_polyline(self, tm):
        if not tm.current_poly_points:
            return
        path = tm.create_standard_path(tm.current_poly_points)
        self._update_preview(tm, path)

    def _update_preview(self, tm, path):
        for line in tm.preview_lines:
            tm.view.scene.removeItem(line)
        tm.preview_lines.clear()
        preview = QGraphicsPathItem(path)
        preview.setPen(QPen(QColor(0,0,0),2))
        preview.setZValue(1)
        tm.view.scene.addItem(preview)
        tm.preview_lines.append(preview)

    def _clear_preview(self, tm):
        for point in tm.current_poly_points:
            tm.view.scene.removeItem(point)
        for line in tm.preview_lines:
            tm.view.scene.removeItem(line)
        tm.current_poly_points.clear()
        tm.preview_lines.clear()
        tm.view.setDragMode(tm.view.DragMode.ScrollHandDrag)