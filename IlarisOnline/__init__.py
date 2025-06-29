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
from IlarisOnline.ProgressDialog import ProgressDialog

PLUGIN_DATA_KEYS = [
    "Id",
    # "Gruppe",
    "Bearbeitet",
    "Erstellt",
    # "Hausregel",
    # "Besitzer",
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
        self.ioTab.ui.labelErstellt.setText("-")
        if ioData.get("Id"):
            self.ioTab.ui.labelId.setText(ioData["Id"])
        self.ioTab.ui.labelGruppe.setText("-")
        base_url = 'https://ilaris-online.de/app/'
        self.ioTab.ui.labelGruppe.setText("-")
        self.ioTab.ui.labelGruppe.setToolTip("Keine Gruppe zugeordnet")
        if ioData.get("Gruppe"):
            url = base_url + 'gruppe/' + ioData["Gruppe"].get("@id", "-") + '/'
            self.ioTab.ui.labelGruppe.setText(f"<a href='{url}'>{ioData['Gruppe'].get('@name', '-')}</a>")
            self.ioTab.ui.labelGruppe.setToolTip(ioData["Gruppe"].get("@id", "-"))
            self.ioTab.ui.labelGruppe.setOpenExternalLinks(True)
        self.ioTab.ui.labelBesitzer.setText("-")
        if ioData.get("Besitzer"):
            self.ioTab.ui.labelBesitzer.setText(ioData["Besitzer"].get("@name", "-"))
            self.ioTab.ui.labelBesitzer.setToolTip(ioData["Besitzer"].get("@id", "-"))
            self.ioTab.ui.labelBesitzer.setOpenExternalLinks(True)
        self.ioTab.ui.labelHausregel.setText("-")
        if ioData.get("Hausregel"):
            self.ioTab.ui.labelHausregel.setText(ioData["Hausregel"].get("@name", "-"))
            self.ioTab.ui.labelHausregel.setToolTip(ioData["Hausregel"].get("@id", "-"))
        if ioData.get("Bearbeitet"):
            self.ioTab.ui.labelBearbeitet.setText(ioData["Bearbeitet"])
        url = f'https://ilaris-online.de/app/charakter/{ioData["Id"]}'
        self.ioTab.ui.labelUrl.setText(f'<a href="{url}">{url}</a>')
        self.ioTab.ui.labelUrl.setOpenExternalLinks(True)

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
            if deserializer.find("Gruppe"):
                char.ilarisOnline["Gruppe"] = deserializer.get("id", "")
                char.ilarisOnline["Gruppe"] = deserializer.get("name", "")
                deserializer.end()  # Gruppe
            # char.ilarisOnline["Gruppe"]
            deserializer.end()  # IlarisOnline
        else:
            char.ilarisOnline = {k: "" for k in PLUGIN_DATA_KEYS}
        self.updateTab(char.ilarisOnline)

    def charakterSerialisiertHandler(self, params):
        print(params)
        serializer = params["serializer"]
        char = params["charakter"]
        print(char.neueHausregeln)
        if char.neueHausregeln:
            print("TODO: update hausregeln")
        # char.ilarisOnline["bearbeitet"] = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        if not hasattr(char, "ilarisOnline"):  # i.e. for new created characters
            char.ilarisOnline = {k: "" for k in PLUGIN_DATA_KEYS}
        serializer.begin("IlarisOnline")
        for key, val in char.ilarisOnline.items():
            serializer.setNested(key, val)
        # write abgeleitete werte (avoid calculation serverside)
        serializer.beginList('Abgeleitete')
        for (abk, abwert) in char.abgeleiteteWerte.items():
            serializer.begin('Abgeleitet')
            # abwert.serialize(serializer)
            serializer.set("abk", abk)
            serializer.set("name", abwert.anzeigename)
            serializer.set("wert", abwert.wert)
            # serializer.set("mod", abwert.mod)
            serializer.set("wertStern", abwert.finalwert)
            # serializer.set("mod", abwert.modifikator)
            serializer.end() #abgeleitet
        serializer.end() #abgeleitet
        serializer.end() # IlarisOnline
    
    def uploadCallback(self, data, error=None, status=None):
        print(data)
        if error:
            print("Error uploading character to Ilaris-Online")
            print(error)
            self.uploadDialog.addMessage("Hochladen des Charakters auf Ilaris-Online.de fehlgeschlagen.", style="color: red;")
            self.uploadDialog.addMessage(f"Fehler: {error}", style="color: red;")
            self.uploadError = error
            self.uploadStatus = status
            self.uploadData = data
            if status == 401:
                # raise PermissionError("Unauthorized, please login again")
                loginDialog = LoginDialogWrapper.LoginDialogWrapper(
                    callback=self.startUpload
                )
        else:
            print("Character uploaded successfully")
            self.uploadDialog.addMessage("Charakter erfolgreich hochgeladen.", style="color: green;")
            if "io_data" in data:
                print("IO data found, updating character")
                # self.charakterGeschriebenParams["charakter"].ilarisOnline = self.charakterGeschriebenParams["io_data"]
                print("wird erneut gespeihert")
                self.uploadDialog.addMessage("Charakterdaten aktualisieren und erneut speichern...", 0.9)
                # TODO: compare IO data only update on diff also mention in popup
                ser = self.charakterGeschriebenParams["serializer"]
                if ser.find("IlarisOnline"):
                    if ser.find("id"):
                        print("IlarisOnline id found in serializer, updating")
                        ser.set("text", data["io_data"]["Id"])
                        ser.end()  # id
                    ser.end()  # IlarisOnline
                char = self.charakterGeschriebenParams["charakter"]
                # todo compare char.ilarisOnline with data["io_data"] and update only if different
                char.ilarisOnline = data["io_data"]
                # char.ilarisOnline["id"] = data["io_data"]["id"]
                # char.ilarisOnline["gruppe"] = data["io_data"]["gruppe"]
                # char.ilarisOnline["besitzer"] = data["io_data"]["besitzer"]
                print(f"writing file to {self.charakterGeschriebenParams['filepath']}")
                ser.writeFile(self.charakterGeschriebenParams["filepath"])
                self.updateTab(data["io_data"])
        self.uploadDialog.enable()
            

    def startUpload(self):
        """Start the upload process for the character."""
        params = self.geschriebenParams
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
        self.retryUploads = 3  # allow 3 retries on error (i.e. unauthorized)
        self.uploadDialog = ProgressDialog()
        self.uploadDialog.show()
        # self.uploadDialog.raise_()
        # self.uploadDialog.activateWindow()
        self.uploadDialog.addMessage("Charakter lokal gespeichert...", 0.2)
        self.uploadDialog.addMessage("Charakter mit Ilaris-Online.de synchronisieren...", 0.5)
        self.geschriebenParams = params
        self.startUpload()
        # except PermissionError as e:
        #     print(f"Error starting upload: {e}")
        #     print("PERMISSION ERROR: RUN LOGIN NOW")
        #     self.uploadDialog.addMessage("Fehler beim Hochladen des Charakters.", style="color: red;")
        #     self.uploadDialog.enable()
        #     return

        # client.uploadHausregel(char.ilarisOnline["hausregel"], char.ilarisOnline["alias"])
