from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPen, QColor, QPainterPath
from PyQt6.QtWidgets import QGraphicsPathItem
from items import YoloBox, BezierPoint, TempPoint
import numpy as np

class ToolManager:
    def __init__(self, view, log_callback=None):
        self.view = view
        self.current_tool = None
        self.current_poly_points = []
        self.preview_lines = []
        self.log_callback = log_callback

        # Pencil / Eraser
        self.brush_size = 2
        self.current_path_item = None
        self.last_pos = None
        self.first_move_done = False

    # ---------- LOG ----------
    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    # ---------- TOOL ----------
    def set_tool(self, tool_name):
        # dokonči prebiehajúce PENCIL/ERASER kreslenie
        if getattr(self.view,"drawing",False) and self.current_tool in ["PENCIL","ERASER"]:
            if self.current_path_item:
                self.view.undo_stack.append(self.current_path_item)
                self.current_path_item = None
            self.view.drawing = False

        self._clear_preview()
        self.current_tool = tool_name
        self.first_move_done = False

        if tool_name is None:
            self.view.setDragMode(self.view.DragMode.ScrollHandDrag)
        else:
            self.view.setDragMode(self.view.DragMode.NoDrag)
        self.log(f"[Tool] Tool set to {tool_name if tool_name else 'NONE'}")

    # ---------- RESET ----------
    def reset(self):
        for line in self.preview_lines:
            self.view.scene.removeItem(line)
        self.preview_lines.clear()
        self.current_poly_points.clear()

    # ---------- MOUSE ----------
    def mousePressEvent(self, event):
        if not self.view.pixmap_item:
            return

        scene_pos = self.view.mapToScene(event.position().toPoint())

        # Pravý klik: odstráni posledný bod polytoolov
        if event.button() == Qt.MouseButton.RightButton:
            if self.current_tool in ["LINE","POLYLINE","POLYCURVE"] and self.current_poly_points:
                last_point = self.current_poly_points.pop()
                self.view.scene.removeItem(last_point)
                self.update_curve_path()
                self.log(f"Removed point, remaining: {len(self.current_poly_points)}")
            return

        # NONE nástroj: nič nekreslí
        if self.current_tool is None:
            return

        # PENCIL / ERASER
        if self.current_tool in ["PENCIL","ERASER"]:
            self.view.drawing = True
            path = QPainterPath()
            path.moveTo(scene_pos)
            self.current_path_item = QGraphicsPathItem(path)
            color = QColor(255,255,255) if self.current_tool=="ERASER" else QColor(0,0,0)
            pen = QPen(color, self.brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            self.current_path_item.setPen(pen)
            self.view.scene.addItem(self.current_path_item)
            self.last_pos = scene_pos
            self.first_move_done = False
            return

        # POLYTOOLS
        if self.current_tool in ["LINE","POLYLINE","POLYCURVE"]:
            items_at_pos = self.view.scene.items(scene_pos)
            for item in items_at_pos:
                if isinstance(item, BezierPoint):
                    return
            if self.current_tool == "LINE" and len(self.current_poly_points) >= 2:
                return
            point = BezierPoint(scene_pos.x(), scene_pos.y(), parent_manager=self)
            self.view.scene.addItem(point)
            self.current_poly_points.append(point)
            self.update_curve_path()
            self.log(f"Added point, total points: {len(self.current_poly_points)}")

    def mouseMoveEvent(self, event):
        scene_pos = self.view.mapToScene(event.position().toPoint())

        # PENCIL / ERASER kreslenie
        if self.current_tool in ["PENCIL","ERASER"] and getattr(self.view,"drawing",False):
            if not self.first_move_done:
                self.last_pos = scene_pos
                self.first_move_done = True
                return
            path = self.current_path_item.path()
            path.moveTo(self.last_pos)
            path.lineTo(scene_pos)
            self.current_path_item.setPath(path)
            self.last_pos = scene_pos
            return

        # POLYTOOLS preview
        if self.current_tool in ["LINE","POLYLINE","POLYCURVE"] and self.current_poly_points:
            temp_points = self.current_poly_points + [TempPoint(scene_pos)]
            if self.current_tool=="POLYCURVE":
                path = self.create_polycurve_path(temp_points)
            else:
                path = self.create_standard_path(temp_points)
            self._update_preview(path)

    def mouseReleaseEvent(self, event):
        # PENCIL / ERASER koniec kreslenia
        if self.current_tool in ["PENCIL","ERASER"]:
            if self.current_path_item:
                self.view.undo_stack.append(self.current_path_item)
                self.current_path_item = None
            self.view.drawing = False
            return

        # POLYTOOLS koniec
        if self.current_tool in ["LINE","POLYLINE","POLYCURVE"]:
            if len(self.current_poly_points) == 0:
                return
            if self.current_tool == "LINE" and len(self.current_poly_points) == 2:
                path = self.create_standard_path(self.current_poly_points)
                item = QGraphicsPathItem(path)
                item.setPen(QPen(QColor(0,0,0), self.brush_size))
                self.view.scene.addItem(item)
                self.view.undo_stack.append(item)
                self._clear_preview()

    # ---------- KEY ----------
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self._clear_preview()
        elif key in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            if self.current_poly_points:
                path = (self.create_polycurve_path(self.current_poly_points)
                        if self.current_tool=="POLYCURVE" else
                        self.create_standard_path(self.current_poly_points))
                item = QGraphicsPathItem(path)
                item.setPen(QPen(QColor(0,0,0), self.brush_size))
                self.view.scene.addItem(item)
                self.view.undo_stack.append(item)
                self._clear_preview()
        elif key == Qt.Key.Key_Delete:
            for item in self.view.scene.selectedItems():
                if item in self.view.undo_stack:
                    self.view.undo_stack.remove(item)
                self.view.scene.removeItem(item)

    # ---------- PATH HELPERS ----------
    def create_standard_path(self, points):
        if len(points) < 2:
            return QPainterPath(points[0].pos())
        path = QPainterPath(points[0].pos())
        for pt in points[1:]:
            path.lineTo(pt.pos())
        return path

    def create_polycurve_path(self, points):
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

    # ---------- UPDATE / CLEAR ----------
    def update_curve_path(self):
        if not self.current_poly_points:
            return
        path = (self.create_polycurve_path(self.current_poly_points)
                if self.current_tool=="POLYCURVE" else
                self.create_standard_path(self.current_poly_points))
        self._update_preview(path)

    def _update_preview(self, path_or_item):
        for line in self.preview_lines:
            self.view.scene.removeItem(line)
        self.preview_lines.clear()
        item = QGraphicsPathItem(path_or_item) if not isinstance(path_or_item,QGraphicsPathItem) else path_or_item
        if not isinstance(path_or_item,QGraphicsPathItem):
            item.setPen(QPen(QColor(0,0,0), self.brush_size))
        self.view.scene.addItem(item)
        self.preview_lines.append(item)

    def _clear_preview(self):
        for pt in self.current_poly_points:
            self.view.scene.removeItem(pt)
        for line in self.preview_lines:
            self.view.scene.removeItem(line)
        self.current_poly_points.clear()
        self.preview_lines.clear()