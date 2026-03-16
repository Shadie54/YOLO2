#shortcuts.py
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt

def register_shortcuts(main_window):
    view = main_window.view

    # Uloženie shortcutov, aby ich GC nezmazal
    main_window._shortcuts = []

    def add_shortcut(key_sequence, callback):
        sc = QShortcut(QKeySequence(key_sequence), main_window)
        sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        sc.activated.connect(callback)
        main_window._shortcuts.append(sc)
        return sc

    # ---------- OPEN IMAGE ----------
    add_shortcut("O", main_window.open_image)

    # ---------- UNDO ----------
    add_shortcut("Ctrl+Z", view.undo)

    # ---------- FIT IMAGE ----------
    add_shortcut("Space", view.fit_image)

    # ---------- TOOLS ----------
    add_shortcut("B", lambda: view.tool_manager.set_tool("BOX"))
    add_shortcut("L", lambda: view.tool_manager.set_tool("LINE"))
    add_shortcut("P", lambda: view.tool_manager.set_tool("POLYLINE"))
    add_shortcut("V", lambda: view.tool_manager.set_tool("POLYCURVE"))
    add_shortcut("E", lambda: view.tool_manager.set_tool("ERASER"))