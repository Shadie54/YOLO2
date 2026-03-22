
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtGui import QPainter, QFont, QColor
from PyQt6.QtCore import Qt


class ImageView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.pixmap_item = None
        self.undo_stack = []
        self.tool_manager = None
        self.drawing = False

        # render + zoom
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(self.DragMode.ScrollHandDrag)

        self.default_font = QFont("Arial", 16)
        self.default_color = QColor("black")

    # ---------- IMAGE ----------
    def set_image(self, cv_img):
        from utils.utils import cv2_to_qpixmap
        self.scene.clear()
        self.pixmap_item = self.scene.addPixmap(cv2_to_qpixmap(cv_img))
        self.fit_image()
        self.undo_stack.clear()
        if self.tool_manager:
            self.tool_manager.reset()

    def fit_image(self):
        if self.pixmap_item:
            self.resetTransform()
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    # ---------- ZOOM ----------
    def wheelEvent(self, event):
        if not self.pixmap_item:
            return
        factor = 1.15 if event.angleDelta().y() > 0 else 0.87
        self.scale(factor, factor)

    # ---------- EVENTS ----------
    def mousePressEvent(self, event):
        if self.tool_manager:
            self.tool_manager.mousePressEvent(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.tool_manager:
            self.tool_manager.mouseMoveEvent(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.tool_manager:
            self.tool_manager.mouseReleaseEvent(event)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if self.tool_manager:
            self.tool_manager.keyPressEvent(event)
        super().keyPressEvent(event)

    # ---------- UNDO ----------
    def undo(self):
        if not self.undo_stack:
            return
        item = self.undo_stack.pop()
        if item.scene():
            self.scene.removeItem(item)