from PyQt6.QtGui import QPen, QColor, QPainterPath
from PyQt6.QtWidgets import QGraphicsPathItem
from PyQt6.QtCore import QPointF
from items.items import BezierPoint
from .tools_helpers import TempPoint
import numpy as np

class PolycurveTool:
    """POLYCURVE nástroj - hladké krivky cez Bezier body"""

    def mousePress(self, tm, event):
        view = tm.view
        scene_pos = view.mapToScene(event.position().toPoint())
        if not view.pixmap_item:
            return

        from PyQt6.QtCore import Qt
        if event.button() == Qt.MouseButton.RightButton:
            if tm.current_poly_points:
                last_point = tm.current_poly_points.pop()
                view.scene.removeItem(last_point)
                tm.log(f"Removed point, remaining: {len(tm.current_poly_points)}")
                if tm.current_poly_points:
                    self.update_curve_path(tm)
                else:
                    self._clear_preview(tm, reset_drag=False)
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        for item in view.scene.items(scene_pos):
            if isinstance(item, BezierPoint):
                return

        point = BezierPoint(scene_pos.x(), scene_pos.y(), parent_manager=tm)
        view.scene.addItem(point)
        tm.current_poly_points.append(point)
        tm.log(f"Added point, total points: {len(tm.current_poly_points)}")
        self.update_curve_path(tm)

    def mouseMove(self, tm, event):
        if not tm.current_poly_points:
            return
        scene_pos = tm.view.mapToScene(event.position().toPoint())
        temp_points = tm.current_poly_points + [TempPoint(scene_pos)]
        path = self.create_polycurve_path(tm, temp_points)
        self._update_preview(tm, path)

    def mouseRelease(self, tm, event):
        pass

    def keyPress(self, tm, event):
        from PyQt6.QtCore import Qt
        if event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            if tm.current_poly_points:
                path = self.create_polycurve_path(tm, tm.current_poly_points)
                item = QGraphicsPathItem(path)
                item.setPen(QPen(QColor(0,0,0), tm.brush_size))
                tm.view.scene.addItem(item)
                tm.view.undo_stack.append(item)
            self._clear_preview(tm, reset_drag=False)
        elif event.key() == Qt.Key.Key_Escape:
            self._clear_preview(tm, reset_drag=False)

    # ---------- PATH LOGIC ----------
    def create_polycurve_path(self, tm, points):
        if len(points) < 2:
            return QPainterPath(points[0].pos())
        path = QPainterPath(points[0].pos())
        pts = [p.pos() for p in points]
        p_ext = [pts[0]] + pts + [pts[-1]]
        for i in range(1, len(p_ext)-2):
            p0,p1,p2,p3 = p_ext[i-1],p_ext[i],p_ext[i+1],p_ext[i+2]
            for t in np.linspace(0,1,20):
                x = 0.5*((2*p1.x())+(-p0.x()+p2.x())*t+(2*p0.x()-5*p1.x()+4*p2.x()-p3.x())*t**2+(-p0.x()+3*p1.x()-3*p2.x()+p3.x())*t**3)
                y = 0.5*((2*p1.y())+(-p0.y()+p2.y())*t+(2*p0.y()-5*p1.y()+4*p2.y()-p3.y())*t**2+(-p0.y()+3*p1.y()-3*p2.y()+p3.y())*t**3)
                pt = QPointF(x,y)
                if t==0 and i==1: prev=pt; continue
                path.lineTo(pt)
        return path

    def update_curve_path(self, tm):
        if not tm.current_poly_points:
            return
        path = self.create_polycurve_path(tm, tm.current_poly_points)
        self._update_preview(tm, path)

    # ---------- PREVIEW ----------
    def _update_preview(self, tm, path):
        for line in tm.preview_lines:
            tm.view.scene.removeItem(line)
        tm.preview_lines.clear()
        preview = QGraphicsPathItem(path)
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