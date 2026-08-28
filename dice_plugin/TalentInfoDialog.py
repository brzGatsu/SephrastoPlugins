# dice_plugin/TalentInfoDialog.py
from PySide6 import QtCore, QtWidgets, QtGui
from Wolke import Wolke
from Hilfsmethoden import Hilfsmethoden
import random
import re

# Hilfsfunktion für Würfelwürfe direkt im Dialog
def parse_and_roll_dice_string(dice_string, modifier=0):
    total_result = 0
    result_parts = []
    
    pattern = r"([+-]?\s*\d*[wWdD]\d+|\s*[+-]?\s*\d+)"
    parts = re.findall(pattern, dice_string.replace(" ",""))
    
    for part in parts:
        part = part.strip()
        if not part: continue
        
        dice_pattern = re.match(r"([+-])?(\d+)?[wWdD](\d+)", part)
        mod_pattern = re.match(r"([+-])?(\d+)", part)
        
        if dice_pattern:
            sign = -1 if dice_pattern.group(1) == '-' else 1
            num_dice = int(dice_pattern.group(2)) if dice_pattern.group(2) else 1
            sides = int(dice_pattern.group(3))
            
            current_rolls = [random.randint(1, sides) for _ in range(num_dice)]
            sum_of_rolls = sum(current_rolls)
            total_result += sign * sum_of_rolls
            
            roll_str = f"{num_dice}W{sides} ({', '.join(map(str, current_rolls))})"
            op = dice_pattern.group(1) or '+'
            result_parts.append(f"{op} {roll_str}")
            
        elif mod_pattern and not re.search(r'[wWdD]', part):
            sign = -1 if mod_pattern.group(1) == '-' else 1
            value = int(mod_pattern.group(2))
            total_result += sign * value
            result_parts.append(f"{mod_pattern.group(1) or '+'} {value}")
            
    if modifier != 0:
        total_result += modifier
        sign_str = "+" if modifier > 0 else "-"
        result_parts.append(f"{sign_str} {abs(modifier)} (Mod)")

    if not result_parts:
        return 0, "Ergebnis: Ungültige Eingabe."
        
    full_result_str = " ".join(result_parts).lstrip('+ ')
    return total_result, f"{full_result_str} = <b>{total_result}</b>"

class TalentInfoDialog(QtWidgets.QDialog):
    def __init__(self, talent_name, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Talentinformation")
        # Nicht-modal: Sephrasto bleibt bedienbar
        # KEIN WindowStaysOnTopHint – sonst liegen Fenster über dem Task-Manager
        self.setModal(False)
        self.setWindowModality(QtCore.Qt.WindowModality.NonModal)
        self.setWindowFlags(
            QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.WindowTitleHint
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            | QtCore.Qt.WindowType.WindowMinMaxButtonsHint
        )
        
        # UI-Elemente erstellen
        self.layout = QtWidgets.QVBoxLayout(self)
        self.labelName = QtWidgets.QLabel()
        self.labelName.setObjectName("h2") # Nutzt den h2-Stil aus dem Stylesheet
        self.labelTyp = QtWidgets.QLabel()
        self.labelKosten = QtWidgets.QLabel()
        self.plainText = QtWidgets.QTextBrowser()
        self.plainText.setOpenExternalLinks(True)

        # Layout zusammenbauen
        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addWidget(self.labelTyp)
        h_layout.addStretch()
        h_layout.addWidget(self.labelKosten)
        
        self.layout.addWidget(self.labelName)
        self.layout.addLayout(h_layout)
        self.layout.addWidget(self.plainText)

        # Würfelbereich
        roll_box = QtWidgets.QGroupBox("Würfel")
        roll_layout = QtWidgets.QHBoxLayout(roll_box)
        self.roll_edit = QtWidgets.QLineEdit()
        self.roll_edit.setPlaceholderText("z.B. 1W6+2")
        self.roll_btn = QtWidgets.QPushButton("Würfeln")
        self.roll_result_label = QtWidgets.QLabel("")
        self.roll_result_label.setWordWrap(True)
        roll_layout.addWidget(self.roll_edit)
        roll_layout.addWidget(self.roll_btn)
        self.layout.addWidget(roll_box)
        self.layout.addWidget(self.roll_result_label)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        self.layout.addWidget(self.buttonBox)

        self.buttonBox.rejected.connect(self.close)
        self.buttonBox.accepted.connect(self.close)
        self.roll_btn.clicked.connect(self.trigger_roll)
        self.roll_edit.returnPressed.connect(self.trigger_roll)

        self.setMinimumSize(450, 450)
        self.load_talent(talent_name)

    def load_talent(self, talent_name):
        if not hasattr(Wolke, "DB") or talent_name not in Wolke.DB.talente:
            self.labelName.setText(talent_name or "—")
            self.labelTyp.setText("")
            self.labelKosten.setText("")
            self.plainText.setText("Talent nicht in der Datenbank gefunden.")
            return

        talent = Wolke.DB.talente[talent_name]
        anzeigename = getattr(talent, "anzeigename", None) or talent_name
        if getattr(talent, "verbilligt", False):
            anzeigename += " (verbilligt)"
        self.labelName.setText(anzeigename)

        try:
            kategorie = talent.kategorieName(Wolke.DB) if hasattr(talent, "kategorieName") else ""
        except Exception:
            kategorie = ""
        self.labelTyp.setText(kategorie or "")

        kosten_str = "—"
        if talent.kosten != -1:
            kosten_str = f"{talent.kosten} EP"
        if talent.variableKosten:
            kosten_str = f"Ab {talent.kosten} EP"
        self.labelKosten.setText(f"Kosten: {kosten_str}")

        beschreibung = talent.text
        if talent.info:
            beschreibung += f"\n\n<b>Sephrasto-Hinweis:</b> {talent.info}"
        
        self.plainText.setText(Hilfsmethoden.fixHtml(beschreibung))
        
        # Automatische Anpassung der Höhe an den Inhalt
        self.adjust_size_to_content()

    def adjust_size_to_content(self):
        # Dokument neu berechnen lassen
        self.plainText.document().adjustSize()
        doc_height = self.plainText.document().size().height()
        
        # Puffer für Header, Buttons und Roll-Box berechnen
        # Ca. 220px Overhead für die anderen UI Elemente
        ui_overhead = 220
        new_height = int(doc_height + ui_overhead)
        
        # Bildschirmhöhe ermitteln um nicht größer als der Screen zu werden
        screen_height = QtGui.QGuiApplication.primaryScreen().availableGeometry().height()
        max_height = int(screen_height * 0.85)
        
        # Finalen Wert zwischen Min (450) und Max begrenzen
        final_height = max(450, min(new_height, max_height))
        
        self.resize(self.width() or 500, final_height)

    def trigger_roll(self):
        expr = self.roll_edit.text()
        if expr:
            total, html_res = parse_and_roll_dice_string(expr)
            self.roll_result_label.setText(html_res)
