from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from Wolke import Wolke
from Core.DatenbankEinstellung import DatenbankEinstellung
from Core.AbgeleiteterWert import AbgeleiteterWertDefinition

class Plugin:
    def __init__(self):
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)
        EventBus.addAction("datenbank_geladen", self.datenbankGeladenHandler)
        EventBus.addAction("post_charakter_aktualisieren", self.postCharakterAktualisierenHandler)
        EventBus.addAction("charakter_instanziiert", self.charakterInstanziiertHandler)
        EventBus.addFilter("class_inventar_wrapper", self.provideInventarWrapperHook)
        EventBus.addFilter("pdf_export", self.pdfExportHook)
        EventBus.addFilter("charakter_laden", self.charakterLadenHook, 100)
        EventBus.addFilter("charakter_schreiben", self.charakterSchreibenHook, 100)

    @staticmethod
    def getDescription():
        return "Das Plugin setzt die Tragkraft der 'Regeln für Reisen' von Alrik Normalpaktierer um (siehe dsaforum.de). Dazu wird in der Regelbasis ein neuer abgeleiteter Wert 'TK' eingefügt, wodurch die neuen Script-Funktionen 'getTK', 'setTK' und 'modifyTK' zur Verfügung stehen." +\
    "Durch diese kann die Tragkraft mit Vorteilen oder Waffeneigenschaften modifiziert werden.\n.\n" +\
    "Die Tragkraft und der resultierende BE-Modifikator werden in der ersten Inventarzeile angezeigt. Der BE-Modifikator wird nicht(!) bei der BE oder den Waffen eingerechnet. Allen anderen Zeilen kann eine Last zugewiesen werden.\n" +\
    "Mit der Datenbank-Einstellung 'Last BE Script' kann angegeben werden, wie aus Tragkraft und Last der BE-Modifikator berechnet wird."

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
        ab.text = "Die Tragkraft bestimmt, wieviel Last du mit dir führen kannst. Jeder getragene Gegenstand, der über diese Menge hinausgeht, erhöht deine BE um 1, reduziert dein DH also um 2. Fällt dein DH dadurch auf 1, kannst du keinen weiteren Gegenstand transportieren."
        ab.formel = "KK * 2"
        ab.script = "getAttribut('KK')*2"
        ab.finalscript = ""
        ab.sortorder = 60
        self.db.loadElement(ab)

        e = DatenbankEinstellung()
        e.name = "Tragkraft Plugin: Last BE Script"
        e.beschreibung = "Das Pythonscript berechnet den BE-Modifikator durch Tragkraft und Last. Es stehen hierfür die Funktionen getAttribut('Attributsname'), getTK() und getLast() zur Verfügung.\n" +\
           "Letztere liefert einen Int-Array mit den Last-Einträgen der Inventarzeilen zurück (exklusive der ersten Zeile). Der Modifikator muss der Variable 'be' zugewiesen werden."
        e.text = "be = max(sum(getLast()) - getTK(), 0)"
        e.typ = "Exec"
        self.db.loadElement(e)

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

    def postCharakterAktualisierenHandler(self, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].wert:
            return
        char = params["charakter"]

        pb = 0
        if len(char.ausrüstungPlatzbedarf) > 0:
            pb = char.ausrüstungPlatzbedarf[0]

        scriptAPI = {
            'getAttribut' : lambda attribut: char.attribute[attribut].wert,
            'getTK' : lambda: char.abgeleiteteWerte["TK"].wert,
            'getLast' : lambda: char.ausrüstungPlatzbedarf[1:] if len(char.ausrüstungPlatzbedarf) > 1 else [0],
            'be' : 0
        }
        exec(Wolke.DB.einstellungen["Tragkraft Plugin: Last BE Script"].wert, scriptAPI)
        text = f"Tragkraft {char.abgeleiteteWerte['TK'].wert}, Last {pb} -> zusätzliche BE {scriptAPI['be']}"

        if len(char.ausrüstung) == 0:
            char.ausrüstung.append(text)
        elif char.ausrüstung[0].startswith("Tragkraft"):
            char.ausrüstung[0] = text
        else:
            char.ausrüstung.insert(0, text)

        if len(char.ausrüstungPlatzbedarf) == 0:
            char.ausrüstungPlatzbedarf.append(0)

    def pdfExportHook(self, fields, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].wert:
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

    
    def charakterLadenHook(self, deserializer, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].wert:
            return deserializer

        char = params["charakter"]
        if deserializer.find('Objekte'):
            if deserializer.find('Ausrüstung'):
                for tag in deserializer.listTags():
                    char.ausrüstungPlatzbedarf.append(deserializer.getInt('platzbedarf', 0))
                deserializer.end() #ausrüstung
            deserializer.end() #objekte
        return deserializer

    def charakterSchreibenHook(self, serializer, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].wert:
            return root

        char = params["charakter"]
        if serializer.find('Objekte'):
            if serializer.find('Ausrüstung'):
                index = 0
                for tag in serializer.listTags():
                    if index < len(char.ausrüstungPlatzbedarf):
                        serializer.set('platzbedarf', char.ausrüstungPlatzbedarf[index])
                    index += 1
                serializer.end() #ausrüstung
            serializer.end() #objekte
        return serializer

    def provideInventarWrapperHook(self, base, params):
        if not self.db.einstellungen["Tragkraft Plugin: Aktivieren"].wert:
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