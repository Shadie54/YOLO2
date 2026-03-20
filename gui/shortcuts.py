from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt

def register_shortcuts(main_window):
    view = main_window.view
    tm = view.tool_manager

    main_window._shortcuts = []

    def add(key, func):
        sc = QShortcut(QKeySequence(key), main_window)
        sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        sc.activated.connect(func)
        main_window._shortcuts.append(sc)

    # tools
    add("C", lambda: tm.set_tool("PENCIL"))
    add("X", lambda: tm.set_tool("ERASER"))
    add("L", lambda: tm.set_tool("LINE"))
    add("P", lambda: tm.set_tool("POLYLINE"))
    add("V", lambda: tm.set_tool("POLYCURVE"))
    add("Escape", lambda: tm.set_tool(None))

    # actions
    add("Ctrl+Z", view.undo)
    add("Space", view.fit_image)