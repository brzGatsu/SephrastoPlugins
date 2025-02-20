from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from Tierbegleiter import TierbegleiterEditor
from Core.DatenbankEinstellung import DatenbankEinstellung
from Hilfsmethoden import Hilfsmethoden

class Plugin:
    def __init__(self):
        self.mainWindowButton = None
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)

    def createMainWindowButtons(self):
        self.mainWindowButton = QtWidgets.QPushButton()
        self.mainWindowButton.setObjectName("buttonPlugin")
        self.mainWindowButton.setToolTip("Tierbegleiter erstellen")
        self.mainWindowButton.setProperty("class", "icon")
        font = self.mainWindowButton.font()
        font.setHintingPreference(QtGui.QFont.PreferNoHinting)
        self.mainWindowButton.setFont(font)
        self.mainWindowButton.setText("\uf6f0")
        self.mainWindowButton.clicked.connect(self.createTierbegleiterEditor) 
        return [self.mainWindowButton]

    def createTierbegleiterEditor(self):
        self.ed = TierbegleiterEditor.TierbegleiterEditor()
        self.ed.newCharacter()

    def basisDatenbankGeladenHandler(self, params):
        self.db = params["datenbank"]

        e = DatenbankEinstellung()
        e.name = "Tierbegleiter Plugin: EP-Kosten Werte Script"
        e.beschreibung = "Das script berechnet die EP-Kosten der verschiedenen Werte. Diese müssen der Variable 'kosten' zugewiesen werden. " +\
        "Es wird einmal für jeden Wert aufgerufen, dessen Name in der Variable 'name' und dessen Wert in der Variable 'wert' steht. " +\
        "Folgende Werte gibt es: 'KO', 'MU', 'GE', 'KK', 'IN', 'KL', 'CH', 'FF', 'WS', 'RS', 'BE', 'MR', 'GS', 'TP', 'INI', 'AT', 'VT'"
        e.text = """if name in ["WS", "RS", "BE"]:
    kosten = 0
else:
    kosten = wert"""
        e.typ = "Exec"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Tierbegleiter Plugin: EP-Kosten Talente Script"
        e.beschreibung = "Das script berechnet die EP-Kosten der Talente. Diese müssen der Variable 'kosten' zugewiesen werden. " +\
        "Das Script wird einmal für jedes Talent aufgerufen, dessen Name in der Variable 'name' und dessen Wert in der Variable 'wert' steht."
        e.text = "kosten = wert"
        e.typ = "Exec"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Tierbegleiter Plugin: EP-Kosten Vorteile Script"
        e.beschreibung = "Das script berechnet die EP-Kosten der Vorteile. Diese müssen der Variable 'kosten' zugewiesen werden. " +\
        "Das Script wird einmal für jeden Vorteil aufgerufen, dessen Name in der Variable 'name' steht."
        e.text = "kosten = 1"
        e.typ = "Exec"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Tierbegleiter Plugin: EP-Kosten Infotext"
        e.beschreibung = "Der Text, der im Ausrüstung & Info Tab im Punkt Erfahrungspunkte erscheinen soll."
        e.text = "Erfahrungspunkte sind in erster Linie für Vertrautentiere gedacht: Da sie besonders prächtige Vertreter ihrer Gattung sind, " +\
            "erhältst du 4 Erfahrungspunkte pro Stufe der Geodischen oder Hexischen Tradition. Pro Punkt darfst du einen Spielwert des Vertrautentiers " +\
            "(ausgenommen WS, WS* und RW) um 1 Punkt erhöhen, solange das Ergebnis dem gesunden Menschenverstand nicht widerspricht."
        e.typ = "Text"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Tierbegleiter Plugin: Zucht"
        e.beschreibung = "Pro Zeile wird eine Zuchtstufe eingetragen, zusammen mit einem Preismultiplikator. Beispiel: Normal=0.5. Wenn das Feld leer ist, wird die Zuchtauswahl nicht eingeblendet."
        e.text = ""
        e.strip = True
        e.typ = "TextDict"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Tierbegleiter Plugin: Reiterkampf Waffeneigenschaften"
        e.beschreibung = "Zusätzliche Waffeneigenschaften, die jeder Reiterkampf-Waffe hinzugefügt werden sollen. Eine Eigenschaft pro Zeile."
        e.text = "AT +4 gegen kleinere Gegner"
        e.typ = "TextList"
        e.separator = "\n"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Tierbegleiter Plugin: Fenstertitel"
        e.beschreibung = "Der Titel des Tierbegleiter-Fensters."
        e.text = "Sephrasto"
        e.typ = "Text"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Tierbegleiter Plugin: DH Script"
        e.beschreibung = "Das Script berechnet das DH. Für die Berechnung zur Verfügung stehen KO und WS."
        e.text = "round(KO/2)"
        e.typ = "Eval"
        self.db.loadElement(e)
        