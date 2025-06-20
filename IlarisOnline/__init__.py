from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from IlarisOnline import (CharakterBrowserWrapper)
from IlarisOnline.PluginSettingsDialog import PluginSettingsDialog, DEFAULT_SETTINGS
from Hilfsmethoden import Hilfsmethoden
from EinstellungenWrapper import EinstellungenWrapper
from QtUtils.RichTextButton import RichTextToolButton
from IlarisOnline import LoginDialogWrapper
from IlarisOnline.IlarisOnlineApi import APIClient
from Wolke import Wolke
from datetime import datetime as dt
from lxml import etree
from IlarisOnline.ConfirmCheckDialog import ConfirmCheckDialog
from IlarisOnline.TabWrapper import TabWrapper
from CharakterEditor import Tab

PLUGIN_DATA_KEYS = [
    "alias",
    "gruppe",
    "bearbeitet",
    "hausregel"
]

class Plugin:
    def __init__(self):
        self.mainWindowButton = None
        EinstellungenWrapper.addSettings(DEFAULT_SETTINGS)
        # EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)
        EventBus.addAction("charakter_serialisiert", self.charakterSerialisiertHandler)
        EventBus.addAction("charakter_deserialisiert", self.charakterDeserialisiertHandler)
        EventBus.addAction("charakter_geschrieben", self.charakterGeschriebenHandler, 0)
        EventBus.addAction("charaktereditor_oeffnet", self.charakterEditorOeffnet)

    def changesCharacter(self):
        return True

    def charakterEditorOeffnet(self, params):
        self.ioTab = TabWrapper()
        # self.historieTab.ui.historieTable.itemClicked.connect(self.rowClicked)
    
    def createCharakterTabs(self):
        tab = Tab(72, self.ioTab, self.ioTab.form, "Ilaris-Online")
        return [tab]

    def updateTab(self, ioData=None):
        if ioData is None:
            # ioData = Wolke.Charakter.ilarisOnline  # how to get char from here?
            pass
        self.ioTab.ui.labelAlias.setText(ioData["alias"])

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

    def charakterDeserialisiertHandler(self, params):
        char = params["charakter"]
        deserializer = params["deserializer"]
        if deserializer.find("IlarisOnline"):
            char.ilarisOnline = {k: deserializer.getNested(k, "") for k in PLUGIN_DATA_KEYS}
            deserializer.end()  # IlarisOnline
        else:
            char.ilarisOnline = {k: "" for k in PLUGIN_DATA_KEYS}

    def charakterSerialisiertHandler(self, params):
        print(params)
        serializer = params["serializer"]
        char = params["charakter"]
        print(char.neueHausregeln)
        if char.neueHausregeln:
            print("TODO: update hausregeln")
        char.ilarisOnline["bearbeitet"] = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        serializer.begin("IlarisOnline")
        for key, val in char.ilarisOnline.items():
            serializer.setNested(key, val)
        serializer.end() # IlarisOnline
    
    def uploadCallback(self, data, error=None, status=None):
        print(data)
        if error:
            print("Error uploading character to Ilaris-Online")
            print(error)
            QtWidgets.QMessageBox.critical(
                QtWidgets.QApplication.activeWindow(),
                "Ilaris-Online",
                "Fehler beim Hochladen des Charakters auf Ilaris-Online.de.",
            )
        else:
            print("Character uploaded successfully")
            QtWidgets.QMessageBox.information(
                QtWidgets.QApplication.activeWindow(),
                "Ilaris-Online",
                "Dein Charakter wurde erfolgreich auf Ilaris-Online.de hochgeladen.",
            )
            if "io_data" in data:
                print("IO data found, updating character")
                # self.charakterGeschriebenParams["charakter"].ilarisOnline = self.charakterGeschriebenParams["io_data"]
                print("wird erneut gespeihert")
                # TODO: compare IO data only update on diff also mention in popup
                ser = self.charakterGeschriebenParams["serializer"]
                if ser.find("IlarisOnline"):
                    if ser.find("alias"):
                        print("IlarisOnline alias found in serializer, updating")
                        ser.set("text", data["io_data"]["alias"])
                    ser.end()  # alias
                ser.end()  # IlarisOnline
                self.charakterGeschriebenParams["charakter"].ilarisOnline["alias"] = data["io_data"]["alias"]
                print(f"writing file to {self.charakterGeschriebenParams['filepath']}")
                ser.writeFile(self.charakterGeschriebenParams["filepath"])
                self.updateTab(data["io_data"])
            

    def charakterGeschriebenHandler(self, params):
        """Upload after save to include serialized data from other plugins."""
        print("charakter geschrieben handler")
        char = params["charakter"]
        if not Wolke.Settings["IO_AutoUploadChar"]:
            confirm = ConfirmCheckDialog(
                "Möchtest du die Änderungen an deinem Charakter auch auf Ilaris-Online.de speichern?",
                "Nicht mehr Fragen und Änderungen automatisch hochladen (kann in den Plugin-Einstellungen zurückgesetzt werden).",
            )
            if confirm.exec_() != QtWidgets.QDialog.Accepted:
                print("User cancelled upload")
                return
            if confirm.isChecked():
                print("Auto-upload enabled")
                Wolke.Settings["IO_AutoUploadChar"] = True
            print("User confirmed upload")
        client = APIClient()
        xml_string = etree.tostring(etree.ElementTree(params['serializer'].root).getroot(), encoding='unicode')
        self.charakterGeschriebenParams = params  # keep reference to access in callbacks
        client.post(
            "ilaris/charakter/pluginxml/",
            {
                "xml": xml_string,
            },
            callback=self.uploadCallback
        )

        # client.uploadHausregel(char.ilarisOnline["hausregel"], char.ilarisOnline["alias"])
