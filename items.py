#items.py
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsItem
from PyQt6.QtGui import QPen, QBrush, QColor

class YoloBox(QGraphicsRectItem):
    def __init__(self, rect, label="object"):
        super().__init__(rect)
        self.label = label
        self.normal_pen = QPen(QColor(255,0,0),2)
        self.hover_pen = QPen(QColor(255,255,0),3)
        self.selected_pen = QPen(QColor(0,255,255),3)
        self.setPen(self.normal_pen)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)

    def hoverEnterEvent(self, event):
        if not self.isSelected(): self.setPen(self.hover_pen)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self.isSelected(): self.setPen(self.normal_pen)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.isSelected(): self.setPen(self.selected_pen)

class BezierPoint(QGraphicsEllipseItem):
    """Interaktívny Bezier bod s dynamickým preview"""
    def __init__(self, x, y, parent_manager, radius=5):
        super().__init__(-radius,-radius,radius*2,radius*2)
        self.setPos(x,y)
        self.radius = radius
        self.parent_manager = parent_manager
        self.setBrush(QBrush(QColor(0,255,255)))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(10)  # nad preview
        self.setAcceptHoverEvents(True)

    def itemChange(self, change, value):
        print("POINT MOVED -> updating curve")
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene() and self.parent_manager:
            # dynamicky aktualizuje preview path
            self.parent_manager.update_curve_path()
        return super().itemChange(change, value)

    def keyPressEvent(self, event):
        from PyQt6.QtCore import Qt
        if event.key() == Qt.Key.Key_Delete:
            if self.scene() and self.parent_manager:
                if self in self.parent_manager.current_poly_points:
                    self.parent_manager.current_poly_points.remove(self)
                self.scene().removeItem(self)
                self.parent_manager.update_curve_path()
        super().keyPressEvent(event)