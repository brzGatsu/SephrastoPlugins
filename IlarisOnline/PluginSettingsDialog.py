from PySide6 import QtWidgets, QtGui
from PySide6.QtWidgets import QCheckBox, QLineEdit, QPushButton, QHBoxLayout
from QtUtils.SimpleSettingsDialog import SimpleSettingsDialog
from IlarisOnline.IlarisOnlineLoginWrapper import IlarisOnlineLoginWrapper
from Wolke import Wolke


DEFAULT_SETTINGS = {
    "IO_Username": "",
    "IO_API_Token": "",
    "IO_Auto_Upload_Char": False,
    "IO_Auto_Upload_DB": False,
    "IO_Show_Char_Upload_Button": True,
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
        self.addSetting("IO_API_Token", "API Token", tokenField, layout=tokenRow)

        self.addSetting("IO_Auto_Upload_Char", "Charaktere automatisch hochladen", QCheckBox())
        self.addSetting("IO_Auto_Upload_DB", "Hausregeln automatisch hochladen", QCheckBox())
        self.addSetting("IO_Show_Char_Upload_Button", "Upload-Button im Charaktereditor", QCheckBox())
    
    def clickedLogin(self):
        """Login-Button-Klick-Handler."""
        def updateTokenField():
            self.tokenField.setText(Wolke.Settings.get("IO_API_Token", ""))
        IlarisOnlineLoginWrapper(callback=updateTokenField)
