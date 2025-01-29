# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from Core.DatenbankEinstellung import DatenbankEinstellung
from Core.Ruestung import Ruestung, RuestungDefinition
from Hilfsmethoden import Hilfsmethoden, SortedCategoryToListDict
from RuestungenPlus.RSCharakterRuestungWrapper import RSCharakterRuestungWrapper
from Wolke import Wolke
import DatenbankEditor
from RuestungenPlus import RSDatenbankEditRuestungseigenschaftWrapper, Ruestungseigenschaft
import copy
import re
from Core.Ruestung import RuestungDefinition, Ruestung
from Scripts import Script, ScriptParameter

# Add dynamic properties to Ruestung
RuestungDefinition.preis = property(lambda self: self._preis if hasattr(self, "_preis") else 0).setter(lambda self, v: setattr(self, "_preis", v))

deepEqualsOld = RuestungDefinition.deepequals
def deepequals(self, other): 
    return deepEqualsOld(self, other) and self.preis == other.preis

RuestungDefinition.deepequals = deepequals

def ruestungGetEigenschaften(self):
    if not hasattr(self, "_eigenschaften"):
        self._eigenschaften = []
        if self.definition.text:
            self._eigenschaften = list(map(str.strip, self.definition.text.split(",")))
    return self._eigenschaften

Ruestung.eigenschaften = property(ruestungGetEigenschaften).setter(lambda self, v: setattr(self, "_eigenschaften", v))
Ruestung.kategorie = property(lambda self: self._kategorie if hasattr(self, "_kategorie") else -1).setter(lambda self, v: setattr(self, "_kategorie", v))
Ruestung.zrsMod = property(lambda self: self._zrsMod if hasattr(self, "_zrsMod") else 0).setter(lambda self, v: setattr(self, "_zrsMod", v))

class Plugin:
    def __init__(self):
        EventBus.addAction("datenbank_laden", self.datenbankLadenHook)
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)

        # Rüstungseigenschaften
        EventBus.addFilter("datenbank_editor_typen", self.datenbankEditorTypenHook)
        EventBus.addAction("charakter_aktualisieren_fertigkeiten", self.charakterAktualisierenHandler)
        EventBus.addFilter("scripts_available", self.scriptsAvailableHook)

        # Regelanhang
        EventBus.addAction("regelanhang_anfuegen", self.regelanhangAnfuegenHandler)
        EventBus.addFilter("regelanhang_reihenfolge_name", lambda kuerzel, params: "Rüstungen" if kuerzel == "R" else kuerzel)

        # Slots
        EventBus.addFilter("class_ruestungspicker_wrapper", self.provideRuestungPickerWrapperHook)
        EventBus.addFilter("class_ausruestung_wrapper", self.provideAusruestungWrapperHook)
        EventBus.addFilter("class_inventar_wrapper", self.provideInventarWrapperHook)
        EventBus.addAction("charakter_instanziiert", self.charakterInstanziiertHandler)
        EventBus.addAction("charakter_deserialisiert", self.charakterDeserialisiertHandler)
        EventBus.addAction("charakter_serialisiert", self.charakterSerialisiertHandler, 100)
        EventBus.addAction("ruestungdefinition_serialisiert", self.rüstungdefinitionSerialisiertHandler)
        EventBus.addAction("ruestungdefinition_deserialisiert", self.rüstungdefinitionDeserialisiertHandler)
        EventBus.addAction("ruestung_serialisiert", self.rüstungSerialisiertHandler)
        EventBus.addAction("ruestung_deserialisiert", self.rüstungDeserialisiertHandler)
        
        EventBus.addFilter("dbe_class_ruestungdefinition_wrapper", self.dbeClassRüstungFilter)

    def changesCharacter(self):
        return self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].wert

    def changesDatabase(self):
        return True

    def datenbankLadenHook(self, params):
        self.db = params["datenbank"]
        self.db.ruestungseigenschaften = {}       
        self.db.insertTable(Ruestungseigenschaft.Ruestungseigenschaft, self.db.ruestungseigenschaften)

    def basisDatenbankGeladenHandler(self, params):
        e = DatenbankEinstellung()
        e.name = "RüstungenPlus Plugin: Aktivieren"
        e.beschreibung = "Hiermit kannst du das RüstungenPlus-Plugin nur für diese Hausregeln deaktivieren und es trotzdem allgemein in den Sephrasto-Einstellungen aktiviert lassen."
        e.text = "True"
        e.typ = "Bool"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "RüstungenPlus Plugin: Rüstungseigenschaften"
        e.beschreibung = "Falls aktiviert, erhalten alle Rüstungsslots eine weitere Spalte für Rüstungseigenschaften. Diese können im Datenbankeditor angelegt und wie Waffeneigenschaften mit Scripts versehen werden. "+\
            "Die Eigenschaften werden dann im Beschreibungsfeld der Rüstungen angegeben. Die bestehenden Beschreibungen sollten also nach Aktivierung als erstes bei allen Rüstungen geleert werden."
        e.text = "False"
        e.typ = "Bool"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "RüstungenPlus Plugin: Preis anzeigen"
        e.beschreibung = "Ermöglicht es, im Datenbankeditor bei Rüstungen Preise anzugeben. Diese werden dann im Rüstungsauswahlfenster des Charaktereditors angezeigt."
        e.text = "False"
        e.typ = "Bool"
        self.db.loadElement(e)

    def charakterInstanziiertHandler(self, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].wert:
            return
        char = params["charakter"]
        char.teilrüstungen1 = []
        char.teilrüstungen2 = []
        char.teilrüstungen3 = []
        
        char.rüstungenScriptAPI = copy.copy(char.charakterScriptAPI)
        char.rüstungenScriptAPI['getEigenschaftParam'] = lambda paramNb: self.API_getEigenschaftParam(paramNb)
        char.rüstungenScriptAPI['modifyZRSPunkte'] = lambda zrs: setattr(self.currentRuestung, 'zrsMod', self.currentRuestung.zrsMod + zrs)

    def scriptsAvailableHook(self, scripts, params):
        context = params["context"]
        if context == RSDatenbankEditRuestungseigenschaftWrapper.RSDatenbankEditRuestungseigenschaftWrapper.ScriptContext:
            script = Script(f"Rüstungseigenschaft Parameter (Zahl)", f"getEigenschaftParam", "Rüstungseigenschaften", castType = int)
            script.parameter.append(ScriptParameter("Index", int))
            scripts.numberGetter[script.name] = script

            script = Script(f"Waffeneigenschaft Parameter (Text)", f"getEigenschaftParam", "Rüstungseigenschaften")
            script.parameter.append(ScriptParameter("Index", int))
            scripts.stringGetter[script.name] = script

            script = Script("Rüstungseigenschaft ZRS-Punkte modifizieren", "modifyZRSPunkte", "Rüstungseigenschaften")
            script.beschreibung = "Modifiert die ZRS-Punkte, die eine Rüstung anhand ihrer Zonenrüstungswerte hat. "\
                "Damit kann das RS/BE-Verhältnis verbessert oder verschlechtert werden."
            script.parameter.append(ScriptParameter("Modifikator", int))
            scripts.setters[script.name] = script

        return scripts
    
    def rüstungdefinitionSerialisiertHandler(self, params):
        ser = params["serializer"]
        rüstung = params["object"]
    
        if self.db.einstellungen["RüstungenPlus Plugin: Preis anzeigen"].wert:
            ser.set("preis", rüstung.preis)

    def rüstungdefinitionDeserialisiertHandler(self, params):
        ser = params["deserializer"]
        rüstung = params["object"]
        rüstung.preis = ser.getInt("preis", rüstung.preis)

    def rüstungSerialisiertHandler(self, params):
        if not Wolke.DB.einstellungen["RüstungenPlus Plugin: Rüstungseigenschaften"].wert:
            return
        ser = params["serializer"]
        rüstung = params["object"]
        if rüstung.kategorie != -1:
            ser.set('kategorie', rüstung.kategorie)
        ser.set('text', ", ".join(rüstung.eigenschaften))

    def rüstungDeserialisiertHandler(self, params):
        if not Wolke.DB.einstellungen["RüstungenPlus Plugin: Rüstungseigenschaften"].wert:
            return
        ser = params["deserializer"]
        rüstung = params["object"]
        rüstung._kategorie = ser.getInt('kategorie', -1)
        eigenschaften = ser.get('text')
        if eigenschaften is not None:
            if eigenschaften:
                rüstung._eigenschaften = list(map(str.strip, eigenschaften.split(",")))
            else:
                rüstung._eigenschaften = []

    def charakterDeserialisiertHandler(self, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].wert:
            return

        deserializer = params["deserializer"]
        char = params["charakter"]
        teilrüstungen = [char.teilrüstungen1, char.teilrüstungen2, char.teilrüstungen3]

        if deserializer.find('Objekte'):
            for i in range(3):
                if deserializer.find('Teilrüstungen'+str(i+1)):
                    for tag in deserializer.listTags():
                        rüstung = Ruestung.__new__(Ruestung)
                        if not rüstung.deserialize(deserializer, Wolke.DB.rüstungen, char):
                            continue
                        teilrüstungen[i].append(rüstung)
                    deserializer.end() #teilrüstungen
            deserializer.end() #objekte

    def charakterSerialisiertHandler(self, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].wert:
            return

        serializer = params["serializer"]
        char = params["charakter"]
        teilrüstungen = [char.teilrüstungen1, char.teilrüstungen2, char.teilrüstungen3]

        if serializer.find('Objekte'):
            for i in range(3):
                serializer.beginList('Teilrüstungen'+str(i+1))
                for rüstung in teilrüstungen[i]:
                    serializer.begin('Rüstung')
                    rüstung.serialize(serializer)
                    serializer.end() #rüstung
                serializer.end() #teilrüstungen
            serializer.end() #objekte

    @staticmethod
    def getRuestungseigenschaft(eigStr, datenbank):
        weName = eigStr
        index = weName.find("(")
        if index != -1:
            weName = str.strip(weName[:index])
        
        if not weName in datenbank.ruestungseigenschaften:
            raise Exception("Unbekannte Rüstungseigenschaft '" + weName + "'")

        if index != -1:
            endIndex = eigStr[index:].find(")")
            if endIndex == -1:
                raise Exception("Parameter der Rüstungseigenschaft '" + weName + "' müssen mit ')' abgeschlossen werden. Mehrere Parameter werden mit Semikolon getrennt.")

        return datenbank.ruestungseigenschaften[weName]

    def API_getEigenschaftParam(self, paramNb):
        match = re.search(r"\((.+?)\)", self.currentEigenschaft, re.UNICODE)
        if not match:
            raise Exception("Die Rüstungseigenschaft '" + self.currentEigenschaft + "' erfordert einen Parameter, aber es wurde keiner gefunden")
        parameters = list(map(str.strip, match.group(1).split(";")))
        if not len(parameters) >= paramNb:
            raise Exception("Die Rüstungseigenschaft '" + self.currentEigenschaft + "' erfordert " + paramNb + " Parameter, aber es wurden nur " + len(parameters) + " gefunden. Parameter müssen mit Semikolon getrennt werden")
        return parameters[paramNb]

    def charakterAktualisierenHandler(self, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Rüstungseigenschaften"].wert:
            return

        char = params["charakter"]
        if len(char.rüstung) == 0:
            return

        for i in range(len(char.rüstung)):
            self.currentRuestung = char.rüstung[i]
            self.currentRuestung.zrsMod = 0
            for eig in self.currentRuestung.eigenschaften:
                self.currentEigenschaft = eig
                try:
                    ruestungsEigenschaft = Plugin.getRuestungseigenschaft(eig, Wolke.DB)
                except Exception:
                    continue #Manually added Eigenschaften are allowed
                if not ruestungsEigenschaft.script:
                    continue
                if ruestungsEigenschaft.scriptOnlyFirst and i != 0:
                    continue
                ruestungsEigenschaft.executeScript(char.rüstungenScriptAPI)

    ############################
    # Charaktereditor
    ############################

    def provideRuestungPickerWrapperHook(self, base, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].wert:
            return base

        class RSRuestungPicker(base):
            def __init__(self, ruestung, system, filterType):
                self.ruestungErsetzen = True
                self.filterType = filterType
                super().__init__(ruestung, system)
                
            def onSetupUi(self):
                super().onSetupUi()
                if Wolke.DB.einstellungen["RüstungenPlus Plugin: Preis anzeigen"].wert:
                    self.ui.labelPreis = QtWidgets.QLabel()
                    self.ui.labelPreis.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
                    self.ui.formLayout.insertRow(2, "Preis", self.ui.labelPreis)

            def populateTree(self):
                currSet = self.current != ""
                self.ui.treeArmors.clear()

                rüstungenByKategorie = SortedCategoryToListDict(Wolke.DB.einstellungen["Rüstungen: Kategorien"].wert)
                rüstungenByKategorie.setNameFilter(self.ui.nameFilterEdit.text())
                rüstungenByKategorie.setCategoryFilter([rüstungenByKategorie.categories.index(self.filterType)])
                for r in Wolke.DB.rüstungen.values():
                    if r.system != 0 and r.system != self.system:
                        continue
                    rüstungenByKategorie.append(r.kategorie, r.name)
                rüstungenByKategorie.sortValues()

                for kategorie, rüstungen in rüstungenByKategorie.items():
                    if len(rüstungen) == 0:
                        continue
                    parent = QtWidgets.QTreeWidgetItem(self.ui.treeArmors)
                    parent.setText(0, kategorie)
                    parent.setExpanded(True)
                    font = QtGui.QFont(Wolke.Settings["Font"], Wolke.FontHeadingSizeL3)
                    font.setBold(True)
                    font.setCapitalization(QtGui.QFont.SmallCaps)
                    parent.setFont(0, font)
                    for el in rüstungen:
                        if not currSet:
                            self.current = el
                            currSet = True
                        child = QtWidgets.QTreeWidgetItem(parent)
                        child.setData(0, QtCore.Qt.UserRole, el)
                        if el.endswith(" (ZRS)"):
                            child.setText(0, el[:-6])
                        else:
                            child.setText(0, el)

                if self.current in Wolke.DB.rüstungen:
                    found = self.ui.treeArmors.findItems(self.current, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
                    if len(found) > 0:
                        self.ui.treeArmors.setCurrentItem(found[0], 0, QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows)
                elif self.ui.treeArmors.topLevelItemCount() > 0 and self.ui.treeArmors.topLevelItem(0).childCount() > 0:
                    self.ui.treeArmors.setCurrentItem(self.ui.treeArmors.topLevelItem(0).child(0), 0, QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows)
                self.changeHandler()
                        
            def updateInfo(self):
                super().updateInfo()
                if Wolke.DB.einstellungen["RüstungenPlus Plugin: Preis anzeigen"].wert:
                    self.ui.labelPreis.setText("0 ST")
                    
                if self.current == "":
                    return
                R = Wolke.DB.rüstungen[self.current]
                if Wolke.DB.einstellungen["RüstungenPlus Plugin: Preis anzeigen"].wert:
                    self.ui.labelPreis.setText(str(R.preis) + " ST")

        return RSRuestungPicker

    def provideAusruestungWrapperHook(self, base, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].wert:
            return base

        class RSCharakterEquipmentWrapper(base):
            def __init__(self):
                super().__init__()

                if hasattr(self, "inventarWrapper"):
                    idx = self.ui.tabs.indexOf(self.inventarWrapper.form)
                    self.ui.tabs.setTabText(idx, "Inventar")

                self.ruestungWrapper = []
                for i in range(3):
                    wrapper = RSCharakterRuestungWrapper(i)
                    wrapper.modified.connect(self.onModified)
                    wrapper.reloadRSTabs.connect(self.reloadRSTabs)
                    self.ui.tabs.insertTab(1+i, wrapper.form, "Rüstung " + str(i+1))
                    self.ruestungWrapper.append(wrapper)
            
            def load(self):
                super().load()
                for i in range(3):
                    if self.ui.tabs.currentWidget() == self.ruestungWrapper[i].form:
                        self.ruestungWrapper[i].load()

            def reloadRSTabs(self):
                for wrapper in self.ruestungWrapper:
                    wrapper.load()

        return RSCharakterEquipmentWrapper

    def provideInventarWrapperHook(self, base, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].wert:
            return base

        class RSCharakterInventarWrapper(base):
            def __init__(self):
                super().__init__()
                self.ui.gbRstungen.hide()
                self.ui.gbInventar.setTitle("")

        return RSCharakterInventarWrapper

    ############################
    # Datenbankeditor
    ############################
    
    def datenbankEditorTypenHook(self, typen, params):
        typ = Ruestungseigenschaft.Ruestungseigenschaft
        editor = RSDatenbankEditRuestungseigenschaftWrapper.RSDatenbankEditRuestungseigenschaftWrapper
        typen[typ] = DatenbankEditor.DatenbankTypWrapper(typ, editor, True)
        return typen
    
    def dbeClassRüstungFilter(self, editorType, params):
        class DatenbankEditRüstungWrapperPlus(editorType):
            def __init__(self, datenbank, rüstung=None):
                super().__init__(datenbank, rüstung)

            def onSetupUi(self):
                super().onSetupUi()

                if self.datenbank.einstellungen["RüstungenPlus Plugin: Preis anzeigen"].wert:
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
                    self.ui.formLayout.insertRow(10, self.ui.labelPreis, self.ui.preisLayout)
                    self.registerInput(self.ui.spinPreis, self.ui.labelPreis)

            def load(self, rüstung):
                if self.datenbank.einstellungen["RüstungenPlus Plugin: Preis anzeigen"].wert:
                    self.ui.spinPreis.setValue(rüstung.preis)
                super().load(rüstung)

            def update(self, rüstung):
                super().update(rüstung)
                if self.datenbank.einstellungen["RüstungenPlus Plugin: Preis anzeigen"].wert:
                    rüstung.preis = self.ui.spinPreis.value()

        return DatenbankEditRüstungWrapperPlus

    ############################
    # PDF Export
    ############################

    def regelanhangAnfuegenHandler(self, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].wert:
            return
        reihenfolge = params["reihenfolge"]
        appendCb = params["appendCallback"]
    
        if reihenfolge != "R":
            return
        
        if len(Wolke.Char.rüstung) == 0:
            return

        teilrüstungen = [Wolke.Char.teilrüstungen1, Wolke.Char.teilrüstungen2, Wolke.Char.teilrüstungen3]
        addEigenschaften = self.db.einstellungen["RüstungenPlus Plugin: Rüstungseigenschaften"].wert 
        strList = ["<h2>Rüstungen</h1>"]
        for i in range(len(Wolke.Char.rüstung)):
            if not Wolke.Char.rüstung[i].name and Wolke.Char.rüstung[i].getRSGesamtInt() == 0:
                continue
            strList.append("<article><h3>Rüstung " + str(i+1) + "</h3>")
            strList.append(Wolke.Char.rüstung[i].name)
            if addEigenschaften and len(Wolke.Char.rüstung[i].eigenschaften) > 0:
                strList.append("<br>Eigenschaften: " + ", ".join(Wolke.Char.rüstung[i].eigenschaften))

            strList.append("<table><tr>")
            strList.append("<th align='left'>Name</th>")
            if Wolke.Char.zonenSystemNutzen:       
                for header in ["Beine", "L.&nbsp;Arm", "R.&nbsp;Arm", "Bauch", "Brust", "Kopf"]:
                    strList.append("<th>" + header + "</th>")
            else:
                strList.append("<th>RS</th>")
            strList.append("</tr>")

            for r in teilrüstungen[i]:
                if sum(r.rs) == 0:
                    continue
                strList.append("<tr>")
                strList.append("<td>" + r.name + "</td>")
                if Wolke.Char.zonenSystemNutzen:
                    for cell in [str(r.rs[0]), str(r.rs[1]), str(r.rs[2]), str(r.rs[3]), str(r.rs[4]), str(r.rs[5])]:
                        strList.append("<td align='center'>" + cell + "</td>")
                else:
                    strList.append("<td align='center'>" + str(r.getRSGesamtInt()) + "</td>")
                strList.append("</tr>")
                strList.append("<tr>")
                strList.append("<td colspan='100' style='font-size: 6pt;'>&nbsp;&nbsp;&nbsp;&nbsp;" + Wolke.DB.einstellungen["Rüstungen: Kategorien"].wert.keyAtIndex(r.kategorie))
                if addEigenschaften:
                    strList.append(" | Eigenschaften: ")
                    if len(r.eigenschaften) > 0:
                        strList.append(", ".join(r.eigenschaften))
                    else:
                        strList.append("-")
                strList.append("</td></tr>")

            strList.append("</table>")
            strList.append("</article>")

        if len(strList) > 1:
            appendCb("".join(strList))

        if not addEigenschaften:
            return

        eigenschaftenList = {}
        for i in range(len(Wolke.Char.rüstung)):
            for eig in Wolke.Char.rüstung[i].eigenschaften:
                try:
                    we = Plugin.getRuestungseigenschaft(eig, Wolke.DB)
                    if we.text:
                        eigenschaftenList[we.name] = we.text
                except Exception:
                    continue #Manually added Eigenschaften are allowed

        count = 0
        strList = ["<h2>Rüstungseigenschaften</h2>"]
        for eig in sorted(eigenschaftenList):
            count += 1
            strList.append("<article><h3>" + eig + "</h3>")
            strList.append(eigenschaftenList[eig])
            strList.append("</article>")
        if len(strList) > 1:
            appendCb("".join(strList))