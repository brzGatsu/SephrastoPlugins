from PySide6 import QtWidgets, QtCore, QtGui
import shutil
import os
import lxml.etree as etree
from EventBus import EventBus
from Wolke import Wolke
from EinstellungenWrapper import EinstellungenWrapper
import copy
import re
from CheatsheetGenerator import CheatsheetGenerator
from DatenbankEinstellung import DatenbankEinstellung
import Objekte
from Hilfsmethoden import Hilfsmethoden

class Plugin:
    def __init__(self):
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)
        EventBus.addFilter("class_waffen_wrapper", self.provideWaffenWrapperHook)
        EventBus.addFilter("class_waffenpicker_wrapper", self.provideWaffenPickerWrapperHook)
        EventBus.addFilter("pdf_export", self.pdfExportWaffenHook)
    
    @staticmethod
    def getDescription():
        return "Dieses Plugin schafft einige Anpassungsmöglichkeiten für Waffen:\n\n" +\
            "- Zeigt im Waffen-Tab ein VT-WM Feld an. Waffen in der Datenbank kann die Eigenschaft Unhandlich(X) gegeben werden, wobei X von der VT abgezogen wird. Beispiel: ein WM von 2 und Unhandlich (3) bedeutet einen Gesamt-WM von 2/-1.\n" +\
            "- Optionale Waffeneigenschaften, die mit '(*)' am Ende des Namens markiert werden; Beispiel: die Streitaxt erhält die Eigenschaft Rüstungsbrechend (*). Diese Markierung muss im Charaktereditor entfernt werden, ansonsten wird die Eigenschaft nicht auf dem Charakterbogen ausgegeben.\n" +\
            "- In den Hausregeln können bestimmte Waffeneigenschaften via 'WaffenPlus Plugin: Waffeneigenschaften Gruppieren' in der PDF separat gruppiert werden.\n" +\
            "- Die Waffeneigenschaft Vielseitig gibt Waffen eine Doppelreichweite.\n\n" +\
            "Diese Features (außer Vielseitig) können in den Hausregeln über diverse 'WaffenPlus Plugin' Einstellungen deaktiviert werden. Vielseitig kann einfach gelöscht werden."

    def changesDatabase(self):
        return False

    def basisDatenbankGeladenHandler(self, params):
        self.db = params["datenbank"]

        e = DatenbankEinstellung()
        e.name = "WaffenPlus Plugin: Separater VT-WM"
        e.beschreibung = "Zeigt im Waffen-Tab ein VT-WM Feld an. Waffen in der Datenbank kann die Eigenschaft Unhandlich(X) gegeben werden, wobei X von der VT abgezogen wird; Beispiel: ein WM von 2 und Unhandlich (3) bedeutet einen Gesamt-WM von 2/-1." +\
        "Falls die Option deaktiviert wird, sollte auch die Waffeneigenschaft Unhandlich gelöscht werden."
        e.wert =  "True"
        e.typ = "Bool"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "WaffenPlus Plugin: Optionale Waffeneigenschaften"
        e.beschreibung = "Die Idee hinter optionalen Waffeneigenschaften ist, dass es verschiedene (unterschiedlich teure) Versionen derselben Waffe geben kann. " +\
        "Diese werden mit '(*)' am Ende des Namens markiert; Beispiel: die Streitaxt erhält die Eigenschaft Rüstungsbrechend (*). Diese Markierung muss im Charaktereditor entfernt werden, ansonsten wird die Eigenschaft nicht auf dem Charakterbogen ausgegeben."
        e.wert =  "True"
        e.typ = "Bool"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "WaffenPlus Plugin: Waffeneigenschaften Gruppieren"
        e.beschreibung = "Hier kann eine kommaseparierte Liste von Waffeneigenschaften angegeben werden, die im Charakterbogen separat gruppiert werden sollen."
        e.wert =  ""
        e.typ = "Text"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        w = Objekte.Waffeneigenschaft()
        w.name = "Unhandlich"
        w.text = "Diese Waffeneigenschaft sollte nur im Datenbankeditor verwendet werden. Im Charaktereditor wird sie durch das VT-WM Feld ersetzt."
        w.script = "modifyWaffeVT(-int(getEigenschaftParam(1)))"
        w.isUserAdded = False
        self.db.waffeneigenschaften[w.name] = w

        w = Objekte.Waffeneigenschaft()
        w.name = "Vielseitig"
        w.text = "Die Waffe ist in einer um eine Stufe kürzeren Reichweite ebenso effektiv."
        w.isUserAdded = False
        self.db.waffeneigenschaften[w.name] = w
    
    def provideWaffenWrapperHook(self, base, params):
        if not self.db.einstellungen["WaffenPlus Plugin: Separater VT-WM"].toBool():
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
                    
            def getWEParam(self, str):
                match = re.search("\(\s*([+-]?\d*)\s*\)", str)
                if match:
                    return int(match.groups()[0])
                return 0

            def loadWeaponIntoFields(self, W, index):
                W = copy.deepcopy(W)
                vtWM = W.wm
                for we in W.eigenschaften:
                    if we.startswith("Unhandlich"):
                        vtWM -= self.getWEParam(we)
                        W.eigenschaften.remove(we)
                        break
                isEmpty = W == Objekte.Nahkampfwaffe()

                vtVerboten = Wolke.DB.einstellungen["Waffen: Talente VT verboten"].toTextList()
                self.spinWM2[index].setEnabled(not isEmpty and not (W.name in vtVerboten or W.talent in vtVerboten))
                self.spinWM2[index].setValue(vtWM if self.spinWM2[index].isEnabled() else 0)
                super().loadWeaponIntoFields(W, index)

            def createWaffe(self, index):
                W = super().createWaffe(index)
                if type(W) == Objekte.Nahkampfwaffe and self.spinWM2[index].value() != W.wm:
                    W.eigenschaften.append("Unhandlich (" + str(W.wm - self.spinWM2[index].value()) + ")")
                return W

            def refreshDerivedWeaponValues(self, W, index):
                unhandlich = None
                for i in range(len(W.eigenschaften)):
                    if W.eigenschaften[i].startswith("Unhandlich"):
                        unhandlich = W.eigenschaften[i]
                        del W.eigenschaften[i]
                        break
                super().refreshDerivedWeaponValues(W, index)
                if unhandlich:
                    W.eigenschaften.insert(i, unhandlich)

            def diffWeapons(self, weapon1, weapon2):
                diff = []
                würfelDiff = weapon1.würfel - weapon2.würfel
                plusDiff = weapon1.plus - weapon2.plus

                härteDiff = weapon1.härte - weapon2.härte
                waffenHärteWSStern = Wolke.DB.einstellungen["Waffen: Härte WSStern"].toTextList()
                if weapon2.name in waffenHärteWSStern:
                    härteDiff = weapon1.härte - Wolke.Char.wsStern

                atWMDiff = weapon1.wm - weapon2.wm
                def getUnhandlichParam(weapon):
                    for we in weapon.eigenschaften:
                        if we.startswith("Unhandlich"):
                            return self.getWEParam(we)
                    return 0
                vtWMDiff = getUnhandlichParam(weapon2) - getUnhandlichParam(weapon1) + atWMDiff

                rwDiff = weapon1.rw - weapon2.rw
                lzDiff = 0
                if type(weapon1) is Objekte.Fernkampfwaffe:
                    lzDiff = weapon1.lz - weapon2.lz

                w1Eig = [eig for eig in weapon1.eigenschaften if not eig.startswith("Unhandlich")]
                w2Eig = [eig for eig in weapon2.eigenschaften if not eig.startswith("Unhandlich")]
                eigPlusDiff = list(set(w1Eig) - set(w2Eig))
                eigMinusDiff = list(set(w2Eig) - set(w1Eig))

                if würfelDiff != 0:
                    diff.append("TP " + ("+" if würfelDiff >= 0 else "") + str(würfelDiff) + "W" + str(weapon1.würfelSeiten))
                if plusDiff != 0:
                    tmp = ("+" if plusDiff >= 0 else "") + str(plusDiff)
                    if würfelDiff != 0:
                        diff[0] += tmp
                    else:
                        diff.append("TP " + tmp)
                if rwDiff != 0:
                    diff.append("RW " + ("+" if rwDiff >= 0 else "") + str(rwDiff))
                if atWMDiff != 0 or vtWMDiff != 0:
                    diff.append("WM " + ("+" if atWMDiff >= 0 else "") + str(atWMDiff))
                    vtVerboten = Wolke.DB.einstellungen["Waffen: Talente VT verboten"].toTextList()
                    if weapon1.name in vtVerboten or weapon1.talent in vtVerboten:
                        diff[-1] += "/-"
                    else:
                        diff[-1] += "/" + ("+" if vtWMDiff >= 0 else "") + str(vtWMDiff)
                if lzDiff != 0:
                    diff.append("LZ " + ("+" if lzDiff >= 0 else "") + str(lzDiff))
                if härteDiff != 0:
                    diff.append("Härte " + ("+" if härteDiff >= 0 else "") + str(härteDiff))
                if len(eigPlusDiff) > 0:
                    diff.append("Eigenschaften +" + ", +".join(eigPlusDiff))
                if len(eigMinusDiff) > 0:
                    if len(eigPlusDiff) > 0:
                        diff[-1] += ", " + ("-" + ", -".join(eigMinusDiff))
                    else:
                        diff.append("Eigenschaften -" + ", -".join(eigMinusDiff))
                return diff

        return IAWaffenWrapper

    def provideWaffenPickerWrapperHook(self, base, params):
        if not self.db.einstellungen["WaffenPlus Plugin: Separater VT-WM"].toBool():
            return base
        class IAWaffenPicker(base):
            def __init__(self, W):
                super().__init__(W)

            def updateInfo(self):
                super().updateInfo()
                if self.current == "":
                    return
                W = Wolke.DB.waffen[self.current]
                eigenschaftenNew = []
                vtWM = W.wm
                for we in W.eigenschaften:
                    name = re.sub(r"\((.*?)\)", "", we, re.UNICODE).strip() # remove parameters
                    if name == "Unhandlich":
                        match = re.search("\(\s*([+-]?\d*)\s*\)", we)
                        if match:
                            vtWM -= int(match.groups()[0])
                    else:
                        eigenschaftenNew.append(we)
                self.ui.labelEigenschaften.setText("Eigenschaften: " + ", ".join(eigenschaftenNew))
                if type(W) == Objekte.Nahkampfwaffe:
                    self.ui.labelWM_Text.setText("Waffenmodifikator AT/VT")
                    self.ui.labelWM.setText(("+" if W.wm > 0 else "") + str(W.wm) + "/" + ("+" if vtWM > 0 else "") + str(vtWM))
                else:
                    self.ui.labelWM_Text.setText("Waffenmodifikator")
                    self.ui.labelWM.setText(("+" if W.wm > 0 else "") + str(W.wm))

        return IAWaffenPicker

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
            if waffeIndex+1 > len(waffeToKey):
                continue
        
            vtKey = waffeToKey[waffeIndex] + "VTm"
            atKey = waffeToKey[waffeIndex] + "ATm"
            härteKey = waffeToKey[waffeIndex] + "HA"
            rwKey = waffeToKey[waffeIndex] + "RW"
            wmKey = waffeToKey[waffeIndex] + "WM"
            tpmKey = waffeToKey[waffeIndex] + "TPm"
        
            #Vielseitig
            vielseitig = getEigenschaft(waffe, "Vielseitig")
            if vielseitig:
                fields[rwKey] = str((int(fields[rwKey]) - 1)) + "-" + fields[rwKey]
                removeEigenschaft(waffeIndex, vielseitig)

            #Unhandlich
            if self.db.einstellungen["WaffenPlus Plugin: Separater VT-WM"].toBool():
                unhandlich = getEigenschaft(waffe, "Unhandlich")
                if fields[wmKey] and unhandlich:
                    match = re.search("\(\s*([+-]?\d*)\s*\)", unhandlich)
                    if match:
                        val = int(match.groups()[0])
                        fields[wmKey] = fields[wmKey] + "/" + str(int(fields[wmKey]) - val)
                        removeEigenschaft(waffeIndex, unhandlich)
                elif not hasattr(waffe, 'lz'):
                    fields[wmKey] = fields[wmKey] + "/" + fields[wmKey]

            #Optionale Eigenschaften
            if self.db.einstellungen["WaffenPlus Plugin: Optionale Waffeneigenschaften"].toBool():
                for val in waffe.eigenschaften:
                    if val.endswith("(*)"):
                        removeEigenschaft(waffeIndex, val)

            waffeIndex += 1
        
        # Waffeneigenschaften gruppieren
        gruppieren = self.db.einstellungen["WaffenPlus Plugin: Waffeneigenschaften Gruppieren"].toTextList() 
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