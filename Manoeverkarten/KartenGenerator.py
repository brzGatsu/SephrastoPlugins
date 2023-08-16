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
from Core.Vorteil import Vorteil, VorteilLinkKategorie
import lxml.etree as etree
import DatenbankEditor
from Manoeverkarten import DatenbankEditKarteWrapper, KartenExportDialogWrapper
from Manoeverkarten.Manoeverkarte import KartenTyp, Karte, KartenUtility
from Core.Talent import TalentDefinition
from Core.Vorteil import VorteilDefinition
from Core.Waffeneigenschaft import Waffeneigenschaft
from Core.Regel import Regel
from EventBus import EventBus
import copy
import PathHelper
from QtUtils.WebEngineViewPlus import WebEngineViewPlus

class KartenGenerator:
    def __init__(self, db):
        self.db = db
        self.templates = {}

        self.pluginFolder = os.path.dirname(os.path.abspath(__file__))
        self.fertImagesFolder = os.path.join(self.pluginFolder, "Data", "Fertigkeiten")
        templateFolder = os.path.join(self.pluginFolder, "Data", "Templates")
        for file in PathHelper.listdir(templateFolder):
            absoluteFilePath = os.path.join(templateFolder, file)
            if not os.path.isfile(absoluteFilePath) or not file.endswith(".html"):
                continue

            with open(absoluteFilePath, 'r', encoding="utf-8") as infile:
                self.templates[os.path.splitext(file)[0]] = [absoluteFilePath, infile.read()]

    def getVorteilBedingungen(self, vorteil):
        bedingungen = vorteil.bedingungen
        if vorteil.linkKategorie == VorteilLinkKategorie.Vorteil: 
            beschreibungenErsetzen = self.db.einstellungen["Regelanhang: Vorteilsbeschreibungen ersetzen"].wert
            if vorteil.typ not in beschreibungenErsetzen:
                bedingungen2 = self.getVorteilBedingungen(self.db.vorteile[vorteil.linkElement])
                if bedingungen2:
                    bedingungen = bedingungen2 + "\n" + bedingungen

        return bedingungen.strip()

    def getVorteilDescription(self, vorteil):
        beschreibung = vorteil.cheatsheetBeschreibung.replace("\n\n", "\n")
        if not beschreibung:
            beschreibung = vorteil.text.replace("\n\n", "\n")

        if vorteil.linkKategorie == VorteilLinkKategorie.Vorteil:              
            beschreibungenErsetzen = self.db.einstellungen["Regelanhang: Vorteilsbeschreibungen ersetzen"].wert
            namenErsetzen = self.db.einstellungen["Regelanhang: Vorteilsnamen ersetzen"].wert
            #hacky, we only want to merge descriptions for kampfstile and traditionen
            if vorteil.typ not in beschreibungenErsetzen and vorteil.typ in namenErsetzen:
                beschreibung2 = self.getVorteilDescription(self.db.vorteile[vorteil.linkElement])
                beschreibung = CharakterPrintUtility.mergeDescriptions(beschreibung2, beschreibung)

        return beschreibung

    def generatePrologKarte(self):
        karte = Karte()
        karte.name = "Intro"
        karte.subtitel = "Manöverkarten"
        karte.typ = KartenTyp.Deck
        karte.text = '''Manöverkarten enthalten die wichtigsten Regeln für den Kampf, Zauber, Liturgien und mehr \
auf ausdruckbaren Spielkarten. Im Spiel legst du je nach Situation die passenden Karten vor dir ab, um immer \
einen guten Überblick zu bewahren. Als Nahkämpfer könnten das z.B. die <i>Nahkampfmanöver</i>-Karten sowie die Karten <i>Nahkampfmodifikatoren</i> \
und <i>Modifikator</i> sein. Manöver hältst du auf der Hand, spielst sie aus, wenn du sie ansagen möchtest und nimmst \
sie wieder auf die Hand, wenn die Wirkung beendet ist.<br><br><br><br>
<p align="center">Erstellt mit Gatsus Manöverkarten-Plugin<br>Grafiken der Deck-Karten und Kartenhintergrund mit freundlicher Erlaubnis von Bernhard Eisner.</p>'''

        return self.generateZusatzKarte(karte, "#000000")

    def generateDruckanleitungKarte(self):
        karte = Karte()
        karte.name = "Druckanleitung"
        karte.subtitel = "Manöverkarten"
        karte.typ = KartenTyp.Deck
        karte.text = '''Öffne die PDF mit dem Adobe Reader und notiere die Seitenzahlen aller Karten, die für dich relevant \
sind. Gehe in das Druckmenü, unter <b>Zu druckende Seiten</b> selektiere <b>Seiten</b> und tippe die Seitenzahlen ein – \
kommagetrennt oder mehrere nacheinander mit einem Bindestrich. Unter <b>Seite anpassen und Optionen</b> nun <b>Mehrere</b> und bei Seiten pro Blatt <b>9</b> \
auswählen. Wenn du Tinte/Tone sparen möchtest, kannst du die Karten ohne Hintergrund nutzen und <b>In Graustufen</b> auswählen.<br>\
Nutze möglichst dickes, seidenmatt beschichtetes Papier („coated silk“). Die meisten Drucker unterstützen bis zu 180 g/m², auf \
höhere Herstellerangaben ist leider kein Verlass. Die ausgeschnittenen Karten erhalten mit Card Sleeves für die Größe 63,5 x 88 mm \
mehr Festigkeit. Zusätzlich bieten diese Schutz gegen Abnutzung und können mit einem Folienstift beschrieben werden. Gute Erfahrungen \
habe ich mit docsmagic.de gemacht, hier werden Sleeves mit farbigen Rückseiten angeboten, passend zu den Decks.'''

        return self.generateZusatzKarte(karte, "#000000")

    def removeLine(self, text, line):
        res = re.findall(r'^({}.*?)($|\n)'.format(line), text, re.UNICODE|re.MULTILINE)
        if len(res) == 1:
            return text.replace(res[0][0] + "\n", "").replace(res[0][0], ""), res[0][0].replace(line, "").strip()
        return text, ""

    def removeLineHtml(self, text, line):
        text, extractedLine = self.removeLine(text, f"<b>{line}</b>")
        if not extractedLine:
            text, extractedLine = self.removeLine(text, line)
        return text, extractedLine

    def findLine(self, text, line):
        res = re.findall(r'^({}.*?)($|\n)'.format(line), text, re.UNICODE|re.MULTILINE)
        if len(res) == 1:
            return res[0][0].replace(line, "").strip()
        return ""

    def findLineHtml(self, text, line):
        extractedLine = self.findLine(text, f"<b>{line}</b>")
        if not extractedLine:
            extractedLine = self.findLine(text, line)
        return extractedLine

    def shorten(self, line, mapping):
        for key, value in mapping.items():
            line = line.replace(key, value)
        line = line.replace("$plugins_dir$", "file:///" + Wolke.Settings['Pfad-Plugins'].replace('\\', '/'))
        return line

    def shortenCost(self, line):
        changed = False
        for key, value in self.db.einstellungen["Manöverkarten Plugin: Talente Kosten kürzen"].wert.items():
            if key in line:
                changed = True
                line = line.replace(key, value)

        if not changed:
            kosten = []
            for match in re.findall(r"\d+", line, re.UNICODE):
                kosten.append(match)
            line = "/".join(kosten)
        line = line.replace("$plugins_dir$", "file:///" + Wolke.Settings['Pfad-Plugins'].replace('\\', '/'))
        return line

    def shouldRemove(self, line, mapping):
        for value in mapping:
            if value in line:
                return False
        return True

    def findFertImage(self, fert):
        if fert in self.db.einstellungen["Manöverkarten Plugin: Zusätzliche Fertigkeiticons"].wert:
            file = self.db.einstellungen["Manöverkarten Plugin: Zusätzliche Fertigkeiticons"].wert[fert]
            file = file.replace("$plugins_dir$", "file:///" + Wolke.Settings['Pfad-Plugins'].replace('\\', '/'))
            if file.endwith(".svg"):
                return f"<div><img src='{file}'></div>"            
            else:
                return f"<img src='{file}'>"

        fertSplit = fert.split(" (")[0] #remove all from paranthesis on
        file = os.path.join(self.fertImagesFolder, fert + ".png")
        if os.path.isfile(file):
            return f"<img src='{file}'>"
        file = os.path.join(self.fertImagesFolder, fertSplit + ".png")
        if os.path.isfile(file): 
            return f"<img src='{file}'>"
        file = os.path.join(self.fertImagesFolder, fert + ".svg")
        if os.path.isfile(file): # we expect svg to be icons only
            return f"<div><img src='{file}'></div>"
        file = os.path.join(self.fertImagesFolder, fertSplit + ".svg")
        if os.path.isfile(file):
            return f"<div><img src='{file}'></div>"

        return f"<div><span>{fert.replace(' ', '<br>', 1)}</span></div>" # just add the name as text with max 1 linebreak

    def postProcessTalent(self, karte, element = None):
        for data in ["vorbereitungszeiticon", "vorbereitungszeit", "zielicon", "ziel", "reichweiteicon", "reichweite", "wirkungsdauericon", "wirkungsdauer", "kostenicon", "kosten", "erlernen", "fertigkeiten"]:
            karte.customData[data] = ""

        karte.text, line = self.removeLineHtml(karte.text, "Probenschwierigkeit:")
        if line:
            if karte.subtitel:
                karte.subtitel += " | "
            karte.subtitel += self.shorten(line, self.db.einstellungen["Manöverkarten Plugin: Talente Schwierigkeit kürzen"].wert)

        line = self.findLineHtml(karte.text, "Vorbereitungszeit:")
        if line:
            karte.customData["vorbereitungszeiticon"] = "\uf254"
            if self.shouldRemove(line, self.db.einstellungen["Manöverkarten Plugin: Talente Zeit im Text"].wert):
                karte.text, line = self.removeLineHtml(karte.text, "Vorbereitungszeit:")
                karte.customData["vorbereitungszeit"] = self.shorten(line, self.db.einstellungen["Manöverkarten Plugin: Talente Zeit kürzen"].wert)
            else:
                karte.customData["vorbereitungszeit"] = "<span>\uf063</span>"

        line = self.findLineHtml(karte.text, "Ziel:")
        if line:
            karte.customData["zielicon"] = "\uf140"
            if self.shouldRemove(line, self.db.einstellungen["Manöverkarten Plugin: Talente Ziel im Text"].wert):
                karte.text, line = self.removeLineHtml(karte.text, "Ziel:")
                karte.customData["ziel"] = self.shorten(line, self.db.einstellungen["Manöverkarten Plugin: Talente Ziel kürzen"].wert)
            else:
                karte.customData["ziel"] = "<span>\uf063</span>"

        karte.text, line = self.removeLineHtml(karte.text, "Reichweite:")
        if line:
            karte.customData["reichweiteicon"] = "\uf545"
            karte.customData["reichweite"] = self.shorten(line, self.db.einstellungen["Manöverkarten Plugin: Talente Reichweite kürzen"].wert)

        line = self.findLineHtml(karte.text, "Wirkungsdauer:")
        if line:
            karte.customData["wirkungsdauericon"] = "\uf2f2"
            if self.shouldRemove(line, self.db.einstellungen["Manöverkarten Plugin: Talente Zeit im Text"].wert):
                karte.text, line = self.removeLineHtml(karte.text, "Wirkungsdauer:")
                karte.customData["wirkungsdauer"] = self.shorten(line, self.db.einstellungen["Manöverkarten Plugin: Talente Zeit kürzen"].wert)
            else:
                karte.customData["wirkungsdauer"] = "<span>\uf063</span>"

        line = self.findLineHtml(karte.text, "Kosten:")
        if line:
            karte.customData["kostenicon"] = "\uf0e7"
            if self.shouldRemove(line, self.db.einstellungen["Manöverkarten Plugin: Talente Kosten im Text"].wert):
                karte.text, line = self.removeLineHtml(karte.text, "Kosten:")
                karte.customData["kosten"] = self.shortenCost(line)
            else:
                karte.customData["kosten"] = "<span>\uf063</span>"


        karte.text, line = self.removeLineHtml(karte.text, "Fertigkeiten:")
        ferts = []
        if line:
            ferts = list(map(str.strip, re.split(",(?![^(]*\))", line, re.UNICODE))) #spells like Hartes schmelze have paranthesis here
        elif element is not None and element.hauptfertigkeit is not None:
            ferts.append(element.hauptfertigkeit.name)

        images = []
        fertFolder = os.path.join(self.pluginFolder, "Data", "Fertigkeiten")
        for fert in ferts:
            images.append(self.findFertImage(fert))
        karte.customData["fertigkeiten"] = "".join(images)

        karte.text, line = self.removeLineHtml(karte.text, "Erlernen:")
        if line:
            karte.customData["erlernen"] = line

        karte.text = karte.text.strip()

    def generateZusatzKarte(self, k, farbe):
        karte = Karte()
        karte.typ = k.typ
        karte.farbe = farbe
        karte.name = k.name
        karte.titel = k.anzeigename
        karte.text = k.text.replace("$original$", "")
        if k.typ == KartenTyp.Talent:
            karte.subtitel = k.subtitel.replace("$original$", "PW <u>" + "&nbsp;"*12 + "</u>")
        else:
            karte.subtitel = k.subtitel.replace("$original$", "")
        footer = ""
        if k.typ == KartenTyp.Vorteil:
            footer = self.db.einstellungen["Vorteile: Typen"].wert[k.subtyp]
        elif k.typ == KartenTyp.Regel:
            footer = self.db.einstellungen["Regeln: Typen"].wert[k.subtyp]
        karte.fusszeile = k.fusszeile.replace("$original$", footer)

        if k.typ == KartenTyp.Talent:
            self.postProcessTalent(karte)

        return karte

    def generateKarte(self, element, farbe, overrideKarte = None):
        karte = Karte()
        karte.farbe = farbe
        karte.name = element.name
        karte.titel = element.name

        if isinstance(element, VorteilDefinition):
            karte.typ = KartenTyp.Vorteil
            karte.subtyp = element.typ
            #if Wolke.Char:
            #    titel = CharakterPrintUtility.getLinkedName(Wolke.Char, vorteil, True)
            text = self.getVorteilDescription(element)
            listified = "<ul" in text or "<ol" in text
            if not listified and "\n" in text:
                text = "<ul><li>" + text.replace("\n", "</li><li>") + "</li></ul>"
                listified = True

            #if not Wolke.Char:
            text = "<i>Wirkung:</i> " + text
            bedingungen = self.getVorteilBedingungen(element)
            if bedingungen:
                text = f"<i>Bedingungen:</i> {bedingungen}\n{text}"

            voraussetzungen = Hilfsmethoden.VorArray2AnzeigeStr(element.voraussetzungen, self.db)
            voraussetzungen = (voraussetzungen[:100] + '...') if len(voraussetzungen) > 100 else voraussetzungen
            if element.variableKosten:
                voraussetzungen += f"; EP-Kosten variabel"
            else:
                voraussetzungen += f"; {element.kosten} EP"
            if not listified:
                text += "<br>"
            text += "<i>Voraussetzungen:</i> " + voraussetzungen + "<br><i>Nachkauf:</i> " + element.nachkauf
            karte.text = text
            karte.fusszeile = self.db.einstellungen["Vorteile: Typen"].wert[element.typ]
            karte.subtitel = ""
            if element.kommentarErlauben:
                line = "<table style='width: 100%; margin-bottom: 4px;'><tr style='border-bottom: 1px solid black;'><td>&nbsp;</td></tr></table>"
                if "$kommentar$" in karte.text:
                    karte.text = karte.text.replace("$kommentar$.", "$kommentar$").replace("$kommentar$", line)
                else:
                    karte.subtitel = line
        elif isinstance(element, TalentDefinition):
            karte.typ = KartenTyp.Talent
            karte.subtyp = element.spezialTyp
            karte.text = element.text
            karte.subtitel = "PW <u>" + "&nbsp;"*12 + "</u>"
            if element.hauptfertigkeit is not None:
                karte.fusszeile = self.db.einstellungen["Fertigkeiten: Typen übernatürlich"].wert[element.hauptfertigkeit.typ]
            else:
                karte.fusszeile = ""
            if element.kommentarErlauben:
                line = "<table style='width: 100%; margin-bottom: 4px;'><tr style='border-bottom: 1px solid black;'><td>&nbsp;</td></tr></table>"
                if "$kommentar$" in karte.text:
                    karte.text = karte.text.replace("$kommentar$.", "$kommentar$").replace("$kommentar$", line)
                else:
                    karte.text = line + karte.text
        elif isinstance(element, Regel):
            karte.typ = KartenTyp.Regel
            karte.subtyp = element.typ
            karte.titel = element.anzeigename
            karte.text = element.text
            karte.subtitel = element.probe
            karte.fusszeile = self.db.einstellungen["Regeln: Typen"].wert[element.typ]
        elif isinstance(element, Waffeneigenschaft):
            karte.typ = KartenTyp.Waffeneigenschaft
            karte.text = element.text
            karte.subtitel = ""
            karte.fusszeile = "Waffeneigenschaft"

        if overrideKarte is not None:
            if overrideKarte.löschen:
                return None

            karte.titel = overrideKarte.titel.replace("$original$", karte.titel)
            karte.subtitel = overrideKarte.subtitel.replace("$original$", karte.subtitel)
            karte.text = overrideKarte.text.replace("$original$", karte.text)
            karte.fusszeile = overrideKarte.fusszeile.replace("$original$", karte.fusszeile)
            karte.typ = overrideKarte.typ
            karte.subtyp = overrideKarte.subtyp

        if isinstance(element, TalentDefinition):
            self.postProcessTalent(karte, element)

        if not karte.text:
            return None

        return karte

    def generateDBKarten(self, deaktivierteKategorien):
        talente = [t for t in self.db.talente.values() if t.cheatsheetAuflisten and not t.name.endswith(" (Tiergeist)")]
        return self.generate(deaktivierteKategorien, self.db.vorteile.values(), self.db.regeln.values(), self.db.waffeneigenschaften.values(), talente, self.db.karten.values())

    def generateCharKarten(self, deaktivierteKategorien):
        # Vorteile
        namenErsetzen = self.db.einstellungen["Regelanhang: Vorteilsnamen ersetzen"].wert
        isLinkedTo = {}
        for vorteil in Wolke.Char.vorteile.values():
            if vorteil.linkKategorie == VorteilLinkKategorie.Vorteil and vorteil.typ in namenErsetzen:
                isLinkedTo[vorteil.linkElement] = True
        vorteile = [v.definition for v in Wolke.Char.vorteile.values() if v.cheatsheetAuflisten and not v.name in isLinkedTo]

        # Regeln
        regeln = []
        for r in self.db.regeln.values():
            if not Wolke.Char.voraussetzungenPrüfen(r):
                continue
            regeln.append(r)

        # Waffeneigenschaften
        waffeneigenschaften = []
        for waffe in Wolke.Char.waffen:
            for el in waffe.eigenschaften:
                try:
                    we = Hilfsmethoden.GetWaffeneigenschaft(el, self.db)
                    if not we in waffeneigenschaften:
                        waffeneigenschaften.append(we)
                except WaffeneigenschaftException:
                    pass

        # Talente
        talente = [t.definition for t in Wolke.Char.talente.values() if t.cheatsheetAuflisten]

        # Karten
        karten = [k for k in self.db.karten.values() if Wolke.Char.voraussetzungenPrüfen(k)]

        # Lets go
        return self.generate(deaktivierteKategorien, vorteile, regeln, waffeneigenschaften, talente, karten)

    def generate(self, deaktivierteKategorien, vorteile, regeln, waffeneigenschaften, talente, karten):
        # Vorteile
        vorteilTypen = self.db.einstellungen["Vorteile: Typen"].wert
        vorteileGruppiert = []
        for i in range(len(vorteilTypen)):
            vorteileGruppiert.append([v for v in vorteile if v.typ == i])

        # Regeln
        regelTypen = self.db.einstellungen["Regeln: Typen"].wert
        regelnGruppiert = []
        for i in range(len(regelTypen)):
            regelnGruppiert.append([r for r in regeln if r.typ == i])

        # Talente
        spezialTalentTypen = self.db.einstellungen["Talente: Spezialtalent Typen"].wert
        talenteByTyp = []
        for typ in range(len(spezialTalentTypen)):
            talenteByTyp.append([t for t in talente if t.spezialTyp == typ])

        # Benutzerdefiniert
        benutzerdefiniert = [k for k in karten if k.typ == KartenTyp.Benutzerdefiniert and k.subtyp]
        benutzerdefiniertByTyp = {}
        for k in benutzerdefiniert:
            if k.subtyp not in benutzerdefiniertByTyp:
                benutzerdefiniertByTyp[k.subtyp] = []
            benutzerdefiniertByTyp[k.subtyp].append(k)

        # Override Karten
        overrideKarten = {}
        for k in karten:
            originalElement = k.getOriginalElement(self.db)
            if originalElement is not None:
                overrideKarten[originalElement] = k

        # Lets go
        decks = {}
        if "Manöverkarten_PrologAusgeben" not in Wolke.Settings or Wolke.Settings["Manöverkarten_PrologAusgeben"]:
            prolog = []
            prolog.append(self.generatePrologKarte())
            prolog.append(self.generateDruckanleitungKarte())
            decks["Prolog"] = prolog

        farbe = "#000000"
        currentDeck = []

        reihenfolge = copy.copy(self.db.einstellungen["Regelanhang: Reihenfolge"].wert)
        for b in benutzerdefiniertByTyp:
            reihenfolge.append("T:" + b) #generate deck card
            reihenfolge.append("B:" + b)

        for r in reihenfolge:
            if r[0] == "T" and len(r) > 2:
                titel = r[2:]
                decks[titel] = []
                currentDeck = decks[titel]
                deckKarte = KartenUtility.getDeckKarte(self.db, titel)
                if deckKarte is None:
                    deckKarte = Karte()
                    deckKarte.typ = KartenTyp.Deck
                    deckKarte.name = titel
                    deckKarte.text = f"Hinweis: Erstelle eine Karte vom Typ Deck mit dem Namen \"{titel}\", um diese Karte und die Deckfarbe anzupassen."
                farbe = deckKarte.farbe
                karte = self.generateZusatzKarte(deckKarte, deckKarte.farbe)
                decks[titel].append(karte)
                continue
            if r in deaktivierteKategorien:
                continue
            if r[0] == "V" and len(r) > 2 and r[2:].isnumeric():
                typ = int(r[2:])
                if typ >= len(vorteileGruppiert):
                    continue
                for el in vorteileGruppiert[typ]:
                    karte = self.generateKarte(el, farbe, overrideKarten[el] if el in overrideKarten else None)
                    if karte is not None:
                        currentDeck.append(karte)
                currentDeck.extend([self.generateZusatzKarte(k, farbe) for k in karten if k.typ == KartenTyp.Vorteil and k.isNew(self.db) and k.subtyp == typ])
            elif r[0] == "R" and len(r) > 2 and r[2:].isnumeric():
                typ = int(r[2:])
                if typ >= len(regelnGruppiert):
                    continue
                for el in regelnGruppiert[typ]:
                    karte = self.generateKarte(el, farbe, overrideKarten[el] if el in overrideKarten else None)
                    if karte is not None:
                        currentDeck.append(karte)
                currentDeck.extend([self.generateZusatzKarte(k, farbe) for k in karten if k.typ == KartenTyp.Regel and k.isNew(self.db) and k.subtyp == typ])
            elif r[0] == "W":
                for el in waffeneigenschaften:
                    karte = self.generateKarte(el, farbe, overrideKarten[el] if el in overrideKarten else None)
                    if karte is not None:
                        currentDeck.append(karte)
                currentDeck.extend([self.generateZusatzKarte(k, farbe) for k in karten if k.typ == KartenTyp.Waffeneigenschaft and k.isNew(self.db)])
            elif r[0] == "S" and len(r) > 2 and r[2:].isnumeric():
                typ = int(r[2:])
                if typ >= len(spezialTalentTypen):
                    continue
                for el in talenteByTyp[typ]:
                    karte = self.generateKarte(el, farbe, overrideKarten[el] if el in overrideKarten else None)
                    if karte is not None:
                        currentDeck.append(karte)
                currentDeck.extend([self.generateZusatzKarte(k, farbe) for k in karten if k.typ == KartenTyp.Talent and k.isNew(self.db) and k.subtyp == typ])
            elif r[0] == "B" and len(r) > 2:
                typ = r[2:]
                if not typ in benutzerdefiniertByTyp:
                    continue
                for el in benutzerdefiniertByTyp[typ]:            
                    karte = self.generateZusatzKarte(el, farbe)
                    if karte is not None:
                        currentDeck.append(karte)
            EventBus.doAction("karten_anfuegen", { "reihenfolge" : r, "appendCallback" : lambda karte: currentDeck.append(karte) })

        for deck in decks.values():
            deck[1:] = sorted(deck[1:], key=lambda k: (k.fusszeile, k.name))

        return decks

    ###########################
    # I/O
    ###########################

    def generateHtml(self, karte, forceHintergrund = False):
        typName = KartenTyp.TypNamen[karte.typ]
        if typName in self.templates:
            htmlPath = self.templates[typName][0]
            html = self.templates[typName][1]
        else:
            htmlPath = self.templates["Karte"][0]
            html = self.templates["Karte"][1]

        footerDict = self.db.einstellungen["Manöverkarten Plugin: Automatische Fußzeile ändern"].wert
        footer = karte.fusszeile
        if footer in footerDict:
            footer = footerDict[footer]

        text = Hilfsmethoden.fixHtml(karte.text, False)
        html = html.replace("{card_title}", karte.titel)
        html = html.replace("{card_title_color}", karte.farbe)
        html = html.replace("{card_subtitle}", karte.subtitel)
        html = html.replace("{card_footer}", footer)
        html = html.replace("{card_content}", text)
        html = html.replace("{sephrasto_dir}", "file:///" + os.getcwd().replace('\\', '/'))
        for key,value in karte.customData.items():
            html = html.replace("{" + key + "}", value)

        if forceHintergrund or Wolke.Settings["Manöverkarten_Hintergrundbild"]:
            html = html.replace("{card_backgroundimage}", "url(../Hintergrund.jpg)")
        else:
            html = html.replace("{card_backgroundimage}", "none")

        return html, htmlPath

    def __writeTempPDF(self, webEngineView, karte):
        html, htmlPath = self.generateHtml(karte)
            
        pl = QtGui.QPageLayout()
        pl.setPageSize(QtGui.QPageSize(QtCore.QSizeF(63, 88), QtGui.QPageSize.Millimeter, "", QtGui.QPageSize.ExactMatch))
        pl.setOrientation(QtGui.QPageLayout.Portrait)
        pl.setTopMargin(0)
        pl.setRightMargin(0)
        pl.setBottomMargin(0)
        pl.setLeftMargin(0)
        pfad = PdfSerializer.convertHtmlToPdf(html, htmlPath, pl, Wolke.Settings["Manöverkarten_ExportVerzögerungMs"], karte.farbe, None, webEngineView)
        return [pfad, karte.titel]

    def writeKarten(self, spath, karten, writeEinzeln, nameFormat, progressDlg):
        if len(karten) == 0:
            return

        bookmarks = []
        webEngineView = WebEngineViewPlus()
        kartenPdfs = []
        count = 1
        lastFooter = ""
        lastDeck = ""
        for karte in karten:
            if karte.typ == KartenTyp.Deck:
                lastDeck = karte.titel
                progressDlg.setLabelText("Exportiere " + karte.titel + "-Deck...")
                bookmarks.append(PdfSerializer.PdfBookmark(karte.titel, count, 1))
                lastFooter = ""
            else:  
                if karte.fusszeile and karte.fusszeile != lastFooter and karte.fusszeile != lastDeck:
                    lastFooter = karte.fusszeile
                    bookmarks.append(PdfSerializer.PdfBookmark(karte.fusszeile.replace("$original$", "Allgemein"), count, 2))
                bookmarks.append(PdfSerializer.PdfBookmark(karte.titel, count, 3 if lastFooter else 2))
            
            kartenPdfs.append(self.__writeTempPDF(webEngineView, karte))   
            count += 1

            progressDlg.setValue(progressDlg.value()+1)
            if progressDlg.shouldCancel():
                for pdf in kartenPdfs: os.remove(pdf[0])
                return

        if writeEinzeln:
            progressDlg.setLabelText("Optimiere Dateigröße...")
            deckName = os.path.splitext(os.path.basename(spath))[0]
            for karte in kartenPdfs:
                titel = karte[1].replace(" / ", " oder ").replace("/", " oder ")
                chop = [" (passiv)", " (Passiv)", " (einfach)", " (voll)", " (Sinn)", " (Tier)", " [Fertigkeit oder Attribut]"]
                for suffix in chop:
                    if titel.endswith(suffix):
                        titel = titel[:-len(suffix)]
                titel = "".join(c for c in titel if c not in "\/:*?<>|+‘´`'!?[]{}(),").strip()
                kartenName = nameFormat.replace("{deckname}", deckName).replace("{titel}", titel)
                path = os.path.join(os.path.dirname(spath), f"{kartenName}.pdf")
                PdfSerializer.squeeze(karte[0], path)
                os.remove(karte[0])
        else:
            progressDlg.setLabelText("Füge Karten zu einer Datei zusammen...")
            karten = [k[0] for k in kartenPdfs]
            def chunks(lst, n):
                for i in range(0, len(lst), n):
                    yield lst[i:i + n]

            tmp = []
            for chunk in chunks(karten, 100):
                tmp.append(PdfSerializer.concat(chunk))
                if progressDlg.shouldCancel():
                    for pdf in kartenPdfs + tmp: os.remove(pdf)
                    return

            tmp2 = PdfSerializer.concat(tmp)
            progressDlg.setLabelText("Füge Lesezeichen hinzu...")
            PdfSerializer.addBookmarks(tmp2, bookmarks, spath)
            os.remove(tmp2)

            progressDlg.setLabelText("Optimiere Dateigröße...")
            PdfSerializer.squeeze(spath, spath)
            for pdf in karten + tmp:
                os.remove(pdf)
            if Wolke.Settings["Manöverkarten_PDF-Open"]:
                Hilfsmethoden.openFile(spath)

    def __convertHtmlToJpg(self, out_file, html, htmlBaseUrl, width, height, scale = 1, backgroundColor = QtCore.Qt.transparent, webView = None):
        if isinstance(htmlBaseUrl, str):
            htmlBaseUrl = QtCore.QUrl.fromLocalFile(QtCore.QFileInfo(htmlBaseUrl).absoluteFilePath())

        if webView is None:
            webView = WebEngineViewPlus()
        webView.setFixedSize(width*scale, height*scale)
        webView.setZoomFactor(scale)
        webView.page().setBackgroundColor(backgroundColor)
        webView.show()
        with PdfSerializer.waitForSignal(webView.htmlLoaded):
            webView.setHtml(html, htmlBaseUrl)

        if Wolke.Settings["Manöverkarten_ExportVerzögerungMs"] > 0:
            timer = QtCore.QTimer()
            with PdfSerializer.waitForSignal(timer.timeout):
                timer.start(Wolke.Settings["Manöverkarten_ExportVerzögerungMs"])

        pixmap = webView.grab()
        pixmap.save(out_file, "JPG", 90)

    def writeKartenBilder(self, spath, karten, nameFormat, progressDlg):
        if len(karten) == 0:
            return
        deckName = os.path.splitext(os.path.basename(spath))[0]
        webView = WebEngineViewPlus()

        for karte in karten:
            if karte.typ == KartenTyp.Deck:
                progressDlg.setLabelText("Exportiere " + karte.titel + "-Deck...")

            titel = karte.titel.replace(" / ", " oder ").replace("/", " oder ")
            chop = [" (passiv)", " (Passiv)", " (einfach)", " (voll)", " (Sinn)", " (Tier)", " [Fertigkeit oder Attribut]"]
            for suffix in chop:
                if titel.endswith(suffix):
                    titel = titel[:-len(suffix)]
            titel = "".join(c for c in titel if c not in "\/:*?<>|+‘´`'!?[]{}(),").strip()

            kartenName = nameFormat.replace("{deckname}", deckName).replace("{titel}", titel)
            path = os.path.join(os.path.dirname(spath), f"{kartenName}.jpg")
            html, htmlPath = self.generateHtml(karte)
            self.__convertHtmlToJpg(path, html, htmlPath, 238, 332, 3, karte.farbe)
            progressDlg.setValue(progressDlg.value()+1)
            if progressDlg.shouldCancel():
                return