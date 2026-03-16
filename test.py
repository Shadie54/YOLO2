import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QPainter, QKeySequence, QShortcut
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene

from tools import ToolManager
from items import BezierPoint

class TestView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.tool_manager = ToolManager(self)
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)
        self.setDragMode(self.DragMode.ScrollHandDrag)

    def mousePressEvent(self, event):
        self.tool_manager.mousePressEvent(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.tool_manager.mouseMoveEvent(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.tool_manager.mouseReleaseEvent(event)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        self.tool_manager.keyPressEvent(event)
        super().keyPressEvent(event)

    def undo(self):
        if not self.undo_stack:
            return
        item = self.undo_stack.pop()
        if item.scene():
            self.scene.removeItem(item)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bezier Preview Test")
        self.view = TestView()
        self.setCentralWidget(self.view)

        # nastav nástroj na POLYCURVE pre test
        self.view.tool_manager.set_tool("POLYCURVE")

        # shortcut ENTER na commit
        sc = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        sc.activated.connect(lambda: self.view.tool_manager.keyPressEvent(
            type('E', (), {'key': lambda: Qt.Key.Key_Return})()
        ))

        # shortcut ESC na zrušenie
        sc2 = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        sc2.activated.connect(lambda: self.view.tool_manager.keyPressEvent(
            type('E', (), {'key': lambda: Qt.Key.Key_Escape})()
        ))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800,600)
    window.show()
    sys.exit(app.exec())