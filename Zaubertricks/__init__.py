from PySide6 import QtWidgets, QtCore, QtGui
import shutil
import os
from EventBus import EventBus
from Wolke import Wolke
from EinstellungenWrapper import EinstellungenWrapper
import copy
import re
from CheatsheetGenerator import CheatsheetGenerator
from Core.DatenbankEinstellung import DatenbankEinstellung
from Hilfsmethoden import Hilfsmethoden

class Plugin:
    def __init__(self):
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)
        EventBus.addFilter("class_uebernatuerlichefertigkeiten_wrapper", self.provideUeberWrapperZaubertricksHook)
        EventBus.addFilter("pdf_export", self.pdfExportZaubertricksHook)
        EventBus.addFilter("pdf_export_extrapage", self.pdfExportZaubertricksHook)

    def changesCharacter(self):
        return False

    def basisDatenbankGeladenHandler(self, params):
        self.db = params["datenbank"]

        e = DatenbankEinstellung()
        e.name = "Zaubertricks Plugin: Aktivieren"
        e.beschreibung = "Hiermit kannst du das Zaubertricks-Plugin nur für diese Hausregeln deaktivieren und es trotzdem allgemein in den Sephrasto-Einstellungen aktiviert lassen."
        e.text = "True"
        e.typ = "Bool"
        self.db.loadElement(e)

    def provideUeberWrapperZaubertricksHook(self, base, params):
        if not self.db.einstellungen["Zaubertricks Plugin: Aktivieren"].wert:
            return base

        class ZTUebernatuerlichWrapper(base):
            def __init__(self):
                super().__init__()

            def load(self):
                super().load()
                self.zauberTricksFW = QtWidgets.QLabel("-")
                self.zauberTricksFW.setAlignment(QtCore.Qt.AlignCenter)
                for row in range(self.ui.tableWidget.rowCount()):
                    widget = self.ui.tableWidget.cellWidget(row, 1)
                    if widget is not None and widget.text() == "Zaubertricks":
                        self.ui.tableWidget.setCellWidget(row,2, self.zauberTricksFW)
                        self.ui.tableWidget.cellWidget(row,3).setText("-")
                        self.ui.tableWidget.cellWidget(row,3).setAlignment(QtCore.Qt.AlignCenter)
                        self.ui.tableWidget.cellWidget(row,4).setText("-")                

            def updateInfo(self):
                self.ui.labelAttribute.setVisible(self.currentFertName != "Zaubertricks")
                self.ui.label.setVisible(self.currentFertName != "Zaubertricks")
                self.ui.label_5.setVisible(self.currentFertName != "Zaubertricks")
                self.ui.label_6.setVisible(self.currentFertName != "Zaubertricks")
                self.ui.label_7.setVisible(self.currentFertName != "Zaubertricks")
                self.ui.label_8.setVisible(self.currentFertName != "Zaubertricks")
                self.ui.spinSF.setVisible(self.currentFertName != "Zaubertricks")
                self.ui.spinBasis.setVisible(self.currentFertName != "Zaubertricks")
                self.ui.spinFW.setVisible(self.currentFertName != "Zaubertricks")
                self.ui.spinPW.setVisible(self.currentFertName != "Zaubertricks")
                self.ui.labelKategorie.setVisible(self.currentFertName != "Zaubertricks")
                self.ui.line.setVisible(self.currentFertName != "Zaubertricks")

                if self.currentFertName == "Zaubertricks":
                    self.currentlyLoading = True
                    fert = Wolke.DB.übernatürlicheFertigkeiten["Zaubertricks"]
                    self.ui.labelFertigkeit.setText(fert.name)
                    self.ui.plainText.setText(Hilfsmethoden.fixHtml(fert.text))
                    self.model.clear()
                    self.updateTalents()
                    self.currentlyLoading = False
                else:
                    super().updateInfo()

        return ZTUebernatuerlichWrapper

    def pdfExportZaubertricksHook(self, fields, params):
        if not self.db.einstellungen["Zaubertricks Plugin: Aktivieren"].wert:
            return fields

        for field in fields:
            if not (field.startswith("Uebertal") and field.endswith("NA")):
                continue

            if fields[field] in Wolke.DB.talente and "Zaubertricks" in Wolke.DB.talente[fields[field]].fertigkeiten:
                fields[field[:-2] + "PW"] = "-"
        return fields