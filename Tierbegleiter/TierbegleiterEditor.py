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
        self.zuchteigenschaftenValid = True
        self.attribute = ["KO", "MU", "GE", "KK", "IN", "KL", "CH", "FF", "WS", "RS", "WS*", "MR", "GS", "GS2", "TP", "INI", "WM"]
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

        self.inventory = [self.ui.leAusruestung1, self.ui.leAusruestung2, self.ui.leAusruestung3, self.ui.leAusruestung4, self.ui.leAusruestung5, self.ui.leAusruestung6, self.ui.leAusruestung7, self.ui.leAusruestung8, self.ui.leAusruestung9, self.ui.leAusruestung10,
                     self.ui.leAusruestung11, self.ui.leAusruestung12, self.ui.leAusruestung13, self.ui.leAusruestung14, self.ui.leAusruestung15, self.ui.leAusruestung16, self.ui.leAusruestung17, self.ui.leAusruestung18, self.ui.leAusruestung19, self.ui.leAusruestung20]
        self.ui.cbTier.addItems(sorted(self.datenbank.tierbegleiter.keys()))
        self.ui.cbTier.setCurrentIndex(0)
        self.ui.cbZucht.setCurrentIndex(3)
        self.ui.cbGuteEig1.addItems(sorted(self.datenbank.guteZuchteigenschaften.keys()))
        self.ui.cbGuteEig1.setCurrentIndex(0)
        self.ui.cbGuteEig2.addItems(sorted(self.datenbank.guteZuchteigenschaften.keys()))
        self.ui.cbGuteEig2.setCurrentIndex(1)
        self.ui.cbGuteEig3.addItems(sorted(self.datenbank.guteZuchteigenschaften.keys()))
        self.ui.cbGuteEig3.setCurrentIndex(2)
        self.ui.cbSchlechteEig1.addItems(sorted(self.datenbank.schlechteZuchteigenschaften.keys()))
        self.ui.cbSchlechteEig1.setCurrentIndex(0)
        self.ui.cbSchlechteEig2.addItems(sorted(self.datenbank.schlechteZuchteigenschaften.keys()))
        self.ui.cbSchlechteEig2.setCurrentIndex(1)
        self.updateAusbildungen()

        self.ui.checkAutoHintergrund.stateChanged.connect(self.stateChanged)
        self.ui.cbTier.currentIndexChanged.connect(self.updateAusbildungen)
        self.ui.cbTier.currentIndexChanged.connect(self.updateTier)
        self.ui.cbTier.currentIndexChanged.connect(self.stateChanged)
        self.ui.cbZucht.currentIndexChanged.connect(self.stateChanged)
        self.ui.cbGuteEig1.currentIndexChanged.connect(self.stateChanged)
        self.ui.cbGuteEig2.currentIndexChanged.connect(self.stateChanged)
        self.ui.cbGuteEig3.currentIndexChanged.connect(self.stateChanged)
        self.ui.cbSchlechteEig1.currentIndexChanged.connect(self.stateChanged)
        self.ui.cbSchlechteEig2.currentIndexChanged.connect(self.stateChanged)
        self.ui.cbAusbildung.currentIndexChanged.connect(self.ausbildungChanged)
        self.ui.cbAusbildung.currentIndexChanged.connect(self.stateChanged)
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
        self.ui.sbKampfwerte.valueChanged.connect(self.stateChanged)
        self.ui.sbGS.valueChanged.connect(self.stateChanged)
        self.ui.sbRS.valueChanged.connect(self.stateChanged)
        self.ui.leVorteile.editingFinished.connect(self.stateChanged)

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

        for i in range(self.ui.tabWidget.tabBar().count()):
            self.ui.tabWidget.tabBar().setTabTextColor(i, QtGui.QColor(Wolke.HeadingColor))

        self.ui.tabWidget.setStyleSheet('QTabBar { font-weight: bold; font-size: ' + str(Wolke.Settings["FontHeadingSize"]) + 'pt; font-family: \"' + Wolke.Settings["FontHeading"] + '\"; }')

        if not self.datenbank.iaZuchtAusbildung:
            if hasattr(self.ui.tabWidget, "setTabVisible"):
                self.ui.tabWidget.setTabVisible(1, False)
            self.ui.checkAutoHintergrund.setVisible(False)
            self.ui.groupBox.setTitle("Vorschau")

        self.vorteilCompleter = TextTagCompleter(self.ui.leVorteile, self.datenbank.tiervorteile.keys())

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
        self.ui.checkAutoHintergrund.setChecked(root.find('AutoHintergrund').text == "1")
        self.ui.teHintergrund.setPlainText(root.find('Hintergrund').text)
        self.ui.cbTier.setCurrentText(root.find('Tier').text)
        self.ui.sbRK.setValue(int(root.find('Reiterkampf').text))
        self.ui.sbReiten.setValue(int(root.find('ReitenPW').text))
        self.ui.cbZucht.setCurrentIndex(int(root.find('Zucht').text))
        guteEigenschaften = root.findall('GuteEigenschaften/Eigenschaft')
        self.ui.cbGuteEig1.setCurrentText(guteEigenschaften[0].text)
        self.ui.cbGuteEig2.setCurrentText(guteEigenschaften[1].text)
        self.ui.cbGuteEig3.setCurrentText(guteEigenschaften[2].text)
        schlechteEigenschaften = root.findall('SchlechteEigenschaften/Eigenschaft')
        self.ui.cbSchlechteEig1.setCurrentText(schlechteEigenschaften[0].text)
        self.ui.cbSchlechteEig2.setCurrentText(schlechteEigenschaften[1].text)
        self.ui.cbAusbildung.setCurrentText(root.find('Ausbildung').text)

        self.ui.sbKO.setValue(int(root.find('KO').text))
        self.ui.sbMU.setValue(int(root.find('MU').text))
        self.ui.sbGE.setValue(int(root.find('GE').text))
        self.ui.sbKK.setValue(int(root.find('KK').text))
        self.ui.sbIN.setValue(int(root.find('IN').text))
        self.ui.sbKL.setValue(int(root.find('KL').text))
        self.ui.sbCH.setValue(int(root.find('CH').text))
        self.ui.sbFF.setValue(int(root.find('FF').text))
        self.ui.sbKampfwerte.setValue(int(root.find('WM').text))
        self.ui.sbGS.setValue(int(root.find('GS').text))
        self.ui.sbRS.setValue(int(root.find('RS').text))

        self.ui.leVorteile.setText(root.find('WeitereVorteile').text)

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
        etree.SubElement(root, 'AutoHintergrund').text = "1" if self.ui.checkAutoHintergrund.isChecked() else "0"
        etree.SubElement(root, 'Hintergrund').text = self.ui.teHintergrund.toPlainText()
        etree.SubElement(root, 'Reiterkampf').text = str(self.ui.sbRK.value())
        etree.SubElement(root, 'ReitenPW').text = str(self.ui.sbReiten.value())
        etree.SubElement(root, 'Zucht').text = str(self.ui.cbZucht.currentIndex())
        guteEigenschaften = etree.SubElement(root, 'GuteEigenschaften')
        etree.SubElement(guteEigenschaften, 'Eigenschaft').text = self.ui.cbGuteEig1.currentText()
        etree.SubElement(guteEigenschaften, 'Eigenschaft').text = self.ui.cbGuteEig2.currentText()
        etree.SubElement(guteEigenschaften, 'Eigenschaft').text = self.ui.cbGuteEig3.currentText()
        schlechteEigenschaften = etree.SubElement(root, 'SchlechteEigenschaften')
        etree.SubElement(schlechteEigenschaften, 'Eigenschaft').text = self.ui.cbSchlechteEig1.currentText()
        etree.SubElement(schlechteEigenschaften, 'Eigenschaft').text = self.ui.cbSchlechteEig2.currentText()
        etree.SubElement(root, 'Ausbildung').text = self.ui.cbAusbildung.currentText()

        etree.SubElement(root, 'KO').text = str(self.ui.sbKO.value())
        etree.SubElement(root, 'MU').text = str(self.ui.sbMU.value())
        etree.SubElement(root, 'GE').text = str(self.ui.sbGE.value())
        etree.SubElement(root, 'KK').text = str(self.ui.sbKK.value())
        etree.SubElement(root, 'IN').text = str(self.ui.sbIN.value())
        etree.SubElement(root, 'KL').text = str(self.ui.sbKL.value())
        etree.SubElement(root, 'CH').text = str(self.ui.sbCH.value())
        etree.SubElement(root, 'FF').text = str(self.ui.sbFF.value())
        etree.SubElement(root, 'WM').text = str(self.ui.sbKampfwerte.value())
        etree.SubElement(root, 'GS').text = str(self.ui.sbGS.value())
        etree.SubElement(root, 'RS').text = str(self.ui.sbRS.value())
        
        etree.SubElement(root, 'WeitereVorteile').text = self.ui.leVorteile.text()

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

    def updateAusbildungen(self):
        ausbildungen = []
        tier = self.datenbank.tierbegleiter[self.ui.cbTier.currentText()]
        for key, ausbildung in self.datenbank.ausbildungen.items():
            if ausbildung.kategorie == 0 or ausbildung.kategorie == tier.kategorie:
                ausbildungen.append(key)
        
        ausbildungen = sorted(ausbildungen, key=lambda ausbildung: ausbildung if ausbildung != "Keine Ausbildung" else "###") #"Keine" is always first
        self.ui.cbAusbildung.blockSignals(True)
        self.ui.cbAusbildung.clear()
        self.ui.cbAusbildung.addItems(ausbildungen)
        self.ui.cbAusbildung.blockSignals(False)
        self.ui.cbAusbildung.setCurrentIndex(0)
        self.ui.lblReiten.setVisible(tier.reittier == 1)
        self.ui.sbReiten.setVisible(tier.reittier == 1)
        self.ui.lblRK.setVisible(tier.reittier == 1)
        self.ui.sbRK.setVisible(tier.reittier == 1)

    def updateZucht(self):
        zucht = self.ui.cbZucht.currentIndex()
        numGuteEig = 3
        numSchlechteEig = 3

        if zucht == 0: #keine
            numGuteEig = 1
            numSchlechteEig = 2
        elif zucht == 1: #keine verrechnet
            numGuteEig = 0
            numSchlechteEig = 1
        elif zucht == 2: #gewöhnlich
            numGuteEig = 1
            numSchlechteEig = 1
        elif zucht == 3: #gewöhnlich verrechnet
            numGuteEig = 0
            numSchlechteEig = 0
        elif zucht == 4: #aussergewöhnlich
            numGuteEig = 2
            numSchlechteEig = 1
        elif zucht == 5: #aussergewöhnlich verrechnet
            numGuteEig = 1
            numSchlechteEig = 0
        elif zucht == 6: #herausragend
            numGuteEig = 2
            numSchlechteEig = 0
        elif zucht == 7: #einzigartig
            numGuteEig = 3
            numSchlechteEig = 0

        self.ui.lblGuteEig.setVisible(numGuteEig >= 1)
        self.ui.cbGuteEig1.setVisible(numGuteEig >= 1)
        self.ui.lblGuteEig1.setVisible(numGuteEig >= 1)
        self.ui.cbGuteEig2.setVisible(numGuteEig >= 2)
        self.ui.lblGuteEig2.setVisible(numGuteEig >= 2)
        self.ui.cbGuteEig3.setVisible(numGuteEig >= 3)
        self.ui.lblGuteEig3.setVisible(numGuteEig >= 3)
        self.ui.lblSchlechteEig.setVisible(numSchlechteEig >= 1)
        self.ui.cbSchlechteEig1.setVisible(numSchlechteEig >= 1)
        self.ui.lblSchlechteEig1.setVisible(numSchlechteEig >= 1)
        self.ui.cbSchlechteEig2.setVisible(numSchlechteEig >= 2)
        self.ui.lblSchlechteEig2.setVisible(numSchlechteEig >= 2)

        self.validateZuchteigenschaften()

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

    def ausbildungChanged(self):
        ausbildung = self.datenbank.ausbildungen[self.ui.cbAusbildung.currentText()]
        if ausbildung.weiterevorteile:
            self.ui.leVorteile.setText(ausbildung.weiterevorteile)
            self.vorteilCompleter.popup().hide()

    def stateChanged(self):
        if self.currentlyLoading:
            return
        self.updateZucht()

        if self.datenbank.iaZuchtAusbildung and self.ui.checkAutoHintergrund.isChecked():
            zucht = self.ui.cbZucht.currentText()
            if zucht.find(" (") != -1:
                zucht = zucht[:zucht.find(" (")]
            eigenschaften = [self.ui.cbGuteEig1, self.ui.cbGuteEig2, self.ui.cbGuteEig3, self.ui.cbSchlechteEig1, self.ui.cbSchlechteEig2]
            # "or not hidden", WTF? Need to do this because the form might not be visible yet, resulting in all children not being visible...
            eigenschaften = [e.currentText() for e in eigenschaften if e.isVisible() or not e.isHidden()]
            if len(eigenschaften) > 0:
                zucht += " (" + ", ".join(eigenschaften) + ")"
            ausbildung = self.ui.cbAusbildung.currentText()
            if ausbildung.endswith(" Ausbildung"):
                ausbildung = ausbildung[:-len(" Ausbildung")]

            self.ui.teHintergrund.setPlainText(f"Zucht: {zucht}\nAusbildung: {ausbildung} ")
        self.ui.teHintergrund.setEnabled(not self.datenbank.iaZuchtAusbildung or not self.ui.checkAutoHintergrund.isChecked())

        allModifiers = []
        self.ui.lblGuteEig1.setText("")
        self.ui.lblGuteEig2.setText("")
        self.ui.lblGuteEig3.setText("")
        self.ui.lblSchlechteEig1.setText("")
        self.ui.lblSchlechteEig2.setText("")
        self.ui.lblAusbildung.setText("")
        self.ui.lblTier.setText("")

        if self.ui.cbGuteEig1.isVisible() or not self.ui.cbGuteEig1.isHidden():
            eig = self.datenbank.guteZuchteigenschaften[self.ui.cbGuteEig1.currentText()]
            allModifiers.extend(eig.modifikatoren)
            self.updatePreview(self.ui.lblGuteEig1, eig.modifikatoren)

        if self.ui.cbGuteEig2.isVisible() or not self.ui.cbGuteEig2.isHidden():
            eig = self.datenbank.guteZuchteigenschaften[self.ui.cbGuteEig2.currentText()]
            allModifiers.extend(eig.modifikatoren)
            self.updatePreview(self.ui.lblGuteEig2, eig.modifikatoren)

        if self.ui.cbGuteEig3.isVisible() or not self.ui.cbGuteEig3.isHidden():
            eig = self.datenbank.guteZuchteigenschaften[self.ui.cbGuteEig3.currentText()]
            allModifiers.extend(eig.modifikatoren)
            self.updatePreview(self.ui.lblGuteEig3, eig.modifikatoren)

        if self.ui.cbSchlechteEig1.isVisible() or not self.ui.cbSchlechteEig1.isHidden():
            eig = self.datenbank.schlechteZuchteigenschaften[self.ui.cbSchlechteEig1.currentText()]
            allModifiers.extend(eig.modifikatoren)
            self.updatePreview(self.ui.lblSchlechteEig1, eig.modifikatoren)

        if self.ui.cbSchlechteEig2.isVisible() or not self.ui.cbSchlechteEig2.isHidden():
            eig = self.datenbank.schlechteZuchteigenschaften[self.ui.cbSchlechteEig2.currentText()]
            allModifiers.extend(eig.modifikatoren)
            self.updatePreview(self.ui.lblSchlechteEig2, eig.modifikatoren)

        ausbildung = self.datenbank.ausbildungen[self.ui.cbAusbildung.currentText()]
        allModifiers.extend(ausbildung.modifikatoren)
        self.updatePreview(self.ui.lblAusbildung, ausbildung.modifikatoren, True)

        if self.ui.leVorteile.text():
            weitereVorteile = list(map(str.strip, self.ui.leVorteile.text().split(",")))
            for vorteil in weitereVorteile:
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

        # Default values
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
        attributModifiers["WM"] += self.ui.sbKampfwerte.value()
        attributModifiers["GS"] += self.ui.sbGS.value()
        attributModifiers["RS"] += self.ui.sbRS.value()

        # Abgeleitete Werte
        tier = self.datenbank.tierbegleiter[self.ui.cbTier.currentText()]

        tierLabelText = ""
        if tier.rassen:
            tierLabelText += tier.rassen + ". "

        if self.datenbank.iaZuchtAusbildung:
            if tier.groesse >= 5:
                attributModifiers["KK"] *= 4
                attributModifiers["KO"] *= 4
            elif tier.groesse == 4:
                attributModifiers["KK"] *= 2
                attributModifiers["KO"] *= 2

            attributModifiers["MR"] += int(attributModifiers["MU"] / 4);
            attributModifiers["TP"] += int(attributModifiers["KK"] / 2);
            attributModifiers["WS"] += int(attributModifiers["KO"] / 2);
            attributModifiers["GS"] += int(attributModifiers["GE"] / 2);
            attributModifiers["INI"] += attributModifiers["IN"];

            if tier.groesse == 4:
                tierLabelText += "Großes Tier, KO und KK-Bonusse werden in der Endberechnung verdoppelt."
            elif tier.groesse >= 5:
                tierLabelText += "Sehr großes Tier, KO und KK-Bonusse werden in der Endberechnung vervierfacht."

        self.ui.lblTier.setVisible(tierLabelText != "")
        self.ui.lblTier.setText(tierLabelText)

        #Ausbildung, Zucht etc inkl. abgeleiteter Werte sind berechnet, jetzt tier attribute hinzufügen
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

        reiterkampfWM = 0
        if "Reiterkampf WM" in talentModifiers:
            reiterkampfWM = talentModifiers["Reiterkampf WM"] + attributModifiers["WM"]
            del talentModifiers["Reiterkampf WM"]

        waffen = copy.deepcopy(tier.waffen)
        for waffe in waffen:
            if waffe.plus is not None:
                waffe.plus += attributModifiers["TP"]
            if waffe.at is not None:
                waffe.at += attributModifiers["WM"]
            if waffe.vt is not None:
                waffe.vt += attributModifiers["WM"]

        if tier.reittier == 1:
            if len(waffen) > 0 :
                reitenWaffe = copy.copy(waffen[0])
                reitenWaffe.name = "Reiterkampf (" + reitenWaffe.name + ")"
                reitenWaffe.at = self.ui.sbReiten.value() + reiterkampfWM + self.ui.sbRK.value()
                reitenWaffe.vt = self.ui.sbReiten.value() + reiterkampfWM + self.ui.sbRK.value()
                reitenWaffe.plus += self.ui.sbRK.value()
                if reitenWaffe.eigenschaften:
                    reitenWaffe.eigenschaften += ", "
                reitenWaffe.eigenschaften += "AT +4 gegen kleinere Gegner"
                waffen.append(reitenWaffe)

            vorteilModifiers.append(copy.copy(self.datenbank.tiervorteile["Sturmangriff (Reiterkampf)"]))
            if self.ui.sbRK.value() == 0:
                vorteilModifiers[-1].name = vorteilModifiers[-1].name[:-1] + "-Stufe nicht ausreichend)"

            if self.datenbank.iaZuchtAusbildung:
                for vorteilMod in vorteilModifiers:
                    if vorteilMod.name == "Überrennen (Reiterkampf)" and self.ui.sbRK.value() < 3:
                        vorteilMod.name = vorteilMod.name[:-1] + "-Stufe nicht ausreichend)"
                    if vorteilMod.name == "Befreiungsschlag (Reiterkampf)" and self.ui.sbRK.value() < 3:
                        vorteilMod.name = vorteilMod.name[:-1] + "-Stufe nicht ausreichend)"
                    if vorteilMod.name == "Ausfall (Reiterkampf)" and self.ui.sbRK.value() < 2:
                        vorteilMod.name = vorteilMod.name[:-1] + "-Stufe nicht ausreichend)"
                    if vorteilMod.name == "Hammerschlag (Reiterkampf)" and self.ui.sbRK.value() < 2:
                        vorteilMod.name = vorteilMod.name[:-1] + "-Stufe nicht ausreichend)"
                    if vorteilMod.name == "Trampeln (Reiterkampf)" and self.ui.sbRK.value() < 2:
                        vorteilMod.name = vorteilMod.name[:-1] + "-Stufe nicht ausreichend)"
            else:
                if self.ui.sbRK.value() > 2:
                    vorteilModifiers.append(self.datenbank.tiervorteile["Überrennen (Reiterkampf)"])

        del attributModifiers["TP"]
        del attributModifiers["WM"]

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
        if self.datenbank.iaZuchtAusbildung:
            text += '<p><b>Preis: </b>'
            preis = tier.preis
            zucht = self.ui.cbZucht.currentIndex()
            if zucht == 0 or zucht == 1:
                preis *= 0.5
            elif zucht == 4 or zucht == 5:
                preis *= 2
            elif self.ui.cbZucht.currentIndex() == 6:
                preis *= 4
            elif self.ui.cbZucht.currentIndex() == 7:
                preis *= 8
            preis += ausbildung.preis
            text += str(int(preis)) + " Dukaten"
            if tier.preis == 0:
                   text += " (der Basispreis des Tiers liegt bei 0)"
            text += "</p>"
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

    def validateZuchteigenschaften(self):
        sEig1Valid = True
        sEig2Valid = True
        gEig1Valid = True
        gEig2Valid = True
        gEig3Valid = True

        if self.ui.cbSchlechteEig1.isVisible() and self.hasVorteil(self.ui.cbSchlechteEig1.currentText()):
            self.ui.cbSchlechteEig1.setToolTip("Es ist nicht erlaubt die gleiche Eigenschaft mehrmals zu wählen (eventuell ist sie auch bereits bei der Spezies enthalten).")
            self.ui.cbSchlechteEig1.setStyleSheet("border: 1px solid red;")
            sEig1Valid= False
        else:
            self.ui.cbSchlechteEig1.setToolTip("")
            self.ui.cbSchlechteEig1.setStyleSheet("")

        if self.ui.cbSchlechteEig2.isVisible() and (self.ui.cbSchlechteEig1.currentIndex() == self.ui.cbSchlechteEig2.currentIndex() or self.hasVorteil(self.ui.cbSchlechteEig2.currentText())):
            self.ui.cbSchlechteEig2.setToolTip("Es ist nicht erlaubt die gleiche Eigenschaft mehrmals zu wählen (eventuell ist sie auch bereits bei der Spezies enthalten).")
            self.ui.cbSchlechteEig2.setStyleSheet("border: 1px solid red;")
            sEig2Valid= False
        else:
            self.ui.cbSchlechteEig2.setToolTip("")
            self.ui.cbSchlechteEig2.setStyleSheet("")

        if self.ui.cbGuteEig1.isVisible() and self.hasVorteil(self.ui.cbGuteEig1.currentText()):
            self.ui.cbGuteEig1.setToolTip("Es ist nicht erlaubt die gleiche Eigenschaft mehrmals zu wählen (eventuell ist sie auch bereits bei der Spezies enthalten).")
            self.ui.cbGuteEig1.setStyleSheet("border: 1px solid red;")
            gEig1Valid = False
        else:
            self.ui.cbGuteEig1.setToolTip("")
            self.ui.cbGuteEig1.setStyleSheet("")

        if self.ui.cbGuteEig2.isVisible() and (self.ui.cbGuteEig1.currentIndex() == self.ui.cbGuteEig2.currentIndex() or self.hasVorteil(self.ui.cbGuteEig2.currentText())):
            self.ui.cbGuteEig2.setToolTip("Es ist nicht erlaubt die gleiche Eigenschaft mehrmals zu wählen (eventuell ist sie auch bereits bei der Spezies enthalten).")
            self.ui.cbGuteEig2.setStyleSheet("border: 1px solid red;")
            gEig2Valid = False
        else:
            self.ui.cbGuteEig2.setToolTip("")
            self.ui.cbGuteEig2.setStyleSheet("")

        if self.ui.cbGuteEig3.isVisible() and (self.ui.cbGuteEig3.currentIndex() == self.ui.cbGuteEig1.currentIndex() or self.ui.cbGuteEig3.currentIndex() == self.ui.cbGuteEig2.currentIndex() or self.hasVorteil(self.ui.cbGuteEig3.currentText())):
            self.ui.cbGuteEig3.setToolTip("Es ist nicht erlaubt die gleiche Eigenschaft mehrmals zu wählen (eventuell ist sie auch bereits bei der Spezies enthalten).")
            self.ui.cbGuteEig3.setStyleSheet("border: 1px solid red;")
            gEig3Valid = False
        else:
            self.ui.cbGuteEig3.setToolTip("")
            self.ui.cbGuteEig3.setStyleSheet("")

        self.zuchteigenschaftenValid = sEig1Valid and sEig2Valid and gEig1Valid and gEig2Valid and gEig3Valid

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

        tiereigenschaften = [vorteilMod for vorteilMod in self.vorteilModifiers if vorteilMod.name in self.datenbank.guteZuchteigenschaften or vorteilMod.name in self.datenbank.schlechteZuchteigenschaften]
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

        addRules = self.ui.checkRegeln.isChecked() and (len(tiervorteile) + len(tiereigenschaften) > 0)
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
            if len(tiereigenschaften) > 0:
                rules.append(self.categoryHeading("Tiereigenschaften"))
                for vorteilMod in tiereigenschaften:
                    rules.append("<article>")
                    rules.append(self.ruleHeading(vorteilMod.name))
                    rules.append(vorteilMod.wirkung)
                    rules.append("</article>")

            if sum(1 for v in self.vorteilModifiers if not v.manöver) > 0:
                rules.append(self.categoryHeading("Tiervorteile"))
                if self.datenbank.iaZuchtAusbildung:
                    rules.append("Der Einsatz eines Vorteils, der nicht passiv ist, erfordert eine Probe auf Tiere beeinflussen (20). Kampfmanöver gelten immer als passiv.\n\n")
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
        dlg.hide()
        dlg.deleteLater()

        if Wolke.Settings['PDF-Open']:
            Hilfsmethoden.openFile(path)