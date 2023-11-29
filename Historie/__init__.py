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

class Plugin:

    def __init__(self):
        EventBus.addAction("charaktereditor_oeffnet", self.charakterEditorOeffnet)
        EventBus.addAction("charakter_instanziiert", self.charakterInstanziiertHandler)
        EventBus.addAction("charakter_geladen", self.charakterGeladen)
        EventBus.addFilter("charakter_schreiben", self.charakterSchreibenHook)
        # Einstellungen mit defaults registrieren
        EinstellungenWrapper.addSettings({
            "Historie_Plugin_Daten" : True,
            "Historie_Datei_Kopie" : True,
            "Historie_Dateiname_Template" : "${name}_${datum}",
            "Historie_Datumsformat" : "%Y-%m-%d",
            "Historie_Ordner": "",
        })
        self.alterCharakter = None


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
        pass 

    def createCharakterTabs(self):
        tab = Tab(72, self.historieTab, self.historieTab.form, "Historie")
        return [tab]

    def charakterGeladen(self, params):
        print("Charakter Zwischenspeichern")
        # raise Exception("TT")
        self.alterCharakter = deepcopy(params["charakter"])
        print(self.alterCharakter)
        # return serializer
    
    def charakterSchreibenHook(self, serializer, params):
        if Wolke.Settings["Historie_Plugin_Daten"]:
            serializer = self.updatePluginData(serializer, params)
        if not Wolke.Settings["Historie_Datei_Kopie"]:
            return serializer
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
        print(fname)
        serializer.writeFile(fname)
        return serializer

    def updatePluginData(self, serializer, params):
        # TODO: add note field on history tab that is used for next note message
        neu = params["charakter"]
        alt = self.alterCharakter
        diff = {}
        diff['datum'] = dt.datetime.now()
        diff['epGesamt'] = neu.epGesamt - alt.epGesamt
        diff['epAusgegeben'] = neu.epAusgegeben - alt.epAusgegeben
        neu.historie.append(diff)
        self.alterCharakter = deepcopy(neu)
        return serializer
