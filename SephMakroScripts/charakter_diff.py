from PySide6 import QtWidgets
from Charakter import Char
import Definitionen
import os
from Wolke import Wolke

# Das Makro fordert dich auf, zwei Dateien auszuwählen - eine Datei mit dem alten Charakterstand und eine mit dem Neuen
# Die beiden werden dann verglichen und der Unterschied ausgegeben
def diffCharacters():
    if os.path.isdir(Wolke.Settings['Pfad-Chars']):
        startDir = Wolke.Settings['Pfad-Chars']
    else:
        startDir = ""
    pathOld, _ = QtWidgets.QFileDialog.getOpenFileName(None,"Alten Charakterstand wählen...", startDir, "XML Datei (*.xml)")
    if not pathOld:
        print("Du hast keine alte Charakterdatei gewählt.")
        return
    charOld = Char()
    try:
        charOld.xmlLesen(pathOld)
    except:
        print("Fehler beim Laden der ersten Datei. Es werden nur von Sephrasto erzeuge Charakter-XML-Dateien unterstützt.")
        return

    pathNew, _ = QtWidgets.QFileDialog.getOpenFileName(None,"Neuen Charakterstand wählen...", "", "XML Datei (*.xml)")
    if not pathNew:
        print("Du hast keine neue Charakterdatei gewählt.")
        return
    charNew = Char()
    try:
        charNew.xmlLesen(pathNew)
    except:
        print("Fehler beim Laden der zweiten Datei. Es werden nur von Sephrasto erzeuge Charakter-XML-Dateien unterstützt.")
        return

    def valStr(value):
        return str(value) if value < 0 else "+" + str(value)

    print("Änderungen von " + os.path.basename(pathOld) + " (alt) zu " + os.path.basename(pathNew) + " (neu)\n")
    print("EP Total: " + valStr(charNew.EPtotal - charOld.EPtotal))
    print("EP ausgegeben: " + valStr(charNew.EPspent - charOld.EPspent))
    print("EP verbleibend: " + valStr((charNew.EPtotal - charNew.EPspent) - (charOld.EPtotal - charOld.EPspent)))

    print("\n=== Attribute ===")
    for attribut in Definitionen.Attribute:
        if charOld.attribute[attribut].wert != charNew.attribute[attribut].wert:
            print(attribut + ": " + valStr(charNew.attribute[attribut].wert - charOld.attribute[attribut].wert))

    if charOld.asp.wert != charNew.asp.wert:
        print("Zugekaufte AsP: " + valStr(charNew.asp.wert - charOld.asp.wert))

    if charOld.kap.wert != charNew.kap.wert:
        print("Zugekaufte KaP: "+  valStr(charNew.kap.wert - charOld.kap.wert))

    print("\n=== Vorteile ===")
    for vorteil in sorted(datenbank.vorteile):
        if vorteil in charOld.vorteile and not vorteil in charNew.vorteile:
            print(vorteil + ": entfernt")
        elif not vorteil in charOld.vorteile and vorteil in charNew.vorteile:
            print(vorteil + ": gekauft")
        elif vorteil in charOld.vorteileVariable and vorteil in charNew.vorteileVariable and charOld.vorteileVariable[vorteil].kosten != charNew.vorteileVariable[vorteil].kosten:
            print(vorteil + ": variable Kosten geändert (" + valStr(charNew.vorteileVariable[vorteil].kosten - charOld.vorteileVariable[vorteil].kosten) + " EP)")

    print("\n=== Freie Fertigkeiten ===")
    fertigkeiten = set([f.name for f in charOld.freieFertigkeiten] + [f.name for f in charNew.freieFertigkeiten])
    for fertigkeit in fertigkeiten:
        old = next((f for f in charOld.freieFertigkeiten if f.name == fertigkeit), None)
        new = next((f for f in charNew.freieFertigkeiten if f.name == fertigkeit), None)
        if old is not None and new is None:
            print(fertigkeit + ": entfernt (" + valStr(-old.wert) + ")")
        elif old is None and new is not None:
            print(fertigkeit + ": gekauft (" + valStr(new.wert) + ")")
        elif new.wert != old.wert:
            print(fertigkeit + ": " + valStr(new.wert - old.wert))
        
    def printFertigkeiten(old, new, db):
        for fertigkeit in sorted(db):
            if old[fertigkeit].wert != new[fertigkeit].wert:
                print(fertigkeit + ": " + valStr(new[fertigkeit].wert -old[fertigkeit].wert))
            talente = set(old[fertigkeit].gekaufteTalente + new[fertigkeit].gekaufteTalente)
            talenteStr = ""
            for talent in talente:
                if talent in old[fertigkeit].gekaufteTalente and not talent in new[fertigkeit].gekaufteTalente:
                    talenteStr += "> " + talent + ": entfernt\n"
                elif not talent in  old[fertigkeit].gekaufteTalente and talent in new[fertigkeit].gekaufteTalente:
                    talenteStr += "> " + talent + ": gekauft\n"
                elif talent in charOld.talenteVariable and talent in charNew.talenteVariable and charOld.talenteVariable[talent].kosten != charNew.talenteVariable[talent].kosten:
                    talenteStr += "> " + talent + ": variable Kosten geändert (" + valStr(charNew.talenteVariable[talent].kosten - charOld.talenteVariable[talent].kosten) + " EP)\n"
            if talenteStr:
                if old[fertigkeit].wert == new[fertigkeit].wert:
                    print(fertigkeit + ": +0")
                print(talenteStr.rstrip("\n"))

    print("\n=== Fertigkeiten ===")
    printFertigkeiten(charOld.fertigkeiten, charNew.fertigkeiten, datenbank.fertigkeiten)

    print("\n=== Übernatürliche Fertigkeiten ===")
    printFertigkeiten(charOld.übernatürlicheFertigkeiten, charNew.übernatürlicheFertigkeiten, datenbank.übernatürlicheFertigkeiten)
    
diffCharacters()