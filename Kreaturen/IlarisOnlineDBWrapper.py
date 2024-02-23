# -*- coding: utf-8 -*-

from PySide6 import QtCore, QtWidgets, QtGui
from Wolke import Wolke
from Hilfsmethoden import Hilfsmethoden
import sys
from EventBus import EventBus
import os
from EinstellungenWrapper import EinstellungenWrapper
import copy
from Kreaturen import IlarisOnlineDB
from Kreaturen.IlarisOnlineApi import APIClient

TYPEN = ["Alle", "humanoid", "tier", "elementar", "mythen", "fee", "geist", "untot", "daimonid", "daemon"]

class KreaturOnlineDBWrapper(object):
    def __init__(self):
        super().__init__()
        self.kreaturen = []
        #     {"name": "Test", "typ": "humanoid", "author": "ich", "beschreibung": "Testbeschreibung"},
        #     {"name": "Test2", "typ": "tier", "author": "du", "beschreibung": "Testbeschreibung2"},
        #     {"name": "Test3", "typ": "elementar", "author": "wir", "beschreibung": "a Testbeschreibung3"},
        # ]

        
        self.form = QtWidgets.QDialog()
        self.ui = IlarisOnlineDB.Ui_Dialog()
        self.ui.setupUi(self.form)
        self.selected = None  # selected ID from list
        self.kreatur = None  # downloaded full data

        self.progressBar = QtWidgets.QProgressBar(self.form)
        self.progressBar.show()
        self.api = APIClient()
        self.api.request("ilaris/kreatur/", self.kreaturenLoaded)

        self.ui.cbTyp.addItems([t.capitalize() for t in TYPEN])
        self.ui.cbTyp.currentIndexChanged.connect(self.filterChanged)
        self.ui.cbNSC.stateChanged.connect(self.filterChanged)
        self.ui.leSuche.textChanged.connect(self.filterChanged)

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText("Laden")
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setDisabled(True)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText("Abbrechen")

        self.ui.treeKreaturen.itemDoubleClicked.connect(self.form.accept)
        self.ui.treeKreaturen.itemSelectionChanged.connect(self.selectionChanged)
        self.form.setWindowModality(QtCore.Qt.ApplicationModal)
        self.filterChanged()
        self.form.show()
        self.cancel = self.form.exec() != QtWidgets.QDialog.Accepted
        if self.cancel:
            self.selected = None
            self.kreatur = None
        else:
            self.api.request(f"ilaris/kreatur/{self.selected}/", self.kreaturLoaded)
        # if not self.cancel:
        #     self.selected = self.ui.treeKreaturen.currentItem().io_id
            # print(kreatur)

    def selectionChanged(self):
        try:
            self.selected = self.ui.treeKreaturen.currentItem().io_id
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        except AttributeError:
            self.selected = None
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
            # self.ui.treeKreaturen.selectedItems()
        # lambda: self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(len(self.ui.treeKreaturen.selectedItems()) > 0)

    def kreaturLoaded(self, data):
        self.kreatur = data
        self.form.accept()

    def kreaturenLoaded(self, data):
        self.kreaturen = data
        self.progressBar.hide()
        # fill tree
        self.ui.treeKreaturen.clear()
        self.filterChanged()  # updates tree
        # for k in self.filtered()

    def filtered(self, kreaturen, search, typ, nsc):
        if not nsc:
            kreaturen = [k for k in kreaturen if not k.get("nsc", False)]
        if search is not None:
            kreaturen = [k for k in kreaturen if search in k["name"].lower() or search in k.get("kurzbeschreibung", "").lower()]
        if typ != "Alle":
            kreaturen = [k for k in kreaturen if k["typ"] == typ]
        return kreaturen
    
    def filterChanged(self):
        search = self.ui.leSuche.text().lower()
        typ = TYPEN[self.ui.cbTyp.currentIndex()]
        nsc = self.ui.cbNSC.isChecked()
        kreaturen = self.filtered(self.kreaturen, search, typ, nsc)
        self.ui.treeKreaturen.clear()
        for k in kreaturen:
            item = QtWidgets.QTreeWidgetItem(self.ui.treeKreaturen)
            item.setText(0, k["name"])
            item.setText(1, k["typ"].capitalize())
            item.setText(2, k.get("kurzbeschreibung"))
            item.setText(3, str(k.get("author")))
            item.io_id = k["id"]
            self.ui.treeKreaturen.addTopLevelItem(item)