# shortcuts.py
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt

def register_shortcuts(main_window):
    """Register shortcuts ONLY for actions not on toolbar to avoid ambiguous keys."""
    view = main_window.view
    main_window._shortcuts = []

    def add_shortcut(key_sequence, callback):
        sc = QShortcut(QKeySequence(key_sequence), main_window)
        sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        sc.activated.connect(callback)
        main_window._shortcuts.append(sc)
        return sc

    # ---------- NON-TOOL SHORTCUTS ----------
    add_shortcut("Ctrl+Z", view.undo)
    add_shortcut("Space", view.fit_image)
    add_shortcut("O", main_window.open_image)