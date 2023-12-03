from EventBus import EventBus
import os
import datetime as dt
import lxml.etree as etree
from PySide6 import QtWidgets, QtCore, QtGui
from QtUtils.SimpleSettingsDialog import SimpleSettingsDialog
from EinstellungenWrapper import EinstellungenWrapper
from Wolke import Wolke
from string import Template
from Historie.HistorieTabWrapper import HistorieTabWrapper
from CharakterEditor import Tab
from copy import deepcopy
from Wolke import Wolke
from Historie.Eintrag import Eintrag

class Plugin:

    def __init__(self):
        print("INIT HISTORIE PLUGIN")
        EventBus.addAction("charaktereditor_oeffnet", self.charakterEditorOeffnet)
        EventBus.addAction("charakter_instanziiert", self.charakterInstanziiertHandler)
        EventBus.addAction("charakter_deserialisiert", self.charakterDeserialisiertHandler)
        EventBus.addAction("charakter_serialisiert", self.charakterSerialisiertHandler, 100)
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

    @staticmethod
    def getDescription():
        return "Dieses Plugin speichert Änderungen des Charakters und kann automatische Kopien mit Zeitstempeln anlegen."

    def changesCharacter(self):
        return True
    
    def showSettings(self):
        dlg = SimpleSettingsDialog("Historie Plugin Einstellungen")
        dlg.addSetting("Historie_Plugin_Daten", "Änderungen als Verlauf im Charakter speichern", QtWidgets.QCheckBox())
        dlg.addSetting("Historie_Datei_Kopie", "Kopien der Charaktere anlegen", QtWidgets.QCheckBox())
        dirField = QtWidgets.QLineEdit()
        dirField.setToolTip("Pfad relativ zum Speicherort. ${name} kann als Platzhalter verwendet werden.")
        dlg.addSetting("Historie_Ordner", "Kopien in Unterordner speiechern", dirField)
        fnameField = QtWidgets.QLineEdit()
        fnameField.setToolTip("${name} für den originalen Dateinamen, ${datum} für Datum/Uhrzeit, ${epgesamt} bzw. ${ep} für die Gesamt- bzw. ausgegebenen EP des Charakters")
        fnameField.setPlaceholderText("${name}_${datum}")
        dlg.addSetting("Historie_Dateiname_Template", "Template für die Dateinamen.\nDefault: ${name}_${datum}", fnameField)
        dateformatField = QtWidgets.QLineEdit()
        dateformatField.setToolTip("Liste der Optionen zum darstellen des Datums/Uhrzeit: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes")
        dateformatField.setPlaceholderText("%Y-%m-%d")
        # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
        dlg.addSetting("Historie_Datumsformat", "Datumsformat.", dateformatField)
        dlg.show()

    def charakterInstanziiertHandler(self, params):
        # if not self.db.einstellungen["Historie Plugin: Aktivieren"].wert:
        #     return
        char = params["charakter"]
        char.historie = []

    def charakterEditorOeffnet(self, params):
        self.historieTab = HistorieTabWrapper()
        self.historieTab.ui.historieTable.itemClicked.connect(self.rowClicked)

    def rowClicked(self, item):
        row = item.row()
        eintrag = self.neuerCharakter.historie[row]
        ui = self.historieTab.ui
        ui.plainText.setText(eintrag.text)
        ui.labelEpGewinn.setText(f"{eintrag.epGewinn}")
        ui.labelEpAusgabe.setText(f"{eintrag.epAusgabe}")
        ui.labelDatum.setText(eintrag.datum.strftime("%d.%m.%Y"))

    def createCharakterTabs(self):
        tab = Tab(72, self.historieTab, self.historieTab.form, "Historie")
        return [tab]

    def charakterDeserialisiertHandler(self, params):
        deser = params["deserializer"]
        char = params["charakter"]
        if deser.find('Historie'):
            for _ in deser.listTags():
                eintrag = Eintrag(ep=0)
                eintrag.deserialize(deser)
                char.historie.append(eintrag)
            deser.end() # historie
        self.alterCharakter = deepcopy(params["charakter"])
        self.updateTab(params["charakter"])
        self.neuerCharakter = params["charakter"]
        print("Charakter geladen")
        # print(self.neuerCharakter.historie[-1])

    def charakterSerialisiertHandler(self, serializer, params):
        if Wolke.Settings["Historie_Plugin_Daten"]:
            serializer = self.updatePluginData(serializer, params)
        if Wolke.Settings["Historie_Datei_Kopie"]:
            serializer = self.extraDateiSpeichern(serializer, params)
        return serializer

    def extraDateiSpeichern(self, serializer, params):
        dateTemplate = Wolke.Settings.get("Historie_Datumsformat", "%Y-%m-%d")
        fnameTemplate = Template(Wolke.Settings["Historie_Dateiname_Template"])
        date = dt.datetime.now().strftime(dateTemplate)
        (name, ext) = os.path.splitext(params['filepath'])
        fname = fnameTemplate.substitute({
            "name": name,
            "datum": date,
            "ep": params["charakter"].epAusgegeben,
            "epgesamt": params["charakter"].epGesamt,
        })
        fname += ext
        folderName = Wolke.Settings["Historie_Ordner"]
        if folderName != "":
            folder = Template(folderName).substitute({"name": name})
            (head, tail) = os.path.split(fname)
            if not os.path.isdir(os.path.join(head, folder)):
                os.mkdir(os.path.join(head, folder))
            fname = os.path.join(head, folder, tail)
        serializer.writeFile(fname)
        return serializer

    def updatePluginData(self, serializer, params):
        # TODO: add note field on history tab that is used for next note message
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
        serializer.beginList('Historie')
        for eintrag in neu.historie:
            serializer = eintrag.serialize(serializer)
        serializer.end() # List
        self.updateAltChar(alt, neu)
        self.updateTab(neu)
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
        self.neuerCharakter = char  # should be redundant


        
    def updateAltChar(self, alt, neu):
        # TODO: self.alt = deepcopy(neu) failed (pickle qt..)
        self.alt = deepcopy(neu)
        # alt.epGesamt = neu.epGesamt
        # alt.epAusgegeben = neu.epAusgegeben
        # alt.eigenheiten = deepcopy(neu.eigenheiten)
        # alt.attribute = deepcopy(neu.attribute)
        # # alt.energien = deepcopy(neu.energien)
        # alt.vorteile = deepcopy(neu.vorteile)
        # alt.fertigkeiten = deepcopy(neu.fertigkeiten)
        # alt.talente = deepcopy(neu.talente)
        # alt.übernatürlicheFertigkeiten = deepcopy(neu.übernatürlicheFertigkeiten)
        # alt.freieFertigkeiten = deepcopy(neu.freieFertigkeiten)
