from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from IlarisOnline import (CharakterBrowserWrapper)
from IlarisOnline.PluginSettingsDialog import PluginSettingsDialog, DEFAULT_SETTINGS
from Hilfsmethoden import Hilfsmethoden
from EinstellungenWrapper import EinstellungenWrapper
from QtUtils.RichTextButton import RichTextToolButton
from IlarisOnline import LoginDialogWrapper
from Wolke import Wolke


class Plugin:
    def __init__(self):
        self.mainWindowButton = None
        EinstellungenWrapper.addSettings(DEFAULT_SETTINGS)
        # EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)

    def createMainWindowButtons(self):
        self.mainWindowButton = QtWidgets.QPushButton()
        self.mainWindowButton.setObjectName("buttonPlugin")
        self.mainWindowButton.setToolTip("ilaris-online.de")
        self.mainWindowButton.setProperty("class", "icon")
        font = self.mainWindowButton.font()
        font.setHintingPreference(QtGui.QFont.PreferNoHinting)
        self.mainWindowButton.setFont(font)
        self.mainWindowButton.setText("\uf0c2")  # \uf0ac is globe
        self.mainWindowButton.clicked.connect(self.clickedMainWindowButton)
        return [self.mainWindowButton]

    def createCharakterButtons(self):
        if not Wolke.Settings["IO_ShowCharUploadButton"]:
            return []
        self.charUploadBtn = RichTextToolButton()
        self.charUploadBtn.setObjectName("buttonPluginCharakter")
        self.charUploadBtn.setToolTip("ilaris-online.de")
        self.charUploadBtn.setProperty("class", "icon")
        self.charUploadBtn.setText(
            f"<span style='{Wolke.FontAwesomeCSS}'>\uf0ee</span>&nbsp;&nbsp;Upload"
        )
        self.charUploadBtn.setShortcut("Ctrl+U")
        self.charUploadBtn.setToolTip("Charakter auf Ilaris-Online.de hochladen.")
        self.charUploadBtn.clicked.connect(self.clickedCharUploadBtn)
        return [self.charUploadBtn]

    def clickedMainWindowButton(self):
        print("clicked ilaris-online window")
        CharakterBrowserWrapper.CharakterBrowserWrapper()

    def clickedCharUploadBtn(self):
        print("clicked char sync")

    def showSettings(self):
        dialog = PluginSettingsDialog()
        dialog.show()
