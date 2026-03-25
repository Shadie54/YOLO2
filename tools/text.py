# tools/text.py
import math, os
from PyQt6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PyQt6.QtGui import QFont, QColor, QCursor, QPixmap, QPen
from PyQt6.QtCore import Qt
from pathlib import Path

class TextItem(QGraphicsTextItem):
    def __init__(self, text="Sem píš..."):
        super().__init__(text)

        self.setFont(QFont("Arial", 16))
        self.setDefaultTextColor(QColor("black"))

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
        )

        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setAcceptHoverEvents(True)

        # ROTATION
        self.rotating = False
        self.start_angle = 0
        self.start_rotation = 0

        BASE_DIR = Path(__file__).resolve().parent.parent
        ICON_PATH = BASE_DIR / "assets" / "icons" / "rotate.png"

        pixmap = QPixmap(str(ICON_PATH)).scaled(24, 24)
        self.rotate_cursor = QCursor(pixmap, 12, 12)

        self.margin = 6
        self.update_origin()

    def update_origin(self):
        self.setTransformOriginPoint(self.boundingRect().center())

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
        pos = event.pos()

        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.setCursor(self.rotate_cursor)
        elif self.is_near_edge(pos):
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.setCursor(Qt.CursorShape.IBeamCursor)

        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        self.update_origin()

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
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.rotating = False
        super().mouseReleaseEvent(event)

    def focusOutEvent(self, event):
        self.update_origin()
        super().focusOutEvent(event)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if self.isSelected():
            pen = QPen(QColor(0, 120, 255), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.boundingRect())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Shift:
            self.setCursor(self.rotate_cursor)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Shift:
            # obnov správny kurzor podľa pozície myši
            view = self.scene().views()[0]
            mouse_scene = view.mapToScene(view.mapFromGlobal(QCursor.pos()))
            mouse_local = self.mapFromScene(mouse_scene)

            if self.is_near_edge(mouse_local):
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.IBeamCursor)

        super().keyReleaseEvent(event)
# ---------------- TOOL ----------------
class TextTool:
    def __init__(self, manager, font_panel=None):
        self.manager = manager
        self.font_panel = font_panel
        self.text_item = None

    def mousePress(self, manager, event):
        scene = manager.view.scene
        scene_pos = manager.view.mapToScene(event.position().toPoint())

        # deselect všetko
        for item in scene.items():
            if isinstance(item, TextItem):
                item.setSelected(False)

        # klik na existujúci
        for item in scene.items(scene_pos):
            if isinstance(item, TextItem):
                self.text_item = item
                item.setSelected(True)
                item.setFocus(Qt.FocusReason.MouseFocusReason)
                self.sync_panel()
                return

        # nový textbox
        self.text_item = TextItem("Sem píš...")
        self.text_item.setPos(scene_pos)

        scene.addItem(self.text_item)
        self.text_item.setSelected(True)
        self.text_item.setFocus(Qt.FocusReason.MouseFocusReason)

        manager.add_to_undo(self.text_item)
        self.sync_panel()

    def mouseMove(self, manager, event):
        pass  # nič – rieši TextItem

    def mouseRelease(self, manager, event):
        pass

    # -------- PANEL --------
    def sync_panel(self):
        if not self.font_panel or not self.text_item:
            return
        f = self.text_item.font()
        self.font_panel.font_box.setCurrentFont(f)
        self.font_panel.size_box.setValue(f.pointSize())

    def set_font(self, font):
        if self.text_item:
            f = self.text_item.font()
            f.setFamily(font.family())
            self.text_item.setFont(f)

    def set_size(self, size):
        if self.text_item:
            f = self.text_item.font()
            f.setPointSize(size)
            self.text_item.setFont(f)

    def set_bold(self, val):
        if self.text_item:
            f = self.text_item.font()
            f.setBold(val)
            self.text_item.setFont(f)

    def set_italic(self, val):
        if self.text_item:
            f = self.text_item.font()
            f.setItalic(val)
            self.text_item.setFont(f)

    def set_color(self):
        pass