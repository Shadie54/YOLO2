# utils/layer_tooltip.py
from PyQt6.QtWidgets import QToolTip
from PyQt6.QtCore import QPoint

def show_layer_tooltip(item, mouse_event, viewport):
    """
    Zobrazí tooltip s info o vrstve nad kurzorom.
    Duck typing: nepotrebujeme importovať TextItem ani SelectionItem.
    """
    class_name = type(item).__name__

    if class_name == "TextItem":
        info = f"Vrstva textboxu: {item.zValue()})"
    elif hasattr(item, "rotating"):
        info = f"Vrstva výberu: {item.zValue()})"
    else:
        info = f"Kresliaca vrstva: {item.zValue()})"

    # zobraz tooltip
    QToolTip.showText(
        QPoint(int(mouse_event.globalPosition().x()), int(mouse_event.globalPosition().y())),
        info,
        viewport
    )