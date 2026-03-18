from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPen, QColor, QPainterPath
from PyQt6.QtWidgets import QGraphicsPathItem
from items import YoloBox, BezierPoint
from tools_helpers import TempPoint
import numpy as np

class ToolManager:
    def __init__(self, view, log_callback=None):
        self.view = view
        self.current_tool = "BOX"
        self.current_poly_points = []
        self.preview_lines = []
        self.log_callback = log_callback

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def set_tool(self, tool_name):
        self.current_tool = tool_name
        self._clear_preview()
        self.log(f"[Tool] Tool set to {tool_name}")

    # ---------------- MOUSE EVENTS ----------------
    def mousePressEvent(self, event):
        scene_pos = self.view.mapToScene(event.position().toPoint())
        if not self.view.pixmap_item:
            return

        # Pravý klik: odstráni posledný bod poly nástrojov
        if event.button() == Qt.MouseButton.RightButton:
            if self.current_tool in ["LINE","POLYLINE","POLYCURVE"] and self.current_poly_points:
                last_point = self.current_poly_points.pop()
                self.view.scene.removeItem(last_point)
                self.log(f"Removed point, remaining: {len(self.current_poly_points)}")
                self.update_curve_path()
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        # BOX drawing
        if self.current_tool == "BOX":
            self.view.setDragMode(self.view.DragMode.NoDrag)
            self.view.drawing = True
            self.view.start_pos = scene_pos
            self.view.preview_rect = self.view.scene.addRect(scene_pos.x(), scene_pos.y(), 0, 0, QPen(QColor(0,255,0),2))
            return

        # Poly tools
        if self.current_tool in ["LINE","POLYLINE","POLYCURVE"]:
            for item in self.view.scene.items(scene_pos):
                if isinstance(item, BezierPoint):
                    return

            if self.current_tool == "LINE" and len(self.current_poly_points) >= 2:
                return

            point = BezierPoint(scene_pos.x(), scene_pos.y(), parent_manager=self)
            self.view.scene.addItem(point)
            self.current_poly_points.append(point)
            self.log(f"Added point, total points: {len(self.current_poly_points)}")
            self.update_curve_path()

    def mouseMoveEvent(self, event):
        scene_pos = self.view.mapToScene(event.position().toPoint())
        # BOX drag
        if self.current_tool=="BOX" and self.view.drawing and self.view.preview_rect:
            rect = self.view.preview_rect.rect()
            rect.setBottomRight(scene_pos)
            self.view.preview_rect.setRect(rect)

        # Poly preview
        if self.current_tool in ["LINE","POLYLINE","POLYCURVE"] and self.current_poly_points:
            if self.current_tool=="POLYCURVE":
                temp_points = self.current_poly_points + [TempPoint(scene_pos)]
                path = self.create_polycurve_path(temp_points)
            else:
                if self.current_tool=="LINE" and len(self.current_poly_points)>=2:
                    path = self.create_standard_path(self.current_poly_points)
                else:
                    temp_points = self.current_poly_points + [TempPoint(scene_pos)]
                    path = self.create_standard_path(temp_points)
            self._update_preview(path)

    def mouseReleaseEvent(self, event):
        if self.current_tool=="BOX" and self.view.drawing and self.view.preview_rect:
            box = YoloBox(self.view.preview_rect.rect())
            self.view.scene.addItem(box)
            self.view.undo_stack.append(box)
            self.view.scene.removeItem(self.view.preview_rect)
            self.view.preview_rect = None
            self.view.drawing = False
            self.view.setDragMode(self.view.DragMode.ScrollHandDrag)

    # ---------------- KEY EVENTS ----------------
    def keyPressEvent(self, event):
        from PyQt6.QtCore import Qt
        if event.key()==Qt.Key.Key_Escape:
            self._clear_preview()
        elif event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            if self.current_poly_points:
                if self.current_tool=="POLYCURVE":
                    path = self.create_polycurve_path(self.current_poly_points)
                else:
                    path = self.create_standard_path(self.current_poly_points)
                curve_item = QGraphicsPathItem(path)
                curve_item.setPen(QPen(QColor(0,0,0),2))
                self.view.scene.addItem(curve_item)
                self.view.undo_stack.append(curve_item)
            self._clear_preview()
        elif event.key() == Qt.Key.Key_Delete:
            for item in self.view.scene.selectedItems():
                if isinstance(item,(YoloBox,QGraphicsPathItem)):
                    if item in self.view.undo_stack:
                        self.view.undo_stack.remove(item)
                    self.view.scene.removeItem(item)

    # ---------------- PATH HELPERS ----------------
    def create_standard_path(self, points):
        path = QPainterPath(points[0].pos())
        for pt in points[1:]:
            path.lineTo(pt.pos())
        return path

    def create_polycurve_path(self, points):
        path = QPainterPath(points[0].pos())
        pts = [p.pos() for p in points]
        p_ext = [pts[0]] + pts + [pts[-1]]
        for i in range(1, len(p_ext)-2):
            p0,p1,p2,p3 = p_ext[i-1],p_ext[i],p_ext[i+1],p_ext[i+2]
            for t in np.linspace(0,1,20):
                x = 0.5*((2*p1.x())+(-p0.x()+p2.x())*t + (2*p0.x()-5*p1.x()+4*p2.x()-p3.x())*t**2 + (-p0.x()+3*p1.x()-3*p2.x()+p3.x())*t**3)
                y = 0.5*((2*p1.y())+(-p0.y()+p2.y())*t + (2*p0.y()-5*p1.y()+4*p2.y()-p3.y())*t**2 + (-p0.y()+3*p1.y()-3*p2.y()+p3.y())*t**3)
                path.lineTo(QPointF(x,y))
        return path

    # ---------------- UPDATE / PREVIEW ----------------
    def update_curve_path(self):
        if not self.current_poly_points:
            return
        if self.current_tool=="POLYCURVE":
            path = self.create_polycurve_path(self.current_poly_points)
        else:
            path = self.create_standard_path(self.current_poly_points)
        self._update_preview(path)

    def _update_preview(self, path):
        for line in self.preview_lines:
            self.view.scene.removeItem(line)
        self.preview_lines.clear()
        preview = QGraphicsPathItem(path)
        preview.setPen(QPen(QColor(0,0,0),2))
        preview.setZValue(1)
        self.view.scene.addItem(preview)
        self.preview_lines.append(preview)

    def _clear_preview(self):
        for point in self.current_poly_points:
            self.view.scene.removeItem(point)
        for line in self.preview_lines:
            self.view.scene.removeItem(line)
        self.current_poly_points.clear()
        self.preview_lines.clear()
        self.view.setDragMode(self.view.DragMode.ScrollHandDrag)