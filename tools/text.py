# tools/text.py
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent, QFont, QColor
from items.items import TextItem
import math

class TextTool:
    def __init__(self):
        self.editing = False
        self.text_item = None

    # ---------- MOUSE ----------
    def mousePress(self, manager, event):
        scene_pos = manager.view.mapToScene(event.pos())
        if not self.editing:
            # vytvor nový text
            self.text_item = TextItem(
                font=getattr(manager.view, 'default_font', QFont("Arial", 16)),
                color=getattr(manager.view, 'default_color', QColor("black"))
            )
            self.text_item.setPos(scene_pos)
            manager.view.scene.addItem(self.text_item)
            self.text_item.setFocus()
            self.editing = True

    # ---------- MOUSE MOVE ----------
    def mouseMove(self, manager, event):
        # TextTool nevyžaduje pohyb okrem drag/rotate, handled v TextItem
        pass

    # ---------- MOUSE RELEASE ----------
    def mouseRelease(self, manager, event):
        pass

    # ---------- KEY ----------
    def keyPress(self, manager, event: QKeyEvent):
        if not self.editing:
            return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._finalize_text(manager)
        elif event.key() == Qt.Key.Key_Escape:
            self._cancel_text(manager)

    # ---------- FINALIZE ----------
    def _finalize_text(self, manager):
        if self.text_item:
            manager.add_to_undo(self.text_item)  # uložíme text do undo
            self.text_item.clearFocus()  # zrušíme rámček
            self.text_item = None
        self.editing = False
        # NEPREPÍNAME nástroj na None → TextTool zostáva aktívny

    # ---------- CANCEL ----------
    def _cancel_text(self, manager):
        if self.text_item:
            manager.view.scene.removeItem(self.text_item)
            self.text_item.clearFocus()
            self.text_item = None
        self.editing = False
        manager.set_tool(None)  # ESC zruší aj nástroj