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
from Hilfsmethoden import Hilfsmethoden

class Plugin:
    def __init__(self):
        EventBus.addAction("plugins_geladen", self.pluginsLoadedHandler)
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)

        # Kulturkunde
        EventBus.addFilter("class_beschreibungdetails_wrapper", self.provideBeschreibungDetailsWrapperHook)
        EventBus.addFilter("pdf_export", self.pdfExportKulturkundeHook)

        # Ansehen
        EventBus.addAction("pre_charakter_aktualisieren", self.preCharakterAktualisierenAnsehenHandler)
        EventBus.addAction("post_charakter_aktualisieren", self.postCharakterAktualisierenAnsehenHandler)
        EventBus.addAction("charakter_instanziiert", self.charakterInstanziiertAnsehenHandler)
        EventBus.addAction("charakter_deserialisiert", self.charakterDeserialisiertAnsehenHandler, 100)
        EventBus.addAction("charakter_serialisiert", self.charakterSerialisiertAnsehenHandler, 100)
        EventBus.addFilter("pdf_export", self.pdfExportAnsehenHook)

        # Build paths
        rootdir = os.path.dirname(os.path.abspath(__file__))
        charakterbögenPath = Wolke.Settings["Pfad-Charakterbögen"]
        charakterbogenFile = "Drachentöter Charakterbogen.pdf"
        charakterbogenFilePath = os.path.join(rootdir, "Data", charakterbogenFile)
        charakterbogenTargetPath = os.path.join(charakterbögenPath, charakterbogenFile)
        rulesPath = Wolke.Settings["Pfad-Regeln"]
        dtRulesFile = "IlarisAdvanced10.xml"
        dtRulesFilePath = os.path.join(rootdir, "Data", dtRulesFile)
        rulesTargetPath = os.path.join(rulesPath, dtRulesFile)

        if os.path.isfile(dtRulesFilePath) and os.path.isdir(rulesPath):
            #copy drachentöter charakterbogen to charakterbögen path (overwrite if there is a new rules file)
            restart = False
            if os.path.isfile(charakterbogenFilePath) and os.path.isdir(charakterbögenPath):
                if not os.path.isfile(charakterbogenTargetPath) or not os.path.isfile(rulesTargetPath):
                    shutil.copy2(charakterbogenFilePath, charakterbogenTargetPath)
                    shutil.copy2(os.path.splitext(charakterbogenFilePath)[0] + ".ini", os.path.splitext(charakterbogenTargetPath)[0] + ".ini")
                    restart = True
            
            #copy drachentöter rules file to rules path
            if not os.path.isfile(rulesTargetPath):
                shutil.copy2(dtRulesFilePath, rulesTargetPath)
                messagebox = QtWidgets.QMessageBox()
                messagebox.setWindowTitle("Drachentöter Hausregeln aktivieren?")
                messagebox.setText("Die Drachentöter Regeln und der Charakterbogen wurden in die entsprechenden Pfade kopiert (siehe Sephrasto-Einstellungen).\n"\
                    "Sollen sie jetzt in den Einstellungen als Standard für neue Charaktere gesetzt werden?"\
                    "\n\nHinweis: Für bereits existierende Charaktere musst du Regeln und Charakterbogen manuell im Info-Tab des Charaktereditors ändern.")
                messagebox.setIcon(QtWidgets.QMessageBox.Question)
                messagebox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                messagebox.setDefaultButton(QtWidgets.QMessageBox.Yes)
                result = messagebox.exec()
                if result == QtWidgets.QMessageBox.Yes:
                    Wolke.Settings["Datenbank"] = dtRulesFile
                    Wolke.Settings["Bogen"] = os.path.splitext(charakterbogenFile)[0]
                    EinstellungenWrapper.save()

            if restart:
                EinstellungenWrapper.restartSephrasto()
                
    @staticmethod
    def getDescription():
        return "Das Drachentöter Plugin aktiviert die Hausregel-Datenbank und den Drachentöter Charakterbogen für dich und setzt alle Regeln um, die über die Datenbasis nicht einstellbar sind.\n"\
            "Einzelne Funktionen des Plugins können über die \"Drachentöter Plugin\" Datenbankeinstellungen angepasst oder deaktiviert werden."

    def changesCharacter(self):
        return self.db.einstellungen["Drachentöter Plugin: Ansehen"].wert

    def pluginsLoadedHandler(self, params):
        EventBus.doAction("drachentöter")

    def basisDatenbankGeladenHandler(self, params):
        self.db = params["datenbank"]
        disable = False
        if not self.db.hausregelDatei or not ("ilarisadvanced" in self.db.hausregelDatei.lower() or "drachentöter" in self.db.hausregelDatei.lower()):
            disable = True

        e = DatenbankEinstellung()
        e.name = "Drachentöter Plugin: Kulturkunde"
        e.beschreibung = "Fügt den Namen der aufgelisteten Fertigkeiten noch '(Kultur)' hinzu. Die Angabe erfolgt als kommaseparierte Liste."
        e.text = "" if disable else "Straßenkunde, Diplomatie, Mythenkunde, Darbietung"
        e.typ = "TextList"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "Drachentöter Plugin: Ansehen"
        e.beschreibung = "Zeigt das Ansehen im Beschreibung-Details Tab und speichert es in der Charakterdatei.\n" +\
            "Vorteile  können es durch Scripts modifizieren, hierfür stehen die Funktionen getAnsehenMod und modifyAnsehenMod zur Verfügung."
        e.text = "False" if disable else "True"
        e.typ = "Bool"
        self.db.loadElement(e)

    ##############################
    # Ansehen
    ###############################

    def charakterInstanziiertAnsehenHandler(self, params):
        if not self.db.einstellungen["Drachentöter Plugin: Ansehen"].wert:
            return
        char = params["charakter"]
        char.ansehenBasis = 0
        char.ansehenMod = 0
        char.ansehen = 0
        char.charakterScriptAPI["getAnsehenMod"] = lambda: char.ansehenMod
        char.charakterScriptAPI["modifyAnsehenMod"] = lambda ansehenMod: setattr(char, 'ansehenMod', char.ansehenMod + ansehenMod)

    def preCharakterAktualisierenAnsehenHandler(self, params):
        if not self.db.einstellungen["Drachentöter Plugin: Ansehen"].wert:
            return
        char = params["charakter"]
        char.ansehenMod = 0

    def postCharakterAktualisierenAnsehenHandler(self, params):
        if not self.db.einstellungen["Drachentöter Plugin: Ansehen"].wert:
            return
        char = params["charakter"]
        privCount = 0
        for vort in char.vorteile:
            if vort.startswith("Privilegien"):
                privCount += 1
        if privCount > 0:
            char.ansehenMod -= privCount -1
        char.ansehen = char.ansehenBasis + char.ansehenMod

    def provideBeschreibungDetailsWrapperHook(self, base, params):
        if not self.db.einstellungen["Drachentöter Plugin: Ansehen"].wert:
            return base

        self.lblAnsehen = QtWidgets.QLabel("Ansehen")
        self.lblAnsehen.setProperty("class", "h4")

        self.sbAnsehen = QtWidgets.QSpinBox()
        self.sbAnsehen.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
        self.sbAnsehen.valueChanged.connect(self.onAnsehenChanged)

        self.labelAnsehenMod = QtWidgets.QLabel()

        self.ansehenLayout = QtWidgets.QHBoxLayout()
        self.ansehenLayout.addWidget(self.sbAnsehen)
        self.ansehenLayout.addWidget(self.labelAnsehenMod)

        class DTBeschreibungDetailsWrapper(base):
            def __init__(self2):
                super().__init__()
                # Remove first hintergrund row and move hintergrund label down by one row
                widgetItem = self2.ui.gridLayout_2.itemAtPosition(6, 4)
                if widgetItem and widgetItem.widget():
                    widgetItem.widget().setParent(None)

                widgetItem = self2.ui.gridLayout_2.itemAtPosition(5, 4)
                if widgetItem and widgetItem.widget():
                    self2.ui.gridLayout_2.addWidget(widgetItem.widget(), 6, 4, 1, 2)

                # Add ansehen
                self2.ui.gridLayout_2.addWidget(self.lblAnsehen, 5, 4)
                self2.ui.gridLayout_2.addLayout(self.ansehenLayout, 5, 5)

                self2.form.setTabOrder(self2.ui.leTitel, self.sbAnsehen)
                self2.form.setTabOrder(self.sbAnsehen, self2.ui.leHintergrund1)

            def load(self2):
                super().load()
                self.labelAnsehenMod.setText("  + " + str(Wolke.Char.ansehenMod))
                self.sbAnsehen.setMinimum(-8 - Wolke.Char.ansehenMod)
                self.sbAnsehen.setMaximum(8 - Wolke.Char.ansehenMod)
                self.sbAnsehen.setValue(Wolke.Char.ansehenBasis)

        return DTBeschreibungDetailsWrapper

    def onAnsehenChanged(self):
        Wolke.Char.ansehenBasis = self.sbAnsehen.value()
        EventBus.doAction("charaktereditor_modified")

    def charakterDeserialisiertAnsehenHandler(self, params):
        if not self.db.einstellungen["Drachentöter Plugin: Ansehen"].wert:
            return     
        deserializer = params["deserializer"]
        
        char = params["charakter"]
        if deserializer.find('BeschreibungDetails'):
            char.ansehenBasis = deserializer.getNestedInt('ansehen', 0)
            deserializer.end() #BeschreibungDetails                       

    def charakterSerialisiertAnsehenHandler(self, params):
        if not self.db.einstellungen["Drachentöter Plugin: Ansehen"].wert:
            return
        serializer = params["serializer"]
        char = params["charakter"]
        if serializer.find('BeschreibungDetails'):
            serializer.setNested('ansehen', char.ansehenBasis)
            serializer.end() #BeschreibungDetails

    def pdfExportAnsehenHook(self, fields, params):
        if not self.db.einstellungen["Drachentöter Plugin: Ansehen"].wert:
            return fields

        fields['Ansehen'] = str(Wolke.Char.ansehen) + " | PW " + str(abs(Wolke.Char.ansehen) * 2)
        return fields

    ###############################
    # Kulturkunde
    ###############################

    def pdfExportKulturkundeHook(self, fields, params):
        fertNameToKey = {}
        for k,v in fields.items():
            if k.startswith("Fertigkeit") and k.endswith("NA"):
                fertNameToKey[v] = k[:-2]

        for name in self.db.einstellungen["Drachentöter Plugin: Kulturkunde"].wert:
            if name in fertNameToKey:
                key = fertNameToKey[name] + "NA"
                fields[key] = fields[key] + " (Kultur)"
        return fields