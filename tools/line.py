# tools/line.py
from PyQt6.QtGui import QPen, QColor, QPainterPath
from PyQt6.QtWidgets import QGraphicsPathItem
from items.aa_path_item import AAPathItem
from items.items import BezierPoint
from .tools_helpers import TempPoint

class LineTool:
    def mousePress(self, tm, event):
        scene_pos = tm.view.mapToScene(event.position().toPoint())
        self.points = getattr(self, "points", [])

        if len(self.points) == 2:
            return  # už máme hotovú čiaru

        point = BezierPoint(scene_pos.x(), scene_pos.y(), parent_manager=tm)
        tm.view.scene.addItem(point)
        self.points.append(point)

        if len(self.points) == 2:
            self._finalize_line(tm)

    def mouseMove(self, tm, event):
        if not getattr(self, "points", None) or len(self.points) == 0:
            return
        scene_pos = tm.view.mapToScene(event.position().toPoint())
        temp_points = self.points + [TempPoint(scene_pos)]
        path = QPainterPath(temp_points[0].pos())
        path.lineTo(temp_points[1].pos())
        self._update_preview(tm, path)

    def mouseRelease(self, tm, event):
        pass

    def keyPress(self, tm, event):
        pass

    # ---------- HELPERS ----------
    def _finalize_line(self, tm):
        path = QPainterPath(self.points[0].pos())
        path.lineTo(self.points[1].pos())

        # dynamicky berieme AA z ToolManager
        print(f"[DEBUG] Creating line AA = {tm.antialiasing}")
        line_item = AAPathItem(path, use_aa=tm.antialiasing)
        line_item.setPen(QPen(QColor(0, 0, 0), tm.brush_size))
        tm.view.scene.addItem(line_item)
        tm.view.undo_stack.append(line_item)

        # odstrániť body a preview
        for pt in self.points:
            tm.view.scene.removeItem(pt)
        for line in tm.preview_lines:
            tm.view.scene.removeItem(line)
        tm.preview_lines.clear()
        self.points = []

    def _update_preview(self, tm, path):
        print(f"[DEBUG] Line preview AA = {tm.antialiasing}")
        for line in tm.preview_lines:
            tm.view.scene.removeItem(line)
        tm.preview_lines.clear()

        preview = AAPathItem(path, use_aa=tm.antialiasing)
        preview.setPen(QPen(QColor(0, 0, 0), tm.brush_size))
        preview.setZValue(1)
        tm.view.scene.addItem(preview)
        tm.preview_lines.append(preview)