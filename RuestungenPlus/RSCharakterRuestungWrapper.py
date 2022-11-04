# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore, QtGui
import copy
import re
from RuestungenPlus import RSCharakterRuestung
from Wolke import Wolke
from EventBus import EventBus
import logging
from CharakterRuestungPickerWrapper import RuestungPicker
import Objekte
from Hilfsmethoden import Hilfsmethoden
from TextTagCompleter import TextTagCompleter

class RSCharakterRuestungWrapper(QtCore.QObject):
    modified = QtCore.Signal()
    reloadRSTabs = QtCore.Signal()

    def __init__(self, index):
        super().__init__()

        self.index = index
        self.charTeilrüstungen = Wolke.Char.teilrüstungen1
        if self.index == 1:
            self.charTeilrüstungen = Wolke.Char.teilrüstungen2
        elif self.index == 2:
            self.charTeilrüstungen = Wolke.Char.teilrüstungen3

        self.form = QtWidgets.QWidget()
        self.ui = RSCharakterRuestung.Ui_formAusruestung()
        self.ui.setupUi(self.form)

        self.currentlyLoading = False

        self.ui.checkZonen.stateChanged.connect(self.checkZonenChanged)

        self.ruestungsTypen = Wolke.DB.einstellungen["Rüstungen: Typen"].toTextList()
        self.ruestungsEigenschaften = Wolke.DB.einstellungen["RüstungenPlus Plugin: Rüstungseigenschaften"].toBool()
        self.gesamtZRS = [self.ui.spinGesamtBein, self.ui.spinGesamtLarm, self.ui.spinGesamtRarm, self.ui.spinGesamtBauch, self.ui.spinGesamtBrust, self.ui.spinGesamtKopf]

        self.ui.editGesamtName.editingFinished.connect(self.updateGesamtRuestung)
        self.ui.spinGesamtBE.valueChanged.connect(self.updateGesamtRuestung)

        if self.ruestungsEigenschaften:
            self.ui.labelHinweis.setText(self.ui.labelHinweis.text() + "\nEs werden außerdem nur die Eigenschaften der gesamten Rüstung (Zeile 1) ausgewertet.")

            self.labelEigenschaften = QtWidgets.QLabel("Eigenschaften")
            self.labelEigenschaften.setProperty("class", "h4")
            self.ui.Ruestungen.addWidget(self.labelEigenschaften, 0, 11, 1, 1)

            self.editGesamtEigenschaften = QtWidgets.QLineEdit()
            self.editGesamtEigenschaften.editingFinished.connect(self.updateGesamtRuestung)
            self.ui.Ruestungen.addWidget(self.editGesamtEigenschaften, 1, 11, 1, 1)
            self.ui.editGesamtName.setMaximumSize(QtCore.QSize(200, 16777215))

        self.labels = []
        self.editRName = []
        self.spinRS = []
        self.spinZRS = []
        self.spinPunkte = []
        self.buttons = []
        self.editEigenschaften = []
        self.eigenschaftenCompleter = []
        row = 3
        index = 0
        for typ in self.ruestungsTypen:
            col = 0
            label = QtWidgets.QLabel(typ)
            self.labels.append(label)
            self.ui.Ruestungen.addWidget(label, row, col, 1, 1)
            col += 1

            editRName = QtWidgets.QLineEdit()
            editRName.editingFinished.connect(self.updateRuestungen)
            if self.ruestungsEigenschaften:
                editRName.setMaximumSize(QtCore.QSize(200, 16777215))
            self.editRName.append(editRName)
            self.ui.Ruestungen.addWidget(editRName, row, col, 1, 2)
            col += 2

            spinRS = QtWidgets.QSpinBox()
            spinRS.valueChanged.connect(self.updateRuestungen)
            self.spinRS.append(spinRS)
            spinRS.setMinimum(0)
            spinRS.setMaximum(99)
            spinRS.setAlignment(QtCore.Qt.AlignCenter)
            spinRS.setButtonSymbols(QtWidgets.QSpinBox.PlusMinus)
            self.ui.Ruestungen.addWidget(spinRS, row, col, 1, 1)
            col += 1

            self.spinZRS.append([])
            for i in range(6):
                spinZRS = QtWidgets.QSpinBox()
                spinZRS.valueChanged.connect(self.updateRuestungen)
                self.spinZRS[index].append(spinZRS)
                spinZRS.setMinimum(0)
                spinZRS.setMaximum(99)
                spinZRS.setAlignment(QtCore.Qt.AlignCenter)
                spinZRS.setButtonSymbols(QtWidgets.QSpinBox.PlusMinus)
                self.ui.Ruestungen.addWidget(spinZRS, row, col, 1, 1)
                col += 1

            spinPunkte = QtWidgets.QSpinBox()
            self.spinPunkte.append(spinPunkte)
            spinPunkte.setMinimum(0)
            spinPunkte.setMaximum(999)
            spinPunkte.setAlignment(QtCore.Qt.AlignCenter)
            spinPunkte.setReadOnly(True)
            spinPunkte.setButtonSymbols(QtWidgets.QSpinBox.NoButtons)
            self.ui.Ruestungen.addWidget(spinPunkte, row, col, 1, 1)
            col += 1

            if self.ruestungsEigenschaften:
                leEigenschaft = QtWidgets.QLineEdit()
                leEigenschaft.editingFinished.connect(self.updateRuestungen)
                self.editEigenschaften.append(leEigenschaft)
                self.ui.Ruestungen.addWidget(leEigenschaft, row, col, 1, 1)
                eigenschaftenCompleter = TextTagCompleter(leEigenschaft, Wolke.DB.ruestungseigenschaften.keys())
                self.eigenschaftenCompleter.append(eigenschaftenCompleter)
                col += 1

            addR = QtWidgets.QPushButton()
            addR.setText('\u002b')
            addR.setMaximumSize(QtCore.QSize(20, 20))
            addR.setProperty("class", "icon")
            addR.clicked.connect(lambda qtNeedsThis=False, idx=index: self.selectArmor(idx))
            self.buttons.append(addR)
            self.ui.Ruestungen.addWidget(addR, row, col, 1, 1)

            row += 1
            index += 1

        # Add summarized armor value widgets at the end so we can reuse some functions
        self.editRName.append(self.ui.editGesamtName)
        self.spinRS.append(self.ui.spinGesamtRS)
        self.spinPunkte.append(self.ui.spinGesamtPunkte)
        self.spinZRS.append(self.gesamtZRS)
        if self.ruestungsEigenschaften:
            self.editEigenschaften.append(self.editGesamtEigenschaften)
            eigenschaftenCompleter = TextTagCompleter(self.editGesamtEigenschaften, Wolke.DB.ruestungseigenschaften.keys())
            self.eigenschaftenCompleter.append(eigenschaftenCompleter)
        self.gesamtIndex = len(self.ruestungsTypen)

    def load(self):
        self.currentlyLoading = True

        if self.index < len(Wolke.Char.rüstung):
            R = Wolke.Char.rüstung[self.index]
            self.loadArmorIntoFields(R, self.gesamtIndex)

        for index in range(len(self.charTeilrüstungen)):
            R = self.charTeilrüstungen[index]
            if index < len(self.ruestungsTypen):
                self.loadArmorIntoFields(R, index)

        self.ui.checkZonen.setChecked(Wolke.Char.zonenSystemNutzen)
        self.currentlyLoading = False

        self.refreshZRSVisibility()

    def checkZonenChanged(self):
        if self.currentlyLoading:
            return
        #if Wolke.Char.zonenSystemNutzen == self.ui.checkZonen.isChecked():
        #    return
        infoBox = QtWidgets.QMessageBox()
        infoBox.setIcon(QtWidgets.QMessageBox.Warning)
        infoBox.setText("Wenn du zwischen einfachem und Zonensystem wechselst, gilt das für alle Rüstungen. Dabei werden eventuell einige deiner Slots gelöscht, speichere deinen Charakter zur Sicherheit vorher ab. Möchtest du fortfahren?")
        infoBox.setWindowTitle("Wechsel des Rüstungssystems")
        infoBox.addButton("Abbrechen", QtWidgets.QMessageBox.NoRole)
        infoBox.addButton("Ja", QtWidgets.QMessageBox.YesRole)
        result = infoBox.exec()
        if result == 0:
            self.ui.checkZonen.setChecked(not self.ui.checkZonen.isChecked())
            return

        Wolke.Char.zonenSystemNutzen = self.ui.checkZonen.isChecked()
        self.modified.emit()
        self.reloadRSTabs.emit()

    def isArmorDefault(self, R):
        tmp = R.typ
        R.typ = 0
        result = R == Objekte.Ruestung()
        R.typ = tmp
        return result

    def updateGesamtRuestung(self):
        if self.currentlyLoading:
            return
        R = self.createRuestung(self.gesamtIndex)
        self.refreshDerivedArmorValues(R, self.gesamtIndex)
        while self.index >= len(Wolke.Char.rüstung):
            Wolke.Char.rüstung.append(Objekte.Ruestung())

        if Wolke.Char.rüstung[self.index] != R:
            Wolke.Char.rüstung[self.index] = R
            self.modified.emit()
            self.refreshDerivedArmorValues(R, self.gesamtIndex)

    def updateRuestungen(self):
        if self.currentlyLoading:
            return
        ruestungNeu = []
        for index in range(len(self.ruestungsTypen)):
            R = self.createRuestung(index)
            ruestungNeu.append(R)
            self.refreshDerivedArmorValues(R, index)

            if self.isArmorDefault(R):
                self.buttons[index].setText('\u002b')
            else:
                self.buttons[index].setText('\uf2ed')

        if Hilfsmethoden.ArrayEqual(ruestungNeu, self.charTeilrüstungen):
            return

        self.charTeilrüstungen.clear()
        self.charTeilrüstungen += ruestungNeu

        R = Objekte.Ruestung()
        R.name = self.ui.editGesamtName.text()
        for type in range(len(self.ruestungsTypen)):
            if self.ui.checkZonen.isChecked():
                for i in range(6):
                    R.rs[i] += self.spinZRS[type][i].value()
            else:
                for i in range(6):
                    R.rs[i] += self.spinRS[type].value()
        beDelta = self.ui.spinGesamtBE.value() - self.ui.spinGesamtRS.value()
        R.be = R.getRSGesamtInt() + beDelta
        if self.ruestungsEigenschaften:
            R.text = self.editGesamtEigenschaften.text()

        self.currentlyLoading = True
        self.loadArmorIntoFields(R, self.gesamtIndex)
        self.currentlyLoading = False
        self.updateGesamtRuestung()
        self.modified.emit()

    def refreshDerivedArmorValues(self, R, index):
        if self.ui.checkZonen.isChecked():
            self.spinRS[index].blockSignals(True)
            self.spinRS[index].setValue(R.getRSGesamtInt())
            self.spinRS[index].blockSignals(False)
        else:
            for i in range(0, 6):
               self.spinZRS[index][i].blockSignals(True)
               self.spinZRS[index][i].setValue(R.getRSGesamtInt())
               self.spinZRS[index][i].blockSignals(False)

        spinPunkte = self.spinPunkte[index]
        spinPunkte.setValue(sum(R.rs))

        if index == self.gesamtIndex:
            punkte = sum(R.rs)
            if self.index < len(Wolke.Char.rüstung) and hasattr(Wolke.Char.rüstung[self.index], 'zrsMod'):
                punkte += Wolke.Char.rüstung[self.index].zrsMod
            spinPunkte.setValue(punkte)
            if punkte % 6 != 0:
                self.ui.spinGesamtPunkte.setStyleSheet("border: 1px solid orange;")
                missingPoints = 6 - punkte % 6
                if missingPoints == 1:
                    self.ui.spinGesamtPunkte.setToolTip("Der Rüstung fehlt " + str(missingPoints) + " Punkt ZRS.")
                else:
                    self.ui.spinGesamtPunkte.setToolTip("Der Rüstung fehlen " + str(missingPoints) + " Punkte ZRS.")
            else:
                self.ui.spinGesamtPunkte.setStyleSheet("")
                self.ui.spinGesamtPunkte.setToolTip("")

    def createRuestung(self, index):
        R = Objekte.Ruestung() 
        R.name = self.editRName[index].text()
        if self.ui.checkZonen.isChecked():
            for i in range(0, 6):
                R.rs[i] = self.spinZRS[index][i].value()
        else:
            R.rs = 6*[self.spinRS[index].value()]

        if index == self.gesamtIndex:
            R.be = int(self.ui.spinGesamtBE.value())
        else:
            R.be = R.getRSGesamtInt()
            R.typ = index
        R.text = self.editEigenschaften[index].text() or "" if self.ruestungsEigenschaften else ""
        return R

    def loadArmorIntoFields(self, R, index):
        self.editRName[index].setText(R.name)
        for i in range(0, 6):
            if self.ui.checkZonen.isChecked():
                self.spinZRS[index][i].setValue(R.rs[i])
            else:
                self.spinZRS[index][i].setValue(R.getRSGesamtInt())

        if index == self.gesamtIndex:
            self.ui.spinGesamtBE.setValue(EventBus.applyFilter("ruestung_be", R.be, { "name" : R.name }))

        self.spinRS[index].setValue(R.getRSGesamtInt())

        if self.ruestungsEigenschaften:
            self.editEigenschaften[index].setText(R.text)

        self.refreshDerivedArmorValues(R, index)

        if index != self.gesamtIndex:
            if self.isArmorDefault(R):
                self.buttons[index].setText('\u002b')
            else:
                self.buttons[index].setText('\uf2ed')

    def selectArmor(self, index):
        if index >= len(self.charTeilrüstungen) or self.isArmorDefault(self.charTeilrüstungen[index]):
            logging.debug("Starting RuestungPicker")

            pickerClass = EventBus.applyFilter("class_ruestungspicker_wrapper", RuestungPicker)
            picker = pickerClass(self.editRName[index].text(), 2 if self.ui.checkZonen.isChecked() else 1, self.ruestungsTypen[index])
            logging.debug("RuestungPicker created")
            if picker.ruestung is not None:
                self.currentlyLoading = True
                self.loadArmorIntoFields(picker.ruestung, index)
                self.currentlyLoading = False
                self.updateRuestungen()
        else:
            self.currentlyLoading = True
            self.loadArmorIntoFields(Objekte.Ruestung(), index)
            self.currentlyLoading = False
            self.updateRuestungen()

    def shouldShowType(typIdx, system):
        for rues in Wolke.DB.rüstungen:
            if Wolke.DB.rüstungen[rues].typ != typIdx:
                continue
            if Wolke.DB.rüstungen[rues].system != 0 and Wolke.DB.rüstungen[rues].system != system:
                continue
            return True
        return False

    def refreshZRSVisibility(self):
        if self.currentlyLoading:
            return
        self.currentlyLoading = True
        zrsWidgets = [self.ui.labelBein, self.ui.labelBauch, self.ui.labelBrust, self.ui.labelLarm, self.ui.labelRarm, self.ui.labelKopf, self.ui.labelPunkte,
                  self.ui.spinGesamtBein, self.ui.spinGesamtBauch, self.ui.spinGesamtBrust, self.ui.spinGesamtLarm, self.ui.spinGesamtRarm, self.ui.spinGesamtKopf, self.ui.spinGesamtPunkte]
        for widget in zrsWidgets:
            widget.setVisible(self.ui.checkZonen.isChecked())

        for typIdx in range(len(self.ruestungsTypen)):
            showType = RSCharakterRuestungWrapper.shouldShowType(typIdx, 2 if self.ui.checkZonen.isChecked() else 1)
            self.labels[typIdx].setVisible(showType)
            self.editRName[typIdx].setVisible(showType)
            self.spinRS[typIdx].setVisible(showType)
            self.spinRS[typIdx].setEnabled(not self.ui.checkZonen.isChecked())
            for j in range(6):
                self.spinZRS[typIdx][j].setVisible(showType and self.ui.checkZonen.isChecked())
            self.spinPunkte[typIdx].setVisible(showType and self.ui.checkZonen.isChecked())
            if self.ruestungsEigenschaften:
                self.editEigenschaften[typIdx].setVisible(showType)
            self.buttons[typIdx].setVisible(showType)

            if not showType:
                self.loadArmorIntoFields(Objekte.Ruestung(), typIdx)

        self.currentlyLoading = False
        self.updateRuestungen()