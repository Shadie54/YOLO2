# test.py
import sys
from PyQt6.QtWidgets import QApplication, QToolTip
from PyQt6.QtGui import QColor
from gui_main import MainWindow
from items import YoloBox

def fake_yolo_detections():
    """
    Simuluje YOLO detekcie: (x, y, w, h, label)
    - text "foto" + čísla
    - šípky
    """
    return [
        (50, 50, 100, 40, "foto 1"),       # text foto 1
        (200, 60, 80, 20, "arrow_right"),  # šípka
        (50, 120, 120, 50, "foto 4/21"),   # text foto s číslami
        (250, 150, 60, 30, "arrow_up")     # šípka
    ]

def add_predicted_boxes(view, detections):
    """Pridá predikované boxy (modré, polopriesvitné)"""
    for det in detections:
        x, y, w, h, label = det
        box = YoloBox(rect=view.scene.addRect(x, y, w, h).rect(), label=label)
        box.setFlag(box.GraphicsItemFlag.ItemIsSelectable, True)
        box.setFlag(box.GraphicsItemFlag.ItemIsMovable, True)
        box.setOpacity(0.5)
        box.setBrush(QColor(0, 0, 255, 50))  # modrá, polopriesvitná
        box.setToolTip(label)
        view.scene.addItem(box)
        view.undo_stack.append(box)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1300, 900)
    window.show()

    # pridanie testovacích YOLO boxov
    add_predicted_boxes(window.view, fake_yolo_detections())

    sys.exit(app.exec())