import random
import math
import re

talente = datenbank.talente.values()

def roll():
    values = [random.randint(1, 20) for _ in range(3)]
    return sorted(values)[1]

# Traditionen
# Ach,Dru,Geo,Hex,Bor,Elf,Sch,Srl,Mag,Bard,Ztz,Alch,Smn,...
# Setz die gewünschte Tradition ein und führe das Programm aus
# Bedenke: In der Regel würfelt man als Meister nur auf wenige Zauber und nicht für alle Zauber alles aus. Daher wird dir vermutlich mehr angezeigt, als du am Ende aufzeigen möchtest
tradition = "Mag"
bonus = 0

fertigkeiten = ["Antimagie", "Dämonisch", "Eigenschaft", "Einfluss", "Eis", "Erz", "Feuer", "Hellsicht", "Humus", "Illusion", "Kraft", "Luft", "Temporal", "Umwelt", "Verständigung", "Verwandlung", "Wasser", "Dolchzauber", "Elfenlieder", "Gaben des Blutgeists", "Geister der Stärkung", "Geister des Zorns", "Geister rufen", "Geister vertreiben", "Hexenflüche", "Keulenrituale", "Kristallmagie", "Kugelzauber", "Ringrituale", "Schalenzauber", "Stabzauber", "Trommelrituale", "Vertrautenmagie", "Zaubermelodien", "Zaubertänze"]

for talent in talente:
    if len(set(fertigkeiten+talent.fertigkeiten)) != len(fertigkeiten) + len(talent.fertigkeiten):
        erlernen = talent.text.split("<b>Erlernen:</b> ")
        erlernen = erlernen[1] if len(erlernen)>1 else None
        if(erlernen):
            try:
                index = erlernen.index(tradition)
                value = re.search(r'\d+', erlernen[index:]) or None
                value = int(value.group()) if value else 42
                if roll()+bonus>=value:
                    print(talent.name)
            except ValueError:
                pass