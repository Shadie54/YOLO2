import sys
import math
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsTextItem, QToolBar, QFontComboBox, QSpinBox, QLabel
)
from PyQt6.QtGui import QFont, QPainter, QCursor, QPixmap
from PyQt6.QtCore import Qt, QSize
from pathlib import Path

class DraggableTextItem(QGraphicsTextItem):
    def __init__(self, text="Text"):
        super().__init__(text)

        self.setFlags(
            QGraphicsTextItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsTextItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsTextItem.GraphicsItemFlag.ItemIsFocusable
        )

        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setFont(QFont("Arial", 16))
        self.setAcceptHoverEvents(True)

        # ROTATION STATE
        self.rotating = False
        self.start_angle = 0
        self.start_rotation = 0

        BASE_DIR = Path(__file__).resolve().parent.parent
        ICON_PATH = BASE_DIR / "assets" / "icons" / "rotate.png"

        pixmap = QPixmap(str(ICON_PATH)).scaled(24, 24)
        self.rotate_cursor = QCursor(pixmap, 12, 12)

        self.update_transform_origin()
        self.margin = 6

    def update_transform_origin(self):
        self.setTransformOriginPoint(self.boundingRect().center())

    def is_near_edge(self, pos):
        rect = self.boundingRect()
        return (
            abs(pos.x() - rect.left()) < self.margin or
            abs(pos.x() - rect.right()) < self.margin or
            abs(pos.y() - rect.top()) < self.margin or
            abs(pos.y() - rect.bottom()) < self.margin
        )

    def hoverMoveEvent(self, event):
        pos = event.pos()
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            # ihneď zmena na rotate kurzor, aj keď sa myš ešte nepohnula
            self.setCursor(self.rotate_cursor)
        elif self.is_near_edge(pos):
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.setCursor(Qt.CursorShape.IBeamCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        self.update_transform_origin()
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            # začiatok rotácie
            self.rotating = True
            center = self.mapToScene(self.transformOriginPoint())
            mouse_pos = event.scenePos()
            dx = mouse_pos.x() - center.x()
            dy = mouse_pos.y() - center.y()
            self.start_angle = math.degrees(math.atan2(dy, dx))
            self.start_rotation = self.rotation()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.rotating:
            center = self.mapToScene(self.transformOriginPoint())
            mouse_pos = event.scenePos()
            dx = mouse_pos.x() - center.x()
            dy = mouse_pos.y() - center.y()
            current_angle = math.degrees(math.atan2(dy, dx))
            angle_diff = current_angle - self.start_angle
            self.setRotation(self.start_rotation + angle_diff)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.rotating = False
        super().mouseReleaseEvent(event)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.update_transform_origin()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Shift:
            # okamžite prepni kurzor na rotate
            self.setCursor(self.rotate_cursor)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Shift:
            # obnov kurzor podľa pozície myši
            mouse_pos = self.mapFromScene(
                self.scene().views()[0].mapToScene(self.scene().views()[0].mapFromGlobal(QCursor.pos())))
            if self.is_near_edge(mouse_pos):
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.IBeamCursor)
        super().keyReleaseEvent(event)

class GraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

    def mouseDoubleClickEvent(self, event):
        pos = self.mapToScene(event.pos())
        text_item = DraggableTextItem("Edituj ma")
        text_item.setPos(pos)
        self.scene().addItem(text_item)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene()
        self.view = GraphicsView(self.scene)
        self.setCentralWidget(self.view)

        self.setWindowTitle("Text Editor Tool")
        self.create_toolbar()

        # sync toolbar pri selection change
        self.scene.selectionChanged.connect(self.sync_toolbar)

    def create_toolbar(self):
        toolbar = QToolBar("Text Tools")
        self.addToolBar(toolbar)

        self.font_box = QFontComboBox()
        self.font_box.currentFontChanged.connect(self.change_font)
        toolbar.addWidget(QLabel("Font: "))
        toolbar.addWidget(self.font_box)

        self.size_box = QSpinBox()
        self.size_box.setRange(6, 100)
        self.size_box.setValue(16)
        self.size_box.valueChanged.connect(self.change_size)
        toolbar.addWidget(QLabel(" Size: "))
        toolbar.addWidget(self.size_box)

    def get_selected_text_item(self):
        items = self.scene.selectedItems()
        if items and isinstance(items[0], QGraphicsTextItem):
            return items[0]
        return None

    def change_font(self, font):
        item = self.get_selected_text_item()
        if item:
            current = item.font()
            current.setFamily(font.family())
            item.setFont(current)

    def change_size(self, size):
        item = self.get_selected_text_item()
        if item:
            current = item.font()
            current.setPointSize(size)
            item.setFont(current)

    def sync_toolbar(self):
        item = self.get_selected_text_item()
        if item:
            current_font = item.font()
            self.font_box.setCurrentFont(current_font)
            self.size_box.setValue(current_font.pointSize())


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()