from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from Core.DatenbankEinstellung import DatenbankEinstellung
from Wolke import Wolke
import DatenbankEditor
import logging
from .DatenbankEditRegelWrapperPlus import DatenbankEditRegelWrapperPlus
from .RegelExtension import extend_regel

__version__ = "1.0.0"  # Plugin Version

# Categories that should show the modifications field
FOUNDRY_CATEGORIES = [
    "Nahkampfmanöver",
    "Fernkampfmanöver",
    "Magische Modifikationen",
    "Karmale Modifikationen",
    "Dämonische Modifikationen"
]

class Plugin:
    def __init__(self):        
        # Store event bus registrations
        EventBus.addAction("datenbank_laden", self.datenbankLadenHook)
        EventBus.addFilter("dbe_class_regel_wrapper", self.dbeClassRegelFilter)

        # Extend the Regel class with XML serialization support
        extend_regel()

    def changesCharacter(self):
        if not hasattr(self, "db") or self.db is None or not hasattr(self.db, "einstellungen"):
            return True
        return self.db.einstellungen["FoundryVTTRuleExtension Plugin: Aktivieren"].wert

    def changesDatabase(self):
        return True

    def datenbankLadenHook(self, params):
        try:
            # Initialize settings when database is loaded
            self.db = params["datenbank"]
            
            # Plugin activation setting
            e = DatenbankEinstellung()
            e.name = "FoundryVTTRuleExtension Plugin: Aktivieren"
            e.beschreibung = "Hiermit kannst du das FoundryVTTRuleExtension-Plugin nur für diese Hausregeln deaktivieren."
            e.text = "True"
            e.typ = "Bool"
            e.kategorie = "Plugins"
            self.db.loadElement(e)
            
            # Default text modification setting
            e = DatenbankEinstellung()
            e.name = "FoundryVTTRuleExtension Plugin: Standard Text"
            e.beschreibung = "Standardtext für neue Regeln in Foundry VTT."
            e.text = "Keine Modifikationen"
            e.typ = "Text"
            e.kategorie = "Plugins"
            self.db.loadElement(e)
            
            logger.info("Settings loaded successfully")
            
        except Exception as e:
            logger.error("Error in datenbankLadenHook: %s", str(e), exc_info=True)
            raise

    def dbeClassRegelFilter(self, editorType, params):
        if not hasattr(self, "db"):
            return editorType
        if self.db is None:
            return editorType
        if not hasattr(self.db, "einstellungen"):
            return editorType
        if not self.db.einstellungen["FoundryVTTRuleExtension Plugin: Aktivieren"].wert:
            return editorType

        return DatenbankEditRegelWrapperPlus 

    def createDatenbankEditRegelWrapper(self, datenbank, regel=None):
        return DatenbankEditRegelWrapperPlus(datenbank, regel) 