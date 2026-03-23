# tools/text.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QFontComboBox, QSpinBox, QPushButton, QColorDialog
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt
from items.items import TextItem

class TextTool:
    """Text tool s panelom na nastavenie fontu, veľkosti, štýlu, farby a vrstvy"""

    def __init__(self):
        self.text_item = None        # aktuálny TextItem
        self.editing = False         # či je aktívne písanie
        # nastavenia pre nový text
        self.current_font = QFont("Arial", 16)
        self.current_bold = False
        self.current_italic = False
        self.current_size = 16
        self.current_color = QColor("black")

    # ===========================
    # TEXT PANEL METHODS
    # ===========================
    def set_font(self, font):
        self.current_font = font
        if self.text_item:
            f = self.text_item.font()
            f.setFamily(font.family())
            self.text_item.setFont(f)

    def set_size(self, size):
        self.current_size = size
        if self.text_item:
            f = self.text_item.font()
            f.setPointSize(size)
            self.text_item.setFont(f)

    def set_bold(self, bold):
        self.current_bold = bold
        if self.text_item:
            f = self.text_item.font()
            f.setBold(bold)
            self.text_item.setFont(f)

    def set_italic(self, italic):
        self.current_italic = italic
        if self.text_item:
            f = self.text_item.font()
            f.setItalic(italic)
            self.text_item.setFont(f)

    def set_color(self, color=None):
        if color is None:
            color = QColorDialog.getColor()
            if not color.isValid():
                return
        self.current_color = color
        if self.text_item:
            self.text_item.setDefaultTextColor(color)

    # ===========================
    # LAYER METHODS
    # ===========================
    def bring_forward(self):
        if self.text_item:
            self.text_item.setZValue(self.text_item.zValue() + 1)
            #self.log(f"Z-value: {item.zValue()}")

    def send_backward(self):
        if self.text_item:
            self.text_item.setZValue(self.text_item.zValue() - 1)
            #self.log(f"Z-value: {item.zValue()}")
    # ===========================
    # MOUSE EVENTS
    # ===========================
    def mousePress(self, manager, event):
        scene_pos = manager.view.mapToScene(event.pos())
        if not self.editing:
            # vytvoríme nový TextItem
            self.text_item = TextItem(
                text="",
                font=self.current_font,
                color=self.current_color
            )
            f = self.text_item.font()
            f.setBold(self.current_bold)
            f.setItalic(self.current_italic)
            f.setPointSize(self.current_size)
            self.text_item.setFont(f)

            self.text_item.setPos(scene_pos)
            manager.view.scene.addItem(self.text_item)
            self.text_item.setFocus()
            self.editing = True
        else:
            pass  # klik mimo nezasahuje

    def mouseMove(self, manager, event):
        # TextTool sa nepohybuje pri drag
        pass

    def mouseRelease(self, manager, event):
        pass

    # ===========================
    # KEY EVENTS
    # ===========================
    def keyPress(self, manager, event):
        if not self.editing or not self.text_item:
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._finalize_text(manager)
        elif event.key() == Qt.Key.Key_Escape:
            manager.view.scene.removeItem(self.text_item)
            self.text_item = None
            self.editing = False

    # ===========================
    # FINALIZE
    # ===========================
    def _finalize_text(self, manager):
        if self.text_item:
            manager.add_to_undo(self.text_item)
            self.text_item.clearFocus()
            self.text_item = None
        self.editing = False