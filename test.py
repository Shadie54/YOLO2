# tools/polyline_dashed.py
from PyQt6.QtWidgets import QGraphicsPathItem
from PyQt6.QtGui import QPainterPath, QPen, QColor
from PyQt6.QtCore import Qt

class PolylineDashedTool:
    """Polyline s prerušovanou čiarou. Nastavenia: brush size, dash segment a gap."""

    def __init__(self):
        self.current_path_item = None
        self.path = None
        self.last_point = None

    def mousePress(self, tm, event):
        view = tm.view
        scene_pos = view.mapToScene(event.position().toPoint())

        # začiatok novej polyline
        if not self.path:
            self.path = QPainterPath()
            self.path.moveTo(scene_pos)
            self.current_path_item = QGraphicsPathItem(self.path)

            pen = QPen(QColor(0, 0, 0), tm.brush_size)
            pen.setStyle(Qt.PenStyle.CustomDashLine)
            pen.setDashPattern([tm.dash_segment, tm.dash_gap])
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            self.current_path_item.setPen(pen)

            view.scene.addItem(self.current_path_item)

        else:
            # pridanie ďalšieho bodu
            self.path.lineTo(scene_pos)
            self.current_path_item.setPath(self.path)

        self.last_point = scene_pos

    def mouseMove(self, tm, event):
        if self.path and self.last_point:
            view = tm.view
            scene_pos = view.mapToScene(event.position().toPoint())
            tmp_path = QPainterPath(self.path)
            tmp_path.lineTo(scene_pos)
            self.current_path_item.setPath(tmp_path)

    def mouseRelease(self, tm, event):
        # polyline sa dokončí až po finish()
        pass

    def finish(self, tm):
        """Ukončí aktuálnu polyline a uloží do undo stacku."""
        if self.current_path_item:
            tm.view.undo_stack.append(self.current_path_item)
        self.current_path_item = None
        self.path = None
        self.last_point = None

    def set_brush_size(self, tm, size):
        """Dynamicky meni brush size počas kreslenia"""
        if self.current_path_item:
            pen = self.current_path_item.pen()
            pen.setWidth(size)
            self.current_path_item.setPen(pen)

    def set_dash_pattern(self, tm, segment, gap):
        """Dynamicky meni dash pattern počas kreslenia"""
        if self.current_path_item:
            pen = self.current_path_item.pen()
            pen.setDashPattern([segment, gap])
            self.current_path_item.setPen(pen)