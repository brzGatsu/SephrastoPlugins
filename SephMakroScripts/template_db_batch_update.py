# Mit diesem Template können Elemente der in SephMakro aktivierten Datenbank massenhaft per code bearbeitet werden
# Am Ende wird die Datenbank überspeichert, also besser vorher eine Sicherheitskopie machen.

import copy
from Hilfsmethoden import Hilfsmethoden
import re

for el in datenbank.vorteile.values(): # oder datenbank.talente, .waffen etc.
    # hier el modifizieren
    # el.name = "Test"
    datenbank.tablesByType[el.__class__][el.name] = copy.deepcopy(el)

datenbank.saveFile()