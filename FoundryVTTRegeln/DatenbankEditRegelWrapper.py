# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore, QtGui
from DatenbankElementEditorBase import DatenbankElementEditorBase
from Wolke import Wolke
from Core.Regel import Regel
import UI.DatenbankEditRegel
import json

# Categories that should show the modifications field
FOUNDRY_CATEGORIES = [
    "Nahkampfmanöver",
    "Fernkampfmanöver",
    "Magische Modifikationen",
    "Karmale Modifikationen",
    "Dämonische Modifikationen"
]

# Modification types
MODIFICATION_TYPES = [
    "DAMAGE",
    "DEFENCE",
    "ATTACK",
    "INITIATIVE",
    "LOADING_TIME",
    "SPECIAL_RESSOURCE",
    "WEAPON_DAMAGE",
    "CHANGE_DAMAGE_TYPE",
    "ZERO_DAMAGE",
    "ARMOR_BREAKING",
    "SPECIAL_TEXT"
]

# Operators
OPERATORS = [
    "MULTIPLY",
    "ADD",
    "SUBTRACT",
    "DIVIDE"
]

class ModificationWidget(QtWidgets.QWidget):
    removed = QtCore.Signal(object)  # Signal when this modification is removed

    def __init__(self, modification_data=None, parent=None):
        super().__init__(parent)
        self.setupUi()
        if modification_data:
            self.setData(modification_data)

    def setupUi(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Type ComboBox
        self.typeCombo = QtWidgets.QComboBox()
        self.typeCombo.addItems(MODIFICATION_TYPES)
        layout.addWidget(self.typeCombo)

        # Value SpinBox
        self.valueSpinBox = QtWidgets.QSpinBox()
        self.valueSpinBox.setRange(-999, 999)
        layout.addWidget(self.valueSpinBox)

        # Operator ComboBox
        self.operatorCombo = QtWidgets.QComboBox()
        self.operatorCombo.addItems(OPERATORS)
        layout.addWidget(self.operatorCombo)

        # Target LineEdit
        self.targetEdit = QtWidgets.QLineEdit()
        self.targetEdit.setPlaceholderText("actor.system...")
        layout.addWidget(self.targetEdit)

        # Remove Button
        removeButton = QtWidgets.QPushButton("-")
        removeButton.setMaximumWidth(30)
        removeButton.clicked.connect(lambda: self.removed.emit(self))
        layout.addWidget(removeButton)

    def setData(self, data):
        self.typeCombo.setCurrentText(data.get("type", "DAMAGE"))
        self.valueSpinBox.setValue(data.get("value", 0))
        self.operatorCombo.setCurrentText(data.get("operator", "ADD"))
        self.targetEdit.setText(data.get("target", ""))

    def getData(self):
        return {
            "type": self.typeCombo.currentText(),
            "value": self.valueSpinBox.value(),
            "operator": self.operatorCombo.currentText(),
            "target": self.targetEdit.text()
        }

class DatenbankEditRegelWrapperPlus(DatenbankElementEditorBase):
    def __init__(self, datenbank, regel=None):
        super().__init__(datenbank, UI.DatenbankEditRegel.Ui_dialog(), Regel, regel)
        self.modificationWidgets = []

    def onSetupUi(self):
        super().onSetupUi()
        
        # Create container for modifications
        self.modContainer = QtWidgets.QWidget()
        self.modLayout = QtWidgets.QVBoxLayout(self.modContainer)
        self.modLayout.setContentsMargins(0, 0, 0, 0)
        
        # Add button for new modifications
        self.addButton = QtWidgets.QPushButton("+")
        self.addButton.setMaximumWidth(30)
        self.addButton.clicked.connect(self.addModification)

        # Icon input field
        iconLayout = QtWidgets.QHBoxLayout()
        iconLabel = QtWidgets.QLabel("Icon:")
        self.iconEdit = QtWidgets.QLineEdit()
        self.iconEdit.setPlaceholderText("systems/dsa5/icons/...")
        iconLayout.addWidget(iconLabel)
        iconLayout.addWidget(self.iconEdit)

        # Main header
        mainHeaderLayout = QtWidgets.QHBoxLayout()
        mainHeaderLabel = QtWidgets.QLabel("Foundry Regel Erweiterungen")
        font = mainHeaderLabel.font()
        font.setBold(True)
        mainHeaderLabel.setFont(font)
        mainHeaderLayout.addWidget(mainHeaderLabel)
        mainHeaderLayout.addStretch()

        # Verteidigungsmanöver checkbox
        self.verteidigungCheckbox = QtWidgets.QCheckBox("Verteidigungsmanöver")
        self.verteidigungCheckbox.hide()  # Initially hidden
        
        # Verteidigungsmanöver description
        self.verteidigungDesc = QtWidgets.QLabel("Flaggt Manöver als Verteidigungsmanöver in Foundry für bessere Sortierung im Kampfdialog")
        self.verteidigungDesc.setWordWrap(True)
        self.verteidigungDesc.setStyleSheet("color: gray;")  # Make it look like a hint
        self.verteidigungDesc.hide()  # Initially hidden

        # Sub-header for modifications
        subHeaderLayout = QtWidgets.QHBoxLayout()
        subHeaderLabel = QtWidgets.QLabel("Foundry Manöver Modifikatoren")
        subHeaderLayout.addWidget(subHeaderLabel)
        subHeaderLayout.addStretch()
        subHeaderLayout.addWidget(self.addButton)
        
        # Description and hints
        descLabel = QtWidgets.QLabel("Hier definierst du die Effekte des Manövers für Foundry VTT. Empfehlungen:")
        descLabel.setWordWrap(True)
        
        hintsLayout = QtWidgets.QVBoxLayout()
        hints = [
            "Verwende \"Subtrahieren\" nur wenn nötig (z.B. für Belastungswert, wenn du das Feld Target verwendest)",
            "Eine -1 ist leichter zu lesen als \"Subtrahieren\"",
            "Beispiel Wuchtschlag: AT -1 (Addieren) und Schaden +1 (Addieren)"
        ]
        for hint in hints:
            hintLabel = QtWidgets.QLabel("• " + hint)
            hintLabel.setWordWrap(True)
            hintsLayout.addWidget(hintLabel)
        
        # Main layout for modifications section
        self.modificationsWidget = QtWidgets.QWidget()
        mainLayout = QtWidgets.QVBoxLayout(self.modificationsWidget)
        mainLayout.addLayout(mainHeaderLayout)
        mainLayout.addWidget(self.verteidigungCheckbox)
        mainLayout.addWidget(self.verteidigungDesc)
        mainLayout.addLayout(subHeaderLayout)
        mainLayout.addWidget(descLabel)
        mainLayout.addLayout(hintsLayout)
        mainLayout.addWidget(self.modContainer)
        mainLayout.addLayout(iconLayout)  # Add icon field at the bottom
        
        # Add to form layout after description
        if hasattr(self.ui, "teBeschreibung"):
            self.ui.formLayout.insertRow(self.ui.formLayout.rowCount(), "", self.modificationsWidget)
            # Initially hide the fields - they will be shown/hidden based on category
            self.modificationsWidget.hide()
        
        # Connect category combobox change to our visibility handler
        if hasattr(self.ui, "comboKategorie"):
            self.ui.comboKategorie.currentTextChanged.connect(self.updateModificationFieldVisibility)

    def addModification(self, data=None):
        widget = ModificationWidget(data)
        widget.removed.connect(self.removeModification)
        self.modificationWidgets.append(widget)
        self.modLayout.addWidget(widget)

    def removeModification(self, widget):
        if widget in self.modificationWidgets:
            self.modificationWidgets.remove(widget)
            widget.deleteLater()

    def updateModificationFieldVisibility(self):
        if not hasattr(self.ui, "comboKategorie"):
            return
        
        current_category = self.ui.comboKategorie.currentText()
        should_show = current_category in FOUNDRY_CATEGORIES
        
        self.modificationsWidget.setVisible(should_show)
        # Show/hide Verteidigungsmanöver checkbox and description only for Nahkampfmanöver
        is_nahkampf = current_category == "Nahkampfmanöver"
        self.verteidigungCheckbox.setVisible(is_nahkampf)
        self.verteidigungDesc.setVisible(is_nahkampf)

    def load(self, regel):
        super().load(regel)
        
        # Clear existing modifications
        for widget in self.modificationWidgets:
            widget.deleteLater()
        self.modificationWidgets.clear()
        
        # Load Verteidigungsmanöver state
        self.verteidigungCheckbox.setChecked(getattr(regel, "foundry_verteidigung", False))
        
        # Load icon
        self.iconEdit.setText(getattr(regel, "foundry_icon", ""))
        
        # Load modifications from regel
        if hasattr(regel, "foundry_modifications"):
            try:
                modifications = json.loads(regel.foundry_modifications)
                for mod in modifications:
                    self.addModification(mod)
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # Update visibility based on current category
        self.updateModificationFieldVisibility()

    def update(self, regel):
        super().update(regel)
        # Update modifications only if the category matches
        if self.ui.comboKategorie.currentText() in FOUNDRY_CATEGORIES:
            modifications = [widget.getData() for widget in self.modificationWidgets]
            regel.foundry_modifications = json.dumps(modifications)
            # Save Verteidigungsmanöver state
            regel.foundry_verteidigung = self.verteidigungCheckbox.isChecked()
            # Save icon
            regel.foundry_icon = self.iconEdit.text() 