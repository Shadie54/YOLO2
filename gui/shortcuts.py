# shortcuts.py
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt

def register_shortcuts(main_window):
    view = main_window.view
    tm = view.tool_manager

    main_window._shortcuts = []

    def add(key, func, ignore_if_text_tool=False):
        """ignore_if_text_tool=True → shortcut sa ignoruje len pri TEXT tool (okrem Enter/Escape)"""
        sc = QShortcut(QKeySequence(key), main_window)
        sc.setContext(Qt.ShortcutContext.ApplicationShortcut)

        def wrapped_func():
            if tm.current_tool == "TEXT" and ignore_if_text_tool:
                # Text tool spracuje všetky klávesy sám
                return
            func()

        sc.activated.connect(wrapped_func)
        main_window._shortcuts.append(sc)

    # ---------- Tools shortcuts ----------
    # ignorujeme prepínanie nástrojov počas TEXT toolu
    add("C", lambda: tm.set_tool("PENCIL"), ignore_if_text_tool=True)
    add("X", lambda: tm.set_tool("ERASER"), ignore_if_text_tool=True)
    add("L", lambda: tm.set_tool("LINE"), ignore_if_text_tool=True)
    add("P", lambda: tm.set_tool("POLYLINE"), ignore_if_text_tool=True)
    add("V", lambda: tm.set_tool("POLYCURVE"), ignore_if_text_tool=True)
    add("Escape", lambda: tm.cancel_text_tool(), ignore_if_text_tool=False)   # zruši písanie textu
    add("Enter", lambda: tm.complete_text_tool(), ignore_if_text_tool=False)   # potvrď text

    # ---------- Actions ----------
    add("Ctrl+Z", view.undo)
    add("Space", view.fit_image)