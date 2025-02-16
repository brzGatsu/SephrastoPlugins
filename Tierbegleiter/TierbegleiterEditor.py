from PySide6 import QtWidgets, QtCore, QtGui
import os.path
import logging
from Tierbegleiter import TierbegleiterPdfExporter
from Tierbegleiter import TierbegleiterDatenbank
from Tierbegleiter import Tierbegleiter
from Wolke import Wolke
import lxml.etree as etree
from PySide6.QtGui import QPixmap
from QtUtils.TextTagCompleter import TextTagCompleter
from Charakterbogen import Charakterbogen
from QtUtils.FocusWatcher import FocusWatcher

class TierbegleiterEditor(object):
    def __init__(self):
        self.datenbank = TierbegleiterDatenbank.TierbegleiterDatenbank()
        self.charakterbogen = Charakterbogen() # use default settings
        self.charakterbogen.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data", "Tierbegleiterbogen.ini"))
        self.savepath = ""
        self.tierbegleiter = Tierbegleiter.Tierbegleiter()
        self.pdfExporter = TierbegleiterPdfExporter.TierbegleiterPdfExporter()

        self.characterImage = None
        self.currentlyLoading = False

    def setupMainForm(self):
        if "WindowSize-TierbegleiterPlugin" in Wolke.Settings:
            windowSize = Wolke.Settings["WindowSize-TierbegleiterPlugin"]
            self.formMain.resize(windowSize[0], windowSize[1])

        self.ui.splitter.adjustSize()
        width = self.ui.splitter.size().width()
        self.ui.splitter.setSizes([int(width*0.6), int(width*0.4)])

        self.vorteile = []
        self.vorteilCompleter = []
        for i in range(1, 15):
            leVorteil = getattr(self.ui, "leVorteil" + str(i))
            leVorteil.editingFinished.connect(self.update)
            self.vorteilCompleter.append(TextTagCompleter(leVorteil, self.datenbank.tiervorteile.keys()))
            self.vorteile.append(leVorteil)

        self.talente = []
        self.talentCompleter = []
        for i in range(1, 9):
            leTalent = getattr(self.ui, "leTalent" + str(i))
            leTalent.editingFinished.connect(self.update)
            self.talentCompleter.append(TextTagCompleter(leTalent, self.datenbank.talente))
            self.talente.append(leTalent)

        self.talentWerte = []
        for i in range(1, 9):
            sbTalent = getattr(self.ui, "sbTalent" + str(i))
            sbTalent.valueChanged.connect(self.update)
            self.talentWerte.append(sbTalent)

        self.ausruestung = []
        for i in range(1, 21):
            leAusruestung = getattr(self.ui, "leAusruestung" + str(i))
            leAusruestung.editingFinished.connect(lambda: setattr(self.tierbegleiter, "ausruestung", [aus.text() for aus in self.ausruestung]))
            self.ausruestung.append(leAusruestung)
        
        self.ui.cbTier.addItems(sorted(self.datenbank.tierbegleiter.keys()))
        self.ui.cbTier.setCurrentIndex(0)

        self.ui.leName.editingFinished.connect(lambda: setattr(self.tierbegleiter, "name", self.ui.leName.text()))
        self.ui.leNahrung.editingFinished.connect(lambda: setattr(self.tierbegleiter, "nahrung", self.ui.leNahrung.text()))

        self.aussehenEditingFinished = FocusWatcher(lambda: setattr(self.tierbegleiter, "aussehen", self.ui.teAussehen.toPlainText()))
        self.ui.teAussehen.installEventFilter(self.aussehenEditingFinished)

        self.hintergrundEditingFinished = FocusWatcher(lambda: setattr(self.tierbegleiter, "hintergrund", self.ui.teHintergrund.toPlainText()))
        self.ui.teHintergrund.installEventFilter(self.hintergrundEditingFinished)

        self.ui.cbTier.currentIndexChanged.connect(self.handleTierChanged)
        self.ui.cbTier.currentIndexChanged.connect(self.update)
        self.ui.sbReiten.valueChanged.connect(self.update)
        self.ui.sbRK.valueChanged.connect(self.handleReiterkampfChanged)
        self.ui.sbRK.valueChanged.connect(self.update)
        self.ui.sbRK4AT.valueChanged.connect(self.update)
        self.ui.sbRK4VT.valueChanged.connect(self.update)
        self.ui.sbRK4TP.valueChanged.connect(self.update)

        self.attribute = {}
        for attribut in Tierbegleiter.Attribute:
            self.attribute[attribut] = getattr(self.ui, "sb" + attribut)
            self.attribute[attribut].valueChanged.connect(self.update)

        self.ui.btnSavePdf.clicked.connect(self.savePdfClickedHandler)
        self.ui.buttonLoad.clicked.connect(self.loadClickedHandler)
        self.ui.buttonSave.clicked.connect(self.saveClickedHandler)
        self.ui.buttonQuicksave.clicked.connect(self.quicksaveClickedHandler)

        self.labelImageText = self.ui.labelImage.text()
        self.ui.buttonLoadImage.clicked.connect(self.buttonLoadImageClicked)
        self.ui.buttonDeleteImage.clicked.connect(self.buttonDeleteImageClicked)
        
        self.ui.checkRegeln.setChecked(self.tierbegleiter.regelnAnhaengen)
        self.ui.checkRegeln.stateChanged.connect(lambda: setattr(self.tierbegleiter, "regelnAnhaengen", self.ui.checkRegeln.isChecked()))

        self.ui.sbRegelnGroesse.setValue(self.tierbegleiter.regelnGroesse)
        self.ui.sbRegelnGroesse.valueChanged.connect(lambda: setattr(self.tierbegleiter, "regelnGroesse", self.ui.sbRegelnGroesse.value()))

        self.ui.checkEditierbar.setChecked(self.tierbegleiter.formularEditierbar)
        self.ui.checkEditierbar.stateChanged.connect(lambda: setattr(self.tierbegleiter, "formularEditierbar", self.ui.checkEditierbar.isChecked()))

        self.handleTierChanged()
        self.update()
        self.updateTitlebar()

        self.formMain.closeEvent = self.closeEvent

    def closeEvent(self,event):
        Wolke.Settings["WindowSize-TierbegleiterPlugin"] = [self.formMain.size().width(), self.formMain.size().height()]

    def updateTitlebar(self):
        file = " - Neuer Tierbegleiter"
        if self.savepath:
            file = " - " + os.path.basename(self.savepath)
        self.formMain.setWindowTitle("Sephrasto" + file)

    def load(self):
        tb = self.tierbegleiter
        self.ui.leName.setText(tb.name)
        self.ui.teAussehen.setPlainText(tb.aussehen)
        self.ui.leNahrung.setText(tb.nahrung)
        self.ui.teHintergrund.setPlainText(tb.hintergrund)
        self.ui.cbTier.setCurrentText(tb.definition.name)
        self.ui.sbRK.setValue(tb.reiterkampfStufe)
        self.ui.sbRK4AT.setValue(tb.reiterkampf4AT)
        self.ui.sbRK4VT.setValue(tb.reiterkampf4VT)
        self.ui.sbRK4TP.setValue(tb.reiterkampf4TP)
        self.ui.sbReiten.setValue(tb.reitenPW)
        
        for attribut in Tierbegleiter.Attribute:
            self.attribute[attribut].setValue(self.tierbegleiter.attributMods[attribut])
        
        for i in range(len(self.vorteile)):
            self.vorteilCompleter[i].setEnabled(False)

            if i >= len(self.tierbegleiter.vorteilMods):
                self.vorteile[i].setText("")
            else:
                self.vorteile[i].setText(self.tierbegleiter.vorteilMods[i].name)

            self.vorteilCompleter[i].setEnabled(True)

        for i in range(len(self.talente)):
            self.talentCompleter[i].setEnabled(False)

            if i >= len(self.tierbegleiter.talentMods):
                self.talente[i].setText("")
                self.talentWerte[i].setValue(0)
            else:
                self.talente[i].setText(self.tierbegleiter.talentMods[i].name)
                self.talentWerte[i].setValue(self.tierbegleiter.talentMods[i].mod)

            self.talentCompleter[i].setEnabled(True)
        
        for i in range(len(self.ausruestung)):
            if i >= len(self.tierbegleiter.ausruestung):
                self.ausruestung[i].setText("")
            else:
                self.ausruestung[i].setText(self.tierbegleiter.ausruestung[i])
        
        if self.tierbegleiter.bild is not None:
            self.characterImage = QtGui.QPixmap()
            self.characterImage.loadFromData(self.tierbegleiter.bild)
            self.setImage(self.characterImage)     

        self.ui.checkRegeln.setChecked(self.tierbegleiter.regelnAnhaengen)
        self.ui.sbRegelnGroesse.setValue(self.tierbegleiter.regelnGroesse)
        self.ui.checkEditierbar.setChecked(self.tierbegleiter.formularEditierbar)

    def update(self):
        if self.currentlyLoading:
            return
        tier = self.datenbank.tierbegleiter[self.ui.cbTier.currentText()]
        self.tierbegleiter.definition = tier

        attributMods = {}
        talentMods = []
        vorteilMods = []

        # Reiterkampf
        self.tierbegleiter.reitenPW = self.ui.sbReiten.value()
        self.tierbegleiter.reiterkampfStufe = self.ui.sbRK.value()
        self.tierbegleiter.reiterkampf4AT = self.ui.sbRK4AT.value()
        self.tierbegleiter.reiterkampf4VT = self.ui.sbRK4VT.value()
        self.tierbegleiter.reiterkampf4TP = self.ui.sbRK4TP.value()

        # Zusätzliche Attribute
        attributMods["KO"] = self.ui.sbKO.value()
        attributMods["MU"] = self.ui.sbMU.value()
        attributMods["GE"] = self.ui.sbGE.value()
        attributMods["KK"] = self.ui.sbKK.value()
        attributMods["IN"] = self.ui.sbIN.value()
        attributMods["KL"] = self.ui.sbKL.value()
        attributMods["CH"] = self.ui.sbCH.value()
        attributMods["FF"] = self.ui.sbFF.value()
        attributMods["AT"] = self.ui.sbAT.value()
        attributMods["VT"] = self.ui.sbVT.value()
        attributMods["GS"] = self.ui.sbGS.value()
        attributMods["RS"] = self.ui.sbRS.value()
        attributMods["BE"] = self.ui.sbBE.value()
        attributMods["TP"] = self.ui.sbTP.value()
        attributMods["INI"] = self.ui.sbINI.value()
        attributMods["MR"] = self.ui.sbMR.value()
        attributMods["WS"] = self.ui.sbWS.value()

        # Zusätzliche Vorteile
        for leVorteil in self.vorteile:
            vorteil = leVorteil.text()
            if vorteil in self.datenbank.tiervorteile:
                vorteilMods.append(self.datenbank.tiervorteile[vorteil])
            else:
                mod = Tierbegleiter.Modifikator()
                mod.name = vorteil
                vorteilMods.append(mod) 

        # Zusätzliche Talente
        for i in range(0, len(self.talente)):
            mod = Tierbegleiter.Modifikator()
            mod.name = self.talente[i].text()
            mod.mod = self.talentWerte[i].value()
            talentMods.append(mod)

        self.tierbegleiter.attributMods = attributMods
        self.tierbegleiter.talentMods = talentMods
        self.tierbegleiter.vorteilMods = vorteilMods

        self.tierbegleiter.aktualisieren()

        self.updateInfo()

    def updateInfo(self):
        text = self.tierbegleiter.modifiersToString(True)
        self.ui.lblWerte.setText(text)

        tooltip = ""
        for vorteilMod in self.tierbegleiter.vorteilModsMerged:
            if vorteilMod.wirkung:
                tooltip += "<b>" + vorteilMod.name + ":</b> " + vorteilMod.wirkung + "\n"     

        if tooltip:
            tooltip = tooltip[:-1].replace("\n", "<br>")
        self.ui.lblWerte.setToolTip(tooltip)

    def handleTierChanged(self):
        tier = self.datenbank.tierbegleiter[self.ui.cbTier.currentText()]

        tierLabelText = ""
        if tier.rassen:
            tierLabelText += tier.rassen + ". "
        self.ui.lblTier.setVisible(tierLabelText != "")
        self.ui.lblTier.setText(tierLabelText)

        self.ui.hlReittier.setVisible(tier.reittier == 1)
        self.handleReiterkampfChanged()

        if not self.currentlyLoading:
            self.tierbegleiter.nahrung = tier.futter
            self.ui.leNahrung.setText(self.tierbegleiter.nahrung)

            groessen = ["Winziges", "Sehr kleines", "Kleines", "Mittelgroßes", "Großes", "Sehr großes"]
            self.tierbegleiter.aussehen = groessen[tier.groesse] + " Tier"
            self.ui.teAussehen.setPlainText(self.tierbegleiter.aussehen)

    def handleReiterkampfChanged(self):
        tier = self.datenbank.tierbegleiter[self.ui.cbTier.currentText()]
        self.ui.hlRK4.setVisible(self.ui.sbRK.value() == 4)

    def setImage(self, pixmap):
        self.ui.labelImage.setPixmap(pixmap.scaled(self.ui.labelImage.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

    def buttonLoadImageClicked(self):
        spath, _ = QtWidgets.QFileDialog.getOpenFileName(None,"Bild laden...", "", "Bild Dateien (*.png *.jpg *.bmp)")
        if spath == "":
            return
        
        self.characterImage = QPixmap(spath).scaled(QtCore.QSize(260, 340), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.setImage(self.characterImage)

        buffer = QtCore.QBuffer()
        buffer.open(QtCore.QIODevice.WriteOnly);
        self.characterImage.save(buffer, "JPG")
        imageData = buffer.data().data()
        self.tierbegleiter.bild = imageData

    def buttonDeleteImageClicked(self):
        self.characterImage = None
        self.ui.labelImage.setPixmap(QPixmap())
        self.ui.labelImage.setText(self.labelImageText)
        self.tierbegleiter.bild = None

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
        self.tierbegleiter.deserialize(root, self.datenbank)
        self.load()
        self.currentlyLoading = False
        self.updateTitlebar()
        self.updateInfo()

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
        self.tierbegleiter.serialize(root)
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
            self.pdfExporter.createPdf(spath, self.tierbegleiter, self.charakterbogen, self.datenbank)
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