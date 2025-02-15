from PySide6 import QtWidgets, QtCore, QtGui
import os.path
import logging
from Tierbegleiter import TierbegleiterDatenbank
from Tierbegleiter import TierbegleiterTypes
from Wolke import Wolke
import PdfSerializer
import copy
import tempfile
import lxml.etree as etree
import math
from PySide6.QtGui import QPixmap
import base64
import platform
from shutil import which
import re
from QtUtils.TextTagCompleter import TextTagCompleter
from Hilfsmethoden import Hilfsmethoden
from Charakterbogen import Charakterbogen
import shutil
from QtUtils.ProgressDialogExt import ProgressDialogExt

class TierbegleiterEditor(object):
    def __init__(self):
        self.datenbank = TierbegleiterDatenbank.TierbegleiterDatenbank()
        self.attribute = ["KO", "MU", "GE", "KK", "IN", "KL", "CH", "FF", "WS", "RS", "BE", "WS*", "MR", "GS", "GS2", "TP", "INI", "AT", "VT"]
        self.charakterbogen = Charakterbogen() # use default settings
        self.charakterbogen.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data", "Tierbegleiterbogen.ini"))

        self.attributModifiers = {}
        self.talentModifiers = {}
        self.vorteilModifiers = []
        self.waffen = []
        self.savepath = ""

        self.characterImage = None
        self.currentlyLoading = False

    def setupMainForm(self):
        if "WindowSize-TierbegleiterPlugin" in Wolke.Settings:
            windowSize = Wolke.Settings["WindowSize-TierbegleiterPlugin"]
            self.formMain.resize(windowSize[0], windowSize[1])

        self.ui.splitter.adjustSize()
        width = self.ui.splitter.size().width()
        self.ui.splitter.setSizes([int(width*0.6), int(width*0.4)])

        self.inventory = [self.ui.leAusruestung1, self.ui.leAusruestung2, self.ui.leAusruestung3, self.ui.leAusruestung4, self.ui.leAusruestung5, self.ui.leAusruestung6, self.ui.leAusruestung7, self.ui.leAusruestung8, self.ui.leAusruestung9, self.ui.leAusruestung10,
                     self.ui.leAusruestung11, self.ui.leAusruestung12, self.ui.leAusruestung13, self.ui.leAusruestung14, self.ui.leAusruestung15, self.ui.leAusruestung16, self.ui.leAusruestung17, self.ui.leAusruestung18, self.ui.leAusruestung19, self.ui.leAusruestung20]
        
        self.vorteile = []
        self.vorteilCompleter = []
        for i in range(1, 15):
            leVorteil = getattr(self.ui, "leVorteil" + str(i))
            leVorteil.editingFinished.connect(self.stateChanged)
            self.vorteilCompleter.append(TextTagCompleter(leVorteil, self.datenbank.tiervorteile.keys()))
            self.vorteile.append(leVorteil)

        self.talente = []
        self.talentCompleter = []
        for i in range(1, 9):
            leTalent = getattr(self.ui, "leTalent" + str(i))
            leTalent.editingFinished.connect(self.stateChanged)
            self.talentCompleter.append(TextTagCompleter(leTalent, self.datenbank.talente))
            self.talente.append(leTalent)

        self.talentWerte = []
        for i in range(1, 9):
            sbTalent = getattr(self.ui, "sbTalent" + str(i))
            sbTalent.valueChanged.connect(self.stateChanged)
            self.talentWerte.append(sbTalent)
        
        self.ui.cbTier.addItems(sorted(self.datenbank.tierbegleiter.keys()))
        self.ui.cbTier.setCurrentIndex(0)
        self.updateTier()

        self.ui.cbTier.currentIndexChanged.connect(self.updateTier)
        self.ui.cbTier.currentIndexChanged.connect(self.stateChanged)
        self.ui.sbReiten.valueChanged.connect(self.stateChanged)
        self.ui.sbRK.valueChanged.connect(self.stateChanged)
        self.ui.sbKO.valueChanged.connect(self.stateChanged)
        self.ui.sbMU.valueChanged.connect(self.stateChanged)
        self.ui.sbGE.valueChanged.connect(self.stateChanged)
        self.ui.sbKK.valueChanged.connect(self.stateChanged)
        self.ui.sbIN.valueChanged.connect(self.stateChanged)
        self.ui.sbKL.valueChanged.connect(self.stateChanged)
        self.ui.sbCH.valueChanged.connect(self.stateChanged)
        self.ui.sbFF.valueChanged.connect(self.stateChanged)
        self.ui.sbAT.valueChanged.connect(self.stateChanged)
        self.ui.sbVT.valueChanged.connect(self.stateChanged)
        self.ui.sbGS.valueChanged.connect(self.stateChanged)
        self.ui.sbRS.valueChanged.connect(self.stateChanged)
        self.ui.sbBE.valueChanged.connect(self.stateChanged)
        self.ui.sbTP.valueChanged.connect(self.stateChanged)
        self.ui.sbINI.valueChanged.connect(self.stateChanged)
        self.ui.sbMR.valueChanged.connect(self.stateChanged)
        self.ui.sbWS.valueChanged.connect(self.stateChanged)

        self.ui.btnSavePdf.clicked.connect(self.savePdfClickedHandler)
        self.ui.buttonLoad.clicked.connect(self.loadClickedHandler)
        self.ui.buttonSave.clicked.connect(self.saveClickedHandler)
        self.ui.buttonQuicksave.clicked.connect(self.quicksaveClickedHandler)

        self.labelImageText = self.ui.labelImage.text()
        self.ui.buttonLoadImage.clicked.connect(self.buttonLoadImageClicked)
        self.ui.buttonDeleteImage.clicked.connect(self.buttonDeleteImageClicked)
        
        self.ui.checkRegeln.setChecked(Wolke.Settings['Cheatsheet'])
        self.ui.spinRegelnGroesse.setValue(Wolke.Settings['Cheatsheet-Fontsize'])
        self.ui.checkEditierbar.setChecked(Wolke.Settings['Formular-Editierbarkeit'])

        self.stateChanged()
        self.updateTitlebar()

        self.formMain.closeEvent = self.closeEvent

    def closeEvent(self,event):
        Wolke.Settings["WindowSize-TierbegleiterPlugin"] = [self.formMain.size().width(), self.formMain.size().height()]

    def loadClickedHandler(self):
        if os.path.isdir(Wolke.Settings['Pfad-Chars']):
            startDir = Wolke.Settings['Pfad-Chars']
        else:
            startDir = ""
        spath, _ = QtWidgets.QFileDialog.getOpenFileName(None,"Tierbegleiter laden...",startDir,"XML-Datei (*.xml)")
        if spath == "":
            return
        if not spath.endswith(".xml"):
            spath = spath + ".xml"

        self.savepath = spath
        if not self.savepath:
            return
        self.currentlyLoading = True

        root = etree.parse(self.savepath).getroot()
        self.ui.leName.setText(root.find('Name').text)
        self.ui.teAussehen.setPlainText(root.find('Aussehen').text)
        self.ui.leNahrung.setText(root.find('Nahrung').text)
        self.ui.teHintergrund.setPlainText(root.find('Hintergrund').text)
        self.ui.cbTier.setCurrentText(root.find('Tier').text)
        self.ui.sbRK.setValue(int(root.find('Reiterkampf').text))
        self.ui.sbReiten.setValue(int(root.find('ReitenPW').text))

        self.ui.sbKO.setValue(int(root.find('KO').text))
        self.ui.sbMU.setValue(int(root.find('MU').text))
        self.ui.sbGE.setValue(int(root.find('GE').text))
        self.ui.sbKK.setValue(int(root.find('KK').text))
        self.ui.sbIN.setValue(int(root.find('IN').text))
        self.ui.sbKL.setValue(int(root.find('KL').text))
        self.ui.sbCH.setValue(int(root.find('CH').text))
        self.ui.sbFF.setValue(int(root.find('FF').text))
        self.ui.sbAT.setValue(int(root.find('AT').text))
        self.ui.sbVT.setValue(int(root.find('VT').text))
        self.ui.sbGS.setValue(int(root.find('GS').text))
        self.ui.sbRS.setValue(int(root.find('RS').text))
        self.ui.sbBE.setValue(int(root.find('BE').text))
        self.ui.sbTP.setValue(int(root.find('TP').text))
        self.ui.sbINI.setValue(int(root.find('INI').text))
        self.ui.sbMR.setValue(int(root.find('MR').text))
        self.ui.sbWS.setValue(int(root.find('WS').text))

        i = 0
        for vorteilNode in root.findall('Vorteile/'):
            self.vorteile[i].setText(vorteilNode.attrib['name'])
            i += 1
            if i == len(self.vorteile):
                break

        i = 0
        for talentNode in root.findall('Talente/'):
            self.talente[i].setText(talentNode.attrib['name'])
            self.talentWerte[i].setValue(int(talentNode.attrib['wert']))
            i += 1
            if i == len(self.talente):
                break

        #self.ui.leVorteile.setText(root.find('WeitereVorteile').text)

        if root.find('bild') is not None:
            byteArray = bytes(root.find('bild').text, 'utf-8')
            image = base64.b64decode(byteArray)
            self.characterImage = QtGui.QPixmap()
            self.characterImage.loadFromData(image)
            self.setImage(self.characterImage)

        ausruestung = root.findall('Ausrüstung/Gegenstand')
        count = 0
        for inventoryLine in self.inventory:
            inventoryLine.setText(ausruestung[count].text)
            count += 1

        if root.find('RegelnAnhängen') is not None:
            self.ui.checkRegeln.setChecked(root.find('RegelnAnhängen').text == "1")
        if root.find('RegelnGrösse') is not None:
            self.ui.spinRegelnGroesse.setValue(int(root.find('RegelnGrösse').text))
        if root.find('FormularEditierbarkeit') is not None:
            self.ui.checkEditierbar.setChecked(root.find('FormularEditierbarkeit').text == "1")

        self.currentlyLoading = False
        self.updateTitlebar()
        self.stateChanged()

    def updateTitlebar(self):
        file = " - Neuer Tierbegleiter"
        if self.savepath:
            file = " - " + os.path.basename(self.savepath)

        rules = ""
        if Wolke.Settings['Datenbank']:
           rules = " (" + os.path.splitext(os.path.basename(Wolke.Settings['Datenbank']))[0] + ")"
        self.formMain.setWindowTitle("Sephrasto" + file + rules)

    def saveClickedHandler(self):
        if self.savepath != "":
            startDir = self.savepath
        elif os.path.isdir(Wolke.Settings['Pfad-Chars']):
            startDir = os.path.join(Wolke.Settings['Pfad-Chars'], self.ui.leName.text())
        else:
            startDir = ""
        spath, _ = QtWidgets.QFileDialog.getSaveFileName(None,"Tierbegleiter speichern...",startDir,"XML-Datei (*.xml)")
        if spath == "":
            return
        if ".xml" not in spath:
            spath = spath + ".xml"
            
        self.savepath = spath
        self.updateTitlebar()
        self.quicksaveClickedHandler()

    def quicksaveClickedHandler(self):
        if self.savepath == "":
            self.saveClickedHandler()
            return

        root = etree.Element('Tierbegleiter')
        etree.SubElement(root, 'Name').text = self.ui.leName.text()
        etree.SubElement(root, 'Nahrung').text = self.ui.leNahrung.text()
        etree.SubElement(root, 'Aussehen').text = self.ui.teAussehen.toPlainText()
        etree.SubElement(root, 'Tier').text = self.ui.cbTier.currentText()
        etree.SubElement(root, 'Hintergrund').text = self.ui.teHintergrund.toPlainText()
        etree.SubElement(root, 'Reiterkampf').text = str(self.ui.sbRK.value())
        etree.SubElement(root, 'ReitenPW').text = str(self.ui.sbReiten.value())

        etree.SubElement(root, 'KO').text = str(self.ui.sbKO.value())
        etree.SubElement(root, 'MU').text = str(self.ui.sbMU.value())
        etree.SubElement(root, 'GE').text = str(self.ui.sbGE.value())
        etree.SubElement(root, 'KK').text = str(self.ui.sbKK.value())
        etree.SubElement(root, 'IN').text = str(self.ui.sbIN.value())
        etree.SubElement(root, 'KL').text = str(self.ui.sbKL.value())
        etree.SubElement(root, 'CH').text = str(self.ui.sbCH.value())
        etree.SubElement(root, 'FF').text = str(self.ui.sbFF.value())
        etree.SubElement(root, 'AT').text = str(self.ui.sbAT.value())
        etree.SubElement(root, 'VT').text = str(self.ui.sbVT.value())
        etree.SubElement(root, 'GS').text = str(self.ui.sbGS.value())
        etree.SubElement(root, 'RS').text = str(self.ui.sbRS.value())
        etree.SubElement(root, 'BE').text = str(self.ui.sbBE.value())
        etree.SubElement(root, 'TP').text = str(self.ui.sbTP.value())
        etree.SubElement(root, 'INI').text = str(self.ui.sbINI.value())
        etree.SubElement(root, 'MR').text = str(self.ui.sbMR.value())
        etree.SubElement(root, 'WS').text = str(self.ui.sbWS.value())
        
        vorteileNode = etree.SubElement(root, 'Vorteile')
        for leVorteil in self.vorteile:
            vorteil = leVorteil.text()
            etree.SubElement(vorteileNode, 'Vorteil').attrib['name'] = vorteil

        talenteNode = etree.SubElement(root, 'Talente')
        for i in range(0, len(self.talente)):
            leTalent = self.talente[i]
            sbTalent = self.talentWerte[i]
            
            talentNode = etree.SubElement(talenteNode, 'Talent')
            talentNode.attrib['name'] = leTalent.text()
            talentNode.attrib['wert'] = str(sbTalent.value())

        #etree.SubElement(root, 'WeitereVorteile').text = self.ui.leVorteile.text()

        if self.characterImage:
            buffer = QtCore.QBuffer()
            buffer.open(QtCore.QIODevice.WriteOnly);
            self.characterImage.save(buffer, "JPG")
            etree.SubElement(root,'bild').text = base64.b64encode(buffer.data().data())

        ausruestung = etree.SubElement(root, 'Ausrüstung')
        for inventoryLine in self.inventory:
            etree.SubElement(ausruestung, 'Gegenstand').text = inventoryLine.text()

        etree.SubElement(root, 'RegelnAnhängen').text = "1" if self.ui.checkRegeln.isChecked() else "0"
        etree.SubElement(root, 'RegelnGrösse').text = str(self.ui.spinRegelnGroesse.value())
        etree.SubElement(root, 'FormularEditierbarkeit').text = "1" if self.ui.checkEditierbar.isChecked() else "0"

        doc = etree.ElementTree(root)
        with open(self.savepath,'wb') as file:
            file.seek(0)
            file.truncate()
            doc.write(file, encoding='UTF-8', pretty_print=True)
            file.truncate()

    def savePdfClickedHandler(self):       
        if not os.path.isfile(self.charakterbogen.filePath):
            messagebox = QtWidgets.QMessageBox()
            messagebox.setWindowTitle("Fehler!")
            messagebox.setText("Konnte " + self.charakterbogen.filePath + " nicht im Pluginordner finden")
            messagebox.setIcon(QtWidgets.QMessageBox.Critical)
            messagebox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            messagebox.exec()
            return
        
        if os.path.isdir(Wolke.Settings['Pfad-Chars']):
            startDir = Wolke.Settings['Pfad-Chars']
        else:
            startDir = ""

        startDir = os.path.join(startDir, self.ui.leName.text() or os.path.splitext(os.path.basename(self.savepath))[0] or "Tierbegleiter")
            
        # Let the user choose a saving location and name
        spath, _ = QtWidgets.QFileDialog.getSaveFileName(None,"Tierbegleiterbogen erstellen...",startDir,"PDF-Datei (*.pdf)")
        if spath == "":
            return
        if ".pdf" not in spath:
            spath = spath + ".pdf"
            
        try:
            self.createPdf(spath)
        except Exception as e:
            logging.error("Exception: " + str(e))
            infoBox = QtWidgets.QMessageBox()
            infoBox.setIcon(QtWidgets.QMessageBox.Information)
            infoBox.setText("PDF-Erstellung fehlgeschlagen!")
            infoBox.setInformativeText("Beim Erstellen des Tierbegleiterbogens ist ein Fehler aufgetreten.")
            infoBox.setWindowTitle("PDF-Erstellung fehlgeschlagen.")
            infoBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            infoBox.setEscapeButton(QtWidgets.QMessageBox.Close)  
            infoBox.exec()
        return

    def updateTier(self):
        tier = self.datenbank.tierbegleiter[self.ui.cbTier.currentText()]
        self.ui.leNahrung.setText(tier.futter)

        groessen = ["Winziges", "Sehr kleines", "Kleines", "Mittelgroßes", "Großes", "Sehr großes"]
        self.ui.teAussehen.setPlainText(groessen[tier.groesse] + " Tier")

        self.ui.lblReiten.setVisible(tier.reittier == 1)
        self.ui.sbReiten.setVisible(tier.reittier == 1)
        self.ui.lblRK.setVisible(tier.reittier == 1)
        self.ui.sbRK.setVisible(tier.reittier == 1)

    def initKey(self, dict, key):
        if not key in dict:
            dict[key] = 0

    def gatherModifiers(self, allModifiers, attributModifiers, talentModifiers, vorteilModifiers):
        for mod in allModifiers:
            if mod.mod is not None:
                if mod.name in self.attribute:
                    self.initKey(attributModifiers, mod.name)
                    attributModifiers[mod.name] += mod.mod
                else:
                    self.initKey(talentModifiers, mod.name)
                    talentModifiers[mod.name] += mod.mod
            else:
                vorteilModifiers.append(copy.copy(mod))

    def modifiersToString(self, attributModifiers, talentModifiers, vorteilModifiers, waffen = [], summary = False):
        attributModifiers = sorted(attributModifiers.items(), key = lambda x: self.attribute.index(x[0])) 
        talentModifiers = sorted(talentModifiers.items(), key = lambda x: x) 
        vorteilModifiers = sorted(vorteilModifiers, key = lambda mod : mod.name)
        lineStart = ""
        lineEnd = ". "
        boldStart = ""
        boldEnd = ""
        if summary:
            lineStart = "<p>"
            lineEnd = "</p>"
            boldStart = '<b>'
            boldEnd = '</b>'

        text = ""
        addTitle = len(attributModifiers) + len(talentModifiers) + len(vorteilModifiers) > 1

        if len(attributModifiers) > 0:
            text += lineStart
            if addTitle:
                text += boldStart + "Attribute: " + boldEnd
            text += ", ".join(['%s: %s' % (tuple[0], tuple[1]) if summary or tuple[1] < 0 else '%s: +%s' % (tuple[0], tuple[1]) for tuple in attributModifiers]) + lineEnd
        if len(talentModifiers) > 0:
            text += lineStart
            if addTitle:
                text += boldStart + "Talente: " + boldEnd
            text += ", ".join(['%s: %s' % (tuple[0], tuple[1]) if tuple[1] < 0 else '%s: +%s' % (tuple[0], tuple[1]) for tuple in talentModifiers]) + lineEnd
        if len(vorteilModifiers) > 0:
            text += lineStart
            if addTitle:
                text += boldStart + "Vorteile: " + boldEnd
            text += ", ".join([mod.name if (summary or not mod.wirkung) else mod.wirkung for mod in vorteilModifiers]) + lineEnd
        if len(waffen) > 0:
            text += lineStart + boldStart + "Waffen: " + boldEnd + lineEnd
            for w in waffen:
                text +=  lineStart + w.name + " (RW " + str(w.rw)
                text += ", AT " + (str(w.at) if w.at is not None else "-")
                text += ", VT " + (str(w.vt) if w.vt is not None else  "-" )
                text += ", TP "
                text += w.getTP()
                if w.eigenschaften:
                    text += ", " + w.eigenschaften
                text += ")" + lineEnd

        return text

    def updatePreview(self, label, modifiers, summary = False):
        attributModifiers = {}
        talentModifiers = {}
        vorteilModifiers = []
        self.gatherModifiers(modifiers, attributModifiers, talentModifiers, vorteilModifiers)
        label.setText(self.modifiersToString(attributModifiers, talentModifiers, vorteilModifiers, [], summary))

    def stateChanged(self):
        if self.currentlyLoading:
            return

        allModifiers = []
        self.ui.lblTier.setText("")

        for leVorteil in self.vorteile:
            vorteil = leVorteil.text()
            if not vorteil:
                continue
            if vorteil in self.datenbank.tiervorteile:
                allModifiers.append(self.datenbank.tiervorteile[vorteil])
            else:
                mod = TierbegleiterTypes.Modifikator()
                mod.name = vorteil
                allModifiers.append(mod)    

        attributModifiers = {}
        talentModifiers = {}
        vorteilModifiers = []
        waffen = []

        self.gatherModifiers(allModifiers, attributModifiers, talentModifiers, vorteilModifiers)

        # Default werte
        for attribut in self.attribute:
            if attribut != "GS2":
                self.initKey(attributModifiers, attribut)

        # Manuelle werte
        attributModifiers["KO"] += self.ui.sbKO.value()
        attributModifiers["MU"] += self.ui.sbMU.value()
        attributModifiers["GE"] += self.ui.sbGE.value()
        attributModifiers["KK"] += self.ui.sbKK.value()
        attributModifiers["IN"] += self.ui.sbIN.value()
        attributModifiers["KL"] += self.ui.sbKL.value()
        attributModifiers["CH"] += self.ui.sbCH.value()
        attributModifiers["FF"] += self.ui.sbFF.value()
        attributModifiers["AT"] += self.ui.sbAT.value()
        attributModifiers["VT"] += self.ui.sbVT.value()
        attributModifiers["GS"] += self.ui.sbGS.value()
        attributModifiers["RS"] += self.ui.sbRS.value()
        attributModifiers["BE"] += self.ui.sbBE.value()
        attributModifiers["TP"] += self.ui.sbTP.value()
        attributModifiers["INI"] += self.ui.sbINI.value()
        attributModifiers["MR"] += self.ui.sbMR.value()
        attributModifiers["WS"] += self.ui.sbWS.value()

        for i in range(0, len(self.talente)):
            leTalent = self.talente[i]
            if not leTalent.text():
                continue
            sbTalent = self.talentWerte[i] 
            talentModifiers[leTalent.text()] = sbTalent.value()

        # Label
        tier = self.datenbank.tierbegleiter[self.ui.cbTier.currentText()]

        tierLabelText = ""
        if tier.rassen:
            tierLabelText += tier.rassen + ". "

        self.ui.lblTier.setVisible(tierLabelText != "")
        self.ui.lblTier.setText(tierLabelText)

        # Attribute
        modGS = attributModifiers["GS"]
        del attributModifiers["GS"]
        self.gatherModifiers(tier.modifikatoren, attributModifiers, talentModifiers, vorteilModifiers)

        if "GS2" in attributModifiers:
            attributModifiers["GS"] = str(attributModifiers["GS"]) + "/" + str(attributModifiers["GS2"] + modGS)
            del attributModifiers["GS2"]
        else:
            attributModifiers["GS"] += modGS

        attributModifiers["WS*"] = attributModifiers["WS"] + attributModifiers["RS"]
        del attributModifiers["RS"]

        reiterkampfAT = 0
        reiterkampfVT = 0
        if "Reiterkampf WM" in talentModifiers:
            reiterkampfAT = talentModifiers["Reiterkampf WM"] + attributModifiers["AT"] - attributModifiers["BE"]
            reiterkampfVT = talentModifiers["Reiterkampf WM"] + attributModifiers["VT"] - attributModifiers["BE"]
            del talentModifiers["Reiterkampf WM"]

        waffen = copy.deepcopy(tier.waffen)
        for waffe in waffen:
            if waffe.plus is not None:
                waffe.plus += attributModifiers["TP"]
            if waffe.at is not None:
                waffe.at += attributModifiers["AT"] - attributModifiers["BE"]
            if waffe.vt is not None:
                waffe.vt += attributModifiers["VT"] - attributModifiers["BE"]

        if tier.reittier == 1:
            if len(waffen) > 0 :
                reitenWaffe = copy.copy(waffen[0])
                reitenWaffe.name = "Reiterkampf (" + reitenWaffe.name + ")"
                reitenWaffe.at = self.ui.sbReiten.value() + reiterkampfAT + self.ui.sbRK.value()
                reitenWaffe.vt = self.ui.sbReiten.value() + reiterkampfVT + self.ui.sbRK.value()
                reitenWaffe.plus += self.ui.sbRK.value()
                if reitenWaffe.eigenschaften:
                    reitenWaffe.eigenschaften += ", "
                reitenWaffe.eigenschaften += "AT +4 gegen kleinere Gegner"
                waffen.append(reitenWaffe)

            vorteilModifiers.append(copy.copy(self.datenbank.tiervorteile["Sturmangriff (Reiterkampf)"]))
            if self.ui.sbRK.value() == 0:
                vorteilModifiers[-1].name = vorteilModifiers[-1].name[:-1] + "-Stufe nicht ausreichend)"
            elif self.ui.sbRK.value() > 2:
                vorteilModifiers.append(self.datenbank.tiervorteile["Überrennen (Reiterkampf)"])

        del attributModifiers["TP"]
        del attributModifiers["AT"]
        del attributModifiers["VT"]

        for (key, value) in list(attributModifiers.items()):
            if value == 0:
                del attributModifiers[key]

        for (key, value) in list(talentModifiers.items()):
            if value == 0:
                del talentModifiers[key]

        self.attributModifiers = attributModifiers
        self.talentModifiers = talentModifiers
        self.vorteilModifiers = sorted(vorteilModifiers, key = lambda mod : mod.name)
        self.waffen = waffen

        text = self.modifiersToString(attributModifiers, talentModifiers, vorteilModifiers, waffen, True)
        self.ui.lblWerte.setText(text)

        tooltip = ""
        for vorteilMod in self.vorteilModifiers:
            if vorteilMod.wirkung:
                tooltip += "<b>" + vorteilMod.name + ":</b> " + vorteilMod.wirkung + "\n"     

        if tooltip:
            tooltip = tooltip[:-1].replace("\n", "<br>")
        self.ui.lblWerte.setToolTip(tooltip)

    def hasVorteil(self, name):
        tier = self.datenbank.tierbegleiter[self.ui.cbTier.currentText()]
        for vorteilMod in tier.modifikatoren:
            if vorteilMod.name == name:
                return True
        return False

    def setImage(self, pixmap):
        self.ui.labelImage.setPixmap(pixmap.scaled(self.ui.labelImage.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

    def buttonLoadImageClicked(self):
        spath, _ = QtWidgets.QFileDialog.getOpenFileName(None,"Bild laden...", "", "Bild Dateien (*.png *.jpg *.bmp)")
        if spath == "":
            return
        
        self.characterImage = QPixmap(spath).scaled(QtCore.QSize(260, 340), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.setImage(self.characterImage)

    def buttonDeleteImageClicked(self):
        self.characterImage = None
        self.ui.labelImage.setPixmap(QPixmap())
        self.ui.labelImage.setText(self.labelImageText)

    def categoryHeading(self, text):
        return "<h2>" + text + "</h2>"

    def ruleHeading(self, text):
        return "<h3>" + text + "</h3>"

    def createPdf(self, path):
        try:
            dlg = ProgressDialogExt(minimum = 0, maximum = 100)
            dlg.disableCancel()
            dlg.setWindowTitle("Exportiere Tierbegleiter")
            dlg.show()
            QtWidgets.QApplication.processEvents() #make sure the dialog immediatelly shows

            dlg.setLabelText("Befülle Formularfelder")
            fields = copy.copy(self.attributModifiers)
            fields["WSStern"] = fields["WS*"]

            if "KO" in fields:
                fields["DH"] = int(int(fields["KO"]) / 2)

            talentModifierList = []
            for key, value in self.talentModifiers.items():
                temp = [key,value]
                talentModifierList.append(temp)
            talentModifierList = sorted(talentModifierList)

            for i in range(0, self.charakterbogen.maxFertigkeiten):
                if i < len(talentModifierList):
                    fields['Talent.' + str(i)] = talentModifierList[i][0]
                    fields['TalentPW.' + str(i)] = talentModifierList[i][1]

            for i in range(0, self.charakterbogen.maxVorteile):
                if i < len(self.vorteilModifiers):
                    fields['Vorteil.' + str(i)] = self.vorteilModifiers[i].name

            fields["Name"] = self.ui.leName.text()

            tier = self.datenbank.tierbegleiter[self.ui.cbTier.currentText()]
            fields["Spezies"] = tier.name
            fields["Nahrung"] = self.ui.leNahrung.text()

            charsPerLine = 80
            text = self.ui.teHintergrund.toPlainText().split("\n")
            if len(text[-1]) < charsPerLine:
                text[-1] += " " * (int(charsPerLine * 1.5) - len(text[-1])) # space has less width, so add 50%
            fields["Hintergrund"] = "\n".join(text)

            text = self.ui.teAussehen.toPlainText().split("\n")
            if len(text[-1]) < charsPerLine:
                text[-1] += " " * (int(charsPerLine * 1.5) - len(text[-1])) # space has less width, so add 50%
            fields["Aussehen"] = "\n".join(text)

            for i in range(0, 3):
                if i < len(self.waffen):
                    fields['Waffe.' + str(i)] = self.waffen[i].name
                    fields['WaffeRW.' + str(i)] = self.waffen[i].rw
                    fields['WaffeEig.' + str(i)] = self.waffen[i].eigenschaften
                    fields['WaffeAT.' + str(i)] = self.waffen[i].at if self.waffen[i].at is not None else "-"
                    fields['WaffeVT.' + str(i)] = self.waffen[i].vt if self.waffen[i].vt is not None else "-"
                    fields['WaffeTP.' + str(i)] = self.waffen[i].getTP()

            for i in range(len(self.inventory)):
                fields['Ausruestung.' + str(i)] = self.inventory[i].text()

            tiervorteile = [vorteilMod for vorteilMod in self.vorteilModifiers if vorteilMod.name in self.datenbank.tiervorteile]
            for waffe in self.waffen:
                eigenschaften = list(map(str.strip, waffe.eigenschaften.split(",")))
                for eig in eigenschaften:
                    name = re.sub(r"\((.*?)\)", "", eig, re.UNICODE).strip() # remove parameters
                    if name in self.datenbank.tiervorteile:
                        hatVorteil = False
                        for vorteilMod in tiervorteile:
                            if vorteilMod.name == name:
                              hatVorteil = True
                              break
                        if hatVorteil:
                            continue
                        tiervorteile.append(self.datenbank.tiervorteile[name])
            tiervorteile = sorted(tiervorteile, key = lambda vort: vort.name)

            addRules = self.ui.checkRegeln.isChecked() and (len(tiervorteile) > 0)
            handle, tmpTierbegleiterPath = tempfile.mkstemp()
            os.close(handle)

            flatten = not self.ui.checkEditierbar.isChecked()
            PdfSerializer.write_pdf(self.charakterbogen.filePath, fields, tmpTierbegleiterPath, flatten)

            bookmarks = []
            for i in range(PdfSerializer.getNumPages(self.charakterbogen.filePath)):
                text = "Charakterbogen"
                if i < len(self.charakterbogen.seitenbeschreibungen):
                    text = self.charakterbogen.seitenbeschreibungen[i]
                bookmarks.append(PdfSerializer.PdfBookmark("S. " + str(i+1) + " - " + text, i+1))
            i += 1

            if self.characterImage is not None:
                # The approach is to convert the image to pdf and stamp it over the char sheet with pdftk
                dlg.setLabelText("Stemple Charakterbild")
                dlg.setValue(30)
                buffer = QtCore.QBuffer()
                buffer.open(QtCore.QIODevice.WriteOnly);
                self.characterImage.save(buffer, "JPG")
                image = buffer.data().data()
                image_pdf = PdfSerializer.convertJpgToPdf(image, self.charakterbogen.getImageSize(0, [193, 254]), self.charakterbogen.getImageOffset(0), self.charakterbogen.getPageLayout())
                stamped_pdf = PdfSerializer.stamp(tmpTierbegleiterPath, image_pdf)
                os.remove(image_pdf)
                os.remove(tmpTierbegleiterPath)
                tmpTierbegleiterPath = stamped_pdf

            if addRules:
                dlg.setLabelText("Erstelle Regelanhang")
                dlg.setValue(50)
                fields = {}
                rules = ["<h1>Regeln für " + self.ui.leName.text() + "</h1>"]

                if sum(1 for v in self.vorteilModifiers if not v.manöver) > 0:
                    rules.append(self.categoryHeading("Tiervorteile"))
                    for vorteilMod in tiervorteile:
                        if vorteilMod.wirkung and not vorteilMod.manöver:
                            rules.append("<article>")
                            rules.append(self.ruleHeading(vorteilMod.name))
                            rules.append(vorteilMod.wirkung)
                            rules.append("</article>")

                if sum(1 for v in self.vorteilModifiers if v.manöver) > 0:
                    rules.append(self.categoryHeading("Manöver und Waffeneigenschaften"))
                    for vorteilMod in tiervorteile:
                        if vorteilMod.wirkung and vorteilMod.manöver:
                            rules.append("<article>")
                            rules.append(self.ruleHeading(vorteilMod.name))
                            rules.append(vorteilMod.wirkung)
                            rules.append("</article>")
                rules = "".join(rules).replace("\n", "<br>")
                html = ""
                with open(self.charakterbogen.regelanhangPfad, 'r', encoding="utf-8") as infile:
                    rules = rules.replace("$sephrasto_dir$", "file:///" + os.getcwd().replace('\\', '/'))
                    rules = rules.replace("$regeln_dir$", "file:///" + Wolke.Settings['Pfad-Regeln'].replace('\\', '/'))
                    rules = rules.replace("$plugins_dir$", "file:///" + Wolke.Settings['Pfad-Plugins'].replace('\\', '/'))
                    html = infile.read()
                    html = html.replace("{sephrasto_dir}", "file:///" + os.getcwd().replace('\\', '/'))
                    html = html.replace("{rules_content}", rules)
                    html = html.replace("{rules_font_size}", str(self.ui.spinRegelnGroesse.value()))
                baseUrl = QtCore.QUrl.fromLocalFile(QtCore.QFileInfo(self.charakterbogen.regelanhangPfad).absoluteFilePath())
                rulesFile = PdfSerializer.convertHtmlToPdf(html, baseUrl, self.charakterbogen.getRegelanhangPageLayout(), 100)

                for j in range(1, PdfSerializer.getNumPages(rulesFile)+1):
                    bookmarks.append(PdfSerializer.PdfBookmark("S. " + str(i+1) + " - Regelanhang " + str(j), i+1))
                    i += 1

                if self.charakterbogen.regelanhangHintergrundPfad:
                    tmpRulesFile = PdfSerializer.addBackground(rulesFile, self.charakterbogen.regelanhangHintergrundPfad)
                    os.remove(rulesFile)
                    rulesFile = tmpRulesFile

                tmp = PdfSerializer.concat([tmpTierbegleiterPath, rulesFile])
                os.remove(tmpTierbegleiterPath)
                os.remove(rulesFile)
                tmpTierbegleiterPath = tmp

            dlg.setLabelText("Füge Lesezeichen hinzu")
            dlg.setValue(80)
            PdfSerializer.addBookmarks(tmp, bookmarks, path)
            os.remove(tmp)

            dlg.setLabelText("Optimiere Dateigröße")
            dlg.setValue(90)
            PdfSerializer.squeeze(path, path)
            dlg.setValue(100)
        finally:
            dlg.hide()
            dlg.deleteLater()

        if Wolke.Settings['PDF-Open']:
            Hilfsmethoden.openFile(path)