from EventBus import EventBus
from Wolke import Wolke
import os
from CharakterPrintUtility import CharakterPrintUtility
import Version

class Plugin:
    def __init__(self):
        EventBus.addFilter("charakter_xml_schreiben", self.charakterSchreibenHook)

    @staticmethod
    def getDescription():
        return "Dieses Plugin speichert die Charakterwerte beim Speichern zusätzlich als Textdatei ab. Die Werte können dadurch leicht kopiert und z.B. in Trello-Karten eingefügt werden."

    def charakterSchreibenHook(self, node, params):
        char = params["charakter"]
        content = []

        content.append("=== Beschreibung ===")
        content.append("Name: " + char.name)
        content.append("Spezies: " + char.spezies)
        content.append("Kurzbeschreibung: " + char.kurzbeschreibung)
        content.append("Status: " + Wolke.DB.einstellungen["Statusse"].wert[char.status])
        content.append("Heimat: " + char.heimat)

        content.append("\nEigenheiten:")
        for eigenheit in char.eigenheiten:
            if eigenheit:
                content.append(eigenheit)

        content.append("\n=== Attribute === ")
        attribute = [a for a in sorted(char.attribute.values(), key=lambda value: value.sortorder)]
        for attribut in attribute:
            content.append(attribut.name + " " + str(attribut.wert) + "/" + str(attribut.probenwert))

        content.append("\nAbgeleitete Werte und Energien:")
        abgeleiteteWerte = [a for a in sorted(char.abgeleiteteWerte.values(), key=lambda value: value.sortorder)]
        for ab in abgeleiteteWerte:
            if not ab.anzeigen:
                continue
            content.append(ab.name + " " + str(ab.wert))

        energien = [e for e in sorted(char.energien.values(), key=lambda value: value.sortorder)]
        for en in energien:
            content.append(en.name + " " + str(en.gesamtwert))

        content.append("\n=== Allgemeine und Profane Vorteile === ")
        vorteile = CharakterPrintUtility.getVorteile(char)
        (vorteileAllgemein, vorteileKampf, vorteileUeber) = CharakterPrintUtility.groupVorteile(char, vorteile, link = True)
        for v in vorteileAllgemein:
            content.append(v)

        content.append("\n=== Profane Fertigkeiten === ")

        fertigkeitsTypen = Wolke.DB.einstellungen["Fertigkeiten: Typen profan"].wert
        lastType = -1
        for f in CharakterPrintUtility.getFertigkeiten(char):
            fert = char.fertigkeiten[f]
            if lastType != fert.typ:
                content.append("\n" + fertigkeitsTypen[fert.typ] + ":")
                lastType = fert.typ

            talente = CharakterPrintUtility.getTalente(char, fert)
            talentStr = " "
            if len(talente) > 0:
                talentStr = " (" + ", ".join(talente) + ") "
            content.append(fert.name + talentStr + str(fert.probenwert) + "/" + str(fert.probenwertTalent))

        content.append("\nFreie Fertigkeiten:")
        for fert in CharakterPrintUtility.getFreieFertigkeiten(char):
            if fert:
                content.append(fert)

        content.append("\n=== Kampf === ")
        if "WS" in abgeleiteteWerte:
            content.append("WS " + str(abgeleiteteWerte["WS"].wert))
            content.append("WS* " + str(abgeleiteteWerte["WS"].finalwert))
        if "GS" in abgeleiteteWerte:
            content.append("GS* " + str(abgeleiteteWerte["GS"].finalwert))
        if "DH" in abgeleiteteWerte:
            content.append("DH* " + str(abgeleiteteWerte["DH"].finalwert))
        if "INI" in abgeleiteteWerte:
            content.append("INI " + str(abgeleiteteWerte["INI"].wert))

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
            keinSchaden = waffe.würfel == 0 and waffe.plus == 0
            sg = ""
            if waffe.plus >= 0:
                sg = "+"
            content.append(waffe.anzeigename)
            if waffe.fernkampf:
                content[-1] += " LZ " + str(waffe.lz)
            content[-1] += " AT " + str(werte.at)

            vtVerboten = Wolke.DB.einstellungen["Waffen: Talente VT verboten"].wert
            if waffe.talent in vtVerboten or waffe.name in vtVerboten:
                content[-1] += " VT -"
            else:
                content[-1] += " VT " + str(werte.vt)
            content[-1] += " " + ("-" if keinSchaden else str(werte.würfel) + "W" + str(waffe.würfelSeiten) + sg + str(werte.plus))
            if len(waffe.eigenschaften) > 0:
                content.append(", ".join(waffe.eigenschaften))
            content.append("")
            count += 1
        content.pop()

        überFerts = CharakterPrintUtility.getÜberFertigkeiten(char)
        überTalente = CharakterPrintUtility.getÜberTalente(char)
        anyÜberTalente = False
        for arr in überTalente:
            if len(arr) > 0:
                anyÜberTalente = True
                break
        if len(vorteileUeber) > 0 or len(überFerts) > 0 or anyÜberTalente:
            content.append("\n=== Übernatürliche Fertigkeiten und Talente ===")

            content.append("\nVorteile:")
            for v in vorteileUeber:
                content.append(v)

            content.append("\nÜbernatürliche Fertigkeiten:")
            for f in überFerts:
                fert = char.übernatürlicheFertigkeiten[f]
                content.append(fert.name + " " + str(fert.probenwertTalent))

            content.append("\nÜbernatürliche Talente:")
            for arr in überTalente:
                for talent in arr:
                    content.append(talent.anzeigename + " " + str(talent.probenwert))

        path = os.path.splitext(params["filepath"])[0] + "_text.txt"
        with open(path, 'w', encoding="utf-8") as f:
            f.write("\n".join(content))
        return node


