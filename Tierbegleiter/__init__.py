from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from Tierbegleiter import TierbegleiterEditor
from Tierbegleiter import TierbegleiterMain
from Core.DatenbankEinstellung import DatenbankEinstellung
from Hilfsmethoden import Hilfsmethoden

class Plugin:
    def __init__(self):
        self.mainWindowButton = None
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)

    @staticmethod
    def getDescription():
        return "Dieses Plugin erlaubt das Erstellen von Tierbegleitern und das Exportieren in einen Tierbegleiterbogen. Optional können in der Regelbasis mittels der Einstellung \"Tierbegleiter Plugin: IA Zucht und Ausbildung\" die Ilaris Advanced Regeln zu Zucht und Ausbildung aktiviert werden."

    def createMainWindowButtons(self):
        self.mainWindowButton = QtWidgets.QPushButton()
        self.mainWindowButton.setObjectName("buttonPlugin")
        self.mainWindowButton.setToolTip("Tierbegleiter erstellen")
        self.mainWindowButton.setProperty("class", "icon")
        self.mainWindowButton.setText("\uf6f0")
        self.mainWindowButton.clicked.connect(self.createTierbegleiterEditor) 
        return [self.mainWindowButton]

    def createTierbegleiterEditor(self):
        self.ed = TierbegleiterEditor.TierbegleiterEditor()
        self.ed.formMain = QtWidgets.QWidget()
        self.ed.ui = TierbegleiterMain.Ui_formMain()
        self.ed.ui.setupUi(self.ed.formMain)
        self.ed.setupMainForm()
        self.ed.formMain.show()

    def basisDatenbankGeladenHandler(self, params):
        self.db = params["datenbank"]

        e = DatenbankEinstellung()
        e.name = "Tierbegleiter Plugin: IA Zucht und Ausbildung"
        e.beschreibung = "Falls aktiviert, wird ein zusätzlicher Tab zur Einstellung der Ilaris Advanced-Regeln zu Zucht und Ausbildung eingeblendet und es werden entsprechend angepasste Tierbegleiter verwendet."
        e.text = "False"
        e.typ = "Bool"
        self.db.loadElement(e)