# tools/text.py
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PyQt6.QtGui import QPen, QColor, QFont
from PyQt6.QtCore import Qt, QRectF, QPointF

class TextTool:
    def __init__(self):
        self.text_item = None       # QGraphicsTextItem pre editáciu
        self.rect_item = None       # rámček okolo textu
        self.editing = False
        self.rotation_angle = 0     # aktuálny uhol rotácie

    def mousePress(self, tm, event):
        scene_pos = tm.view.mapToScene(event.position().toPoint())

        # ak práve editujeme text a klik mimo → potvrdenie
        if self.editing and not self.rect_item.contains(self.rect_item.mapFromScene(scene_pos)):
            self._finalize_text(tm)
            return

        # začíname nový text
        if not self.editing:
            self.text_item = QGraphicsTextItem("Type here")
            self.text_item.setDefaultTextColor(QColor(0, 0, 0))
            self.text_item.setFont(QFont("Arial", 20))
            self.text_item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
            self.text_item.setPos(scene_pos)
            tm.view.scene.addItem(self.text_item)

            # rámček
            self.rect_item = QGraphicsRectItem()
            self.rect_item.setPen(QPen(QColor(0, 0, 255), 1, Qt.PenStyle.DashLine))
            self.rect_item.setZValue(self.text_item.zValue() + 1)
            tm.view.scene.addItem(self.rect_item)

            self._update_rect()
            self.editing = True

    def mouseMove(self, tm, event):
        if self.editing:
            scene_pos = tm.view.mapToScene(event.position().toPoint())
            # možnosť posunu textu priamo myšou
            center = self.text_item.boundingRect().center()
            self.text_item.setPos(scene_pos - center)
            self._update_rect()

    def mouseRelease(self, tm, event):
        pass

    def keyPress(self, tm, event):
        if not self.editing:
            return

        key = event.key()
        if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            # ENTER → nový riadok
            cursor = self.text_item.textCursor()
            cursor.insertBlock()
            self.text_item.setTextCursor(cursor)
        elif key == Qt.Key.Key_Escape:
            # ESC → zrušiť text
            self._cancel_text(tm)
        else:
            # ostatné písmená sa normálne píšu (editor to spracuje)
            pass

    def _update_rect(self):
        if self.text_item and self.rect_item:
            br = self.text_item.boundingRect()
            self.rect_item.setRect(br)
            self.rect_item.setPos(self.text_item.pos())

    def _finalize_text(self, tm):
        if self.text_item:
            # pridáme do undo
            tm.add_to_undo(self.text_item)
            # odstránime rámček
            if self.rect_item:
                tm.view.scene.removeItem(self.rect_item)
            self.text_item = None
            self.rect_item = None
            self.editing = False
            self.rotation_angle = 0
            tm.set_tool(None)

    def _cancel_text(self, tm):
        if self.text_item:
            tm.view.scene.removeItem(self.text_item)
            if self.rect_item:
                tm.view.scene.removeItem(self.rect_item)
            self.text_item = None
            self.rect_item = None
            self.editing = False
            self.rotation_angle = 0
            tm.set_tool(None)