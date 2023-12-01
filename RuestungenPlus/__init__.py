# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from Core.DatenbankEinstellung import DatenbankEinstellung
from Core.Ruestung import Ruestung, RuestungDefinition
from Hilfsmethoden import Hilfsmethoden
from RuestungenPlus.RSCharakterRuestungWrapper import RSCharakterRuestungWrapper
from Wolke import Wolke
import DatenbankEditor
from RuestungenPlus import RSDatenbankEditRuestungseigenschaftWrapper, Ruestungseigenschaft
import copy
import re

class Plugin:
    def __init__(self):
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)

        # Rüstungseigenschaften
        EventBus.addFilter("datenbank_editor_typen", self.datenbankEditorTypenHook)
        EventBus.addAction("charakter_aktualisieren_fertigkeiten", self.charakterAktualisierenHandler)

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

    @staticmethod
    def getDescription():
        return "Dieses Plugin teilt die drei Rüstungen auf jeweils eigene Tabs auf. " +\
    "Dort werden sie nach Slots (wie Arme und Kopf) aufgeteilt, sodass einzelne Rüstungsteile besser verwaltet werden können.\n" +\
    "Im Charakterbogen erscheinen aus Platzmangel weiterhin nur die berechneten kompletten Rüstungen, die Einzelteile können aber im Regelanhang ausgegeben werden:\n" +\
    "Hierzu musst du in der Datenbankeinstellung 'Regelanhang: Reihenfolge' an der gewünschten Position (z.B. nach 'W') ein 'R' einfügen.\n" +\
    "Wenn du die Option 'Rüstungseigenschaften' aktivierst, kannst du zusätzlich Rüstungseigenschaften anlegen, optional mit Scripts versehen und Slots zuweisen."

    def changesCharacter(self):
        return self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].wert

    def changesDatabase(self):
        return True

    def basisDatenbankGeladenHandler(self, params):
        self.db = params["datenbank"]

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

        self.db.ruestungseigenschaften = {}       
        self.db.insertTable(Ruestungseigenschaft.Ruestungseigenschaft, self.db.ruestungseigenschaften)

    # -----------------------
    # Rüstungseigenschaften
    # -----------------------

    def datenbankEditorTypenHook(self, typen, params):
        typ = Ruestungseigenschaft.Ruestungseigenschaft
        editor = RSDatenbankEditRuestungseigenschaftWrapper.RSDatenbankEditRuestungseigenschaftWrapper
        typen[typ] = DatenbankEditor.DatenbankTypWrapper(typ, editor, True)
        return typen

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
        return parameters[paramNb-1]

    def charakterAktualisierenHandler(self, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Rüstungseigenschaften"].wert:
            return

        char = params["charakter"]
        if len(char.rüstung) == 0:
            return

        api = copy.copy(char.charakterScriptAPI)
        api['getEigenschaftParam'] = lambda paramNb: self.API_getEigenschaftParam(paramNb)
        api['modifyZRSPunkte'] = lambda zrs: setattr(self.currentRuestung, 'zrsMod', self.currentRuestung.zrsMod + zrs)

        for i in range(len(char.rüstung)):
            self.currentRuestung = char.rüstung[i]
            self.currentRuestung.zrsMod = 0
            if not hasattr(self.currentRuestung, "eigenschaften"):
                RSCharakterRuestungWrapper.applyEigenschaften(self.currentRuestung)
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
                ruestungsEigenschaft.executeScript(api)

    # -----------------------
    # Regelanhang
    # -----------------------

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
        slots = Wolke.DB.einstellungen["Rüstungen: Typen"].wert
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
                strList.append("<td colspan='100' style='font-size: 6pt;'>&nbsp;&nbsp;&nbsp;&nbsp;" + slots[r.typ])
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

    # -----------------------
    # Slots
    # -----------------------

    def provideRuestungPickerWrapperHook(self, base, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].wert:
            return base

        class RSRuestungPicker(base):
            def __init__(self, ruestung, system, filterType):
                self.ruestungErsetzen = True
                self.filterType = filterType
                super().__init__(ruestung, system)

            def populateTree(self):
                super().populateTree()
                root = self.ui.treeArmors.invisibleRootItem()
                for idx in range(root.childCount()):
                    name = root.child(idx).text(0)
                    if root.child(idx).text(0) != self.filterType:
                        root.child(idx).setHidden(True)

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
                    self.ui.tabs.tabBar().setTabTextColor(1+i, QtGui.QColor(Wolke.HeadingColor))
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

    def charakterInstanziiertHandler(self, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].wert:
            return
        char = params["charakter"]
        char.teilrüstungen1 = []
        char.teilrüstungen2 = []
        char.teilrüstungen3 = []

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
                        name = deserializer.get('name')
                        definition = None
                        if name in Wolke.DB.rüstungen:
                            definition = copy.deepcopy(Wolke.DB.rüstungen[name])
                        else:
                            definition = RuestungDefinition()
                            definition.name = name
                        rüst = Ruestung(definition)
                        rüst.be = deserializer.getInt('be')
                        rüst.rs = Hilfsmethoden.RsStr2Array(deserializer.get('rs'))
                        typ = deserializer.getInt('typ')
                        if typ:
                            rüst.typ = typ

                        if Wolke.DB.einstellungen["RüstungenPlus Plugin: Rüstungseigenschaften"].wert:
                            eigenschaften = deserializer.get('text')
                            if eigenschaften:
                                definition.text = eigenschaften
                            RSCharakterRuestungWrapper.applyEigenschaften(rüst)
                        teilrüstungen[i].append(rüst)
                    deserializer.end() #teilrüstungen

            if Wolke.DB.einstellungen["RüstungenPlus Plugin: Rüstungseigenschaften"].wert:
                if deserializer.find('Rüstungen'):
                    count = 0
                    for tag in deserializer.listTags():
                        eigenschaften = deserializer.get('text')
                        if eigenschaften:
                            char.rüstung[count].definition.text = eigenschaften
                        count += 1
                    deserializer.end() #rüstungen

                for rüst in char.rüstung:
                    RSCharakterRuestungWrapper.applyEigenschaften(rüst)

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
                for rüst in teilrüstungen[i]:
                    serializer.begin('Rüstung')
                    serializer.set('name',rüst.name)
                    serializer.set('be', rüst.be)
                    serializer.set('rs', Hilfsmethoden.RsArray2Str(rüst.rs))
                    serializer.set('typ', rüst.typ)
                    if Wolke.DB.einstellungen["RüstungenPlus Plugin: Rüstungseigenschaften"].wert:
                        serializer.set('text', ", ".join(rüst.eigenschaften))
                    serializer.end() #rüstung
                serializer.end() #teilrüstungen

            if Wolke.DB.einstellungen["RüstungenPlus Plugin: Rüstungseigenschaften"].wert:
                if serializer.find('Rüstungen'):
                    count = 0
                    for tag in serializer.listTags():
                        serializer.set('text', ", ".join(char.rüstung[count].eigenschaften))
                        count += 1
                    serializer.end() #rüstungen

            serializer.end() #objekte