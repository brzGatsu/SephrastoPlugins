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
from Scripts import Script, ScriptParameter

# Add dynamic properties to WaffeDefinition and Waffe that work exactly like the implementation of "wm"
# The only difference is that WaffeDefinition returns wm if wmVt was never set.
WaffeDefinition.wmVt = property(lambda self: self._wmVt if hasattr(self, "_wmVt") else self.wm).setter(lambda self, v: setattr(self, "_wmVt", v))
WaffeDefinition.preis = property(lambda self: self._preis if hasattr(self, "_preis") else 0).setter(lambda self, v: setattr(self, "_preis", v))

deepEqualsOld = WaffeDefinition.deepequals

def deepequals(self, other): 
    return deepEqualsOld(self, other) and self.wmVt == other.wmVt and self.preis == other.preis

WaffeDefinition.deepequals = deepequals

Waffe.wmVt = property(lambda self: self._wmVtOverride if hasattr(self, "_wmVtOverride") else self.definition.wmVt).setter(lambda self, v: setattr(self, "_wmVtOverride", v))

class Plugin:
    def __init__(self):
        EventBus.addAction("datenbank_laden", self.datenbankLadenHandler)
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)
        EventBus.addAction("charakter_instanziiert", self.charakterInstanziiertHandler)
        EventBus.addFilter("scripts_available", self.scriptsAvailableHook)
        EventBus.addFilter("class_waffen_wrapper", self.provideWaffenWrapperHook)
        EventBus.addFilter("class_waffenpicker_wrapper", self.provideWaffenPickerWrapperHook)
        EventBus.addFilter("pdf_export", self.pdfExportWaffenHook)
        EventBus.addFilter("dbe_class_waffedefinition_wrapper", self.dbeClassWaffeFilter)
        EventBus.addAction("waffedefinition_serialisiert", self.waffedefinitionSerialisiertHandler)
        EventBus.addAction("waffedefinition_deserialisiert", self.waffedefinitionDeserialisiertHandler)
        EventBus.addAction("waffe_serialisiert", self.waffeSerialisiertHandler)
        EventBus.addAction("waffe_deserialisiert", self.waffeDeserialisiertHandler)

    def changesCharacter(self):
        return self.db.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert

    def changesDatabase(self):
        return self.db.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert or self.db.einstellungen["WaffenPlus Plugin: Preis anzeigen"].wert

    def datenbankLadenHandler(self, params):
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

        e = DatenbankEinstellung()
        e.name = "WaffenPlus Plugin: Preis anzeigen"
        e.beschreibung = "Ermöglicht es, im Datenbankeditor bei Waffen Preise anzugeben. Diese werden dann im Waffenauswahlfenster des Charaktereditors angezeigt."
        e.text = "False"
        e.typ = "Bool"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "WaffenPlus Plugin: Härte anzeigen"
        e.beschreibung = "Ermöglicht es, im Datenbank- und im Charakereditor bei Waffen die Härte auszublenden."
        e.text = "True"
        e.typ = "Bool"
        self.db.loadElement(e)

    def basisDatenbankGeladenHandler(self, params):
        e = self.db.einstellungen["Charakter aktualisieren Script"]
        e.text = e.text.replace("vt = pw + getKampfstilVT(kampfstil) + getWaffeWM(idx) - be",
                                "vt = pw + getKampfstilVT(kampfstil) + getWaffeWMVT(idx) - be")

    def charakterInstanziiertHandler(self, params):
        char = params["charakter"]
        if self.db.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
            char.charakterScriptAPI["getWaffeWMVT"] = lambda index: char.API_getWaffeValue(index, "wmVt")
        else:
            char.charakterScriptAPI["getWaffeWMVT"] = lambda index: char.API_getWaffeValue(index, "wm")
        char.waffenScriptAPI["getWaffeWMVT"] = char.charakterScriptAPI["getWaffeWMVT"]
        if hasattr(char, "rüstungenScriptAPI"): #rüstungenplus plugin
            char.rüstungenScriptAPI["getWaffeWMVT"] = char.charakterScriptAPI["getWaffeWMVT"]

    def scriptsAvailableHook(self, scripts, params):
        script = Script(f"Waffe WM VT", f"getWaffeWMVT", "Ausrüstung")
        script.parameter.append(ScriptParameter("Index", int))
        scripts.numberGetter[script.name] = script
        return scripts

    def waffedefinitionSerialisiertHandler(self, params):
        ser = params["serializer"]
        waffe = params["object"]
    
        if self.db.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
            ser.set("wmVt", waffe.wmVt)
        if self.db.einstellungen["WaffenPlus Plugin: Preis anzeigen"].wert:
            ser.set("preis", waffe.preis)

    def waffedefinitionDeserialisiertHandler(self, params):
        ser = params["deserializer"]
        waffe = params["object"]
        waffe.wmVt = ser.getInt("wmVt", waffe.wm)
        waffe.preis = ser.getInt("preis", waffe.preis)

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
        class IAWaffenWrapper(base):
            def __init__(self):
                super().__init__()
                
                if not Wolke.DB.einstellungen["WaffenPlus Plugin: Härte anzeigen"].wert:
                   self.ui.labelHaerte.setVisible(False)
                   for spin in self.spinHärte:
                       spin.setVisible(False)

                if Wolke.DB.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
                    self.ui.labelWM.setText("WM AT/VT")
                    self.spinWM2 = []
                    self.spinWM2Layout = []
                    for i in range(8):
                        spin = QtWidgets.QSpinBox()
                        spin.setAlignment(QtCore.Qt.AlignCenter)
                        spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
                        spin.valueChanged.connect(self.updateWaffen)
                        spin.setMinimum(-99)
                        spin.setMaximum(99)

                        layout = QtWidgets.QHBoxLayout()
                        widgetItem = self.ui.Waffen.itemAtPosition(3 + i*5, 4)
                        layout.addWidget(widgetItem.widget())
                        layout.addWidget(QtWidgets.QLabel(" / "))
                        layout.addWidget(spin)
                        self.ui.Waffen.addLayout(layout, 3 + i*5, 4, 1, 1)
                        self.spinWM2.append(spin)
                        self.spinWM2Layout.append(layout)

                        self.form.setTabOrder(self.spinWM[i], spin)
                        self.form.setTabOrder(spin, self.spinLZ[i])

            def loadWeaponIntoFields(self, W, index):
                super().loadWeaponIntoFields(W, index)
                
                if Wolke.DB.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
                    isEmpty = W.name == ""
                    vtVerboten = W.isVTVerboten(Wolke.DB)
                    self.spinWM2[index].setEnabled(not isEmpty and not vtVerboten)
                    if vtVerboten:
                        self.spinWM2[index].setValue(0)
                    else:
                        self.spinWM2[index].setValue(W.wmVt)

            def createWaffe(self, index):
                W = super().createWaffe(index)
                
                if Wolke.DB.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
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
                vtWMDiff = 0
                if Wolke.DB.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
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
                    if Wolke.DB.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
                        if waffe.isATVerboten(Wolke.DB):
                            diff[-1] += "-"
                        else:
                            diff[-1] += ("+" if atWMDiff >= 0 else "") + str(atWMDiff)
                        if waffe.isVTVerboten(Wolke.DB):
                            diff[-1] += "/-"
                        else:
                            diff[-1] += "/" + ("+" if vtWMDiff >= 0 else "") + str(vtWMDiff)
                    else:
                        diff[-1] += ("+" if atWMDiff >= 0 else "") + str(atWMDiff)
                if lzDiff != 0:
                    diff.append("LZ " + ("+" if lzDiff >= 0 else "") + str(lzDiff))
                if Wolke.DB.einstellungen["WaffenPlus Plugin: Härte anzeigen"].wert and härteDiff != 0:
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
        class IAWaffenPicker(base):
            def __init__(self, W = None):
                super().__init__(W)
                
            def onSetupUi(self):
                super().onSetupUi()
                if Wolke.DB.einstellungen["WaffenPlus Plugin: Preis anzeigen"].wert:
                    self.ui.labelPreis = QtWidgets.QLabel()
                    self.ui.labelPreis.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
                    self.ui.formLayout.insertRow(11, "Preis", self.ui.labelPreis)
                    
                if not Wolke.DB.einstellungen["WaffenPlus Plugin: Härte anzeigen"].wert:
                    self.ui.formLayout.setRowVisible(self.ui.labelHaerte, False)

            def updateInfo(self):
                super().updateInfo()
                if Wolke.DB.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
                    self.ui.labelWM.setText("Waffenmodifikator AT/VT")
                if Wolke.DB.einstellungen["WaffenPlus Plugin: Preis anzeigen"].wert:
                    self.ui.labelPreis.setText("0 ST")
                    
                if self.current == "":
                    return

                W = Wolke.DB.waffen[self.current]
                
                if Wolke.DB.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
                    wmAT = ("+" if W.wm > 0 else "") + str(W.wm)
                    wmVT = ("+" if W.wmVt > 0 else "") + str(W.wmVt)

                    if W.isATVerboten(Wolke.DB):
                        wmAT = "-"
                    if W.isVTVerboten(Wolke.DB):
                        wmVT = "-"

                    self.ui.labelWMWert.setText(f"{wmAT}/{wmVT}")
                    
                if Wolke.DB.einstellungen["WaffenPlus Plugin: Preis anzeigen"].wert:
                    self.ui.labelPreis.setText(str(W.preis) + " ST")

        return IAWaffenPicker

    ############################
    # Datenbankeditor
    ############################

    def dbeClassWaffeFilter(self, editorType, params):
        class DatenbankEditWaffeWrapperPlus(editorType):
            def __init__(self, datenbank, fertigkeit=None):
                super().__init__(datenbank, fertigkeit)

            def onSetupUi(self):
                super().onSetupUi()
                if self.datenbank.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
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
                    self.registerInput(self.ui.spinWMVT, self.ui.labelWM)

                if self.datenbank.einstellungen["WaffenPlus Plugin: Preis anzeigen"].wert:
                    self.ui.labelPreis = QtWidgets.QLabel("Preis")
                    self.ui.spinPreis = QtWidgets.QSpinBox()
                    self.ui.spinPreis.setMinimumSize(QtCore.QSize(50, 0))
                    self.ui.spinPreis.setAlignment(QtCore.Qt.AlignCenter)
                    self.ui.spinPreis.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
                    self.ui.spinPreis.setMinimum(0)
                    self.ui.spinPreis.setMaximum(99999)
                    self.ui.preisLayout = QtWidgets.QHBoxLayout()
                    self.ui.preisLayout.addStretch()
                    self.ui.preisLayout.addWidget(self.ui.spinPreis)
                    self.ui.formLayout.insertRow(7, self.ui.labelPreis, self.ui.preisLayout)
                    self.registerInput(self.ui.spinPreis, self.ui.labelPreis)

                if not self.datenbank.einstellungen["WaffenPlus Plugin: Härte anzeigen"].wert:
                    self.ui.formLayout.setRowVisible(self.ui.labelHaerte, False)

            def load(self, waffe):
                if self.datenbank.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
                    self.ui.spinWMVT.setValue(waffe.wmVt)
                if self.datenbank.einstellungen["WaffenPlus Plugin: Preis anzeigen"].wert:
                    self.ui.spinPreis.setValue(waffe.preis)
                super().load(waffe)

            def update(self, waffe):
                super().update(waffe)
                if self.datenbank.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
                    if not waffe.isVTVerboten(self.datenbank):
                        waffe.wmVt = int(self.ui.spinWMVT.value())
                if self.datenbank.einstellungen["WaffenPlus Plugin: Preis anzeigen"].wert:
                    waffe.preis = self.ui.spinPreis.value()

            def nameChanged(self):
                super().nameChanged()
                self.updateVTWM()

            def updateVTWM(self):
                if not self.datenbank.einstellungen["WaffenPlus Plugin: Separater VT-WM"].wert:
                    return
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