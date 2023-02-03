from PySide6 import QtWidgets, QtCore, QtGui
import lxml.etree as etree
from EventBus import EventBus
from Wolke import Wolke
from DatenbankEinstellung import DatenbankEinstellung
import Objekte

class Plugin:
    def __init__(self):
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)
        EventBus.addAction("charakter_aktualisieren_vorteilscripts", self.charakterAktualisierenVorteileHandler)
        EventBus.addAction("post_charakter_aktualisieren", self.postCharakterAktualisierenHandler)
        EventBus.addAction("charakter_instanziiert", self.charakterInstanziiertHandler)
        EventBus.addFilter("class_inventar_wrapper", self.provideInventarWrapperHook)
        EventBus.addFilter("pdf_export", self.pdfExportHook)
        EventBus.addFilter("charakter_xml_laden", self.charakterXmlLadenHook, 100)
        EventBus.addFilter("charakter_xml_schreiben", self.charakterXmlSchreibenHook, 100)

    @staticmethod
    def getDescription():
        return "Das Plugin setzt die Tragkraft der 'Regeln für Reisen' von Alrik Normalpaktierer um (siehe dsaforum.de). Die Formel zur Berechnung dieser kann in der Datenbank-Einstellung 'Basis TK Script' gefunden werden.\n" +\
    "Die Tragkraft und der resultierende BE-Modifikator werden in der ersten Inventarzeile angezeigt. Der BE-Modifikator wird nicht(!) bei der BE oder den Waffen eingerechnet. Allen anderen Zeilen kann eine Last zugewiesen werden.\n" +\
    "Zudem stehen die neuen Script-Funktionen 'getTK', 'setTK' und 'modifyTK' zur Verfügung, um die Tragkraft mit Vorteilen oder Waffeneigenschaften zu modifizieren.\n" +\
    "Mit der Datenbank-Einstellung 'Last BE Script' kann angegeben werden, wie aus Tragkraft und Last der BE-Modifikator berechnet wird."

    def changesCharacter(self):
        return self.db.einstellungen["Tragkraft Plugin: Aktivieren"].toBool()

    def basisDatenbankGeladenHandler(self, params):
        self.db = params["datenbank"]

        e = DatenbankEinstellung()
        e.name = "Tragkraft Plugin: Aktivieren"
        e.beschreibung = "Hiermit kannst du das Tragkraft-Plugin nur für diese Hausregeln deaktivieren und es trotzdem allgemein in den Sephrasto-Einstellungen aktiviert lassen."
        e.wert = "True"
        e.typ = "Bool"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "Tragkraft Plugin: Basis TK Script"
        e.beschreibung = "Das Pythonscript berechnet die Basis-Tragkraft. Es steht hierfür die Funktion getAttribut('Attributsname') zur Verfügung."
        e.wert = "getAttribut('KK')*2"
        e.typ = "Text"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "Tragkraft Plugin: Last BE Script"
        e.beschreibung = "Das Pythonscript berechnet den BE-Modifikator durch Tragkraft und Last. Es stehen hierfür die Funktionen getAttribut('Attributsname'), getTK() und getLast() zur Verfügung.\n" +\
           "Letztere liefert einen Int-Array mit den Last-Einträgen der Inventarzeilen zurück (exklusive der ersten Zeile). Der Modifikator muss der Variable 'be' zugewiesen werden."
        e.wert = "be = max(sum(getLast()) - getTK(), 0)"
        e.typ = "Text"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

    def charakterInstanziiertHandler(self, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].toBool():
            return
        char = params["charakter"]
        char.tk = 0
        char.ausrüstungPlatzbedarf = []
        char.charakterScriptAPI["getTK"] = lambda: char.tk
        char.charakterScriptAPI["setTK"] = lambda tk: setattr(char, 'tk', tk)
        char.charakterScriptAPI["modifyTK"] = lambda tk: setattr(char, 'tk', char.tk + tk)

    def charakterAktualisierenVorteileHandler(self, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].toBool():
            return
        char = params["charakter"]

        scriptAPI = { 'getAttribut' : lambda attribut: char.attribute[attribut].wert }
        char.tk = eval(Wolke.DB.einstellungen["Tragkraft Plugin: Basis TK Script"].toText(), scriptAPI)

    def postCharakterAktualisierenHandler(self, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].toBool():
            return
        char = params["charakter"]

        pb = 0
        if len(Wolke.Char.ausrüstungPlatzbedarf) > 0:
            pb = Wolke.Char.ausrüstungPlatzbedarf[0]

        scriptAPI = {
            'getAttribut' : lambda attribut: char.attribute[attribut].wert,
            'getTK' : lambda: char.tk,
            'getLast' : lambda: char.ausrüstungPlatzbedarf[1:] if len(char.ausrüstungPlatzbedarf) > 1 else [0],
            'be' : 0
        }
        exec(Wolke.DB.einstellungen["Tragkraft Plugin: Last BE Script"].toText(), scriptAPI)
        text = f"Tragkraft {char.tk}, Last {pb} -> zusätzliche BE {scriptAPI['be']}"

        if len(char.ausrüstung) == 0:
            char.ausrüstung.append(text)
        elif char.ausrüstung[0].startswith("Tragkraft"):
            char.ausrüstung[0] = text
        else:
            char.ausrüstung.insert(0, text)

        if len(char.ausrüstungPlatzbedarf) == 0:
            char.ausrüstungPlatzbedarf.append(0)

    def pdfExportHook(self, fields, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].toBool():
            return fields
        count = 1
        countl = 1
        countr = 11
        for i in range(len(Wolke.Char.ausrüstung)):
            if count % 2 != 0:
                index = countl
                countl += 1
            else:
                index = countr
                countr += 1
            if i == 0:
                pass
            elif len(Wolke.Char.ausrüstungPlatzbedarf) > i and Wolke.Char.ausrüstungPlatzbedarf[i] > 0:
                fields['Ausruestung' + str(index)] += " (Last " + str(Wolke.Char.ausrüstungPlatzbedarf[i]) + ")"
            if count >= 20:
                break
            count += 1
        return fields

    
    def charakterXmlLadenHook(self, root, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].toBool():
            return root

        objekte = root.find('Objekte')
        if objekte is None:
            return root

        char = params["charakter"]

        for aus in objekte.findall('Ausrüstung/Ausrüstungsstück'):
            if aus.get('platzbedarf'):
                char.ausrüstungPlatzbedarf.append(int(aus.get('platzbedarf')))
            else:
                char.ausrüstungPlatzbedarf.append(0)

        return root

    def charakterXmlSchreibenHook(self, root, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].toBool():
            return root

        objekte = root.find('Objekte')
        if objekte is None:
            return root

        char = params["charakter"]
        index = 0
        for aus in objekte.findall('Ausrüstung/Ausrüstungsstück'):
            if index < len(char.ausrüstungPlatzbedarf):
                aus.set('platzbedarf', str(char.ausrüstungPlatzbedarf[index]))
            index += 1
        return root

    def provideInventarWrapperHook(self, base, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].toBool():
            return base

        class TKInventarWrapper(base):
            def __init__(self):
                super().__init__()

                self.tkSpin = []

                rowCount = 0
                colCount = 0
                self.leTK = None
                
                for i in range(20):
                    lineEdit = self.ui.gridLayout_2.itemAtPosition(rowCount, colCount).widget()
                    spin = QtWidgets.QSpinBox()
                    spin.setMinimum(0)
                    spin.setAlignment(QtCore.Qt.AlignCenter)
                    if i == 0:
                        self.leTK = lineEdit
                        spin.setReadOnly(True)
                        spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
                        lineEdit.setReadOnly(True)
                        spin.setMaximum(999)
                    else:
                        spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
                        spin.valueChanged.connect(self.updatePlatzbedarf)
                        spin.setMaximum(32)
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
                for spin in self.tkSpin[1:]:
                    Wolke.Char.ausrüstungPlatzbedarf.append(spin.value())
                self.tkSpin[0].setValue(sum(Wolke.Char.ausrüstungPlatzbedarf))
                Wolke.Char.ausrüstungPlatzbedarf.insert(0, self.tkSpin[0].value())

                self.modified.emit()
                if len(Wolke.Char.ausrüstung) > 0:
                    self.leTK.setText(Wolke.Char.ausrüstung[0])

            def updateInventory(self):
                super().updateInventory()
                self.updateTKSpinner()
                while len(Wolke.Char.ausrüstungPlatzbedarf) < len(Wolke.Char.ausrüstung):
                    Wolke.Char.ausrüstungPlatzbedarf.append(0)

            def updateTKSpinner(self):
                for i in range(1,20):
                    if i < len(Wolke.Char.ausrüstung) and Wolke.Char.ausrüstung[i]:
                        self.tkSpin[i].setEnabled(True)
                    else:
                        self.tkSpin[i].setEnabled(False)
                        self.tkSpin[i].setValue(0)

        return TKInventarWrapper