# tools/polyline.py
from PyQt6.QtGui import QPen, QColor, QPainterPath
from items.aa_path_item import AAPathItem
from items.items import BezierPoint
from .tools_helpers import TempPoint

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
                    self._clear_preview(tm, reset_drag=False)
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        # nepridáva bod, ak už je BezierPoint na pozícii
        for item in view.scene.items(scene_pos):
            if isinstance(item, BezierPoint):
                return

        point = BezierPoint(scene_pos.x(), scene_pos.y(), parent_manager=tm)
        view.scene.addItem(point)
        tm.current_poly_points.append(point)
        tm.log(f"Added point, total points: {len(tm.current_poly_points)}")
        self.update_polyline(tm)

    def mouseMove(self, tm, event):
        if not tm.current_poly_points:
            return
        scene_pos = tm.view.mapToScene(event.position().toPoint())
        temp_points = tm.current_poly_points + [TempPoint(scene_pos)]
        path = tm.create_standard_path(temp_points)
        self._update_preview(tm, path)

    def mouseRelease(self, tm, event):
        pass  # finalizácia Enterom

    def keyPress(self, tm, event):
        from PyQt6.QtCore import Qt
        if event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            if tm.current_poly_points:
                path = tm.create_standard_path(tm.current_poly_points)
                item = AAPathItem(path, use_aa=tm.antialiasing)
                item.setPen(QPen(QColor(0,0,0), tm.brush_size))
                tm.view.scene.addItem(item)
                tm.view.undo_stack.append(item)
            self._clear_preview(tm, reset_drag=False)
        elif event.key() == Qt.Key.Key_Escape:
            self._clear_preview(tm, reset_drag=False)

    # ---------- HELPERS ----------
    def update_polyline(self, tm):
        if not tm.current_poly_points:
            return
        path = tm.create_standard_path(tm.current_poly_points)
        self._update_preview(tm, path)

    def _update_preview(self, tm, path):
        for line in tm.preview_lines:
            tm.view.scene.removeItem(line)
        tm.preview_lines.clear()
        preview = AAPathItem(path, use_aa=tm.antialiasing)
        preview.setPen(QPen(QColor(0,0,0), tm.brush_size))
        preview.setZValue(1)
        tm.view.scene.addItem(preview)
        tm.preview_lines.append(preview)

    def _clear_preview(self, tm, reset_drag=True):
        for pt in tm.current_poly_points:
            tm.view.scene.removeItem(pt)
        for line in tm.preview_lines:
            tm.view.scene.removeItem(line)
        tm.current_poly_points.clear()
        tm.preview_lines.clear()
        if reset_drag:
            tm.view.setDragMode(tm.view.DragMode.ScrollHandDrag)