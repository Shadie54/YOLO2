# tools_eraser.py
from items.items import YoloBox
from PyQt6.QtWidgets import QGraphicsPathItem

class EraserTool:
    def mousePress(self, tm, event):
        view = tm.view
        scene_pos = view.mapToScene(event.position().toPoint())
        items = view.scene.items(scene_pos)
        for item in items:
            if isinstance(item, (YoloBox, QGraphicsPathItem)):
                if item in view.undo_stack:
                    view.undo_stack.remove(item)
                view.scene.removeItem(item)
                tm.log("Item erased")

    def mouseMove(self, tm, event):
        # môže ísť aj drag eraser, pre simplicity zatiaľ len click
        self.mousePress(tm, event)

    def mouseRelease(self, tm, event):
        pass