from PySide6 import QtWidgets, QtGui
from PySide6.QtWidgets import QCheckBox, QLineEdit, QPushButton, QHBoxLayout
from QtUtils.SimpleSettingsDialog import SimpleSettingsDialog
from IlarisOnline.LoginDialogWrapper import LoginDialogWrapper
from Wolke import Wolke


DEFAULT_SETTINGS = {
    "IO_Username": "",
    "IO_APIToken": "",
    "IO_AutoUploadChar": False,
    "IO_AutoUploadDB": False,
    "IO_ShowCharUploadButton": True,
}

class PluginSettingsDialog(SimpleSettingsDialog):
    """Dialog Plugin-Einstellungen."""
    def __init__(self):
        super().__init__("IlarisOnline Plugin Einstellungen")
        self.addSettings()

    def addSettings(self):
        # Einstellungen hinzufügen
        tokenRow = QHBoxLayout()
        tokenField = QLineEdit()
        # tokenField.setEchoMode(QLineEdit.EchoMode.Password)
        tokenField.setPlaceholderText("API-Token eingeben, oder via ilaris-online.de einloggen.")
        tokenField.setToolTip("Der API-Token erlaubt es deiner Sephrasto-Installation, über dein Benutzerkonto auf ilaris-online.de zuzugreifen.\nDer Token ist nur eine begrenzte Zeit gültig.")
        self.tokenField = tokenField
        tokenRow.addWidget(tokenField)
        loginButton = QPushButton("Login")
        loginButton.clicked.connect(self.clickedLogin)
        loginButton.setToolTip("Via Login automatisch einen Token erstellen.")
        tokenRow.addWidget(loginButton)
        self.addSetting("IO_APIToken", "API Token", tokenField, layout=tokenRow)

        self.addSetting("IO_AutoUploadChar", "Charaktere automatisch hochladen", QCheckBox())
        self.addSetting("IO_AutoUploadDB", "Hausregeln automatisch hochladen", QCheckBox())
        self.addSetting("IO_ShowCharUploadButton", "Upload-Button im Charaktereditor", QCheckBox())
    
    def clickedLogin(self):
        """Login-Button-Klick-Handler."""
        def updateTokenField():
            self.tokenField.setText(Wolke.Settings.get("IO_APIToken", ""))
        LoginDialogWrapper(callback=updateTokenField)
