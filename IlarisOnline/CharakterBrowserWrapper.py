# -*- coding: utf-8 -*-

from PySide6 import QtCore, QtWidgets, QtGui
from Wolke import Wolke
from Hilfsmethoden import Hilfsmethoden
import sys
from EventBus import EventBus
import os
from EinstellungenWrapper import EinstellungenWrapper
import copy
from IlarisOnline import CharakterBrowser
from IlarisOnline.IlarisOnlineApi import APIClient


class CharakterBrowserWrapper(object):
    def __init__(self):
        super().__init__()
        self.charaktere = []

        
        self.form = QtWidgets.QDialog()
        self.ui = CharakterBrowser.Ui_Dialog()
        self.ui.setupUi(self.form)
        self.selected = None  # selected ID from list
        self.charakter = None  # downloaded full data

        self.progressBar = QtWidgets.QProgressBar(self.form)
        self.progressBar.show()
        self.api_token = Wolke.Settings["IO_APIToken"]
        self.api = APIClient(self.api_token)
        self.api.request("ilaris/charakter/", self.charaktereLoaded)

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText("Laden")
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setDisabled(True)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText("Abbrechen")

        self.ui.treeCharaktere.itemDoubleClicked.connect(self.form.accept)
        self.ui.treeCharaktere.itemSelectionChanged.connect(self.selectionChanged)
        self.form.setWindowModality(QtCore.Qt.ApplicationModal)
        self.filterChanged()
        self.form.show()
        self.cancel = self.form.exec() != QtWidgets.QDialog.Accepted
        if self.cancel:
            self.selected = None
            self.charakter = None
        else:
            self.api.request(f"ilaris/charakter/{self.selected}/", self.charakterLoaded)

    def selectionChanged(self):
        try:
            self.selected = self.ui.treeCharaktere.currentItem().io_id
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        except AttributeError:
            self.selected = None
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
            # self.ui.treeCharaktere.selectedItems()
        # lambda: self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(len(self.ui.treeCharaktere.selectedItems()) > 0)


    def charakterLoaded(self, data, error=None, status=None):
        if error:
            error_dia = QtWidgets.QMessageBox.critical(self.form, "Fehler", "API Request fehlgeschlagen")
        self.charakter = data
        self.form.accept()

    def charaktereLoaded(self, data, error=None, status=None):
        if error:
            error_dia = QtWidgets.QMessageBox.critical(self.form, "Fehler", "API Request fehlgeschlagen")
        self.charaktere = data
        self.progressBar.hide()
        # fill tree
        self.ui.treeCharaktere.clear()
        self.filterChanged()  # updates tree
        # for k in self.filtered()

    def filtered(self, chars, search):
        # if not nsc:
        #     charaktere = [k for k in charaktere if not k.get("nsc", False)]
        # if search is not None:
        #     charaktere = [k for k in charaktere if search in k["name"].lower() or search in k.get("kurzbeschreibung", "").lower()]
        # if typ != "Alle":
        #     charaktere = [k for k in charaktere if k["typ"] == typ]
        return chars
    
    def filterChanged(self):
        search = self.ui.leSuche.text().lower()
        chars = self.filtered(self.charaktere, search)
        self.ui.treeCharaktere.clear()
        for k in chars:
            item = QtWidgets.QTreeWidgetItem(self.ui.treeCharaktere)
            item.setText(0, k["name"])
            # item.setText(1, k["typ"].capitalize())
            item.setText(2, k.get("kurzbeschreibung"))
            item.setText(3, str(k.get("author")))
            item.io_id = k["id"]
            self.ui.treeCharaktere.addTopLevelItem(item)