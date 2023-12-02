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
from Core.Waffeneigenschaft import Waffeneigenschaft
from Hilfsmethoden import Hilfsmethoden
from Core.Waffe import WaffeDefinition, Waffe

# Add dynamic properties to WaffeDefinition and Waffe that work exactly like the implementation of "wm"
# The only difference is that WaffeDefinition returns wm if wmVt was never set.
WaffeDefinition.wmVt = property(lambda self: self._wmVt if hasattr(self, "_wmVt") else self.wm).setter(lambda self, v: setattr(self, "_wmVt", v))
Waffe.wmVt = property(lambda self: self._wmVtOverride if hasattr(self, "_wmVtOverride") else self.definition.wmVt).setter(lambda self, v: setattr(self, "_wmVtOverride", v))

class Plugin:
    def __init__(self):
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)
        EventBus.addFilter("class_waffen_wrapper", self.provideWaffenWrapperHook)
        EventBus.addFilter("class_waffenpicker_wrapper", self.provideWaffenPickerWrapperHook)
        EventBus.addFilter("pdf_export", self.pdfExportWaffenHook)
        EventBus.addFilter("dbe_class_waffedefinition_wrapper", self.dbeClassWaffeFilter)
        EventBus.addAction("waffedefinition_serialisiert", self.waffedefinitionSerialisiertHandler)
        EventBus.addAction("waffedefinition_deserialisiert", self.waffedefinitionDeserialisiertHandler)
        EventBus.addAction("waffe_serialisiert", self.waffeSerialisiertHandler)
        EventBus.addAction("waffe_deserialisiert", self.waffeDeserialisiertHandler)

    @staticmethod
    def getDescription():
        return "Dieses Plugin schafft einige Anpassungsmöglichkeiten für Waffen:\n\n" +\
            "- Zeigt im Waffen-Tab ein VT-WM Feld an. Waffen in der Datenbank kann die Eigenschaft Unhandlich(X) gegeben werden, wobei X von der VT abgezogen wird. Beispiel: ein WM von 2 und Unhandlich (3) bedeutet einen Gesamt-WM von 2/-1.\n" +\
            "- Optionale Waffeneigenschaften, die mit '(*)' am Ende des Namens markiert werden; Beispiel: die Streitaxt erhält die Eigenschaft Rüstungsbrechend (*). Diese Markierung muss im Charaktereditor entfernt werden, ansonsten wird die Eigenschaft nicht auf dem Charakterbogen ausgegeben.\n" +\
            "- In den Hausregeln können bestimmte Waffeneigenschaften via 'WaffenPlus Plugin: Waffeneigenschaften Gruppieren' in der PDF separat gruppiert werden.\n" +\
            "Diese Features können in den Hausregeln über diverse 'WaffenPlus Plugin' Einstellungen deaktiviert werden."

    def changesCharacter(self):
        return self.db.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert

    def changesDatabase(self):
        return self.db.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert

    def basisDatenbankGeladenHandler(self, params):
        self.db = params["datenbank"]

        e = DatenbankEinstellung()
        e.name = "WaffenPlus Plugin: Separater VT-WM"
        e.beschreibung = "Zeigt im Waffen-Tab und im Datenbank-Waffeneditor ein VT-WM Feld an. Achtung: Wenn du diese Option deaktivierst, verlieren alle Waffen den VT-WM Wert, den du eventuell bereits angegeben hast."
        e.text = "True"
        e.typ = "Bool"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "WaffenPlus Plugin: Optionale Waffeneigenschaften"
        e.beschreibung = "Die Idee hinter optionalen Waffeneigenschaften ist, dass es verschiedene (unterschiedlich teure) Versionen derselben Waffe geben kann. " +\
        "Diese werden mit '(*)' am Ende des Namens markiert; Beispiel: die Streitaxt erhält die Eigenschaft Rüstungsbrechend (*). Diese Markierung muss im Charaktereditor entfernt werden, ansonsten wird die Eigenschaft nicht auf dem Charakterbogen ausgegeben."
        e.text = "True"
        e.typ = "Bool"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "WaffenPlus Plugin: Waffeneigenschaften Gruppieren"
        e.beschreibung = "Hier kann eine kommaseparierte Liste von Waffeneigenschaften angegeben werden, die im Charakterbogen separat gruppiert werden sollen."
        e.text = ""
        e.typ = "TextList"
        self.db.loadElement(e)

        e = self.db.einstellungen["Waffen: Waffenwerte Script"]
        e.text = """waffe = getWaffe()
kampfstil = getKampfstil()
be = max(getBEBySlot(waffe.beSlot) + kampfstil.be, 0)
at = getPW() + kampfstil.at + waffe.wm - be
vt = getPW() + kampfstil.vt + waffe.wmVt - be
sb = getSB() if waffe.fertigkeit not in ["Schusswaffen"] else 0
plus = waffe.plus + kampfstil.plus + sb
rw = getWaffe().rw + getKampfstil().rw
setWaffenwerte(at, vt, plus, rw)"""
    
    def waffedefinitionSerialisiertHandler(self, params):
        if not self.db.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
            return
        ser = params["serializer"]
        waffe = params["object"]
        ser.set("wmVt", waffe.wmVt)

    def waffedefinitionDeserialisiertHandler(self, params):
        ser = params["deserializer"]
        waffe = params["object"]
        waffe.wmVt = ser.getInt("wmVt", waffe.wm)

    def waffeSerialisiertHandler(self, params):
        if not self.db.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
            return
        ser = params["serializer"]
        waffe = params["object"]
        ser.set("wmVt", waffe.wmVt)

    def waffeDeserialisiertHandler(self, params):
        ser = params["deserializer"]
        waffe = params["object"]
        waffe.wmVt = ser.getInt("wmVt", waffe.wm)

    ############################
    # Charaktereditor
    ############################

    def provideWaffenWrapperHook(self, base, params):
        if not self.db.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
            return base

        class IAWaffenWrapper(base):
            def __init__(self):
                super().__init__()
                self.ui.labelWM.setText("WM AT/VT")
                self.spinWM2 = []
                self.spinWM2Layout = []
                for i in range(8):
                    spin = QtWidgets.QSpinBox()
                    spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
                    spin.valueChanged.connect(self.updateWaffen)
                    spin.setMinimum(-99)
                    spin.setMaximum(99)

                    layout = QtWidgets.QHBoxLayout()
                    widgetItem = self.ui.Waffen.itemAtPosition(3 + i*4, 4)
                    layout.addWidget(widgetItem.widget())
                    layout.addWidget(QtWidgets.QLabel(" / "))
                    layout.addWidget(spin)
                    self.ui.Waffen.addLayout(layout, 3 + i*4, 4, 1, 1)
                    self.spinWM2.append(spin)
                    self.spinWM2Layout.append(layout)

                    self.form.setTabOrder(self.spinWM[i], spin)
                    self.form.setTabOrder(spin, self.spinLZ[i])

            def loadWeaponIntoFields(self, W, index):
                super().loadWeaponIntoFields(W, index)
                isEmpty = W.name == ""
                vtVerboten = W.isVTVerboten(Wolke.DB)
                self.spinWM2[index].setEnabled(not isEmpty and not vtVerboten)
                if vtVerboten:
                    self.spinWM2[index].setValue(0)
                else:
                    self.spinWM2[index].setValue(W.wmVt)

            def createWaffe(self, index):
                W = super().createWaffe(index)
                W.wmVt = self.spinWM2[index].value()
                return W

            def diffWaffeDefinition(self, waffe):
                diff = []
                würfelDiff = waffe.würfel - waffe.definition.würfel
                plusDiff = waffe.plus - waffe.definition.plus

                härteDiff = waffe.härte - waffe.definition.härte
                waffenHärteWSStern = Wolke.DB.einstellungen["Waffen: Härte WSStern"].wert
                if waffe.definition.name in waffenHärteWSStern:
                    härteDiff = 0

                atWMDiff = waffe.wm - waffe.definition.wm
                vtWMDiff = waffe.wmVt - waffe.definition.wmVt
                rwDiff = waffe.rw - waffe.definition.rw
                lzDiff = 0
                if waffe.fernkampf:
                    lzDiff = waffe.lz - waffe.definition.lz

                def rchop(s, suffix):
                    if suffix and s.endswith(suffix):
                        return s[:-len(suffix)]
                    return s

                w1Eig = [rchop(eig, "(*)").strip() for eig in waffe.eigenschaften]
                w2Eig = [rchop(eig, "(*)").strip() for eig in waffe.definition.eigenschaften]
                eigPlusDiff = list(set(w1Eig) - set(w2Eig))
                eigMinusDiff = list(set(w2Eig) - set(w1Eig))

                if würfelDiff != 0:
                    diff.append("TP " + ("+" if würfelDiff >= 0 else "") + str(würfelDiff) + "W" + str(waffe.würfelSeiten))
                if plusDiff != 0:
                    tmp = ("+" if plusDiff >= 0 else "") + str(plusDiff)
                    if würfelDiff != 0:
                        diff[0] += tmp
                    else:
                        diff.append("TP " + tmp)
                if rwDiff != 0:
                    diff.append("RW " + ("+" if rwDiff >= 0 else "") + str(rwDiff))
                if atWMDiff != 0 or vtWMDiff != 0:
                    diff.append("WM ")
                    if waffe.isATVerboten(Wolke.DB):
                        diff[-1] += "-"
                    else:
                        diff[-1] += ("+" if atWMDiff >= 0 else "") + str(atWMDiff)
                    if waffe.isVTVerboten(Wolke.DB):
                        diff[-1] += "/-"
                    else:
                        diff[-1] += "/" + ("+" if vtWMDiff >= 0 else "") + str(vtWMDiff)
                if lzDiff != 0:
                    diff.append("LZ " + ("+" if lzDiff >= 0 else "") + str(lzDiff))
                if härteDiff != 0:
                    diff.append("Härte " + ("+" if härteDiff >= 0 else "") + str(härteDiff))
                if len(eigPlusDiff) > 0:
                    diff.append(f"<span style='{Wolke.FontAwesomeCSS}'>\u002b</span>&nbsp;&nbsp;" + ", ".join(eigPlusDiff))
                if len(eigMinusDiff) > 0:
                    if len(eigPlusDiff) > 0:
                        diff[-1] += f"&nbsp;&nbsp;<span style='{Wolke.FontAwesomeCSS}'>\uf068</span>&nbsp;&nbsp;" + ", ".join(eigMinusDiff)
                    else:
                        diff.append(f"<span style='{Wolke.FontAwesomeCSS}'>\uf068</span>&nbsp;&nbsp;" + ", ".join(eigMinusDiff))
                return diff

        return IAWaffenWrapper

    def provideWaffenPickerWrapperHook(self, base, params):
        if not self.db.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
            return base
        class IAWaffenPicker(base):
            def __init__(self, W = None):
                super().__init__(W)

            def updateInfo(self):
                self.ui.labelWM_Text.setText("Waffenmodifikator AT/VT")
                super().updateInfo()
                if self.current == "":
                    return
                W = Wolke.DB.waffen[self.current]
                wmAT = ("+" if W.wm > 0 else "") + str(W.wm)
                wmVT = ("+" if W.wmVt > 0 else "") + str(W.wmVt)

                if W.isATVerboten(Wolke.DB):
                    wmAT = "-"
                if W.isVTVerboten(Wolke.DB):
                    wmVT = "-"

                self.ui.labelWM.setText(f"{wmAT}/{wmVT}")

        return IAWaffenPicker

    ############################
    # Datenbankeditor
    ############################

    def dbeClassWaffeFilter(self, editorType, params):
        if not self.db.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
            return editorType

        class DatenbankEditWaffeWrapperPlus(editorType):
            def __init__(self, datenbank, fertigkeit=None, readonly=False):
                super().__init__(datenbank, fertigkeit, readonly)

            def onSetupUi(self):
                super().onSetupUi()
                self.ui.labelWMSeparator = QtWidgets.QLabel()
                self.ui.labelWMSeparator.setText("/")
                self.ui.spinWMVT = QtWidgets.QSpinBox()
                self.ui.spinWMVT.setMinimumSize(QtCore.QSize(50, 0))
                self.ui.spinWMVT.setAlignment(QtCore.Qt.AlignCenter)
                self.ui.spinWMVT.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
                self.ui.spinWMVT.setMinimum(-99)
                self.ui.spinWMVT.setMaximum(99)
                self.ui.horizontalLayout_3.addWidget(self.ui.labelWMSeparator)
                self.ui.horizontalLayout_3.addWidget(self.ui.spinWMVT)
                self.ui.comboTalent.currentTextChanged.connect(self.updateVTWM)

            def load(self, waffe):
                self.ui.spinWMVT.setValue(waffe.wmVt)
                super().load(waffe)

            def update(self, waffe):
                super().update(waffe)
                if not waffe.isVTVerboten(self.datenbank):
                    waffe.wmVt = int(self.ui.spinWMVT.value())

            def nameChanged(self):
                super().nameChanged()
                self.updateVTWM()

            def updateVTWM(self):
                name = self.ui.leName.text()
                talent = self.ui.comboTalent.currentText()
                vtVerboten = talent in self.datenbank.einstellungen["Waffen: Talente VT verboten"].wert or \
                    name in self.datenbank.einstellungen["Waffen: Talente VT verboten"].wert
                self.ui.spinWMVT.setVisible(not vtVerboten)
                self.ui.labelWMSeparator.setVisible(not vtVerboten)
                self.ui.labelWM.setText("WM AT" if vtVerboten else "WM AT/VT")

        return DatenbankEditWaffeWrapperPlus

    ############################
    # PDF Export
    ############################

    def pdfExportWaffenHook(self, fields, params):
        waffen = copy.deepcopy(Wolke.Char.waffen) #{ name, text, würfel, würfelseiten, plus, eigenschaften[], härte, fertigkeit, talent, kampfstile[], kampfstil, rw, wm, lz}[]>
  
        waffeToKey = {}
        for i in range(0, min(len(waffen), 8)):
            assert(fields["Waffe" + str(i+1) + "NA"] == waffen[i].anzeigename)
            waffeToKey[i] = "Waffe" + str(i+1)
 
        def removeEigenschaft(index, eigenschaft):
            eigenschaftenKey = waffeToKey[index] + "EI"
            waffe = waffen[index]
            waffe.eigenschaften.remove(eigenschaft)
            fields[eigenschaftenKey] = ", ".join(waffe.eigenschaften)
    
        def getEigenschaft(waffe, eigenschaft):
            result = None
            for val in waffe.eigenschaften:
                if val.startswith(eigenschaft):
                    result = val
                    break
            return result

        waffeIndex = 0
        for waffe in waffen:
            if waffeIndex+1 > len(waffeToKey) or not waffe.name:
                continue
        
            vtKey = waffeToKey[waffeIndex] + "VTm"
            atKey = waffeToKey[waffeIndex] + "ATm"
            härteKey = waffeToKey[waffeIndex] + "HA"
            rwKey = waffeToKey[waffeIndex] + "RW"
            wmKey = waffeToKey[waffeIndex] + "WM"
            tpmKey = waffeToKey[waffeIndex] + "TPm"

            #VT WM
            if self.db.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
                #fernkampfwaffen haben schon die LZ hier eingetragen...
                wmAT = ("+" if waffe.wm > 0 else "") + str(waffe.wm)
                wmVT = ("+" if waffe.wmVt > 0 else "") + str(waffe.wmVt)
                if waffe.isATVerboten(Wolke.DB):
                    wmAT = "-"
                if waffe.isVTVerboten(Wolke.DB):
                    wmVT = "-"
                if waffe.nahkampf:
                    fields[wmKey] = f"{wmAT} / {wmVT}"
                else:
                    fields[wmKey] = f"{wmAT} / LZ {waffe.lz}"

            #Optionale Eigenschaften
            if self.db.einstellungen["WaffenPlus Plugin: Optionale Waffeneigenschaften"].wert:
                for val in waffe.eigenschaften:
                    if val.endswith("(*)"):
                        removeEigenschaft(waffeIndex, val)

            waffeIndex += 1
        
        # Waffeneigenschaften gruppieren
        gruppieren = self.db.einstellungen["WaffenPlus Plugin: Waffeneigenschaften Gruppieren"].wert
        if len(gruppieren) > 0:
            waffeIndex = 0
            for waffe in waffen:
                if waffeIndex+1 > len(waffeToKey):
                    continue
                eigenschaftenKey = waffeToKey[waffeIndex] + "EI"

                filtered = []
                for eig in gruppieren:
                    found = getEigenschaft(waffe, eig)
                    if found:
                        removeEigenschaft(waffeIndex, found)
                        filtered.append(found)

                fields[eigenschaftenKey] = ", ".join(filtered)
                if len(waffe.eigenschaften) > 0:
                    if len(filtered) > 0:
                        fields[eigenschaftenKey] += " | "
                    fields[eigenschaftenKey] += ", ".join(waffe.eigenschaften)

                waffeIndex += 1
        return fields