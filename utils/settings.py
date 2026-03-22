# utils/settings.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton,
    QLineEdit, QPushButton, QFileDialog, QCheckBox, QButtonGroup
)
from PyQt6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None, tool_manager=None):
        super().__init__(parent)

        self.tool_manager = tool_manager
        self.settings = settings or {}

        self.setWindowTitle("Nastavenia")
        self.resize(500, 300)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        # ---------- Ukladanie ----------
        main_layout.addWidget(QLabel("<b>Ukladanie obrázkov</b>"))

        self.save_group = QButtonGroup(self)
        self.save_origin_rb = QRadioButton("Prepísať originálny obrázok")
        self.save_origin_rb.setToolTip("Prepíše originálny obrázok s aktuálnymi úpravami")
        self.save_subfolder_rb = QRadioButton("Uložiť do podzložky (default)")
        self.save_subfolder_rb.setToolTip("Uloží obrázok do podsložky s rovnakým názvom, "
                                          "napr: <br> Ak máme : <b>folder/image1.jpg</b> <br>"
                                          "uloží sa do: <b>folder/folder/image1.jpg</b>")
        self.save_custom_rb = QRadioButton("Vybrať vlastnú zložku")
        self.save_custom_rb.setToolTip("Uloží obrázok do zložky podľa valstného výberu")
        self.save_group.addButton(self.save_origin_rb)
        self.save_group.addButton(self.save_subfolder_rb)
        self.save_group.addButton(self.save_custom_rb)

        main_layout.addWidget(self.save_origin_rb)
        main_layout.addWidget(self.save_subfolder_rb)

        custom_layout = QHBoxLayout()
        custom_layout.addWidget(self.save_custom_rb)
        self.custom_folder_edit = QLineEdit()
        self.custom_folder_edit.setPlaceholderText("Vyberte zložku...")
        self.custom_folder_edit.setReadOnly(True)
        self.browse_btn = QPushButton("Prehľadávať")
        self.browse_btn.clicked.connect(self.select_custom_folder)
        custom_layout.addWidget(self.custom_folder_edit)
        custom_layout.addWidget(self.browse_btn)
        main_layout.addLayout(custom_layout)

        # prednastavenie
        save_mode = self.settings.get("save_mode", "subfolder")
        if save_mode == "origin":
            self.save_origin_rb.setChecked(True)
        elif save_mode == "custom":
            self.save_custom_rb.setChecked(True)
            self.custom_folder_edit.setText(self.settings.get("custom_folder", ""))
        else:
            self.save_subfolder_rb.setChecked(True)

        # ---------- Kreslenie ----------
        main_layout.addWidget(QLabel("<b>Kreslenie</b>"))

        self.aa_checkbox = QCheckBox("Použiť vyhladzovanie (antialiasing) pri kreslení")
        self.aa_checkbox.setChecked(self.settings.get("antialiasing", True))
        self.aa_checkbox.toggled.connect(
            lambda checked: self.tool_manager.set_antialiasing(checked)
            if self.tool_manager else None
        )
        main_layout.addWidget(self.aa_checkbox)

        # ---------- Buttons ----------
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Zrušiť")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    # ---------- METHODS ----------
    def select_custom_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Vybrať zložku", "")
        if folder:
            self.custom_folder_edit.setText(folder)
            self.save_custom_rb.setChecked(True)

    def get_settings(self):
        # vracia slovník nastavení
        if self.save_origin_rb.isChecked():
            save_mode = "origin"
            folder = ""
        elif self.save_subfolder_rb.isChecked():
            save_mode = "subfolder"
            folder = ""
        else:
            save_mode = "custom"
            folder = self.custom_folder_edit.text()
        return {
            "save_mode": save_mode,
            "custom_folder": folder,
            "antialiasing": self.aa_checkbox.isChecked()
        }