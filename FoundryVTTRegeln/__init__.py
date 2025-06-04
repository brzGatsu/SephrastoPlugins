from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from Core.DatenbankEinstellung import DatenbankEinstellung
from Wolke import Wolke
import DatenbankEditor
import logging
from .DatenbankEditRegelWrapper import DatenbankEditRegelWrapperPlus

__version__ = "1.0.0"  # Plugin Version

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FoundryVTTRegeln")
print("FoundryVTTRegeln Plugin module loaded") # Direct console output

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
        print("FoundryVTTRegeln Plugin initializing...") # Direct console output
        logger.info("FoundryVTTRegeln Plugin initializing...")
        
        # Store event bus registrations
        self.datenbank_laden_reg = EventBus.addAction("datenbank_laden", self.datenbankLadenHook)
        self.regel_reg = EventBus.addFilter("dbe_class_regel_wrapper", self.dbeClassRegelFilter)
        
        print("Event handlers registered:") # Direct console output
        print(f"- datenbank_laden: {self.datenbank_laden_reg}")
        print(f"- dbe_class_regel_wrapper: {self.regel_reg}")
        logger.info("Event handlers registered")

    def changesCharacter(self):
        if not hasattr(self, "db") or self.db is None or not hasattr(self.db, "einstellungen"):
            return True
        return self.db.einstellungen["FoundryVTTRegeln Plugin: Aktivieren"].wert

    def changesDatabase(self):
        return True

    def datenbankLadenHook(self, params):
        print("FoundryVTTRegeln datenbankLadenHook called") # Direct console output
        logger.info("datenbankLadenHook called with params: %s", params)
        
        try:
            # Initialize settings when database is loaded
            self.db = params["datenbank"]
            print("Database reference stored") # Direct console output
            
            # Plugin activation setting
            e = DatenbankEinstellung()
            e.name = "FoundryVTTRegeln Plugin: Aktivieren"
            e.beschreibung = "Hiermit kannst du das FoundryVTTRegeln-Plugin nur für diese Hausregeln deaktivieren."
            e.text = "True"
            e.typ = "Bool"
            e.kategorie = "Plugins"
            self.db.loadElement(e)
            print("Activation setting loaded") # Direct console output
            
            # Default text modification setting
            e = DatenbankEinstellung()
            e.name = "FoundryVTTRegeln Plugin: Standard Text"
            e.beschreibung = "Standardtext für neue Regeln in Foundry VTT."
            e.text = "Keine Modifikationen"
            e.typ = "Text"
            e.kategorie = "Plugins"
            self.db.loadElement(e)
            print("Default text setting loaded") # Direct console output
            
            logger.info("Settings loaded successfully")
            print("FoundryVTTRegeln Plugin: Settings loaded successfully") # Direct console output
            
        except Exception as e:
            logger.error("Error in datenbankLadenHook: %s", str(e), exc_info=True)
            print(f"Error in FoundryVTTRegeln: {str(e)}") # Direct console output
            raise

    def dbeClassRegelFilter(self, editorType, params):
        print(f"dbeClassRegelFilter called for type: {editorType}") # Direct console output
        logger.info("dbeClassRegelFilter called for type: %s", editorType)
        
        if not hasattr(self, "db"):
            print("No database reference") # Direct console output
            return editorType
        if self.db is None:
            print("Database is None") # Direct console output
            return editorType
        if not hasattr(self.db, "einstellungen"):
            print("No settings in database") # Direct console output
            return editorType
        if not self.db.einstellungen["FoundryVTTRegeln Plugin: Aktivieren"].wert:
            print("Plugin is disabled") # Direct console output
            return editorType

        print("Returning extended editor class") # Direct console output
        return DatenbankEditRegelWrapperPlus 