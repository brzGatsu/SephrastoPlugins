from Hilfsmethoden import Hilfsmethoden

#========== Settings ===========
# Trage hier den Namen einer Fertigkeit ein um Details für sie zu erhalten
debugFertigkeit = ""
# Setze diese EInstellung auf True, um die EP-Differenzen zu den unten festgelegten Schwellen mit auszugeben
showDeltaEP = False
# Talente die "(passiv)" im Namen haben werden für die Berechnung übersprungen
skipPassivTalente = True
# Traditionen mit Gesamt-Talent-EP unter dieser Grenze werden für die Berechnung übersprungen
skipTraditionBelowEP = 121
# Untere EP-Grenzwerte für Steigerungsfaktoren
sf2Threshold = 0
sf3Threshold = 360
sf4Threshold = 700
# Trage hier kommasepariert alle Traditionen ein, die keinen Vorteil mit 'Tradition I' im Namen haben
zusatzTraditionen = ["Magiedilettant"] 
# Trage hier Vorteile ein, die neben der Tradition für die Überprüfung der Voraussetzungen als gekauft gelten sollen.
gekaufteVorteile = ["Geweiht I", "Zauberer I", "Paktierer I"]
# Trage hier Funktionen für bestimmte Talente ein, um die Kosten für die Berechnung zu modifizieren
kostenModifikatoren = {
    # Beispiele:
    #"Elementarbann" : lambda f, t: t.kosten if f.name == "Antimagie" else t.kosten/6,
    #"Schutzkreis gegen Elementare" : lambda f, t: t.kosten if f.name == "Antimagie" else t.kosten/6,
}

#========== Implementation ===========
traditionen = [v.name for v in datenbank.vorteile.values() if v.name.startswith("Tradition") and v.name.endswith(" I")]
traditionen += zusatzTraditionen
spezialTalente = [t for t in datenbank.talente.values() if t.isSpezialTalent()]
if skipPassivTalente:
    spezialTalente = [t for t in spezialTalente if not t.name.endswith("(passiv)")]
fertigkeiten = sorted(datenbank.übernatürlicheFertigkeiten.values(), key= lambda f : (f.printclass, f.name))
if debugFertigkeit:
    fertigkeiten = [datenbank.übernatürlicheFertigkeiten[debugFertigkeit]]

for fertigkeit in fertigkeiten:
    talentCost = {}
    for tradition in traditionen:
        vorteile = [tradition] + gekaufteVorteile
        if not Hilfsmethoden.voraussetzungenPrüfen(vorteile, [], [], [], [], fertigkeit.voraussetzungen):
            continue
        talentCost[tradition] = 0
        if debugFertigkeit:
            print("\n=== " + tradition.strip(" I") + " ===")
        for talent in sorted(spezialTalente, key = lambda t:  t.name):
            if not fertigkeit.name in talent.fertigkeiten:
                continue
            if not Hilfsmethoden.voraussetzungenPrüfen(vorteile, [], [], [], [], talent.voraussetzungen):
                continue

            if talent.name in kostenModifikatoren:
                kosten = kostenModifikatoren[talent.name](fertigkeit, talent)
            else:
                kosten = talent.kosten
            talentCost[tradition] += kosten
            if debugFertigkeit:
                print(talent.name + ": " + str(kosten) + " EP")
        if talentCost[tradition] < skipTraditionBelowEP:
            if debugFertigkeit:
                print(tradition + " enthält nur Talente im Wert von " + str(talentCost[tradition]) + " EP und wird übersprungen")
            del talentCost[tradition]
    if len(talentCost) == 0:
        print(fertigkeit.name + ": Berechnung wird nicht unterstützt")
        continue
    if debugFertigkeit:
        print("\n=======================")
        for tradition in talentCost:
            print(tradition + ": " + str(talentCost[tradition]) + " EP gesamt")
    averageCost = int(round(sum(talentCost.values()) / len(talentCost)))
    sf = 2
    delta = str(sf3Threshold - averageCost) + " EP unter SF 3"
    if averageCost >= sf4Threshold:
        sf = 4
        delta = str(averageCost - sf4Threshold) + " EP über SF 3"
    elif averageCost >= sf3Threshold:
        sf = 3
        delta = str(averageCost - sf3Threshold) + " EP über SF 2"

    if showDeltaEP:
        print(fertigkeit.name + ": Avg EP " + str(averageCost) + ", SF " + str(sf) + " (" + delta + ")")
    else:
        print(fertigkeit.name + ": Avg EP " + str(averageCost) + ", SF " + str(sf))