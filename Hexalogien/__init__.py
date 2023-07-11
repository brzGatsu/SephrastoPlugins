from EventBus import EventBus
from Wolke import Wolke
from Core.DatenbankEinstellung import DatenbankEinstellung

class Plugin:
    def __init__(self):
        EventBus.addFilter("talent_kosten", self.talentKostenHook)
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)

    hexalogien = [
        #Feuer, Luft, Erz, Eis, Wasser, Humus
        ["Feuerlauf", "", "", "Firnlauf", "Wellenlauf", "Wipfellauf"],
        ["Leib des Feuers", "Leib des Windes", "Leib des Erzes", "Leib des Eises", "Leib der Wogen", "Leib der Erde"],
        ["Ignifaxius Flammenstrahl", "Orcanofaxius", "Archofaxius", "Frigifaxius", "Aquafaxius", "Humofaxius"],
        ["Ignisphaero", "Orcanosphaero", "Archosphaero", "Frigisphaero", "Aquasphaero", "Humosphaero"],
        ["Wand aus Flammen", "Orkanwand", "Wand aus Erz", "Gletscherwand", "Wasserwand", "Wand aus Dornen"],
        ["Feuersturm", "Windhose", "Malmkreis", "Eiswirbel", "Mahlstrom", "Sumpfstrudel"],
        ["Ignimorpho Feuerform", "Aeromorpho Wirbelform", "Metamorpho Felsenform", "Metamorpho Gletscherform", "Aquamorpho Wasserform", "Metamorpho Eisenholz"],
        ["Weisheit der Flammen", "Weisheit der Wolken", "Weisheit der Steine", "Weisheit des Eises", "Weisheit des Teiches", "Weisheit der Bäume"],
        ["Pfeil des Feuers", "Pfeil der Luft", "Pfeil des Erzes", "Pfeil des Eises", "Pfeil des Wassers", "Pfeil des Humus"],
        ["Herbeirufung des Feuers", "Herbeirufung der Luft", "Herbeirufung des Erzes", "Herbeirufung des Eises", "Herbeirufung des Wassers", "Herbeirufung des Humus", "Macht des Feuers", "Macht der Luft", "Macht des Erzes", "Macht des Eises", "Macht des Wassers", "Macht des Humus"]
    ]

    @staticmethod
    def getDescription():
        return "Dieses Plugin halbiert die EP-Kosten von Talenten aus elementaren Hexalogien. Der volle EP-Preis muss nur für das teuerste erlernte Talent aus der Hexalogie bezahlt werden.\nBeinhaltet sind alle bestätigten Hexalogien gemäß https://de.wiki-aventurica.de/wiki/Hexalogie (nicht die vermuteten), zusätzlich noch die Herbeirufung und Macht des <Elements> Zauber."

    def changesCharacter(self):
        return self.db.einstellungen["Hexalogien Plugin: Aktivieren"].wert

    def basisDatenbankGeladenHandler(self, params):
        self.db = params["datenbank"]

        e = DatenbankEinstellung()
        e.name = "Hexalogien Plugin: Aktivieren"
        e.beschreibung = Plugin.getDescription()
        e.text = "True"
        e.typ = "Bool"
        self.db.loadElement(e)

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

        for hexalogie in Plugin.hexalogien:
            if talent in hexalogie:
                talHexalogie = hexalogie
                break

        if talHexalogie is None:
            return val

        mostExpensivePaid = talent
        for tal in talHexalogie:
            if tal in char.talente:
                if Wolke.DB.talente[tal].kosten >= Wolke.DB.talente[mostExpensivePaid].kosten:
                    mostExpensivePaid = tal

        if mostExpensivePaid != talent:
            return int(val / 2)
        return val