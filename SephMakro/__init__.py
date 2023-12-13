from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from SephMakro import SephMakroEditor
from SephMakro import SephMakroMain
from Hilfsmethoden import Hilfsmethoden

class Plugin:
    def __init__(self):
        self.mainWindowButton = None

    def createMainWindowButtons(self):
        self.mainWindowButton = QtWidgets.QPushButton()
        self.mainWindowButton.setObjectName("buttonPlugin")
        self.mainWindowButton.setToolTip("SephMakro")
        self.mainWindowButton.setProperty("class", "icon")
        self.mainWindowButton.setText("\uf120")
        self.mainWindowButton.clicked.connect(self.createSephMakroEditor)
        return [self.mainWindowButton]

    def createSephMakroEditor(self):
        self.ed = SephMakroEditor.SephMakroEditor()
        self.ed.formMain = QtWidgets.QWidget()
        self.ed.ui = SephMakroMain.Ui_formMain()
        self.ed.ui.setupUi(self.ed.formMain)
        self.ed.setupMainForm()
        self.ed.formMain.show()