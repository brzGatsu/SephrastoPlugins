# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore, QtGui
import lxml.etree as etree
from EventBus import EventBus
from DatenbankEinstellung import DatenbankEinstellung
import Objekte
from Hilfsmethoden import Hilfsmethoden
from RuestungenPlus import RSCharakterRuestungWrapper
from Wolke import Wolke
import DatenbankEditor
from RuestungenPlus import RSDatenbankEditRuestungseigenschaftWrapper
import copy
import re

class Plugin:
    def __init__(self):
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)

        # Rüstungseigenschaften
        EventBus.addFilter("datenbank_editor_typen", self.datenbankEditorTypenHook)
        EventBus.addFilter("datenbank_xml_laden", self.datenbankXmlLadenHook)
        EventBus.addFilter("datenbank_xml_schreiben", self.datenbankXmlSchreibenHook)
        EventBus.addAction("charakter_aktualisieren_fertigkeiten", self.charakterAktualisierenHandler)

        # Regelanhang
        EventBus.addAction("regelanhang_anfuegen", self.regelanhangAnfuegenHandler)
        EventBus.addFilter("regelanhang_reihenfolge_name", lambda kuerzel, params: "Rüstungen" if kuerzel == "R" else kuerzel)

        # Slots
        EventBus.addFilter("class_ruestungspicker_wrapper", self.provideRuestungPickerWrapperHook)
        EventBus.addFilter("class_ausruestung_wrapper", self.provideAusruestungWrapperHook)
        EventBus.addFilter("class_inventar_wrapper", self.provideInventarWrapperHook)
        EventBus.addAction("charakter_instanziiert", self.charakterInstanziiertHandler)
        EventBus.addAction("charakter_xml_geladen", self.charakterXmlGeladenHook)
        EventBus.addFilter("charakter_xml_schreiben", self.charakterXmlSchreibenHook, 100)

    @staticmethod
    def getDescription():
        return "Dieses Plugin teilt die drei Rüstungen auf jeweils eigene Tabs auf. " +\
    "Dort werden sie nach Slots (wie Arme und Kopf) aufgeteilt, sodass einzelne Rüstungsteile besser verwaltet werden können.\n" +\
    "Im Charakterbogen erscheinen aus Platzmangel weiterhin nur die berechneten kompletten Rüstungen, die Einzelteile können aber im Regelanhang ausgegeben werden:\n" +\
    "Hierzu musst du in der Datenbankeinstellung 'Regelanhang: Reihenfolge' an der gewünschten Position (z.B. nach 'W') ein 'R' einfügen.\n" +\
    "Wenn du die Option 'Rüstungseigenschaften' aktivierst, kannst du zusätzlich Rüstungseigenschaften anlegen, optional mit Scripts versehen und Slots zuweisen."

    def changesCharacter(self):
        return self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].toBool()

    def changesDatabase(self):
        return self.db.einstellungen["RüstungenPlus Plugin: Rüstungseigenschaften"].toBool()

    def basisDatenbankGeladenHandler(self, params):
        self.db = params["datenbank"]

        e = DatenbankEinstellung()
        e.name = "RüstungenPlus Plugin: Aktivieren"
        e.beschreibung = "Hiermit kannst du das RüstungenPlus-Plugin nur für diese Hausregeln deaktivieren und es trotzdem allgemein in den Sephrasto-Einstellungen aktiviert lassen."
        e.wert = "True"
        e.typ = "Bool"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e

        e = DatenbankEinstellung()
        e.name = "RüstungenPlus Plugin: Rüstungseigenschaften"
        e.beschreibung = "Falls aktiviert, erhalten alle Rüstungsslots eine weitere Spalte für Rüstungseigenschaften. Diese können im Datenbankeditor angelegt und wie Waffeneigenschaften mit Scripts versehen werden (erfordert einen Neustart des Datenbankeditors nach Aktivierung). "+\
            "Die Eigenschaften werden dann im Beschreibungsfeld der Rüstungen angegeben. Die bestehenden Beschreibungen sollten also nach Aktivierung als erstes bei allen Rüstungen geleert werden."
        e.wert = "False"
        e.typ = "Bool"
        e.isUserAdded = False
        self.db.einstellungen[e.name] = e
    
        self.db.ruestungseigenschaften = {}       
        self.db.tablesByName["Rüstungseigenschaft"] = self.db.ruestungseigenschaften

    # -----------------------
    # Rüstungseigenschaften
    # -----------------------

    def datenbankEditorTypenHook(self, typen, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Rüstungseigenschaften"].toBool():
            return typen
        typen["Rüstungseigenschaft"] = DatenbankEditor.DatenbankTypWrapper(self.addRuestungseigenschaft, self.editRuestungseigenschaft)
        return typen

    def datenbankXmlLadenHook(self, root, params):
        if params["basisdatenbank"]:
            return root

        eigenschaftNodes = root.findall('Rüstungseigenschaft')
        for eigenschaft in eigenschaftNodes:
            R = RSDatenbankEditRuestungseigenschaftWrapper.Ruestungseigenschaft()
            R.name = eigenschaft.get('name')
            R.text = eigenschaft.text or ''
            R.script = eigenschaft.get('script')
            R.scriptOnlyFirst = eigenschaft.attrib['scriptOnlyFirst'] == "1"
            R.isUserAdded = True
                                            
            if params["conflictCallback"] and R.name in self.db.ruestungseigenschaften:
                R = params["conflictCallback"]('Rüstungseigenschaft', self.db.ruestungseigenschaften[R.name], R)
            self.db.ruestungseigenschaften.update({R.name: R})

        return root

    def datenbankXmlSchreibenHook(self, root, params):
        for we in self.db.ruestungseigenschaften:
            eigenschaft = self.db.ruestungseigenschaften[we]
            w = etree.SubElement(root, 'Rüstungseigenschaft')
            w.set('name', eigenschaft.name)
            w.set('scriptOnlyFirst', "1" if eigenschaft.scriptOnlyFirst else "0")
            w.text = eigenschaft.text
            if eigenschaft.script:
                w.set('script', eigenschaft.script)

        return root

    def addRuestungseigenschaft(self):
        we = RSDatenbankEditRuestungseigenschaftWrapper.Ruestungseigenschaft()
        return self.editRuestungseigenschaft(we)

    def editRuestungseigenschaft(self, inp, readonly = False):
        dbW = RSDatenbankEditRuestungseigenschaftWrapper.RSDatenbankEditRuestungseigenschaftWrapper(self.db, inp, readonly)
        return dbW.ruestungseigenschaft

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
        if not self.db.einstellungen["RüstungenPlus Plugin: Rüstungseigenschaften"].toBool():
            return

        char = params["charakter"]
        if len(char.rüstung) == 0:
            return

        api = copy.copy(char.charakterScriptAPI)
        api['getEigenschaftParam'] = lambda paramNb: self.API_getEigenschaftParam(paramNb)
        api['modifyZRSPunkte'] = lambda zrs: setattr(self.currentRuestung, 'zrsMod', self.currentRuestung.zrsMod + zrs)

        for i in range(len(char.rüstung)):
            if not char.rüstung[i].text:
                continue
            self.currentRuestung = char.rüstung[i]
            self.currentRuestung.zrsMod = 0
            eigenschaften = list(map(str.strip, char.rüstung[i].text.split(",")))
            for eig in eigenschaften:
                self.currentEigenschaft = eig
                try:
                    we = Plugin.getRuestungseigenschaft(eig, Wolke.DB)
                except Exception:
                    continue #Manually added Eigenschaften are allowed
                if not we.script:
                    continue
                if we.scriptOnlyFirst and i != 0:
                    continue
                exec(we.script, api)

    # -----------------------
    # Regelanhang
    # -----------------------

    def regelanhangAnfuegenHandler(self, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].toBool():
            return
        reihenfolge = params["reihenfolge"]
        appendCb = params["appendCallback"]
    
        if reihenfolge != "R":
            return
        
        if len(Wolke.Char.rüstung) == 0:
            return

        teilrüstungen = [Wolke.Char.teilrüstungen1, Wolke.Char.teilrüstungen2, Wolke.Char.teilrüstungen3]
        slots = Wolke.DB.einstellungen["Rüstungen: Typen"].toTextList()
        addEigenschaften = self.db.einstellungen["RüstungenPlus Plugin: Rüstungseigenschaften"].toBool() 
        strList = []
        for i in range(len(Wolke.Char.rüstung)):
            strList.append("Rüstung " + str(i+1) + " - " + Wolke.Char.rüstung[i].name)
            if addEigenschaften and Wolke.Char.rüstung[i].text:
                strList.append(": " + Wolke.Char.rüstung[i].text)

            if Wolke.Char.zonenSystemNutzen:
                strList.append("\nSlot: Name | RS: Beine | L. Arm | R. Arm | Bauch | Brust | Kopf")
            else:
                strList.append("\nSlot: Name | RS")
            if addEigenschaften:
                strList.append(" | Eigenschaften")

            for r in teilrüstungen[i]:
                if sum(r.rs) == 0:
                    continue
                if Wolke.Char.zonenSystemNutzen:
                    strList.append("\n" + slots[r.typ] + ": " + r.name + " | " + str(r.rs[0]) + " | " + str(r.rs[1]) + " | " + str(r.rs[2]) + " | " + str(r.rs[3]) + " | " + str(r.rs[4]) + " | " + str(r.rs[5]))
                else:
                    strList.append("\n" + slots[r.typ] + ": " + r.name + " | " + str(r.getRSGesamtInt()))

                if not addEigenschaften:
                    continue
                if r.name in Wolke.DB.rüstungen:
                    strList.append(" | " + (Wolke.DB.rüstungen[r.name].text or "-"))
                else:
                    strList.append(" | -")
            
            strList.append("\n\n")

        appendCb("Rüstungen", "".join(strList))

        if not addEigenschaften:
            return

        strList = []
        eigenschaftenList = {}
        for i in range(len(Wolke.Char.rüstung)):
            if not Wolke.Char.rüstung[i].text:
                continue
            eigenschaften = list(map(str.strip, Wolke.Char.rüstung[i].text.split(",")))
            for eig in eigenschaften:
                try:
                    we = Plugin.getRuestungseigenschaft(eig, Wolke.DB)
                    if we.text:
                        eigenschaftenList[we.name] = we.text
                except Exception:
                    continue #Manually added Eigenschaften are allowed

        for eig in sorted(eigenschaftenList):
            strList.append(eig)
            strList.append("\n")
            strList.append(eigenschaftenList[eig])
            strList.append("\n\n")
        appendCb("Rüstungseigenschaften", "".join(strList))

    # -----------------------
    # Slots
    # -----------------------

    def provideRuestungPickerWrapperHook(self, base, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].toBool():
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
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].toBool():
            return base

        class RSCharakterEquipmentWrapper(base):
            def __init__(self):
                super().__init__()

                if hasattr(self, "inventarWrapper"):
                    idx = self.ui.tabs.indexOf(self.inventarWrapper.form)
                    self.ui.tabs.setTabText(idx, "Inventar")

                self.ruestungWrapper = []
                for i in range(3):
                    wrapper = RSCharakterRuestungWrapper.RSCharakterRuestungWrapper(i)
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
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].toBool():
            return base

        class RSCharakterInventarWrapper(base):
            def __init__(self):
                super().__init__()
                self.ui.gbRstungen.hide()
                self.ui.gbInventar.setTitle("")

        return RSCharakterInventarWrapper

    def charakterInstanziiertHandler(self, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].toBool():
            return
        char = params["charakter"]
        char.teilrüstungen1 = []
        char.teilrüstungen2 = []
        char.teilrüstungen3 = []

    def charakterXmlGeladenHook(self, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].toBool():
            return

        root = params["xmlRoot"]
        objekte = root.find('Objekte')
        if objekte is None:
            return

        char = params["charakter"]
        teilrüstungen = [char.teilrüstungen1, char.teilrüstungen2, char.teilrüstungen3]

        for i in range(3):
            for rüs in objekte.findall('Teilrüstungen'+str(i+1)+'/Rüstung'):
                rüst = Objekte.Ruestung()
                rüst.name = rüs.attrib['name']
                rüst.be = int(rüs.attrib['be'])
                rüst.rs = Hilfsmethoden.RsStr2Array(rüs.attrib['rs'])
                if 'typ' in rüs.attrib:
                    rüst.typ = int(rüs.attrib['typ'])
                rüst.text = rüs.text
                teilrüstungen[i].append(rüst)

        count = 0
        for rüs in objekte.findall('Rüstungen/Rüstung'):
            char.rüstung[count].text = rüs.text
            count += 1

    def charakterXmlSchreibenHook(self, root, params):
        if not self.db.einstellungen["RüstungenPlus Plugin: Aktivieren"].toBool():
            return root

        objekte = root.find('Objekte')
        if objekte is None:
            return root

        char = params["charakter"]
        teilrüstungen = [char.teilrüstungen1, char.teilrüstungen2, char.teilrüstungen3]

        for i in range(3):
            rüs = etree.SubElement(objekte,'Teilrüstungen'+str(i+1))
            for rüst in teilrüstungen[i]:
                rüsNode = etree.SubElement(rüs,'Rüstung')
                rüsNode.set('name',rüst.name)
                rüsNode.set('be',str(rüst.be))
                rüsNode.set('rs',Hilfsmethoden.RsArray2Str(rüst.rs))
                rüsNode.set('typ',str(rüst.typ))
                rüsNode.text = rüst.text

        count = 0
        for rüs in objekte.findall('Rüstungen/Rüstung'):
            rüs.text = char.rüstung[count].text
            count += 1
        return root