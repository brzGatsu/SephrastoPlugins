from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from Wolke import Wolke
import tempfile
import os
import re
import math
from Hilfsmethoden import Hilfsmethoden, WaffeneigenschaftException
import Objekte
from CharakterPrintUtility import CharakterPrintUtility
from DatenbankEinstellung import DatenbankEinstellung
from Fertigkeiten import VorteilLinkKategorie, KampffertigkeitTyp
import lxml.etree as etree

class Plugin:
    def __init__(self):
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHook)
        self.db = None

    @staticmethod
    def getDescription():
        return "Exportiert via Datenbank-Editor Button die Datenbank in ein Text-Format."

    def createDatabaseButtons(self):
        self.exportDB = QtWidgets.QPushButton()
        self.exportDB.setObjectName("buttonMeinExport")
        self.exportDB.setText("Text Export")
        self.exportDB.setToolTip("Exportiert die Datenbank in ein Text-Format.")
        self.exportDB.clicked.connect(self.export)
        return [self.exportDB]

    def basisDatenbankGeladenHook(self, params):
        self.db = params["datenbank"]

    def getVorteile(self):
        vorteilTypen = self.db.einstellungen["Vorteile: Typen"].toTextList()
        vorteileGruppiert = {}
        for i in range(len(vorteilTypen)):
            vorteile = [v for v in self.db.vorteile.values() if v.typ == i]
            vorteile = sorted(vorteile, key = lambda v: v.name)
            vorteileGruppiert[vorteilTypen[i]] = vorteile
        return vorteileGruppiert

    def getRegeln(self):
        regelTypen = self.db.einstellungen["Regeln: Typen"].toTextList()
        regelnGruppiert = {}
        for i in range(len(regelTypen)):
            regeln = [m for m in self.db.regeln.values() if m.typ == i]
            regeln = sorted(regeln, key = lambda m: m.name)
            regelnGruppiert[regelTypen[i]] = regeln
        return regelnGruppiert

    def getFertigkeitenProfan(self):
        fertigkeitsTypenProfan = self.db.einstellungen["Fertigkeiten: Typen profan"].toTextList()
        fertigkeitenGruppiert = {}
        for i in range(len(fertigkeitsTypenProfan)):
            fertigkeiten = [f for f in self.db.fertigkeiten.values() if f.typ == i]
            fertigkeiten = sorted(fertigkeiten, key = lambda f: f.name)
            fertigkeitenGruppiert[fertigkeitsTypenProfan[i]] = fertigkeiten
        return fertigkeitenGruppiert

    def getFertigkeitenÜbernatürlich(self):
        fertigkeitsTypenUeber = self.db.einstellungen["Fertigkeiten: Typen übernatürlich"].toTextList()
        fertigkeitenGruppiert = {}
        for i in range(len(fertigkeitsTypenUeber)):
            fertigkeiten = [f for f in self.db.übernatürlicheFertigkeiten.values() if f.typ == i]
            fertigkeiten = sorted(fertigkeiten, key = lambda f: f.name)
            fertigkeitenGruppiert[fertigkeitsTypenUeber[i]] = fertigkeiten
        return fertigkeitenGruppiert

    def getWaffen(self):
        waffenGruppiert = {}
        for waffe in self.db.waffen.values():
            if not waffe.fertigkeit in waffenGruppiert:
                waffenGruppiert[waffe.fertigkeit] = []
            waffenGruppiert[waffe.fertigkeit].append(waffe)

        for f in waffenGruppiert:
            waffenGruppiert[f] = sorted(waffenGruppiert[f], key = lambda w: w.name)

        return waffenGruppiert

    def getWaffeneigenschaften(self):
        return sorted(self.db.waffeneigenschaften.values(), key = lambda w: w.name)

    def getTalenteProfan(self):
        return sorted([t for t in self.db.talente.values() if not t.isSpezialTalent()], key = lambda t : t.name)

    def getTalenteÜbernatürlich(self):
        talenteUeber = [t for t in self.db.talente.values() if t.isSpezialTalent()]

        def getTalentTyp(talent):
            if len(talent.fertigkeiten) == 0:
                return 0

            for f in talent.fertigkeiten:
                if self.db.übernatürlicheFertigkeiten[f].talenteGruppieren:
                    return self.db.übernatürlicheFertigkeiten[f].typ
            return self.db.übernatürlicheFertigkeiten[talent.fertigkeiten[0]].typ

        def sortTalente(talent):
            return (getTalentTyp(talent), talent.name)

        talenteUeber = sorted(talenteUeber, key = lambda talent: sortTalente(talent))
        liturgieTypen = [int(t) for t in self.db.einstellungen["Fertigkeiten: Liturgie-Typen"].toTextList()]
        anrufungTypen = [int(t) for t in self.db.einstellungen["Fertigkeiten: Anrufungs-Typen"].toTextList()]
        zauber = []
        liturgien = []
        anrufungen = []
        fertigkeitsTypenUeber = self.db.einstellungen["Fertigkeiten: Typen übernatürlich"].toTextList()
        for t in fertigkeitsTypenUeber:
            zauber.append([])
            liturgien.append([])
            anrufungen.append([])

        for tal in talenteUeber:
            typ = getTalentTyp(tal)
            if typ >= len(fertigkeitsTypenUeber):
                continue
            if typ in liturgieTypen:
                liturgien[typ].append(tal)
            elif typ in anrufungTypen:
                anrufungen[typ].append(tal)
            else:
                zauber[typ].append(tal)

        return (zauber, liturgien, anrufungen)

    def voraussetzungenToString(self, voraussetzungen):
        voraussetzungen = [v.strip() for v in Hilfsmethoden.VorArray2Str(voraussetzungen).split(",")]
        voraussetzungen = [v for v in voraussetzungen if not v.startswith("Kein Vorteil Tradition")]
        voraussetzungen = [v + " und 2 weitere Attribute auf insgesamt 16" if "MeisterAttribut" in v else v for v in voraussetzungen]
        voraussetzungen = ", ".join(voraussetzungen)
        voraussetzungen = voraussetzungen.replace(" ODER ", " oder ")
        voraussetzungen = voraussetzungen.replace("'", "") # remove apostrophes from "Fertigkeit" and "Übernatürliche-Fertigkeit"
        voraussetzungen = voraussetzungen.replace("Fertigkeit ", "")
        voraussetzungen = voraussetzungen.replace("Übernatürliche-Fertigkeit ", "")
        voraussetzungen = voraussetzungen.replace("MeisterAttribut ", "")
        voraussetzungen = voraussetzungen.replace("Attribut ", "")
        voraussetzungen = voraussetzungen.replace("Vorteil ", "")
        voraussetzungen = voraussetzungen.replace("Kein ", "kein ")
        if not voraussetzungen:
            voraussetzungen = "keine"
        return voraussetzungen

    def shortenText(self, text):
        index = text.find('\nSephrasto')
        if index != -1:
            text = text[:index]
        index = text.find(' Sephrasto:')
        if index != -1:
            text = text[:index]
        return text

    def export(self):
        if self.db is None:
            return

        content = []
        content.append("VORTEILE\n")
        for vTyp, vorteile in self.getVorteile().items():
            content.append(f"==={vTyp} ===\n")
            for v in vorteile:
                content.append(v.name)
                content.append(self.shortenText(v.text))
                if (len(v.voraussetzungen) > 0):
                    content.append(f"Voraussetzungen: {self.voraussetzungenToString(v.voraussetzungen)}; {v.kosten} EP")
                else:
                    content.append(f"Voraussetzungen: {v.kosten} EP")
                content.append(f"Nachkauf: {v.nachkauf}")
                content.append("")

        content.append("\nPROFANE FERTIGKEITEN\n")
        for fTyp, fertigkeiten in self.getFertigkeitenProfan().items():
            content.append(f"=== {fTyp} ===\n")
            for f in fertigkeiten:
                sf = str(f.steigerungsfaktor)
                if f.kampffertigkeit == KampffertigkeitTyp.Nahkampf:
                    sf = "4/" + str(sf)
                content.append(f"{f.name} ({f.attribute[0]}/{f.attribute[1]}/{f.attribute[2]}, {sf})")
                content.append(self.shortenText(f.text))
                if len(f.voraussetzungen) > 0:
                    content.append(f"Voraussetzungen: {self.voraussetzungenToString(f.voraussetzungen)}")
                content.append("")

        content.append("\nPROFANE TALENTE\n")
        for t in self.getTalenteProfan():
            content.append(t.name)
            if t.verbilligt == 1:
                content[-1] += " (verbilligt)"
            content.append(self.shortenText(t.text))
            content.append("")

        content.append("\nÜBERNATÜRLICHE FERTIGKEITEN\n")
        for fTyp, fertigkeiten in self.getFertigkeitenÜbernatürlich().items():
            content.append(f"=== {fTyp} ===\n")
            for f in fertigkeiten:
                content.append(f"{f.name} ({f.attribute[0]}/{f.attribute[1]}/{f.attribute[2]}, {f.steigerungsfaktor})")
                content.append(self.shortenText(f.text))
                if len(f.voraussetzungen) > 0:
                    content.append(f"Voraussetzungen: {self.voraussetzungenToString(f.voraussetzungen)}")
                content.append("")

        (zauberKategorien, liturgienKategorien, anrufungenKategorien) = self.getTalenteÜbernatürlich()
        content.append("\nZAUBER\n")
        for zauber in zauberKategorien:
            for z in zauber:
                content.append(z.name)
                content.append(self.shortenText(z.text))
                # also available: t.fertigkeiten (array of strings), t.voraussetzungen (array, see voraussetzungenToString), t.kosten (int)
                content.append("")

        content.append("\nLITURGIEN\n")
        for liturgien in liturgienKategorien:
            for l in liturgien:
                content.append(l.name)
                content.append(self.shortenText(l.text))
                # also available: t.fertigkeiten (array of strings), t.voraussetzungen (array, see voraussetzungenToString), t.kosten (int)
                content.append("")

        content.append("\nANRUFUNGEN\n")
        for anrufungen in anrufungenKategorien:
            for a in anrufungen:
                content.append(a.name)
                content.append(self.shortenText(a.text))
                # also available: t.fertigkeiten (array of strings), t.voraussetzungen (array, see voraussetzungenToString), t.kosten (int)
                content.append("")

        content.append("\nREGELN\n")
        for rTyp, regeln in self.getRegeln().items():
            content.append(f"=== {rTyp} ===\n")
            for r in regeln:
                content.append(r.name)
                if r.probe:
                    content[-1] += f" ({r.probe})"
                content.append(f"Wirkung: {self.shortenText(r.text)}")
                if len(r.voraussetzungen) > 0:
                    content.append(f"Voraussetzungen: {self.voraussetzungenToString(r.voraussetzungen)}")
                content.append("")

        content.append("\nWAFFEN\n")
        for fert, waffen in self.getWaffen().items():
            content.append(f"=== {fert} ===\n")
            for w in waffen:
                tpPlus = f"+{w.plus}" if w.plus >= 0 else f"{w.plus}"

                if type(w) == Objekte.Fernkampfwaffe:
                    content.append(f"{w.name} | TP {w.würfel}W{w.würfelSeiten}{tpPlus} | RW {w.rw} | WM {w.wm} | LZ {w.lz} | Härte {w.härte} | Eigenschaften: " + (", ".join(w.eigenschaften) if len(w.eigenschaften) > 0 else "-"))
                else:
                    content.append(f"{w.name} | TP {w.würfel}W{w.würfelSeiten}{tpPlus} | RW {w.rw} | WM {w.wm} | Härte {w.härte} | Eigenschaften: " + (", ".join(w.eigenschaften) if len(w.eigenschaften) > 0 else "-"))
                # also available: w.kampfstile (array of strings)
                content.append("")

        content.append("\nWAFFENEIGENSCHAFTEN\n")
        for we in self.getWaffeneigenschaften():
            content.append(we.name)
            if we.text:
                content.append(self.shortenText(we.text))
            content.append("")

        startDir = ""
        spath, _ = QtWidgets.QFileDialog.getSaveFileName(None,"Datenbank speichern...", startDir, "Text-Datei (*.txt)")
        if spath == "":
            return
        if ".txt" not in spath:
            spath = spath + ".txt"

        with open(spath, 'w', encoding="utf-8") as f:
            f.write("\n".join(content))