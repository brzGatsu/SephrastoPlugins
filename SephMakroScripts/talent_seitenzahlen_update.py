import os
import platform
import subprocess
import copy
from PySide6 import QtWidgets

# Das Makro aktualisiert die Seitenzahl-Angaben von übernatürlichen Talenten in der Sephrasto-Datenbank.
# Dazu werden die Lesezeichen einer gewählten PDF-Datei ausgewertet. Diese müssen exakt gleich, wie die Talente heißen.
# PDFs ohne Talentnamen in den Lesezeichen werden nicht unterstützt!

#========== Settings ===========
pdfDir = "" # gib hier einen Pfad an, um nicht mehr nach der PDF gefragt zu werden
printFoundPages = False # setze auf True, um auch erfolgreich zugewiesene Seitenzahlen auszugeben
stripEndsWith = [" (Dämonisch)", " (Tiergeist)"] # alle Eintragungen hier werden am Ende von Talentnamen gekürzt, beispielsweise wird "Weiches Erstarre (Dämonisch)" zu "Weiches Erstarre".
referenzBuchIndex = 0 # bei allen Talenten mit aktualisierter Seitenzahl wird auch dieses Referenzbuch gesetzt (siehe Datenbankeinstellung "Referenzbücher")

#========== Implementation ===========

cpdfPath = os.path.join("Bin", platform.system(), "cpdf", "cpdf")
def check_output_silent(call):
    if platform.system() == 'Windows':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return subprocess.check_output(call, startupinfo=startupinfo, stderr=subprocess.STDOUT, encoding='utf-8')
    else:
        return subprocess.check_output(call, stderr=subprocess.STDOUT, encoding='utf-8')

if not pdfDir:
    startDir = ""
    pdfDir, _ = QtWidgets.QFileDialog.getOpenFileName(None,"Regelwerk PDF wählen...", startDir, "PDF Datei (*.pdf)")

call = [cpdfPath, "-list-bookmarks", "-utf8", pdfDir]
output = check_output_silent(call).split("\n")
bookmarks = {}
for i in range(3, len(output)-1):
    bookmarkStr = output[i]
    idxName1 = bookmarkStr.index('"')+1
    idxName2 = idxName1 + bookmarkStr[idxName1:].index('"')
    name = bookmarkStr[idxName1:idxName2]
    idxPage1 = idxName2+2
    idxPage2 = idxPage1 + bookmarkStr[idxPage1:].index(" ")
    page = bookmarkStr[idxPage1:idxPage2]
    bookmarks[name] = int(page)

for tal in datenbank.talente.values():
    if not tal.spezialTalent:
        continue
    name = tal.name.replace("'", "’")
    if name.startswith("Mirakel:"):
        name = "Mirakel"
    elif name.startswith("Dämonische Stärkung:"):
        name = "Dämonische Stärkung"

    for strip in stripEndsWith:
        if name.endswith(strip):
            name = name[:-len(strip)]

    if name in bookmarks:
        tal = copy.deepcopy(tal)
        datenbank.talente[tal.name] = tal
        tal.referenzSeite = bookmarks[name]
        tal.referenzBuch = referenzBuchIndex
        tal.finalize(datenbank)
        if printFoundPages:
            print(f"Seitenzahl für {tal.name}: {tal.referenzSeite}")
    else:
        print(f"Seitenzahl fehlt für: {tal.name}")

startDir = os.path.dirname(pdfDir)
dbDir, _ = QtWidgets.QFileDialog.getSaveFileName(None,"Speicherpfad für Datenbank wählen...", startDir, "XML Datei (*.xml)")
if dbDir:
    datenbank.saveFile(dbDir)
    print("Aktualisierte Seitenzahlen erfolgreich gespeichert.")
else:
    print("Kein Speicherpfad gewählt, aktualisierte Seitenzahlen werden nicht gespeichert.")