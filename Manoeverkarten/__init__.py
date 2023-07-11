from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from Wolke import Wolke
import tempfile
import PdfSerializer
import os
import re
import math
from Hilfsmethoden import Hilfsmethoden, WaffeneigenschaftException, VoraussetzungException
from CharakterPrintUtility import CharakterPrintUtility
from Core.DatenbankEinstellung import DatenbankEinstellung
from Core.Vorteil import VorteilLinkKategorie
import lxml.etree as etree
from Manoeverkarten import DatenbankEditKarteWrapper, KartenExportDialogWrapper, KartenGenerator
from Manoeverkarten.Manoeverkarte import KartenTyp, Karte
import DatenbankEditor
from EinstellungenWrapper import EinstellungenWrapper
from QtUtils.ProgressDialogExt import ProgressDialogExt
from HilfeWrapper import HilfeWrapper
from QtUtils.SimpleSettingsDialog import SimpleSettingsDialog

class Plugin:
    def __init__(self):
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHook)
        EventBus.addFilter("datenbank_editor_typen", self.datenbankEditorTypenHook)
        EventBus.addFilter("datenbank_xml_laden", self.datenbankXmlLadenHook)
        EventBus.addFilter("datenbank_xml_schreiben", self.datenbankXmlSchreibenHook)
        EventBus.addFilter("datenbank_verify", self.datenbankVerifyHook)
        EventBus.addAction("dbe_menuitems_erstellen", self.menusErstellen)
        EventBus.addAction("charakter_instanziiert", self.charakterInstanziiertKategorienHandler)
        EventBus.addFilter("charakter_xml_laden", self.charakterXmlLadenKategorienHook)
        EventBus.addFilter("charakter_xml_schreiben", self.charakterXmlSchreibenKategorienHook)

        self.db = None
        EinstellungenWrapper.addSettings({"Manöverkarten_PDF-Open" : True,
                                          "Manöverkarten_Hintergrundbild" : True,
                                          "Manöverkarten_PrologAusgeben" : True,
                                          "Manöverkarten_CharaktereditorButton" : True,
                                          "Manöverkarten_ExportVerzögerungMs" : 20,
                                          "Manöverkarten_DeaktivierteKategorien" : []})

    @staticmethod
    def getDescription():
        return "Dieses Plugin gibt den Regelanhang zusätzlich als separate PDF in Spielkartengröße, auf sogenannten Manöverkarten aus.\n"\
            "Alternativ kann damit im Datenbankeditor auch die gesamte Regelbasis auf Karten ausgegeben werden.\n" \
            "Die Karten können dann z.B. im 3x3 Format auf dickes Papier gedruckt und dann ausgeschnitten werden."

    def createCharakterButtons(self):
        if not Wolke.Settings["Manöverkarten_CharaktereditorButton"]:
           return []
        self.exportChar = QtWidgets.QPushButton()
        self.exportChar.setObjectName("checkManöverkartenEnable")
        self.exportChar.setText("Manöverkarten erstellen")
        self.exportChar.setToolTip("Erstellt eine Datei mit dem Regelanhang in Form von Manöverkarten, falls aktiviert.")
        self.exportChar.clicked.connect(self.writeCharakterKarten)
        return [self.exportChar]

    def showSettings(self):
        dlg = SimpleSettingsDialog("Manöverkarten Plugin Einstellungen")
        dlg.addSetting("Manöverkarten_PrologAusgeben", "Prolog mit Druckanleitung ausgeben", QtWidgets.QCheckBox())
        dlg.addSetting("Manöverkarten_CharaktereditorButton", "Export Button im Charaktereditor anzeigen", QtWidgets.QCheckBox())
        spinDelay = QtWidgets.QSpinBox()
        spinDelay.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
        spinDelay.setToolTip("Erhöhe den Wert, wenn Karten Darstellungsfehler aufweisen.\nSenke den Wert, um die Exportgeschwindigkeit zu erhöhen.")
        spinDelay.setSingleStep(10)
        spinDelay.setMaximum(9999)
        spinDelay.setSuffix("ms")
        dlg.addSetting("Manöverkarten_ExportVerzögerungMs", "Export-Verzögerung", spinDelay)
        dlg.show()

    def menusErstellen(self, params):
        addMenuItemCB = params["addMenuItemCB"]
        self.exportDB = QtGui.QAction("Manöverkarten")
        self.exportDB.triggered.connect(self.writeDatenbankKarten)
        addMenuItemCB("Export", self.exportDB)

        self.help = QtGui.QAction("Manöverkarten Plugin")
        self.help.triggered.connect(self.showHelp)
        addMenuItemCB("Hilfe", self.help)

    def showHelp(self):
        if not hasattr(self, "helpWindow"):
            self.helpWindow = HilfeWrapper("Help.md", False, [os.path.join(Wolke.Settings['Pfad-Plugins'], "Manoeverkarten", "Doc")])
            self.helpWindow.form.show()
        else:
            self.helpWindow.form.show()
            self.helpWindow.form.activateWindow()

    def basisDatenbankGeladenHook(self, params):
        self.db = params["datenbank"]

        self.kartenGenerator = KartenGenerator.KartenGenerator(self.db)

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Automatische Fußzeile ändern"
        e.beschreibung = "Die Fußzeile wird automatisch auf den Typ des Elements gesetzt, zum Beispiel 'Allgemeine Zauber' beim Ignifaxius. Hiermit kann pro Zeile nach folgendem Format bei einer automatischen Fußzeile die selbige geändert werden: 'Fußzeile=Neue Fußzeile'"
        e.text = '''\
Allgemeine Vorteile=Allgemeiner Vorteil
Profane Vorteile=Profaner Vorteil
Kampfvorteile=Kampfvorteil
Kampfstile=Kampfstil
Magische Vorteile=Magischer Vorteil
Magische Traditionen=Magische Tradition
Karmale Vorteile=Karmaler Vorteil
Karmale Traditionen=Karmale Tradition
Dämonische Traditionen=Dämonische Tradition
Allgemeine Zauber=Allgemeiner Zauber
Allgemeine Liturgien=Allgemeine Liturgie
Traditionsliturgien=Traditionsliturgie
Anrufungen=Anrufung
Magische Modifikationen=Spontane Modifikation
Karmale Modifikationen=Spontane Modifikation
Weitere Magieregeln=
Aktionen und Reaktionen=
Dämonische Modifikationen=Spontane Modifikation
Weitere Karmaregeln=
Weitere Kampfregeln=
Weitere Paktiererregeln=
Gesundheit=
Proben=
Profanes='''
        e.typ = "TextDict"
        e.separator = "\n"
        e.strip = False
        self.db.loadElement(e)

    def datenbankEditorTypenHook(self, typen, params):
        typen[Karte] = DatenbankEditor.DatenbankTypWrapper(Karte, DatenbankEditKarteWrapper.DatenbankEditKarteWrapper, True)
        return typen

    def datenbankXmlLadenHook(self, root, params):
        sephrastoDb = params["datenbank"]
        kartenRoot = root
        if params["basisdatenbank"]:
            sephrastoDb.karten = {}     
            sephrastoDb.insertTable(Karte, sephrastoDb.karten)
            dbFilePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data", "datenbank.xml")
            kartenRoot = etree.parse(dbFilePath).getroot()

        kartenNodes = kartenRoot.findall('Karte')
        for karte in kartenNodes:
            K = Karte()
            K.name = karte.get('name')
            K.typ = int(karte.get('typ'))
            K.subtyp = karte.get('subtyp')
            if K.typ != KartenTyp.Benutzerdefiniert:
                K.subtyp = int(K.subtyp)
            if K.typ == KartenTyp.Deck:
                K.farbe = karte.get('farbe')
            K.titel = karte.get('titel')
            K.subtitel = karte.get('subtitel')
            K.fusszeile = karte.get('fusszeile')
            K.löschen = karte.get('löschen') == "1"
            if karte.get('voraussetzungen'):
                K.voraussetzungen = Hilfsmethoden.VorStr2Array(karte.get('voraussetzungen'))
            K.text = karte.text or ''
            sephrastoDb.loadElement(K, params["basisdatenbank"], params["conflictCallback"])

        return root

    def datenbankXmlSchreibenHook(self, root, params):
        for karte in self.db.karten.values():
            if not self.db.isChangedOrNew(karte): continue
            k = etree.SubElement(root, 'Karte')
            k.set('name', karte.name)
            k.set('typ', str(karte.typ))
            k.set('subtyp', str(karte.subtyp))
            if karte.typ == KartenTyp.Deck:
                k.set('farbe', karte.farbe)
            k.set('titel', karte.titel)
            k.set('subtitel', karte.subtitel)
            k.set('fusszeile', karte.fusszeile)
            k.set('löschen', "1" if karte.löschen else "0")
            k.set('voraussetzungen',Hilfsmethoden.VorArray2Str(karte.voraussetzungen))
            k.text = karte.text
        return root

    def datenbankVerifyHook(self, errors, params):
        db = params["datenbank"]
        isCharakterEditor = params["isCharakterEditor"]
        for karte in db.karten.values():
            try:
                Hilfsmethoden.VerifyVorArray(karte.voraussetzungen, db)
            except VoraussetzungException as e:
                if isCharakterEditor:
                    karte.voraussetzungen = []
                errorStr = f"{karte.displayName} {karte.name} hat fehlerhafte Voraussetzungen: {str(e)}"
                errors.append([karte, errorStr])
        return errors

    def charakterInstanziiertKategorienHandler(self, params):
        char = params["charakter"]
        char.deaktivierteKartenKategorien = []

    def charakterXmlLadenKategorienHook(self, root, params):
        einstellungen = root.find('Einstellungen')
        char = params["charakter"]
        if einstellungen is not None:
            if einstellungen.find('DeaktivierteKartenKategorien') is not None and einstellungen.find('DeaktivierteKartenKategorien').text:
                char.deaktivierteKartenKategorien = list(map(str.strip, einstellungen.find('DeaktivierteKartenKategorien').text.split(",")))
        return root

    def charakterXmlSchreibenKategorienHook(self, root, params):
        char = params["charakter"]
        einstellungen = root.find('Einstellungen')
        if einstellungen is None:
            return root
        etree.SubElement(einstellungen, 'DeaktivierteKartenKategorien').text = str(",".join(char.deaktivierteKartenKategorien))
        return root

    def writeDatenbankKarten(self):
        if self.db is None:
            return
        dialog = KartenExportDialogWrapper.KartenExportDialogWrapper(True, self.db)
        if dialog.cancel:
            return

        startDir = ""
        spath = QtWidgets.QFileDialog.getExistingDirectory(None, "Wähle einen Ordner, in dem die Kartendecks gespeichert werden sollen", startDir)
        if spath == "":
            return

        decks = self.kartenGenerator.generateDBKarten(dialog.deaktivierteKategorien)

        max = 0
        for deck in decks.values():
            if len(deck) <= 1:
                continue
            max += len(deck)

        dlg = ProgressDialogExt(minimum = 0, maximum = max)
        dlg.setWindowTitle("Exportiere Manöverkarten")
        dlg.show()
        QtWidgets.QApplication.processEvents() #make sure the dialog immediatelly shows
        for titel, deck in decks.items():
            if len(deck) <= 1:
                continue
            if dialog.bilderExport:
                self.kartenGenerator.writeKartenBilder(os.path.join(spath, titel + ".pdf"), deck, dialog.nameFormat, dlg)
            else:
                self.kartenGenerator.writeKarten(os.path.join(spath, titel + ".pdf"), deck, dialog.einzelExport, dialog.nameFormat, dlg)
            if dlg.shouldCancel():
                break
        dlg.hide()
        dlg.deleteLater()

    def writeCharakterKarten(self):
        if self.db is None:
            return
        dialog = KartenExportDialogWrapper.KartenExportDialogWrapper(False, self.db)
        if dialog.cancel:
            return

        startDir = ""
        if os.path.isdir(Wolke.Settings['Pfad-Chars']):
            startDir = Wolke.Settings['Pfad-Chars']
        spath, _ = QtWidgets.QFileDialog.getSaveFileName(None,"Manöverkarten speichern...", startDir, "PDF-Datei (*.pdf)")
        if spath == "":
            return
        if ".pdf" not in spath:
            spath = spath + ".pdf"

        decks = self.kartenGenerator.generateCharKarten(dialog.deaktivierteKategorien)
        deck = []
        for d in decks.values():
            if len(d) <= 1:
                continue
            deck.extend(d)

        dlg = ProgressDialogExt(minimum = 0, maximum = len(deck))
        dlg.setWindowTitle("Exportiere Manöverkarten")
        dlg.show()
        QtWidgets.QApplication.processEvents() #make sure the dialog immediatelly shows
        self.kartenGenerator.writeKarten(spath, deck, dialog.einzelExport, dialog.nameFormat, dlg)
        dlg.hide()
        dlg.deleteLater()