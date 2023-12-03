from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from Wolke import Wolke
import tempfile
import os
import re
import math
from Hilfsmethoden import Hilfsmethoden, WaffeneigenschaftException
from CharakterPrintUtility import CharakterPrintUtility
from Core.Fertigkeit import KampffertigkeitTyp

class Plugin:
    def __init__(self):
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHook)
        EventBus.addAction("dbe_menuitems_erstellen", self.menusErstellen)
        self.db = None

    @staticmethod
    def getDescription():
        return "Exportiert via Datenbank-Editor Button die Datenbank in ein Text-Format."

    def menusErstellen(self, params):
        addMenuItemCB = params["addMenuItemCB"]
        self.exportDB = QtGui.QAction("Text-Export")
        self.exportDB.triggered.connect(self.export)
        addMenuItemCB("Export", self.exportDB)

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
        vorteilTypen = self.db.einstellungen["Vorteile: Typen"].wert
        vorteileGruppiert = {}
        for i in range(len(vorteilTypen)):
            vorteile = [v for v in self.db.vorteile.values() if v.typ == i]
            vorteile = sorted(vorteile, key = lambda v: v.name)
            vorteileGruppiert[vorteilTypen[i]] = vorteile
        return vorteileGruppiert

    def getRegeln(self):
        regelTypen = self.db.einstellungen["Regeln: Typen"].wert
        regelnGruppiert = {}
        for i in range(len(regelTypen)):
            regeln = [m for m in self.db.regeln.values() if m.typ == i]
            regeln = sorted(regeln, key = lambda m: m.name)
            regelnGruppiert[regelTypen[i]] = regeln
        return regelnGruppiert

    def getFertigkeitenProfan(self):
        fertigkeitsTypenProfan = self.db.einstellungen["Fertigkeiten: Typen profan"].wert
        fertigkeitenGruppiert = {}
        for i in range(len(fertigkeitsTypenProfan)):
            fertigkeiten = [f for f in self.db.fertigkeiten.values() if f.typ == i]
            fertigkeiten = sorted(fertigkeiten, key = lambda f: f.name)
            fertigkeitenGruppiert[fertigkeitsTypenProfan[i]] = fertigkeiten
        return fertigkeitenGruppiert

    def getFertigkeitenÜbernatürlich(self):
        fertigkeitsTypenUeber = self.db.einstellungen["Fertigkeiten: Typen übernatürlich"].wert
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
        return sorted([t for t in self.db.talente.values() if not t.spezialTalent], key = lambda t : t.name)

    def getTalenteÜbernatürlich(self):
        talenteUeber = [t for t in self.db.talente.values() if t.spezialTalent]

        def sortTalente(tal):
            hauptFert = tal.hauptfertigkeit
            if hauptFert is None:
                return (0, "", tal.name)
            elif hauptFert.talenteGruppieren:
               return (hauptFert.typ, hauptFert.name, tal.name)
            else:
               return (hauptFert.typ, "", tal.name)

        talenteByTyp = []
        for typ in range(len(self.db.einstellungen["Talente: Spezialtalent Typen"].wert)):
            talenteByTyp.append([t for t in talenteUeber if t.spezialTyp == typ])
            talenteByTyp[-1].sort(key = sortTalente)

        return talenteByTyp

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

        content.append("ATTRIBUTE\n")
        attribute = [a for a in sorted(self.db.attribute.values(), key=lambda value: value.sortorder)]
        for attribut in attribute:
            # see Core.Attribut.AttributDefinition for all properties
            content.append(f"{attribut.anzeigename} ({attribut.name})")
            if attribut.text:
                content.append(attribut.text)
            content.append("")

        content.append("\nABGELEITETE WERTE\n")
        abgeleiteteWerte = [a for a in sorted(self.db.abgeleiteteWerte.values(), key=lambda value: value.sortorder)]
        for ab in abgeleiteteWerte:
            # see Core.AbgeleiteterWert.AbgeleiteterWertDefinition for all properties
            content.append(f"{ab.anzeigename} ({ab.name})")
            if ab.text:
                content.append(ab.text)
            if ab.formel:
                content.append("Formel: " + ab.formel)
            content.append("")

        content.append("\nENERGIEN\n")
        energien = [e for e in sorted(self.db.energien.values(), key=lambda value: value.sortorder)]
        for en in energien:
            # see Core.Energie.EnergieDefinition for all properties
            content.append(f"{en.anzeigename} ({en.name})")
            if en.text:
                content.append(en.text)
            content.append("Voraussetzungen: " + en.voraussetzungen.anzeigetext(self.db))
            content.append(f"")

        content.append("\nVORTEILE\n")
        for vTyp, vorteile in self.getVorteile().items():
            content.append(f"==={vTyp} ===\n")
            for v in vorteile:
                # see Core.Vorteil.VorteilDefinition for all properties
                content.append(v.name)
                content.append(self.shortenText(v.text))
                if v.voraussetzungen.text:
                    content.append(f"Voraussetzungen: {v.voraussetzungen.anzeigetext(self.db)}; {v.kosten} EP")
                else:
                    content.append(f"Voraussetzungen: {v.kosten} EP")
                content.append(f"Nachkauf: {v.nachkauf}")
                content.append("")

        content.append("\nPROFANE FERTIGKEITEN\n")
        for fTyp, fertigkeiten in self.getFertigkeitenProfan().items():
            content.append(f"=== {fTyp} ===\n")
            for f in fertigkeiten:
                # see Core.Fertigkeit.FertigkeitDefinition for all properties
                sf = str(f.steigerungsfaktor)
                if f.kampffertigkeit == KampffertigkeitTyp.Nahkampf:
                    sf = "4/" + str(sf)
                content.append(f"{f.name} ({f.attribute[0]}/{f.attribute[1]}/{f.attribute[2]}, {sf})")
                content.append(self.shortenText(f.text))
                if f.voraussetzungen.text:
                    content.append(f"Voraussetzungen: {f.voraussetzungen.anzeigetext(self.db)}")
                content.append("")

        content.append("\nPROFANE TALENTE\n")
        for t in self.getTalenteProfan():
            # see Core.Talent.TalentDefinition for all properties
            content.append(t.name)
            if t.verbilligt == 1:
                content[-1] += " (verbilligt)"
            if t.text:
                content.append(self.shortenText(t.text))
            content.append("")

        content.append("\nÜBERNATÜRLICHE FERTIGKEITEN\n")
        for fTyp, fertigkeiten in self.getFertigkeitenÜbernatürlich().items():
            content.append(f"=== {fTyp} ===\n")
            for f in fertigkeiten:
                # see Core.Fertigkeit.FertigkeitDefinition for all properties
                content.append(f"{f.name} ({f.attribute[0]}/{f.attribute[1]}/{f.attribute[2]}, {f.steigerungsfaktor})")
                content.append(self.shortenText(f.text))
                if f.voraussetzungen.text:
                    content.append(f"Voraussetzungen: {f.voraussetzungen.anzeigetext(self.db)}")
                content.append("")

        talenteByTyp = self.getTalenteÜbernatürlich()
        spezialTalentTypen = list(self.db.einstellungen["Talente: Spezialtalent Typen"].wert.values())
        for i in range(len(talenteByTyp)):
            content.append("\n" + spezialTalentTypen[i].upper() + "\n")
            for t in talenteByTyp[i]:
                # see Core.Talent.TalentDefinition for all properties
                content.append(t.name)
                content.append(self.shortenText(t.text))      
                content.append("")

        content.append("\nREGELN\n")
        for rTyp, regeln in self.getRegeln().items():
            content.append(f"=== {rTyp} ===\n")
            for r in regeln:
                # see Core.Regel.Regel for all properties
                content.append(r.name)
                if r.probe:
                    content[-1] += f" ({r.probe})"
                content.append(f"Wirkung: {self.shortenText(r.text)}")
                if r.voraussetzungen.text:
                    content.append(f"Voraussetzungen: {r.voraussetzungen.anzeigetext(self.db)}")
                content.append("")

        content.append("\nWAFFEN\n")
        for fert, waffen in self.getWaffen().items():
            content.append(f"=== {fert} ===\n")
            for w in waffen:
                # see Core.Waffe.WaffeDefinition for all properties
                tpPlus = f"+{w.plus}" if w.plus >= 0 else f"{w.plus}"

                if w.fernkampf:
                    content.append(f"{w.name} | TP {w.würfel}W{w.würfelSeiten}{tpPlus} | RW {w.rw} | WM {w.wm} | LZ {w.lz} | Härte {w.härte} | Eigenschaften: " + (", ".join(w.eigenschaften) if len(w.eigenschaften) > 0 else "-"))
                else:
                    content.append(f"{w.name} | TP {w.würfel}W{w.würfelSeiten}{tpPlus} | RW {w.rw} | WM {w.wm} | Härte {w.härte} | Eigenschaften: " + (", ".join(w.eigenschaften) if len(w.eigenschaften) > 0 else "-"))
                content.append("")

        content.append("\nWAFFENEIGENSCHAFTEN\n")
        for we in self.getWaffeneigenschaften():
            # see Core.Waffeneigenschaft.Waffeneigenschaft for all properties
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