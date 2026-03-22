from PyQt6.QtWidgets import QGraphicsPathItem
from PyQt6.QtGui import QPainter


class AAPathItem(QGraphicsPathItem):
    def __init__(self, path, use_aa=True):
        super().__init__(path)
        self.use_aa = True if use_aa is None else use_aa

    def set_antialiasing(self, value: bool):
        self.use_aa = value
        self.update()

    def paint(self, painter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, self.use_aa)
        super().paint(painter, option, widget)
        painter.restore()