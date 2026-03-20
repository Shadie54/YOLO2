# items/items.py
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsItem
from PyQt6.QtGui import QPen, QBrush, QColor

class YoloBox(QGraphicsRectItem):
    def __init__(self, rect, label="object"):
        super().__init__(rect)
        self.label = label
        self.setPen(QPen(QColor(255,0,0), 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)

class BezierPoint(QGraphicsEllipseItem):
    def __init__(self, x, y, parent_manager, radius=5):
        super().__init__(-radius, -radius, radius*2, radius*2)
        self.setPos(x, y)
        self.parent_manager = parent_manager

        self.setBrush(QBrush(QColor(0, 255, 255)))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(10)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.parent_manager and self.parent_manager.current_tool:
                # zavolá správnu aktualizáciu podľa nástroja
                tool_name = self.parent_manager.current_tool
                if tool_name == "POLYCURVE":
                    from tools.polycurve import PolycurveTool
                    PolycurveTool().update_curve_path(self.parent_manager)
                elif tool_name == "POLYLINE":
                    from tools.polyline import PolylineTool
                    PolylineTool().update_polyline(self.parent_manager)
        return super().itemChange(change, value)

class TempPoint:
    """Dočasný bod pre náhľad cesty"""
    def __init__(self, pos):
        self._pos = pos

    def pos(self):
        return self._pos