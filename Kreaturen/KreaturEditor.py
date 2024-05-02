from PySide6 import QtWidgets, QtCore, QtGui, QtWebEngineCore
import os.path
import logging
from Wolke import Wolke
import copy
import tempfile
import lxml.etree as etree
import math
from PySide6.QtGui import QPixmap
import base64
import json
import re
import platform
from shutil import which
import re
from QtUtils.TextTagCompleter import TextTagCompleter
from Hilfsmethoden import Hilfsmethoden
import shutil
from QtUtils.ProgressDialogExt import ProgressDialogExt
from Kreaturen.IlarisOnlineApi import APIClient
from Kreaturen import AngriffWidget


ATTRIBUTE = ["KO", "MU", "GE", "KK", "IN", "KL", "CH", "FF"]
KAMPFWERTE = ["WS", "WSE", "KOL", "MR", "INI", "GS", "GSS", "GST", "GSS_label", "GST_label"]
TYPEN = ["humanoid", "tier", "elementar", "mythen", "fee", "geist", "untot", "daimonid", "daemon", "pflanze"]
EIGENSCHAFTEN = ["ASDF", "BSDF"]
KATEGORIEN = ["Profan", "Kampf", "Übernatürlich", "Allgemein", "Info"]
DATA = {
    "abenteuer": [],
    "id": None,
    "quelle": {"name": ""},
    "attribute": {k: None for k in ATTRIBUTE},
    "kampfwerte": {k: None for k in KAMPFWERTE},
    "eigenschaften": [],
    "angriffe": [],
    "freietalente": [],
    "gup": None,
    "asp": None,
    "kap": None,
    "nsc": False,
}

def as_int(value, fallback=0):
    if value is None:
        return fallback
    else:
        return int(value)

class KategoriePicker(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QtWidgets.QComboBox(parent)
        editor.addItems(KATEGORIEN)
        return editor
    
class AngriffWidgetWrapper(QtWidgets.QWidget, AngriffWidget.Ui_Form):
    def __init__(self, parent=None):
        super(AngriffWidgetWrapper, self).__init__(parent)
        self.setupUi(self)

    def setAngriff(self, angriff):
        # self.ui = AngriffWidget.Ui_Form()
        # self.ui.setupUi(self)
        self.leName.setText(angriff.get("name", ""))
        self.leTP.setText(angriff.get("tp", ""))
        self.sbRW.setValue(as_int(angriff.get("rw")))
        self.sbAT.setValue(as_int(angriff.get("at")))
        self.sbVT.setValue(as_int(angriff.get("vt")))
        self.sbLZ.setValue(as_int(angriff.get("lz")))
        self.leEigenschaften.setText(angriff.get("eigenschaften", ""))
        # self.ui.leEigenschaften.setText(", ".join(angriff.get("eigenschaften", [])))

    def getAngriff(self):
        return {
            "name": self.leName.text(),
            "tp": self.leTP.text(),
            "rw": self.sbRW.value(),
            "at": self.sbAT.value(),
            "vt": self.sbVT.value(),
            "lz": self.sbLZ.value(),
            "eigenschaften": self.leEigenschaften.text(),
        }

    def clear(self):
        self.ui.leName.setText("")
        self.ui.leWert.setText("")
        self.ui.leText.setText("")


class KreaturEditor(object):
    def __init__(self):
        self.data = copy.deepcopy(DATA)
        self.savepath = ""
        self.characterImage = None
        self.currentlyLoading = False
        # self.angemeldet = False

    def setupMainForm(self): 
        if "WindowSize-KreaturenPlugin" in Wolke.Settings:
            windowSize = Wolke.Settings["WindowSize-KreaturenPlugin"]
            self.formMain.resize(windowSize[0], windowSize[1])

        # main window
        self.ui.btnExport.clicked.connect(self.exportClickedHandler)
        self.ui.btnLogin.clicked.connect(self.loginClickedHandler)
        self.ui.btnDBLaden.clicked.connect(self.loadOnlineClickedHandler)
        self.ui.btnDBSpeichern.clicked.connect(self.saveOnlineClickedHandler)
        self.ui.buttonLoad.clicked.connect(self.loadClickedHandler)
        self.ui.buttonSave.clicked.connect(self.saveClickedHandler)
        self.ui.buttonQuicksave.clicked.connect(self.quicksaveClickedHandler)
        self.labelImageText = self.ui.labelImage.text()
        self.ui.buttonLoadImage.clicked.connect(self.buttonLoadImageClicked)
        self.ui.buttonDeleteImage.clicked.connect(self.buttonDeleteImageClicked)
        for i in range(self.ui.tabWidget.tabBar().count()):
            self.ui.tabWidget.tabBar().setTabTextColor(i, QtGui.QColor(Wolke.HeadingColor))

        # first tab Allgemein
        self.ui.laID.setText("ID: " + str(self.data.get("id")))
        self.ui.laID.setVisible(bool(self.data.get("id")))
        self.ui.leName.editingFinished.connect(self.allgemeinChanged)
        self.ui.cbTyp.addItems([t.capitalize() for t in TYPEN])
        self.ui.leKurzbeschreibung.editingFinished.connect(self.allgemeinChanged)
        self.ui.cbNSC.clicked.connect(self.allgemeinChanged)
        self.ui.cbPublik.clicked.connect(self.allgemeinChanged)


        # second tab Eigenschaften
        self.ui.btnAddEigenschaft.clicked.connect(self.addEigenschaftClicked)
        # self.ui.btnAddInfo.clicked.connect(self.addInfoClicked)
        
        delegate = KategoriePicker(self.ui.treeEigenschaften)
        self.ui.treeEigenschaften.setItemDelegateForColumn(1, delegate)

        # third tab fertigkeiten
        self.ui.btnAddTalent.clicked.connect(self.addTalentClicked)
        self.ui.btnAddZauberfertigkeit.clicked.connect(self.addZauberfertigkeitClicked)
        self.ui.tabWidget.setStyleSheet('QTabBar { font-weight: bold; font-size: ' + str(Wolke.Settings["FontHeadingSize"]) + 'pt; font-family: \"' + Wolke.Settings["FontHeading"] + '\"; }')

        # fourth tab Angriffe
        self.ui.btnAddAngriff.clicked.connect(self.addAngriffClicked)
        self.stateChanged()
        self.updateTitlebar()
        self.updateLoginStatus()

        self.formMain.closeEvent = self.closeEvent

    def closeEvent(self,event):
        Wolke.Settings["WindowSize-KreaturPlugin"] = [self.formMain.size().width(), self.formMain.size().height()]

    def exportClickedHandler(self):
        pass

    def removeEmptyItems(self, treeWidget):
        for idx in range(treeWidget.topLevelItemCount()):
            item = treeWidget.topLevelItem(idx)
            if item is None or (item.text(0) == "" and item.text(1) == ""):
                treeWidget.takeTopLevelItem(idx)

    def addAngriffClicked(self):
        widget = AngriffWidgetWrapper()
        self.ui.layoutAngriffe.addWidget(widget)

    def addEigenschaftClicked(self):
        """remove emty items and add a new one"""
        self.removeEmptyItems(self.ui.treeEigenschaften)
        item = QtWidgets.QTreeWidgetItem(["", "Allgemein", ""])
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.ui.treeEigenschaften.addTopLevelItem(item)
        self.ui.treeEigenschaften.setCurrentItem(item)

    def addInfoClicked(self):
        """remove emty items and add a new one"""
        self.removeEmptyItems(self.ui.treeInfos)
        item = QtWidgets.QTreeWidgetItem(["", ""])
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.ui.treeInfos.addTopLevelItem(item)
        self.ui.treeInfos.setCurrentItem(item)

    def addTalentClicked(self):
        """remove emty items and add a new one"""
        self.removeEmptyItems(self.ui.treeTalente)
        item = QtWidgets.QTreeWidgetItem(["", 0, ""])
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.ui.treeTalente.addTopLevelItem(item)
        self.ui.treeTalente.setCurrentItem(item)

    def addZauberfertigkeitClicked(self):
        """remove emty items and add a new one"""
        self.removeEmptyItems(self.ui.treeZauberfertigkeiten)
        item = QtWidgets.QTreeWidgetItem(["", 0, ""])
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.ui.treeZauberfertigkeiten.addTopLevelItem(item)
        self.ui.treeZauberfertigkeiten.setCurrentItem(item)

    def loginClickedHandler(self):
        if Wolke.Settings.get("IlarisOnlineToken", False) is not None:
            # abmelden
            popup = QtWidgets.QMessageBox()
            popup.setWindowTitle("Abmelden")
            popup.setText("Möchtest du dich wirklich abmelden?")
            okButton = popup.addButton("Ja, Abmelden", QtWidgets.QMessageBox.AcceptRole)
            noButton = popup.addButton("Nein, Abbrechen", QtWidgets.QMessageBox.RejectRole)
            # popup.setDefaultButton(QtWidgets.QMessageBox.AcceptRole)
            clickedButton = popup.exec()
            # print(popup.exec())
            if popup.clickedButton() == okButton:
                print("abmelden...")
                Wolke.Settings["IlarisOnlineToken"] = None
                Wolke.Settings["IlarisOnlineUser"] = None
                print("wolke cleaned")
            self.updateLoginStatus()
            return
        # sonst anmelde popup
        diag = self.loginDialog(callback=self.updateLoginStatus)
        # diag.loginSuccessful.connect(self.updateLoginStatus)
        # self.loginDialog.show()
        # if diag.exec_():
        # self.angemeldet = True
        # self.ui.btnDBLaden.setEnabled(True)
        # self.ui.btnDBSpeichern.setEnabled(True)

    def updateLoginStatus(self):
        self.ui.btnDBSpeichern.setEnabled(False)
        self.ui.btnLogin.setText("Anmelden")
        self.ui.laStatus.setText("Nicht angemeldet")
        if Wolke.Settings.get("IlarisOnlineToken", False) is not None:
            self.ui.btnDBSpeichern.setEnabled(True)
            self.ui.btnLogin.setText("Abmelden")
            name = Wolke.Settings.get("IlarisOnlineUser")
            if Wolke.Settings.get("IlarisOnlineUser", False):
                self.ui.laStatus.setText(f"Hallo {Wolke.Settings["IlarisOnlineUser"]}!")

    def loadOnlineClickedHandler(self):
        print("load online click handler")
        diag = self.onlineDialog()
        print("dialog closed with data: ")
        print(diag.kreatur['kampfwerte'])
        if diag.kreatur is not None:
            self.data = diag.kreatur
            print(self.data['kampfwerte'])
            self.renderData()

    def on_save(self, data, error=None, status=None):
        print("SAVING CODE: ", status)
        if error:
            print("error")
            print(data)
            message = f"Status: {status}\n"
            detail = data.pop("detail", None)
            if detail is not None:
                message += detail + "\n"
            for k,v in data.items():
                message += f"<b>{k}:</b> {v}\n"
            error_diag = QtWidgets.QMessageBox.critical(None, "Fehler beim Speichern", message)
            return
        print("server feedback:")
        print(data)
        self.data = data
        self.renderData()
    
    def saveOnlineClickedHandler(self):
        self.updateData()
        self.client = APIClient(Wolke.Settings.get("IlarisOnlineToken", None))
        # TODO decide based on popup with options overwrite or create new
        if self.data.get("id") is not None:
            MB = QtWidgets.QMessageBox
            reply = MB.question(self.formMain, "Bestätigen", "In der DB liegt möglicherweise eine Kreatur mit dieser ID vor. Möchtest du sie überschreiben?", MB.Yes | MB.No)
            if reply == MB.Yes:
                print("clicked update...")
                print(self.data["name"])
                self.client.request(f"ilaris/kreatur/{self.data['id']}/", self.on_save, method="PUT", payload=self.data)
                # self.client.update(f"ilaris/kreatur/{self.data['id']}/", self.data, self.on_save)
            else:
                print("clicked create...")
                self.client.post("ilaris/kreatur/", self.data, self.on_save)
        else:
            print("auto creating...")
            self.client.post("ilaris/kreatur/", self.data, self.on_save)

    
    @staticmethod
    def printData(data):
        print(data)

    def loadClickedHandler(self):
        if os.path.isdir(Wolke.Settings['Pfad-Chars']):
            startDir = Wolke.Settings['Pfad-Chars']
        else:
            startDir = ""
        spath, _ = QtWidgets.QFileDialog.getOpenFileName(None,"Kreatur laden...",startDir,"JSON-Datei (*.json)")
        if spath == "":
            return
        if not spath.endswith(".json"):
            spath = spath + ".json"

        self.savepath = spath
        if not self.savepath:
            return
        self.currentlyLoading = True
        with open(self.savepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(data)
        self.data = data
        print(data)
        self.renderData()
        # self.werteLoad()

        if data.get('bild') is not None:
            byteArray = bytes(data["bild"], 'utf-8')
            image = base64.b64decode(byteArray)
            self.characterImage = QtGui.QPixmap()
            self.characterImage.loadFromData(image)
            self.setImage(self.characterImage)
        self.updateTitlebar()
        self.currentlyLoading = False
    
    def updateTitlebar(self):
        file = " - Neue Kreatur"
        if self.savepath:
            file = " - " + os.path.basename(self.savepath)
        self.formMain.setWindowTitle("Sephrasto" + file)

    def saveClickedHandler(self):
        if self.savepath != "":
            startDir = self.savepath
        elif os.path.isdir(Wolke.Settings['Pfad-Chars']):
            startDir = os.path.join(Wolke.Settings['Pfad-Chars'], self.ui.leName.text())
        else:
            startDir = ""
        spath, _ = QtWidgets.QFileDialog.getSaveFileName(None,"Kreatur speichern...",startDir,"JSON-Datei (*.json)")
        if spath == "":
            return
        if ".json" not in spath:
            spath = spath + ".json"
            
        self.savepath = spath
        self.updateTitlebar()
        self.quicksaveClickedHandler()

    def quicksaveClickedHandler(self):
        if self.savepath == "":
            self.saveClickedHandler()
            return
        
        self.updateData()

        if self.characterImage:
            buffer = QtCore.QBuffer()
            buffer.open(QtCore.QIODevice.WriteOnly)
            self.characterImage.save(buffer, "JPG")
            # self.data["bild"] = base64.b64encode(buffer.data().data())
            self.data["bild"] = base64.b64encode(buffer.data().data()).decode("utf-8")

        with open(self.savepath, 'w', encoding='utf-8') as file:
            json.dump(self.data, file, indent=2, ensure_ascii=False)

    def updatePreview(self, label, modifiers, summary = False):
        attributModifiers = {}
        talentModifiers = {}
        vorteilModifiers = []
        self.gatherModifiers(modifiers, attributModifiers, talentModifiers, vorteilModifiers)
        label.setText(self.modifiersToString(attributModifiers, talentModifiers, vorteilModifiers, [], summary))

    def stateChanged(self):
        """recalculate values and update preview and conditional forms"""
        pass

    def updateData(self):
        self.allgemeinChanged()
        self.werteChanged()
        self.eigenschaftenChanged()
        self.talenteChanged()
        self.zauberfertigkeitenChanged()
        self.angriffeChanged()

    def werteChanged(self):
        for attr in ATTRIBUTE:
            self.data["attribute"][attr] = self.ui.__getattribute__(f"sb{attr}").value()
        for attr in KAMPFWERTE:
            if attr in ["GSS_label", "GST_label"]:
                self.data["kampfwerte"][attr] = self.ui.__getattribute__(f"le{attr}").text()
            else:
                self.data["kampfwerte"][attr] = self.ui.__getattribute__(f"sb{attr}").value()
        self.data["gup"] = self.ui.sbGUP.value()
        self.data["asp"] = self.ui.sbASP.value()
        self.data["kap"] = self.ui.sbKAP.value()
        # self.stateChanged()
    
    # def kampfwerteChanged(self):
    #     if self.currentlyLoading:
    #         return
    #     fields = {a: f"sb{a}" for a in KAMPFWERTE if a not in ["GSS_label", "GST_label"]}
    #     for attr, field in fields.items():
    #         self.data["kampfwerte"][attr] = self.ui.__getattribute__(field).value()
    #     self.data["kampfwerte"]["GSS_label"] = self.ui.leGSS_label.text()
    #     self.data["kampfwerte"]["GST_label"] = self.ui.leGST_label.text()

    def allgemeinChanged(self):
        if self.currentlyLoading:
            return
        self.data["name"] = self.ui.leName.text()
        self.data["kurzbeschreibung"] = self.ui.leKurzbeschreibung.text()
        self.data["typ"] = self.ui.cbTyp.currentText().lower()
        self.data["nsc"] = self.ui.cbNSC.isChecked()
        self.data["publik"] = self.ui.cbPublik.isChecked()
        self.data["quelle"] = {"name": self.ui.leQuelle.text()}
        self.data["abenteuer"] = [{"abk": s.strip()} for s in self.ui.leAbenteuer.text().split(",")]
        # self.werteChanged()
    

    def eigenschaftenChanged(self):
        if self.currentlyLoading:
            return
        self.data["eigenschaften"] = []
        for i in range(self.ui.treeEigenschaften.topLevelItemCount()):
            item = self.ui.treeEigenschaften.topLevelItem(i)
            if not item.text(0):
                continue  # TODO: could remove empty entries from tree.. as well or call render after save?
            self.data["eigenschaften"].append(
                {"name": item.text(0), "kategorie": item.text(1), "text": item.text(2)})
        # self.removeEmptyItems(self.ui.treeEigenschaften)

    # def infosChanged(self):
    #     if self.currentlyLoading:
    #         return
    #     self.data["infos"] = []
    #     for i in range(self.ui.treeInfos.topLevelItemCount()):
    #         item = self.ui.treeInfos.topLevelItem(i)
    #         self.data["infos"].append(
    #             {"name": item.text(0), "text": item.text(1)})
        # self.removeEmptyItems(self.ui.treeInfos)


    def talenteChanged(self):
        self.data["freietalente"] = []
        for i in range(self.ui.treeTalente.topLevelItemCount()):
            item = self.ui.treeTalente.topLevelItem(i)
            if not item.text(0):
                continue
            try:
                wert = int(item.text(1))
            except ValueError:
                wert = -99
            self.data["freietalente"].append(
                {"name": item.text(0), "wert": wert, "text": item.text(2)})
        # self.removeEmptyItems(self.ui.treeTalente)

    def zauberfertigkeitenChanged(self):
        if self.currentlyLoading:
            return
        self.data["zauberfertigkeiten"] = []
        for i in range(self.ui.treeZauberfertigkeiten.topLevelItemCount()):
            item = self.ui.treeZauberfertigkeiten.topLevelItem(i)
            if not item.text(0):
                continue
            zaubers = item.text(2).split(", ")
            try:
                wert = int(item.text(1))
            except ValueError:
                wert = -99
            self.data["zauberfertigkeiten"].append(
                {"name": item.text(0), "wert": wert, "zaubers": [{"name": z} for z in zaubers]})
        # self.removeEmptyItems(self.ui.treeZauberfertigkeiten)

    def angriffeChanged(self):
        if self.currentlyLoading:
            return
        self.data["angriffe"] = []
        for i in range(self.ui.layoutAngriffe.count()):
            widget = self.ui.layoutAngriffe.itemAt(i).widget()
            if not widget.getAngriff()["name"]:
                continue
            self.data["angriffe"].append(widget.getAngriff())

    def renderData(self):
        """render self.data to the ui elements"""
        self.ui.laID.setText("ID: " + str(self.data.get("id")))
        self.ui.laID.setVisible(bool(self.data.get("id")))
        print("render data")
        print(self.data['kampfwerte'])
        self.renderAllgemein()
        print(self.data['kampfwerte'])
        self.renderWerte()
        self.renderEigenschaften()
        self.renderTalente()
        self.renderZauberfertigkeiten()
        self.renderAngriffe()

    def renderAllgemein(self):
        self.ui.leName.setText(self.data["name"])
        self.ui.leKurzbeschreibung.setText(self.data["kurzbeschreibung"])
        self.ui.cbTyp.setCurrentText(self.data["typ"].capitalize())
        self.ui.cbPublik.setChecked(self.data.get("publik", False))
        self.ui.cbNSC.setChecked(self.data.get("nsc", False))
        self.ui.leQuelle.setText(self.data.get("quelle", {}).get("name", ""))
        self.ui.leAbenteuer.setText(", ".join([a["abk"] for a in self.data.get("abenteuer", [])]))
        self.ui.sbGUP.setValue(as_int(self.data.get("gup")))
        self.ui.sbASP.setValue(as_int(self.data.get("asp")))
        self.ui.sbKAP.setValue(as_int(self.data.get("kap")))
        self.ui.cbNSC.setChecked(self.data.get("nsc", False))
    
    def renderTalente(self):
        self.ui.treeTalente.clear()
        for t in self.data.get("freietalente", []):
            item = QtWidgets.QTreeWidgetItem([t["name"], str(t["wert"]), t["text"]])
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            self.ui.treeTalente.addTopLevelItem(item)

    def renderZauberfertigkeiten(self):
        self.ui.treeZauberfertigkeiten.clear()
        for z in self.data["zauberfertigkeiten"]:
            item = QtWidgets.QTreeWidgetItem([z["name"], str(z["wert"]), ", ".join([z["name"] for z in z["zaubers"]])])
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            self.ui.treeZauberfertigkeiten.addTopLevelItem(item)
    
    def renderAngriffe(self):
        # empty angriff box
        while self.ui.layoutAngriffe.takeAt(0) is not None:
            pass
        for a in self.data["angriffe"]:
            widget = AngriffWidgetWrapper()
            widget.setAngriff(a)
            self.ui.layoutAngriffe.addWidget(widget)

    def renderWerte(self):
        print(self.data["attribute"])
        print(self.data["kampfwerte"])
        for a in ATTRIBUTE:
            self.ui.__getattribute__(f"sb{a}").setValue(as_int(self.data["attribute"].get(a)))
        for a in KAMPFWERTE:
            if a == "GSS_label":
                self.ui.__getattribute__(f"le{a}").setText(self.data["kampfwerte"].get("GSS_label", "schwimmend"))
            elif a == "GST_label":
                self.ui.__getattribute__(f"le{a}").setText(self.data["kampfwerte"].get("GST_label", "fliegend"))
            else:
                self.ui.__getattribute__(f"sb{a}").setValue(as_int(self.data["kampfwerte"].get(a)))

    def renderEigenschaften(self):
        self.ui.treeEigenschaften.clear()
        for e in self.data["eigenschaften"]:
            item = QtWidgets.QTreeWidgetItem([e["name"], e["kategorie"], e["text"]])
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            self.ui.treeEigenschaften.addTopLevelItem(item)

    # def renderInfos(self):
    #     self.ui.treeInfos.clear()
    #     for i in self.data["infos"]:
    #         item = QtWidgets.QTreeWidgetItem([i["name"], i["text"]])
    #         item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
    #         self.ui.treeInfos.addTopLevelItem(item)

    def setImage(self, pixmap):
        self.ui.labelImage.setPixmap(pixmap.scaled(self.ui.labelImage.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

    def buttonLoadImageClicked(self):
        spath, _ = QtWidgets.QFileDialog.getOpenFileName(None,"Bild laden...", "", "Bild Dateien (*.png *.jpg *.bmp)")
        if spath == "":
            return
        
        self.characterImage = QPixmap(spath).scaled(QtCore.QSize(260, 340), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.setImage(self.characterImage)

    def buttonDeleteImageClicked(self):
        self.characterImage = None
        self.ui.labelImage.setPixmap(QPixmap())
        self.ui.labelImage.setText(self.labelImageText)

    def categoryHeading(self, text):
        return "<h2>" + text + "</h2>"

    def ruleHeading(self, text):
        return "<h3>" + text + "</h3>"
