from EventBus import EventBus
import os
import datetime as dt
from PySide6 import QtWidgets
from QtUtils.SimpleSettingsDialog import SimpleSettingsDialog
from EinstellungenWrapper import EinstellungenWrapper
from Wolke import Wolke
from string import Template
from Historie.HistorieTabWrapper import HistorieTabWrapper
from CharakterEditor import Tab
from copy import deepcopy
from Wolke import Wolke
from Historie.Eintrag import Eintrag
from Charakter import Char
from PySide6.QtWidgets import QFileDialog
from pathlib import Path
import Version

class Plugin:

    def __init__(self):
        EventBus.addAction("charaktereditor_oeffnet", self.charakterEditorOeffnet)
        EventBus.addAction("charaktereditor_geschlossen", self.charakterEditorGeschlossen)
        EventBus.addAction("charakter_instanziiert", self.charakterInstanziiertHandler)
        EventBus.addAction("charakter_deserialisiert", self.charakterDeserialisiertHandler)
        EventBus.addAction("charakter_serialisiert", self.charakterSerialisiertHandler, 100)
        # EventBus.addAction("charakter_geschrieben", self.charakterGeschriebenHandler, 110)
        # Einstellungen mit defaults registrieren
        EinstellungenWrapper.addSettings({
            "Historie_Plugin_Daten" : True,
            "Historie_Datei_Kopie" : True,
            "Historie_Dateiname_Template" : "${name}_${datum}",
            "Historie_Datumsformat" : "%Y-%m-%d",
            "Historie_Ordner": "",
        })
        self.alterCharakter = None
        self.neuerCharakter = None
        self.historieTab = None

    def changesCharacter(self):
        return Wolke.Settings.get("Historie_Plugin_Daten", True)
    
    def showSettings(self):
        dlg = SimpleSettingsDialog("Historie Plugin Einstellungen")
        dlg.addSetting("Historie_Plugin_Daten", "Änderungen als Verlauf im Charakter speichern", QtWidgets.QCheckBox())
        dlg.addSetting("Historie_Datei_Kopie", "Kopien der Charaktere anlegen", QtWidgets.QCheckBox())
        dirField = QtWidgets.QLineEdit()
        dirField.setToolTip("Pfad zum Speichern der Charakterkopien. Relative Pfade werden relativ zum Charakterordner verstanden.")
        dirButton = QtWidgets.QPushButton('\uf07c')
        dirButton.setProperty("class", "icon")
        dirButton.clicked.connect(lambda: self.selectDirectory(dirField))
        # dlg.addSetting("Historie_Ordner", "Kopien in Unterordner speichern", dirField)
        dirRow = QtWidgets.QHBoxLayout()
        dirRow.addWidget(dirField)
        dirRow.addWidget(dirButton)
        dlg.addSetting("Historie_Ordner", "Backupordner", dirField, layout=dirRow)
        # dlg.addSetting("Historie_Ordner_Button", "", dirButton)
        fnameField = QtWidgets.QLineEdit()
        fnameField.setToolTip("Es stehen die Platzhalter ${name}, ${datum},\n${epgesamt}, ${ep} (ausgegeben), ${version} (sephrasto) zur Verfügung.")
        fnameField.setPlaceholderText("${name}_${datum}")
        dlg.addSetting("Historie_Dateiname_Template", "Template für Dateinamen\nDefault: ${name}_${datum}", fnameField)
        dateformatField = QtWidgets.QLineEdit()
        dateformatField.setToolTip("Liste der Optionen zum darstellen des Datums/Uhrzeit:\nhttps://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes")
        dateformatField.setPlaceholderText("%Y-%m-%d")
        # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
        dlg.addSetting("Historie_Datumsformat", "Datumsformat.", dateformatField)
        dlg.show()

    def selectDirectory(self, dirField):
        directory = QFileDialog.getExistingDirectory(
            None, 
            "Backupordner auswählen", 
            Wolke.Settings["Pfad-Chars"], 
            QFileDialog.ShowDirsOnly)
        if directory:  # Don't update if user cancelled the dialog
            try:
                directory = Path(directory).relative_to(Wolke.Settings["Pfad-Chars"])
            except ValueError:
                pass
            dirField.setText(str(directory))

    def charakterInstanziiertHandler(self, params):
        # if not self.db.einstellungen["Historie Plugin: Aktivieren"].wert:
        #     return
        char = params["charakter"]
        char.historie = [] 

    def charakterEditorOeffnet(self, params):
        self.historieTab = HistorieTabWrapper()
        self.historieTab.ui.historieTable.itemClicked.connect(self.rowClicked)

    def charakterEditorGeschlossen(self, params):
        self.alterCharakter = None
        self.neuerCharakter = None
        self.historieTab = None

    def rowClicked(self, item):
        row = item.row()
        eintrag = self.neuerCharakter.historie[row]
        ui = self.historieTab.ui
        ui.plainText.setText(eintrag.text)
        ui.labelEpGewinn.setText(f"{eintrag.epGewinn}")
        ui.labelEpAusgabe.setText(f"{eintrag.epAusgabe}")
        ui.labelDatum.setText(eintrag.datum.strftime("%d.%m.%Y"))
    
    def clearDetails(self):
        ui = self.historieTab.ui
        ui.plainText.clear()
        ui.labelEpGewinn.clear()
        ui.labelEpAusgabe.clear()
        ui.labelDatum.clear()

    def createCharakterTabs(self):
        if not Wolke.Settings.get("Historie_Plugin_Daten"):
            return []
        tab = Tab(72, self.historieTab, self.historieTab.form, "Historie")
        return [tab]

    def charakterDeserialisiertHandler(self, params):
        deser = params["deserializer"]
        self.alterCharakter = Char()
        self.neuerCharakter = params["charakter"]
        self.updateAltChar(self.neuerCharakter)
        if deser.find('Historie'):
            for _ in deser.listTags():
                eintrag = Eintrag(ep=0)
                eintrag.deserialize(deser)
                self.neuerCharakter.historie.append(eintrag)
            deser.end() # historie
        self.updateAltChar(self.neuerCharakter)
        if self.historieTab is not None:
            self.updateTab(self.neuerCharakter)

    def charakterSerialisiertHandler(self, params):
        serializer = params["serializer"]
        if self.alterCharakter is None:
            self.alterCharakter = Char()
        if Wolke.Settings["Historie_Plugin_Daten"]:
            self.updateHistorie(params)
            serializer = self.serialize(serializer)
        if Wolke.Settings["Historie_Datei_Kopie"]:
            serializer = self.extraDateiSpeichern(serializer, params)

    def extraDateiSpeichern(self, serializer, params):
        dateTemplate = Wolke.Settings.get("Historie_Datumsformat", "%Y-%m-%d")
        fnameTemplate = Template(Wolke.Settings["Historie_Dateiname_Template"])
        char_folder = Wolke.Settings["Pfad-Chars"]
        date = dt.datetime.now().strftime(dateTemplate)
        # (name, ext) = os.path.splitext(params['filepath'])
        char = params["charakter"]
        fname = fnameTemplate.substitute({
            "name": char.name,
            "datum": date,
            "ep": char.epAusgegeben,
            "epgesamt": char.epGesamt,
            "version": Version.clientToString(),
        })
        folder = Wolke.Settings.get("Historie_Ordner", char_folder)
        fpath = os.path.join(folder, fname)
        if not fpath.endswith(".xml"):
            fpath += ".xml"
        # ensure absolute path
        fpath = str(Path(char_folder) / Path(fpath))
        serializer.writeFile(fpath)
        return serializer

    def updateHistorie(self, params):
        neu = params["charakter"]
        self.neuerCharakter = neu
        alt = self.alterCharakter
        # generate new history entry or merge with last one
        if len(neu.historie) > 0 and neu.historie[-1].ep == neu.epGesamt:
            eintrag = neu.historie[-1]
            eintrag.compare(alt, neu, reset=False)   
        else:
            eintrag = Eintrag(ep=neu.epGesamt)
            eintrag.compare(alt, neu)
            if eintrag.totalChanges > 0:
                neu.historie.append(eintrag)
        if self.historieTab is not None:
            self.updateTab(self.neuerCharakter)
            self.clearDetails()
    
    def serialize(self, serializer):
        serializer.beginList('Historie')
        for eintrag in self.neuerCharakter.historie:
            serializer = eintrag.serialize(serializer)
        serializer.end() # List
        self.updateAltChar(self.neuerCharakter)
        return serializer


    def updateTab(self, char):
        table = self.historieTab.ui.historieTable
        while table.rowCount() > 0:
            table.removeRow(0)
        table.setRowCount(len(char.historie))
        for r, eintrag in enumerate(char.historie):
            datum = QtWidgets.QTableWidgetItem(eintrag.datum.strftime("%d.%m.%Y"))
            ep = QtWidgets.QTableWidgetItem(str(eintrag.ep))
            notiz = QtWidgets.QTableWidgetItem(eintrag.notiz)
            table.setItem(r, 0, ep)
            table.setItem(r, 1, datum)
            table.setItem(r, 2, notiz)
        table.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked)
        table.itemChanged.connect(self.saveChanges)

    def saveChanges(self, item):
        row = item.row()
        col = item.column()
        eintrag = self.neuerCharakter.historie[row]
        if col == 0:
            try:
                eintrag.ep = int(item.text())
            except Exception as e:
                item.setText(str(eintrag.ep))  # reset cell
                error_message = "Für EP sind nur ganze Zahlen erlaubt."
                QtWidgets.QMessageBox.critical(None, "Error", error_message)
        elif col == 1:
            try:
                eintrag.datum = dt.datetime.strptime(item.text(), "%d.%m.%Y")
            except Exception as e:
                item.setText(eintrag.datum.strftime("%d.%m.%Y"))  # reset cell
                error_message = "Falsches Datumsformate. Es muss 'dd.mm.yyyy' entsprechen."
                QtWidgets.QMessageBox.critical(None, "Error", error_message)
        elif col == 2:
            eintrag.notiz = item.text()
        self.historieTab.changed()
        
    def updateAltChar(self, neu):
        if self.alterCharakter is None:
            self.alterCharakter = Char()
        self.alterCharakter.epGesamt = neu.epGesamt
        self.alterCharakter.epAusgegeben = neu.epAusgegeben
        self.alterCharakter.eigenheiten = deepcopy(neu.eigenheiten)
        self.alterCharakter.attribute = deepcopy(neu.attribute)
        self.alterCharakter.energien = deepcopy(neu.energien)
        self.alterCharakter.vorteile = deepcopy(neu.vorteile)
        self.alterCharakter.fertigkeiten = deepcopy(neu.fertigkeiten)
        self.alterCharakter.talente = deepcopy(neu.talente)
        self.alterCharakter.übernatürlicheFertigkeiten = deepcopy(neu.übernatürlicheFertigkeiten)
        self.alterCharakter.freieFertigkeiten = deepcopy(neu.freieFertigkeiten)
