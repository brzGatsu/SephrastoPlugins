from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from Wolke import Wolke
import tempfile
import PdfSerializer
import os
import re
import math
from Hilfsmethoden import Hilfsmethoden, WaffeneigenschaftException
import Objekte
from CharakterPrintUtility import CharakterPrintUtility
from DatenbankEinstellung import DatenbankEinstellung
from Fertigkeiten import Vorteil, VorteilLinkKategorie
import lxml.etree as etree

class Plugin:

    def __init__(self):
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHook)

        self.db = None
        self.enable = False
        self.maxLines = 20
        self.maxCharactersPerLine = 50

    @staticmethod
    def getDescription():
        return "Dieses Plugin gibt den Regelanhang zusätzlich als separate PDF in Spielkartengröße, auf sogenannten Manöverkarten aus.\n"\
            "Alternativ kann damit im Datenbankeditor auch die gesamte Regelbasis auf Karten ausgegeben werden.\n" \
            "Die Karten können dann z.B. im 3x3 Format auf dickes Papier gedruckt und dann ausgeschnitten werden."

    def createCharakterButtons(self):
        if not self.db.einstellungen["Manöverkarten Plugin: Charaktereditor Button zeigen"].toBool():
            return []

        self.exportChar = QtWidgets.QPushButton()
        self.exportChar.setObjectName("checkManöverkartenEnable")
        self.exportChar.setText("Manöverkarten erstellen")
        self.exportChar.setToolTip("Erstellt eine Datei mit dem Regelanhang in Form von Manöverkarten, falls aktiviert.")
        self.exportChar.clicked.connect(self.writeCharakterKarten)
        return [self.exportChar]

    def createDatabaseButtons(self):
        if not self.db.einstellungen["Manöverkarten Plugin: Datenbankeditor Button zeigen"].toBool():
            return []

        self.exportDB = QtWidgets.QPushButton()
        self.exportDB.setObjectName("buttonManöverkarten")
        self.exportDB.setText("Manöverkarten exportieren")
        self.exportDB.setToolTip("Exportiert die gesamte Datenbank als Manöverkarten.\n"\
            "Achtung: dieser Prozess kann eine lange Zeit benötigen (> 3 min.) und benötigt über 200 MB Speicherplatz, mehr je nach Größe eventueller Hausregeln.")
        self.exportDB.clicked.connect(self.writeDatenbankKarten)
        return [self.exportDB]

    def basisDatenbankGeladenHook(self, params):
        self.db = params["datenbank"]
        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Vorteilsfarbe Script"
        e.beschreibung = "Das Pythonscript kann dem Kartengenerator mitteilen, welche Vorteiltypen welche Kartenfarbe erhalten sollen.\n"\
            "Es stehen hierfür die Variablen typ (Vorteiltyp-Index) und farbe (blau, rot, violett, gold, schwarz, grün oder orange) zur Verfügung."
        e.wert = '''\
if typ ==  2 or typ == 3:
    farbe = "orange"
elif typ == 4 or typ == 5:
    farbe = "violett"
elif typ == 6 or typ == 7:
    farbe = "gold"
else:
    farbe = "schwarz"'''
        e.typ = "Text"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Manöverfarbe Script"
        e.beschreibung = "Das Pythonscript kann dem Kartengenerator mitteilen, welche Manövertypen welche Kartenfarbe erhalten sollen.\n"\
            "Es stehen hierfür die Variablen typ (Manövertyp-Index) und farbe (blau, rot, violett, gold, schwarz, grün oder orange) zur Verfügung."
        e.wert = '''\
if typ == 2 or typ == 4:
    farbe = "violett"
elif typ == 9:
    farbe = "schwarz"
elif typ == 3 or typ == 6 or typ == 7 or typ == 10:
    farbe = "gold"
else:
    farbe = "orange"'''
        e.typ = "Text"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Waffeneigenschaftenfarbe"
        e.beschreibung = "Definiert, welche Kartenfarbe Waffeneigenschaften haben sollen. Zur Verfügung stehen: blau, rot, violett, gold, schwarz, grün oder orange"
        e.wert = "orange"
        e.typ = "Text"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Zauberfarbe"
        e.beschreibung = "Definiert, welche Kartenfarbe Zauber haben sollen. Zur Verfügung stehen: blau, rot, violett, gold, schwarz, grün oder orange"
        e.wert = "blau"
        e.typ = "Text"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Liturgienfarbe"
        e.beschreibung = "Definiert, welche Kartenfarbe Liturgien haben sollen. Zur Verfügung stehen: blau, rot, violett, gold, schwarz, grün oder orange"
        e.wert = "grün"
        e.typ = "Text"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Anrufungsfarbe"
        e.beschreibung = "Definiert, welche Kartenfarbe Anrufungen haben sollen. Zur Verfügung stehen: blau, rot, violett, gold, schwarz, grün oder orange"
        e.wert = "grün"
        e.typ = "Text"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Vorteile zusammenfassen"
        e.beschreibung = "Definiert, welche Vorteilstyp-Indices (siehe 'Vorteile: Typen') auf Karten zusammengefasst zu werden. Die Angabe erfolgt als kommaseparierte Liste."
        e.wert = "0, 1, 2, 3, 4, 5, 6, 7, 8"
        e.typ = "Text"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Manöver zusammenfassen"
        e.beschreibung = "Definiert, welche Manövertyp-Indices (siehe 'Manöver: Typen') auf Karten zusammengefasst zu werden. Die Angabe erfolgt als kommaseparierte Liste."
        e.wert = ""
        e.typ = "Text"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Waffeneigenschaften zusammenfassen"
        e.beschreibung = "Definiert, ob Waffeneigenschaften auf Karten zusammengefasst werden."
        e.wert = "True"
        e.typ = "Bool"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Karten ohne Hintergrund"
        e.beschreibung = "Wenn diese Option aktiviert wird, verwendet der Kartengenerator Karten mit weißem Hintergrund - ideal, um Tinte zu sparen."
        e.wert = "False"
        e.typ = "Bool"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Charaktereditor Button zeigen"
        e.beschreibung = "Wenn diese Option aktiviert ist, wird im Charaktereditor eine Manöverkarten-Button zum Exportieren der charakterspezifischen Manöverkarten angezeigt."
        e.wert = "True"
        e.typ = "Bool"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "Manöverkarten Plugin: Datenbankeditor Button zeigen"
        e.beschreibung = "Wenn diese Option aktiviert wird, wird im Datenbankeditor ein Manöverkarten-Button zum Exportieren der Datenbank angezeigt."
        e.wert = "True"
        e.typ = "Bool"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

    def shortenTalent(self, text, dbExport = False):
        #Remove everything from Sephrasto on
        index = text.find('\nSephrasto')
        if index != -1:
            text = text[:index]

        index = text.find(' Sephrasto:')
        if index != -1:
            text = text[:index]

        if dbExport:
            return text

        #Remove everything from Anmerkung on but keep the text and append it later
        index = text.find('\nAnmerkung')
        anmerkung = ""
        if index != -1:
            anmerkung = text[index:]
            text = text[:index]

        #Remove everything from Fertigkeiten on
        index = text.find('\nFertigkeiten')
        if index != -1:
            text = text[:index]

        #Remove everything from Erlernen on (some talents don't have a Fertigkeiten list)
        index = text.find('\nErlernen')
        if index != -1:
            text = text[:index]

        text = text.strip(" \n")

        if anmerkung:
            text += (anmerkung)

        return text

    def adjustSize(self, text):
        lines = text.split("\n")
        linesAvailable = self.maxLines
        for line in lines:
            linesAvailable -= max(int(math.ceil(len(line) / self.maxCharactersPerLine)), 1)

        if linesAvailable > 0:
            text += ("\n" * linesAvailable)
        return text

    def doesFit(self, text, additional):
        if text == "":
            return True
        lines = text.split("\n")
        linesAvailable = int(self.maxLines * 1.1) # give it some leeway
        for line in lines:
            linesAvailable -= max(int(math.ceil(len(line) / self.maxCharactersPerLine)), 1)

        lines = additional.split("\n")
        for line in lines:
            linesAvailable -= max(int(math.ceil(len(line) / self.maxCharactersPerLine)), 1)

        return linesAvailable >= 0

    def writeTempPDF(self, srcFile, fields):
        if Wolke.Char:
            flatten = Wolke.Char.formularEditierbarkeit == 1 or Wolke.Char.formularEditierbarkeit == 2
        else:
            flatten = Wolke.Settings['Formular-Editierbarkeit'] == 1 or Wolke.Settings['Formular-Editierbarkeit'] == 2
        return PdfSerializer.write_pdf(srcFile, fields, None, flatten)

    def writeVorteilKartenEinzeln(self, karten, pdfName, vorteile):
        fields = { "Titel" : "", "Text" : "" }
        for vor in vorteile:
            vorteil = self.db.vorteile[vor]
            fields["Titel"] = CharakterPrintUtility.getLinkedName(Wolke.Char, vorteil)
            fields["Text"] = CharakterPrintUtility.getLinkedDescription(Wolke.Char, vorteil)
            if not fields["Text"]:
                continue
            if "\n" in fields["Text"]:
                fields["Text"] = "- " + fields["Text"].replace("\n", "\n- ")
            fields["Text"] = self.adjustSize(fields["Text"])
            karten.append(self.writeTempPDF(pdfName, fields))

    def writeVorteilKarten(self, karten, pdfName, titel, vorteile):
        num = 1
        text = ""
        fields = { "Titel" : titel + " " + str(num), "Text" : "" }
        for vor in vorteile:
            vorteil = self.db.vorteile[vor]
            beschreibung = CharakterPrintUtility.getLinkedDescription(Wolke.Char, vorteil)
            if not beschreibung:
                continue
            if "\n" in beschreibung:
                beschreibung = "- " + beschreibung.replace("\n", "\n- ")

            nextVortText = CharakterPrintUtility.getLinkedName(Wolke.Char, vorteil) + ":\n"
            nextVortText += beschreibung
            if self.doesFit(text, nextVortText):
                text += nextVortText + "\n\n"
            else:
                fields["Text"] = self.adjustSize(text[:-2])
                karten.append(self.writeTempPDF(pdfName, fields))
                text = nextVortText + "\n\n"
                num += 1
                fields["Titel"] = titel + " " + str(num)
        if text != "":
            fields["Text"] = self.adjustSize(text[:-2])
            karten.append(self.writeTempPDF(pdfName, fields))

    def writeTalentKarten(self, karten, pdfName, talente):
        fields = { "Titel" : "", "Text" : "" }
        for tal in talente:
            fields["Titel"] = tal.na
            fields["Text"] = self.adjustSize(self.shortenTalent(tal.text))
            karten.append(self.writeTempPDF(pdfName, fields))

    def trimManöverName(self, name):
        trim = [" (M)", " (L)", "(D)", " (FK)"]
        for t in trim:
            if name.endswith(t):
                name = name[:-len(t)]
        return name

    def writeManöverKartenEinzeln(self, karten, pdfName, manöver):
        fields = { "Titel" : "", "Text" : "" }
        for man in manöver:
            manöver = self.db.manöver[man]
            fields["Titel"] = self.trimManöverName(man)
            fields["Text"] = ""
            if manöver.probe:
                fields["Text"] += "Probe: " + manöver.probe + "\n"
            if manöver.gegenprobe:
                fields["Text"] += "Gegenprobe: " + manöver.gegenprobe + "\n"

            fields["Text"] += manöver.text
            fields["Text"] = self.adjustSize(fields["Text"])
            karten.append(self.writeTempPDF(pdfName, fields))

    def writeManöverKarten(self, karten, pdfName, titel, manöver):
        num = 1
        text = ""
        fields = { "Titel" : titel + " " + str(num), "Text" : "" }
        for man in manöver:
            manöver = self.db.manöver[man]
            nextManText = self.trimManöverName(man)
            if manöver.probe:
                nextManText += " (" + manöver.probe +")"
            nextManText += ":\n"
            if manöver.gegenprobe:
                nextManText += "Gegenprobe: " + manöver.gegenprobe + "\n"
            nextManText += manöver.text
            
            if self.doesFit(text, nextManText):
                text += nextManText + "\n\n"
            else:
                fields["Text"] = self.adjustSize(text[:-2])
                karten.append(self.writeTempPDF(pdfName, fields))
                text = nextManText + "\n\n"
                num += 1
                fields["Titel"] = titel + " " + str(num)
        if text != "":
            fields["Text"] = self.adjustSize(text[:-2])
            karten.append(self.writeTempPDF(pdfName, fields))

    def writeWaffeneigenschaftenKartenEinzeln(self, karten, pdfName, eigenschaften):
        fields = { "Titel" : "", "Text" : "" }
        for weName, waffen in sorted(eigenschaften.items()):
            if not self.db.waffeneigenschaften[weName].text:
                continue
            fields["Titel"] = weName
            fields["Text"] = "Waffen: " + (", ".join(waffen)) + "\n\n"
            fields["Text"] += self.db.waffeneigenschaften[weName].text
            fields["Text"] = self.adjustSize(fields["Text"])
            karten.append(self.writeTempPDF(pdfName, fields))

    def writeWaffeneigenschaftenKarten(self, karten, pdfName, titel, eigenschaften):
        num = 1
        text = ""
        fields = { "Titel" : titel + " " + str(num), "Text" : "" }
        for weName, waffen in sorted(eigenschaften.items()):
            nextWEText = weName + " (" + (", ".join(waffen)) + "):\n"
            nextWEText += self.db.waffeneigenschaften[weName].text
            if self.doesFit(text, nextWEText):
                text += nextWEText + "\n\n"
            else:
                fields["Text"] = self.adjustSize(text[:-2])
                karten.append(self.writeTempPDF(pdfName, fields))
                text = nextWEText + "\n\n"
                num += 1
                fields["Titel"] = titel + " " + str(num)
        if text != "":
            fields["Text"] = self.adjustSize(text[:-2])
            karten.append(self.writeTempPDF(pdfName, fields))

    def writeCharakterKarten(self):
        startDir = ""
        if os.path.isdir(Wolke.Settings['Pfad-Chars']):
            startDir = Wolke.Settings['Pfad-Chars']

        spath, _ = QtWidgets.QFileDialog.getSaveFileName(None,"Manöverkarten speichern...", startDir, "PDF-Datei (*.pdf)")
        if spath == "":
            return
        if ".pdf" not in spath:
            spath = spath + ".pdf"

        waffeneigenschaften = {}
        for waffe in Wolke.Char.waffen:
            for el in waffe.eigenschaften:
                try:
                    we = Hilfsmethoden.GetWaffeneigenschaft(el, Wolke.DB)
                    if not we.text:
                        continue
                    if not we.name in waffeneigenschaften:
                        waffeneigenschaften[we.name] = [waffe.anzeigename]
                    else:
                        waffeneigenschaften[we.name].append(waffe.anzeigename)
                except WaffeneigenschaftException:
                    pass      
        
        talentboxList = [t for t in CharakterPrintUtility.getÜberTalente(Wolke.Char) if t.text and t.cheatsheetAuflisten]
        (zauber, liturgien, anrufungen) = CharakterPrintUtility.groupUeberTalente(talentboxList)
        vorteilTypen = self.db.einstellungen["Vorteile: Typen"].toTextList()
        manöverTypen = self.db.einstellungen["Manöver: Typen"].toTextList()

        sortV = Wolke.Char.vorteile.copy()
        sortV = sorted(sortV, key=str.lower)
        vorteileGruppiert = []
        for i in range(len(vorteilTypen)):
            vorteileGruppiert.append([v for v in sortV if self.db.vorteile[v].text and \
                self.db.vorteile[v].cheatsheetAuflisten and \
                self.db.vorteile[v].typ == i and \
                not CharakterPrintUtility.isLinkedToVorteil(Wolke.Char, self.db.vorteile[v])])

        sortM = list(self.db.manöver.keys())
        sortM = sorted(sortM, key=str.lower)
        manöverGruppiert = []
        for i in range(len(manöverTypen)):
            manöverGruppiert.append(sorted([m for m in sortM if self.db.manöver[m].text and \
                self.db.manöver[m].typ == i and \
                Wolke.Char.voraussetzungenPrüfen(self.db.manöver[m].voraussetzungen)]))

        kartenPfad = os.path.dirname(os.path.abspath(__file__))
        kartenPfad = os.path.join(kartenPfad, "Data")

        vorteileZusammenfassen = self.db.einstellungen["Manöverkarten Plugin: Vorteile zusammenfassen"].toTextList()
        for i in range(len(vorteileZusammenfassen)):
            vorteileZusammenfassen[i] = int(vorteileZusammenfassen[i])
        manöverZusammenfassen = self.db.einstellungen["Manöverkarten Plugin: Manöver zusammenfassen"].toTextList()
        for i in range(len(manöverZusammenfassen)):
            manöverZusammenfassen[i] = int(manöverZusammenfassen[i])
        weZusammenfassen = self.db.einstellungen["Manöverkarten Plugin: Waffeneigenschaften zusammenfassen"].toBool()
        manöverFarbeScript = self.db.einstellungen["Manöverkarten Plugin: Manöverfarbe Script"].toText()
        vorteilFarbeScript = self.db.einstellungen["Manöverkarten Plugin: Vorteilsfarbe Script"].toText()
        reihenfolge = self.db.einstellungen["Regelanhang: Reihenfolge"].toTextList()
        karten = []
        for r in reihenfolge:
            if r[0] == "V":
                typ = int(r[1:])
                if typ >= len(vorteileGruppiert):
                    continue
                scriptVariables = { "typ" : typ, "farbe" : "schwarz" }
                exec(vorteilFarbeScript, scriptVariables)
                karte = os.path.join(kartenPfad, scriptVariables["farbe"] + ".pdf")
                if typ in vorteileZusammenfassen:
                    self.writeVorteilKarten(karten, karte, vorteilTypen[typ], vorteileGruppiert[typ])
                else:
                    self.writeVorteilKartenEinzeln(karten, karte, vorteileGruppiert[typ])                    
            elif r[0] == "M":
                typ = int(r[1:])
                if typ >= len(manöverGruppiert):
                    continue
                scriptVariables = { "typ" : typ, "farbe" : "schwarz" }
                exec(manöverFarbeScript, scriptVariables)
                karte = os.path.join(kartenPfad, scriptVariables["farbe"] + ".pdf")
                if typ in manöverZusammenfassen:
                    self.writeManöverKarten(karten, karte, manöverTypen[typ], manöverGruppiert[typ])
                else:   
                    self.writeManöverKartenEinzeln(karten, karte, manöverGruppiert[typ])
            elif r[0] == "W":
                karte = os.path.join(kartenPfad, self.db.einstellungen["Manöverkarten Plugin: Waffeneigenschaftenfarbe"].toText() + ".pdf")
                if weZusammenfassen:
                    self.writeWaffeneigenschaftenKarten(karten, karte, "Waffeneigenschaften", waffeneigenschaften)
                else:
                    self.writeWaffeneigenschaftenKartenEinzeln(karten, karte, waffeneigenschaften)
            elif r[0] == "Z":
                karte = os.path.join(kartenPfad, self.db.einstellungen["Manöverkarten Plugin: Zauberfarbe"].toText() + ".pdf")
                self.writeTalentKarten(karten, karte, zauber)
            elif r[0] == "L":
                karte = os.path.join(kartenPfad, self.db.einstellungen["Manöverkarten Plugin: Liturgienfarbe"].toText() + ".pdf")
                self.writeTalentKarten(karten, karte, liturgien)
            elif r[0] == "A":
                karte = os.path.join(kartenPfad, self.db.einstellungen["Manöverkarten Plugin: Anrufungsfarbe"].toText() + ".pdf")
                self.writeTalentKarten(karten, karte, anrufungen)

        if self.db.einstellungen["Manöverkarten Plugin: Karten ohne Hintergrund"].toBool():
            PdfSerializer.concat(karten, spath)
            PdfSerializer.squeeze(spath, spath)
        else:
            concatPath = PdfSerializer.concat(karten)
            hintergrundPath = os.path.join(kartenPfad, "hintergrund.pdf")
            PdfSerializer.addBackground(concatPath, hintergrundPath, spath)
            os.remove(concatPath)
            PdfSerializer.squeeze(spath, spath)

        for karte in karten:
            os.remove(karte)

        if Wolke.Settings['PDF-Open']:
            os.startfile(spath, 'open')

    def writeDatenbankDeck(self, karten, spath, deckName):
        if len(karten) == 0:
            return
        if self.db.einstellungen["Manöverkarten Plugin: Karten ohne Hintergrund"].toBool():
            path = os.path.join(spath, deckName + ".pdf")
            PdfSerializer.concat(karten, path)
            PdfSerializer.squeeze(path, path)

        else:
            handle, concatPath = tempfile.mkstemp()
            os.close(handle)
            PdfSerializer.concat(karten, concatPath)
            kartenPfad = os.path.dirname(os.path.abspath(__file__))
            kartenPfad = os.path.join(kartenPfad, "Data")
            hintergrundPath = os.path.join(kartenPfad, "hintergrund.pdf")
            path = os.path.join(spath, deckName + ".pdf")
            PdfSerializer.addBackground(concatPath, hintergrundPath, path)
            PdfSerializer.squeeze(path, path)
            os.remove(concatPath)

        for karte in karten:
            os.remove(karte)
        karten.clear()

    def getVorteilDescription(self, vorteil):
        beschreibung = vorteil.text.replace("\n\n", "\n")
        if len(vorteil.cheatsheetBeschreibung) > 0 and not "$kommentar$" in vorteil.cheatsheetBeschreibung:
            beschreibung = vorteil.cheatsheetBeschreibung

        if vorteil.linkKategorie == VorteilLinkKategorie.Vorteil:
            beschreibungenErsetzen = [int(typ) for typ in self.db.einstellungen["Regelanhang: Vorteilsbeschreibungen ersetzen"].toTextList()]
            if vorteil.typ in beschreibungenErsetzen:
                return beschreibung
            beschreibung2 = self.getVorteilDescription(self.db.vorteile[vorteil.linkElement])
            beschreibung = CharakterPrintUtility.mergeDescriptions(beschreibung2, beschreibung)

        return beschreibung

    def writeDatenbankKarten(self):
        if self.db is None:
            return

        startDir = ""
        spath = QtWidgets.QFileDialog.getExistingDirectory(None, "Wähle einen Ordner, in dem die Kartendecks gespeichert werden sollen", startDir)
        if spath == "":
            return

        kartenPfad = os.path.dirname(os.path.abspath(__file__))
        kartenPfad = os.path.join(kartenPfad, "Data")

        manöverFarbeScript = self.db.einstellungen["Manöverkarten Plugin: Manöverfarbe Script"].toText()
        vorteilFarbeScript = self.db.einstellungen["Manöverkarten Plugin: Vorteilsfarbe Script"].toText()

        vorteilTypen = self.db.einstellungen["Vorteile: Typen"].toTextList()
        manöverTypen = self.db.einstellungen["Manöver: Typen"].toTextList()
        vorteileGruppiert = []
        for i in range(len(vorteilTypen)):
            vorteileGruppiert.append([v for v in self.db.vorteile.values() if v.text and v.cheatsheetAuflisten and v.typ == i])
            vorteileGruppiert[i] = sorted(vorteileGruppiert[i], key = lambda v: v.name)

        manöverGruppiert = []
        for i in range(len(manöverTypen)):
            manöverGruppiert.append([m for m in self.db.manöver.values() if m.text and m.typ == i])
            manöverGruppiert[i] = sorted(manöverGruppiert[i], key = lambda m: m.name)

        waffeneigenschaften = [w for w in self.db.waffeneigenschaften.values() if w.text]
        waffeneigenschaften = sorted(waffeneigenschaften, key = lambda w: w.name)

        talente = [t for t in self.db.talente.values() if t.isSpezialTalent() and \
            t.cheatsheetAuflisten and \
            not t.name.endswith(" (Blutgeist)") and \
            not t.name.endswith(" (Tiergeist)")]

        def getTalentTyp(talent):
            if len(talent.fertigkeiten) == 0:
                return 0

            for f in talent.fertigkeiten:
                if self.db.übernatürlicheFertigkeiten[f].talenteGruppieren:
                    return self.db.übernatürlicheFertigkeiten[f].printclass
            return self.db.übernatürlicheFertigkeiten[talent.fertigkeiten[0]].printclass

        def sortTalente(talent):
            return (getTalentTyp(talent), talent.name)

        talente = sorted(talente, key = lambda talent: sortTalente(talent))
        liturgieTypen = [int(t) for t in self.db.einstellungen["Fertigkeiten: Liturgie-Typen"].toTextList()]
        anrufungTypen = [int(t) for t in self.db.einstellungen["Fertigkeiten: Anrufungs-Typen"].toTextList()]
        fertigkeitsTypen = self.db.einstellungen["Fertigkeiten: Typen übernatürlich"].toTextList()
        zauber = []
        liturgien = []
        anrufungen = []
        for t in fertigkeitsTypen:
            zauber.append([])
            liturgien.append([])
            anrufungen.append([])

        for tal in talente:
            typ = getTalentTyp(tal)
            if typ >= len(fertigkeitsTypen):
                continue
            if typ in liturgieTypen:
                liturgien[typ].append(tal)
            elif typ in anrufungTypen:
                anrufungen[typ].append(tal)
            else:
                zauber[typ].append(tal)

        fields = { "Titel" : "", "Text" : "" }
        karten = []
        for typ in range(len(vorteilTypen)):
            scriptVariables = { "typ" : typ, "farbe" : "schwarz" }
            exec(vorteilFarbeScript, scriptVariables)
            karte = os.path.join(kartenPfad, scriptVariables["farbe"] + ".pdf")
            for vorteil in vorteileGruppiert[typ]:
                fields["Titel"] = vorteil.name
                if "Regelanhang: Vorteilsbeschreibungen ersetzen" in self.db.einstellungen: # sephrasto 3.2+
                    fields["Text"] = self.shortenTalent(self.getVorteilDescription(vorteil), True)
                else:
                    fields["Text"] = self.shortenTalent(vorteil.text, True)
                if "\n" in fields["Text"]:
                    fields["Text"] = "- " + fields["Text"].replace("\n", "\n- ")
                fields["Text"] = self.adjustSize(fields["Text"])
                karten.append(self.writeTempPDF(karte, fields))
            self.writeDatenbankDeck(karten, spath, vorteilTypen[typ])

        for typ in range(len(manöverTypen)):
            scriptVariables = { "typ" : typ, "farbe" : "schwarz" }
            exec(manöverFarbeScript, scriptVariables)
            karte = os.path.join(kartenPfad, scriptVariables["farbe"] + ".pdf")

            for manöver in manöverGruppiert[typ]:
                fields["Titel"] = self.trimManöverName(manöver.name)
                fields["Text"] = ""
                if manöver.probe:
                    if len(manöver.probe) > 15:
                        fields["Text"] += "Probe: " + manöver.probe + "\n"
                    else:
                        fields["Titel"] += " (" + manöver.probe + ")"
                if manöver.gegenprobe:
                    fields["Text"] += "Gegenprobe: " + manöver.gegenprobe + "\n"
                fields["Text"] += manöver.text
                fields["Text"] = self.adjustSize(fields["Text"])
                karten.append(self.writeTempPDF(karte, fields))
            self.writeDatenbankDeck(karten, spath, manöverTypen[typ])

        karte = os.path.join(kartenPfad, self.db.einstellungen["Manöverkarten Plugin: Waffeneigenschaftenfarbe"].toText() + ".pdf")
        for we in waffeneigenschaften:
            fields["Titel"] = we.name
            fields["Text"] = self.adjustSize(we.text)
            karten.append(self.writeTempPDF(karte, fields))
        self.writeDatenbankDeck(karten, spath, "Waffeneigenschaften")

        karte = os.path.join(kartenPfad, self.db.einstellungen["Manöverkarten Plugin: Zauberfarbe"].toText() + ".pdf")
        for i in range(len(zauber)):
            for talent in zauber[i]:
                fields["Titel"] = talent.name
                fields["Text"] = self.adjustSize(self.shortenTalent(talent.text, dbExport = True))
                karten.append(self.writeTempPDF(karte, fields))
            self.writeDatenbankDeck(karten, spath, fertigkeitsTypen[i])

        karte = os.path.join(kartenPfad, self.db.einstellungen["Manöverkarten Plugin: Liturgienfarbe"].toText() + ".pdf")
        for i in range(len(liturgien)):
            for talent in liturgien[i]:
                fields["Titel"] = talent.name
                fields["Text"] = self.adjustSize(self.shortenTalent(talent.text, dbExport = True))
                karten.append(self.writeTempPDF(karte, fields))
            self.writeDatenbankDeck(karten, spath, fertigkeitsTypen[i])

        karte = os.path.join(kartenPfad, self.db.einstellungen["Manöverkarten Plugin: Anrufungsfarbe"].toText() + ".pdf")
        for i in range(len(anrufungen)):
            for talent in anrufungen[i]:
                fields["Titel"] = talent.name
                fields["Text"] = self.adjustSize(self.shortenTalent(talent.text, dbExport = True))
                karten.append(self.writeTempPDF(karte, fields))
            self.writeDatenbankDeck(karten, spath, fertigkeitsTypen[i])