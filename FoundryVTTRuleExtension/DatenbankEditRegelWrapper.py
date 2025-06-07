# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore, QtGui
from DatenbankElementEditorBase import DatenbankElementEditorBase
from Wolke import Wolke
from Core.Regel import Regel
import UI.DatenbankEditRegel
from DatenbankEditRegelWrapper import DatenbankEditRegelWrapper
import json
import os
import glob

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

# Input field types with descriptions
INPUT_FIELD_TYPES = {
    "CHECKBOX": {
        "label": "Checkbox",
        "description": "Checkbox - Eine einfache Ja/Nein Auswahl"
    },
    "NUMBER": {
        "label": "Nummerneingabefeld",
        "description": "Nummerneingabefeld - Ein Feld für Zahleneingaben"
    },
    "TREFFER_ZONE": {
        "label": "Trefferzonenauswahl",
        "description": "Trefferzonenauswahl - Auswahl einer spezifischen Trefferzone"
    }
}

class ModificationWidget(QtWidgets.QWidget):
    removed = QtCore.Signal(object)  # Signal when this modification is removed

    def __init__(self, modification_data=None, parent=None):
        super().__init__(parent)
        self.setupUi()
        if modification_data:
            self.setData(modification_data)

    def setupUi(self):
        # Create main layout
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(10, 10, 10, 10)

        # Create a frame for the border
        frame = QtWidgets.QFrame()
        frame.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Sunken)
        frameLayout = QtWidgets.QVBoxLayout(frame)
        frameLayout.setContentsMargins(10, 10, 10, 10)

        # Grid for the actual content
        grid = QtWidgets.QGridLayout()
        grid.setVerticalSpacing(10)

        # Row 1: Type and Value
        typeLabel = QtWidgets.QLabel("Typ")
        self.typeCombo = QtWidgets.QComboBox()
        self.typeCombo.addItems(MODIFICATION_TYPES)
        
        valueLabel = QtWidgets.QLabel("Wert")
        self.valueSpinBox = QtWidgets.QSpinBox()
        self.valueSpinBox.setRange(-999, 999)

        grid.addWidget(typeLabel, 0, 0)
        grid.addWidget(self.typeCombo, 0, 1)
        grid.addWidget(valueLabel, 0, 2)
        grid.addWidget(self.valueSpinBox, 0, 3)

        # Row 2: Operator and Target
        operatorLabel = QtWidgets.QLabel("Operator")
        self.operatorCombo = QtWidgets.QComboBox()
        self.operatorCombo.addItems(OPERATORS)

        targetLabel = QtWidgets.QLabel("Ziel")
        self.targetEdit = QtWidgets.QLineEdit()
        self.targetEdit.setPlaceholderText("actor.system...")

        grid.addWidget(operatorLabel, 1, 0)
        grid.addWidget(self.operatorCombo, 1, 1)
        grid.addWidget(targetLabel, 1, 2)
        grid.addWidget(self.targetEdit, 1, 3)

        # Row 3: Checkbox and Remove button
        self.affectedByInputCheck = QtWidgets.QCheckBox("Durch Input beeinflusst")
        removeButton = QtWidgets.QPushButton("-")
        removeButton.setMaximumWidth(30)
        removeButton.clicked.connect(lambda: self.removed.emit(self))

        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addWidget(self.affectedByInputCheck)
        buttonLayout.addStretch()
        buttonLayout.addWidget(removeButton)

        grid.addLayout(buttonLayout, 2, 0, 1, 4)  # Span all columns

        # Set column stretches
        grid.setColumnStretch(1, 2)  # Type combo gets more space
        grid.setColumnStretch(3, 2)  # Target edit gets more space

        # Add grid to frame
        frameLayout.addLayout(grid)

        # Add frame to main layout
        mainLayout.addWidget(frame)

        # Add bottom margin to separate from next modification
        self.setContentsMargins(0, 0, 0, 5)

    def setData(self, data):
        self.typeCombo.setCurrentText(data.get("type", "DAMAGE"))
        try:
            value = int(data.get("value", 0))
        except (ValueError, TypeError):
            value = 0
        self.valueSpinBox.setValue(value)
        self.operatorCombo.setCurrentText(data.get("operator", "ADD"))
        self.targetEdit.setText(data.get("target", ""))
        self.affectedByInputCheck.setChecked(data.get("affectedByInput", False))

    def getData(self):
        return {
            "type": self.typeCombo.currentText(),
            "value": self.valueSpinBox.value(),
            "operator": self.operatorCombo.currentText(),
            "target": self.targetEdit.text(),
            "affectedByInput": self.affectedByInputCheck.isChecked()
        }

class InputConfigWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi()

    def setupUi(self):
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        # Description text
        descLabel = QtWidgets.QLabel("Hier legst du fest, welches Eingabefeld im Würfeldialog für dieses Manöver angezeigt werden soll:")
        descLabel.setWordWrap(True)
        mainLayout.addWidget(descLabel)

        # Input configuration grid
        inputGrid = QtWidgets.QGridLayout()
        
        # Label field
        labelLabel = QtWidgets.QLabel("Label")
        self.labelEdit = QtWidgets.QLineEdit()
        inputGrid.addWidget(labelLabel, 0, 0)
        inputGrid.addWidget(self.labelEdit, 0, 1)

        # Field type combo
        fieldLabel = QtWidgets.QLabel("Feldtyp")
        self.fieldCombo = QtWidgets.QComboBox()
        # Add translated items
        for key, data in INPUT_FIELD_TYPES.items():
            self.fieldCombo.addItem(data["label"], key)  # Store the key as user data
            # Add tooltip for the item
            self.fieldCombo.setItemData(self.fieldCombo.count() - 1, data["description"], QtCore.Qt.ToolTipRole)
        self.fieldCombo.currentTextChanged.connect(self.onFieldTypeChanged)
        # Add tooltip for the combo box itself
        self.fieldCombo.setToolTip(INPUT_FIELD_TYPES[self.fieldCombo.itemData(0)]["description"])
        self.fieldCombo.currentTextChanged.connect(self.updateTooltip)
        
        inputGrid.addWidget(fieldLabel, 0, 2)
        inputGrid.addWidget(self.fieldCombo, 0, 3)

        # Min/Max fields (initially hidden)
        minLabel = QtWidgets.QLabel("Min")
        self.minSpinBox = QtWidgets.QSpinBox()
        self.minSpinBox.setRange(-999, 999)
        maxLabel = QtWidgets.QLabel("Max")
        self.maxSpinBox = QtWidgets.QSpinBox()
        self.maxSpinBox.setRange(-999, 999)
        
        self.minLabel = minLabel
        self.maxLabel = maxLabel
        
        inputGrid.addWidget(minLabel, 0, 4)
        inputGrid.addWidget(self.minSpinBox, 0, 5)
        inputGrid.addWidget(maxLabel, 0, 6)
        inputGrid.addWidget(self.maxSpinBox, 0, 7)

        # Set column stretches
        inputGrid.setColumnStretch(1, 2)  # Label edit gets more space
        inputGrid.setColumnStretch(3, 1)  # Field combo
        inputGrid.setColumnStretch(5, 1)  # Min spin
        inputGrid.setColumnStretch(7, 1)  # Max spin

        mainLayout.addLayout(inputGrid)

        # Set initial visibility
        self.onFieldTypeChanged(self.fieldCombo.currentText())

    def updateTooltip(self, text):
        # Update the combo box tooltip when selection changes
        index = self.fieldCombo.currentIndex()
        key = self.fieldCombo.itemData(index)
        self.fieldCombo.setToolTip(INPUT_FIELD_TYPES[key]["description"])

    def onFieldTypeChanged(self, field_text):
        # Get the actual field type from user data
        index = self.fieldCombo.currentIndex()
        field_type = self.fieldCombo.itemData(index)
        show_min_max = field_type == "NUMBER"
        self.minLabel.setVisible(show_min_max)
        self.maxLabel.setVisible(show_min_max)
        self.minSpinBox.setVisible(show_min_max)
        self.maxSpinBox.setVisible(show_min_max)

    def setData(self, data):
        if not data:
            return
        self.labelEdit.setText(data.get('label', ''))
        # Find and set the correct field type
        field_type = data.get('field', 'NUMBER')
        for i in range(self.fieldCombo.count()):
            if self.fieldCombo.itemData(i) == field_type:
                self.fieldCombo.setCurrentIndex(i)
                break
        self.minSpinBox.setValue(data.get('min', 0))
        self.maxSpinBox.setValue(data.get('max', 8))

    def getData(self):
        # Get the actual field type from user data
        index = self.fieldCombo.currentIndex()
        field_type = self.fieldCombo.itemData(index)
        
        data = {
            'label': self.labelEdit.text(),
            'field': field_type
        }
        if field_type == "NUMBER":
            data['min'] = self.minSpinBox.value()
            data['max'] = self.maxSpinBox.value()
        return data

class DatenbankEditRegelWrapperPlus(DatenbankEditRegelWrapper):
    def __init__(self, datenbank, regel=None):
        super().__init__(datenbank, regel)
        self.modificationWidgets = []
        self.foundry_maneuvers = self.load_foundry_maneuvers()

    def load_config(self):
        """Load configuration from maneuver_foundry_extensions.json"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "maneuver_foundry_extensions.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            return None

    def load_foundry_maneuvers(self):
        """Load maneuvers from config file."""
        try:
            config = self.load_config()
            return config.get('maneuvers', {})
        except Exception as e:
            print(f"Error loading maneuvers from config: {str(e)}")
            return {}

    def onSetupUi(self):
        # First setup the base UI
        super().onSetupUi()
        
        # Then add our custom UI elements
        self.setupFoundryUi()

    def setupFoundryUi(self):
        # Create form layout for Foundry extensions
        formLayout = QtWidgets.QFormLayout()
        formLayout.setLabelAlignment(QtCore.Qt.AlignLeft)
        formLayout.setFormAlignment(QtCore.Qt.AlignLeft)

        # Verteidigungsmanöver checkbox
        self.verteidigungLabel = QtWidgets.QLabel("Verteidigungsmanöver")
        self.verteidigungCheckbox = QtWidgets.QCheckBox()
        defenseWidget = QtWidgets.QWidget()
        defenseLayout = QtWidgets.QHBoxLayout(defenseWidget)
        defenseLayout.setContentsMargins(0, 0, 0, 0)
        defenseLayout.addWidget(self.verteidigungCheckbox)
        defenseLayout.addStretch()
        formLayout.addRow(self.verteidigungLabel, defenseWidget)

        # Input configuration with subheader
        formLayout.addRow("Input:", QtWidgets.QWidget())  # Empty row for spacing
        self.inputConfigWidget = InputConfigWidget()
        formLayout.addRow("", self.inputConfigWidget)

        # Icon input with its label
        self.iconEdit = QtWidgets.QLineEdit()
        self.iconEdit.setPlaceholderText("systems/dsa5/icons/...")
        formLayout.addRow("Icon:", self.iconEdit)

        # Modifications section with header and add button
        headerWidget = QtWidgets.QWidget()
        headerLayout = QtWidgets.QHBoxLayout(headerWidget)
        headerLayout.setContentsMargins(0, 0, 0, 0)
        self.addButton = QtWidgets.QPushButton("+")
        self.addButton.setMaximumWidth(30)
        self.addButton.clicked.connect(self.addModification)
        headerLayout.addWidget(self.addButton)
        headerLayout.addStretch()
        formLayout.addRow("Modifikatoren:", headerWidget)

        # Description and hints for modifications
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

        # Add description and hints to a container
        hintsContainer = QtWidgets.QWidget()
        hintsContainerLayout = QtWidgets.QVBoxLayout(hintsContainer)
        hintsContainerLayout.setContentsMargins(0, 0, 0, 10)  # Add bottom margin before modifications
        hintsContainerLayout.addWidget(descLabel)
        hintsContainerLayout.addLayout(hintsLayout)
        formLayout.addRow("", hintsContainer)

        # Create container for modifications
        self.modContainer = QtWidgets.QWidget()
        self.modLayout = QtWidgets.QVBoxLayout(self.modContainer)
        self.modLayout.setContentsMargins(0, 0, 0, 0)
        self.modLayout.setSpacing(0)  # Remove spacing between modifications
        formLayout.addRow("", self.modContainer)
        
        # Main widget setup
        self.modificationsWidget = QtWidgets.QWidget()
        mainLayout = QtWidgets.QVBoxLayout(self.modificationsWidget)
        mainLayout.addLayout(formLayout)
        
        # Add to form layout after description
        if hasattr(self.ui, "teBeschreibung"):
            self.ui.formLayout.insertRow(self.ui.formLayout.rowCount(), "Foundry Regel\nErweiterungen:", self.modificationsWidget)
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
        # Show/hide Verteidigungsmanöver checkbox and label only for Nahkampfmanöver
        is_nahkampf = current_category == "Nahkampfmanöver"
        self.verteidigungLabel.setVisible(is_nahkampf)
        self.verteidigungCheckbox.setVisible(is_nahkampf)

    def load(self, regel):
        # First check the category
        current_category = self.ui.comboKategorie.currentText()
        foundry_enabled = current_category in FOUNDRY_CATEGORIES
        
        # Load all original fields first
        super().load(regel)
        
        # Clear existing modifications
        for widget in self.modificationWidgets:
            widget.deleteLater()
        self.modificationWidgets.clear()
        
        # Only proceed with Foundry-specific loading if category matches
        if not foundry_enabled:
            self.updateModificationFieldVisibility()
            return
            
        # Check if we have predefined modifications for this regel
        if regel.name in self.foundry_maneuvers:
            foundry_data = self.foundry_maneuvers[regel.name]
            
            # Set defense checkbox if it's a defense maneuver
            self.verteidigungCheckbox.setChecked(foundry_data['isDefense'])
            
            # Set icon if available
            self.iconEdit.setText(foundry_data['icon'])
            
            # Load predefined modifications if no custom ones exist
            if not hasattr(regel, 'foundry_modifications'):
                modifications = foundry_data['modifications']
                regel.foundry_modifications = json.dumps(modifications)
        
        # Load Verteidigungsmanöver state (if not already set from predefined data)
        if not regel.name in self.foundry_maneuvers:
            self.verteidigungCheckbox.setChecked(getattr(regel, "foundry_verteidigung", False))
        
        # Load icon (if not already set from predefined data)
        if not regel.name in self.foundry_maneuvers:
            self.iconEdit.setText(getattr(regel, "foundry_icon", ""))

        # Load input configuration
        if hasattr(regel, "foundry_input"):
            try:
                input_data = json.loads(regel.foundry_input)
                self.inputConfigWidget.setData(input_data)
            except (json.JSONDecodeError, AttributeError):
                pass
        
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
            # Save input configuration
            regel.foundry_input = json.dumps(self.inputConfigWidget.getData()) 