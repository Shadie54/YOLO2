# tools/select.py
import math
from PyQt6.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem, QToolTip
from PyQt6.QtGui import QPen, QColor, QPixmap, QCursor
from PyQt6.QtCore import Qt, QRectF, QPoint
from pathlib import Path
from utils.layer_tooltip import show_layer_tooltip

class SelectionItem(QGraphicsPixmapItem):
    """Objekt, ktorý môže byť vybraný, presunutý a rotovaný."""

    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.setFlags(
            QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable
        )
        self.setAcceptHoverEvents(True)
        #self.setZValue(1000)

        # ROTATION
        self.rotating = False
        self.start_angle = 0
        self.start_rotation = 0

        # kurzory
        BASE_DIR = Path(__file__).resolve().parent.parent
        rotate_icon = QPixmap(str(BASE_DIR / "assets" / "icons" / "rotate.png")).scaled(24, 24)
        self.rotate_cursor = QCursor(rotate_icon, 12, 12)
        self.move_cursor = QCursor(Qt.CursorShape.SizeAllCursor)

        self.margin = 6
        self.setTransformOriginPoint(self.boundingRect().center())

    # ---------------- HELPERS ----------------
    def is_near_edge(self, pos):
        r = self.boundingRect()
        return (
            abs(pos.x() - r.left()) < self.margin or
            abs(pos.x() - r.right()) < self.margin or
            abs(pos.y() - r.top()) < self.margin or
            abs(pos.y() - r.bottom()) < self.margin
        )

    # ---------------- EVENTS ----------------
    def hoverMoveEvent(self, event):
        modifiers = event.modifiers()

        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            self.setCursor(self.rotate_cursor)
        else:
            # Move cursor na celý objekt
            self.setCursor(self.move_cursor)

        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        self.setTransformOriginPoint(self.boundingRect().center())

        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.rotating = True
            center = self.mapToScene(self.transformOriginPoint())
            mouse = event.scenePos()
            dx = mouse.x() - center.x()
            dy = mouse.y() - center.y()
            self.start_angle = math.degrees(math.atan2(dy, dx))
            self.start_rotation = self.rotation()
            self.setCursor(self.rotate_cursor)
            event.accept()
            return

        if self.is_near_edge(event.pos()):
            self.setCursor(self.move_cursor)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.rotating:
            center = self.mapToScene(self.transformOriginPoint())
            mouse = event.scenePos()
            dx = mouse.x() - center.x()
            dy = mouse.y() - center.y()
            angle = math.degrees(math.atan2(dy, dx))
            diff = angle - self.start_angle
            self.setRotation(self.start_rotation + diff)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.rotating = False
        super().mouseReleaseEvent(event)


# ----------------- SELECT TOOL -----------------
class SelectTool:
    def __init__(self, manager):
        self.manager = manager
        self.origin = None
        self.temp_rect = None
        self.selected_item = None

    # ---------- MOUSE ----------
    def mousePress(self, manager, event):
        view = manager.view
        scene = view.scene

        if not view.pixmap_item:
            return

        item = scene.itemAt(view.mapToScene(event.position().toPoint()), view.transform())

        if item is None or item == view.pixmap_item:
            # Začiatok selekcie (rubber band)
            self.origin = view.mapToScene(event.position().toPoint())
            self.temp_rect = QGraphicsRectItem(QRectF(self.origin, self.origin))
            pen = QPen(QColor(0, 120, 215), 2, Qt.PenStyle.DashLine)
            self.temp_rect.setPen(pen)
            self.temp_rect.setBrush(QColor(0, 120, 215, 50))
            self.temp_rect.setZValue(2000)
            scene.addItem(self.temp_rect)
        else:
            # Klik na existujúci objekt
            self.selected_item = item
            item.setSelected(True)

            # --- tooltip pomocou globálneho helpera ---
            show_layer_tooltip(item, event, manager.view.viewport())

    def mouseMove(self, manager, event):
        view = manager.view
        scene = view.scene
        if self.temp_rect:
            rect = QRectF(self.origin, view.mapToScene(event.position().toPoint())).normalized()
            self.temp_rect.setRect(rect)

    def mouseRelease(self, manager, event):
        view = manager.view
        scene = view.scene
        if self.temp_rect:
            rect = self.temp_rect.rect()
            if rect.width() > 5 and rect.height() > 5:
                pixmap = view.pixmap_item.pixmap().copy(
                    int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height())
                )
                item = SelectionItem(pixmap)
                item.setPos(rect.topLeft())
                scene.addItem(item)
                item.setSelected(True)
                manager.add_to_undo(item)
            scene.removeItem(self.temp_rect)
            self.temp_rect = None

    def mouseReleaseEvent(self, manager, event):
        self.mouseRelease(manager, event)