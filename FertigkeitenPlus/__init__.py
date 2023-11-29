from EventBus import EventBus
from Wolke import Wolke
import os
from PySide6 import QtWidgets, QtCore

class Plugin:
    def __init__(self):
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHook)
        EventBus.addFilter("dbe_class_fertigkeitdefinition_wrapper", self.dbeClassFertigkeitFilter)
        EventBus.addFilter("dbe_class_ueberfertigkeitdefinition_wrapper", self.dbeClassFertigkeitFilter)

    @staticmethod
    def getDescription():
        return "Dieses Plugin bietet bei Fertigkeiten die Möglichkeit, ein viertes Attribut anzugeben.\n"\
        "Berechnungen für den Basiswert verwenden dann nur die 3 höchsten Attribute (siehe angepasste Einstellung \"Fertigkeiten: BW Script\")."

    def changesCharacter(self):
        return True

    def changesDatabase(self):
        return True

    def basisDatenbankGeladenHook(self, params):
        self.db = params["datenbank"]

        dbe = self.db.einstellungen["Fertigkeiten: BW Script"]
        dbe.text = "int(sum(sorted(getAttribute(), reverse=True)[:3])/3+0.5)"

    def dbeClassFertigkeitFilter(self, editorType, params):
        class DatenbankEditFertigkeitWrapperPlus(editorType):
            def __init__(self, datenbank, fertigkeit=None, readonly=False):
                super().__init__(datenbank, fertigkeit, readonly)

            def load(self, fertigkeit):
                super().load(fertigkeit)

                if not hasattr(self.ui, "comboAttribut4"):
                    self.ui.comboAttribut4Separator = QtWidgets.QLabel()
                    self.ui.comboAttribut4Separator.setText(" Optional:")
                    self.ui.comboAttribut4 = QtWidgets.QComboBox()
                    self.ui.comboAttribut4.setMinimumSize(QtCore.QSize(45, 0))
                    self.ui.horizontalLayout.insertWidget(5, self.ui.comboAttribut4Separator)
                    self.ui.horizontalLayout.insertWidget(6, self.ui.comboAttribut4)

                attribute = [a.name for a in sorted(self.datenbank.attribute.values(), key=lambda value: value.sortorder)]
                self.ui.comboAttribut4.addItems(["-"] + attribute)
                if len(fertigkeit.attribute) >= 4:
                    self.ui.comboAttribut4.setCurrentText(fertigkeit.attribute[3])

            def update(self, fertigkeit):
                super().update(fertigkeit)
                if self.ui.comboAttribut4.currentText() == "-":
                    if len(fertigkeit.attribute) >= 4:
                        fertigkeit.attribute.pop()
                else:
                    if len(fertigkeit.attribute) < 4:
                        fertigkeit.attribute.append(self.ui.comboAttribut4.currentText())
                    else:
                        fertigkeit.attribute[3] = self.ui.comboAttribut4.currentText()

        return DatenbankEditFertigkeitWrapperPlus

    def dbeClassUeberFertigkeitFilter(self, editorType):
        return editorType

