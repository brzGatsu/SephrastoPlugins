# -*- coding: utf-8 -*-
from Manoeverkarten import KartenExportDialog
from PySide6 import QtCore, QtWidgets, QtGui
from Wolke import Wolke
from Hilfsmethoden import Hilfsmethoden
from Manoeverkarten import DatenbankEditKarteWrapper
import sys
from EventBus import EventBus
import os
from EinstellungenWrapper import EinstellungenWrapper
from Manoeverkarten.Manoeverkarte import KartenUtility
import copy
from QtUtils.TreeExpansionHelper import TreeExpansionHelper

class KartenExportDialogWrapper(object):
    def __init__(self, isDbExport, datenbank):
        super().__init__()
        self.form = QtWidgets.QDialog()
        self.ui = KartenExportDialog.Ui_Dialog()
        self.ui.setupUi(self.form)

        self.ui.checkOpen.setChecked(Wolke.Settings["Manöverkarten_PDF-Open"])
        self.ui.checkHintergrund.setChecked(Wolke.Settings["Manöverkarten_Hintergrundbild"])
        
        deaktiviert = Wolke.Settings["Manöverkarten_DeaktivierteKategorien"] if isDbExport else Wolke.Char.deaktivierteKartenKategorien
        def createItem(parent, name, cat):
            if isinstance(parent, QtWidgets.QTreeWidgetItem) and parent.text(0) == name:
                parent.setData(0, QtCore.Qt.UserRole, cat)
                if cat in deaktiviert:
                    parent.setCheckState(0, QtCore.Qt.Unchecked)
                return

            item = QtWidgets.QTreeWidgetItem(parent)
            item.setText(0, name)
            item.setData(0, QtCore.Qt.UserRole, cat)
            if cat in deaktiviert:
                item.setCheckState(0, QtCore.Qt.Unchecked)
            else:
                item.setCheckState(0, QtCore.Qt.Checked)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsAutoTristate)

        parent = QtWidgets.QTreeWidgetItem(self.ui.treeCategories)
        root = parent
        parent.setText(0, "Alle Kategorien")
        parent.setExpanded(True)
        parent.setCheckState(0, QtCore.Qt.Checked)
        parent.setFlags(parent.flags() | QtCore.Qt.ItemIsAutoTristate)
        for r in datenbank.einstellungen["Regelanhang: Reihenfolge"].wert:
            if r[0] == "T" and len(r) > 2:
                parent = QtWidgets.QTreeWidgetItem(root)
                parent.setText(0, r[2:])
                parent.setExpanded(True)
                parent.setCheckState(0, QtCore.Qt.Checked)
                parent.setFlags(parent.flags() | QtCore.Qt.ItemIsAutoTristate)
            elif r[0] == "V" and len(r) > 2 and r[2:].isnumeric():
                kategorie = int(r[2:])
                createItem(parent, datenbank.einstellungen["Vorteile: Kategorien"].wert.keyAtIndex(kategorie), r)
            elif r[0] == "R" and len(r) > 2 and r[2:].isnumeric():
                kategorie = int(r[2:])
                createItem(parent, datenbank.einstellungen["Regeln: Kategorien"].wert.keyAtIndex(kategorie), r)
            elif r[0] == "W":
                createItem(parent, "Waffeneigenschaften", r)
            elif r[0] == "S" and len(r) > 2 and r[2:].isnumeric():
                kategorie = int(r[2:])
                createItem(parent, datenbank.einstellungen["Talente: Kategorien"].wert.keyAtIndex(kategorie), r)
            else:
                name = EventBus.applyFilter("regelanhang_reihenfolge_name", r)
                createItem(parent, name, r)

        benutzerdefiniert = KartenUtility.getBenutzerdefinierteTypen(datenbank)
        if len(benutzerdefiniert) > 0:
            parent = QtWidgets.QTreeWidgetItem(root)
            parent.setText(0, "Benutzerdefiniert")
            parent.setExpanded(True)
            parent.setCheckState(0, QtCore.Qt.Checked)
            parent.setFlags(parent.flags() | QtCore.Qt.ItemIsAutoTristate)
            for b in KartenUtility.getBenutzerdefinierteTypen(datenbank):
                createItem(parent, b, "B:"+b)

        self.ui.treeCategories.setHeaderHidden(True)
        self.ui.treeCategories.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)

        self.ui.comboFormat.currentIndexChanged.connect(self.formatChanged)
        self.ui.checkEinzeln.stateChanged.connect(self.einzelnExportChanged)
        self.einzelnExportChanged()

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText("Exportieren")

        self.expansionHelper = TreeExpansionHelper(self.ui.treeCategories, self.ui.buttonExpandToggle, True)

        self.form.setWindowModality(QtCore.Qt.ApplicationModal)
        self.form.show()
        self.cancel = self.form.exec() != QtWidgets.QDialog.Accepted
        if not self.cancel:
            Wolke.Settings["Manöverkarten_PDF-Open"] = self.ui.checkOpen.isChecked()
            Wolke.Settings["Manöverkarten_Hintergrundbild"] = self.ui.checkHintergrund.isChecked()
            self.einzelExport = self.ui.checkEinzeln.isChecked()
            self.nameFormat = self.ui.leNameFormat.text()
            self.bilderExport = self.ui.comboFormat.currentIndex() == 1
            self.deaktivierteKategorien = []
            for i in range(root.childCount()):
                parent = root.child(i)
                if parent.data(0, QtCore.Qt.UserRole) is not None and parent.checkState(0) == QtCore.Qt.Unchecked:
                    self.deaktivierteKategorien.append(parent.data(0, QtCore.Qt.UserRole))
                for j in range(parent.childCount()):
                    child = parent.child(j)
                    if child.checkState(0) == QtCore.Qt.Unchecked:
                        self.deaktivierteKategorien.append(child.data(0, QtCore.Qt.UserRole))
            if isDbExport:
                Wolke.Settings["Manöverkarten_DeaktivierteKategorien"] = self.deaktivierteKategorien
            else:
                Wolke.Char.deaktivierteKartenKategorien = self.deaktivierteKategorien
            EinstellungenWrapper.save()

    def formatChanged(self):
        self.ui.checkEinzeln.setEnabled(self.ui.comboFormat.currentIndex() == 0)
        if self.ui.comboFormat.currentIndex() == 1:
            self.ui.checkEinzeln.setChecked(True)

    def einzelnExportChanged(self):
        self.ui.labelNameFormat.setVisible(self.ui.checkEinzeln.isChecked())
        self.ui.leNameFormat.setVisible(self.ui.checkEinzeln.isChecked())