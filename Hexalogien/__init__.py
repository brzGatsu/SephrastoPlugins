from EventBus import EventBus
from Wolke import Wolke
from Core.DatenbankEinstellung import DatenbankEinstellung
import logging

class Plugin:
    def __init__(self):
        EventBus.addFilter("talent_kosten", self.talentKostenHook)
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)
        EventBus.addAction("datenbank_geladen", self.datenbankGeladenHandler)

    def changesCharacter(self):
        return self.db.einstellungen["Hexalogien Plugin: Aktivieren"].wert

    def basisDatenbankGeladenHandler(self, params):
        self.db = params["datenbank"]

        e = DatenbankEinstellung()
        e.name = "Hexalogien Plugin: Aktivieren"
        e.beschreibung = "Wenn du den Haken entfernst, kannst du das Plugin speziell für diese Hausregeln deaktivieren, ohne es löschen zu müssen."
        e.text = "True"
        e.typ = "Bool"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Hexalogien Plugin: Talente"
        e.beschreibung = "Jede Zeile wird als eigene kommaseparierte Liste behandelt. Wenn ein Charakter mehrere Talente einer Liste beherrscht, bezahlt er die vollen Kosten nur für das teuerste Talent - alle anderen kosten nur die Hälfte. Standardmäßig beinhaltet die Einstellung alle bestätigten Hexalogien gemäß https://de.wiki-aventurica.de/wiki/Hexalogie (nicht die vermuteten), zusätzlich noch die Herbeirufung und Macht des <Elements> Zauber."
        e.text = """Feuerlauf, Firnlauf, Wellenlauf, Wipfellauf
Leib des Feuers, Leib des Windes, Leib des Erzes, Leib des Eises, Leib der Wogen, Leib der Erde
Ignifaxius Flammenstrahl, Orcanofaxius, Archofaxius, Frigifaxius, Aquafaxius, Humofaxius
Ignisphaero, Orcanosphaero, Archosphaero, Frigisphaero, Aquasphaero, Humosphaero
Wand aus Flammen, Orkanwand, Wand aus Erz, Gletscherwand, Wasserwand, Wand aus Dornen
Feuersturm, Windhose, Malmkreis, Eiswirbel, Mahlstrom, Sumpfstrudel
Ignimorpho Feuerform, Aeromorpho Wirbelform, Metamorpho Felsenform, Metamorpho Gletscherform, Aquamorpho Wasserform, Metamorpho Eisenholz, Haselbusch und Ginsterkraut
Weisheit der Flammen, Weisheit der Wolken, Weisheit der Steine, Weisheit des Eises, Weisheit des Teiches, Weisheit der Bäume
Pfeil des Feuers, Pfeil der Luft, Pfeil des Erzes, Pfeil des Eises, Pfeil des Wassers, Pfeil des Humus
Herbeirufung des Feuers, Herbeirufung der Luft, Herbeirufung des Erzes, Herbeirufung des Eises, Herbeirufung des Wassers, Herbeirufung des Humus, Macht des Feuers, Macht der Luft, Macht des Erzes, Macht des Eises, Macht des Wassers, Macht des Humus"""
        e.typ = "TextList"
        e.separator = "\n"
        e.strip = True
        self.db.loadElement(e)

    def datenbankGeladenHandler(self, params):
        for hexalogie in self.db.einstellungen["Hexalogien Plugin: Talente"].wert:
            for tal in [t.strip() for t in hexalogie.split(",")]:
                if not tal in self.db.talente:
                    logging.debug("Hexalogien Plugin: Unbekanntes Talent in EInstellung 'Hexalogien Plugin: Talente': " + tal)

    def talentKostenHook(self, val, params):
        if not self.db.einstellungen["Hexalogien Plugin: Aktivieren"].wert:
            return val

        talent = params["talent"]
        char = params["charakter"]

        if not talent in Wolke.DB.talente:
            return val

        dbTalent = Wolke.DB.talente[talent]

        if not dbTalent.spezialTalent:
            return val

        talHexalogie = None

        for hexalogie in self.db.einstellungen["Hexalogien Plugin: Talente"].wert:
            if talent in hexalogie:
                talHexalogie = hexalogie
                break

        if talHexalogie is None:
            return val

        mostExpensivePaid = talent
        for tal in [t.strip() for t in talHexalogie.split(",")]:
            if tal in char.talente:
                if Wolke.DB.talente[tal].kosten >= Wolke.DB.talente[mostExpensivePaid].kosten:
                    mostExpensivePaid = tal

        if mostExpensivePaid != talent:
            return int(val / 2)
        return val