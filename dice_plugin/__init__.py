# dice_plugin/__init__.py
import os
import json
import sys
import traceback

from Wolke import Wolke
from EventBus import EventBus
from CharakterEditor import Tab

# Pfad hinzufügen, damit lokale Module (EffectsHelper, …) gefunden werden
current_path = os.path.dirname(os.path.abspath(__file__))
if current_path not in sys.path:
    sys.path.insert(0, current_path)

# Wrapper erst nach path-Fix importieren – Fehler sichtbar machen, Plugin-Klasse bleibt ladbar
_IMPORT_ERROR = None
DicePluginWrapper = None
MasterPluginWrapper = None
try:
    from DicePluginWrapper import DicePluginWrapper
    from MasterPluginWrapper import MasterPluginWrapper
except Exception as e:
    _IMPORT_ERROR = e
    traceback.print_exc()
    try:
        import logging
        logging.getLogger().critical(
            "dice_plugin: Import fehlgeschlagen: %s", e, exc_info=True
        )
    except Exception:
        pass


def dice_plugin_charakter_serialisiert(params):
    serializer = params["serializer"]
    char = params["charakter"]

    serializer.begin("DicePlugin")

    # === Hauptcharakter ===
    wunden = getattr(char, "dicePlugin_wunden", [None] * 8)
    wunden_str = ",".join(str(w) if w is not None else "None" for w in wunden)
    serializer.set("Einschraenkungen", wunden_str)
    serializer.set("EinschraenkungenIgnorieren", getattr(char, "dicePlugin_wunden_ignorieren", False))
    serializer.set("EinschraenkungenModus", int(getattr(char, "dicePlugin_wunden_modus", 0) or 0))

    serializer.set("Schips", getattr(char, "dicePlugin_schips", 4))
    geld = getattr(char, "dicePlugin_geld", {'Dukaten': 0, 'Silber': 0, 'Heller': 0, 'Kreuzer': 0})
    serializer.set("Dukaten", geld.get('Dukaten', 0))
    serializer.set("Silber", geld.get('Silber', 0))
    serializer.set("Heller", geld.get('Heller', 0))
    serializer.set("Kreuzer", geld.get('Kreuzer', 0))
    serializer.set("Kleidung", getattr(char, "dicePlugin_kleidung", ""))
    serializer.set("CurrentAsP", getattr(char, "dicePlugin_current_asp", -1))
    serializer.set("CurrentKaP", getattr(char, "dicePlugin_current_kap", -1))
    try:
        serializer.set(
            "Munition",
            json.dumps(getattr(char, "dicePlugin_munition", []) or [], ensure_ascii=False),
        )
    except Exception:
        serializer.set("Munition", "[]")

    # Effekte Hauptcharakter (erweitertes Modell)
    serializer.beginList("Effekte")
    for e in getattr(char, "dicePlugin_effekte", []) or []:
        serializer.begin("Effekt")
        serializer.set("name", e.get("name", ""))
        serializer.set("duration", int(e.get("duration", 0) or 0))
        serializer.set("has_timer", bool(e.get("has_timer", True)))
        serializer.set("info_text", e.get("info_text", "") or "")
        serializer.set("info_roll", e.get("info_roll", "") or "")
        serializer.set("notify_at", int(e.get("notify_at", 0) or 0))
        serializer.set("source", e.get("source", "custom") or "custom")
        serializer.set("on_end", e.get("on_end") or "")
        mods = e.get("mods") or {}
        serializer.set("mods", json.dumps(mods, ensure_ascii=False))
        flags = e.get("flags") or {}
        serializer.set("flags", json.dumps(flags, ensure_ascii=False))
        known = {
            "name", "duration", "has_timer", "info_text", "info_roll",
            "notify_at", "source", "on_end", "mods", "flags",
        }
        extra = {k: v for k, v in e.items() if k not in known}
        try:
            serializer.set("extra", json.dumps(extra, ensure_ascii=False))
        except Exception:
            serializer.set("extra", "{}")
        serializer.end()
    serializer.end()

    # Inventar
    serializer.beginList("Inventar")
    for c in getattr(char, "dicePlugin_inventar", [{"name": "Am Körper", "inhalt": ""}]):
        serializer.begin("Behälter")
        serializer.set("name", c.get("name", ""))
        serializer.set("inhalt", c.get("inhalt", ""))
        serializer.end()
    serializer.end()

    # Tagebuch
    serializer.beginList("Tagebuch")
    for t in getattr(char, "dicePlugin_tagebuch", [{"titel": "Allgemein", "inhalt": ""}]):
        serializer.begin("Thema")
        serializer.set("titel", t.get("titel", ""))
        serializer.set("inhalt", t.get("inhalt", ""))
        serializer.end()
    serializer.end()

    serializer.end()  # DicePlugin


def dice_plugin_charakter_deserialisiert(params):
    deserializer = params["deserializer"]
    char = params["charakter"]
    if not deserializer.find("DicePlugin"):
        return

    # === Hauptcharakter ===
    w_str = deserializer.get("Einschraenkungen", "")
    char.dicePlugin_wunden = [None]*8 if not w_str else [None if x=="None" else x for x in w_str.split(",")]
    char.dicePlugin_wunden_ignorieren = deserializer.getBool("EinschraenkungenIgnorieren", False)
    char.dicePlugin_wunden_modus = deserializer.getInt("EinschraenkungenModus", 0)
    char.dicePlugin_schips = deserializer.getInt("Schips", 4)
    char.dicePlugin_geld = {
        'Dukaten': deserializer.getInt("Dukaten", 0),
        'Silber': deserializer.getInt("Silber", 0),
        'Heller': deserializer.getInt("Heller", 0),
        'Kreuzer': deserializer.getInt("Kreuzer", 0)
    }
    char.dicePlugin_kleidung = deserializer.get("Kleidung", "")
    char.dicePlugin_current_asp = deserializer.getInt("CurrentAsP", -1)
    char.dicePlugin_current_kap = deserializer.getInt("CurrentKaP", -1)
    mun_raw = deserializer.get("Munition", "[]")
    try:
        mun = json.loads(mun_raw) if mun_raw else []
    except Exception:
        mun = []
    char.dicePlugin_munition = mun if isinstance(mun, list) else []

    # Effekte (abwärtskompatibel)
    char.dicePlugin_effekte = []
    if deserializer.find("Effekte"):
        for _ in deserializer.listTags():
            mods_raw = deserializer.get("mods", "{}")
            flags_raw = deserializer.get("flags", "{}")
            try:
                mods = json.loads(mods_raw) if mods_raw else {}
            except Exception:
                mods = {}
            try:
                flags = json.loads(flags_raw) if flags_raw else {}
            except Exception:
                flags = {}
            has_timer_raw = deserializer.get("has_timer", "True")
            if isinstance(has_timer_raw, bool):
                has_timer = has_timer_raw
            else:
                has_timer = str(has_timer_raw).lower() in ("1", "true", "yes")
            extra_raw = deserializer.get("extra", "{}")
            try:
                extra = json.loads(extra_raw) if extra_raw else {}
            except Exception:
                extra = {}
            if not isinstance(extra, dict):
                extra = {}
            packed = {
                "name": deserializer.get("name", ""),
                "duration": deserializer.getInt("duration", 0),
                "has_timer": has_timer,
                "info_text": deserializer.get("info_text", ""),
                "info_roll": deserializer.get("info_roll", ""),
                "notify_at": deserializer.getInt("notify_at", 0),
                "source": deserializer.get("source", "custom"),
                "on_end": deserializer.get("on_end", "") or None,
                "mods": mods,
                "flags": flags,
            }
            packed.update(extra)
            char.dicePlugin_effekte.append(packed)
        deserializer.end()

    # Inventar
    char.dicePlugin_inventar = [{"name": "Am Körper", "inhalt": ""}]
    if deserializer.find("Inventar"):
        char.dicePlugin_inventar = []
        for _ in deserializer.listTags():
            char.dicePlugin_inventar.append({"name": deserializer.get("name", ""), "inhalt": deserializer.get("inhalt", "")})
        deserializer.end()

    # Tagebuch
    char.dicePlugin_tagebuch = [{"titel": "Allgemein", "inhalt": ""}]
    if deserializer.find("Tagebuch"):
        char.dicePlugin_tagebuch = []
        for _ in deserializer.listTags():
            char.dicePlugin_tagebuch.append({"titel": deserializer.get("titel", ""), "inhalt": deserializer.get("inhalt", "")})
        deserializer.end()

    deserializer.end()


def mark_as_modified():
    if hasattr(Wolke, "Char") and Wolke.Char is not None:
        Wolke.Char.modified = True


class Plugin:
    """Einstiegspunkt für Sephrasto – muss immer existieren."""

    def __init__(self):
        self.diceWrapper = None
        self.masterWrapper = None

        if _IMPORT_ERROR is not None:
            try:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    None,
                    "Dice Plugin – Importfehler",
                    "Das Dice Plugin konnte nicht vollständig geladen werden:\n\n"
                    f"{_IMPORT_ERROR}\n\n"
                    "Bitte stelle sicher, dass alle Dateien im Ordner dice_plugin liegen:\n"
                    "• __init__.py\n"
                    "• DicePluginWrapper.py\n"
                    "• MasterPluginWrapper.py\n"
                    "• EffectsHelper.py\n"
                    "• TalentInfoDialog.py\n"
                    "• manifest.json",
                )
            except Exception:
                pass

        EventBus.addAction("charakter_serialisiert", dice_plugin_charakter_serialisiert)
        EventBus.addAction("charakter_deserialisiert", dice_plugin_charakter_deserialisiert)
        EventBus.addAction("charaktereditor_oeffnet", self.on_editor_opened)
        EventBus.addAction("charaktereditor_geschlossen", self.on_editor_closed)

    def on_editor_opened(self, params):
        if DicePluginWrapper is None or MasterPluginWrapper is None:
            return
        self.diceWrapper = DicePluginWrapper()
        self.masterWrapper = MasterPluginWrapper()

        from PySide6.QtWidgets import QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QCheckBox, QComboBox

        def connect_widget(widget):
            if isinstance(widget, (QLineEdit, QTextEdit)):
                widget.textChanged.connect(mark_as_modified)
            elif isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(mark_as_modified)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.valueChanged.connect(mark_as_modified)
            elif isinstance(widget, QCheckBox):
                widget.stateChanged.connect(mark_as_modified)

        widget_types = [QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QCheckBox, QComboBox]
        for wtype in widget_types:
            for child in self.diceWrapper.form.findChildren(wtype):
                connect_widget(child)

    def on_editor_closed(self, params):
        self.diceWrapper = None
        self.masterWrapper = None

    def createCharakterTabs(self):
        tabs = []
        if self.diceWrapper:
            tabs.append(Tab(order=80, wrapper=self.diceWrapper, form=self.diceWrapper.form, name="Dice Plugin"))
        if self.masterWrapper:
            tabs.append(Tab(order=81, wrapper=self.masterWrapper, form=self.masterWrapper.form, name="Dice Master"))
        return tabs
