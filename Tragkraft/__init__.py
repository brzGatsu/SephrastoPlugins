from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from Wolke import Wolke
from Core.DatenbankEinstellung import DatenbankEinstellung
from Core.AbgeleiteterWert import AbgeleiteterWertDefinition
from Hilfsmethoden import Hilfsmethoden

class Plugin:
    def __init__(self):
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)
        EventBus.addAction("datenbank_geladen", self.datenbankGeladenHandler)
        EventBus.addAction("charakter_instanziiert", self.charakterInstanziiertHandler)
        EventBus.addFilter("class_inventar_wrapper", self.provideInventarWrapperHook)
        EventBus.addFilter("pdf_export", self.pdfExportHook)
        EventBus.addAction("charakter_deserialisiert", self.charakterDeserialisiertHandler, 100)
        EventBus.addAction("charakter_serialisiert", self.charakterSerialisiertHandler, 100)

    def changesCharacter(self):
        return self.db.einstellungen["Tragkraft Plugin: Aktivieren"].wert

    def basisDatenbankGeladenHandler(self, params):
        self.db = params["datenbank"]

        e = DatenbankEinstellung()
        e.name = "Tragkraft Plugin: Aktivieren"
        e.beschreibung = "Hiermit kannst du das Tragkraft-Plugin nur für diese Hausregeln deaktivieren und es trotzdem allgemein in den Sephrasto-Einstellungen aktiviert lassen."
        e.text = "True"
        e.typ = "Bool"
        self.db.loadElement(e)

        ab = AbgeleiteterWertDefinition()
        ab.name = "TK"
        ab.anzeigename = "Tragkraft"
        ab.text = "Du kannst Gegenstände mit einer Last von bis zu deiner Tragkraft über weite Strecken transportieren. Sie beträgt wenigstens 2."
        ab.formel = "KK + KO"
        ab.script = "max(getAttribut('KK') + getAttribut('KO'), 2)"
        ab.finalscript = ""
        ab.sortorder = 60
        self.db.loadElement(ab)

    def datenbankGeladenHandler(self, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].wert and params["isCharakterEditor"]:
            self.db.referenceDB[AbgeleiteterWertDefinition].pop("TK")
            if "TK" in self.db.abgeleiteteWerte:
                self.db.abgeleiteteWerte.pop("TK")

    def charakterInstanziiertHandler(self, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].wert:
            return
        char = params["charakter"]
        char.ausrüstungPlatzbedarf = []

    def pdfExportHook(self, fields, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].wert:
            return fields

        for i in range(len(Wolke.Char.ausrüstung)):
            field = 'Ausruestung' + str(i+1)
            if field not in fields or not fields[field].strip():
                continue
            if len(Wolke.Char.ausrüstungPlatzbedarf) <= i:
                break
            fields[field] += " (Last " + str(Wolke.Char.ausrüstungPlatzbedarf[i]) + ")"

        return fields

    
    def charakterDeserialisiertHandler(self, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].wert:
            return

        char = params["charakter"]
        deserializer = params["deserializer"]
        if deserializer.find('Objekte'):
            if deserializer.find('Ausrüstung'):
                for tag in deserializer.listTags():
                    char.ausrüstungPlatzbedarf.append(deserializer.getInt('platzbedarf', 0))
                deserializer.end() #ausrüstung
            deserializer.end() #objekte

    def charakterSerialisiertHandler(self, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].wert:
            return

        char = params["charakter"]
        serializer = params["serializer"]
        if serializer.find('Objekte'):
            if serializer.find('Ausrüstung'):
                index = 0
                for tag in serializer.listTags():
                    if index < len(char.ausrüstungPlatzbedarf):
                        serializer.set('platzbedarf', char.ausrüstungPlatzbedarf[index])
                    index += 1
                serializer.end() #ausrüstung
            serializer.end() #objekte

    def provideInventarWrapperHook(self, base, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].wert:
            return base

        class TKInventarWrapper(base):
            def __init__(self):
                super().__init__()

                self.tkSpin = []

                rowCount = 0
                colCount = 0
                
                for i in range(20):
                    lineEdit = self.ui.gridLayout_2.itemAtPosition(rowCount, colCount).widget()
                    spin = QtWidgets.QSpinBox()
                    spin.setMinimum(0)
                    spin.setAlignment(QtCore.Qt.AlignCenter)
                    spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
                    spin.valueChanged.connect(self.updatePlatzbedarf)
                    spin.setMaximum(99)
                    self.ui.gridLayout_2.addWidget(lineEdit, rowCount + 1, 0 if colCount == 0 else 2, 1, 1)
                    self.ui.gridLayout_2.addWidget(spin, rowCount + 1, 1 if colCount == 0 else 3, 1, 1)
                    self.tkSpin.append(spin)
                    
                    colCount = 1 if i % 2 == 0 else 0
                    if colCount == 0:
                        rowCount += 1

                    if len(self.tkSpin) > 1:
                        self.form.setTabOrder(self.tkSpin[-2], lineEdit)
                    self.form.setTabOrder(lineEdit, spin)

                self.label1 = QtWidgets.QLabel("Gegenstand")
                self.label1.setProperty("class", "h4")
                self.ui.gridLayout_2.addWidget(self.label1, 0, 0, 1, 1)
                self.label2 = QtWidgets.QLabel("Last")
                self.label2.setProperty("class", "h4")
                self.ui.gridLayout_2.addWidget(self.label2, 0, 1, 1, 1)
                self.label3 = QtWidgets.QLabel("Gegenstand")
                self.label3.setProperty("class", "h4")
                self.ui.gridLayout_2.addWidget(self.label3, 0, 2, 1, 1)
                self.label4 = QtWidgets.QLabel("Last")
                self.label4.setProperty("class", "h4")
                self.ui.gridLayout_2.addWidget(self.label4, 0, 3, 1, 1)

            def load(self):
                super().load()
                self.currentlyLoading = True
                self.updateTKSpinner()
                for i in range(len(Wolke.Char.ausrüstungPlatzbedarf)):
                    self.tkSpin[i].setValue(Wolke.Char.ausrüstungPlatzbedarf[i])
                self.currentlyLoading = False

            def updatePlatzbedarf(self):
                if self.currentlyLoading:
                    return
                Wolke.Char.ausrüstungPlatzbedarf = []
                for spin in self.tkSpin:
                    Wolke.Char.ausrüstungPlatzbedarf.append(spin.value())

                self.modified.emit()

            def updateInventory(self):
                super().updateInventory()
                self.updateTKSpinner()
                while len(Wolke.Char.ausrüstungPlatzbedarf) < len(Wolke.Char.ausrüstung):
                    Wolke.Char.ausrüstungPlatzbedarf.append(0)

            def updateTKSpinner(self):
                for i in range(20):
                    if i < len(Wolke.Char.ausrüstung) and Wolke.Char.ausrüstung[i]:
                        self.tkSpin[i].setEnabled(True)
                    else:
                        self.tkSpin[i].setEnabled(False)
                        self.tkSpin[i].setValue(0)

        return TKInventarWrapper
