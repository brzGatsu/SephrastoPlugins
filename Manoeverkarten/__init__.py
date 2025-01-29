from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from Wolke import Wolke
import tempfile
import PdfSerializer
import os
import re
import math
from Hilfsmethoden import Hilfsmethoden, WaffeneigenschaftException
from CharakterPrintUtility import CharakterPrintUtility
from Core.DatenbankEinstellung import DatenbankEinstellung
from Core.Vorteil import VorteilLinkKategorie
from Manoeverkarten import DatenbankEditKarteWrapper, KartenExportDialogWrapper, KartenGenerator
from Manoeverkarten.Manoeverkarte import KartenTyp, Karte
import DatenbankEditor
from EinstellungenWrapper import EinstellungenWrapper
from QtUtils.ProgressDialogExt import ProgressDialogExt
from WebEngineWrapper import WebEngineWrapper
from QtUtils.SimpleSettingsDialog import SimpleSettingsDialog
from VoraussetzungenListe import VoraussetzungenListe, VoraussetzungException
from Serialization import Serialization
from QtUtils.RichTextButton import RichTextToolButton

class Plugin:
    def __init__(self):
        EventBus.addAction("datenbank_laden", self.datenbankLadenHook)
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHook)
        EventBus.addFilter("datenbank_editor_typen", self.datenbankEditorTypenHook)
        EventBus.addFilter("datenbank_verify", self.datenbankVerifyHook)
        EventBus.addAction("dbe_menuitems_erstellen", self.menusErstellen)
        EventBus.addAction("charakter_instanziiert", self.charakterInstanziiertKategorienHandler)
        EventBus.addAction("charakter_deserialisiert", self.charakterDeserialisiertKategorienHandler)
        EventBus.addAction("charakter_serialisiert", self.charakterSerialisiertKategorienHandler)

        self.db = None
        EinstellungenWrapper.addSettings({"Manöverkarten_PDF-Open" : True,
                                          "Manöverkarten_Hintergrundbild" : True,
                                          "Manöverkarten_PrologAusgeben" : True,
                                          "Manöverkarten_CharaktereditorButton" : True,
                                          "Manöverkarten_ExportVerzögerungMs" : 50,
                                          "Manöverkarten_FontTitle" : "Aniron",
                                          "Manöverkarten_Font" : "Minion Pro",
                                          "Manöverkarten_DeaktivierteKategorien" : []})

    def changesDatabase(self):
        return True

    def createCharakterButtons(self):
        if not Wolke.Settings["Manöverkarten_CharaktereditorButton"]:
           return []
        self.exportChar = RichTextToolButton()
        self.exportChar.setObjectName("checkManöverkartenEnable")
        self.exportChar.setText("<span style='" + Wolke.FontAwesomeCSS + f"'>\uf1c1</span>&nbsp;&nbsp;Manöverkarten")
        self.exportChar.setShortcut("Ctrl+M")
        self.exportChar.setToolTip("Für den Charakter relevante Manöverkarten als PDF exportieren (" + self.exportChar.shortcut().toString(QtGui.QKeySequence.NativeText) + ")")
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

        fontFamilies = QtGui.QFontDatabase().families()

        comboFont = QtWidgets.QComboBox()
        comboFont.addItems(fontFamilies)
        if Wolke.Settings["Manöverkarten_FontTitle"]in fontFamilies:
            comboFont.setCurrentText(Wolke.Settings["Manöverkarten_FontTitle"])
        else:
            comboFont.setCurrentText(Wolke.DefaultOSFont)
        dlg.addSetting("Manöverkarten_FontTitle", "Karten Schriftart Titel", comboFont)

        comboFont = QtWidgets.QComboBox()
        comboFont.addItems(fontFamilies)
        if Wolke.Settings["Manöverkarten_Font"]in fontFamilies:
            comboFont.setCurrentText(Wolke.Settings["Manöverkarten_Font"])
        else:
            comboFont.setCurrentText(Wolke.DefaultOSFont)
        dlg.addSetting("Manöverkarten_Font", "Karten Schriftart Text", comboFont)

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
            self.helpWindow = WebEngineWrapper("Hilfe", os.path.join(Wolke.Settings['Pfad-Plugins'], "Manoeverkarten", "Data", "Doc", "index.html"), extraCss = Wolke.MkDocsCSS)

            self.helpWindow.form.show()
        else:
            self.helpWindow.form.show()
            self.helpWindow.form.activateWindow()

    def datenbankLadenHook(self, params):
        self.db = params["datenbank"]
        self.db.karten = {}
        self.db.insertTable(Karte, self.db.karten)

    def basisDatenbankGeladenHook(self, params):
        self.kartenGenerator = KartenGenerator.KartenGenerator(self.db)

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Automatische Fußzeile ändern"
        e.beschreibung = "Die Fußzeile wird automatisch auf den Typ des Elements gesetzt, zum Beispiel 'Allgemeine Zauber' beim Ignifaxius. "\
            "Hiermit kann pro Zeile nach folgendem Format bei einer automatischen Fußzeile die selbige geändert werden: 'Fußzeile=Neue Fußzeile'"\
            "Wichtig: Leerzeichen spielen eine Rolle."
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

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Titel kürzen"
        e.beschreibung = "Der Titel von Manöverkarten muss in eine Zeile passen, ansonsten wird automatisch seine Schriftgröße verkleinert."\
            "Hier kannst du Teile davon durch Abkürzungen ersetzen. "\
            "Wichtig: 1. Leerzeichen spielen eine Rolle. 2. Die Reihenfolge kann eine Rolle Spielen, die Ersetzungen werden von oben nach unten durchgeführt."
        e.text = """\
 und= &
des Heiligen=d. hl.
der Heiligen=d. hl.
Tradition der =
geweihten=geweihte"""
        e.typ = "TextDict"
        e.separator = "\n"
        e.strip = False
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Zusätzliche Fertigkeiticons"
        e.beschreibung = "Bei Talenten werden für die Fertigkeiten Icons statt Text eingetragen. "\
            "Hier kannst du die Pfade zu solchen Icons eintragen oder existierende ändern. "\
            "Pro Zeile kannst du nach folgendem Format eine Fertigkeit eintragen: FertigkeitName=C://Pfad/Zu/Icon/Icon.png. "\
            "Falls du eine .svg Datei einfügst, erhält diese automatisch einen Kreis als Hintergrundbild.\n\n"\
            "Du kannst außerdem das Makro $plugins_dir$ verwenden, um deine Bilder in einem eigenen Ordner innerhalb des Pluginordners abzulegen. "\
            "Beispiel: Feuer=$plugins_dir$/ManoeverkartenBilder/Feuer.png"
        e.text = ""
        e.typ = "TextDict"
        e.separator = "\n"
        e.strip = True
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Talente Schwierigkeit kürzen"
        e.beschreibung = "Bei Talenten wird die Schwierigkeit in den Untertitel eingetragen. Die Texte können dafür jedoch zu lang sein - "\
            "hier kannst du Teile davon zum Beispiel durch Abkürzungen oder Icons (bspw. von game-icons.net) ersetzen. "\
            "FontAwesome icons kannst du innerhalb eines span-Tags nutzen (hier nicht richtig dargestellt), beliebige andere Icons innerhalb eines img-Tags. "\
            "Du kannst außerdem das Makro $plugins_dir$ verwenden, um deine Bilder in einem eigenen Ordner innerhalb des Pluginordners abzulegen."\
            "Wichtig: 1. Leerzeichen spielen eine Rolle. 2. Die Reihenfolge kann eine Rolle Spielen, die Ersetzungen werden von oben nach unten durchgeführt."
        e.text = """\
Magieresistenz=MR
Probenschwierigkeit bzw. Beschwörungsschwierigkeit=Proben-/Beschwörungsschwierigkeit
16 bis 28 (nach Mächtigkeit des Geistes)=16 bis 28 (je nach Geist)
Beschwörungsschwierigkeit des Dämons -4=Beschwörungsschwierigkeit -4
Probenschwierigkeit -4 bzw. Beschwörungsschwierigkeit -4=Proben-/Beschwörungsschwierigkeit -4
Herstellungsschwierigkeit des Handwerksstücks=Herstellungsschwierigkeit
Beschwörungsschwierigkeit des zu bannenden Wesens=Beschwörungsschwierigkeit"""
        e.typ = "TextDict"
        e.separator = "\n"
        e.strip = False
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Talente Zeit kürzen"
        e.beschreibung =  "Bei Talenten werden die Zauberdauer und Wirkungsdauer in die obere Leiste eingetragen. Die Texte können dafür jedoch zu lang sein - "\
            "hier kannst du Teile davon zum Beispiel durch Abkürzungen oder Icons (bspw. von game-icons.net) ersetzen. "\
            "FontAwesome icons kannst du innerhalb eines span-Tags nutzen (hier nicht richtig dargestellt), beliebige andere Icons innerhalb eines img-Tags."\
            "Du kannst außerdem das Makro $plugins_dir$ verwenden, um deine Bilder in einem eigenen Ordner innerhalb des Pluginordners abzulegen."\
            "Wichtig: 1. Leerzeichen spielen eine Rolle. 2. Die Reihenfolge kann eine Rolle Spielen, die Ersetzungen werden von oben nach unten durchgeführt."
        e.text = """\
 Aktionen=
 Aktion=
 Sekunden= s
 Sekunde= s
 Minuten= m
 Minute= m
 Stunden= h
 Stunde= h
 Tage= T
 Tag= T
 Wochen= W
 Woche= W
 Monate= M
 Monat= M
 Jahr= J
 Jahre= J
 Initiativephasen=&nbsp;<span>\uf2f9</span>
 Initiativephase=&nbsp;<span>\uf2f9</span>
 Lebensjahr=&nbsp;<span>\uf1fd</span>
 Nacht=&nbsp;<span>\uf186</span>
bis zum nächsten Sonnenaufgang=<img src='../Icons/sunrise.svg'>
augenblicklich=0
bis die Bindung gelöst wird=<span>\uf127</span>
solange das Gift wirkt=<img src='../Icons/poison-bottle.svg'><span>\uf254</span>
bis zur Fertigstellung=<img src='../Icons/toolbox.svg'><span>\uf254</span>
permanent=<span>\uf534</span>
frei wählbar=<span>\uf83e</span>
nach Vorhaben=<span>\uf83e</span>
nach Projekt=<span>\uf83e</span>
nach Artefakt=<span>\uf83e</span>
wie das Ziel-Zeichen=<span>\u003d</span>&nbsp;<img src='../Icons/rune-stone.svg'>
wie die Ziel-Rune=<span>\u003d</span>&nbsp;<img src='../Icons/rune-stone.svg'>
bis zu =<span style='font-size: 6pt;'>\uf537</span>&nbsp;
bis zum =<span style='font-size: 6pt;'>\uf537</span>&nbsp;
mindestens =<span style='font-size: 6pt;'>\uf532</span>&nbsp;"""
        e.typ = "TextDict"
        e.separator = "\n"
        e.strip = False
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Talente Kosten kürzen"
        e.beschreibung = "Bei Talenten werden die Kosten in die obere Leiste eingetragen. Die Texte können dafür jedoch zu lang sein - "\
            "hier kannst du Teile davon zum Beispiel durch Abkürzungen oder Icons (bspw. von game-icons.net) ersetzen. "\
            "FontAwesome icons kannst du innerhalb eines span-Tags nutzen (hier nicht richtig dargestellt), beliebige andere Icons innerhalb eines img-Tags."\
            "Du kannst außerdem das Makro $plugins_dir$ verwenden, um deine Bilder in einem eigenen Ordner innerhalb des Pluginordners abzulegen."\
            "Wichtig: 1. Leerzeichen spielen eine Rolle. 2. Die Reihenfolge kann eine Rolle Spielen, die Ersetzungen werden von oben nach unten durchgeführt."
        e.text = """\
nach Projekt=<span>\uf83e</span>
nach Vorhaben=<span>\uf83e</span>"""
        e.typ = "TextDict"
        e.separator = "\n"
        e.strip = False
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Talente Reichweite kürzen"
        e.beschreibung = "Bei Talenten wird die Reichweite in die obere Leiste eingetragen. Die Texte können dafür jedoch zu lang sein - "\
            "hier kannst du Teile davon zum Beispiel durch Abkürzungen oder Icons (bspw. von game-icons.net) ersetzen. "\
            "FontAwesome icons kannst du innerhalb eines span-Tags nutzen (hier nicht richtig dargestellt), beliebige andere Icons innerhalb eines img-Tags."\
            "Du kannst außerdem das Makro $plugins_dir$ verwenden, um deine Bilder in einem eigenen Ordner innerhalb des Pluginordners abzulegen."\
            "Wichtig: 1. Leerzeichen spielen eine Rolle. 2. Die Reihenfolge kann eine Rolle Spielen, die Ersetzungen werden von oben nach unten durchgeführt."
        e.text = """\
 Schritt= S
 Meilen= Mi
 Meile= Mi
Berührung=<span>\uf256</span>
dereweit=<span>\uf0ac</span>
aventurienweit=<span>\uf0ac</span>"""
        e.typ = "TextDict"
        e.separator = "\n"
        e.strip = False
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Talente Ziel kürzen"
        e.beschreibung = "Bei Talenten wird das Ziel in die obere Leiste eingetragen. Die Texte können dafür jedoch zu lang sein - "\
            "hier kannst du Teile davon zum Beispiel durch Abkürzungen oder Icons (bspw. von game-icons.net) ersetzen. "\
            "FontAwesome icons kannst du innerhalb eines span-Tags nutzen (hier nicht richtig dargestellt), beliebige andere Icons innerhalb eines img-Tags."\
            "Du kannst außerdem das Makro $plugins_dir$ verwenden, um deine Bilder in einem eigenen Ordner innerhalb des Pluginordners abzulegen."\
            "Wichtig: 1. Leerzeichen spielen eine Rolle. 2. Die Reihenfolge kann eine Rolle Spielen, die Ersetzungen werden von oben nach unten durchgeführt."
        e.text = """\
 / =&nbsp;
/=&nbsp;
Einzelpersonen=<span>\uf0c0</span>
Einzelperson=<span>\uf183</span>
zwei Personen=<span>\uf183</span>&nbsp;+&nbsp;<span>\uf183</span>
Einzelwesen=<span>W</span>
Einzelobjekt (Hexenbesen)=<span>\uf51a</span>
Zone=<img src='../Icons/area-floor-size-icon.svg'>
selbst=<img src='../Icons/noun-me-4660321.svg'>
Einzelobjekte=<span>\uf468</span>
Einzelobjekt=<span>\uf466</span>
Ritualgegenstand=<img src='../Icons/curvy-knife.svg'>
Schale der Alchemie=<img src='../Icons/cauldron.svg'>
Zauberstab=<img src='../Icons/wizard-staff.svg'>
Zauberrune=<img src='../Icons/rune-stone.svg'>
Zauberzeichen=<img src='../Icons/rune-stone.svg'>
wirkender Zauber=<span>\uf72b</span>
Zauber=<span>\uf72b</span>
Liturgie=<img src='../Icons/sundial.svg'>
gebundener Kristall=<span>\uf3a5</span>
Knochenkeule=<img src='../Icons/bone-mace.svg'>
Kristallkugel=<img src='../Icons/crystal-ball.svg'>
zwei Objekte=<span>\uf466</span>&nbsp;+&nbsp;<span>\uf466</span>
einzelner Geist=<img src='../Icons/spectre.svg'>
einzelnes Tier=<span>\uf1b0</span>
Tier=<span>\uf1b0</span>
einzelne Pflanze=<span>\uf4d8</span>
Pflanze=<span>\uf4d8</span>
Vertrautentier=<span>\uf6be</span>
Bindungspartner=<img src='../Icons/noun-me-4660321.svg'>
zwei Elixiere=<span>\uf0c3</span>&nbsp;+&nbsp;<span>\uf0c3</span>
Elixier=<span>\uf0c3</span>
Miniatur der Herrschaft=<img src='../Icons/voodoo-doll.svg'>
einzelner Dämon=<img src='../Icons/daemon-skull.svg'>
einzelnes Elementar=<img src='../Icons/djinn.svg'>
Teilobjekt=Teil-<span>\uf466</span>
Iama=<img src='../Icons/lyre.svg'>
Schlangenreif=<img src='../Icons/ouroboros.svg'>
Schuppenbeutel=<img src='../Icons/swap-bag.svg'>
Bienen=<img src='../Icons/bee.svg'>
Oger=<img src='../Icons/ogre.svg'>
Pferd=<span>\uf6f0</span>
Feuermähre=<span>\uf6f0</span>
Leiche=<img src='../Icons/dead-head.svg'>
Material für einen einzelnen Untoten=<img src='../Icons/carrion.svg'>
Material für einen einzelnen Golem=<img src='../Icons/rock-golem.svg'>
Material für eine einzelne Chimäre=<img src='../Icons/lion.svg'><img src='../Icons/bird-claw.svg'><img src='../Icons/scorpion-tail.svg'>
, =&nbsp;|&nbsp;
,=&nbsp;|&nbsp;
 oder =&nbsp;|&nbsp;
 und =&nbsp;+&nbsp;"""
        e.typ = "TextDict"
        e.separator = "\n"
        e.strip = False
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Talente Ziel im Text"
        e.beschreibung = "Bei Talenten wird das Ziel normalerweise in die obere Leiste eingetragen. "\
            "Falls der Ziel-Text jedoch einen zum Teil aus einem der Einträge hier besteht, verbleibt er im Text."
        e.text = """\
Beschworenes Wesen
Einzelperson (nur maritime Humanoide)
Einzelperson von niedrigerem Status
Einzelpersonen, mit dir zumindest langjährig befreundet
Einzelobjekt aus (überwiegend) Holz
Tier der Größenklasse winzig
Sippenmitglied
ganze Sippe
Mackestopp
Bann- oder Schutzkreis"""
        e.typ = "TextList"
        e.separator = "\n"
        e.strip = False
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Talente Kosten im Text"
        e.beschreibung = "Bei Talenten werden die Kosten normalerweise in die obere Leiste eingetragen. "\
            "Falls der Kosten-Text jedoch einen zum Teil aus einem der Einträge hier besteht, verbleibt er im Text."
        e.text = """\
16/32/64 AsP
8/16/24/32 AsP
16/24/32/48/64/80 AsP
der Basiskosten als gAsP
halbe Basiskosten"""
        e.typ = "TextList"
        e.separator = "\n"
        e.strip = False
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Talente Zeit im Text"
        e.beschreibung = "Bei Talenten wird die Vorbereitungszeit bzw. Wirkungsdauer normalerweise in die obere Leiste eingetragen. "\
            "Falls der Text jedoch einen zum Teil aus einem der Einträge hier besteht, verbleibt er im Text."
        e.text = """\
augenblicklich; der Geist erscheint nach 2W6 Initiativephasen
bis das Schiff deutlich umgebaut wird
bis die Unterkunft deutlich umgebaut wird
8 Stunden oder bis der Fang eingeholt wird
Bis die Aufgabe gelöst wurde, maximal 1 Monat
oder bis der Befehl erfüllt ist
4 Stunden zzgl. frei wählbare Beschwörungsvorbereitung
1 Monat lang jede Nacht
8 Stunden je geprüftem Leben
bis du aufhörst oder das Opfer stirbt
bis die Bindung gelöst wird oder der Mackestopp zerbricht
bis die Bindung gelöst wird, nach Aktivierung noch 4 Minuten
bis die Bindung gelöst wird oder ein Patzer eingetreten ist
bis die Bindung gelöst wird, nach Aktivierung noch 1 Stunde
augenblicklich, der Tiegel bleibt etwa eine Stunde vor Ort
nach Spielleiterentscheid, monatelang wirkende Magnum Opera sollten eine schwächere Basiswirkung haben
bis die Bindung gelöst wird oder alle Pfeile ihr Ziel gefunden haben
32 Minuten oder bis 8 Schritte zurückgelegt wurden"""
        e.typ = "TextList"
        e.separator = "\n"
        e.strip = False
        self.db.loadElement(e)

        # only load plugin db if the main db doesn't contain cards already
        # this can happen if it is a merged db
        if len(self.db.karten) == 0:
            deserializer = Serialization.getDeserializer(".xml")
            dbFilePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data", "datenbank.xml")
            deserializer.readFile(dbFilePath)
            for name in deserializer.listTags():
                if name == "Karte":
                    k = Karte()
                    k.deserialize(deserializer)
                    self.db.loadElement(k)

    def datenbankEditorTypenHook(self, typen, params):
        typen[Karte] = DatenbankEditor.DatenbankTypWrapper(Karte, DatenbankEditKarteWrapper.DatenbankEditKarteWrapper, True)
        return typen

    def datenbankVerifyHook(self, errors, params):
        db = params["datenbank"]
        for karte in db.karten.values():
            try:
                VoraussetzungenListe().compile(karte.voraussetzungen.text, db)
            except VoraussetzungException as e:
                errorStr = f"{karte.displayName} {karte.name} hat fehlerhafte Voraussetzungen: {str(e)}"
                errors.append([karte, errorStr])
        return errors

    def charakterInstanziiertKategorienHandler(self, params):
        char = params["charakter"]
        char.deaktivierteKartenKategorien = []

    def charakterDeserialisiertKategorienHandler(self, params):
        char = params["charakter"]
        deserializer = params["deserializer"]
        if deserializer.find('Einstellungen'):
            deaktivierteKategorien = deserializer.getNested('DeaktivierteKartenKategorien')
            if deaktivierteKategorien:
                char.deaktivierteKartenKategorien = list(map(str.strip, deaktivierteKategorien.split(",")))      
            deserializer.end() #einstellungen

    def charakterSerialisiertKategorienHandler(self, params):
        char = params["charakter"]
        serializer = params["serializer"]
        if serializer.find('Einstellungen'):
            serializer.setNested('DeaktivierteKartenKategorien', ",".join(char.deaktivierteKartenKategorien))
            serializer.end() #einstellungen

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

        try:
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
        finally:
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

        try:
            dlg = ProgressDialogExt(minimum = 0, maximum = len(deck))
            dlg.setWindowTitle("Exportiere Manöverkarten")
            dlg.show()
            QtWidgets.QApplication.processEvents() #make sure the dialog immediatelly shows
            self.kartenGenerator.writeKarten(spath, deck, dialog.einzelExport, dialog.nameFormat, dlg)
        finally:
            dlg.hide()
            dlg.deleteLater()