# -*- coding: utf-8 -*-
import Objekte
from PySide6 import QtWidgets, QtCore
from Wolke import Wolke
from RuestungenPlus import RSDatenbankEditRuestungseigenschaft

class Ruestungseigenschaft():
    def __init__(self):
        self.name = ''
        self.text = ''
        self.script = ''
        self.scriptOnlyFirst = False
        self.isUserAdded = True

class RSDatenbankEditRuestungseigenschaftWrapper(object):
    def __init__(self, datenbank, ruestungseigenschaft=None, readonly = False):
        super().__init__()
        self.datenbank = datenbank
        if ruestungseigenschaft is None:
            ruestungseigenschaft = Ruestungseigenschaft()
        self.ruestungseigenschaftPicked = ruestungseigenschaft
        self.nameValid = True
        self.readonly = readonly
        self.dialog = QtWidgets.QDialog()
        self.ui = RSDatenbankEditRuestungseigenschaft.Ui_ruestungseigenschaftDialog()
        self.ui.setupUi(self.dialog)

        self.dialog.setWindowFlags(
                QtCore.Qt.Window |
                QtCore.Qt.CustomizeWindowHint |
                QtCore.Qt.WindowTitleHint |
                QtCore.Qt.WindowCloseButtonHint |
                QtCore.Qt.WindowMaximizeButtonHint |
                QtCore.Qt.WindowMinimizeButtonHint)
        
        windowSize = Wolke.Settings["WindowSize-DBWaffeneigenschaft"]
        self.dialog.resize(windowSize[0], windowSize[1])

        self.ui.nameEdit.setText(ruestungseigenschaft.name)
        self.ui.nameEdit.textChanged.connect(self.nameChanged)
        self.nameChanged()

        self.ui.textEdit.setPlainText(ruestungseigenschaft.text)

        self.ui.scriptEdit.setText(ruestungseigenschaft.script)
        self.ui.scriptEdit.setToolTip("Siehe \"Skripte für Vorteile und Waffeneigenschaften\" in der Sephrasto-Hilfe für verfügbare Funktionen und Beispiele.")
        self.ui.checkOnlyFirst.setChecked(ruestungseigenschaft.scriptOnlyFirst)

        self.dialog.show()
        ret = self.dialog.exec()

        Wolke.Settings["WindowSize-DBWaffeneigenschaft"] = [self.dialog.size().width(), self.dialog.size().height()]

        if ret == QtWidgets.QDialog.Accepted:
            self.ruestungseigenschaft = Ruestungseigenschaft()
            self.ruestungseigenschaft.name = self.ui.nameEdit.text()
            self.ruestungseigenschaft.text = self.ui.textEdit.toPlainText()
            self.ruestungseigenschaft.script = str.strip(self.ui.scriptEdit.text())
            self.ruestungseigenschaft.scriptOnlyFirst = self.ui.checkOnlyFirst.isChecked()
            if self.ruestungseigenschaft == self.ruestungseigenschaftPicked:
                self.ruestungseigenschaft = None
        else:
            self.ruestungseigenschaft = None
           
    def nameChanged(self):
        name = self.ui.nameEdit.text()
        if name == "":
            self.ui.nameEdit.setToolTip("Name darf nicht leer sein.")
            self.ui.nameEdit.setStyleSheet("border: 1px solid red;")
            self.nameValid = False
        elif name != self.ruestungseigenschaftPicked.name and name in self.datenbank.ruestungseigenschaften:
            self.ui.nameEdit.setToolTip("Name existiert bereits.")
            self.ui.nameEdit.setStyleSheet("border: 1px solid red;")
            self.nameValid = False
        else:
            self.ui.nameEdit.setToolTip("")
            self.ui.nameEdit.setStyleSheet("")
            self.nameValid = True
        self.updateSaveButtonState()

    def updateSaveButtonState(self):
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Save).setEnabled(not self.readonly and self.nameValid)