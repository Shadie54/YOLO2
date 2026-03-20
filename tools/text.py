# tools/text.py
from PyQt6.QtWidgets import QGraphicsTextItem
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class TextTool:
    def mousePress(self, tm, event):
        scene_pos = tm.view.mapToScene(event.position().toPoint())
        # vytvoríme dočasný QGraphicsTextItem
        text_item = QGraphicsTextItem("Type here")
        text_item.setPos(scene_pos)
        text_item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        font = QFont("Arial", 24)
        text_item.setFont(font)
        tm.view.scene.addItem(text_item)
        tm.text_edit_item = text_item
        text_item.setFocus()

    def mouseMove(self, tm, event):
        pass

    def mouseRelease(self, tm, event):
        pass

    def keyPress(self, tm, event):
        # Text tool spracuje všetky klávesy sám
        pass