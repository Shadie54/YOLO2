# items/items.py
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsItem
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QCursor
from PyQt6.QtCore import Qt
import math

from PyQt6.QtWidgets import QGraphicsRectItem
from PyQt6.QtGui import QPen, QColor, QBrush, QCursor
from PyQt6.QtCore import Qt

class YoloBox(QGraphicsRectItem):
    def __init__(self, rect, label, scene):
        super().__init__(rect)
        self.label = label
        self.scene_ref = scene

        # 🔴 červený rámček
        self.setPen(QPen(QColor(255, 0, 0), 2))
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))

        # hover + kurzor
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip(f"Klikni pre odstránenie: {label}")

    # 🟡 hover efekt
    def hoverEnterEvent(self, event):
        self.setPen(QPen(QColor(255, 255, 0), 2))
        self.setBrush(QBrush(QColor(255, 255, 255, 40)))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPen(QPen(QColor(255, 0, 0), 2))
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        rect = self.rect()

        # 🟡 offset 1px, aby nezostali kúsky červeného okraja
        offset = 1
        white_rect = QGraphicsRectItem(
            rect.adjusted(-offset, -offset, offset, offset)
        )
        white_rect.setPen(QPen(Qt.PenStyle.NoPen))
        white_rect.setBrush(QBrush(QColor(255, 255, 255)))

        self.scene_ref.addItem(white_rect)
        self.scene_ref.removeItem(self)

        super().mousePressEvent(event)
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

class TextItem(QGraphicsTextItem):
    def __init__(self, text="", font=None, color=None):
        super().__init__(text)

        if font is None:
            font = QFont("Arial", 16)
        if color is None:
            color = QColor("black")

        self.setFont(font)
        self.setDefaultTextColor(color)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)

        # Pohyb a výber
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        # Transform origin na stred pre rotáciu
        self.setTransformOriginPoint(self.boundingRect().center())

        # pre rotáciu počas shift+drag
        self._rotating = False
        self._start_angle = 0
        self._start_mouse_angle = 0

    # -----------------
    # Mouse events pre rotáciu
    # -----------------
    def mousePressEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self._rotating = True
            self._start_angle = self.rotation()

            center = self.mapToScene(self.boundingRect().center())
            mouse = self.mapToScene(event.pos())
            self._start_mouse_angle = math.degrees(
                math.atan2(mouse.y() - center.y(), mouse.x() - center.x())
            )
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._rotating:
            center = self.mapToScene(self.boundingRect().center())
            mouse = self.mapToScene(event.pos())
            current_angle = math.degrees(
                math.atan2(mouse.y() - center.y(), mouse.x() - center.x())
            )
            delta = current_angle - self._start_mouse_angle
            self.setRotation(self._start_angle + delta)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._rotating = False
        super().mouseReleaseEvent(event)