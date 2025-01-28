from Wolke import Wolke
from Ressourcen import CharakterRessourcen
from PySide6 import QtWidgets, QtCore, QtGui
from Hilfsmethoden import Hilfsmethoden
from EventBus import EventBus
from functools import partial
from Ressourcen.Ressource import Ressource

class CharakterRessourcenWrapper(QtCore.QObject):
    modified = QtCore.Signal()
    
    def __init__(self):
        super().__init__()
        self.form = QtWidgets.QWidget()
        self.ui = CharakterRessourcen.Ui_Form()
        self.ui.setupUi(self.form)

        self.ressourcenCount = 0

        self.leNameList = []
        self.leKommentarList = []
        self.cbWertList = []

        self.standardRessourcen = Wolke.DB.einstellungen["Ressourcen Plugin: Standardressourcen"].wert

        count = 0
        for key in self.standardRessourcen.keys():
            if len(Wolke.Char.ressourcen) <= count or Wolke.Char.ressourcen[count].name != key:
                ressource = Ressource()
                ressource.name = key
                ressource.kommentar = self.standardRessourcen[key][0]
                Wolke.Char.ressourcen.insert(count, ressource)
            count += 1

        if len(Wolke.Char.ressourcen) == 0:
            for key in self.standardRessourcen.keys():
                ressource = Ressource()
                ressource.name = key
                Wolke.Char.ressourcen.append(ressource)

        self.ui.scrollAreaWidgetContents.layout().setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)

        for row in range(0, max(len(self.standardRessourcen) + 3, len(Wolke.Char.ressourcen))):
            self.ressourcenCount +=1

            if len(self.standardRessourcen) >= self.ressourcenCount:
                leName = QtWidgets.QLabel()
            else:
                leName = QtWidgets.QLineEdit()
                leName.editingFinished.connect(self.update)

            leName.setProperty("class", "h4")
            leName.setFixedWidth(Hilfsmethoden.emToPixels(20))

            self.leNameList.append(leName)
            self.ui.ressourcenGrid.layout().addWidget(leName, row+1, 0)

            cbWert = QtWidgets.QComboBox()
            cbWert.addItem("0")
            cbWert.addItem("W4")
            cbWert.addItem("W6")
            cbWert.addItem("W8")
            cbWert.addItem("W10")
            cbWert.addItem("W12")
            cbWert.currentIndexChanged.connect(partial(self.wertChangedHandler, ressourceIndex=len(self.cbWertList)))
            self.cbWertList.append(cbWert)
            self.ui.ressourcenGrid.layout().addWidget(cbWert, row+1, 1)

            leKommentar = QtWidgets.QLineEdit()
            leKommentar.editingFinished.connect(self.update)
            self.leKommentarList.append(leKommentar)
            self.ui.ressourcenGrid.layout().addWidget(leKommentar, row+1, 2)

            if row % 2 != 0:
                leKommentar.setProperty("class", "alternateBase")
        
    def load(self):
        standardRessourcenVals = list(self.standardRessourcen.values())
        count = 0
        for el in Wolke.Char.ressourcen:
            self.leNameList[count].blockSignals(True)
            self.leKommentarList[count].blockSignals(True)
            self.cbWertList[count].blockSignals(True)

            self.leNameList[count].setText(el.name)
            self.leKommentarList[count].setText(el.kommentar)
            if count < len(standardRessourcenVals):
                self.cbWertList[count].setToolTip(standardRessourcenVals[count][el.wert])

            index = el.wert
            self.cbWertList[count].setCurrentIndex(index)

            self.leNameList[count].blockSignals(False)
            self.leKommentarList[count].blockSignals(False)
            self.cbWertList[count].blockSignals(False)

            count += 1
            if count >= self.ressourcenCount:
                break

        while count < self.ressourcenCount:
            self.leNameList[count].blockSignals(True)
            self.leKommentarList[count].blockSignals(True)
            self.cbWertList[count].blockSignals(True)

            self.leNameList[count].setText("")
            self.leKommentarList[count].setText("")
            index = 0
            self.cbWertList[count].setCurrentIndex(index)

            self.leNameList[count].blockSignals(False)
            self.leKommentarList[count].blockSignals(False)
            self.cbWertList[count].blockSignals(False)
            count += 1

        self.updateInfoLabel()
    
    def wertChangedHandler(self, index, ressourceIndex):
        standardRessourcenVals = list(self.standardRessourcen.values())
        if ressourceIndex < len(standardRessourcenVals):
            wert = self.cbWertList[ressourceIndex].currentIndex()
            bedeutung = standardRessourcenVals[ressourceIndex][wert]

            self.cbWertList[ressourceIndex].setToolTip(bedeutung)
            self.leKommentarList[ressourceIndex].blockSignals(True)
            self.leKommentarList[ressourceIndex].setText(bedeutung)
            self.leKommentarList[ressourceIndex].blockSignals(False)

        self.updateInfoLabel()
        self.update()

    def update(self):
        ressourcenNeu = []
        for count in range(0,self.ressourcenCount):
            name = self.leNameList[count].text()
            #definition = None
            #if name in Wolke.DB.freieFertigkeiten:
            #    definition = Wolke.DB.freieFertigkeiten[name]
            #else:
            #    definition = FreieFertigkeitDefinition()
            #    definition.name = name
            ressource = Ressource()
            ressource.name = name
            ressource.kommentar = self.leKommentarList[count].text()
            ressource.wert = self.cbWertList[count].currentIndex()
            ressourcenNeu.append(ressource)

        #Preserve the position of actual elements but remove any trailing empty elements
        #This is needed for ArrayEqual later to work as intended
        for ressource in reversed(ressourcenNeu):
            if ressource.name == "":
                ressourcenNeu.pop()
            else:
                break

        if not Hilfsmethoden.ArrayEqual(ressourcenNeu, Wolke.Char.ressourcen):
            Wolke.Char.ressourcen = ressourcenNeu
            self.modified.emit()

    def updateInfoLabel(self):
        pointsAvailable = 2 + int(Wolke.Char.epGesamt / 400)
        pointsSpent = 0
        for cbWert in self.cbWertList:
            pointsSpent += cbWert.currentIndex()

        self.ui.labelInfo.setText(f"{pointsSpent} Punkte ausgegeben. Verfügbar: {pointsAvailable - pointsSpent} Punkte (gemäß Fausregel 2 + 1 je 400 EP). ")