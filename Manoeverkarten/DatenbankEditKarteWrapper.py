# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore, QtGui
from Wolke import Wolke
from Manoeverkarten import DatenbankEditKarte
from Core.Regel import Regel
from Core.Talent import TalentDefinition
from Core.Vorteil import VorteilDefinition
from Core.Waffeneigenschaft import Waffeneigenschaft
from Hilfsmethoden import Hilfsmethoden
from Manoeverkarten.Manoeverkarte import KartenTyp, Karte, KartenUtility
from DatenbankElementEditorBase import DatenbankElementEditorBase, BeschreibungEditor, VoraussetzungenEditor
from QtUtils.WebEngineViewPlus import WebEngineViewPlus
from Manoeverkarten import KartenGenerator
from QtUtils.HtmlToolbar import HtmlToolbar
import os
import shiboken6

class DatenbankEditKarteWrapper(DatenbankElementEditorBase):
    def __init__(self, datenbank, karte=None):
        super().__init__(datenbank, DatenbankEditKarte.Ui_karteDialog(), Karte, karte)
        self.beschreibungEditor = BeschreibungEditor(self, "text", "teBeschreibung", None)
        self.voraussetzungenEditor = VoraussetzungenEditor(self)
        
    def onSetupUi(self):
        super().onSetupUi()
        
        ui = self.ui
        self.registerInput(ui.leName, ui.labelName)
        self.registerInput(ui.comboTyp, ui.labelTyp)
        self.registerInput(ui.comboSubtyp, ui.labelSubtyp)
        self.registerInput(ui.labelFarbeGewaehlt, ui.labelFarbe)
        self.registerInput(ui.leName, ui.labelNewEditDelete)
        self.registerInput(ui.radioEdit, ui.labelName)
        self.registerInput(ui.radioDelete, ui.labelName)
        self.registerInput(ui.teVoraussetzungen, ui.labelVoraussetzungen)
        self.registerInput(ui.leTitel, ui.labelTitel)
        self.registerInput(ui.leUntertitel, ui.labelUntertitel)
        self.registerInput(ui.teBeschreibung, ui.labelBeschreibung)
        self.registerInput(ui.leFusszeile, ui.labelFusszeile)
        
    def load(self, karte):
        super().load(karte)

        self.htmlToolbar = HtmlToolbar(self.ui.teBeschreibung)
        self.ui.vlBeschreibung.insertWidget(0, self.htmlToolbar)

        self.voraussetzungenEditor.load(karte)
        self.beschreibungEditor.load(karte)

        if karte.löschen:
            self.ui.radioDelete.setChecked(True)
        else:
            self.ui.radioEdit.setChecked(True)
        self.ui.radioEdit.clicked.connect(self.deleteChanged)
        self.ui.radioDelete.clicked.connect(self.deleteChanged)

        if karte.typ != KartenTyp.Invalid:
            self.ui.comboTyp.setCurrentIndex(karte.typ)
        self.ui.comboTyp.currentIndexChanged.connect(self.typChanged)

        self.ui.leTitel.setText(karte.titel)
        self.ui.leUntertitel.setText(karte.subtitel)
        self.ui.leFusszeile.setText(karte.fusszeile)

        self.nameChanged()
        self.deleteChanged()

        if karte.typ == KartenTyp.Benutzerdefiniert:
            self.ui.comboSubtyp.setCurrentText(karte.subtyp)
        elif karte.subtyp != -1:
            self.ui.comboSubtyp.setCurrentIndex(karte.subtyp)

        self.updateTimer = QtCore.QTimer()
        self.updateTimer.setSingleShot(True)
        self.updateTimer.timeout.connect(self.updateWebView)
        self.webView = WebEngineViewPlus()
        self.webView.installJSBridge()
        self.ui.gbPreview.layout().addWidget(self.webView)
        zoomFactor = 2
        self.webView.setFixedSize(238 * zoomFactor, 332 * zoomFactor)
        self.webView.setZoomFactor(zoomFactor)
        self.webView.setEnabled(False)

        for edit in [self.ui.leName, self.ui.leTitel, self.ui.leUntertitel, self.ui.teBeschreibung, self.ui.leFusszeile]:
            edit.textChanged.connect(self.updateWebViewTimer)

        self.ui.radioDelete.clicked.connect(self.updateWebViewTimer)
        self.ui.radioEdit.clicked.connect(self.updateWebViewTimer)
        self.ui.comboTyp.currentIndexChanged.connect(self.updateWebViewTimer)
        self.ui.comboSubtyp.currentIndexChanged.connect(self.updateWebViewTimer)
        self.ui.buttonFarbe.clicked.connect(self.chooseColor)          
        self.ui.buttonFarbe.setText("\uf53f")
        buttonSize = Hilfsmethoden.emToPixels(2.3)
        self.ui.buttonFarbe.setMinimumSize(buttonSize, buttonSize)
        self.ui.buttonFarbe.setMaximumSize(buttonSize, buttonSize)
        self.ui.labelFarbeGewaehlt.setMinimumSize(buttonSize*2, buttonSize)
        self.ui.labelFarbeGewaehlt.setMaximumSize(buttonSize*2, buttonSize)
        self.ui.labelFarbeGewaehlt.setProperty("col", karte.farbe)
        self.ui.labelFarbeGewaehlt.setStyleSheet(f"QLabel {{ background-color: {karte.farbe}; }}")
        self.updateWebView()

    def update(self, karte):
        super().update(karte)
        self.voraussetzungenEditor.update(karte)
        self.beschreibungEditor.update(karte)

        karte.typ = self.ui.comboTyp.currentIndex()
        isNew = KartenUtility.isNew(self.datenbank, karte.name, karte.typ)
        if isNew:
            karte.löschen = False
            if karte.typ == KartenTyp.Deck:
                karte.farbe = self.ui.labelFarbeGewaehlt.property("col")
            karte.titel = "$original$"
        else:
            karte.löschen = self.ui.radioDelete.isChecked()
            karte.titel = self.ui.leTitel.text()

        if karte.typ == KartenTyp.Benutzerdefiniert:
            karte.subtyp = self.ui.comboSubtyp.currentText()
        elif karte.typ in [KartenTyp.Vorteil, KartenTyp.Regel, KartenTyp.Talent]:
            karte.subtyp = self.ui.comboSubtyp.currentIndex()
        else:
            karte.subtyp = -1

        karte.subtitel = self.ui.leUntertitel.text()
        karte.fusszeile = self.ui.leFusszeile.text()

    def chooseColor(self):
        color = QtWidgets.QColorDialog.getColor(self.ui.labelFarbeGewaehlt.property("col"))
        if not color.isValid():
            return

        self.ui.labelFarbeGewaehlt.setProperty("col", color.name())
        self.ui.labelFarbeGewaehlt.setStyleSheet(f"QLabel {{ background-color: {color.name()}; }}")
        self.updateWebViewTimer()

    def updateWebViewTimer(self):
        if self.updateTimer.isActive():
            return
        self.updateTimer.start(1000)

    def updateWebView(self):
        if not shiboken6.isValid(self.webView):
            return

        karte = Karte()
        self.update(karte)
        original = KartenUtility.getOriginalElement(self.datenbank, karte.name, karte.typ)
        generator = KartenGenerator.KartenGenerator(self.datenbank)

        if original is None:
            karte = generator.generateZusatzKarte(karte, karte.farbe)
        else:
            karte = generator.generateKarte(original, "#000000", overrideKarte=karte)
        if karte is None:
            self.webView.setHtml("<div style='position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);'>Gelöscht!</div>", "")
            return
        
        reihenfolge = self.datenbank.einstellungen["Regelanhang: Reihenfolge"].wert
        currentCat = ""

        if self.ui.comboTyp.currentIndex() != KartenTyp.Deck:
            if self.ui.comboTyp.currentIndex() == KartenTyp.Benutzerdefiniert:
                karte.subtyp = self.ui.comboSubtyp.currentText()
                currentCat = karte.subtyp
            else:
                for r in reihenfolge:
                    if r[0] == "T" and len(r) > 2:
                        currentCat = r[2:]
                    elif r[0] == "V" and len(r) > 2 and r[2:].isnumeric():
                        kategorie = int(r[2:])
                        if self.ui.comboTyp.currentIndex() == KartenTyp.Vorteil and kategorie == self.ui.comboSubtyp.currentIndex():
                            break;
                    elif r[0] == "R" and len(r) > 2 and r[2:].isnumeric():
                        kategorie = int(r[2:])
                        if self.ui.comboTyp.currentIndex() == KartenTyp.Regel and kategorie == self.ui.comboSubtyp.currentIndex():
                            break;
                    elif r[0] == "W":
                        if self.ui.comboTyp.currentIndex() == KartenTyp.Waffeneigenschaft:
                            break;
                    elif r[0] == "S" and len(r) > 2 and r[2:].isnumeric():
                        kategorie = int(r[2:])
                        if self.ui.comboTyp.currentIndex() == KartenTyp.Talent and kategorie == self.ui.comboSubtyp.currentIndex():
                            break;
                    else:
                        continue

            deckKarte = KartenUtility.getDeckKarte(self.datenbank, currentCat)
            if deckKarte is not None:
                karte.farbe = deckKarte.farbe

        html, htmlPath = generator.generateHtml(karte, 0, forceHintergrund = True)
        self.webView.page().setBackgroundColor(karte.farbe)
        self.webView.setHtml(html, QtCore.QUrl.fromLocalFile(QtCore.QFileInfo(htmlPath).absoluteFilePath()))        
           
    def nameChanged(self):
        super().nameChanged()
        self.typChanged()

    def typChanged(self):
        self.validator["Benutzerdefiniert"] = True
        self.ui.comboSubtyp.setProperty("error", False)
        self.ui.comboSubtyp.setToolTip("")
        prevSubtypIndex = self.ui.comboSubtyp.currentIndex()
        prevSubtypItems = [self.ui.comboSubtyp.itemText(i) for i in range(self.ui.comboSubtyp.count())]

        self.ui.comboSubtyp.clear()
        isNew = KartenUtility.isNew(self.datenbank, self.ui.leName.text(), self.ui.comboTyp.currentIndex())
        self.ui.comboSubtyp.setVisible(self.ui.comboTyp.currentIndex() != KartenTyp.Deck)
        self.ui.comboSubtyp.setEnabled(isNew and self.ui.comboTyp.currentIndex() != KartenTyp.Waffeneigenschaft)

        originalElement = KartenUtility.getOriginalElement(self.datenbank, self.ui.leName.text(), self.ui.comboTyp.currentIndex())
        if self.ui.comboTyp.currentIndex() == KartenTyp.Vorteil:
            self.ui.comboSubtyp.addItems(self.datenbank.einstellungen["Vorteile: Kategorien"].wert.keyList)
        elif self.ui.comboTyp.currentIndex() == KartenTyp.Regel:
            self.ui.comboSubtyp.addItems(self.datenbank.einstellungen["Regeln: Kategorien"].wert.keyList)
        elif self.ui.comboTyp.currentIndex() == KartenTyp.Talent:
            self.ui.comboSubtyp.addItems(self.datenbank.einstellungen["Talente: Kategorien"].wert.keyList)
        elif self.ui.comboTyp.currentIndex() == KartenTyp.Benutzerdefiniert:
            typen = KartenUtility.getBenutzerdefinierteTypen(self.datenbank)
            if len(typen) == 0:
                self.validator["Benutzerdefiniert"] = False
                self.ui.comboSubtyp.setProperty("error", True)
                self.ui.comboSubtyp.setToolTip("Erstelle erst ein neues Deck")
            else:
                self.ui.comboSubtyp.addItems(typen)
                
        if originalElement is not None:
            if hasattr(originalElement, "kategorie"):
                self.ui.comboSubtyp.setCurrentIndex(originalElement.kategorie)
        elif Hilfsmethoden.ArrayEqual([self.ui.comboSubtyp.itemText(i) for i in range(self.ui.comboSubtyp.count())], prevSubtypItems):
            self.ui.comboSubtyp.setCurrentIndex(prevSubtypIndex)
            
        self.ui.comboSubtyp.style().unpolish(self.ui.comboSubtyp)
        self.ui.comboSubtyp.style().polish(self.ui.comboSubtyp)

        self.ui.labelTitel.setVisible(not isNew)
        self.ui.leTitel.setVisible(not isNew)
        
        if isNew:
            self.ui.labelInfo.setText("Neue Karte erstellen")
        else:
            self.ui.labelInfo.setText(KartenTyp.TypNamen[self.ui.comboTyp.currentIndex()] + " gefunden:")
        self.ui.radioEdit.setVisible(not isNew)
        self.ui.radioDelete.setVisible(not isNew)
        self.deleteChanged()

        self.ui.buttonFarbe.setVisible(self.ui.comboTyp.currentIndex() == KartenTyp.Deck)
        self.ui.labelSubtyp.setVisible(self.ui.comboTyp.currentIndex() != KartenTyp.Deck)
        self.ui.labelFarbe.setVisible(self.ui.comboTyp.currentIndex() == KartenTyp.Deck)
        self.ui.labelFarbeGewaehlt.setVisible(self.ui.comboTyp.currentIndex() == KartenTyp.Deck)
        self.ui.leFusszeile.setEnabled(self.ui.comboTyp.currentIndex() != KartenTyp.Deck)
        if self.ui.comboTyp.currentIndex() == KartenTyp.Deck:
            self.ui.leFusszeile.setText("")
        self.updateSaveButtonState()
        
    def deleteChanged(self):
        isNew = KartenUtility.isNew(self.datenbank, self.ui.leName.text(), self.ui.comboTyp.currentIndex())
        delete = not isNew and self.ui.radioDelete.isChecked()
        self.ui.labelTitel.setEnabled(not delete)
        self.ui.leTitel.setEnabled(not delete)
        self.ui.labelUntertitel.setEnabled(not delete)
        self.ui.leUntertitel.setEnabled(not delete)
        self.ui.labelVoraussetzungen.setEnabled(not delete)
        self.ui.teVoraussetzungen.setEnabled(not delete)
        self.ui.labelBeschreibung.setEnabled(not delete)
        self.ui.teBeschreibung.setEnabled(not delete)
        self.ui.labelFusszeile.setEnabled(not delete)
        self.ui.leFusszeile.setEnabled(not delete)