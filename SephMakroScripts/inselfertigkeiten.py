from Hilfsmethoden import Hilfsmethoden

#========== Settings ===========

# Fertigkeiten, die Talente mit einem Gesamt-EP-Wert von mindestens der angegebenen Summe
# für die jeweilige Tradition haben, werden für die Bewertung nicht betrachtet. Das heisst, je höher der Wert,
# desto mehr Fertigkeiten werden als Inselfertigkeiten betrachtet
problematicEPThreshold = 121

# Trage hier kommasepariert alle Traditionen ein, die keinen Vorteil mit 'Tradition I' im Namen haben
zusatzTraditionen = ["Magiedilettant"] 

# Trage hier Vorteile ein, die neben der Tradition für die Überprüfung der Voraussetzungen als gekauft gelten sollen.
gekaufteVorteile = ["Geweiht I", "Zauberer I", "Paktierer I"]

#========== Implementation ===========

fertigkeiten = sorted(datenbank.übernatürlicheFertigkeiten.values(), key= lambda f : (f.kategorie, f.name))
spezialTalente = sorted([t for t in datenbank.talente.values() if t.spezialTalent and not t.name.endswith("(passiv)")], key = lambda t:  t.name)
traditionen = [v.name for v in datenbank.vorteile.values() if v.name.startswith("Tradition") and v.name.endswith(" I")]
traditionen += zusatzTraditionen

talente = {}
for fertigkeit in fertigkeiten:
    talente[fertigkeit.name] = {}
    for tradition in traditionen:
        vorteile = [tradition] + gekaufteVorteile
        talente[fertigkeit.name][tradition] = []
        if not Hilfsmethoden.voraussetzungenPrüfen(fertigkeit, vorteile, [], [], [], [], []):
            continue
        for talent in spezialTalente:
            if not fertigkeit.name in talent.fertigkeiten:
                continue
            if not Hilfsmethoden.voraussetzungenPrüfen(talent, vorteile, [], [], [], [], []):
                continue
            talente[fertigkeit.name][tradition].append(talent)

problematicFerts = {}
for fertigkeit in talente:
    for tradition in talente[fertigkeit]:
        if not tradition in problematicFerts:
            problematicFerts[tradition] = []
        numTalente = len(talente[fertigkeit][tradition])
        epTotal = 0
        for talent in talente[fertigkeit][tradition]:
            epTotal += talent.kosten
        if epTotal == 0 or epTotal >= problematicEPThreshold:
            continue
        problematicFerts[tradition].append(fertigkeit)

notFine = {}
for fertigkeit in talente:
    for tradition in talente[fertigkeit]:
        numTalente = len(talente[fertigkeit][tradition])
        if not fertigkeit in problematicFerts[tradition]:
            continue
        for talent in talente[fertigkeit][tradition]:
            fine = False
            for f in talent.fertigkeiten:
                if f == fertigkeit or f in problematicFerts[tradition]:
                    continue
                vorteile = [tradition] + gekaufteVorteile
                if not Hilfsmethoden.voraussetzungenPrüfen(datenbank.übernatürlicheFertigkeiten[f], vorteile, [], [], [], [], []):
                    continue
                fine = True
                break
            if not fine:
                if not tradition in notFine:
                    notFine[tradition] = {}
                if not fertigkeit in notFine[tradition]:
                    notFine[tradition][fertigkeit] = []
                notFine[tradition][fertigkeit].append(talent)
	
for tradition in notFine:
    print("=== " + tradition + " ===")
    for fertigkeit in notFine[tradition]:
        print(fertigkeit + ":")
        for talent in notFine[tradition][fertigkeit]:
            print(talent.name)
        print("")