from EventBus import EventBus
from PySide6 import QtWidgets, QtGui
from Wolke import Wolke
from CharakterEditor import Tab
from Ressourcen import CharakterRessourcenWrapper
from Ressourcen.Ressource import Ressource
from Core.DatenbankEinstellung import DatenbankEinstellung

class Plugin:
    def __init__(self):
        EventBus.addAction("charaktereditor_geschlossen", self.charakterEditorGeschlossenHook)
        EventBus.addAction("charakter_epgesamt_geändert", self.charakterEpgesamtGeändertHook)
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHook)
        EventBus.addAction("charakter_instanziiert", self.charakterInstanziiertHook)
        EventBus.addAction("charakter_serialisiert", self.charakterSerialisiertHook)
        EventBus.addAction("charakter_deserialisiert", self.charakterDeserialisiertHook)
        EventBus.addFilter("class_beschreibung_wrapper", self.classBeschreibungWrapperFilter)
        EventBus.addFilter("class_info_wrapper", self.classInfoWrapperFilter)
        EventBus.addFilter("pdf_export", self.pdfExportFilter)
        self.ressourcenTab = None

    def changesCharacter(self):
        return True

    def createCharakterTabs(self):
        self.ressourcenTab = CharakterRessourcenWrapper.CharakterRessourcenWrapper()
        tab = Tab(44, self.ressourcenTab, self.ressourcenTab.form, "Ressourcen")
        return [tab]

    def charakterEditorGeschlossenHook(self, params):
        self.ressourcenTab = None

    def charakterEpgesamtGeändertHook(self, params):
        if self.ressourcenTab is not None:
            self.ressourcenTab.updateInfoLabel()

    def basisDatenbankGeladenHook(self, params):
        db = params["datenbank"]

        e = DatenbankEinstellung()
        e.name = "Ressourcen Plugin: Standardressourcen"
        e.beschreibung = ""
        e.text = '''{\
    "Ansehen" : ["unbekannt", "wohlwollend betrachtet", "geschätzt", "respektiert", "bewundert", "verehrt"],
    "Einkommen" : ["elend, 1 D", "karg, 4 D", "annehmbar, 16 D", "reichlich, 64 D", "üppig, 128 D", "prachtvoll, 256 D"],
    "Entschlossenheit" : ["lethargisch, 3 EnP", "zögerlich, 4 EnP", "optimistisch, 5 EnP", "bestimmt, 6 EnP", "standhaft, 7 EnP", "unerschütterlich, 8 EnP"],
    "Gefolge" : ["kein Gefolge", "klein/unerfahren", "klein/erfahren oder mittel/unerfahren", "klein/meisterlich, mittel/erfahren oder groß/unerfahren", "mittel/meisterlich, groß/erfahren oder sehr groß/unerfahren", "groß/meisterlich oder sehr groß/erfahren"],
    "Stand" : ["Benachteiligte", "Unterschicht", "Mittelschicht", "Obere Mittelschicht", "Oberschicht", "Elite"],
    "Verbindungen" : ["kein Einfluss", "etwas Einfluss in bestimmten Bereichen", "etwas Einfluss in vielen Bereichen", "ansehnlicher Einfluss", "immenser Einfluss", "kennt jeden"],
    "Tierbegleiter" : ["kein Begleiter", "gewöhnlich, +2 EP", "überdurchschnittlich, +4 EP", "außergewöhnlich, +6 EP", "herausragend, +8 EP", "einzigartig, +10 EP"]
}'''
        e.typ = "JsonDict"
        e.separator = "\n"
        e.strip = False
        db.loadElement(e)

    def charakterInstanziiertHook(self, params):
        char = params["charakter"]
        char.ressourcen = []
        char.finanzenAnzeigen = False

    def charakterSerialisiertHook(self, params):
        ser = params["serializer"]
        char = params["charakter"]

        ser.beginList('Ressourcen')
        for ressource in char.ressourcen:
            ser.begin('Ressource')
            ressource.serialize(ser)
            ser.end() #ressource
        ser.end() #ressourcen

    def charakterDeserialisiertHook(self, params):
        ser = params["deserializer"]
        char = params["charakter"]

        if ser.find('Ressourcen'):
            for tag in ser.listTags():
                ressource = Ressource.__new__(Ressource)
                if not ressource.deserialize(ser):
                    continue
                char.ressourcen.append(ressource)
            ser.end() #ressourcen

        char.finanzenAnzeigen = False

    def classBeschreibungWrapperFilter(self, beschreibungWrapperClass, params):
        class RessourcenPluginBeschreibungWrapper(beschreibungWrapperClass):
            def __init__(self):
                super().__init__()
                self.ui.labelStatus.hide()
                self.ui.comboStatus.hide()

        return RessourcenPluginBeschreibungWrapper

    def classInfoWrapperFilter(self, infoWrapperClass, params):
        class RessourcenPluginInfoWrapper(infoWrapperClass):
            def __init__(self):
                super().__init__()
                self.ui.labelFinanzen.hide()
                self.ui.checkFinanzen.hide()

        return RessourcenPluginInfoWrapper

    def pdfExportFilter(self, fields, params):
        wertNamen = ["0", "W4", "W6", "W8", "W10", "W12"]

        for i in range(0, len(Wolke.Char.ressourcen)):
            ressource = Wolke.Char.ressourcen[i]
            fields[f"Ressource{i+1}Name"] = ressource.name
            fields[f"Ressource{i+1}Wert"] = wertNamen[ressource.wert]
            fields[f"Ressource{i+1}Kommentar"] = ressource.kommentar
            fields[f"Ressource{i+1}"] = f"{ressource.name}: {wertNamen[ressource.wert]} ({ressource.kommentar})"

        return fields