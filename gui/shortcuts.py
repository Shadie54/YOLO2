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

    # -------- Tools --------
    add("M", lambda: (tm.set_tool("MOUSE"), main_window.update_tool_highlight()))
    add("C", lambda: (tm.set_tool("PENCIL"), main_window.update_tool_highlight()))
    add("X", lambda: (tm.set_tool("ERASER"), main_window.update_tool_highlight()))
    add("L", lambda: (tm.set_tool("LINE"), main_window.update_tool_highlight()))
    add("P", lambda: (tm.set_tool("POLYLINE"), main_window.update_tool_highlight()))
    add("V", lambda: (tm.set_tool("POLYCURVE"), main_window.update_tool_highlight()))
    add("T", lambda: (tm.set_tool("TEXT"), main_window.update_tool_highlight()))
    add("E", lambda: (tm.set_tool("ERASER"), main_window.update_tool_highlight()))
    add("S", lambda: (tm.set_tool("SELECT"), main_window.update_tool_highlight()))
    add("Escape", lambda: (tm.set_tool(None), main_window.update_tool_highlight()))

    # -------- Actions --------
    add("Ctrl+Z", view.undo)
    add("Space", view.fit_image)
    add("Ctrl+O", main_window.open_folder)