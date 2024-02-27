from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from Kreaturen import KreaturEditor
from Kreaturen import KreaturMain
from Kreaturen import IlarisOnlineDBWrapper
from Kreaturen import IlarisOnlineLoginWrapper
from Hilfsmethoden import Hilfsmethoden

class Plugin:
    def __init__(self):
        self.mainWindowButton = None
        # EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)

    def createMainWindowButtons(self):
        self.mainWindowButton = QtWidgets.QPushButton()
        self.mainWindowButton.setObjectName("buttonPlugin")
        self.mainWindowButton.setToolTip("Kreatur erstellen")
        self.mainWindowButton.setProperty("class", "icon")
        self.mainWindowButton.setText("\uf6e2")    # \uf6f0 is horse
        self.mainWindowButton.clicked.connect(self.createKreaturEditor) 
        return [self.mainWindowButton]

    def createKreaturEditor(self):
        print("create Editor")
        self.ed = KreaturEditor.KreaturEditor()
        self.ed.formMain = QtWidgets.QWidget()
        self.ed.ui = KreaturMain.Ui_formMain()
        print("setup ui")
        print(self.ed.ui)
        try:
            self.ed.ui.setupUi(self.ed.formMain)
            print("ui setup done")
        except Exception as e:
            print(e)
        print("setup main")
        self.ed.setupMainForm()
        self.ed.onlineDialog = IlarisOnlineDBWrapper.KreaturOnlineDBWrapper
        self.ed.loginDialog = IlarisOnlineLoginWrapper.IlarisOnlineLoginWrapper
        self.ed.formMain.show()
