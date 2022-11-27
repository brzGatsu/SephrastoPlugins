from EventBus import EventBus
from Wolke import Wolke
import Definitionen
import os
from CharakterPrintUtility import CharakterPrintUtility
import Version

# This utility function didnt exist before 3.2.2 in Version.py
def isClientSameOrHigher(major, minor, build):
    if Version._sephrasto_version_major < major:
        return False

    if Version._sephrasto_version_major > major:
        return True

    if Version._sephrasto_version_minor < minor:
        return False

    if Version._sephrasto_version_minor > minor:
        return True

    return Version._sephrasto_version_build >= build

class Plugin:
    def __init__(self):
        if isClientSameOrHigher(3, 2, 2):
            EventBus.addFilter("charakter_xml_schreiben", self.charakterSchreibenHook)
        else:
            EventBus.addAction("pdf_geschrieben", self.pdfGeschriebenHook)

    @staticmethod
    def getDescription():
        return "Dieses Plugin speichert die Charakterwerte beim Speichern zusätzlich als Textdatei ab. Die Werte können dadurch leicht kopiert und z.B. in Trello-Karten eingefügt werden."

    def charakterSchreibenHook(self, node, params):
        char = params["charakter"]
        content = []

        content.append("=== Beschreibung ===")
        content.append("Name: " + char.name)
        content.append("Spezies: " + char.rasse)
        content.append("Kurzbeschreibung: " + char.kurzbeschreibung)
        content.append("Status: " + Definitionen.Statusse[char.status])
        content.append("Heimat: " + char.heimat)

        content.append("\nEigenheiten:")
        for eigenheit in char.eigenheiten:
            if eigenheit:
                content.append(eigenheit)

        content.append("\n=== Attribute === ")
        for attribut in Definitionen.Attribute:
            content.append(attribut + " " + str(char.attribute[attribut].wert) + "/" + str(char.attribute[attribut].probenwert))

        content.append("\nAbgeleitete Werte und Energien:")
        content.append("WS " + str(char.ws))
        content.append("MR " + str(char.mr))
        content.append("GS " + str(char.gs))
        content.append("SB " + str(char.schadensbonus))
        content.append("INI " + str(char.ini))
        if "Zauberer I" in char.vorteile:
            content.append("AsP " + str(char.asp.wert + char.aspBasis + char.aspMod))
        if "Geweiht I" in char.vorteile:
            content.append("KaP " + str(char.kap.wert + char.kapBasis + char.kapMod))
        if "Paktierer I" in char.vorteile:
            content.append("GuP " + str(char.kap.wert + char.kapBasis + char.kapMod))
        content.append("Max SchiP " + str(char.schipsMax))

        content.append("\n=== Allgemeine und Profane Vorteile === ")
        vorteile = CharakterPrintUtility.getVorteile(char)
        (vorteileAllgemein, vorteileKampf, vorteileUeber) = CharakterPrintUtility.groupVorteile(char, vorteile, link = True)
        for v in vorteileAllgemein:
            content.append(v)

        content.append("\n=== Profane Fertigkeiten === ")

        fertigkeitsTypen = Wolke.DB.einstellungen["Fertigkeiten: Typen profan"].toTextList()
        lastType = -1
        for f in CharakterPrintUtility.getFertigkeiten(char):
            fert = char.fertigkeiten[f]
            if lastType != fert.printclass:
                content.append("\n" + fertigkeitsTypen[fert.printclass] + ":")
                lastType = fert.printclass

            talente = CharakterPrintUtility.getTalente(char, fert)
            talentStr = " "
            if len(talente) > 0:
                talentStr = " (" + ", ".join([t.anzeigeName for t in talente]) + ") "
            content.append(fert.name + talentStr + str(fert.probenwert) + "/" + str(fert.probenwertTalent))

        content.append("\nFreie Fertigkeiten:")
        for fert in CharakterPrintUtility.getFreieFertigkeiten(char):
            if fert:
                content.append(fert)

        content.append("\n=== Kampf === ")
        content.append("WS " + str(char.ws))
        content.append("WS* " + str(char.wsStern))
        content.append("GS* " + str(char.gsStern))
        content.append("Dh* " + str(char.dhStern))
        content.append("INI " + str(char.ini))

        content.append("\nVorteile:")
        for v in vorteileKampf:
            content.append(v)

        content.append("\nRüstungen:")
        for rüstung in char.rüstung:
            if not rüstung.name:
                continue
            content.append(rüstung.name + " RS " + str(int(rüstung.getRSGesamt())) + " BE " + str(rüstung.be))

        content.append("\nWaffen:")
        count = 0
        for waffe in char.waffen:
            if not waffe.name:
                continue

            werte = char.waffenwerte[count]
            keinSchaden = waffe.W6 == 0 and waffe.plus == 0
            sg = ""
            if waffe.plus >= 0:
                sg = "+"
            content.append(waffe.anzeigename + " AT " + str(werte.AT) + " VT " + str(werte.VT) + " " + ("-" if keinSchaden else str(werte.TPW6) + "W6" + sg + str(werte.TPPlus)))
            if len(waffe.eigenschaften) > 0:
                content.append(", ".join(waffe.eigenschaften))
            content.append("")
            count += 1
        content.pop()

        isZauberer = char.aspBasis + char.aspMod > 0
        isGeweiht = char.kapBasis + char.kapMod > 0
        
        if isZauberer or isGeweiht:
            content.append("\n=== Übernatürliche Fertigkeiten und Talente ===")

            content.append("\nVorteile:")
            for v in vorteileUeber:
                content.append(v)

            content.append("\nÜbernatürliche Fertigkeiten:")
            for f in CharakterPrintUtility.getÜberFertigkeiten(char):
                fert = char.übernatürlicheFertigkeiten[f]
                content.append(fert.name + " " + str(fert.probenwertTalent))

            content.append("\nÜbernatürliche Talente:")
            for talent in CharakterPrintUtility.getÜberTalente(char):
                content.append(talent.anzeigeName + " " + str(talent.pw))

        path = os.path.splitext(params["filepath"])[0] + "_text.txt"
        with open(path, 'w', encoding="utf-8") as f:
            f.write("\n".join(content))
        return node


