# dice_plugin/MasterPluginWrapper.py
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import (Qt, Signal, QSize, QEvent, QObject)
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, 
    QTabWidget, QPushButton, QLabel, QCheckBox, QSpinBox, QSizePolicy, QAbstractSpinBox,
    QPlainTextEdit, QListWidget, QListWidgetItem, QStackedWidget, QLineEdit,
    QSplitter, QScrollArea, QToolButton, QInputDialog, QFrame, QRadioButton, QComboBox, 
    QDialog, QDialogButtonBox, QFormLayout, QTextBrowser, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QAbstractItemView, QMenu, QMessageBox, QFrame, QApplication, QButtonGroup)
from PySide6.QtGui import QFont, QCursor


class _NoWheelFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and isinstance(obj, (QAbstractSpinBox, QComboBox)):
            return True
        return False


def _install_no_wheel_globally():
    app = QApplication.instance()
    if app is None or getattr(app, "_ilaris_no_wheel_installed", False):
        return
    app.installEventFilter(_NoWheelFilter(app))
    app._ilaris_no_wheel_installed = True

from Wolke import Wolke
from functools import partial
import random
import re
import json
import os
import copy
from Hilfsmethoden import Hilfsmethoden, SortedCategoryToListDict
from EffectsHelper import (
    EFFECT_PRESETS, blank_effect, from_preset, normalize_effect, normalize_list,
    sum_mods, effect_summary_line, tick_effects, tick_effects_on_at, tick_effects_on_tp,
    collect_tp_dice_effects, parse_tp_dice_string, make_atemtechnik_effect,
    make_volle_offensive_effect, make_volle_defensive_effect, is_volle_kampfhaltung,
    make_handlungsunfaehig_effect, make_blutend_effect, has_blocking_probe_effect,
    has_blocking_at_effect,
    _has_named_vorteil,
    register_custom_preset, delete_custom_preset, load_custom_presets, dump_custom_presets,
    CUSTOM_EFFECT_PRESETS, load_custom_presets_from_file, save_custom_presets_to_file,
    format_die_html, format_w20_list, format_roll_info_1w20, format_roll_info_3w20,
    colorize_dice_in_text, triumph_patzer_message,
    apply_wounds_batch, check_premature_timers, check_condition_info,
    concentration_ready_text, new_id,
    collect_player_probe_entries, collect_nsc_probe_entries, resolve_probe_pw,
    einschraenkung_malus, count_einschraenkungen,
    is_legacy_blutend_event, blutend_probe_overlay,
    MANOEVER, manöver_label, manöver_available, manöver_tp_hinweis, roll_gegenprobe,
    riposte_combinable_manöver, MUTUALLY_EXCLUSIVE_MANOEVER,
    combat_mod_from_combo,
    NK_MOD_POSITION, NK_MOD_REICHWEITE, NK_MOD_UNTERGRUND, NK_MOD_DUNKELHEIT, NK_MOD_CHECKS,
    FK_MOD_GROESSE, FK_MOD_LICHT, FK_MOD_WIND, FK_MOD_BEWEGUNG, FK_MOD_DECKUNG, FK_MOD_CHECKS,
)

# Import des Info-Dialogs
try:
    from TalentInfoDialog import TalentInfoDialog
except ImportError:
    TalentInfoDialog = None
try:
    from AmmoHelper import (
        blank_ammo, normalize_ammo_list, ammo_has_eigenschaft,
        selected_ammo, set_selected_ammo, consume_selected_ammo, AmmoEditDialog,
        ensure_selected_ammo,
    )
except ImportError:
    blank_ammo = None
    normalize_ammo_list = lambda x: list(x or [])
    ammo_has_eigenschaft = lambda a, p: False
    selected_ammo = lambda items: None
    set_selected_ammo = lambda items, i: list(items or [])
    consume_selected_ammo = lambda items: (list(items or []), None)
    AmmoEditDialog = None
    ensure_selected_ammo = lambda items: list(items or [])

# --- Globale Helper-Funktion für Würfelwürfe ---
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
            colored = ", ".join(format_die_html(r, sides) for r in current_rolls)
            roll_str = f"{num_dice}W{sides} ({colored})"
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

# --- Dialoge (Talent, Waffe, Info, INI) ---

# Reihenfolge / Anzeige-Namen für übernatürliche Fertigkeits-Kategorien
_UEBER_KAT_ORDER = [
    "Allgemeine Zauber",
    "Traditionszauber",
    "Allgemeine Liturgien",
    "Traditionsliturgien",
    "Anrufungen",
]


class TalentSelector(QDialog):
    """Übernatürliche Talente auswählen – Suche nach Name oder Fertigkeit, Filter nach Kategorie, Infobereich."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Übernatürliches Talent auswählen")
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout(self)

        # Kategorie-Filter
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Kategorie:"))
        self.kat_combo = QComboBox()
        self.kat_combo.addItem("Alle", userData=None)
        for k in _UEBER_KAT_ORDER:
            self.kat_combo.addItem(k, userData=k)
        self.kat_combo.currentIndexChanged.connect(self.update_filter)
        filter_row.addWidget(self.kat_combo, 1)
        layout.addLayout(filter_row)

        # Textsuche: Name oder Fertigkeit
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Suchen: Talentname oder Fertigkeit (z. B. Einfluss)…")
        self.filter_edit.textChanged.connect(self.update_filter)
        layout.addWidget(self.filter_edit)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Talent", "Fertigkeiten"])
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.tree.currentItemChanged.connect(self._on_selection_changed)
        left_l.addWidget(self.tree)
        self.count_label = QLabel("")
        left_l.addWidget(self.count_label)
        splitter.addWidget(left)

        self.info_browser = QTextBrowser()
        self.info_browser.setOpenExternalLinks(True)
        self.info_browser.setMinimumWidth(280)
        splitter.addWidget(self.info_browser)
        splitter.setSizes([520, 360])
        layout.addWidget(splitter)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Einträge: {name, ferts: [str], kategorie: str, ferts_str: str}
        self.talents = []
        self.populate_talents()
        self.update_filter()

    def _resolve_ueber_kat_names(self):
        """Map index/key → Anzeigename aus den DB-Einstellungen."""
        ordered = list(_UEBER_KAT_ORDER)
        try:
            cats = Wolke.DB.einstellungen["Fertigkeiten: Kategorien übernatürlich"].wert
            if isinstance(cats, dict) and cats:
                ordered = sorted(
                    cats.keys(),
                    key=lambda k: int(cats[k]) if str(cats[k]).isdigit() else str(cats[k]),
                )
        except Exception:
            pass
        return ordered

    def _skill_to_kategorie(self, skill_name, ordered_kats, skill_kat_map):
        """Kategorie-Name einer übernatürlichen Fertigkeit."""
        if skill_name in skill_kat_map:
            return skill_kat_map[skill_name]
        return None

    def populate_talents(self):
        ordered_kats = self._resolve_ueber_kat_names()
        skill_kat_map = {}  # fert_name → kategorie-name
        supernatural_skills = set()

        try:
            if hasattr(Wolke.DB, "übernatürlicheFertigkeiten"):
                for f_name, f_def in Wolke.DB.übernatürlicheFertigkeiten.items():
                    supernatural_skills.add(f_name)
                    kat_id = getattr(f_def, "kategorie", None)
                    name = None
                    if kat_id is not None and str(kat_id).isdigit():
                        idx = int(kat_id)
                        if 0 <= idx < len(ordered_kats):
                            name = ordered_kats[idx]
                    elif kat_id in ordered_kats:
                        name = kat_id
                    elif str(kat_id) in ordered_kats:
                        name = str(kat_id)
                    skill_kat_map[f_name] = name or "Sonstige"
        except Exception:
            pass

        # Fallback: aus profanen Fertigkeiten mit übernatürlicher Kategorie
        try:
            if "Fertigkeiten: Kategorien übernatürlich" in Wolke.DB.einstellungen:
                ueber_cats = Wolke.DB.einstellungen["Fertigkeiten: Kategorien übernatürlich"].wert
                for f_name, f_def in Wolke.DB.fertigkeiten.items():
                    if f_name in skill_kat_map:
                        continue
                    kat = getattr(f_def, "kategorie", None)
                    if kat in ueber_cats or (isinstance(ueber_cats, dict) and str(kat) in ueber_cats):
                        supernatural_skills.add(f_name)
                        if isinstance(ueber_cats, dict):
                            # kat kann Index oder Name sein
                            if str(kat).isdigit():
                                idx = int(kat)
                                keys = sorted(
                                    ueber_cats.keys(),
                                    key=lambda k: int(ueber_cats[k]) if str(ueber_cats[k]).isdigit() else str(ueber_cats[k]),
                                )
                                skill_kat_map[f_name] = keys[idx] if 0 <= idx < len(keys) else str(kat)
                            else:
                                skill_kat_map[f_name] = str(kat)
                        else:
                            skill_kat_map[f_name] = str(kat)
        except Exception:
            pass

        self.talents = []
        try:
            for t_name, t_def in Wolke.DB.talente.items():
                if not getattr(t_def, "spezialTalent", False):
                    continue
                ferts_raw = getattr(t_def, "fertigkeiten", None) or []
                if isinstance(ferts_raw, str):
                    ferts = [f.strip() for f in ferts_raw.split(",") if f.strip()]
                else:
                    ferts = list(ferts_raw)
                linked = [f for f in ferts if f in supernatural_skills]
                if not linked:
                    continue
                # Primärkategorie: niedrigster Index unter den verknüpften Fertigkeiten
                kat_name = "Sonstige"
                best_idx = 999
                for f in linked:
                    kn = skill_kat_map.get(f)
                    if not kn:
                        continue
                    try:
                        idx = ordered_kats.index(kn)
                    except ValueError:
                        idx = 500
                    if idx < best_idx:
                        best_idx = idx
                        kat_name = kn
                self.talents.append({
                    "name": t_name,
                    "ferts": linked,
                    "ferts_all": ferts,
                    "kategorie": kat_name,
                    "ferts_str": ", ".join(linked),
                })
        except Exception:
            pass

        self.talents.sort(key=lambda t: (t["kategorie"], t["name"].lower()))

    def update_filter(self):
        filter_text = (self.filter_edit.text() or "").strip().lower()
        kat_filter = self.kat_combo.currentData()

        self.tree.clear()
        font_header = QFont()
        font_header.setBold(True)
        font_header.setCapitalization(QFont.Capitalization.SmallCaps)

        # Gruppieren
        by_kat = {k: [] for k in _UEBER_KAT_ORDER}
        by_kat["Sonstige"] = []
        for t in self.talents:
            if kat_filter and t["kategorie"] != kat_filter:
                continue
            if filter_text:
                in_name = filter_text in t["name"].lower()
                in_fert = any(filter_text in f.lower() for f in t["ferts"])
                in_fert_all = any(filter_text in f.lower() for f in t.get("ferts_all", []))
                if not (in_name or in_fert or in_fert_all):
                    continue
            key = t["kategorie"] if t["kategorie"] in by_kat else "Sonstige"
            by_kat[key].append(t)

        shown = 0
        order = list(_UEBER_KAT_ORDER) + (["Sonstige"] if by_kat.get("Sonstige") else [])
        for kat_name in order:
            entries = by_kat.get(kat_name) or []
            if not entries:
                continue
            parent = QTreeWidgetItem(self.tree, [kat_name, ""])
            parent.setFont(0, font_header)
            parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            for t in entries:
                child = QTreeWidgetItem(parent, [t["name"], t["ferts_str"]])
                child.setData(0, Qt.ItemDataRole.UserRole, t["name"])
                shown += 1
            parent.setExpanded(True)

        self.count_label.setText(f"{shown} Talent(e)")

    def _on_double_click(self, item, column):
        if item and item.data(0, Qt.ItemDataRole.UserRole):
            self.accept()

    def _on_selection_changed(self, current, previous):
        name = current.data(0, Qt.ItemDataRole.UserRole) if current else None
        self._show_talent_info(name)

    def _show_talent_info(self, name):
        if not name or not hasattr(Wolke, "DB") or name not in Wolke.DB.talente:
            self.info_browser.setHtml("<p style='color:#888;'>Talent auswählen…</p>")
            return
        t = Wolke.DB.talente[name]
        anzeigename = getattr(t, "anzeigename", None) or name
        if getattr(t, "verbilligt", False):
            anzeigename += " (verbilligt)"
        try:
            kategorie = t.kategorieName(Wolke.DB) if hasattr(t, "kategorieName") else ""
        except Exception:
            kategorie = ""
        kosten = getattr(t, "kosten", -1)
        if kosten == -1:
            kosten_str = "—"
        elif getattr(t, "variableKosten", False):
            kosten_str = f"Ab {kosten} EP"
        else:
            kosten_str = f"{kosten} EP"
        ferts = getattr(t, "fertigkeiten", None) or []
        if isinstance(ferts, str):
            ferts_str = ferts
        else:
            ferts_str = ", ".join(ferts)
        text = getattr(t, "text", "") or ""
        info = getattr(t, "info", "") or ""
        try:
            body = Hilfsmethoden.fixHtml(text)
        except Exception:
            body = text
        if info:
            try:
                body += f"<br/><br/><b>Sephrasto-Hinweis:</b> {Hilfsmethoden.fixHtml(info)}"
            except Exception:
                body += f"<br/><br/><b>Sephrasto-Hinweis:</b> {info}"
        html = (
            f"<h2 style='margin-top:0'>{anzeigename}</h2>"
            f"<p style='margin:2px 0;color:#555'>{kategorie}</p>"
            f"<p style='margin:2px 0'><b>Kosten:</b> {kosten_str}<br/>"
            f"<b>Fertigkeiten:</b> {ferts_str or '—'}</p>"
            f"<hr/>{body}"
        )
        self.info_browser.setHtml(html)

    def get_selected_talent(self):
        item = self.tree.currentItem()
        if not item:
            return None
        return item.data(0, Qt.ItemDataRole.UserRole) or None



def _db_weapon_is_fk(w) -> bool:
    """fk aus datenbank.xml (fk=0/1) hat Vorrang vor .fernkampf."""
    if w is None:
        return False
    val = getattr(w, "fk", None)
    if val is None:
        val = getattr(w, "fernkampf", None)
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return int(val) != 0
    s = str(val).strip().lower()
    if s in ("", "0", "false", "nein", "no", "nk", "nahkampf"):
        return False
    return s in ("1", "true", "ja", "yes", "fk", "fernkampf")


class WeaponSelector(QDialog):
    """Waffe auswählen – gruppiert nach Fertigkeit, Infobereich wie in Sephrasto."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Waffe auswählen")
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout(self)

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Suchen: Name, Talent oder Fertigkeit…")
        self.filter_edit.textChanged.connect(self.update_filter)
        layout.addWidget(self.filter_edit)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Talent"])
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.tree.currentItemChanged.connect(self._on_selection_changed)
        left_l.addWidget(self.tree)
        self.count_label = QLabel("")
        left_l.addWidget(self.count_label)
        splitter.addWidget(left)

        self.info_browser = QTextBrowser()
        self.info_browser.setOpenExternalLinks(True)
        self.info_browser.setMinimumWidth(280)
        splitter.addWidget(self.info_browser)
        splitter.setSizes([520, 360])
        layout.addWidget(splitter)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # {name, display, fertigkeit, talent, is_fk}
        self.weapons = []
        self.populate_weapons()
        self.update_filter()

    def populate_weapons(self):
        self.weapons = []
        try:
            for name, w in Wolke.DB.waffen.items():
                display = getattr(w, "anzeigename", None) or name
                fert = getattr(w, "fertigkeit", "") or "Sonstige"
                talent = getattr(w, "talent", "") or ""
                is_fk = _db_weapon_is_fk(w)
                self.weapons.append({
                    "name": name,
                    "display": display,
                    "fertigkeit": fert,
                    "talent": talent,
                    "is_fk": is_fk,
                })
        except Exception:
            pass
        self.weapons.sort(key=lambda x: (x["fertigkeit"].lower(), x["display"].lower()))

    def update_filter(self):
        ft = (self.filter_edit.text() or "").strip().lower()
        self.tree.clear()
        font_header = QFont()
        font_header.setBold(True)
        font_header.setCapitalization(QFont.Capitalization.SmallCaps)

        by_fert = {}
        for w in self.weapons:
            if ft:
                if not (
                    ft in w["name"].lower()
                    or ft in w["display"].lower()
                    or ft in (w["talent"] or "").lower()
                    or ft in (w["fertigkeit"] or "").lower()
                ):
                    continue
            by_fert.setdefault(w["fertigkeit"] or "Sonstige", []).append(w)

        shown = 0
        for fert in sorted(by_fert.keys(), key=lambda s: s.lower()):
            parent = QTreeWidgetItem(self.tree, [fert.upper(), ""])
            parent.setFont(0, font_header)
            parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            for w in by_fert[fert]:
                child = QTreeWidgetItem(parent, [w["display"], w["talent"]])
                child.setData(0, Qt.ItemDataRole.UserRole, w["name"])
                shown += 1
            parent.setExpanded(True)

        self.count_label.setText(f"{shown} Waffe(n)")
        self._show_weapon_info(None)

    def _on_double_click(self, item, column):
        if item and item.data(0, Qt.ItemDataRole.UserRole):
            self.accept()

    def _on_selection_changed(self, current, previous):
        name = current.data(0, Qt.ItemDataRole.UserRole) if current else None
        self._show_weapon_info(name)

    def _show_weapon_info(self, name):
        if not name or not hasattr(Wolke, "DB") or name not in Wolke.DB.waffen:
            self.info_browser.setHtml("<p style='color:#888;'>Waffe auswählen…</p>")
            return
        w = Wolke.DB.waffen[name]
        display = getattr(w, "anzeigename", None) or name
        fert = getattr(w, "fertigkeit", "") or "—"
        talent = getattr(w, "talent", "") or "—"
        is_fk = _db_weapon_is_fk(w)
        typ = "Fernkampfwaffe" if is_fk else "Nahkampfwaffe"

        würfel = getattr(w, "würfel", 0) or 0
        seiten = getattr(w, "würfelSeiten", 6) or 6
        plus = getattr(w, "plus", 0) or 0
        tp = f"{würfel}W{seiten}"
        if plus > 0:
            tp += f"+{plus}"
        elif plus < 0:
            tp += str(plus)

        rw = getattr(w, "rw", 0)
        wm = getattr(w, "wm", 0)
        wm_str = f"+{wm}" if isinstance(wm, int) and wm >= 0 else str(wm)
        haerte = getattr(w, "härte", getattr(w, "haerte", "—"))
        eig = getattr(w, "eigenschaften", None) or []
        if isinstance(eig, str):
            eig_str = eig
        else:
            eig_str = ", ".join(eig) if eig else "keine"
        stile = getattr(w, "kampfstile", "") or ""
        if isinstance(stile, (list, tuple)):
            stile = ", ".join(stile)

        rows = [
            f"<tr><td style='padding:2px 12px 2px 0;color:#555'>Fertigkeit:</td><td style='text-align:right'>{fert}</td></tr>",
            f"<tr><td style='padding:2px 12px 2px 0;color:#555'>Talent:</td><td style='text-align:right'>{talent}</td></tr>",
        ]
        if stile:
            rows.append(
                f"<tr><td style='padding:2px 12px 2px 0;color:#555;vertical-align:top'>Kampfstile:</td>"
                f"<td style='text-align:right'>{stile}</td></tr>"
            )
        rows.append("<tr><td colspan='2'><hr/></td></tr>")
        rows.append(
            f"<tr><td style='padding:2px 12px 2px 0;color:#555'>Trefferpunkte:</td>"
            f"<td style='text-align:right'>{tp}</td></tr>"
        )
        rows.append(
            f"<tr><td style='padding:2px 12px 2px 0;color:#555'>Reichweite:</td>"
            f"<td style='text-align:right'>{rw}</td></tr>"
        )
        rows.append(
            f"<tr><td style='padding:2px 12px 2px 0;color:#555'>Waffenmodifikator:</td>"
            f"<td style='text-align:right'>{wm_str}</td></tr>"
        )
        rows.append(
            f"<tr><td style='padding:2px 12px 2px 0;color:#555'>Härte:</td>"
            f"<td style='text-align:right'>{haerte}</td></tr>"
        )
        if is_fk and hasattr(w, "lz"):
            rows.append(
                f"<tr><td style='padding:2px 12px 2px 0;color:#555'>Ladezeit:</td>"
                f"<td style='text-align:right'>{w.lz}</td></tr>"
            )
        rows.append(
            f"<tr><td style='padding:2px 12px 2px 0;color:#555'>Eigenschaften:</td>"
            f"<td style='text-align:right'>{eig_str}</td></tr>"
        )

        html = (
            f"<h2 style='margin:0 0 4px 0'>{display}</h2>"
            f"<p style='margin:0 0 8px 0;color:#666'><i>{typ}</i></p>"
            f"<table width='100%' cellspacing='0'>{''.join(rows)}</table>"
        )
        self.info_browser.setHtml(html)

    def get_selected_weapon(self):
        item = self.tree.currentItem()
        if not item:
            return None
        return item.data(0, Qt.ItemDataRole.UserRole) or None

class VorteilSelector(QDialog):
    """Vorteile auswählen – Kategorie-Filter, Suche, Tree + Infobereich (wie Waffen/Übernatürliches)."""

    def __init__(self, parent=None, already=None):
        super().__init__(parent)
        self.setWindowTitle("Vorteil auswählen")
        self.setMinimumSize(900, 600)
        self.already = set(already or [])
        self.entries = []  # {name, kategorie, text, kosten, voraussetzungen}

        layout = QVBoxLayout(self)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Kategorie:"))
        self.kat_combo = QComboBox()
        self.kat_combo.addItem("Alle", userData=None)
        self.kat_combo.currentIndexChanged.connect(self.update_filter)
        filter_row.addWidget(self.kat_combo, 1)
        layout.addLayout(filter_row)

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Suchen: Name, Kategorie oder Text…")
        self.filter_edit.textChanged.connect(self.update_filter)
        layout.addWidget(self.filter_edit)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Vorteil", "Kosten"])
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.tree.currentItemChanged.connect(self._on_selection_changed)
        left_l.addWidget(self.tree)
        self.count_label = QLabel("")
        left_l.addWidget(self.count_label)
        splitter.addWidget(left)

        self.info_browser = QTextBrowser()
        self.info_browser.setOpenExternalLinks(False)
        self.info_browser.setMinimumWidth(280)
        splitter.addWidget(self.info_browser)
        splitter.setSizes([520, 360])
        layout.addWidget(splitter)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.populate()
        self.update_filter()

    def _kat_name(self, vdef):
        try:
            if hasattr(vdef, "kategorieName"):
                return str(vdef.kategorieName(Wolke.DB) or "") or "Sonstige"
        except Exception:
            pass
        return str(getattr(vdef, "kategorie", "") or "Sonstige")

    def _vorteil_text(self, vdef):
        for attr in ("text", "beschreibung", "csBeschreibung"):
            t = getattr(vdef, attr, None)
            if t:
                return str(t)
        return ""

    def populate(self):
        self.entries = []
        kats = set()
        try:
            for name, vdef in (Wolke.DB.vorteile or {}).items():
                if name in self.already:
                    continue
                kat = self._kat_name(vdef)
                kats.add(kat)
                kosten = getattr(vdef, "kosten", None)
                if kosten is None:
                    kosten = getattr(vdef, "kostenPrint", "") or ""
                vor = getattr(vdef, "voraussetzungen", None) or getattr(vdef, "voraussetzungenStr", "") or ""
                if not isinstance(vor, str):
                    try:
                        vor = str(vor)
                    except Exception:
                        vor = ""
                self.entries.append({
                    "name": name,
                    "kategorie": kat,
                    "text": self._vorteil_text(vdef),
                    "kosten": kosten,
                    "voraussetzungen": vor,
                })
        except Exception:
            pass
        self.entries.sort(key=lambda e: (e["kategorie"].lower(), e["name"].lower()))

        # Kategorie-Combo füllen (Reihenfolge aus DB wenn möglich)
        ordered = []
        try:
            cats = Wolke.DB.einstellungen["Vorteile: Kategorien"].wert
            if isinstance(cats, dict) and cats:
                ordered = sorted(
                    cats.keys(),
                    key=lambda k: int(cats[k]) if str(cats[k]).isdigit() else str(cats[k]),
                )
        except Exception:
            pass
        if not ordered:
            ordered = sorted(kats, key=lambda s: s.lower())
        self.kat_combo.blockSignals(True)
        while self.kat_combo.count() > 1:
            self.kat_combo.removeItem(1)
        for k in ordered:
            if k in kats or True:
                self.kat_combo.addItem(k, userData=k)
        self.kat_combo.blockSignals(False)

    def update_filter(self):
        ft = (self.filter_edit.text() or "").strip().lower()
        kat_filter = self.kat_combo.currentData()
        self.tree.clear()
        font_header = QFont()
        font_header.setBold(True)
        font_header.setCapitalization(QFont.Capitalization.SmallCaps)

        by_kat = {}
        for e in self.entries:
            if kat_filter and e["kategorie"] != kat_filter:
                continue
            if ft:
                blob = " ".join([
                    e["name"], e["kategorie"], e.get("text") or "",
                    str(e.get("voraussetzungen") or ""),
                ]).lower()
                if ft not in blob:
                    continue
            by_kat.setdefault(e["kategorie"] or "Sonstige", []).append(e)

        shown = 0
        for kat in sorted(by_kat.keys(), key=lambda s: s.lower()):
            parent = QTreeWidgetItem(self.tree, [kat.upper(), ""])
            parent.setFont(0, font_header)
            parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            for e in by_kat[kat]:
                kosten_s = str(e["kosten"]) if e["kosten"] not in (None, "") else ""
                child = QTreeWidgetItem(parent, [e["name"], kosten_s])
                child.setData(0, Qt.ItemDataRole.UserRole, e["name"])
                shown += 1
            parent.setExpanded(bool(ft) or bool(kat_filter))
        if not ft and not kat_filter:
            # erste Kategorie aufgeklappt
            if self.tree.topLevelItemCount():
                self.tree.topLevelItem(0).setExpanded(True)
        self.count_label.setText(f"{shown} Vorteil(e)")

    def _on_double_click(self, item, _col):
        if item and item.data(0, Qt.ItemDataRole.UserRole):
            self.accept()

    def _on_selection_changed(self, current, _prev):
        if not current:
            self.info_browser.clear()
            return
        name = current.data(0, Qt.ItemDataRole.UserRole)
        if not name:
            self.info_browser.clear()
            return
        e = next((x for x in self.entries if x["name"] == name), None)
        if not e:
            self.info_browser.clear()
            return
        kosten = e["kosten"]
        kosten_s = str(kosten) if kosten not in (None, "") else "—"
        vor = e.get("voraussetzungen") or "—"
        text = (e.get("text") or "").replace("\n", "<br>")
        self.info_browser.setHtml(
            f"<h3>{e['name']}</h3>"
            f"<p><b>Kategorie:</b> {e['kategorie']}<br>"
            f"<b>Kosten:</b> {kosten_s}<br>"
            f"<b>Voraussetzungen:</b> {vor}</p>"
            f"<hr/>{text or '<i>Keine Beschreibung</i>'}"
        )

    def get_selected(self):
        item = self.tree.currentItem()
        if not item:
            return None
        return item.data(0, Qt.ItemDataRole.UserRole)


class FertigkeitSelector(QDialog):
    """Profane Fertigkeiten auswählen – Kategorie-Filter, Suche, Tree + Infobereich."""

    def __init__(self, parent=None, already=None):
        super().__init__(parent)
        self.setWindowTitle("Fertigkeit auswählen")
        self.setMinimumSize(900, 600)
        self.already = set(already or [])
        self.entries = []

        layout = QVBoxLayout(self)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Kategorie:"))
        self.kat_combo = QComboBox()
        self.kat_combo.addItem("Alle", userData=None)
        self.kat_combo.currentIndexChanged.connect(self.update_filter)
        filter_row.addWidget(self.kat_combo, 1)
        layout.addLayout(filter_row)

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Suchen: Fertigkeitsname oder Kategorie…")
        self.filter_edit.textChanged.connect(self.update_filter)
        layout.addWidget(self.filter_edit)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Fertigkeit", "Attribute"])
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.tree.currentItemChanged.connect(self._on_selection_changed)
        left_l.addWidget(self.tree)
        self.count_label = QLabel("")
        left_l.addWidget(self.count_label)
        splitter.addWidget(left)

        self.info_browser = QTextBrowser()
        self.info_browser.setOpenExternalLinks(False)
        self.info_browser.setMinimumWidth(280)
        splitter.addWidget(self.info_browser)
        splitter.setSizes([520, 360])
        layout.addWidget(splitter)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.populate()
        self.update_filter()

    def _skill_kat(self, fdef, ordered_kats):
        try:
            if hasattr(fdef, "kategorieName"):
                return str(fdef.kategorieName(Wolke.DB) or "") or "Sonstige"
        except Exception:
            pass
        kat = getattr(fdef, "kategorie", None)
        if isinstance(kat, int) and ordered_kats and 0 <= kat < len(ordered_kats):
            return ordered_kats[kat]
        return str(kat or "Sonstige")

    def populate(self):
        self.entries = []
        ordered = []
        try:
            cats = Wolke.DB.einstellungen["Fertigkeiten: Kategorien profan"].wert
            if isinstance(cats, dict) and cats:
                ordered = sorted(
                    cats.keys(),
                    key=lambda k: int(cats[k]) if str(cats[k]).isdigit() else str(cats[k]),
                )
        except Exception:
            ordered = []

        kats = set()
        try:
            for name, fdef in (Wolke.DB.fertigkeiten or {}).items():
                if name in self.already:
                    continue
                kat = self._skill_kat(fdef, ordered)
                kats.add(kat)
                attrs = getattr(fdef, "attribute", None) or getattr(fdef, "voraussetzungen", "") or ""
                if isinstance(attrs, (list, tuple)):
                    attrs = ", ".join(str(a) for a in attrs)
                steigerung = getattr(fdef, "steigerungsfaktor", None)
                if steigerung is None:
                    steigerung = getattr(fdef, "sf", "")
                text = getattr(fdef, "text", None) or getattr(fdef, "beschreibung", "") or ""
                self.entries.append({
                    "name": name,
                    "kategorie": kat,
                    "attribute": str(attrs or ""),
                    "steigerung": steigerung,
                    "text": str(text or ""),
                })
        except Exception:
            pass
        self.entries.sort(key=lambda e: (e["kategorie"].lower(), e["name"].lower()))

        self.kat_combo.blockSignals(True)
        while self.kat_combo.count() > 1:
            self.kat_combo.removeItem(1)
        for k in (ordered or sorted(kats, key=lambda s: s.lower())):
            self.kat_combo.addItem(k, userData=k)
        self.kat_combo.blockSignals(False)

    def update_filter(self):
        ft = (self.filter_edit.text() or "").strip().lower()
        kat_filter = self.kat_combo.currentData()
        self.tree.clear()
        font_header = QFont()
        font_header.setBold(True)
        font_header.setCapitalization(QFont.Capitalization.SmallCaps)

        by_kat = {}
        for e in self.entries:
            if kat_filter and e["kategorie"] != kat_filter:
                continue
            if ft:
                blob = " ".join([e["name"], e["kategorie"], e.get("attribute") or ""]).lower()
                if ft not in blob:
                    continue
            by_kat.setdefault(e["kategorie"] or "Sonstige", []).append(e)

        shown = 0
        for kat in sorted(by_kat.keys(), key=lambda s: s.lower()):
            parent = QTreeWidgetItem(self.tree, [kat.upper(), ""])
            parent.setFont(0, font_header)
            parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            for e in by_kat[kat]:
                child = QTreeWidgetItem(parent, [e["name"], e.get("attribute") or ""])
                child.setData(0, Qt.ItemDataRole.UserRole, e["name"])
                shown += 1
            parent.setExpanded(bool(ft) or bool(kat_filter))
        if not ft and not kat_filter and self.tree.topLevelItemCount():
            self.tree.topLevelItem(0).setExpanded(True)
        self.count_label.setText(f"{shown} Fertigkeit(en)")

    def _on_double_click(self, item, _col):
        if item and item.data(0, Qt.ItemDataRole.UserRole):
            self.accept()

    def _on_selection_changed(self, current, _prev):
        if not current:
            self.info_browser.clear()
            return
        name = current.data(0, Qt.ItemDataRole.UserRole)
        if not name:
            self.info_browser.clear()
            return
        e = next((x for x in self.entries if x["name"] == name), None)
        if not e:
            self.info_browser.clear()
            return
        sf = e.get("steigerung")
        sf_s = str(sf) if sf not in (None, "") else "—"
        text = (e.get("text") or "").replace("\n", "<br>")
        self.info_browser.setHtml(
            f"<h3>{e['name']}</h3>"
            f"<p><b>Kategorie:</b> {e['kategorie']}<br>"
            f"<b>Attribute:</b> {e.get('attribute') or '—'}<br>"
            f"<b>Steigerungsfaktor:</b> {sf_s}</p>"
            f"<hr/>{text or '<i>Keine Beschreibung</i>'}"
        )

    def get_selected(self):
        item = self.tree.currentItem()
        if not item:
            return None
        return item.data(0, Qt.ItemDataRole.UserRole)

class WeaponInfoDialog(QDialog):
    def __init__(self, weapon_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Info: {weapon_name}")
        self.setMinimumSize(400, 400)
        layout = QVBoxLayout(self)
        
        self.browser = QTextBrowser()
        layout.addWidget(self.browser)
        
        # --- Freies Würfeln Bereich ---
        roll_box = QGroupBox("Freies Würfeln")
        roll_layout = QVBoxLayout(roll_box)
        
        h_layout = QHBoxLayout()
        self.roll_edit = QLineEdit()
        self.roll_edit.setPlaceholderText("z.B. 2W6+4")
        self.roll_edit.returnPressed.connect(self.trigger_roll)
        
        self.roll_btn = QPushButton("🎲")
        self.roll_btn.setFixedWidth(30)
        self.roll_btn.clicked.connect(self.trigger_roll)
        
        h_layout.addWidget(self.roll_edit)
        h_layout.addWidget(self.roll_btn)
        
        self.roll_result_label = QLabel("")
        self.roll_result_label.setWordWrap(True)
        
        roll_layout.addLayout(h_layout)
        roll_layout.addWidget(self.roll_result_label)
        layout.addWidget(roll_box)
        # ----------------------------

        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
        self.load_data(weapon_name)
        
    def load_data(self, name):
        if name not in Wolke.DB.waffen:
            self.browser.setText("Keine Informationen in der Datenbank gefunden.")
            return
            
        w = Wolke.DB.waffen[name]
        
        tp = f"{w.würfel}W{w.würfelSeiten}"
        if w.plus > 0: tp += f"+{w.plus}"
        elif w.plus < 0: tp += f"{w.plus}"
        
        html = f"<h2>{w.anzeigename}</h2><p><b>TP:</b> {tp} &nbsp;&nbsp; <b>RW:</b> {w.rw} &nbsp;&nbsp; <b>WM:</b> {w.wm}</p>"
        
        if w.fernkampf:
             html += f"<p><b>Ladezeit:</b> {w.lz}</p>"
             
        if w.eigenschaften:
            html += f"<p><b>Eigenschaften:</b> {', '.join(w.eigenschaften)}</p>"
            
        self.browser.setHtml(html)

    def trigger_roll(self):
        expr = self.roll_edit.text()
        if expr:
            total, html_res = parse_and_roll_dice_string(expr)
            self.roll_result_label.setText(html_res)


class WeaponEigenschaftDialog(QDialog):
    """Waffeneigenschaften wählen – Liste links, Infotext rechts."""

    def __init__(self, current_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Waffeneigenschaften")
        self.setMinimumSize(720, 480)
        lay = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)
        hint = QLabel("Mehrfachauswahl. Klick zeigt Erklärung rechts.")
        hint.setStyleSheet("color:#555;")
        left_l.addWidget(hint)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        host = QWidget()
        self._grid = QVBoxLayout(host)
        self._grid.setContentsMargins(4, 4, 4, 4)
        self._grid.setSpacing(2)
        self._checks = []
        current = {x.strip().lower() for x in (current_text or "").split(",") if x.strip()}
        props = self._load_props()
        last_kat = None
        for p in props:
            kat = p.get("kategorie") or "standard"
            if kat != last_kat:
                title = "Standard (Regelwerk)" if kat == "standard" else "Kreatur"
                lab = QLabel(f"<b>{title}</b>")
                self._grid.addWidget(lab)
                last_kat = kat
            name = p.get("name") or p.get("id") or ""
            cb = QCheckBox(name)
            tip = p.get("tooltip") or ""
            cb.setProperty("tip_text", tip)
            cb.setProperty("prop_name", name)
            if name.lower() in current or (p.get("id") or "").lower() in current:
                cb.setChecked(True)
            cb.toggled.connect(lambda checked, c=cb: self._show_info(c))
            # auch bei Fokus/Klick auf Label-Bereich
            cb.clicked.connect(lambda checked=False, c=cb: self._show_info(c))
            self._grid.addWidget(cb)
            self._checks.append(cb)
        self._grid.addStretch()
        scroll.setWidget(host)
        left_l.addWidget(scroll)
        splitter.addWidget(left)

        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.addWidget(QLabel("<b>Erklärung</b>"))
        self.info = QTextBrowser()
        self.info.setOpenExternalLinks(False)
        self.info.setMinimumWidth(280)
        self.info.setHtml("<i>Eigenschaft anwählen, um den Text zu sehen.</i>")
        try:
            from PySide6.QtCore import Qt as _Qt
            self.info.setVerticalScrollBarPolicy(_Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.info.setHorizontalScrollBarPolicy(_Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        except Exception:
            pass
        right_l.addWidget(self.info, 1)
        splitter.addWidget(right)
        splitter.setSizes([360, 360])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        lay.addWidget(splitter)

        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        lay.addWidget(box)

    def _load_props(self):
        props = []
        try:
            from MonsterHelper import load_monster_katalog
            props = list(load_monster_katalog().get("waffeneigenschaften") or [])
        except Exception:
            props = []
        # NK/FK sind kein Katalog-Tag, sondern Waffentyp (fernkampf-Flag)
        props = [p for p in props if (p.get("id") or "").lower() not in ("nk", "fk")]
        if not props:
            # Minimal-Fallback
            props = [
                {"id": "kopflastig", "name": "Kopflastig", "kategorie": "standard",
                 "tooltip": "Schadensbonus durch hohe KK zählt doppelt."},
                {"id": "ruestungsbrechend", "name": "Rüstungsbrechend", "kategorie": "standard",
                 "tooltip": "Ermöglicht das Manöver Rüstungsbrecher."},
            ]
        return props

    def _show_info(self, cb):
        name = cb.property("prop_name") or cb.text()
        tip = cb.property("tip_text") or ""
        body = (tip or "Keine Beschreibung hinterlegt.").replace(chr(10), "<br>")
        self.info.setHtml(f"<h3>{name}</h3><p>{body}</p>")

    def selected_text(self):
        return ", ".join(cb.property("prop_name") or cb.text() for cb in self._checks if cb.isChecked())


class WeaponCustomInfoDialog(QDialog):
    """Info-Text einer Waffe anzeigen/bearbeiten (+ DB-Daten falls vorhanden)."""

    def __init__(self, weapon_name="", info_text="", eigenschaften="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Waffen-Info: {weapon_name or '—'}")
        self.setMinimumSize(480, 420)
        lay = QVBoxLayout(self)
        self.browser = QTextBrowser()
        lay.addWidget(self.browser, 1)
        lay.addWidget(QLabel("<b>Eigener Infotext</b> (legendäre Waffen, Sonderregeln …)"))
        self.edit = QTextEdit()
        self.edit.setPlainText(info_text or "")
        self.edit.setMinimumHeight(120)
        lay.addWidget(self.edit)
        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        lay.addWidget(box)
        self._fill(weapon_name, eigenschaften)

    def _fill(self, name, eigenschaften):
        html = f"<h2>{name or 'Waffe'}</h2>"
        try:
            if name and name in Wolke.DB.waffen:
                w = Wolke.DB.waffen[name]
                tp = f"{w.würfel}W{w.würfelSeiten}"
                if w.plus > 0:
                    tp += f"+{w.plus}"
                elif w.plus < 0:
                    tp += f"{w.plus}"
                html += f"<p><b>TP:</b> {tp} &nbsp; <b>RW:</b> {getattr(w, 'rw', '–')} &nbsp; <b>WM:</b> {getattr(w, 'wm', '–')}</p>"
                if getattr(w, "fernkampf", False):
                    html += f"<p><b>Ladezeit:</b> {getattr(w, 'lz', '–')}</p>"
                db_eig = getattr(w, "eigenschaften", None) or []
                if db_eig:
                    if isinstance(db_eig, (list, tuple)):
                        html += f"<p><b>DB-Eigenschaften:</b> {', '.join(str(x) for x in db_eig)}</p>"
                    else:
                        html += f"<p><b>DB-Eigenschaften:</b> {db_eig}</p>"
        except Exception:
            pass
        if eigenschaften:
            html += f"<p><b>Eigenschaften:</b> {eigenschaften}</p>"
            html += self._eig_detail_html(eigenschaften)
        self.browser.setHtml(html)

    def _eig_detail_html(self, eig_text):
        tips = {}
        try:
            from MonsterHelper import load_monster_katalog
            for p in load_monster_katalog().get("waffeneigenschaften") or []:
                tips[(p.get("name") or "").lower()] = p.get("tooltip") or ""
                tips[(p.get("id") or "").lower()] = p.get("tooltip") or ""
        except Exception:
            pass
        parts = []
        for raw in (eig_text or "").split(","):
            name = raw.strip()
            if not name:
                continue
            tip = tips.get(name.lower()) or ""
            tip_html = tip.replace("\n", "<br>") if tip else "<i>Keine Beschreibung</i>"
            parts.append(f"<p><b>{name}</b><br>{tip_html}</p>")
        return "".join(parts)

    def info_text(self):
        return self.edit.toPlainText().strip()


class IniSelectorDialog(QDialog):
    # Signal sendet die Daten des gewählten Charakters an das Hauptfenster
    entrySelected = Signal(object) 

    def __init__(self, sc_list, nsc_list, parent=None, monster_list=None):
        super().__init__(parent)
        self.setWindowTitle("Zum Kampf hinzufügen")
        self.setMinimumSize(350, 450)
        
        layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        # Doppelklick soll hinzufügen, aber nicht schließen
        self.list_widget.itemDoubleClicked.connect(self.trigger_add)
        layout.addWidget(self.list_widget)
        
        # --- Liste füllen ---
        sc_header = QListWidgetItem("--- SCs ---")
        sc_header.setFlags(Qt.ItemFlag.NoItemFlags)
        sc_header.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        sc_header.setBackground(QtGui.QColor(200, 200, 200, 50))
        self.list_widget.addItem(sc_header)
        
        for i, sc in enumerate(sc_list or []):
            item = QListWidgetItem(sc.get("name", "SC"))
            item.setData(Qt.UserRole, {"type": "sc", "index": i})
            self.list_widget.addItem(item)
            
        nsc_header = QListWidgetItem("--- NSCs ---")
        nsc_header.setFlags(Qt.ItemFlag.NoItemFlags)
        nsc_header.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        nsc_header.setBackground(QtGui.QColor(200, 200, 200, 50))
        self.list_widget.addItem(nsc_header)
        
        for i, nsc in enumerate(nsc_list or []):
            item = QListWidgetItem(nsc.get("name", "NSC"))
            item.setData(Qt.UserRole, {"type": "nsc", "index": i})
            self.list_widget.addItem(item)

        mon_header = QListWidgetItem("--- Monster ---")
        mon_header.setFlags(Qt.ItemFlag.NoItemFlags)
        mon_header.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        mon_header.setBackground(QtGui.QColor(200, 200, 200, 50))
        self.list_widget.addItem(mon_header)

        for i, mon in enumerate(monster_list or []):
            item = QListWidgetItem(mon.get("name", "Monster"))
            item.setData(Qt.UserRole, {"type": "monster", "index": i})
            self.list_widget.addItem(item)
        
        # --- Buttons ---
        button_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("Hinzufügen")
        self.btn_add.clicked.connect(self.trigger_add)
        
        self.btn_close = QPushButton("Schließen")
        self.btn_close.clicked.connect(self.reject) # reject schließt das Fenster
        
        button_layout.addWidget(self.btn_add)
        button_layout.addWidget(self.btn_close)
        
        layout.addLayout(button_layout)

    def trigger_add(self, item=None):
        # Wenn wir über den Button kommen, ist item None, wir nehmen das aktuelle
        if item is None or not isinstance(item, QListWidgetItem):
            item = self.list_widget.currentItem()
            
        if item:
            data = item.data(Qt.UserRole)
            if data:
                self.entrySelected.emit(data)
                # Optional: Auswahl aufheben als visuelles Feedback
                self.list_widget.clearSelection()

# --- Widgets für SC/NSC ---
class SCWidget(QWidget):
    rollRequested = Signal(object, str, int) 
    removeRequested = Signal()
    moveUpRequested = Signal()
    moveDownRequested = Signal()
    dataChanged = Signal() 

    def __init__(self, data_ref, show_ini_header=False):
        super().__init__()
        self.data = data_ref 
        self.show_ini_header = show_ini_header
        self.is_expanded = False
        # WICHTIG: isLoading verhindert Speichern beim Initialisieren
        self.isLoading = False 
        self._init_ui()
        self.load_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 5, 0, 5)
        main_layout.setSpacing(0)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        # --- Header ---
        self.header_frame = QFrame()
        self.header_frame.setObjectName("scHeader")
        
        self.header_frame.setStyleSheet("QFrame#scHeader { background-color: rgba(128, 128, 128, 30); border-radius: 4px; border: 1px solid rgba(128, 128, 128, 50); }")
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        move_layout = QVBoxLayout()
        move_layout.setSpacing(0); move_layout.setContentsMargins(0,0,0,0)
        self.btn_up = QToolButton(); self.btn_up.setArrowType(Qt.ArrowType.UpArrow); self.btn_up.setFixedSize(20, 15); self.btn_up.clicked.connect(self.moveUpRequested.emit)
        self.btn_down = QToolButton(); self.btn_down.setArrowType(Qt.ArrowType.DownArrow); self.btn_down.setFixedSize(20, 15); self.btn_down.clicked.connect(self.moveDownRequested.emit)
        move_layout.addWidget(self.btn_up); move_layout.addWidget(self.btn_down)
        header_layout.addLayout(move_layout); header_layout.addSpacing(5)

        self.btn_expand = QToolButton()
        self.btn_expand.setArrowType(Qt.ArrowType.RightArrow)
        self.btn_expand.clicked.connect(self.toggle_expand)
        header_layout.addWidget(self.btn_expand)
        
        # INI HEADER
        if self.show_ini_header:
            header_layout.addWidget(QLabel("INI:"))
            self.header_ini_spin = QSpinBox()
            self.header_ini_spin.setRange(-99, 999)
            self.header_ini_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            self.header_ini_spin.setFixedWidth(40)
            self.header_ini_spin.valueChanged.connect(self.on_header_ini_changed)
            header_layout.addWidget(self.header_ini_spin)
            header_layout.addSpacing(5)
            
            self.btn_ko = QPushButton("☠")
            self.btn_ko.setFixedSize(25, 25)
            self.btn_ko.setCheckable(True)
            self.btn_ko.setToolTip("Kampfunfähig (wird übersprungen)")
            self.btn_ko.clicked.connect(self.on_ko_toggled)
            header_layout.addWidget(self.btn_ko)
            header_layout.addSpacing(5)

            # Reaktionszähler: 1. Reaktion 0, jede weitere –4 VT (kumulativ)
            header_layout.addWidget(QLabel("Reakt.:"))
            self.reaktion_spin = QSpinBox()
            self.reaktion_spin.setRange(0, 20)
            self.reaktion_spin.setValue(0)
            self.reaktion_spin.setFixedWidth(42)
            self.reaktion_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
            self.reaktion_spin.setToolTip(
                "Reaktionen seit eigener INI-Phase.\n"
                "1. Reaktion: kein Malus, 2.: –4, 3.: –8, …\n"
                "Reset bei „Nächste INI“, wenn dieser Charakter dran ist."
            )
            self.reaktion_spin.valueChanged.connect(self.on_reaktion_changed)
            header_layout.addWidget(self.reaktion_spin)
            self.reaktion_malus_label = QLabel("VT ±0")
            self.reaktion_malus_label.setStyleSheet("color: #666; min-width: 42px;")
            header_layout.addWidget(self.reaktion_malus_label)
            header_layout.addSpacing(5)
        else:
            self.reaktion_spin = None
            self.reaktion_malus_label = None

        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("Name des SC")
        self.edit_name.textChanged.connect(lambda: self.changed())
        header_layout.addWidget(self.edit_name, 1) 
        
        self.btn_remove = QPushButton("X")
        self.btn_remove.setFixedSize(25, 25)
        self.btn_remove.setStyleSheet("color: red; font-weight: bold;")
        self.btn_remove.clicked.connect(self.removeRequested.emit)
        header_layout.addWidget(self.btn_remove)

        main_layout.addWidget(self.header_frame)

        # --- Content Area (Collapsible) ---
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 5, 5, 5)

        # 1. Notizen
        self.text_notes = QPlainTextEdit()
        self.text_notes.setPlaceholderText("Notizen")
        self.text_notes.setFixedHeight(120) 
        self.text_notes.textChanged.connect(lambda: self.changed())
        self.content_layout.addWidget(self.text_notes)

        # 2. Einschränkungen & Effekte (wie Dice: gemeinsamer Rahmen, kompakt)
        status_box = QGroupBox()
        status_outer = QVBoxLayout(status_box)
        status_outer.setContentsMargins(6, 6, 6, 6)
        status_outer.setSpacing(4)

        mid_layout = QHBoxLayout()
        mid_layout.setContentsMargins(0, 0, 0, 0)
        mid_layout.setSpacing(8)

        wunden_box = QGroupBox("Einschränkungen")
        wunden_box.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.wunden_layout = QVBoxLayout(wunden_box)
        self.wunden_layout.setContentsMargins(6, 6, 6, 6)
        self.wunden_layout.setSpacing(4)

        wunden_btn_layout = QHBoxLayout()
        wunden_btn_layout.setContentsMargins(0, 0, 0, 0)
        wunden_btn_layout.setSpacing(2)
        wunden_btn_layout.addStretch()
        self.wunden_buttons = []
        for i in range(8):
            btn = QPushButton("")
            btn.setFixedSize(28, 28)
            btn.setToolTip("Klicken: Wunde / Erschöpfung")
            btn.clicked.connect(partial(self.wunde_clicked, i))
            self.wunden_buttons.append(btn)
            wunden_btn_layout.addWidget(btn)
        self.btn_add_einschraenkung = QPushButton("+")
        self.btn_add_einschraenkung.setFixedSize(28, 28)
        self.btn_add_einschraenkung.setToolTip(
            "Mehrere Erschöpfungen/Wunden auf einmal (eine Quelle)"
        )
        self.btn_add_einschraenkung.clicked.connect(self._modal_add_einschraenkungen)
        wunden_btn_layout.addWidget(self.btn_add_einschraenkung)
        wunden_btn_layout.addStretch()
        self.wunden_layout.addLayout(wunden_btn_layout)

        self.check_ignore_wounds = QCheckBox("Ignorieren")
        self.check_ignore_wounds.stateChanged.connect(lambda: self.changed())
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.addWidget(self.check_ignore_wounds)
        bottom_row.addStretch()
        self.btn_wunden_info = QPushButton("i")
        self.btn_wunden_info.setFixedSize(28, 28)
        self.btn_wunden_info.setToolTip("Wundregeln / Proben")
        self.btn_wunden_info.clicked.connect(self._show_wunden_info_dialog)
        bottom_row.addWidget(self.btn_wunden_info)
        self.wunden_layout.addLayout(bottom_row)
        mid_layout.addWidget(wunden_box, 0)

        effekte_box = QGroupBox("Aktive Effekte")
        eff_outer = QVBoxLayout(effekte_box)
        eff_outer.setContentsMargins(6, 6, 6, 6)
        btn_row = QHBoxLayout()
        self.btn_add_preset = QPushButton("+ Vorlage ▾")
        self.btn_add_custom = QPushButton("+ Eigener Effekt")
        self.btn_dec_effects = QPushButton("− Runde")
        self.btn_dec_effects.setToolTip("Dauer aller Timer-Effekte um 1")
        self.btn_dec_effects.clicked.connect(self.decrement_all_effects)
        btn_row.addWidget(self.btn_add_preset)
        btn_row.addWidget(self.btn_add_custom)
        btn_row.addWidget(self.btn_dec_effects)
        btn_row.addStretch()
        eff_outer.addLayout(btn_row)

        self.effects_scroll = QScrollArea()
        self.effects_scroll.setWidgetResizable(True)
        self.effects_scroll.setMinimumHeight(120)
        self.effects_scroll.setMaximumHeight(180)
        self.effects_container = QWidget()
        self.effects_list_layout = QVBoxLayout(self.effects_container)
        self.effects_list_layout.setContentsMargins(0, 0, 0, 0)
        self.effects_list_layout.setSpacing(2)
        self.effects_list_layout.addStretch()
        self.effects_scroll.setWidget(self.effects_container)
        eff_outer.addWidget(self.effects_scroll)

        self._rebuild_preset_menu()
        self.btn_add_custom.clicked.connect(self._add_custom_effect)
        self.effect_widgets = []  # legacy
        self._effects_data = []

        mid_layout.addWidget(effekte_box, 1)
        status_outer.addLayout(mid_layout)

        self.wundenPenaltyLabel = QLabel("")
        self.wundenPenaltyLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wundenPenaltyLabel.setStyleSheet("font-weight: bold; color: #a12323;")
        self.wundenHinweisLabel = QLabel("")
        self.wundenHinweisLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wundenHinweisLabel.setStyleSheet("font-style: italic; color: #666;")
        self.effectsModLabel = QLabel("")
        self.effectsModLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.effectsModLabel.setStyleSheet("font-weight: bold; color: #236fa1;")
        status_outer.addWidget(self.wundenPenaltyLabel)
        status_outer.addWidget(self.wundenHinweisLabel)
        status_outer.addWidget(self.effectsModLabel)

        self.content_layout.addWidget(status_box)

        # 3. Werte & Würfeln (Standard SC Implementierung)
        self.werte_box = QGroupBox("Werte")
        werte_layout = QGridLayout(self.werte_box)
        werte_layout.addWidget(QLabel("<b>Wert</b>"), 0, 0)
        werte_layout.addWidget(QLabel("<b>Input</b>"), 0, 1)
        werte_layout.addWidget(QLabel(""), 0, 2)

        self.spin_ini = self._add_stat_row(werte_layout, 1, "INI", False)
        # Wenn wir im Header INI haben, müssen wir diese syncen
        self.spin_ini.valueChanged.connect(self.sync_ini_spin)

        self.spin_mr = self._add_stat_row(werte_layout, 2, "MR")
        self.spin_in = self._add_stat_row(werte_layout, 3, "IN")
        self.spin_wachsamkeit = self._add_stat_row(werte_layout, 4, "Wachsamkeit")
        self.spin_menschenkenntnis = self._add_stat_row(werte_layout, 5, "Menschenkenntnis")

        self.check_roll_all = QCheckBox("Bei 'Alle würfeln' berücksichtigen")
        self.check_roll_all.stateChanged.connect(lambda: self.changed())
        self.content_layout.addWidget(self.werte_box)
        self.content_layout.addWidget(self.check_roll_all)

        main_layout.addWidget(self.content_widget)
        self.content_widget.hide() 
        self.update_style()

    def _add_stat_row(self, layout, row, label, rollable=True):
        layout.addWidget(QLabel(label), row, 0)
        spin = QSpinBox()
        spin.setRange(0, 999)
        spin.valueChanged.connect(lambda *a: self.changed())
        layout.addWidget(spin, row, 1)
        if rollable:
            btn = QPushButton("🎲")
            btn.setFixedWidth(30)
            btn.clicked.connect(lambda checked=False, n=label, s=spin: self.trigger_roll(n, s.value()))
            layout.addWidget(btn, row, 2)
        else:
            layout.addWidget(QLabel("-"), row, 2)
        return spin

    def trigger_roll(self, attr_name, value): self.rollRequested.emit(self, attr_name, value)

    def trigger_at_roll(self, weapon_name, at_value, tp_string):
        """AT mit zugehörigem TP-String für den Manöver→Schaden-Flow."""
        if hasattr(self, "atRollRequested"):
            self.atRollRequested.emit(self, f"AT {weapon_name}", at_value, tp_string)
        else:
            self.rollRequested.emit(self, f"AT {weapon_name}", at_value)

    def trigger_vt_roll(self, weapon_name, vt_value, tp_string):
        """VT inkl. TP (für Auflaufen lassen → Schaden)."""
        if hasattr(self, "vtRollRequested"):
            self.vtRollRequested.emit(self, f"VT {weapon_name}", vt_value, tp_string)
        elif hasattr(self, "atRollRequested"):
            # Fallback: gleiche Signatur über atRollRequested (Handler erkennt VT)
            self.atRollRequested.emit(self, f"VT {weapon_name}", vt_value, tp_string)
        else:
            self.rollRequested.emit(self, f"VT {weapon_name}", vt_value)
    
    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        self.btn_expand.setArrowType(Qt.ArrowType.DownArrow if self.is_expanded else Qt.ArrowType.RightArrow)

    def set_expanded(self, expanded: bool):
        """Explizit auf- oder zuklappen (z. B. bei INI-Weiter)."""
        self.is_expanded = expanded
        self.content_widget.setVisible(expanded)
        self.btn_expand.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)

    def _get_effects(self):
        # Wichtig: leere Liste ist falsy → nicht mit `or` auf data zurückfallen
        raw = getattr(self, "_effects_data", None)
        if raw is None:
            raw = self.data.get("effekte", [])
        return normalize_list(raw)

    def _set_effects(self, effects):
        self._effects_data = normalize_list(effects)
        self.data["effekte"] = self._effects_data
        if getattr(self, "isLoading", False):
            return
        # Während Würfen/Ticks: UI kann schon gelöscht sein (INI-Umbau) –
        # Daten sind oben gespeichert, changed() nur wenn Widgets noch leben.
        try:
            edit = getattr(self, "edit_name", None)
            if edit is None:
                return
            _ = edit.objectName()  # löst RuntimeError aus, falls C++-Objekt weg
            self.changed()
        except RuntimeError:
            pass

    def _rebuild_effects_ui(self):
        if not hasattr(self, "effects_list_layout"):
            return
        while self.effects_list_layout.count():
            item = self.effects_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for eff in self._get_effects():
            self._add_effect_row_widget(eff)
        self.effects_list_layout.addStretch()
        self._update_effects_mod_label()

    def _add_effect_row_widget(self, eff):
        row = QFrame()
        row.setFrameShape(QFrame.Shape.StyledPanel)
        hl = QHBoxLayout(row)
        hl.setContentsMargins(2, 1, 2, 1)
        hl.setSpacing(3)
        name_lab = QLabel(f"<b>{eff.get('name','?')}</b>")
        hl.addWidget(name_lab, 2)
        summary = QLabel(effect_summary_line(eff))
        summary.setStyleSheet("color:#555;font-size:10px;")
        hl.addWidget(summary, 3)
        timer_btn = QPushButton("⏱" if eff.get("has_timer") else "∞")
        timer_btn.setFixedWidth(26)
        timer_btn.clicked.connect(partial(self._toggle_effect_timer, eff.get("id")))
        hl.addWidget(timer_btn)
        dur = QSpinBox(); dur.setRange(0, 999); dur.setValue(int(eff.get("duration", 0) or 0))
        dur.setFixedWidth(40); dur.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        dur.setEnabled(bool(eff.get("has_timer")))
        dur.valueChanged.connect(partial(self._on_eff_dur, eff.get("id")))
        hl.addWidget(dur)
        info_btn = QPushButton("i"); info_btn.setFixedWidth(22)
        info_btn.setToolTip("Info / freier Wurf")
        info_btn.clicked.connect(partial(self._show_effect_info, eff.get("id")))
        hl.addWidget(info_btn)
        edit_btn = QPushButton("✎"); edit_btn.setFixedWidth(22)
        edit_btn.setToolTip("Effekt bearbeiten")
        edit_btn.clicked.connect(partial(self._edit_effect, eff.get("id")))
        hl.addWidget(edit_btn)
        save_btn = QPushButton("★"); save_btn.setFixedWidth(22)
        save_btn.setToolTip("Als Vorlage speichern")
        save_btn.clicked.connect(partial(self._save_effect_as_preset, eff.get("id")))
        hl.addWidget(save_btn)
        del_btn = QPushButton("✕"); del_btn.setFixedWidth(22)
        del_btn.setStyleSheet("color:#a33;font-weight:bold;")
        del_btn.clicked.connect(partial(self._remove_effect, eff.get("id")))
        hl.addWidget(del_btn)
        self.effects_list_layout.addWidget(row)

    def _rebuild_preset_menu(self):
        menu = QMenu(self)
        builtins = menu.addMenu("Standard")
        for key, preset in EFFECT_PRESETS.items():
            act = builtins.addAction(preset["name"])
            act.triggered.connect(partial(self._add_effect_preset, key))
        user_menu = menu.addMenu("Eigene Vorlagen")
        if CUSTOM_EFFECT_PRESETS:
            for key, preset in sorted(CUSTOM_EFFECT_PRESETS.items(), key=lambda kv: kv[1].get("name") or ""):
                act = user_menu.addAction(preset.get("name") or key)
                act.triggered.connect(partial(self._add_effect_preset, key))
            user_menu.addSeparator()
            del_menu = user_menu.addMenu("Vorlage löschen…")
            for key, preset in sorted(CUSTOM_EFFECT_PRESETS.items(), key=lambda kv: kv[1].get("name") or ""):
                dact = del_menu.addAction(preset.get("name") or key)
                dact.triggered.connect(partial(self._delete_custom_preset, key))
        else:
            empty = user_menu.addAction("(keine)")
            empty.setEnabled(False)
        self.btn_add_preset.setMenu(menu)

    def _persist_custom_presets(self):
        save_custom_presets_to_file()
        # auch in master_data halten, damit save_to_json konsistent bleibt
        try:
            if hasattr(self, "master_data") and isinstance(self.master_data, dict):
                self.master_data["effect_presets"] = dump_custom_presets()
        except Exception:
            pass

    def _delete_custom_preset(self, key):
        if delete_custom_preset(key):
            self._persist_custom_presets()
            self._rebuild_preset_menu()

    def _save_effect_as_preset(self, eid):
        effects = self._get_effects()
        eff = next((e for e in effects if e.get("id") == eid), None)
        if not eff:
            return
        name, ok = QInputDialog.getText(
            self, "Als Vorlage speichern", "Name der Vorlage:",
            text=eff.get("name") or "Vorlage",
        )
        if not ok or not (name or "").strip():
            return
        register_custom_preset(name.strip(), eff)
        self._persist_custom_presets()
        self._rebuild_preset_menu()
        QMessageBox.information(self, "Vorlage", f"„{name.strip()}“ gespeichert.")

    def _nsc_vorteil_names(self):
        names = list(getattr(self, "vorteile_list_data", None) or [])
        # Fallback: powers_data-Namen (manche NSCs speichern Vorteile dort)
        for p in getattr(self, "powers_data", None) or []:
            n = p.get("name") if isinstance(p, dict) else None
            if n and n not in names:
                names.append(n)
        return names

    def _add_effect_preset(self, key):
        effects = self._get_effects()
        if key == "atemtechnik":
            ko = 0
            if hasattr(self, "attr_spins") and "KO" in self.attr_spins:
                ko = self.attr_spins["KO"].value()
            effects = [e for e in effects if not (e.get("name") or "").lower().startswith("atemtechnik")]
            effects.append(make_atemtechnik_effect(ko))
        elif key == "volle_offensive":
            has_ok = _has_named_vorteil(self._nsc_vorteil_names(), "Offensiver Kampfstil")
            effects = [e for e in effects if not is_volle_kampfhaltung(e)]
            effects.append(make_volle_offensive_effect(has_ok))
        elif key == "volle_defensive":
            has_dk = _has_named_vorteil(self._nsc_vorteil_names(), "Defensiver Kampfstil")
            effects = [e for e in effects if not is_volle_kampfhaltung(e)]
            effects.append(make_volle_defensive_effect(has_dk))
        elif key == "blutend":
            effects.append(make_blutend_effect(self._nsc_ws_wert()))
        else:
            effects.append(from_preset(key))
        self._set_effects(effects)
        self._rebuild_effects_ui()

    def _add_custom_effect(self):
        """Gleicher Editor wie im Dice Plugin."""
        eff = blank_effect("Neuer Effekt")

        def _done(edited):
            if not edited:
                return
            effects = self._get_effects()
            effects.append(edited)
            self._set_effects(effects)
            self._rebuild_effects_ui()

        self._effect_editor_dialog(eff, on_done=_done)

    def _edit_effect(self, eid):
        effects = self._get_effects()
        for e in effects:
            if e.get("id") == eid:
                def _done(edited, target=e, all_eff=effects):
                    if not edited:
                        return
                    target.update(edited)
                    self._set_effects(all_eff)
                    self._rebuild_effects_ui()

                self._effect_editor_dialog(e, on_done=_done)
                break

    def _remove_effect(self, eid):
        self._set_effects([e for e in self._get_effects() if e.get("id") != eid])
        self._rebuild_effects_ui()

    def _toggle_effect_timer(self, eid):
        effects = self._get_effects()
        for e in effects:
            if e.get("id") == eid:
                e["has_timer"] = not e.get("has_timer")
        self._set_effects(effects)
        self._rebuild_effects_ui()

    def _on_eff_dur(self, eid, val):
        if getattr(self, "isLoading", False):
            return
        effects = self._get_effects()
        for e in effects:
            if e.get("id") == eid:
                e["duration"] = int(val)
        self._set_effects(effects)

    def _show_effect_info(self, eid):
        eff = next((e for e in self._get_effects() if e.get("id") == eid), None)
        if not eff:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(eff.get("name") or "Effekt")
        dlg.setMinimumWidth(360)
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(f"<b>{eff.get('name')}</b>"))
        lay.addWidget(QLabel(effect_summary_line(eff)))
        info = QPlainTextEdit()
        info.setPlainText(eff.get("info_text") or "")
        info.setReadOnly(True)
        info.setMaximumHeight(120)
        lay.addWidget(info)
        roll_row = QHBoxLayout()
        roll_ed = QLineEdit(eff.get("info_roll") or "")
        roll_ed.setPlaceholderText("z.B. 1W6 oder KO-Probe")
        roll_btn = QPushButton("🎲 Würfeln")
        result_lab = QLabel("")
        result_lab.setWordWrap(True)

        def do_roll():
            s = roll_ed.text().strip()
            if not s:
                return
            m = re.search(r"(\d*)[wWdD](\d+)", s)
            if m:
                n = int(m.group(1) or 1)
                sides = int(m.group(2))
                rolls = [random.randint(1, sides) for _ in range(n)]
                result_lab.setText(f"{rolls} = <b>{sum(rolls)}</b>")
            else:
                result_lab.setText(s)

        roll_btn.clicked.connect(do_roll)
        roll_row.addWidget(roll_ed)
        roll_row.addWidget(roll_btn)
        lay.addLayout(roll_row)
        lay.addWidget(result_lab)
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        box.rejected.connect(dlg.reject)
        box.accepted.connect(dlg.accept)
        lay.addWidget(box)
        dlg.exec()

    def _probe_selector_dialog(self, current_type="attr", current_name="KO"):
        dlg = QDialog(self)
        dlg.setWindowTitle("Probe auswählen")
        dlg.setMinimumSize(520, 480)
        lay = QVBoxLayout(dlg)
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Art:"))
        kat = QComboBox()
        kat.addItem("Alle", None)
        kat.addItem("Attribute", "attr")
        kat.addItem("Fertigkeiten", "fertigkeit")
        kat.addItem("Talente / PW(T)", "talent")
        filter_row.addWidget(kat, 1)
        lay.addLayout(filter_row)
        search = QLineEdit()
        search.setPlaceholderText("Suchen…")
        lay.addWidget(search)
        tree = QTreeWidget()
        tree.setHeaderLabels(["Name", "PW", "Art"])
        tree.setRootIsDecorated(False)
        tree.setAlternatingRowColors(True)
        tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        lay.addWidget(tree)

        try:
            entries = collect_nsc_probe_entries(self)
        except Exception:
            entries = collect_nsc_probe_entries(None, skills=getattr(self, "skills_data", []) or [])

        def refresh():
            ft = search.text().strip().lower()
            want = kat.currentData()
            tree.clear()
            sel = None
            for e in entries:
                if want and e["type"] != want:
                    continue
                if ft and ft not in e["label"].lower() and ft not in e["name"].lower():
                    continue
                item = QTreeWidgetItem([e["label"], str(e["pw"]), e["kind"]])
                item.setData(0, Qt.ItemDataRole.UserRole, e)
                tree.addTopLevelItem(item)
                if e["type"] == current_type and e["name"] == current_name:
                    sel = item
            if sel:
                tree.setCurrentItem(sel)

        search.textChanged.connect(refresh)
        kat.currentIndexChanged.connect(refresh)
        refresh()
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        box.accepted.connect(dlg.accept)
        box.rejected.connect(dlg.reject)
        lay.addWidget(box)
        tree.itemDoubleClicked.connect(lambda *_: dlg.accept())
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None
        item = tree.currentItem()
        if not item:
            return None
        e = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return {"type": e.get("type", "attr"), "name": e.get("name", "KO"), "pw": e.get("pw", 0)}

    def _nsc_weapon_names(self):
        names = []
        for w in getattr(self, "combat_widgets", []) or []:
            try:
                n = w["name"].text().strip()
            except Exception:
                n = ""
            if n:
                names.append(n)
        for c in (self.data.get("weapons") or []):
            n = c.get("name") or c.get("anzeigename") or ""
            if n and n not in names:
                names.append(n)
        return names

    def _effect_editor_dialog(self, eff, on_done=None):
        """Erweiterter Effekt-Editor. on_done → nicht-modal."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Effekt bearbeiten")
        toggle_w, full_h = 36, 800
        try:
            screen = dlg.screen() or QApplication.primaryScreen()
            if screen is not None:
                geo = screen.availableGeometry()
                full_h = max(560, geo.height() - 60)
                total_w = max(1000, min(geo.width() - 20, 1400))
            else:
                total_w = 1200
        except Exception:
            total_w = 1200
        page_w = max(520, (total_w - toggle_w) // 2)
        base_w = page_w
        expert_w = page_w
        dlg.setMinimumWidth(page_w + toggle_w)
        dlg.setMinimumHeight(560)
        dlg.resize(page_w + toggle_w, full_h)
        dlg.setModal(False)
        dlg.setWindowModality(Qt.WindowModality.NonModal)
        dlg.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinMaxButtonsHint
        )
        root = QVBoxLayout(dlg)
        book = QHBoxLayout()
        book.setSpacing(0)
        book.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(page_w)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        form = QVBoxLayout(body)

        g_all = QGroupBox("Allgemein")
        f_all = QFormLayout(g_all)
        name_ed = QLineEdit(eff.get("name") or "")
        f_all.addRow("Name:", name_ed)
        info_ed = QPlainTextEdit(eff.get("info_text") or "")
        info_ed.setMaximumHeight(70)
        info_ed.setPlaceholderText("Beschreibung / Giftwirkung / Hinweistext…")
        f_all.addRow("Info-Text:", info_ed)
        roll_ed = QLineEdit(eff.get("info_roll") or "")
        f_all.addRow("Info-Wurf:", roll_ed)
        focus_ed = QLineEdit(eff.get("focus") or "")
        focus_ed.setPlaceholderText("z. B. Zauber X laden, Falle entschärfen…")
        f_all.addRow("Gegenstand:", focus_ed)
        form.addWidget(g_all)

        g_tim = QGroupBox("Timer / Ladungen")
        f_tim = QFormLayout(g_tim)
        timer_cb = QCheckBox("Timer / Ladungen aktiv")
        timer_cb.setChecked(bool(eff.get("has_timer")))
        dur_spin = QSpinBox()
        dur_spin.setRange(0, 999)
        dur_spin.setValue(int(eff.get("duration", 0) or 0))
        f_tim.addRow(timer_cb, dur_spin)
        tick_combo = QComboBox()
        tick_combo.addItem("Jede Runde (eigene INI)", "runde")
        tick_combo.addItem("Bei erfolgreicher AT", "at_erfolg")
        tick_combo.addItem("Bei TP mit verknüpfter Waffe", "tp_waffe")
        mode = eff.get("tick_mode") or "runde"
        tick_combo.setCurrentIndex(max(0, tick_combo.findData(mode)))
        f_tim.addRow("Tick-Modus:", tick_combo)
        notify_spin = QSpinBox()
        notify_spin.setRange(0, 99)
        notify_spin.setValue(int(eff.get("notify_at", 0) or 0))
        f_tim.addRow("Hinweis bei Dauer ≤", notify_spin)
        form.addWidget(g_tim)

        g_gift = QGroupBox("Waffengift")
        f_gift = QFormLayout(g_gift)
        gift_cb = QCheckBox("Ist Waffengift (Ladung bei TP der Waffe)")
        gift_cb.setChecked(bool(eff.get("is_waffengift")))
        f_gift.addRow(gift_cb)
        wpn_combo = QComboBox()
        wpn_combo.setEditable(True)
        wpn_combo.addItem("— keine —", "")
        for wn in self._nsc_weapon_names():
            wpn_combo.addItem(wn, wn)
        cur_w = (eff.get("weapon_name") or "").strip()
        if cur_w:
            i = wpn_combo.findData(cur_w)
            if i < 0:
                wpn_combo.addItem(cur_w, cur_w)
                i = wpn_combo.findData(cur_w)
            if i >= 0:
                wpn_combo.setCurrentIndex(i)
        f_gift.addRow("Waffe:", wpn_combo)
        form.addWidget(g_gift)

        def _sync_gift():
            if gift_cb.isChecked() and tick_combo.currentData() == "runde":
                tick_combo.setCurrentIndex(tick_combo.findData("tp_waffe"))
        gift_cb.toggled.connect(_sync_gift)

        g_mod = QGroupBox("Modifikatoren")
        f_mod = QFormLayout(g_mod)
        mods = eff.get("mods") or {}
        mod_spins = {}
        for key, label in [
            ("proben", "Proben"), ("at", "AT"), ("vt", "VT/PA"),
            ("gs", "GS"), ("rs", "RS"),
        ]:
            sp = QSpinBox()
            sp.setRange(-40, 40)
            sp.setValue(int(mods.get(key, 0) or 0))
            f_mod.addRow(f"{label}:", sp)
            mod_spins[key] = sp
        tp_legacy = int(mods.get("tp", 0) or 0)
        tp_init = (eff.get("tp_dice") or "").strip()
        if not tp_init and tp_legacy:
            tp_init = f"{tp_legacy:+d}"
        tp_dice_ed = QLineEdit(tp_init)
        tp_dice_ed.setPlaceholderText("z. B. +3, 1W6 oder 2W6+1 (nach Hammerschlag)")
        f_mod.addRow("TP:", tp_dice_ed)
        wsch_ed = QLineEdit(eff.get("waffenschaden") or "")
        wsch_ed.setPlaceholderText("z. B. +2, 1W6 (vor Hammerschlag)")
        f_mod.addRow("Waffenschaden:", wsch_ed)
        flucht_cb = QCheckBox("Nur Flucht")
        flucht_cb.setChecked(bool((eff.get("flags") or {}).get("flucht")))
        rueck_cb = QCheckBox("Rückzug wenn möglich")
        rueck_cb.setChecked(bool((eff.get("flags") or {}).get("rueckzug")))
        rowf = QHBoxLayout()
        rowf.addWidget(flucht_cb)
        rowf.addWidget(rueck_cb)
        f_mod.addRow(rowf)
        form.addWidget(g_mod)
        form.addStretch()

        def _make_probe_picker(initial_type, initial_name, initial_val, parent_form):
            state = {
                "type": initial_type or "attr",
                "name": initial_name or "KO",
                "value": int(initial_val or 14),
            }
            btn = QPushButton()
            val_spin = QSpinBox()
            val_spin.setRange(1, 40)
            val_spin.setValue(state["value"])

            def _label():
                try:
                    entries = collect_nsc_probe_entries(self)
                    val = resolve_probe_pw(entries, state["type"], state["name"], 0)
                    if val:
                        kind = {"attr": "Attr", "fertigkeit": "Fert", "talent": "Tal"}.get(state["type"], "?")
                        return f"{kind}: {state['name']}  (PW {val})"
                except Exception:
                    pass
                kind = {"attr": "Attr", "fertigkeit": "Fert", "talent": "Tal"}.get(state["type"], "?")
                return f"{kind}: {state['name']}"

            def _refresh():
                btn.setText(_label())

            def _open():
                chosen = self._probe_selector_dialog(state["type"], state["name"])
                if chosen:
                    state["type"] = chosen["type"]
                    state["name"] = chosen["name"]
                    _refresh()

            btn.clicked.connect(_open)
            _refresh()
            parent_form.addRow("Probe:", btn)
            parent_form.addRow("Gegen Wert:", val_spin)
            return state, btn, val_spin

        g_mid = QGroupBox("Zwischen-Effekt (Intervall alle x INI, Effekt bleibt)")
        f_mid = QFormLayout(g_mid)
        mid_at = QSpinBox()
        mid_at.setRange(0, 999)
        mid_at.setValue(int(eff.get("mid_trigger_at", 0) or 0))
        mid_at.setToolTip(
            "0 = aus. Wirkung wiederholt sich alle x Timer-/Ladungs-Abzüge "
            "(z. B. 3 = alle 3 − Runde / AT- / TP-Ticks)."
        )
        f_mid.addRow("Alle x INI:", mid_at)
        mid_action = QComboBox()
        mid_action.addItem("Keine / nur weiterlaufen", None)
        mid_action.addItem("1 Erschöpfung (/)", "erschöpfung")
        mid_action.addItem("Einschränkung(en)", "wunde")
        mid_action.addItem("Probe fordern", "probe")
        mid_action.addItem("Hinweis-Popup", "notify")
        mai = mid_action.findData(eff.get("mid_trigger_action"))
        mid_action.setCurrentIndex(mai if mai >= 0 else 0)
        f_mid.addRow("Wirkung:", mid_action)
        mid_wounds = QSpinBox()
        mid_wounds.setRange(1, 8)
        mid_wounds.setValue(max(1, min(8, int(eff.get("mid_wounds", 1) or 1))))
        mid_einsch_art = QComboBox()
        mid_einsch_art.addItem("Wunden", "wunde")
        mid_einsch_art.addItem("Erschöpfung", "ersch")
        mid_ia = mid_einsch_art.findData(eff.get("mid_einsch_art") or "wunde")
        mid_einsch_art.setCurrentIndex(mid_ia if mid_ia >= 0 else 0)
        mid_einsch_row = QWidget()
        mid_einsch_l = QHBoxLayout(mid_einsch_row)
        mid_einsch_l.setContentsMargins(0, 0, 0, 0)
        mid_einsch_l.addWidget(mid_wounds)
        mid_einsch_l.addWidget(mid_einsch_art, 1)
        f_mid.addRow("Anzahl Einschränkungen:", mid_einsch_row)
        mid_hint = QLineEdit(eff.get("mid_notify_text") or "")
        mid_hint.setPlaceholderText("Text für Hinweis-Popup…")
        f_mid.addRow("Hinweis-Text:", mid_hint)
        mid_probe_state, mid_probe_btn, mid_probe_val = _make_probe_picker(
            eff.get("mid_probe_type") or "attr",
            eff.get("mid_probe_name") or "KO",
            eff.get("mid_probe_value", 14),
            f_mid,
        )
        mid_probe_info = QPlainTextEdit(eff.get("mid_probe_info") or "")
        mid_probe_info.setMaximumHeight(54)
        mid_probe_info.setPlaceholderText("Text im Probe-Popup, bevor gewürfelt wird…")
        f_mid.addRow("Probe-Info:", mid_probe_info)
        mid_probe_ok = QLineEdit(eff.get("mid_probe_ok_text") or "")
        mid_probe_ok.setPlaceholderText("Text bei gelungener Probe…")
        f_mid.addRow("Bei Gelingen:", mid_probe_ok)
        mid_probe_fail = QLineEdit(eff.get("mid_probe_fail_text") or "")
        mid_probe_fail.setPlaceholderText("Text bei misslungener Probe…")
        f_mid.addRow("Bei Misslingen:", mid_probe_fail)
        mid_fail_wounds = QSpinBox()
        mid_fail_wounds.setRange(0, 8)
        mid_fail_wounds.setValue(max(0, min(8, int(eff.get("mid_probe_fail_wounds", 0) or 0))))
        mid_fail_art = QComboBox()
        mid_fail_art.addItem("Wunden", "wunde")
        mid_fail_art.addItem("Erschöpfung", "ersch")
        mid_fa = mid_fail_art.findData(eff.get("mid_probe_fail_art") or "wunde")
        mid_fail_art.setCurrentIndex(mid_fa if mid_fa >= 0 else 0)
        mid_fail_row = QWidget()
        mid_fail_l = QHBoxLayout(mid_fail_row)
        mid_fail_l.setContentsMargins(0, 0, 0, 0)
        mid_fail_l.addWidget(mid_fail_wounds)
        mid_fail_l.addWidget(mid_fail_art, 1)
        f_mid.addRow("Misslingen → Einschränkungen:", mid_fail_row)

        g_end = QGroupBox("Bei Ablauf / letzter Ladung")
        f_end = QFormLayout(g_end)
        end_combo = QComboBox()
        end_combo.addItem("Nur entfernen", None)
        end_combo.addItem("1 Erschöpfung (/)", "erschöpfung")
        end_combo.addItem("Einschränkung(en)", "wunde")
        end_combo.addItem("Probe fordern", "probe")
        end_combo.addItem("Hinweis-Popup", "notify")
        ei = end_combo.findData(eff.get("on_end"))
        end_combo.setCurrentIndex(ei if ei >= 0 else 0)
        f_end.addRow("Wirkung:", end_combo)
        end_wounds = QSpinBox()
        end_wounds.setRange(1, 8)
        end_wounds.setValue(max(1, min(8, int(eff.get("on_end_wounds", 1) or 1))))
        end_einsch_art = QComboBox()
        end_einsch_art.addItem("Wunden", "wunde")
        end_einsch_art.addItem("Erschöpfung", "ersch")
        end_ia = end_einsch_art.findData(eff.get("on_end_einsch_art") or "wunde")
        end_einsch_art.setCurrentIndex(end_ia if end_ia >= 0 else 0)
        end_einsch_row = QWidget()
        end_einsch_l = QHBoxLayout(end_einsch_row)
        end_einsch_l.setContentsMargins(0, 0, 0, 0)
        end_einsch_l.addWidget(end_wounds)
        end_einsch_l.addWidget(end_einsch_art, 1)
        f_end.addRow("Anzahl Einschränkungen:", end_einsch_row)
        end_hint = QLineEdit(eff.get("on_end_notify_text") or "")
        end_hint.setPlaceholderText("Text für Hinweis-Popup / Ablauf…")
        f_end.addRow("Hinweis-Text:", end_hint)
        end_probe_state, end_probe_btn, end_probe_val = _make_probe_picker(
            eff.get("on_end_probe_type") or "attr",
            eff.get("on_end_probe_name") or "KO",
            eff.get("on_end_probe_value", 14),
            f_end,
        )
        end_probe_info = QPlainTextEdit(eff.get("on_end_probe_info") or "")
        end_probe_info.setMaximumHeight(54)
        end_probe_info.setPlaceholderText("Text im Probe-Popup, bevor gewürfelt wird…")
        f_end.addRow("Probe-Info:", end_probe_info)
        end_probe_ok = QLineEdit(eff.get("on_end_probe_ok_text") or "")
        end_probe_ok.setPlaceholderText("Text bei gelungener Probe…")
        f_end.addRow("Bei Gelingen:", end_probe_ok)
        end_probe_fail = QLineEdit(eff.get("on_end_probe_fail_text") or "")
        end_probe_fail.setPlaceholderText("Text bei misslungener Probe…")
        f_end.addRow("Bei Misslingen:", end_probe_fail)
        end_fail_wounds = QSpinBox()
        end_fail_wounds.setRange(0, 8)
        end_fail_wounds.setValue(max(0, min(8, int(eff.get("on_end_probe_fail_wounds", 0) or 0))))
        end_fail_art = QComboBox()
        end_fail_art.addItem("Wunden", "wunde")
        end_fail_art.addItem("Erschöpfung", "ersch")
        end_fa = end_fail_art.findData(eff.get("on_end_probe_fail_art") or "wunde")
        end_fail_art.setCurrentIndex(end_fa if end_fa >= 0 else 0)
        end_fail_row = QWidget()
        end_fail_l = QHBoxLayout(end_fail_row)
        end_fail_l.setContentsMargins(0, 0, 0, 0)
        end_fail_l.addWidget(end_fail_wounds)
        end_fail_l.addWidget(end_fail_art, 1)
        f_end.addRow("Misslingen → Einschränkungen:", end_fail_row)

        g_pre = QGroupBox("Vorzeitig Timer auf 0")
        f_pre = QFormLayout(g_pre)
        pre_mode = QComboBox()
        pre_mode.addItem("Aus", None)
        pre_mode.addItem("Bei x Einschränkungen (Ersch. oder Wunde, eine Quelle)", "einschr")
        pre_mode.addItem("Bei x Wunden (eine Quelle)", "wunden")
        pre_mode.addItem("Bei x Erschöpfung (eine Quelle)", "ersch")
        pmi = pre_mode.findData(eff.get("premature_mode"))
        pre_mode.setCurrentIndex(pmi if pmi >= 0 else 0)
        f_pre.addRow("Bedingung:", pre_mode)
        pre_x = QSpinBox()
        pre_x.setRange(1, 8)
        pre_x.setValue(max(1, min(8, int(eff.get("premature_x", 1) or 1))))
        f_pre.addRow("Schwelle x:", pre_x)
        pre_hint = QLineEdit(eff.get("premature_interrupt_text") or "")
        pre_hint.setPlaceholderText("Abbruch-Text…")
        f_pre.addRow("Abbruch-Text:", pre_hint)
        pre_note = QLabel(
            "Nur +Modal / Effekt-Quellen (eine Quelle = ein Schlag)."
        )
        pre_note.setWordWrap(True)
        pre_note.setStyleSheet("color:#666; font-size: 11px;")
        f_pre.addRow(pre_note)

        g_cinfo = QGroupBox("Bei Bedingung Info-Text")
        f_cinfo = QFormLayout(g_cinfo)
        cinfo_mode = QComboBox()
        cinfo_mode.addItem("Aus", None)
        cinfo_mode.addItem("Bei x Einschränkungen (eine Quelle)", "einschr")
        cinfo_mode.addItem("Bei x Wunden (eine Quelle)", "wunden")
        cinfo_mode.addItem("Bei x Erschöpfung (eine Quelle)", "ersch")
        cii = cinfo_mode.findData(eff.get("condition_info_mode"))
        cinfo_mode.setCurrentIndex(cii if cii >= 0 else 0)
        f_cinfo.addRow("Bedingung:", cinfo_mode)
        cinfo_x = QSpinBox()
        cinfo_x.setRange(1, 8)
        cinfo_x.setValue(max(1, min(8, int(eff.get("condition_info_x", 1) or 1))))
        f_cinfo.addRow("Schwelle x:", cinfo_x)
        cinfo_note = QLabel(
            "Timer bleibt. Info-Text wie i-Taste (z. B. Konzentrations-Störung)."
        )
        cinfo_note.setWordWrap(True)
        cinfo_note.setStyleSheet("color:#666; font-size: 11px;")
        f_cinfo.addRow(cinfo_note)

        def _sync_probe_rows(_=None):
            mid_act = mid_action.currentData()
            end_act = end_combo.currentData()
            mid_probe_btn.setEnabled(mid_act == "probe")
            mid_probe_val.setEnabled(mid_act == "probe")
            mid_probe_info.setEnabled(mid_act == "probe")
            mid_probe_ok.setEnabled(mid_act == "probe")
            mid_probe_fail.setEnabled(mid_act == "probe")
            mid_fail_wounds.setEnabled(mid_act == "probe")
            mid_fail_art.setEnabled(mid_act == "probe")
            mid_einsch_art.setEnabled(mid_act == "wunde")
            end_probe_btn.setEnabled(end_act == "probe")
            end_probe_val.setEnabled(end_act == "probe")
            end_probe_info.setEnabled(end_act == "probe")
            end_probe_ok.setEnabled(end_act == "probe")
            end_probe_fail.setEnabled(end_act == "probe")
            end_fail_wounds.setEnabled(end_act == "probe")
            end_fail_art.setEnabled(end_act == "probe")
            end_einsch_art.setEnabled(end_act == "wunde")
            mid_wounds.setEnabled(mid_act == "wunde")
            end_wounds.setEnabled(end_act == "wunde")
            mid_hint.setEnabled(True)
            end_hint.setEnabled(True)
        mid_action.currentIndexChanged.connect(_sync_probe_rows)
        end_combo.currentIndexChanged.connect(_sync_probe_rows)
        _sync_probe_rows()

        expert_scroll = QScrollArea()
        expert_scroll.setWidgetResizable(True)
        expert_body = QWidget()
        expert_form = QVBoxLayout(expert_body)
        expert_form.addWidget(QLabel("<b>Expertenmodus</b>"))
        expert_form.addWidget(g_mid)
        expert_form.addWidget(g_end)
        expert_form.addWidget(g_pre)
        expert_form.addWidget(g_cinfo)
        expert_form.addStretch()
        expert_scroll.setWidget(expert_body)
        expert_scroll.setMinimumWidth(0)
        expert_scroll.setMaximumWidth(0)
        expert_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        expert_scroll.setVisible(False)

        toggle_bar = QFrame()
        toggle_bar.setFixedWidth(36)
        toggle_bar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        toggle_bar.setToolTip("Expertenmodus (Intervall, Ablauf, vorzeitig)")
        toggle_bar.setStyleSheet(
            "QFrame { background: #e0e0e0; border-left: 1px solid #bbb; }"
            "QFrame:hover { background: #d0d0d0; }"
            "QToolButton { border: none; font-size: 18px; background: transparent; }"
        )
        toggle_lay = QVBoxLayout(toggle_bar)
        toggle_lay.setContentsMargins(0, 0, 0, 0)
        toggle_lay.addStretch()
        toggle_btn = QToolButton()
        toggle_btn.setArrowType(Qt.ArrowType.RightArrow)
        toggle_btn.setCheckable(True)
        toggle_btn.setChecked(False)
        toggle_btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        toggle_lay.addWidget(toggle_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        toggle_lay.addStretch()

        expert_open = {"on": False}

        def _set_expert(on: bool):
            expert_open["on"] = on
            toggle_btn.setChecked(on)
            if on:
                expert_scroll.setVisible(True)
                expert_scroll.setMinimumWidth(page_w)
                expert_scroll.setMaximumWidth(page_w)
                expert_scroll.setFixedWidth(page_w)
                scroll.setMinimumWidth(page_w)
                scroll.setMaximumWidth(page_w)
                scroll.setFixedWidth(page_w)
                toggle_btn.setArrowType(Qt.ArrowType.LeftArrow)
                full = page_w * 2 + toggle_w
                dlg.setMinimumWidth(full)
                dlg.resize(full, full_h)
                dlg.setMaximumWidth(16777215)
            else:
                expert_scroll.setMinimumWidth(0)
                expert_scroll.setMaximumWidth(0)
                expert_scroll.setFixedWidth(0)
                expert_scroll.setVisible(False)
                scroll.setMinimumWidth(page_w)
                scroll.setMaximumWidth(16777215)
                scroll.setFixedWidth(page_w)
                toggle_btn.setArrowType(Qt.ArrowType.RightArrow)
                dlg.setMinimumWidth(page_w + toggle_w)
                dlg.resize(page_w + toggle_w, full_h)

        class _ToggleFilter(QObject):
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Type.MouseButtonRelease:
                    _set_expert(not expert_open["on"])
                    return True
                return False

        _tf = _ToggleFilter(toggle_bar)
        toggle_bar.installEventFilter(_tf)
        toggle_bar._toggle_filter = _tf

        has_expert = (
            int(eff.get("mid_trigger_at", 0) or 0) > 0
            or bool(eff.get("mid_trigger_action"))
            or bool(eff.get("on_end"))
            or bool((eff.get("on_end_notify_text") or "").strip())
            or bool(eff.get("premature_mode"))
            or bool(eff.get("condition_info_mode"))
        )
        if has_expert:
            _set_expert(True)

        scroll.setWidget(body)
        book.addWidget(scroll, 1)
        book.addWidget(toggle_bar, 0)
        book.addWidget(expert_scroll, 0)
        root.addLayout(book, 1)
        box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        root.addWidget(box)
        result = {}

        def accept():
            wpn = wpn_combo.currentData()
            if wpn is None:
                wpn = wpn_combo.currentText().strip()
            if wpn == "— keine —":
                wpn = ""
            is_gift = gift_cb.isChecked()
            tick = tick_combo.currentData() or "runde"
            if is_gift and tick == "runde":
                tick = "tp_waffe"
            result.update({
                "id": eff.get("id"),
                "name": name_ed.text().strip() or "Effekt",
                "has_timer": timer_cb.isChecked(),
                "duration": dur_spin.value(),
                "notify_at": notify_spin.value(),
                "notify_fired": eff.get("notify_fired", False),
                "mods": {**{k: sp.value() for k, sp in mod_spins.items()}, "tp": 0},
                "flags": {"flucht": flucht_cb.isChecked(), "rueckzug": rueck_cb.isChecked()},
                "info_text": info_ed.toPlainText(),
                "info_roll": roll_ed.text().strip(),
                "source": eff.get("source", "custom"),
                "on_end": end_combo.currentData(),
                "on_end_wounds": end_wounds.value(),
                "on_end_einsch_art": end_einsch_art.currentData() or "wunde",
                "on_end_notify_text": end_hint.text().strip(),
                "on_end_probe_type": end_probe_state["type"],
                "on_end_probe_name": end_probe_state["name"],
                "on_end_probe_value": end_probe_val.value(),
                "mid_trigger_at": mid_at.value(),
                "mid_ticks_elapsed": (
                    int(eff.get("mid_ticks_elapsed", 0) or 0)
                    if mid_at.value() == int(eff.get("mid_trigger_at", 0) or 0)
                    else 0
                ),
                "mid_trigger_action": mid_action.currentData(),
                "mid_trigger_fired": (
                    bool(eff.get("mid_trigger_fired"))
                    if mid_at.value() == int(eff.get("mid_trigger_at", 0) or 0)
                    else False
                ),
                "mid_wounds": mid_wounds.value(),
                "mid_einsch_art": mid_einsch_art.currentData() or "wunde",
                "mid_notify_text": mid_hint.text().strip(),
                "mid_probe_type": mid_probe_state["type"],
                "mid_probe_name": mid_probe_state["name"],
                "mid_probe_value": mid_probe_val.value(),
                "mid_probe_info": mid_probe_info.toPlainText().strip(),
                "mid_probe_ok_text": mid_probe_ok.text().strip(),
                "mid_probe_fail_text": mid_probe_fail.text().strip(),
                "mid_probe_fail_wounds": mid_fail_wounds.value(),
                "mid_probe_fail_art": mid_fail_art.currentData() or "wunde",
                "on_end_probe_info": end_probe_info.toPlainText().strip(),
                "on_end_probe_ok_text": end_probe_ok.text().strip(),
                "on_end_probe_fail_text": end_probe_fail.text().strip(),
                "on_end_probe_fail_wounds": end_fail_wounds.value(),
                "on_end_probe_fail_art": end_fail_art.currentData() or "wunde",
                "tp_dice": tp_dice_ed.text().strip(),
                "waffenschaden": wsch_ed.text().strip(),
                "tick_mode": tick,
                "is_waffengift": is_gift,
                "weapon_name": wpn or "",
                "focus": focus_ed.text().strip(),
                "premature_mode": pre_mode.currentData(),
                "premature_x": pre_x.value(),
                "premature_interrupt_text": pre_hint.text().strip(),
                "premature_fired": bool(eff.get("premature_fired")),
                "condition_info_mode": cinfo_mode.currentData(),
                "condition_info_x": cinfo_x.value(),
            })
            if (result.get("name") or "").lower().startswith("konzentration"):
                if result.get("on_end") in (None, "notify"):
                    result["on_end"] = "notify"
                if not result.get("on_end_notify_text"):
                    result["on_end_notify_text"] = concentration_ready_text(result)
            dlg.accept()

        def reject():
            dlg.close()
            if on_done:
                on_done(None)

        def accept_and_close():
            accept()
            if on_done:
                on_done(result if result else None)

        if on_done:
            box.accepted.connect(accept_and_close)
            box.rejected.connect(reject)
            dlg.show()
            dlg.raise_()
            dlg.activateWindow()
            if not hasattr(self, "_editor_dialogs"):
                self._editor_dialogs = []
            self._editor_dialogs.append(dlg)
            return None

        box.accepted.connect(accept)
        box.rejected.connect(dlg.reject)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return result
        return None

    def _update_effects_mod_label(self):
        mods = sum_mods(self._get_effects())
        parts = [f"{lab} {mods[k]:+d}" for k, lab in [("proben","Proben"),("at","AT"),("vt","VT"),("tp","TP"),("gs","GS"),("rs","RS")] if mods.get(k)]
        if hasattr(self, "effectsModLabel"):
            self.effectsModLabel.setText("Effekte: " + " · ".join(parts) if parts else "")

    def get_effect_mods(self):
        return sum_mods(self._get_effects())

    def get_wound_penalty(self):
        data = self.data or {}
        if data.get("wunden_ignorieren"):
            return 0
        wunden = list(data.get("wunden") or [])
        if not wunden and getattr(self, "wunden_buttons", None):
            try:
                wunden = [b.text() or None for b in self.wunden_buttons]
            except Exception:
                wunden = []
        return einschraenkung_malus(wunden, False)

    def add_erschopfung(self):
        wunden = list(self.data.get("wunden", [None]*8))
        while len(wunden) < 8:
            wunden.append(None)
        for i in range(8):
            if wunden[i] is None:
                wunden[i] = "/"
                break
        wunden.sort(key=lambda x: (x is None, x != "X"))
        self.data["wunden"] = wunden
        self.update_wound_buttons(wunden)
        self.changed()
        self._apply_premature_from_source(1, 0, source_id=f"effect:ersch:{new_id()}")

    def add_wunde(self, count=1):
        """Koloss: Kratzer I→II (bzw. I–IV). Erschöpfung (/) nie überschreiben."""
        count = max(1, min(8, int(count or 1)))
        mode = int(self.data.get("wunden_modus", 0) or 0)
        wunden = list(self.data.get("wunden", [None] * 8))
        while len(wunden) < 8:
            wunden.append(None)

        def _one():
            if mode == 0:
                for i in range(8):
                    if wunden[i] is None:
                        wunden[i] = "X"
                        return
                for i in range(8):
                    if wunden[i] == "/":
                        wunden[i] = "X"
                        return
                return
            ladder = ["I", "II"] if mode == 1 else ["I", "II", "III", "IV"]
            for step_i, cur in enumerate(ladder[:-1]):
                nxt = ladder[step_i + 1]
                for i in range(8):
                    if wunden[i] == cur:
                        wunden[i] = nxt
                        return
            for i in range(8):
                if wunden[i] is None:
                    wunden[i] = "I"
                    return

        for _ in range(count):
            _one()
        rank = {None: 0, "/": 1, "I": 2, "II": 3, "III": 4, "IV": 5, "X": 6}
        wunden.sort(key=lambda x: rank.get(x, 0), reverse=True)
        self.data["wunden"] = wunden
        self.update_wound_buttons(wunden)
        self.changed()
        self._apply_premature_from_source(0, count, source_id=f"effect:wunde:{new_id()}")

    def remove_erschopfung(self, count=1):
        """Entfernt bis zu count Erschöpfungen (/)."""
        count = max(1, int(count or 1))
        wunden = list(self.data.get("wunden", [None] * 8))
        while len(wunden) < 8:
            wunden.append(None)
        removed = 0
        for i in range(7, -1, -1):
            if removed >= count:
                break
            if wunden[i] == "/":
                wunden[i] = None
                removed += 1
        rank = {None: 0, "/": 1, "I": 2, "II": 3, "III": 4, "IV": 5, "X": 6}
        wunden.sort(key=lambda x: rank.get(x, 0), reverse=True)
        self.data["wunden"] = wunden
        self.update_wound_buttons(wunden)
        self.changed()
        return removed

    def remove_wunde(self, count=1):
        """Entfernt bis zu count Wunden (X bzw. höchste Koloss-Stufe)."""
        count = max(1, int(count or 1))
        mode = int(self.data.get("wunden_modus", 0) or 0)
        wunden = list(self.data.get("wunden", [None] * 8))
        while len(wunden) < 8:
            wunden.append(None)
        removed = 0
        for _ in range(count):
            idx = None
            if mode == 0:
                for i in range(8):
                    if wunden[i] == "X":
                        idx = i
                        break
            else:
                order = ["IV", "III", "II", "I"] if mode == 2 else ["II", "I"]
                for st in order:
                    for i in range(8):
                        if wunden[i] == st:
                            idx = i
                            break
                    if idx is not None:
                        break
            if idx is None:
                break
            wunden[idx] = None
            removed += 1
        rank = {None: 0, "/": 1, "I": 2, "II": 3, "III": 4, "IV": 5, "X": 6}
        wunden.sort(key=lambda x: rank.get(x, 0), reverse=True)
        self.data["wunden"] = wunden
        self.update_wound_buttons(wunden)
        self.changed()
        return removed

    def _modal_add_einschraenkungen(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Einschränkungen hinzufügen")
        lay = QFormLayout(dlg)
        e_spin = QSpinBox(); e_spin.setRange(0, 8)
        w_spin = QSpinBox(); w_spin.setRange(0, 8)
        lay.addRow("Erschöpfung (/):", e_spin)
        lay.addRow("Wunden:", w_spin)
        note = QLabel("Alles aus diesem Dialog zählt als eine Quelle.")
        note.setStyleSheet("color:#666;")
        lay.addRow(note)
        box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        box.accepted.connect(dlg.accept)
        box.rejected.connect(dlg.reject)
        lay.addRow(box)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        n_e, n_w = e_spin.value(), w_spin.value()
        if n_e + n_w <= 0:
            return
        mode = int(self.data.get("wunden_modus", 0) or 0)
        cur = list(self.data.get("wunden", [None] * 8))
        new_w, de, dw = apply_wounds_batch(cur, n_e, n_w, mode)
        self.data["wunden"] = new_w
        self.update_wound_buttons(new_w)
        self._apply_premature_from_source(de, dw, source_id=f"modal:{new_id()}")
        self.changed()

    def _show_top_info(self, title, text):
        name = (title or "Hinweis").strip() or "Hinweis"
        body = (text or "").strip()
        if body and name not in body and f"„{name}“" not in body:
            body = f"<b>{name}</b><br><br>{body}"
        elif not body:
            body = name
        box = QMessageBox(self)
        box.setWindowTitle(name)
        box.setTextFormat(Qt.TextFormat.RichText)
        box.setText(body)
        box.setIcon(QMessageBox.Icon.Information)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.setModal(False)
        box.setWindowModality(Qt.WindowModality.NonModal)
        box.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        box.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        box.show()
        box.raise_()
        box.activateWindow()
        if not hasattr(self, "_info_boxes"):
            self._info_boxes = []
        self._info_boxes = [b for b in getattr(self, "_info_boxes", []) if b is not None]
        self._info_boxes.append(box)

    def _apply_premature_from_source(self, delta_ersch, delta_wunden, source_id=""):
        effects = normalize_list(self._get_effects())
        for m in check_condition_info(effects, delta_ersch, delta_wunden, source_id):
            self._show_top_info(m.get("name") or "Hinweis", m.get("message") or "")
        msgs = check_premature_timers(effects, delta_ersch, delta_wunden, source_id)
        if not msgs:
            return
        end_ersch = False
        end_msg = ""
        kept = []
        for e in effects:
            if e.get("premature_fired") and int(e.get("duration", 0) or 0) <= 0:
                name = (e.get("name") or "").lower()
                if name.startswith("atemtechnik") or e.get("on_end") == "erschöpfung":
                    end_ersch = True
                    end_msg = e.get("premature_interrupt_text") or (
                        "Atemtechnik endet → 1 Erschöpfung."
                    )
                else:
                    self._show_top_info(
                        "Effekt unterbrochen",
                        e.get("premature_interrupt_text")
                        or f"„{e.get('name', 'Effekt')}“ vorzeitig beendet.",
                    )
                continue
            kept.append(e)
        self._set_effects(kept)
        self._rebuild_effects_ui()
        if end_ersch:
            self.add_erschopfung()
            self._show_top_info("Effekt beendet", end_msg)

    def _resolve_nsc_probe_pw(self, ptype, pname):
        try:
            return resolve_probe_pw(collect_nsc_probe_entries(self), ptype, pname, 0)
        except Exception:
            return 0

    def _show_probe_event_dialog(self, ev, resolve_pw, add_wunde_fn):
        if is_legacy_blutend_event(ev):
            ev = blutend_probe_overlay(ev)
        ename = ((ev.get("effect") or {}).get("name") or ev.get("name") or "Probe")
        ptype = ev.get("probe_type") or "attr"
        pname = ev.get("probe_name") or "KO"
        target = int(ev.get("probe_value") or 0)
        kind = {"attr": "Attribut", "fertigkeit": "Fertigkeit", "talent": "Talent"}.get(ptype, "Probe")
        pw = int(resolve_pw(ptype, pname) or 0)
        fail_wounds = max(0, int(ev.get("fail_wounds", 0) or 0))
        fail_art = ev.get("fail_art") or "wunde"
        def _wound_penalty_now():
            try:
                if hasattr(self, "get_wound_penalty"):
                    return int(self.get_wound_penalty() or 0)
            except Exception:
                pass
            return 0

        def _effect_proben_mod():
            try:
                if hasattr(self, "get_effect_mods"):
                    return int((self.get_effect_mods() or {}).get("proben", 0) or 0)
            except Exception:
                pass
            return 0

        wound_penalty = _wound_penalty_now()
        eff_mod = _effect_proben_mod()

        dlg = QDialog(self)
        dlg.setWindowTitle(ename)
        dlg.setModal(False)
        dlg.setWindowModality(Qt.WindowModality.NonModal)
        dlg.setMinimumWidth(420)
        lay = QVBoxLayout(dlg)
        msg = QLabel(ev.get("message") or f"Probe: {kind} {pname} gegen {target}")
        msg.setWordWrap(True)
        lay.addWidget(msg)
        info = (ev.get("probe_info") or "").strip()
        if info:
            info_lab = QLabel(info.replace("\n", "<br>"))
            info_lab.setWordWrap(True)
            info_lab.setTextFormat(Qt.TextFormat.RichText)
            info_lab.setStyleSheet("color:#444;")
            lay.addWidget(info_lab)
        extra_bits = []
        if wound_penalty:
            extra_bits.append(f"−{wound_penalty} Einschränkungen")
        if eff_mod:
            extra_bits.append(f"{eff_mod:+d} Effekte")
        extra_txt = ("  " + "  ".join(extra_bits)) if extra_bits else ""
        meta = QLabel(f"<b>{kind} {pname}</b>  PW {pw}{extra_txt}  gegen {target}")
        meta.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(meta)
        result_lab = QLabel("Noch nicht gewürfelt.")
        result_lab.setWordWrap(True)
        result_lab.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(result_lab)
        outcome_lab = QLabel("")
        outcome_lab.setWordWrap(True)
        outcome_lab.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(outcome_lab)

        btn_row = QHBoxLayout()
        btn1 = QPushButton("1W20 würfeln")
        btn3 = QPushButton("3W20 würfeln")
        if fail_art == "ersch":
            wound_btn = QPushButton(
                f"+{fail_wounds} Erschöpfung" if fail_wounds != 1 else "+1 Erschöpfung"
            )
        else:
            wound_btn = QPushButton(
                f"+{fail_wounds} Wunde" if fail_wounds != 1 else "+1 Wunde"
            )
        wound_btn.setVisible(False)
        wound_btn.setStyleSheet("font-weight:bold; color:#a12323;")
        btn_row.addWidget(btn1)
        btn_row.addWidget(btn3)
        btn_row.addWidget(wound_btn)
        lay.addLayout(btn_row)

        def _apply_outcome(ok):
            if ok:
                txt = (ev.get("probe_ok_text") or "").strip() or "Probe gelungen."
                outcome_lab.setText(f"<b style='color:#2a7a2a'>{txt}</b>")
                wound_btn.setVisible(False)
            else:
                txt = (ev.get("probe_fail_text") or "").strip() or "Probe misslungen."
                outcome_lab.setText(f"<b style='color:#a12323'>{txt}</b>")
                wound_btn.setVisible(fail_wounds > 0)

        def _roll(mode):
            wp = _wound_penalty_now()
            em = _effect_proben_mod()
            if mode == "3":
                rolls = sorted([random.randint(1, 20) for _ in range(3)])
                die = rolls[1]
                detail = format_roll_info_3w20(rolls, die)
            else:
                die = random.randint(1, 20)
                detail = format_roll_info_1w20(die)
            total = pw + int(die) - wp + em
            ok = total >= target
            verdict = "<b style='color:#2a7a2a'>Erfolg</b>" if ok else "<b style='color:#a12323'>Misserfolg</b>"
            parts = [detail, f"+ PW {pw}"]
            if wp:
                parts.append(f"− {wp} (Einschränkungen)")
            if em:
                parts.append(f"{em:+d} (Effekte)")
            result_lab.setText(
                " ".join(parts) + f" = <b>{total}</b> gegen {target} → {verdict}"
            )
            extra_bits = []
            if wp:
                extra_bits.append(f"−{wp} Einschränkungen")
            if em:
                extra_bits.append(f"{em:+d} Effekte")
            extra_txt = ("  " + "  ".join(extra_bits)) if extra_bits else ""
            meta.setText(f"<b>{kind} {pname}</b>  PW {pw}{extra_txt}  gegen {target}")
            _apply_outcome(ok)

        def _add_wunde():
            n = max(1, fail_wounds)
            try:
                if fail_art == "ersch":
                    for _i in range(n):
                        self.add_erschopfung()
                else:
                    add_wunde_fn(n)
            except Exception:
                pass
            wound_btn.setEnabled(False)
            wound_btn.setText("gesetzt")

        btn1.clicked.connect(lambda: _roll("1"))
        btn3.clicked.connect(lambda: _roll("3"))
        wound_btn.clicked.connect(_add_wunde)

        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        box.rejected.connect(dlg.close)
        box.accepted.connect(dlg.close)
        lay.addWidget(box)
        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()
        if not hasattr(self, "_info_boxes"):
            self._info_boxes = []
        self._info_boxes.append(dlg)

    def _handle_effect_events(self, events):
        for ev in events or []:
            if is_legacy_blutend_event(ev):
                ev = blutend_probe_overlay(ev)
            t = ev.get("type")
            ename = ((ev.get("effect") or {}).get("name")
                     or ev.get("name")
                     or "Effekt")
            if t == "erschöpfung":
                n = max(1, int(ev.get("count", 1) or 1))
                for _i in range(n):
                    self.add_erschopfung()
                self._show_top_info(ename, ev.get("message") or f"„{ename}“ beendet.")
            elif t == "wunde":
                self.add_wunde(int(ev.get("count", 1) or 1))
                self._show_top_info(ename, ev.get("message") or f"„{ename}“ beendet.")
            elif t == "probe":
                self._show_probe_event_dialog(
                    ev, self._resolve_nsc_probe_pw, self.add_wunde
                )
            elif t == "notify":
                self._show_top_info(ename, ev.get("message") or "")
            elif t == "removed":
                if ev.get("message"):
                    self._show_top_info(ename, ev.get("message"))


    def _nsc_ko_pw(self) -> int:
        """NSC speichert Attribut-Wert; PW = 2 x Wert (wie beim Wurf-Button)."""
        try:
            if hasattr(self, "attr_spins") and "KO" in self.attr_spins:
                return int(self.attr_spins["KO"].value()) * 2
        except Exception:
            pass
        try:
            return int((self.data or {}).get("attributes", {}).get("KO", 0) or 0) * 2
        except Exception:
            return 0

    def _nsc_zaehigkeit_pw(self) -> int:
        """PW(T) wenn Talent Zähigkeit vorhanden, sonst PW Selbstbeherrschung."""
        try:
            pw = None
            pwt = None
            has_z = False
            for f in getattr(self, "skills_data", None) or []:
                n = (f.get("name") or "")
                if n == "Selbstbeherrschung":
                    pw = int(f.get("val") or f.get("pw") or 0)
                    pwt = int(f.get("pwt") or f.get("val_t") or f.get("val") or 0)
                if "ähigkeit" in n.lower() or n.lower() == "zahigkeit":
                    has_z = True
                    pwt = int(f.get("val") or f.get("pwt") or 0)
            # Talente in vorteile_list / talents list
            for n in getattr(self, "talents_data", None) or []:
                nn = n.get("name") if isinstance(n, dict) else str(n)
                if nn and "ähigkeit" in nn.lower():
                    has_z = True
            for n in getattr(self, "vorteile_list_data", None) or []:
                pass
            if has_z and pwt is not None:
                return int(pwt)
            if pw is not None:
                return int(pw)
        except Exception:
            pass
        return self._nsc_ko_pw()

    def _nsc_ws_wert(self) -> int:
        try:
            if hasattr(self, "attr_spins") and "WS" in self.attr_spins:
                return max(1, int(self.attr_spins["WS"].value() or 4))
            return max(1, int((self.data or {}).get("attributes", {}).get("WS", 4) or 4))
        except Exception:
            return 4

    def _show_wunden_info_dialog(self):
        parent = self.window() if hasattr(self, "window") else None
        dlg = QDialog(parent)
        dlg.setWindowTitle("Wundregeln & Proben")
        dlg.setMinimumSize(1000, 640)
        dlg.resize(1100, 720)
        root = QHBoxLayout(dlg)

        left = QTextBrowser()
        left.setHtml("""
<h3>Wundschmerz</h3>
<ul>
<li>Bei <b>2+ Einschränkungen auf einen Schlag</b>: sofort <b>KO-Probe (20, I)</b></li>
<li>Jede weitere Einschränkung in diesem Schlag: Schwierigkeit <b>+4</b></li>
<li><b>Misslingen</b> → betäubt; erst wieder in der <b>übernächsten</b> Initiativephase handlungsfähig</li>
</ul>
<h3>Kampfunfähigkeit</h3>
<ul>
<li>Ab <b>4 Einschränkungen</b>: jede weitere droht Kampfunfähigkeit</li>
<li>Kampfunfähig: stürzt, keine Aktionen/Reaktionen</li>
<li>Optional: <b>Zähigkeits-Probe (12, I)</b></li>
<li>Misslingen → +1 Erschöpfung und trotzdem kampfunfähig</li>
</ul>
<h3>Blutungen und Tod</h3>
<ul>
<li>Blutung bei Kampfunfähigkeit durch Waffengewalt o.Ä.</li>
<li><b>KO-Probe (12, I)</b> – Misslingen → Blutung beginnt</li>
<li>Bei 8 Einschränkungen + eine weitere = Tod</li>
</ul>
<h3>Regeneration / Heilkunde</h3>
<ul>
<li>1 Wunde/Nacht oder 1 Erschöpfung/Stunde bei Ruhe ohne schädliche Effekte</li>
<li>Erste Hilfe / heilungsfördernde Maßnahmen (S. 33)</li>
</ul>
<h3>Durchatmen</h3>
<ul>
<li>Einmal zwischen zwei Ruhephasen kannst du eine Aktion <b>Konzentration</b> aufwenden
und eine <b>Zähigkeits-Probe (16)</b> ablegen (3W20, mittlerer Wurf).</li>
<li>Gelingt die Probe, regenerierst du sofort <b>1 Wunde</b> oder <b>2 Erschöpfung</b>,
die du im laufenden Kampf erlitten hast.</li>
</ul>
""")
        root.addWidget(left, 1)

        right = QWidget()
        rv = QVBoxLayout(right)

        def _probe_box(title, pw, target, extra=None):
            box = QGroupBox(title)
            lay = QVBoxLayout(box)
            lay.addWidget(QLabel(f"PW {pw} → Ziel {target} (1W20 + PW + Mod ≥ Ziel)"))
            if extra is not None:
                lay.addWidget(extra)
            row = QHBoxLayout()
            btn = QPushButton("Würfeln")
            res = QLabel("–")
            res.setWordWrap(True)
            row.addWidget(btn)
            row.addWidget(res, 1)
            lay.addLayout(row)
            return box, btn, res

        extra_w = QWidget()
        ew = QHBoxLayout(extra_w)
        ew.setContentsMargins(0, 0, 0, 0)
        ew.addWidget(QLabel("Zus. ab 3. (−4 je):"))
        spin_extra = QSpinBox()
        spin_extra.setRange(0, 6)
        ew.addWidget(spin_extra)
        ew.addStretch()

        ko_pw = self._nsc_ko_pw()
        z_pw = self._nsc_zaehigkeit_pw()
        box1, btn1, res1 = _probe_box("Wundschmerz – KO (20, I)", ko_pw, 20, extra_w)
        btn_fail1 = QPushButton("Misslingen → Handlungsunfähig (1 Runde)")
        box1.layout().addWidget(btn_fail1)
        rv.addWidget(box1)

        box2, btn2, res2 = _probe_box("Kampfunfähigkeit – Zähigkeit (12, I)", z_pw, 12)
        btn_fail2 = QPushButton("Misslingen → +1 Erschöpfung")
        box2.layout().addWidget(btn_fail2)
        rv.addWidget(box2)

        box3, btn3, res3 = _probe_box("Blutung – KO (12, I)", ko_pw, 12)
        btn_fail3 = QPushButton("Misslingen → Blutung beginnt")
        box3.layout().addWidget(btn_fail3)
        rv.addWidget(box3)

        box4 = QGroupBox("Durchatmen – Zähigkeits-Probe (16)")
        lay4 = QVBoxLayout(box4)
        lay4.addWidget(QLabel(
            f"PW {z_pw} → Ziel 16 (3W20 mittlerer Wurf + PW + Mod −Wunden ±Effekte ≥ 16)"
        ))
        row4 = QHBoxLayout()
        btn4 = QPushButton("Würfeln (3W20)")
        res4 = QLabel("–")
        res4.setWordWrap(True)
        row4.addWidget(btn4)
        row4.addWidget(res4, 1)
        lay4.addLayout(row4)
        heal_row = QHBoxLayout()
        btn_heal_w = QPushButton("−1 Wunde")
        btn_heal_w.setToolTip("Nach gelungener Probe: 1 Wunde regenerieren")
        btn_heal_e = QPushButton("−2 Erschöpfung")
        btn_heal_e.setToolTip("Nach gelungener Probe: 2 Erschöpfung regenerieren")
        heal_row.addWidget(btn_heal_w)
        heal_row.addWidget(btn_heal_e)
        heal_row.addStretch()
        lay4.addLayout(heal_row)
        rv.addWidget(box4)
        rv.addStretch()

        def _wound_pen():
            try:
                if hasattr(self, "get_wound_penalty"):
                    return int(self.get_wound_penalty() or 0)
            except Exception:
                pass
            return 0

        def _eff_mod():
            try:
                if hasattr(self, "get_effect_mods"):
                    return int((self.get_effect_mods() or {}).get("proben", 0) or 0)
            except Exception:
                pass
            return 0

        def _roll(pw, target, mod, res_label, *, median3=False):
            wound = _wound_pen()
            em = _eff_mod()
            if median3:
                rolls = sorted([random.randint(1, 20) for _ in range(3)])
                die = rolls[1]
                parts = [f"3W20 [{rolls[0]}, <b>{rolls[1]}</b>, {rolls[2]}] + PW {pw}"]
            else:
                die = random.randint(1, 20)
                parts = [f"1W20 ({die}) + PW {pw}"]
            total = int(pw) + die + int(mod) - wound + em
            ok = total >= int(target)
            color = "#2a7a2a" if ok else "#a12323"
            if mod:
                parts.append(f"{mod:+d} (Mod)")
            if wound:
                parts.append(f"-{wound} (Wunden)")
            if em:
                parts.append(f"{em:+d} (Effekte)")
            res_label.setText(
                " ".join(parts) + f" = <b>{total}</b> gegen {target} → "
                f"<b style='color:{color}'>{'Erfolg' if ok else 'Misserfolg'}</b>"
            )

        def heal_wunde():
            n = self.remove_wunde(1) if hasattr(self, "remove_wunde") else 0
            if hasattr(self, "_show_top_info"):
                self._show_top_info(
                    "Durchatmen",
                    "1 Wunde regeneriert." if n else "Keine Wunde zum Regenerieren vorhanden.",
                )

        def heal_ersch():
            n = self.remove_erschopfung(2) if hasattr(self, "remove_erschopfung") else 0
            if hasattr(self, "_show_top_info"):
                self._show_top_info(
                    "Durchatmen",
                    f"{n} Erschöpfung regeneriert." if n else "Keine Erschöpfung zum Regenerieren vorhanden.",
                )

        btn1.clicked.connect(lambda: _roll(ko_pw, 20, -4 * spin_extra.value(), res1))
        btn2.clicked.connect(lambda: _roll(z_pw, 12, 0, res2))
        btn3.clicked.connect(lambda: _roll(ko_pw, 12, 0, res3))
        btn4.clicked.connect(lambda: _roll(z_pw, 16, 0, res4, median3=True))
        btn_heal_w.clicked.connect(heal_wunde)
        btn_heal_e.clicked.connect(heal_ersch)

        def fail_w():
            effects = [e for e in self._get_effects() if "handlungsunfähig" not in (e.get("name") or "").lower()]
            effects.append(make_handlungsunfaehig_effect(1))
            self._set_effects(effects)
            self._rebuild_effects_ui()

        def fail_z():
            if hasattr(self, "add_erschopfung"):
                self.add_erschopfung()
            elif hasattr(self, "wunde_clicked"):
                # fallback: first free slot as erschopfung
                pass

        def fail_b():
            effects = self._get_effects()
            if not any((e.get("name") or "").lower().startswith("blutend") for e in effects):
                effects.append(make_blutend_effect(self._nsc_ws_wert()))
                self._set_effects(effects)
                self._rebuild_effects_ui()

        btn_fail1.clicked.connect(fail_w)
        btn_fail2.clicked.connect(fail_z)
        btn_fail3.clicked.connect(fail_b)

        root.addWidget(right, 1)
        dlg.setModal(False)
        dlg.show()

    def ensure_atemtechnik_effect(self):
        ko = 0
        if hasattr(self, "attr_spins") and "KO" in self.attr_spins:
            ko = self.attr_spins["KO"].value()
        effects = self._get_effects()
        for e in effects:
            if (e.get("name") or "").lower().startswith("atemtechnik"):
                return
        effects.append(make_atemtechnik_effect(ko))
        self._set_effects(effects)
        self._rebuild_effects_ui()

    def apply_atemtechnik(self, on: bool):
        if getattr(self, "_aktionen_busy", False):
            return
        self._aktionen_busy = True
        try:
            effects = [
                e for e in self._get_effects()
                if not (e.get("name") or "").lower().startswith("atemtechnik")
            ]
            if on:
                ko = 1
                try:
                    if hasattr(self, "attr_spins") and "KO" in self.attr_spins:
                        ko = max(1, int(self.attr_spins["KO"].value() or 1))
                except RuntimeError:
                    ko = 1
                effects.append(make_atemtechnik_effect(ko))
            self._set_effects(effects)
            try:
                self._rebuild_effects_ui()
            except RuntimeError:
                pass
        finally:
            self._aktionen_busy = False

    def _has_active_atemtechnik(self):
        for e in self._get_effects():
            if (e.get("name") or "").lower().startswith("atemtechnik"):
                return True
        return False

    def _has_active_volle(self, kind: str) -> bool:
        prefix = "volle offensive" if kind == "off" else "volle defensive"
        for e in self._get_effects():
            if (e.get("name") or "").lower().startswith(prefix):
                return True
        return False

    def _remove_volle_effects(self, kind=None):
        effects = self._get_effects()
        kept = []
        for e in effects:
            n = (e.get("name") or "").lower()
            if kind in (None, "off") and n.startswith("volle offensive"):
                continue
            if kind in (None, "def") and n.startswith("volle defensive"):
                continue
            kept.append(e)
        self._set_effects(kept)
        self._rebuild_effects_ui()

    def apply_volle_offensive(self, on: bool):
        if getattr(self, "_aktionen_busy", False):
            return
        self._aktionen_busy = True
        try:
            effects = [e for e in self._get_effects() if not is_volle_kampfhaltung(e)]
            if on:
                has_ok = _has_named_vorteil(self._nsc_vorteil_names(), "Offensiver Kampfstil")
                effects.append(make_volle_offensive_effect(has_ok))
            self._set_effects(effects)
            try:
                self._rebuild_effects_ui()
            except RuntimeError:
                pass
            # Manöver-Liste neu: Sturm/Überrennen aus- bzw. wieder einblenden
            ref = getattr(self, "_plugin_ref", None)
            if ref is not None and hasattr(ref, "_refresh_manöver_after_volle"):
                ref._refresh_manöver_after_volle()
        finally:
            self._aktionen_busy = False

    def apply_volle_defensive(self, on: bool):
        if getattr(self, "_aktionen_busy", False):
            return
        self._aktionen_busy = True
        try:
            effects = [e for e in self._get_effects() if not is_volle_kampfhaltung(e)]
            if on:
                has_dk = _has_named_vorteil(self._nsc_vorteil_names(), "Defensiver Kampfstil")
                effects.append(make_volle_defensive_effect(has_dk))
            self._set_effects(effects)
            try:
                self._rebuild_effects_ui()
            except RuntimeError:
                pass
            ref = getattr(self, "_plugin_ref", None)
            if ref is not None:
                if hasattr(ref, "_set_zweite_einfache_checks"):
                    ref._set_zweite_einfache_checks(bool(on))
                if hasattr(ref, "_refresh_manöver_after_volle"):
                    ref._refresh_manöver_after_volle()
        finally:
            self._aktionen_busy = False

    def decrement_all_effects(self):
        new_list, events = tick_effects(self._get_effects())
        self._set_effects(new_list)
        self._rebuild_effects_ui()
        self._handle_effect_events(events)
        try:
            ref = getattr(self, "_plugin_ref", None)
            if ref is not None and hasattr(ref, "_refresh_aktionen_from_widget"):
                ref._refresh_aktionen_from_widget(self)
        except Exception:
            pass

    def load_data(self):
        # WICHTIG: Flag setzen, damit changed() nicht feuert und unvollständige Daten speichert
        was_loading = self.isLoading
        self.isLoading = True
        try:
            self.edit_name.setText(self.data.get("name", "Neuer SC"))
            self.text_notes.setPlainText(self.data.get("notizen", ""))
            self.check_roll_all.setChecked(self.data.get("alle_wuerfeln", False))
            self.check_ignore_wounds.setChecked(self.data.get("wunden_ignorieren", False))
            
            self.spin_ini.setValue(self.data.get("val_ini", 0))
            if self.show_ini_header:
                self.header_ini_spin.blockSignals(True)
                self.header_ini_spin.setValue(self.data.get("val_ini", 0))
                self.header_ini_spin.blockSignals(False)
                self.btn_ko.setChecked(self.data.get("ko", False))
                if self.reaktion_spin is not None:
                    self.reaktion_spin.blockSignals(True)
                    self.reaktion_spin.setValue(int(self.data.get("reaktionen", 0) or 0))
                    self.reaktion_spin.blockSignals(False)
                    self._update_reaktion_label()

            self.spin_mr.setValue(self.data.get("val_mr", 0))
            self.spin_in.setValue(self.data.get("val_in", 0))
            self.spin_wachsamkeit.setValue(self.data.get("val_wachsamkeit", 0))
            self.spin_menschenkenntnis.setValue(self.data.get("val_menschenkenntnis", 0))

            wunden = self.data.get("wunden", [None]*8)
            self.update_wound_buttons(wunden)
            
            self._effects_data = normalize_list(self.data.get("effekte", []))
            self.data["effekte"] = self._effects_data
            self._rebuild_effects_ui()
            self.update_style()
        finally:
            if not was_loading:
                self.isLoading = False

    def update_wound_buttons(self, wunden):
        for i, state in enumerate(wunden):
            btn = self.wunden_buttons[i]
            if state == "X": 
                btn.setText("X"); btn.setStyleSheet("background-color: #a12323; color: white; font-weight: bold;")
            elif state == "/": 
                btn.setText("/"); btn.setStyleSheet("background-color: #236fa1; color: white; font-weight: bold;")
            else: 
                btn.setText(""); btn.setStyleSheet("")

    def changed(self):
        if getattr(self, "isLoading", False):
            return
        try:
            self.save_data()
        except RuntimeError:
            pass
        try:
            self.dataChanged.emit()
        except RuntimeError:
            pass

    def save_data(self):
        self.data["effekte"] = normalize_list(getattr(self, "_effects_data", None) or self.data.get("effekte", []))
        # Guard: Widget kann nach deleteLater / INI-Rebuild bereits tot sein
        try:
            self.data["name"] = self.edit_name.text()
            self.data["notizen"] = self.text_notes.toPlainText()
            self.data["alle_wuerfeln"] = self.check_roll_all.isChecked()
            self.data["wunden_ignorieren"] = self.check_ignore_wounds.isChecked()
            self.data["val_ini"] = self.spin_ini.value()
            self.data["val_mr"] = self.spin_mr.value()
            self.data["val_in"] = self.spin_in.value()
            self.data["val_wachsamkeit"] = self.spin_wachsamkeit.value()
            self.data["val_menschenkenntnis"] = self.spin_menschenkenntnis.value()
            if self.show_ini_header:
                self.data["ko"] = self.btn_ko.isChecked()
                if self.reaktion_spin is not None:
                    self.data["reaktionen"] = int(self.reaktion_spin.value())
        except RuntimeError:
            # C++-Objekte schon gelöscht – Daten in self.data bleiben unangetastet
            pass

    def wunde_clicked(self, index):
        wunden = self.data.get("wunden", [None]*8)
        current = wunden[index]
        new_val = None
        if current is None: new_val = "/"
        elif current == "/": new_val = "X"
        else: new_val = None
        
        wunden[index] = new_val
        wunden.sort(key=lambda x: (x is None, x != 'X'))
        
        self.data["wunden"] = wunden
        self.update_wound_buttons(wunden)
        self.changed()
    
    # --- New Methods for INI Header Sync ---
    def on_reaktion_changed(self, val):
        if getattr(self, "isLoading", False):
            return
        self.data["reaktionen"] = int(val)
        self._update_reaktion_label()
        self.changed()

    def _update_reaktion_label(self):
        if not getattr(self, "reaktion_malus_label", None):
            return
        n = int(self.data.get("reaktionen", 0) or 0)
        malus = -4 * n
        if malus == 0:
            self.reaktion_malus_label.setText("VT ±0")
            self.reaktion_malus_label.setStyleSheet("color: #666; min-width: 42px;")
        else:
            self.reaktion_malus_label.setText(f"VT {malus}")
            self.reaktion_malus_label.setStyleSheet("color: #a12323; font-weight: bold; min-width: 42px;")

    def get_reaktion_malus(self):
        """Malus für die nächste Reaktion (–4 × bereits verbrauchte Reaktionen)."""
        return -4 * int(self.data.get("reaktionen", 0) or 0)

    def increment_reaktion(self):
        """Nach einer Reaktion: Zähler +1."""
        n = int(self.data.get("reaktionen", 0) or 0) + 1
        self.data["reaktionen"] = n
        if self.reaktion_spin is not None:
            self.reaktion_spin.blockSignals(True)
            self.reaktion_spin.setValue(n)
            self.reaktion_spin.blockSignals(False)
        self._update_reaktion_label()
        self.changed()

    def reset_reaktionen(self):
        """Zu Beginn der eigenen INI-Phase."""
        self.data["reaktionen"] = 0
        if self.reaktion_spin is not None:
            self.reaktion_spin.blockSignals(True)
            self.reaktion_spin.setValue(0)
            self.reaktion_spin.blockSignals(False)
        self._update_reaktion_label()
        self.changed()

    def on_header_ini_changed(self, val):
        self.spin_ini.setValue(val) # Triggered change via spin_ini -> save_data
    
    def sync_ini_spin(self, val):
        if self.show_ini_header:
            self.header_ini_spin.blockSignals(True)
            self.header_ini_spin.setValue(val)
            self.header_ini_spin.blockSignals(False)

    def on_ko_toggled(self):
        self.data["ko"] = self.btn_ko.isChecked()
        self.update_style()
        self.dataChanged.emit()

    def update_style(self):
        if not self.show_ini_header: return
        
        active = self.data.get("active", False)
        ko = self.data.get("ko", False)
        
        style = "QFrame#scHeader { border-radius: 4px; border: 2px solid "
        
        if ko:
            style += "#a12323; background-color: rgba(161, 35, 35, 30); }" # Rot
        elif active:
            style += "#23a12b; background-color: rgba(35, 161, 43, 30); }" # Grün
        else:
            style += "rgba(128, 128, 128, 50); background-color: rgba(128, 128, 128, 30); }" # Grau
            
        self.header_frame.setStyleSheet(style)


class NSCWidget(SCWidget):
    tpRollRequested = Signal(object, str, str)  # Widget, Name, TP-String
    atRollRequested = Signal(object, str, int, str)  # Widget, Name, AT-Wert, TP-String

    def _init_ui(self):
        super()._init_ui()
        self.attr_spins = {}
        self.skill_widgets = []
        self.power_widgets = []
        self.combat_widgets = []
        self.vorteile_edit = None
        
        # 1. Freies Würfeln
        self.free_roll_frame = QFrame()
        fr_layout = QVBoxLayout(self.free_roll_frame)
        fr_layout.setContentsMargins(0, 0, 0, 5)
        
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0,0,0,0)
        self.fr_line = QLineEdit()
        self.fr_line.setPlaceholderText("Freier Wurf (z.B. 2W6+4)")
        self.fr_line.returnPressed.connect(self.trigger_free_roll)
        self.fr_btn = QPushButton("🎲")
        self.fr_btn.setFixedWidth(30)
        self.fr_btn.clicked.connect(self.trigger_free_roll)
        input_layout.addWidget(QLabel("Würfeln:"))
        input_layout.addWidget(self.fr_line)
        input_layout.addWidget(self.fr_btn)
        fr_layout.addWidget(input_container)
        
        self.label_free_roll_result = QLabel("")
        self.label_free_roll_result.setWordWrap(True)
        self.label_free_roll_result.setStyleSheet("color: #333; font-style: italic; margin-left: 50px;")
        fr_layout.addWidget(self.label_free_roll_result)

        self.content_layout.insertWidget(0, self.free_roll_frame)

        # 2. Koloss Modus
        self.combo_wunden_modus = QComboBox()
        self.combo_wunden_modus.addItems(["Normal", "Koloss I", "Koloss II"])
        self.combo_wunden_modus.currentIndexChanged.connect(lambda: self.update_wunden_modus())
        self.wunden_layout.insertWidget(0, self.combo_wunden_modus)

        # 3. Alte "Werte"-Box entfernen
        self.werte_box.hide() 

        # 4. Tabs hinzufügen
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        
        self._init_attribute_tab()
        self._init_fertigkeiten_tab()
        self._init_uebernatuerliches_tab()
        self._init_kampf_tab()
        self._init_vorteile_tab()
        
        # Insert Tabs before Checkbox
        self.content_layout.insertWidget(self.content_layout.count()-1, self.tabs)
        
        # NEU: Checkbox für NSCs ausblenden
        self.check_roll_all.setVisible(False)

    def _init_attribute_tab(self):
        tab = QWidget()
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(4, 4, 4, 4)

        # Alles eng nach links – kein Zeilen-Verdrehen
        left = QWidget()
        layout = QGridLayout(left)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(6)
        layout.setVerticalSpacing(2)
        layout.setColumnStretch(4, 1)  # Rest rechts leer

        layout.addWidget(QLabel("<b>Attr</b>"), 0, 0)
        layout.addWidget(QLabel("<b>Wert</b>"), 0, 1)
        layout.addWidget(QLabel("<b>PW</b>"), 0, 2)
        layout.addWidget(QLabel(""), 0, 3)

        attrs = ["MU", "KL", "IN", "CH", "FF", "GE", "KO", "KK"]
        self.attr_pw_labels = {}
        row = 1
        for a in attrs:
            lab = QLabel(f"<b>{a}</b>")
            lab.setFixedWidth(28)
            layout.addWidget(lab, row, 0)
            spin = QSpinBox()
            spin.setRange(0, 25)
            spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
            spin.setFixedWidth(52)
            spin.setToolTip(f"Attributwert (Wert). PW = 2 × Wert.")
            spin.valueChanged.connect(lambda val, name=a: self._on_attr_wert_changed(name, val))
            layout.addWidget(spin, row, 1)

            pw_label = QLabel("0")
            pw_label.setFixedWidth(28)
            layout.addWidget(pw_label, row, 2)
            self.attr_pw_labels[a] = pw_label

            btn = QPushButton("🎲")
            btn.setFixedWidth(28)
            btn.setFlat(True)
            btn.clicked.connect(lambda checked=False, name=a, s=spin: self.trigger_roll(name, s.value() * 2))
            layout.addWidget(btn, row, 3)

            self.attr_spins[a] = spin
            row += 1

        # Abgeleitete Werte (ohne WS* – kommt aus Rüstung)
        sep = QLabel("<b>Abgeleitet</b>")
        layout.addWidget(sep, row, 0, 1, 4)
        row += 1
        for a, tip in [
            ("INI", "Initiative"),
            ("MR", "Magieresistenz"),
            ("GS", "Geschwindigkeit (Basis, vor BE)"),
            ("WS", "Wundschwelle (ohne Rüstung)"),
        ]:
            lab = QLabel(f"<b>{a}</b>")
            lab.setFixedWidth(28)
            layout.addWidget(lab, row, 0)
            spin = QSpinBox()
            spin.setRange(0, 200)
            spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            spin.setFixedWidth(52)
            spin.setToolTip(tip)
            spin.valueChanged.connect(lambda *args: self.changed())
            if a == "INI":
                spin.valueChanged.connect(self.sync_ini_spin)
                self.spin_ini = spin
            if a in ("GS", "WS"):
                spin.valueChanged.connect(lambda *a: self._update_kampf_derived())
            layout.addWidget(spin, row, 1)
            if a == "MR":
                btn = QPushButton("🎲")
                btn.setFixedWidth(28)
                btn.setFlat(True)
                btn.clicked.connect(lambda checked=False, name=a, s=spin: self.trigger_roll(name, s.value()))
                layout.addWidget(btn, row, 3)
            self.attr_spins[a] = spin
            row += 1

        layout.setRowStretch(row, 1)
        outer.addWidget(left)
        outer.addStretch(1)
        self.tabs.addTab(tab, "Attribute")

    def _on_attr_wert_changed(self, name, val):
        if name in getattr(self, "attr_pw_labels", {}):
            self.attr_pw_labels[name].setText(str(int(val) * 2))
        if not getattr(self, "isLoading", False):
            self.changed()

    def _init_fertigkeiten_tab(self):
        wrapper = QWidget()
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(4, 4, 4, 4)

        self.skills_tree = QTreeWidget()
        self.skills_tree.setColumnCount(3)
        self.skills_tree.setHeaderLabels(["Fertigkeit", "PW", ""])
        self.skills_tree.setAlternatingRowColors(True)
        self.skills_tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.skills_tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.skills_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.skills_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.skills_tree.header().resizeSection(1, 70)
        self.skills_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.skills_tree.header().resizeSection(2, 40)
        self.skills_tree.setRootIsDecorated(True)
        wl.addWidget(self.skills_tree)

        # Intern: Liste der Fertigkeiten {name, val}
        self.skills_data = []

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Fertigkeit aus DB…")
        add_btn.clicked.connect(self.open_skill_selector)
        del_btn = QPushButton("Entfernen")
        del_btn.clicked.connect(self.remove_selected_skill)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        wl.addLayout(btn_row)

        # Legacy-Listen leer halten (falls andere Code-Pfade zugreifen)
        self.skill_widgets = []
        self.skill_layout = QVBoxLayout()
        self.skill_container = QWidget()

        self.tabs.addTab(wrapper, "Fertigkeiten")

    def open_skill_selector(self):
        """Fertigkeit aus Wolke.DB übernehmen (Suche + Kategorien wie Waffen/Übernatürliches)."""
        already = {s["name"] for s in (self.skills_data or [])}
        try:
            has_db = hasattr(Wolke, "DB") and Wolke.DB and getattr(Wolke.DB, "fertigkeiten", None)
        except Exception:
            has_db = False
        if not has_db:
            name, ok = QInputDialog.getText(self, "Fertigkeit", "Name:")
            if ok and name.strip():
                self._add_skill_entry(name.strip(), 0)
            return
        dlg = FertigkeitSelector(self, already=already)
        if dlg.exec() == QDialog.Accepted:
            name = dlg.get_selected()
            if name:
                self._add_skill_entry(name, 0)

    def _add_skill_entry(self, name, val):
        if any(s["name"] == name for s in self.skills_data):
            return
        self.skills_data.append({"name": name, "val": int(val)})
        self._rebuild_skills_tree()
        self.changed()

    def remove_selected_skill(self):
        item = self.skills_tree.currentItem()
        if not item:
            return
        # Nur echte Fertigkeiten entfernen (UserRole gesetzt), keine Kategorien/Talente
        name = item.data(0, Qt.ItemDataRole.UserRole)
        if not name:
            return
        self.skills_data = [s for s in self.skills_data if s["name"] != name]
        self._rebuild_skills_tree()
        self.changed()

    def _talents_for_skill(self, skill_name):
        """Alle Talente aus der DB, die zu dieser Fertigkeit gehören (alphabetisch)."""
        result = []
        try:
            if not (hasattr(Wolke, "DB") and Wolke.DB and hasattr(Wolke.DB, "talente")):
                return result
            for t_name, t_def in Wolke.DB.talente.items():
                ferts = getattr(t_def, "fertigkeiten", None) or []
                if isinstance(ferts, str):
                    ferts = [f.strip() for f in ferts.split(",") if f.strip()]
                if skill_name in ferts:
                    result.append(t_name)
        except Exception:
            pass
        return sorted(result)

    def _rebuild_skills_tree(self):
        tree = self.skills_tree
        tree.clear()

        # Kategorien wie im Dice-Plugin: korrekte Namen + Sortierung
        try:
            kategorien = Wolke.DB.einstellungen["Fertigkeiten: Kategorien profan"].wert.copy()
        except Exception:
            kategorien = {}
        fertigkeiten_by_kategorie = SortedCategoryToListDict(kategorien)

        name_to_skill = {s["name"]: s for s in self.skills_data}
        sonstige = []
        for s in self.skills_data:
            kat_key = None
            try:
                if hasattr(Wolke, "DB") and Wolke.DB and s["name"] in Wolke.DB.fertigkeiten:
                    fert_def = Wolke.DB.fertigkeiten[s["name"]]
                    kat_key = getattr(fert_def, "kategorie", None)
            except Exception:
                pass
            if kat_key is None:
                sonstige.append(s["name"])
            else:
                fertigkeiten_by_kategorie.append(kat_key, s["name"])
        fertigkeiten_by_kategorie.sortValues()

        font_header = QFont()
        try:
            font_header = QFont(Wolke.Settings["Font"], Wolke.FontHeadingSizeL3)
        except Exception:
            pass
        font_header.setBold(True)
        font_header.setCapitalization(QFont.Capitalization.SmallCaps)

        def _add_skill_item(parent, s):
            child = QTreeWidgetItem(parent, [s["name"], "", ""])
            child.setData(0, Qt.ItemDataRole.UserRole, s["name"])

            pw_w = QWidget()
            hl = QHBoxLayout(pw_w)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setSpacing(2)
            spin = QSpinBox()
            spin.setRange(0, 99)
            spin.setValue(int(s["val"]))
            spin.setFixedWidth(48)
            spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            spin.valueChanged.connect(partial(self._on_skill_pw_changed, s["name"]))
            btn = QPushButton("🎲")
            btn.setFixedWidth(28)
            btn.setFlat(True)
            btn.clicked.connect(partial(self._roll_skill, s["name"]))
            hl.addWidget(spin)
            hl.addWidget(btn)
            tree.setItemWidget(child, 1, pw_w)
            s["_spin"] = spin

            # Zugehörige Talente (wie Dice-Plugin, aber alle aus der DB)
            talents = self._talents_for_skill(s["name"])
            if talents:
                child.setExpanded(False)
                for talent_name in talents:
                    talent_item = QTreeWidgetItem(child)
                    talent_button = QPushButton(f"- {talent_name}")
                    talent_button.setFlat(True)
                    talent_button.setStyleSheet(
                        "text-align: left; border: none; background-color: transparent; "
                        "padding-left: 10px; font-style: italic;"
                    )
                    talent_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                    talent_button.clicked.connect(
                        partial(self.show_talent_info, talent_name)
                    )
                    tree.setItemWidget(talent_item, 0, talent_button)
                    talent_item.setFlags(talent_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

        for kategorie_name, fert_names in fertigkeiten_by_kategorie.items():
            if not fert_names:
                continue
            parent = QTreeWidgetItem(tree, [kategorie_name, "", ""])
            parent.setFont(0, font_header)
            parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            for fert_name in fert_names:
                s = name_to_skill.get(fert_name)
                if s:
                    _add_skill_item(parent, s)
            parent.setExpanded(True)

        if sonstige:
            parent = QTreeWidgetItem(tree, ["Sonstige", "", ""])
            parent.setFont(0, font_header)
            parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            for fert_name in sorted(sonstige):
                s = name_to_skill.get(fert_name)
                if s:
                    _add_skill_item(parent, s)
            parent.setExpanded(True)

    def _on_skill_pw_changed(self, name, val):
        for s in self.skills_data:
            if s["name"] == name:
                s["val"] = int(val)
                break
        if not getattr(self, "isLoading", False):
            self.changed()

    def _roll_skill(self, name):
        val = 0
        for s in self.skills_data:
            if s["name"] == name:
                val = int(s["val"])
                break
        self.trigger_roll(name, val)

    def _init_uebernatuerliches_tab(self):
        wrapper = QWidget()
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(4, 4, 4, 4)

        # --- Energien (wie Dice Plugin) ---
        energie_box = QGroupBox("Energien")
        energie_layout = QFormLayout(energie_box)

        asp_row = QHBoxLayout()
        asp_row.setContentsMargins(0, 0, 0, 0)
        asp_row.addWidget(QLabel("Max:"))
        self.spin_asp_max = QSpinBox()
        self.spin_asp_max.setRange(0, 999)
        self.spin_asp_max.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.spin_asp_max.setFixedWidth(60)
        self.spin_asp_max.valueChanged.connect(self._on_asp_max_changed)
        asp_row.addWidget(self.spin_asp_max)
        asp_row.addSpacing(12)
        asp_row.addWidget(QLabel("Aktuell:"))
        self.spin_asp = QSpinBox()
        self.spin_asp.setRange(0, 999)
        self.spin_asp.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.spin_asp.setFixedWidth(60)
        self.spin_asp.valueChanged.connect(lambda *a: self.changed())
        asp_row.addWidget(self.spin_asp)
        asp_row.addStretch()
        energie_layout.addRow("Astralenergie (AsP):", asp_row)

        kap_row = QHBoxLayout()
        kap_row.setContentsMargins(0, 0, 0, 0)
        kap_row.addWidget(QLabel("Max:"))
        self.spin_kap_max = QSpinBox()
        self.spin_kap_max.setRange(0, 999)
        self.spin_kap_max.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.spin_kap_max.setFixedWidth(60)
        self.spin_kap_max.valueChanged.connect(self._on_kap_max_changed)
        kap_row.addWidget(self.spin_kap_max)
        kap_row.addSpacing(12)
        kap_row.addWidget(QLabel("Aktuell:"))
        self.spin_kap = QSpinBox()
        self.spin_kap.setRange(0, 999)
        self.spin_kap.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.spin_kap.setFixedWidth(60)
        self.spin_kap.valueChanged.connect(lambda *a: self.changed())
        kap_row.addWidget(self.spin_kap)
        kap_row.addStretch()
        energie_layout.addRow("Karmaenergie (KaP):", kap_row)
        wl.addWidget(energie_box)

        # --- Talent-/Fertigkeiten-Baum ---
        self.powers_tree = QTreeWidget()
        self.powers_tree.setColumnCount(2)
        self.powers_tree.setHeaderLabels(["Talent", "PW"])
        self.powers_tree.setAlternatingRowColors(True)
        self.powers_tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.powers_tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.powers_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.powers_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.powers_tree.header().resizeSection(1, 90)
        self.powers_tree.setRootIsDecorated(True)
        wl.addWidget(self.powers_tree)

        self.powers_data = []  # [{name, val}]
        self.power_widgets = []  # legacy
        self.power_layout = QVBoxLayout()
        self.power_container = QWidget()

        btn_row = QHBoxLayout()
        add_talent = QPushButton("+ Talent aus DB…")
        add_talent.clicked.connect(self.open_power_selector)
        del_btn = QPushButton("Entfernen")
        del_btn.clicked.connect(self.remove_selected_power)
        btn_row.addWidget(add_talent)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        wl.addLayout(btn_row)

        self.tabs.addTab(wrapper, "Übernatürliches")

    def _on_asp_max_changed(self, val):
        self.spin_asp.setMaximum(max(val, 0))
        if self.spin_asp.value() > val:
            self.spin_asp.setValue(val)
        if not getattr(self, "isLoading", False):
            self.changed()

    def _on_kap_max_changed(self, val):
        self.spin_kap.setMaximum(max(val, 0))
        if self.spin_kap.value() > val:
            self.spin_kap.setValue(val)
        if not getattr(self, "isLoading", False):
            self.changed()

    def open_power_selector(self):
        dlg = TalentSelector(self)
        if dlg.exec() == QDialog.Accepted:
            selected = dlg.get_selected_talent()
            if selected:
                self._add_power_entry(selected, 0)

    def open_ueber_fert_selector(self):
        names = []
        try:
            if hasattr(Wolke, "DB") and Wolke.DB:
                if hasattr(Wolke.DB, "übernatürlicheFertigkeiten"):
                    names = sorted(Wolke.DB.übernatürlicheFertigkeiten.keys())
                if not names and hasattr(Wolke.DB, "fertigkeiten"):
                    # Fallback: übernatürliche Kategorien
                    try:
                        cats = set(Wolke.DB.einstellungen["Fertigkeiten: Kategorien übernatürlich"].wert.keys())
                        for n, f in Wolke.DB.fertigkeiten.items():
                            if getattr(f, "kategorie", None) in cats:
                                names.append(n)
                        names = sorted(set(names))
                    except Exception:
                        pass
        except Exception:
            names = []
        if not names:
            name, ok = QInputDialog.getText(self, "Übernatürliche Fertigkeit", "Name:")
            if ok and name.strip():
                self._add_power_entry(name.strip(), 0)
            return
        name, ok = QInputDialog.getItem(self, "Übernatürliche Fertigkeit", "Fertigkeit:", names, 0, True)
        if ok and name:
            self._add_power_entry(name, 0)

    def _add_power_entry(self, name, val):
        if any(p["name"] == name for p in self.powers_data):
            return
        self.powers_data.append({"name": name, "val": int(val)})
        self._rebuild_powers_tree()
        self.changed()

    def remove_selected_power(self):
        item = self.powers_tree.currentItem()
        if not item or item.parent() is None:
            return
        name = item.data(0, Qt.ItemDataRole.UserRole) or item.text(0)
        self.powers_data = [p for p in self.powers_data if p["name"] != name]
        self._rebuild_powers_tree()
        self.changed()

    def _ueber_kat_ordered_names(self):
        try:
            cats = Wolke.DB.einstellungen["Fertigkeiten: Kategorien übernatürlich"].wert
            if isinstance(cats, dict) and cats:
                return sorted(
                    cats.keys(),
                    key=lambda k: int(cats[k]) if str(cats[k]).isdigit() else str(cats[k]),
                )
        except Exception:
            pass
        return list(_UEBER_KAT_ORDER)

    def _kategorie_for_power_name(self, name):
        """Auflösung: Allgemeine Zauber / Traditionszauber / … für ein Talent oder eine Fertigkeit."""
        ordered = self._ueber_kat_ordered_names()
        try:
            if not (hasattr(Wolke, "DB") and Wolke.DB):
                return "Sonstige"

            def kat_id_to_name(kat_id):
                if kat_id is None:
                    return None
                if str(kat_id).isdigit():
                    idx = int(kat_id)
                    if 0 <= idx < len(ordered):
                        return ordered[idx]
                if kat_id in ordered:
                    return kat_id
                if str(kat_id) in ordered:
                    return str(kat_id)
                return None

            if hasattr(Wolke.DB, "talente") and name in Wolke.DB.talente:
                tdef = Wolke.DB.talente[name]
                ferts = getattr(tdef, "fertigkeiten", None) or []
                if isinstance(ferts, str):
                    ferts = [f.strip() for f in ferts.split(",") if f.strip()]
                best_idx, best_name = 999, None
                ueber = getattr(Wolke.DB, "übernatürlicheFertigkeiten", {}) or {}
                for f in ferts:
                    if f not in ueber:
                        continue
                    kn = kat_id_to_name(getattr(ueber[f], "kategorie", None))
                    if not kn:
                        continue
                    try:
                        idx = ordered.index(kn)
                    except ValueError:
                        idx = 500
                    if idx < best_idx:
                        best_idx, best_name = idx, kn
                if best_name:
                    return best_name
                return "Talente"

            if hasattr(Wolke.DB, "übernatürlicheFertigkeiten") and name in Wolke.DB.übernatürlicheFertigkeiten:
                fdef = Wolke.DB.übernatürlicheFertigkeiten[name]
                return kat_id_to_name(getattr(fdef, "kategorie", None)) or "Sonstige"
        except Exception:
            pass
        return "Sonstige"

    def _rebuild_powers_tree(self):
        tree = self.powers_tree
        tree.clear()
        ordered = self._ueber_kat_ordered_names()
        by_kat = {k: [] for k in ordered}
        by_kat["Talente"] = []
        by_kat["Sonstige"] = []

        for p in self.powers_data:
            kat = self._kategorie_for_power_name(p["name"])
            if kat not in by_kat:
                kat = "Sonstige"
            by_kat[kat].append(p)

        font = QFont()
        try:
            font = QFont(Wolke.Settings["Font"], Wolke.FontHeadingSizeL3)
        except Exception:
            pass
        font.setBold(True)
        font.setCapitalization(QFont.Capitalization.SmallCaps)

        for kat in list(ordered) + ["Talente", "Sonstige"]:
            entries = by_kat.get(kat) or []
            if not entries:
                continue
            parent = QTreeWidgetItem(tree, [kat, ""])
            parent.setFont(0, font)
            parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            for p in sorted(entries, key=lambda x: x["name"]):
                child = QTreeWidgetItem(parent, [p["name"], ""])
                child.setData(0, Qt.ItemDataRole.UserRole, p["name"])

                pw_w = QWidget()
                hl = QHBoxLayout(pw_w)
                hl.setContentsMargins(0, 0, 0, 0)
                hl.setSpacing(2)
                spin = QSpinBox()
                spin.setRange(0, 99)
                spin.setValue(int(p["val"]))
                spin.setFixedWidth(48)
                spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
                spin.valueChanged.connect(partial(self._on_power_pw_changed, p["name"]))
                btn = QPushButton("🎲")
                btn.setFixedWidth(28)
                btn.setFlat(True)
                btn.clicked.connect(partial(self._roll_power, p["name"]))
                info = QPushButton("i")
                info.setFixedWidth(22)
                info.setFlat(True)
                info.clicked.connect(partial(self.show_talent_info, p["name"]))
                hl.addWidget(spin)
                hl.addWidget(btn)
                hl.addWidget(info)
                tree.setItemWidget(child, 1, pw_w)
                p["_spin"] = spin
            parent.setExpanded(True)

    def _on_power_pw_changed(self, name, val):
        for p in self.powers_data:
            if p["name"] == name:
                p["val"] = int(val)
                break
        if not getattr(self, "isLoading", False):
            self.changed()

    def _roll_power(self, name):
        val = 0
        for p in self.powers_data:
            if p["name"] == name:
                val = int(p["val"])
                break
        self.trigger_roll(name, val)

    def show_talent_info(self, name):
        if not name or not TalentInfoDialog:
            return
        dlg = TalentInfoDialog(name, self)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()
        if not hasattr(self, "_talent_dialogs"):
            self._talent_dialogs = []
        self._talent_dialogs = [d for d in self._talent_dialogs if d is not None]
        self._talent_dialogs.append(dlg)

    def show_weapon_info(self, name, info_text="", eigenschaften="", on_save=None):
        """Zeigt DB-/Eigenschafts-Info und erlaubt eigenen Infotext."""
        dlg = WeaponCustomInfoDialog(name or "", info_text or "", eigenschaften or "", self)
        if dlg.exec() == QDialog.Accepted:
            if callable(on_save):
                on_save(dlg.info_text())
            return dlg.info_text()
        return None

    def open_weapon_eigenschaft_dialog(self, current_text=""):
        dlg = WeaponEigenschaftDialog(current_text or "", self)
        if dlg.exec() == QDialog.Accepted:
            return dlg.selected_text()
        return None

    def open_weapon_selector(self, name_widget, tp_widget):
        self.open_weapon_selector_full(name_widget, tp_widget, tp_widget, None, None, None)

    def open_weapon_selector_full(self, name_widget, tp_base_widget, tp_widget,
                                   rw_spin=None, wm_lz_ed=None, eig_widget=None):
        dlg = WeaponSelector(self)
        if dlg.exec() == QDialog.Accepted:
            selected_name = dlg.get_selected_weapon()
            if selected_name and selected_name in Wolke.DB.waffen:
                w = Wolke.DB.waffen[selected_name]
                name_widget.setText(selected_name)
                tp = f"{w.würfel}W{w.würfelSeiten}"
                if w.plus > 0:
                    tp += f"+{w.plus}"
                elif w.plus < 0:
                    tp += f"{w.plus}"
                if tp_base_widget is not None:
                    tp_base_widget.setText(tp)
                if tp_widget is not None:
                    tp_widget.setText(tp)
                if rw_spin is not None:
                    try:
                        rw_spin.setValue(int(getattr(w, "rw", 0) or 0))
                    except Exception:
                        pass
                if wm_lz_ed is not None:
                    try:
                        wm_lz_ed.setText(("%s/%s" % (int(getattr(w, "wm", 0) or 0), int(getattr(w, "lz", 0) or 0))) if int(getattr(w, "lz", 0) or 0) else str(int(getattr(w, "wm", 0) or 0)))
                    except Exception:
                        pass
                if eig_widget is not None:
                    eig = getattr(w, "eigenschaften", None) or []
                    if isinstance(eig, (list, tuple)):
                        eig_widget.setText(", ".join(str(x) for x in eig))
                    else:
                        eig_widget.setText(str(eig))
                self.changed()

    def _add_eigene_waffe(self):
        """Eigene Waffe: zuerst NK/FK fragen, dann Editor für Eigenschaften."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Eigene Waffe")
        msg.setText("Ist die neue Waffe eine Nahkampf- oder Fernkampfwaffe?")
        msg.setInformativeText(
            "Der Typ steuert Manöver und Kampf-Modifikatoren.\n"
            "Weitere Eigenschaften legst du danach fest."
        )
        btn_nk = msg.addButton("Nahkampf", QMessageBox.ButtonRole.AcceptRole)
        btn_fk = msg.addButton("Fernkampf", QMessageBox.ButtonRole.AcceptRole)
        btn_cancel = msg.addButton(QMessageBox.StandardButton.Cancel)
        msg.exec()
        clicked = msg.clickedButton()
        if clicked is None or clicked == btn_cancel:
            return
        is_fk = clicked == btn_fk
        self.add_list_item("combat", {
            "name": "",
            "eigenschaften": "",
            "fernkampf": bool(is_fk),
        })
        if not self.combat_widgets:
            return
        entry = self.combat_widgets[-1]
        entry["fernkampf"] = bool(is_fk)
        try:
            lab = entry.get("typ_lab")
            if lab is not None:
                lab.setText("FK" if is_fk else "NK")
                lab.setToolTip("Fernkampfwaffe" if is_fk else "Nahkampfwaffe")
                lab.setStyleSheet(
                    "font-weight: bold; color: #1a5f9e;" if is_fk else "font-weight: bold; color: #555;"
                )
        except Exception:
            pass
        try:
            self.save_data()
        except Exception:
            pass
        eig_ed = entry.get("eigenschaften")
        current = eig_ed.text() if eig_ed is not None else ""
        result = self.open_weapon_eigenschaft_dialog(current)
        if result is not None and eig_ed is not None:
            # Sicherheit: NK/FK nie als Eigenschaft speichern
            cleaned = [
                x.strip() for x in result.split(",")
                if x.strip() and x.strip().lower() not in ("nahkampf (nk)", "fernkampf (fk)", "nk", "fk", "nahkampf", "fernkampf")
            ]
            eig_ed.setText(", ".join(cleaned))
            self.changed()

    def _add_weapon_from_db(self):
        """+ Waffe: Datenbank öffnen und neue Zeile befüllen."""
        dlg = WeaponSelector(self)
        if dlg.exec() != QDialog.Accepted:
            return
        selected_name = dlg.get_selected_weapon()
        if not selected_name:
            return
        data = {"name": selected_name, "info": "", "fernkampf": False}
        try:
            if selected_name in Wolke.DB.waffen:
                w = Wolke.DB.waffen[selected_name]
                tp = f"{w.würfel}W{w.würfelSeiten}"
                if w.plus > 0:
                    tp += f"+{w.plus}"
                elif w.plus < 0:
                    tp += f"{w.plus}"
                data["tp"] = tp
                data["tp_base"] = tp
                data["rw"] = int(getattr(w, "rw", 0) or 0)
                data["wm"] = int(getattr(w, "wm", 0) or 0)
                try:
                    data["lz"] = int(getattr(w, "lz", 0) or 0)
                except Exception:
                    data["lz"] = 0
                fk_val = getattr(w, "fernkampf", None)
                if fk_val is None:
                    fk_val = getattr(w, "fk", 0)
                try:
                    if isinstance(fk_val, bool):
                        data["fernkampf"] = fk_val
                    elif isinstance(fk_val, (int, float)):
                        data["fernkampf"] = int(fk_val) != 0
                    else:
                        data["fernkampf"] = str(fk_val).strip() in ("1", "true", "True", "ja")
                except Exception:
                    data["fernkampf"] = False
                eig = getattr(w, "eigenschaften", None) or []
                if isinstance(eig, (list, tuple)):
                    data["eigenschaften"] = ", ".join(str(x) for x in eig)
                else:
                    data["eigenschaften"] = str(eig) if eig else ""
                # Katalog-Tags NK/FK nicht in Eigenschaften speichern
                data["eigenschaften"] = ", ".join(
                    x.strip() for x in (data.get("eigenschaften") or "").split(",")
                    if x.strip() and x.strip().lower() not in (
                        "nahkampf (nk)", "fernkampf (fk)", "nk", "fk", "nahkampf", "fernkampf"
                    )
                )
        except Exception:
            pass
        self.add_list_item("combat", data)
        try:
            self.save_data()
        except Exception:
            pass

    def _edit_last_weapon_eigenschaften(self):
        """Eigenschaften-Button: Dialog für letzte (oder neue) Waffe."""
        if not getattr(self, "combat_widgets", None):
            self.add_list_item("combat", {"name": "", "eigenschaften": ""})
        entry = self.combat_widgets[-1]
        eig_ed = entry.get("eigenschaften")
        current = eig_ed.text() if eig_ed is not None else ""
        result = self.open_weapon_eigenschaft_dialog(current)
        if result is not None and eig_ed is not None:
            eig_ed.setText(result)
            self.changed()

    def _init_kampf_tab(self):

        wrapper = QWidget()
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(4, 4, 4, 4)
        wl.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Abgeleitete Kampfwerte ---
        abg_box = QGroupBox("Abgeleitete Kampfwerte")
        abg_l = QHBoxLayout(abg_box)
        self.kampf_ws_label = QLabel("<b>WS:</b> –")
        self.kampf_ws_stern_label = QLabel("<b>WS*:</b> –")
        self.kampf_gs_label = QLabel("<b>GS*:</b> –")
        self.kampf_ini_label = QLabel("<b>INI:</b> –")
        for w in (self.kampf_ws_label, self.kampf_ws_stern_label, self.kampf_gs_label, self.kampf_ini_label):
            abg_l.addWidget(w)
        abg_l.addStretch()
        wl.addWidget(abg_box)

        # --- Rüstung ---
        ruest_box = QGroupBox("Rüstung")
        ruest_l = QHBoxLayout(ruest_box)
        self.ruest_name = QLineEdit()
        self.ruest_name.setPlaceholderText("Name (z.B. Brigantina)")
        self.ruest_name.textChanged.connect(lambda: self._on_ruestung_changed())
        self.ruest_rs = QSpinBox(); self.ruest_rs.setRange(0, 12); self.ruest_rs.setPrefix("RS ")
        self.ruest_rs.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.ruest_rs.setFixedWidth(70)
        self.ruest_rs.valueChanged.connect(lambda *a: self._on_ruestung_changed())
        self.ruest_be = QSpinBox(); self.ruest_be.setRange(0, 12); self.ruest_be.setPrefix("BE ")
        self.ruest_be.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.ruest_be.setFixedWidth(70)
        self.ruest_be.valueChanged.connect(lambda *a: self._on_ruestung_changed())
        self.ruest_summary = QLabel("")
        self.ruest_summary.setStyleSheet("color: #555;")
        ruest_l.addWidget(self.ruest_name, 2)
        ruest_l.addWidget(self.ruest_rs)
        ruest_l.addWidget(self.ruest_be)
        ruest_l.addWidget(self.ruest_summary, 2)
        wl.addWidget(ruest_box)

        # --- Waffen (Grid: Header + Zeilen in denselben Spalten) ---
        waffen_box = QGroupBox("Waffen")
        outer_w = QVBoxLayout(waffen_box)
        outer_w.setContentsMargins(6, 6, 6, 6)
        outer_w.setSpacing(4)

        self.combat_scroll_area = QScrollArea()
        self.combat_scroll_area.setWidgetResizable(True)
        self.combat_scroll_area.setMinimumHeight(160)
        self.combat_container = QWidget()
        self.combat_layout = QGridLayout(self.combat_container)
        self.combat_layout.setContentsMargins(2, 2, 2, 2)
        self.combat_layout.setHorizontalSpacing(4)
        self.combat_layout.setVerticalSpacing(3)
        self.combat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Spalten: Name, Typ, TP, RW, WM, Eig., AT, 🎲, VT, 🎲, TP*, 🎲, i, ✕
        self._combat_col_widths = {
            0: None,   # Name stretch
            1: 48,     # Typ NK/FK
            2: 70,     # TP
            3: 40,     # RW
            4: 72,     # WM/LZ
            5: None,   # Eigenschaften stretch
            6: 36,     # AT
            7: 26,     # AT-Würfel
            8: 36,     # VT
            9: 26,     # VT-Würfel
            10: 70,    # TP*
            11: 26,    # TP-Würfel
            12: 22,    # i
            13: 22,    # ✕
        }
        for c, w in self._combat_col_widths.items():
            if w is not None:
                self.combat_layout.setColumnMinimumWidth(c, w)
        self.combat_layout.setColumnStretch(0, 3)
        self.combat_layout.setColumnStretch(5, 3)

        # Header-Zeile 0 – linksbündig über den Feldern
        headers = [
            (0, "Name"), (1, "Typ"), (2, "TP"), (3, "RW"), (4, "WM/LZ"), (5, "Eigenschaften"),
            (6, "AT"), (8, "VT"), (10, "TP*"),
        ]
        for col, txt in headers:
            lab = QLabel(f"<b>{txt}</b>")
            lab.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.combat_layout.addWidget(lab, 0, col)
        self._combat_next_row = 1

        self.combat_scroll_area.setWidget(self.combat_container)
        outer_w.addWidget(self.combat_scroll_area)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Waffe")
        add_btn.setToolTip("Waffe aus der Datenbank wählen und hinzufügen")
        add_btn.clicked.connect(self._add_weapon_from_db)
        own_btn = QPushButton("+ Eigene Waffe")
        own_btn.setToolTip("Eigene Waffe anlegen und Eigenschaften-Editor öffnen")
        own_btn.clicked.connect(self._add_eigene_waffe)
        add_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        own_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(own_btn)
        outer_w.addLayout(btn_row)
        self._combat_add_btn = add_btn
        self._combat_own_btn = own_btn
        wl.addWidget(waffen_box)

        self.combat_widgets = []

        munition_box = QGroupBox("Munition")
        mun_l = QVBoxLayout(munition_box)
        self.munition_host = QWidget()
        self.munition_layout = QVBoxLayout(self.munition_host)
        self.munition_layout.setContentsMargins(0, 0, 0, 0)
        mun_l.addWidget(self.munition_host)
        mun_btn = QPushButton("Hinzufügen")
        mun_btn.setToolTip("Munition anlegen")
        mun_btn.clicked.connect(self._add_munition)
        mun_l.addWidget(mun_btn)
        wl.addWidget(munition_box)
        self.munition_data = []

        # Attribute-Änderungen → Kampfwerte aktualisieren
        for k in ("WS", "GS", "INI"):
            if k in self.attr_spins:
                self.attr_spins[k].valueChanged.connect(lambda *a: self._update_kampf_derived())

        self.tabs.addTab(wrapper, "Kampf")

    def _get_munition(self):
        self.munition_data = ensure_selected_ammo(normalize_ammo_list(
            getattr(self, "munition_data", None) or (self.data or {}).get("munition") or []
        ))
        return self.munition_data

    def _set_munition(self, items, notify=True):
        self.munition_data = ensure_selected_ammo(normalize_ammo_list(items))
        if self.data is not None:
            self.data["munition"] = self.munition_data
        if notify:
            try:
                self.changed()
            except RuntimeError:
                pass

    def _add_munition(self):
        if AmmoEditDialog is None:
            return
        dlg = AmmoEditDialog(blank_ammo("Neue Munition") if blank_ammo else {"name": "Neue Munition", "anzahl": 10}, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            items = self._get_munition()
            items.append(dlg.result_data())
            self._set_munition(items)
            self._rebuild_munition_ui()

    def _edit_munition(self, ammo_id):
        if AmmoEditDialog is None:
            return
        items = self._get_munition()
        cur = next((a for a in items if a.get("id") == ammo_id), None)
        if not cur:
            return
        dlg = AmmoEditDialog(cur, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.result_data()
            items = [data if a.get("id") == ammo_id else a for a in items]
            self._set_munition(items)
            self._rebuild_munition_ui()

    def _remove_munition(self, ammo_id):
        self._set_munition([a for a in self._get_munition() if a.get("id") != ammo_id])
        self._rebuild_munition_ui()

    def _rebuild_munition_ui(self):
        host = getattr(self, "munition_host", None)
        if host is None:
            return
        lay = self.munition_layout
        while lay.count():
            child = lay.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        head = QHBoxLayout()
        for txt, w in (("Name", 0), ("Anz.", 40), ("TP", 50), ("RW", 30), ("LZ", 30), ("Eigenschaften", 0)):
            lab = QLabel(f"<b>{txt}</b>")
            if w:
                lab.setFixedWidth(w)
            head.addWidget(lab, 1 if txt in ("Name", "Eigenschaften") else 0)
        head.addSpacing(22)
        head_w = QWidget()
        head_w.setLayout(head)
        lay.addWidget(head_w)
        for a in self._get_munition():
            row = QHBoxLayout()
            mark = QLabel("●" if a.get("selected") else " ")
            mark.setFixedWidth(12)
            row.addWidget(mark)
            btn = QPushButton(a.get("name") or "Munition")
            btn.setFlat(True)
            btn.setStyleSheet("text-align:left;")
            btn.clicked.connect(partial(self._edit_munition, a.get("id")))
            row.addWidget(btn, 2)
            anz = QLabel(str(int(a.get("anzahl", 0) or 0)))
            anz.setFixedWidth(40)
            row.addWidget(anz)
            tp = QLabel(a.get("tp") or "—")
            tp.setFixedWidth(50)
            row.addWidget(tp)
            rw = QLabel(str(a.get("rw") or 0))
            rw.setFixedWidth(30)
            row.addWidget(rw)
            lz = QLabel(str(a.get("lz") or 0))
            lz.setFixedWidth(30)
            row.addWidget(lz)
            eig = QLabel(a.get("eigenschaften") or "")
            eig.setWordWrap(True)
            row.addWidget(eig, 2)
            del_btn = QPushButton("✕")
            del_btn.setFlat(True)
            del_btn.setFixedWidth(22)
            del_btn.clicked.connect(partial(self._remove_munition, a.get("id")))
            row.addWidget(del_btn)
            wrap = QWidget()
            wrap.setLayout(row)
            lay.addWidget(wrap)

    def _on_ruestung_changed(self):
        if getattr(self, "isLoading", False):
            return
        self._update_kampf_derived()
        self.changed()

    def _update_kampf_derived(self):
        """Aktualisiert die Anzeige der abgeleiteten Kampfwerte + Rüstungs-Summary."""
        attrs = {}
        for k, spin in self.attr_spins.items():
            attrs[k] = spin.value()
        ws = attrs.get("WS", 0)
        rs = self.ruest_rs.value() if hasattr(self, "ruest_rs") else 0
        be = self.ruest_be.value() if hasattr(self, "ruest_be") else 0
        # WS* = WS + RS
        ws_stern = ws + rs
        gs = attrs.get("GS", 0)
        # GS* = GS − BE, mindestens 1 (bei GS 0 bleibt 0)
        gs_stern = max(1, gs - be) if gs > 0 else 0
        ini = attrs.get("INI", 0)

        if hasattr(self, "kampf_ws_label"):
            self.kampf_ws_label.setText(f"<b>WS:</b> {ws}")
            self.kampf_ws_stern_label.setText(f"<b>WS*:</b> {ws_stern}")
            self.kampf_gs_label.setText(f"<b>GS*:</b> {gs_stern}")
            self.kampf_ini_label.setText(f"<b>INI:</b> {ini}")
        if hasattr(self, "ruest_summary"):
            name = self.ruest_name.text().strip() if hasattr(self, "ruest_name") else ""
            if name or rs or be:
                self.ruest_summary.setText(f"(RS: {rs} | BE: {be} | WS*: {ws_stern})")
            else:
                self.ruest_summary.setText("")

    def show_nsc_nahkampf_manöver(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Nahkampfmanöver")
        dlg.setMinimumSize(500, 500)
        lay = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setHtml(self._nahkampf_manöver_html())
        lay.addWidget(browser)
        box = QDialogButtonBox(QDialogButtonBox.Close)
        box.rejected.connect(dlg.reject)
        box.accepted.connect(dlg.accept)
        lay.addWidget(box)
        dlg.exec()

    def show_nsc_fernkampf_manöver(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Fernkampfmanöver")
        dlg.setMinimumSize(500, 500)
        lay = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setHtml(self._fernkampf_manöver_html())
        lay.addWidget(browser)
        box = QDialogButtonBox(QDialogButtonBox.Close)
        box.rejected.connect(dlg.reject)
        box.accepted.connect(dlg.accept)
        lay.addWidget(box)
        dlg.exec()

    def _nahkampf_manöver_html(self):
        return """
<h2>Nahkampfmanöver</h2>
<h3>Basismanöver</h3>
<p><b>Ausweichen</b> (VT –2–BE) – vollständig entgehen</p>
<p><b>Binden</b> (VT –X, max. 8) – VT des Gegners erschwert</p>
<p><b>Entfernung verändern</b> (AT –BE) – ohne Passierschläge lösen</p>
<p><b>Entwaffnen</b> (AT/VT –4, Gegenprobe KK) – Waffe entreißen, Schaden 0</p>
<p><b>Umreißen</b> (AT, Gegenprobe GE/KO) – Ziel liegt, Schaden 0</p>
<p><b>Wuchtschlag</b> (AT –X, max. 8) – +X TP</p>
<h3>Eingeschränkt</h3>
<p><b>Rüstungsbrecher</b> (AT –4) – SP statt TP (Waffeneigenschaft nötig)</p>
<p><b>Schildspalter</b> (AT +2) – Schaden am Schild</p>
<p><b>Stumpfer Schlag</b> (AT) – Erschöpfung statt Wunden</p>
<p><b>Auflaufen lassen</b> (VT –4) – Waffenschaden + GS des Angreifers</p>
<h3>Aufbauend (Vorteil nötig)</h3>
<p><b>Hammerschlag</b> (AT –8) – doppelter Waffenschaden</p>
<p><b>Todesstoß</b> (AT –8) – +2 Wunden</p>
<p><b>Niederwerfen</b> (AT –4, Gegenprobe KK) – Ziel liegt</p>
<p><b>Klingentanz</b> (AT –4) – Folgeangriff</p>
<p><b>Sturmangriff</b> (Bewegung+AT) – +GS TP</p>
<p><b>Ausfall</b> (AT –2–BE) – Gegner weicht zurück</p>
"""

    def _fernkampf_manöver_html(self):
        return """
<h2>Fernkampfmanöver</h2>
<p><b>Scharfschuss</b> (FK –X, max. 8) – +X TP</p>
<p><b>Zielen</b> (FK +2) – +1 Aktion Vorbereitung</p>
<p><b>Reichweite erhöhen</b> (FK –4) – RW verdoppelt (bis 2×)</p>
<p><b>Rüstungsbrecher</b> (FK –4) – SP statt TP (Panzerbrechender Pfeil erfordert)</p>
<p><b>Schnellschuss</b> (FK –4) – halbe Ladezeit (Vorteil Schnellziehen)</p>
<p><b>Meisterschuss</b> (FK –8) – +2 Wunden (Vorteil Meisterschuss)</p>
<h3>Modifikatoren</h3>
<p>Größe: sehr groß +8 · groß +4 · mittel 0 · klein –4 · sehr klein –8 · winzig –12</p>
<p>Licht: Dämmerung –4 · Mondlicht –8 · Sternenlicht –16</p>
<p>Bewegung: schnell –4 · sehr schnell –8 · extrem schnell –12</p>
<p>Deckung: halb –4 · Dreiviertel –8 · beritten –4</p>
"""

    def _init_vorteile_tab(self):
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Links: Liste der Vorteile ---
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)

        self.vorteile_tree = QTreeWidget()
        self.vorteile_tree.setColumnCount(2)
        self.vorteile_tree.setHeaderLabels(["Vorteil", "Kosten"])
        self.vorteile_tree.setAlternatingRowColors(True)
        self.vorteile_tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.vorteile_tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.vorteile_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.vorteile_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.vorteile_tree.header().resizeSection(1, 70)
        self.vorteile_tree.itemSelectionChanged.connect(self._nsc_vorteil_selected)
        ll.addWidget(self.vorteile_tree)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Vorteil aus DB…")
        add_btn.clicked.connect(self.add_vorteil_from_db)
        del_btn = QPushButton("Entfernen")
        del_btn.clicked.connect(self.remove_selected_vorteil)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        ll.addLayout(btn_row)

        # Schnellhaken für Manöver-Voraussetzungen (Vorteile, die Manöver freischalten)
        combat_box = QGroupBox("Manöver-Schnellwahl (Vorteile)")
        grid = QGridLayout(combat_box)
        self.vorteil_checks = {}
        for i, name in enumerate([
            "Präzision", "Hammerschlag", "Todesstoß", "Atemtechnik",
            "Niederwerfen", "Sturmangriff", "Klingentanz", "Ausfall",
            "Meisterschuss", "Schnellziehen", "Beidhändiger Kampf III",
            "Kraftvoller Kampf III", "Parierwaffenkampf III", "Schildkampf III",
            "Schneller Kampf III", "Reiterkampf I", "Reiterkampf III",
        ]):
            cb = QCheckBox(name)
            cb.stateChanged.connect(self._on_vorteil_check_changed)
            grid.addWidget(cb, i // 4, i % 4)
            self.vorteil_checks[name] = cb
        ll.addWidget(combat_box)

        splitter.addWidget(left)

        # --- Rechts: Info-Panel ---
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 0, 0, 0)
        self.vorteil_info_name = QLabel("<b>—</b>")
        self.vorteil_info_name.setWordWrap(True)
        self.vorteil_info_meta = QLabel("")
        self.vorteil_info_meta.setWordWrap(True)
        self.vorteil_info_meta.setStyleSheet("color: #555;")
        self.vorteil_info_text = QTextBrowser()
        self.vorteil_info_text.setOpenExternalLinks(False)
        rl.addWidget(self.vorteil_info_name)
        rl.addWidget(self.vorteil_info_meta)
        rl.addWidget(self.vorteil_info_text, 1)
        splitter.addWidget(right)
        splitter.setSizes([280, 320])

        outer.addWidget(splitter)

        # Freitext optional klein
        self.vorteile_edit = QPlainTextEdit()
        self.vorteile_edit.setPlaceholderText("Freitext / Sonderregeln (optional)…")
        self.vorteile_edit.setMaximumHeight(50)
        self.vorteile_edit.textChanged.connect(lambda: self.changed())
        outer.addWidget(self.vorteile_edit)

        # Daten
        self.vorteile_list_data = []  # reine Namensliste
        # legacy alias
        self.vorteile_extra_list = None

        self.tabs.addTab(tab, "Vorteile")

    def _on_vorteil_check_changed(self, *_):
        # Checkboxen mit der Vorteils-Liste synchronisieren
        for name, cb in self.vorteil_checks.items():
            if cb.isChecked():
                if name not in self.vorteile_list_data:
                    self.vorteile_list_data.append(name)
            else:
                if name in self.vorteile_list_data:
                    self.vorteile_list_data = [v for v in self.vorteile_list_data if v != name]
        self._rebuild_vorteile_tree()
        if not getattr(self, "isLoading", False):
            self.changed()

    def add_vorteil_from_db(self):
        already = set(self.vorteile_list_data)
        dlg = VorteilSelector(self, already=already)
        if dlg.exec() == QDialog.Accepted:
            name = dlg.get_selected()
            if not name:
                return
            if name not in self.vorteile_list_data:
                self.vorteile_list_data.append(name)
            if name in self.vorteil_checks:
                self.vorteil_checks[name].blockSignals(True)
                self.vorteil_checks[name].setChecked(True)
                self.vorteil_checks[name].blockSignals(False)
            self._rebuild_vorteile_tree()
            self.changed()
            # Selektion auf neuen Eintrag
            self._select_vorteil_in_tree(name)

    def remove_selected_vorteil(self):
        item = self.vorteile_tree.currentItem()
        if not item or item.parent() is None:
            return
        name = item.data(0, Qt.ItemDataRole.UserRole) or item.text(0)
        self.vorteile_list_data = [v for v in self.vorteile_list_data if v != name]
        if name in self.vorteil_checks:
            self.vorteil_checks[name].blockSignals(True)
            self.vorteil_checks[name].setChecked(False)
            self.vorteil_checks[name].blockSignals(False)
        self._rebuild_vorteile_tree()
        self.vorteil_info_name.setText("<b>—</b>")
        self.vorteil_info_meta.setText("")
        self.vorteil_info_text.clear()
        self.changed()

    def remove_extra_vorteil(self):
        self.remove_selected_vorteil()

    def _select_vorteil_in_tree(self, name):
        root = self.vorteile_tree.invisibleRootItem()
        for i in range(root.childCount()):
            parent = root.child(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if (child.data(0, Qt.ItemDataRole.UserRole) or child.text(0)) == name:
                    self.vorteile_tree.setCurrentItem(child)
                    return

    def _rebuild_vorteile_tree(self):
        tree = self.vorteile_tree
        tree.blockSignals(True)
        tree.clear()
        by_kat = {}
        for name in self.vorteile_list_data:
            kat = "Sonstige"
            kosten = ""
            try:
                if hasattr(Wolke, "DB") and Wolke.DB and name in Wolke.DB.vorteile:
                    vdef = Wolke.DB.vorteile[name]
                    try:
                        kat = vdef.kategorieName(Wolke.DB)
                    except Exception:
                        kat = str(getattr(vdef, "kategorie", "") or "Sonstige")
                    kosten = f"{getattr(vdef, 'kosten', '')} EP" if getattr(vdef, "kosten", None) is not None else ""
            except Exception:
                pass
            by_kat.setdefault(str(kat) or "Sonstige", []).append((name, kosten))

        font = QFont()
        font.setBold(True)
        font.setCapitalization(QFont.Capitalization.SmallCaps)

        for kat in sorted(by_kat.keys()):
            parent = QTreeWidgetItem(tree, [kat, ""])
            parent.setFont(0, font)
            parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            parent.setExpanded(True)
            for name, kosten in sorted(by_kat[kat], key=lambda x: x[0]):
                child = QTreeWidgetItem(parent, [name, kosten])
                child.setData(0, Qt.ItemDataRole.UserRole, name)
        tree.blockSignals(False)

    def _nsc_vorteil_selected(self):
        items = self.vorteile_tree.selectedItems()
        if not items or items[0].parent() is None:
            self.vorteil_info_name.setText("<b>—</b>")
            self.vorteil_info_meta.setText("")
            self.vorteil_info_text.clear()
            return
        name = items[0].data(0, Qt.ItemDataRole.UserRole) or items[0].text(0)
        self.vorteil_info_name.setText(f"<b>{name}</b>")
        meta_parts = []
        text_html = ""
        try:
            if hasattr(Wolke, "DB") and Wolke.DB and name in Wolke.DB.vorteile:
                vdef = Wolke.DB.vorteile[name]
                try:
                    meta_parts.append(vdef.kategorieName(Wolke.DB))
                except Exception:
                    pass
                if getattr(vdef, "kosten", None) is not None:
                    meta_parts.append(f"{vdef.kosten} EP")
                if getattr(vdef, "nachkauf", None):
                    meta_parts.append(f"Nachkauf: {vdef.nachkauf}")
                try:
                    vorauss = vdef.voraussetzungen.anzeigetext(Wolke.DB) if hasattr(vdef, "voraussetzungen") else ""
                    if vorauss:
                        meta_parts.append(f"Voraussetzungen: {vorauss}")
                except Exception:
                    pass
                beschreibung = getattr(vdef, "text", "") or ""
                if getattr(vdef, "bedingungen", None):
                    beschreibung = f"<i>Bedingungen</i>: {vdef.bedingungen}<br><br>" + beschreibung
                if getattr(vdef, "info", None):
                    beschreibung += f"<br><br><b>Hinweis</b>: {vdef.info}"
                try:
                    text_html = Hilfsmethoden.fixHtml(beschreibung) if beschreibung else ""
                except Exception:
                    text_html = beschreibung
            else:
                text_html = "<i>Keine DB-Daten zu diesem Vorteil.</i>"
        except Exception as e:
            text_html = f"<i>Fehler: {e}</i>"
        self.vorteil_info_meta.setText(" · ".join(str(p) for p in meta_parts if p))
        self.vorteil_info_text.setHtml(text_html or "")

    def add_list_item(self, type_str, data=None):
        if type_str == "skill" or type_str == "power":
            layout_target = self.skill_layout if type_str == "skill" else self.power_layout
            widget_list = self.skill_widgets if type_str == "skill" else self.power_widgets
            
            row = QWidget()
            l = QHBoxLayout(row)
            l.setContentsMargins(0,0,0,0)
            
            name_ed = QLineEdit(data.get("name", "") if data else "")
            name_ed.setPlaceholderText("Name")
            name_ed.textChanged.connect(lambda: self.changed())
            
            val_spin = QSpinBox()
            val_spin.setRange(0, 99)
            val_spin.setValue(data.get("val", 0) if data else 0)
            val_spin.setFixedWidth(50)
            val_spin.valueChanged.connect(lambda *a: self.changed())
            
            roll_btn = QPushButton("🎲")
            roll_btn.setFixedWidth(30)
            roll_btn.clicked.connect(lambda checked=False, n=name_ed, s=val_spin: self.trigger_roll(n.text(), s.value()))
            
            l.addWidget(name_ed)
            l.addWidget(val_spin)
            l.addWidget(roll_btn)
            
            if type_str == "power":
                info_btn = QPushButton("i")
                info_btn.setFixedWidth(25)
                info_btn.clicked.connect(lambda checked=False, n=name_ed: self.show_talent_info(n.text()))
                l.addWidget(info_btn)

            del_btn = QPushButton("x")
            del_btn.setFixedWidth(25)
            del_btn.setStyleSheet("color: red;")
            del_btn.clicked.connect(lambda: self.remove_list_item(row, widget_list, type_str))
            
            l.addWidget(del_btn)
            
            layout_target.addWidget(row)
            widget_list.append({"row": row, "name": name_ed, "val": val_spin})

        elif type_str == "combat":
            d = data or {}
            r = getattr(self, "_combat_next_row", 1)

            def _fw(w, width):
                if width:
                    w.setFixedWidth(width)
                return w

            name_ed = QLineEdit(d.get("name", ""))
            name_ed.setPlaceholderText("Waffe")

            tp_base = _fw(QLineEdit(d.get("tp_base", d.get("tp", ""))), 70)
            tp_base.setPlaceholderText("TP")

            rw_spin = _fw(QSpinBox(), 40)
            rw_spin.setRange(0, 20)
            rw_spin.setValue(int(d.get("rw", 0) or 0))
            rw_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

            wm = int(d.get("wm", 0) or 0)
            lz = int(d.get("lz", 0) or 0)
            wm_lz_ed = _fw(QLineEdit(), 72)
            if lz:
                wm_lz_ed.setText(f"{wm}/{lz}")
            else:
                wm_lz_ed.setText(str(wm))
            wm_lz_ed.setPlaceholderText("WM/LZ")
            wm_lz_ed.setToolTip("Waffenmodifikator / Ladezeit (z. B. 0 oder 0/1)")

            eig_ed = QLineEdit(d.get("eigenschaften", ""))
            eig_ed.setPlaceholderText("Eigenschaften (Doppelklick = Katalog)")
            def _eig_dbl(_event=None, ed=eig_ed):
                res = self.open_weapon_eigenschaft_dialog(ed.text())
                if res is not None:
                    ed.setText(res)
                    self.changed()
            eig_ed.mouseDoubleClickEvent = lambda event, fn=_eig_dbl: fn(event)

            at_spin = _fw(QSpinBox(), 36)
            at_spin.setRange(0, 99)
            at_spin.setValue(int(d.get("at", 0) or 0))
            at_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

            vt_spin = _fw(QSpinBox(), 36)
            vt_spin.setRange(0, 99)
            vt_spin.setValue(int(d.get("vt", 0) or 0))
            vt_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

            tp_ed = _fw(QLineEdit(d.get("tp", d.get("tp_base", ""))), 70)
            tp_ed.setPlaceholderText("TP*")

            info_store = {"text": d.get("info", "") or ""}

            btn_info = _fw(QPushButton("i"), 22)
            btn_info.setToolTip("Waffen-Info / eigener Infotext")

            btn_at = _fw(QPushButton("🎲"), 26)
            btn_at.setFlat(True)
            btn_at.setToolTip("Attacke (mit Manöver)")
            btn_at.clicked.connect(
                lambda checked=False, n=name_ed, a=at_spin, t=tp_ed:
                self.trigger_at_roll(n.text(), a.value(), t.text())
            )
            btn_vt = _fw(QPushButton("🎲"), 26)
            btn_vt.setFlat(True)
            btn_vt.setToolTip("Verteidigung (mit Manöver, ggf. Auflaufen → Schaden)")
            btn_vt.clicked.connect(
                lambda checked=False, n=name_ed, v=vt_spin, t=tp_ed:
                self.trigger_vt_roll(n.text(), v.value(), t.text())
            )
            btn_tp = _fw(QPushButton("🎲"), 26)
            btn_tp.setFlat(True)
            btn_tp.setToolTip("Trefferpunkte")
            btn_tp.clicked.connect(
                lambda checked=False, n=name_ed, t=tp_ed:
                self.tpRollRequested.emit(self, f"TP {n.text()}", t.text())
            )

            del_btn = _fw(QPushButton("✕"), 22)
            del_btn.setFlat(True)
            del_btn.setStyleSheet("color: #a33; font-weight: bold;")

            for w in (name_ed, tp_base, eig_ed, tp_ed):
                w.textChanged.connect(lambda: self.changed())
            for w in (rw_spin, at_spin, vt_spin):
                w.valueChanged.connect(lambda *a: self.changed())
            wm_lz_ed.textChanged.connect(lambda: self.changed())

            # fk fest aus Daten (kein nachträglicher Wechsel)
            is_fk = False
            if "fernkampf" in d and d.get("fernkampf") is not None:
                v = d.get("fernkampf")
            elif "is_fk" in d and d.get("is_fk") is not None:
                v = d.get("is_fk")
            elif "fk" in d and d.get("fk") is not None:
                v = d.get("fk")
            else:
                v = False
            if isinstance(v, bool):
                is_fk = v
            elif isinstance(v, (int, float)):
                is_fk = int(v) != 0
            else:
                is_fk = str(v).strip().lower() in ("1", "true", "ja", "yes", "fk", "fernkampf")

            typ_lab = QLabel("FK" if is_fk else "NK")
            typ_lab.setFixedWidth(28)
            typ_lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            typ_lab.setToolTip("Fernkampfwaffe" if is_fk else "Nahkampfwaffe")
            typ_lab.setStyleSheet(
                "font-weight: bold; color: #1a5f9e;" if is_fk else "font-weight: bold; color: #555;"
            )
            if is_fk:
                vt_spin.setVisible(False)
                btn_vt.setVisible(False)
                btn_vt.setEnabled(False)
                vt_spin.setToolTip("Fernkampfwaffen haben keine VT")
                btn_vt.setToolTip("Fernkampfwaffen haben keine VT")

            cells = [
                (0, name_ed), (1, typ_lab), (2, tp_base), (3, rw_spin), (4, wm_lz_ed), (5, eig_ed),
                (6, at_spin), (7, btn_at), (8, vt_spin), (9, btn_vt),
                (10, tp_ed), (11, btn_tp), (12, btn_info), (13, del_btn),
            ]
            for col, w in cells:
                self.combat_layout.addWidget(w, r, col)

            entry = {
                "row": r,  # Grid-Zeilenindex
                "widgets": [w for _, w in cells],
                "name": name_ed, "tp_base": tp_base,
                "rw": rw_spin, "wm_lz": wm_lz_ed, "eigenschaften": eig_ed,
                "at": at_spin, "vt": vt_spin, "tp": tp_ed,
                "info_store": info_store, "info_btn": btn_info,
                "fernkampf": bool(is_fk),
                "typ_lab": typ_lab,
            }
            try:
                name_ed.setToolTip(
                    "Fernkampfwaffe" if is_fk else "Nahkampfwaffe"
                )
            except Exception:
                pass

            def _open_info(e=entry, n=name_ed, eig=eig_ed, store=info_store):
                def _save(txt):
                    store["text"] = txt or ""
                    self.changed()
                self.show_weapon_info(
                    n.text(),
                    info_text=store.get("text", ""),
                    eigenschaften=eig.text() if eig is not None else "",
                    on_save=_save,
                )

            btn_info.clicked.connect(lambda checked=False: _open_info())
            del_btn.clicked.connect(lambda checked=False, e=entry: self._remove_combat_entry(e))
            self.combat_widgets.append(entry)
            self._combat_next_row = r + 1
        
        self.changed()

    def _remove_combat_entry(self, entry):
        """Entfernt eine Waffenzeile und baut das Grid kompakt neu auf."""
        if entry in self.combat_widgets:
            self.combat_widgets.remove(entry)
        for w in entry.get("widgets") or []:
            self.combat_layout.removeWidget(w)
            w.deleteLater()
        self._rebuild_combat_grid_rows()
        self.changed()

    def _rebuild_combat_grid_rows(self):
        """Schiebt verbleibende Waffenzeilen nach oben (Header bleibt in Zeile 0)."""
        # Alle Daten-Widgets aus dem Grid nehmen (nicht löschen)
        for entry in self.combat_widgets:
            for w in entry.get("widgets") or []:
                self.combat_layout.removeWidget(w)
        r = 1
        for entry in self.combat_widgets:
            widgets = entry.get("widgets") or []
            for col, w in enumerate(widgets):
                self.combat_layout.addWidget(w, r, col)
            entry["row"] = r
            r += 1
        self._combat_next_row = r

    def remove_list_item(self, row_widget, list_ref, type_str):
        if type_str == "combat":
            # Legacy-Pfad: falls noch mit altem row-Widget aufgerufen
            for item in list(list_ref):
                if item.get("row") == row_widget or item.get("widgets") and row_widget in item.get("widgets", []):
                    self._remove_combat_entry(item)
                    return
            return
        if type_str == "skill":
            self.skill_layout.removeWidget(row_widget)
        elif type_str == "power":
            self.power_layout.removeWidget(row_widget)
        
        row_widget.deleteLater()
        for i, item in enumerate(list_ref):
            if item["row"] == row_widget:
                del list_ref[i]
                break
        self.changed()

    def load_data(self):
        # WICHTIG: isLoading für NSC Widget nutzen
        was_loading = self.isLoading
        self.isLoading = True 
        try:
            super().load_data()
            self.edit_name.setPlaceholderText("Name des NSC")
            self.combo_wunden_modus.setCurrentIndex(self.data.get("wunden_modus", 0))
            self.fr_line.setText("") 
            self.label_free_roll_result.setText("")
            
            attr_data = self.data.get("attributes", {})
            # Migration: alte NSCs hatten oft PW-Werte (z.B. 14). Wenn Wert > 20, als PW interpretieren.
            for k, spin in self.attr_spins.items():
                if k in ["WS", "GS", "MR", "INI"]:
                    default = 4
                    spin.setValue(attr_data.get(k, default))
                else:
                    default = 8
                    raw = attr_data.get(k, default)
                    # Heuristik: Werte > 20 waren vermutlich alte PW-Einträge
                    if raw > 20:
                        raw = max(1, raw // 2)
                    spin.setValue(raw)
                    if k in getattr(self, "attr_pw_labels", {}):
                        self.attr_pw_labels[k].setText(str(spin.value() * 2))
                
            asp_max = int(self.data.get("val_asp_max", self.data.get("val_asp", 0)) or 0)
            kap_max = int(self.data.get("val_kap_max", self.data.get("val_kap", 0)) or 0)
            if hasattr(self, "spin_asp_max"):
                self.spin_asp_max.setValue(asp_max)
                self.spin_kap_max.setValue(kap_max)
            self.spin_asp.setMaximum(max(asp_max, 999))
            self.spin_kap.setMaximum(max(kap_max, 999))
            self.spin_asp.setValue(int(self.data.get("val_asp", asp_max) or 0))
            self.spin_kap.setValue(int(self.data.get("val_kap", kap_max) or 0))
            
            # Sync Header INI Spin
            if self.show_ini_header:
                self.header_ini_spin.blockSignals(True)
                self.header_ini_spin.setValue(self.attr_spins["INI"].value())
                self.header_ini_spin.blockSignals(False)

            # Waffenzeilen leeren, Header (Zeile 0) behalten
            for entry in list(self.combat_widgets):
                for w in entry.get("widgets") or []:
                    self.combat_layout.removeWidget(w)
                    w.deleteLater()
            self.combat_widgets.clear()
            self._combat_next_row = 1
            # Falls Header verloren ging (erster Load): neu setzen
            if self.combat_layout.itemAtPosition(0, 0) is None:
                headers = [
                    (0, "Name"), (1, "Typ"), (2, "TP"), (3, "RW"), (4, "WM/LZ"), (5, "Eigenschaften"),
                    (5, "AT"), (7, "VT"), (9, "TP*"),
                ]
                for col, txt in headers:
                    lab = QLabel(f"<b>{txt}</b>")
                    lab.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    self.combat_layout.addWidget(lab, 0, col)
            
            # Fertigkeiten (Tree)
            self.skills_data = []
            for s in self.data.get("skills", []) or []:
                self.skills_data.append({"name": s.get("name", ""), "val": int(s.get("val", 0) or 0)})
            self.skills_data = [s for s in self.skills_data if s["name"]]
            self._rebuild_skills_tree()

            self.powers_data = []
            for p in self.data.get("powers", []) or []:
                self.powers_data.append({"name": p.get("name", ""), "val": int(p.get("val", 0) or 0)})
            self.powers_data = [p for p in self.powers_data if p["name"]]
            self._rebuild_powers_tree()

            for c in self.data.get("weapons", []):
                self.add_list_item("combat", c)
            self.munition_data = normalize_ammo_list(self.data.get("munition") or [])
            self._rebuild_munition_ui()
            
            if self.vorteile_edit:
                self.vorteile_edit.setPlainText(self.data.get("vorteile_text", ""))

            vlist = list(self.data.get("vorteile_list", []) or [])
            vtext = (self.data.get("vorteile_text") or "")
            self.vorteile_list_data = list(dict.fromkeys(vlist))
            if hasattr(self, "vorteil_checks"):
                for name, cb in self.vorteil_checks.items():
                    cb.blockSignals(True)
                    checked = name in self.vorteile_list_data or name.lower() in vtext.lower()
                    cb.setChecked(checked)
                    if checked and name not in self.vorteile_list_data:
                        self.vorteile_list_data.append(name)
                    cb.blockSignals(False)
            self._rebuild_vorteile_tree()
        
        finally:
            if not was_loading:
                self.isLoading = False

    def changed(self):
        if getattr(self, "isLoading", False):
            return
        try:
            super().changed()
        except RuntimeError:
            pass

    def save_data(self):
        super().save_data()
        try:
            self.data["wunden_modus"] = self.combo_wunden_modus.currentIndex()
            attr_data = {}
            for k, spin in self.attr_spins.items():
                attr_data[k] = spin.value()
            self.data["attributes"] = attr_data

            # Sync to Val Ini for sorting logic consistency
            self.data["val_ini"] = attr_data.get("INI", 0)

            self.data["val_asp"] = self.spin_asp.value()
            self.data["val_kap"] = self.spin_kap.value()
            if hasattr(self, "spin_asp_max"):
                self.data["val_asp_max"] = self.spin_asp_max.value()
                self.data["val_kap_max"] = self.spin_kap_max.value()

            skill_data = []
            for s in getattr(self, "skills_data", []) or []:
                skill_data.append({"name": s["name"], "val": int(s.get("val", 0))})
            self.data["skills"] = skill_data

            power_data = []
            for p in getattr(self, "powers_data", []) or []:
                power_data.append({"name": p["name"], "val": int(p.get("val", 0))})
            self.data["powers"] = power_data

            combat_data = []
            for w in self.combat_widgets:
                wm_val, lz_val = 0, 0
                try:
                    raw = (w["wm_lz"].text() if w.get("wm_lz") is not None else "") or ""
                    raw = raw.strip().replace(" ", "")
                    if "/" in raw:
                        a, b = raw.split("/", 1)
                        wm_val = int(a or 0)
                        lz_val = int(b or 0)
                    elif raw:
                        wm_val = int(raw)
                except Exception:
                    wm_val, lz_val = 0, 0
                combat_data.append({
                    "name": w["name"].text(),
                    "tp_base": (w["tp_base"].text() if "tp_base" in w else w["tp"].text()),
                    "rw": w["rw"].value() if "rw" in w else 0,
                    "wm": wm_val,
                    "lz": lz_val,
                    "eigenschaften": w["eigenschaften"].text() if "eigenschaften" in w else "",
                    "info": (w.get("info_store") or {}).get("text", "") if isinstance(w.get("info_store"), dict) else w.get("info", ""),
                    "fernkampf": bool(w.get("fernkampf", False)),
                    "at": w["at"].value(),
                    "vt": w["vt"].value(),
                    "tp": w["tp"].text(),
                })
            self.data["weapons"] = combat_data
            self.data["munition"] = normalize_ammo_list(getattr(self, "munition_data", None) or self.data.get("munition") or [])

            if hasattr(self, "ruest_name"):
                self.data["ruestung"] = {
                    "name": self.ruest_name.text(),
                    "rs": self.ruest_rs.value(),
                    "be": self.ruest_be.value(),
                }

            if self.vorteile_edit:
                self.data["vorteile_text"] = self.vorteile_edit.toPlainText()
            vlist = list(getattr(self, "vorteile_list_data", []) or [])
            if hasattr(self, "vorteil_checks"):
                for name, cb in self.vorteil_checks.items():
                    if cb.isChecked() and name not in vlist:
                        vlist.append(name)
            self.data["vorteile_list"] = vlist
        except RuntimeError:
            # C++-Widgets schon gelöscht (z. B. nach INI-Rebuild während TP-Tick)
            pass
        
    def trigger_free_roll(self):
        expr = self.fr_line.text()
        if expr:
            total, html_res = parse_and_roll_dice_string(expr)
            self.label_free_roll_result.setText(html_res)

    def update_wunden_modus(self):
        if getattr(self, "isLoading", False): return
        self.data["wunden_modus"] = self.combo_wunden_modus.currentIndex()
        self.data["wunden"] = [None]*8 
        self.update_wound_buttons(self.data["wunden"])
        self.changed()

    def update_wound_buttons(self, wunden):
        mode = self.data.get("wunden_modus", 0)
        for i, state in enumerate(wunden):
            btn = self.wunden_buttons[i]
            btn.setText(""); btn.setStyleSheet("")
            if state is None: continue
            
            if state == "/":
                btn.setText("/"); btn.setStyleSheet("background-color: #236fa1; color: white; font-weight: bold;")
            elif state in ["X", "II", "IV"]:
                btn.setText(state)
                is_end = (mode == 0 and state == "X") or (mode == 1 and state == "II") or (mode == 2 and state == "IV")
                if is_end: btn.setStyleSheet("background-color: #a12323; color: white; font-weight: bold;")
                else: btn.setStyleSheet("background-color: #d4a017; color: white; font-weight: bold;")
            else:
                btn.setText(state); btn.setStyleSheet("background-color: #d4a017; color: white; font-weight: bold;")

    def wunde_clicked(self, index):
        wunden = self.data.get("wunden", [None]*8)
        current = wunden[index]
        mode = self.data.get("wunden_modus", 0)
        new_val = None
        
        if mode == 0: new_val = "/" if current is None else ("X" if current == "/" else None)
        elif mode == 1: 
            if current is None: new_val = "/"
            elif current == "/": new_val = "I"
            elif current == "I": new_val = "II"
            else: new_val = None
        elif mode == 2:
            cycle = [None, "/", "I", "II", "III", "IV"]
            try: idx = cycle.index(current); new_val = cycle[idx+1] if idx+1 < len(cycle) else None
            except: new_val = "/"
            
        wunden[index] = new_val
        rank = {None: 0, "/": 1, "I": 2, "II": 3, "III": 4, "IV": 5, "X": 6}
        wunden.sort(key=lambda x: rank.get(x, 0), reverse=True)
        self.data["wunden"] = wunden
        self.update_wound_buttons(wunden)
        self.changed()


# MonsterWidget an NSCWidget binden (vermeidet Zirkelimport zur Ladezeit)
_MONSTER_WIDGET_OK = False
_MONSTER_IMPORT_ERROR = ""
try:
    from MonsterWidget import build_monster_widget_class
    MonsterWidget = build_monster_widget_class(NSCWidget)
    _MONSTER_WIDGET_OK = getattr(MonsterWidget, "is_monster", False) is True or MonsterWidget is not NSCWidget
except Exception as _mw_err:
    MonsterWidget = NSCWidget  # Fallback – dann fehlen Monster-Features!
    _MONSTER_IMPORT_ERROR = str(_mw_err)
    print(f"MonsterWidget konnte nicht geladen werden: {_mw_err}")

try:
    from MonsterHelper import (
        default_monster_data, make_monster_has_vorteil, is_monster_widget, load_monster_katalog,
    )
except Exception as _mh_err:
    def default_monster_data(name="Neues Monster"):
        return {"name": name, "kind": "monster", "attributes": {}, "weapons": [], "wunden": [None]*8, "effekte": []}
    def make_monster_has_vorteil(base, freigabe, manöver_list):
        return base
    def is_monster_widget(w):
        return bool(w and (getattr(w, "data", {}) or {}).get("kind") == "monster")
    def load_monster_katalog():
        return {"klassen": [], "eigenschaften": [], "groessen": []}
    if not _MONSTER_IMPORT_ERROR:
        _MONSTER_IMPORT_ERROR = str(_mh_err)
    print(f"MonsterHelper konnte nicht geladen werden: {_mh_err}")


class MasterPluginWrapper(QtCore.QObject):
    modified = QtCore.Signal()

    def __init__(self):
        super().__init__()
        _install_no_wheel_globally()
        self.form = QWidget()
        self.currentlyLoading = False
        self.thema_text_edits = []
        self.sc_widgets = []
        self.nsc_widgets = []
        self.monster_widgets = []
        self.ini_widgets = [] # Liste der aktiven Widgets im INI Tab
        
        self.active_sc_widget = None
        self.active_ini_widget = None # Speziell für den INI Tab
        
        self.active_attribute_name = ""
        self.active_attribute_value = 0
        self.custom_mod_value = 0
        self.active_tp_string = None
        # Zustand für AT → Manöver → Schaden Flow
        self.pending_tp_string = None
        self.pending_weapon_name = None
        self.pending_weapon_is_fk = None
        self._pending_atemtechnik = False  # AT-Haken → TP übernehmen
        self._pending_wuchtschlag_tp = 0
        self._pending_rüstungsbrecher = False
        self._pending_todesstoß = False
        self._pending_manöver_notes = []
        self._pending_no_damage = False
        self._pending_auflaufen = False
        self._pending_riposte = False
        self._last_at_ew = None
        self.präzision_ge_bonus = 0  # GE-Wert, falls Präzision ausgelöst wurde
        self.last_at_die = 0        # gewerteter Würfel der letzten AT
        self._merken_manöver = None
        self._merken_kampfmod = None
        
        self.json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dice_master_data.json")
        self.master_data = {
            "notizen": [{"titel": "Allgemein", "inhalt": ""}],
            "scs": [],
            "nscs": [],
            "monsters": [],  # nicht-humanoide Gegner (Monster-Tab)
            "ini": [],  # Liste der Ini-Einträge: Vollständige DeepCopies der Chars
            "effect_presets": [],  # selbst erstellte Effekt-Vorlagen
        }
        self.load_from_json()
        # Vorlagen in den gemeinsamen Speicher laden
        load_custom_presets(self.master_data.get("effect_presets") or [])
        # falls Datei älter ohne Key: aus dedizierter Datei-Logik nachziehen
        if not self.master_data.get("effect_presets"):
            load_custom_presets_from_file()
            self.master_data["effect_presets"] = dump_custom_presets()

        self._init_ui()
        self._connect_signals()
        
        self.modified.connect(self.save_to_json)
        
    def _init_ui(self):
        layout = QVBoxLayout(self.form)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.tabs.addTab(self._create_notizen_tab(), "Notizen")
        self.tabs.addTab(self._create_sc_tab(), "SC")
        self.tabs.addTab(self._create_nsc_tab(), "NSC")
        self.tabs.addTab(self._create_monster_tab(), "Monster")
        self.tabs.addTab(self._create_ini_tab(), "INI")
        
    def _connect_signals(self):
        self.tabs.currentChanged.connect(self.load_active_tab)
        self.listThemen.itemDoubleClicked.connect(self.thema_doppelgeklickt)
        self.buttonAddThema.clicked.connect(self.add_thema)
        self.buttonRemoveThema.clicked.connect(self.remove_thema)
        self.listThemen.currentItemChanged.connect(self.thema_gewechselt)
        self.buttonFreeRoll.clicked.connect(self.roll_free_dice)
        self.lineFreeRoll.returnPressed.connect(self.roll_free_dice)
        
        # Roller Signale
        self.dice_roller["increase_btn"].clicked.connect(self.increase_mod)
        self.dice_roller["decrease_btn"].clicked.connect(self.decrease_mod)
        self.dice_roller["execute_btn"].clicked.connect(self.execute_master_roll)
        
    def load_from_json(self):
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.master_data.update(loaded)
            except Exception as e:
                print(f"Fehler beim Laden der DiceMaster Daten: {e}")

    def save_to_json(self):
        try:
            # Effekt-Vorlagen immer aktuell mitschreiben
            self.master_data["effect_presets"] = dump_custom_presets()
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.master_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Fehler beim Speichern der DiceMaster Daten: {e}")

    def load(self):
        self.load_active_tab(self.tabs.currentIndex())

    def load_active_tab(self, index):
        self.currentlyLoading = True
        try:
            tab_name = self.tabs.tabText(index)
            if tab_name == "Notizen": self.load_tagebuch()
            elif tab_name == "SC": self.load_scs()
            elif tab_name == "NSC": self.load_nscs()
            elif tab_name == "Monster": self.load_monsters()
            elif tab_name == "INI": self.load_ini_tab()
        finally:
            self.currentlyLoading = False

    def _create_dice_roll_widget(self):
        widget = QWidget(); layout = QVBoxLayout(widget)
        label_probe = QLabel("<h3>Probe: -</h3>")
        
        options_box = QGroupBox("Optionen"); options_layout = QVBoxLayout(options_box)
        radio3W20 = QRadioButton("3W20 (mittlerer Wurf)")
        radio1W20 = QRadioButton("1W20")
        radio3W20.setChecked(True)
        options_layout.addWidget(radio3W20)
        options_layout.addWidget(radio1W20)
        
        check_global_roll = QCheckBox("Alle würfeln (die markiert sind)")
        check_global_roll.setObjectName("checkGlobalRoll")
        options_layout.addWidget(check_global_roll)

        mod_box = QGroupBox("Modifikatoren"); mod_layout = QHBoxLayout(mod_box)
        decrease_mod_btn = QPushButton("-"); label_mod = QLabel("0"); label_mod.setFixedWidth(30); label_mod.setAlignment(Qt.AlignmentFlag.AlignCenter); increase_mod_btn = QPushButton("+")
        mod_layout.addWidget(decrease_mod_btn); mod_layout.addWidget(label_mod); mod_layout.addWidget(increase_mod_btn)
        
        execute_roll_btn = QPushButton("Würfeln")
        
        label_result = QLabel("Ergebnis: ...")
        label_result.setWordWrap(True)
        label_result.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        # SCs brauchen kein ScrollArea, da nur ein Ergebnis
        
        layout.addWidget(label_probe)
        layout.addWidget(options_box)
        layout.addWidget(mod_box)
        layout.addWidget(execute_roll_btn)
        layout.addWidget(label_result)
        layout.addStretch()
        
        return {
            "widget": widget, "label_probe": label_probe, "radio1W20": radio1W20, 
            "radio3W20": radio3W20, "label_mod": label_mod, "label_result": label_result, 
            "increase_btn": increase_mod_btn, "decrease_btn": decrease_mod_btn,
            "execute_btn": execute_roll_btn
        }

    # --- NSC Roll Widget ---
    def _create_nsc_roll_widget(self):
        # Scrollbarer AT/VT/TP-Bereich (Manöver, Kampfmod, Waffeneigenschaften)
        widget = QWidget()
        outer_layout = QVBoxLayout(widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        try:
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        except Exception:
            pass
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        label_probe = QLabel("<h3>Probe: -</h3>")

        # Options
        options_box = QGroupBox("Optionen"); options_layout = QVBoxLayout(options_box)
        radio3W20 = QRadioButton("3W20 (mittlerer Wurf)")
        radio1W20 = QRadioButton("1W20")
        radio3W20.setChecked(True)
        options_layout.addWidget(radio3W20)
        options_layout.addWidget(radio1W20)

        # Legacy-Reichweite-Keys
        reach_malus_check = QCheckBox()
        reach_bonus_check = QCheckBox()
        reach_box = QGroupBox("Kampfmodifikatoren")
        reach_box.setVisible(False)

        # Manöver – kompaktes 2-Spalten-Grid
        manöver_box = QGroupBox("Manöver")
        manöver_outer = QVBoxLayout(manöver_box)
        manöver_outer.setContentsMargins(4, 4, 4, 4)
        manöver_outer.setSpacing(2)
        manöver_inner = QWidget()
        manöver_layout = QGridLayout(manöver_inner)
        manöver_layout.setContentsMargins(0, 0, 0, 0)
        manöver_layout.setHorizontalSpacing(8)
        manöver_layout.setVerticalSpacing(2)
        manöver_outer.addWidget(manöver_inner)
        manöver_btn_row = QHBoxLayout()
        manöver_merken_btn = QPushButton("Merken")
        manöver_merken_btn.setToolTip("Aktuelle Manöver-Auswahl merken (Tab-/Charakterwechsel)")
        manöver_reset_btn = QPushButton("Zurücksetzen")
        manöver_reset_btn.setToolTip("Manöver zurücksetzen und Merkung löschen")
        manöver_btn_row.addWidget(manöver_merken_btn)
        manöver_btn_row.addWidget(manöver_reset_btn)
        manöver_btn_row.addStretch()
        manöver_outer.addLayout(manöver_btn_row)
        manöver_box.setVisible(False)
        manöver_wuchtschlag = QCheckBox("Wuchtschlag")
        manöver_wuchtschlag_spin = QSpinBox()
        manöver_wuchtschlag_spin.setRange(1, 8)
        manöver_wuchtschlag_spin.setValue(2)
        manöver_wuchtschlag_spin.setPrefix("–")
        manöver_hammerschlag = QCheckBox("Hammerschlag")
        manöver_todesstoß = QCheckBox("Todesstoß")
        manöver_rüstungsbrecher = QCheckBox("Rüstungsbrecher")

        # Modifiers
        mod_box = QGroupBox("Modifikatoren"); mod_layout = QHBoxLayout(mod_box)
        decrease_mod_btn = QPushButton("-"); label_mod = QLabel("0"); label_mod.setFixedWidth(30); label_mod.setAlignment(Qt.AlignmentFlag.AlignCenter); increase_mod_btn = QPushButton("+")
        mod_layout.addWidget(decrease_mod_btn); mod_layout.addWidget(label_mod); mod_layout.addWidget(increase_mod_btn)

        hammerschlag_check = QCheckBox("Hammerschlag (x2 Waffe)")
        mod_layout.addWidget(hammerschlag_check)
        hammerschlag_check.setVisible(False)
        zweite_einfache_check = QCheckBox("Zweite einfache Aktion (−4 AT)")
        zweite_einfache_check.setStyleSheet("margin-left: 10px;")
        zweite_einfache_check.setToolTip(
            "Zweite einfache Aktion im selben Zug: AT −4.\n"
            "Wird bei Voller Defensive automatisch gesetzt."
        )
        mod_layout.addWidget(zweite_einfache_check)
        zweite_einfache_check.setVisible(False)

        aktionen_box = QGroupBox("Aktionen")
        aktionen_layout = QVBoxLayout(aktionen_box)
        aktionen_layout.setContentsMargins(6, 4, 6, 4)
        aktionen_layout.setSpacing(2)
        atemtechnik_check = QCheckBox("Atemtechnik (+1W6 TP)")
        atemtechnik_check.setToolTip("Vorteil Atemtechnik – Freie Aktion, +1W6 TP")
        volle_off_check = QCheckBox("Volle Offensive (+4 AT / −8 VT)")
        volle_off_check.setToolTip(
            "Volle Aktion: Nahkampf-AT +4, VT bis nächste INI −8 "
            "(mit Offensiver Kampfstil −4)."
        )
        volle_def_check = QCheckBox("Volle Defensive (+4 VT)")
        volle_def_check.setToolTip(
            "Volle Aktion: VT +4 bis nächste INI.\n"
            "Mit Defensiver Kampfstil: einfache Aktion (AT weiter möglich).\n"
            "Ohne Defensiver Kampfstil: AT blockiert bis nächste eigene INI.\n"
            "Aktiviert automatisch „Zweite einfache Aktion (−4 AT)“ bei den Modifikatoren."
        )
        aktionen_layout.addWidget(atemtechnik_check)
        aktionen_layout.addWidget(volle_off_check)
        aktionen_layout.addWidget(volle_def_check)
        atemtechnik_check.setVisible(False)
        volle_off_check.setVisible(False)
        volle_def_check.setVisible(False)
        aktionen_box.setVisible(False)
        atemtechnik_check.toggled.connect(self._on_nsc_atemtechnik_toggled)
        volle_off_check.toggled.connect(self._on_nsc_volle_offensive_toggled)
        volle_def_check.toggled.connect(self._on_nsc_volle_defensive_toggled)

        präzision_label = QLabel("")
        präzision_label.setStyleSheet("color: #2a7a2a; font-weight: bold;")
        präzision_label.setWordWrap(True)
        präzision_label.setVisible(False)

        auflaufen_gs_label = QLabel("Gegner-GS (Auflaufen):")
        auflaufen_gs_spin = QSpinBox()
        auflaufen_gs_spin.setRange(0, 20)
        auflaufen_gs_spin.setValue(4)
        auflaufen_gs_spin.setToolTip("Geschwindigkeit des Angreifers – wird zum Waffenschaden addiert.")
        auflaufen_gs_label.setVisible(False)
        auflaufen_gs_spin.setVisible(False)
        auflaufen_row = QHBoxLayout()
        auflaufen_row.addWidget(auflaufen_gs_label)
        auflaufen_row.addWidget(auflaufen_gs_spin)
        auflaufen_row.addStretch()

        def _fill_combo(items):
            cb = QComboBox()
            for text, val in items:
                cb.addItem(text, val)
            return cb

        munition_box = QGroupBox("Munition")
        munition_outer = QVBoxLayout(munition_box)
        munition_outer.setContentsMargins(4, 4, 4, 4)
        munition_host = QWidget()
        QVBoxLayout(munition_host).setContentsMargins(0, 0, 0, 0)
        munition_outer.addWidget(munition_host)
        munition_box.setVisible(False)

        kampfmod_box = QGroupBox("Kampf-Modifikatoren")
        kampfmod_outer = QVBoxLayout(kampfmod_box)
        kampfmod_outer.setContentsMargins(4, 4, 4, 4)
        kampfmod_outer.setSpacing(4)

        nk_panel = QWidget()
        nk_grid = QGridLayout(nk_panel)
        nk_grid.setContentsMargins(0, 0, 0, 0)
        nk_grid.setHorizontalSpacing(6)
        nk_grid.setVerticalSpacing(2)
        nk_pos = _fill_combo(NK_MOD_POSITION)
        nk_rw = _fill_combo(NK_MOD_REICHWEITE)
        nk_ug = _fill_combo(NK_MOD_UNTERGRUND)
        nk_dk = _fill_combo(NK_MOD_DUNKELHEIT)
        nk_grid.addWidget(QLabel("Position:"), 0, 0)
        nk_grid.addWidget(nk_pos, 0, 1)
        nk_grid.addWidget(QLabel("Reichweite:"), 0, 2)
        nk_grid.addWidget(nk_rw, 0, 3)
        nk_grid.addWidget(QLabel("Untergrund:"), 1, 0)
        nk_grid.addWidget(nk_ug, 1, 1)
        nk_grid.addWidget(QLabel("Dunkelheit:"), 1, 2)
        nk_grid.addWidget(nk_dk, 1, 3)
        nk_checks = {}
        nk_check_row = QHBoxLayout()
        for cid, label, val in NK_MOD_CHECKS:
            c = QCheckBox(label)
            c.setProperty("mod_val", val)
            nk_checks[cid] = c
            nk_check_row.addWidget(c)
        nk_check_row.addStretch()
        nk_grid.addLayout(nk_check_row, 2, 0, 1, 4)

        fk_panel = QWidget()
        fk_grid = QGridLayout(fk_panel)
        fk_grid.setContentsMargins(0, 0, 0, 0)
        fk_grid.setHorizontalSpacing(6)
        fk_grid.setVerticalSpacing(2)
        fk_gr = _fill_combo(FK_MOD_GROESSE)
        fk_li = _fill_combo(FK_MOD_LICHT)
        fk_wi = _fill_combo(FK_MOD_WIND)
        fk_be = _fill_combo(FK_MOD_BEWEGUNG)
        fk_de = _fill_combo(FK_MOD_DECKUNG)
        fk_grid.addWidget(QLabel("Zielgröße:"), 0, 0)
        fk_grid.addWidget(fk_gr, 0, 1)
        fk_grid.addWidget(QLabel("Licht:"), 0, 2)
        fk_grid.addWidget(fk_li, 0, 3)
        fk_grid.addWidget(QLabel("Wind:"), 1, 0)
        fk_grid.addWidget(fk_wi, 1, 1)
        fk_grid.addWidget(QLabel("Bewegung:"), 1, 2)
        fk_grid.addWidget(fk_be, 1, 3)
        fk_grid.addWidget(QLabel("Deckung:"), 2, 0)
        fk_grid.addWidget(fk_de, 2, 1)
        fk_checks = {}
        fk_check_row = QHBoxLayout()
        for cid, label, val in FK_MOD_CHECKS:
            c = QCheckBox(label)
            c.setProperty("mod_val", val)
            fk_checks[cid] = c
            fk_check_row.addWidget(c)
        fk_check_row.addStretch()
        fk_grid.addLayout(fk_check_row, 2, 2, 1, 2)

        kampfmod_outer.addWidget(nk_panel)
        kampfmod_outer.addWidget(fk_panel)
        kampfmod_btn_row = QHBoxLayout()
        kampfmod_merken_btn = QPushButton("Merken")
        kampfmod_merken_btn.setToolTip("Aktuelle Kampf-Modifikatoren merken")
        kampfmod_reset_btn = QPushButton("Zurücksetzen")
        kampfmod_reset_btn.setToolTip("Kampf-Modifikatoren zurücksetzen und Merkung löschen")
        kampfmod_btn_row.addWidget(kampfmod_merken_btn)
        kampfmod_btn_row.addWidget(kampfmod_reset_btn)
        kampfmod_btn_row.addStretch()
        kampfmod_outer.addLayout(kampfmod_btn_row)
        nk_panel.setVisible(True)
        fk_panel.setVisible(False)
        kampfmod_box.setVisible(False)

        execute_roll_btn = QPushButton("Würfeln")
        # AT: Passierschlag-Reaktion (zählt & Malus)
        reaktion_btn = QPushButton("Reaktion würfeln")
        reaktion_btn.setToolTip(
            "Reaktion (z. B. Passierschlag): –4 je bereits verbrauchter Reaktion, "
            "Zähler danach +1."
        )
        reaktion_btn.setVisible(False)
        # VT: Freie Reaktion (kein Malus, kein Zähler)
        free_reaktion_btn = QPushButton("Freie Reaktion")
        free_reaktion_btn.setToolTip(
            "Freie Reaktion (z. B. gegen kleinere Größenklasse): "
            "kein Reaktionsmalus, Zähler unverändert."
        )
        free_reaktion_btn.setVisible(False)

        roll_btn_row = QHBoxLayout()
        roll_btn_row.setContentsMargins(0, 0, 0, 0)
        roll_btn_row.addWidget(execute_roll_btn)
        roll_btn_row.addWidget(reaktion_btn)
        roll_btn_row.addWidget(free_reaktion_btn)

        continue_btn = QPushButton("Weiter → Schaden")
        continue_btn.setVisible(False)
        continue_btn.setStyleSheet("font-weight: bold;")

        label_result = QLabel("Ergebnis: ...")
        label_result.setWordWrap(True)

        triumph_wrap = QWidget()
        triumph_layout = QHBoxLayout(triumph_wrap)
        triumph_layout.setContentsMargins(0, 2, 0, 2)
        triumph_label = QLabel("")
        triumph_label.setWordWrap(True)
        triumph_layout.addWidget(triumph_label, 1)
        triumph_wrap.setVisible(False)

        # Kompakt ausklappbare Waffeneigenschaften (AT/VT/TP)
        waffeig_wrap = QWidget()
        waffeig_v = QVBoxLayout(waffeig_wrap)
        waffeig_v.setContentsMargins(0, 0, 0, 0)
        waffeig_v.setSpacing(2)
        waffeig_toggle = QToolButton()
        waffeig_toggle.setText("▸ Waffeneigenschaften")
        waffeig_toggle.setCheckable(True)
        waffeig_toggle.setChecked(False)
        waffeig_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        waffeig_toggle.setStyleSheet("QToolButton { border: none; font-weight: bold; text-align: left; padding: 2px; }")
        waffeig_toggle.setToolTip("Eigenschaften der aktuellen Waffe anzeigen")
        waffeig_body = QTextBrowser()
        waffeig_body.setOpenExternalLinks(False)
        waffeig_body.setStyleSheet("color:#333; padding:2px 4px 4px 8px; border: none; background: transparent;")
        waffeig_body.setVisible(False)
        waffeig_body.setMinimumHeight(40)
        waffeig_body.setMaximumHeight(220)
        try:
            waffeig_body.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            waffeig_body.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        except Exception:
            pass

        def _toggle_waffeig(on):
            waffeig_body.setVisible(bool(on))
            waffeig_toggle.setText(("▾" if on else "▸") + " Waffeneigenschaften")
        waffeig_toggle.toggled.connect(_toggle_waffeig)
        waffeig_v.addWidget(waffeig_toggle)
        waffeig_v.addWidget(waffeig_body)
        waffeig_wrap.setVisible(False)
        # Aliase für bestehenden Code
        waffeig_box = waffeig_wrap
        waffeig_browser = waffeig_body

        layout.addWidget(label_probe)
        layout.addWidget(options_box)
        layout.addWidget(manöver_box)
        layout.addWidget(aktionen_box)
        layout.addWidget(mod_box)
        layout.addWidget(präzision_label)
        layout.addLayout(auflaufen_row)
        layout.addLayout(roll_btn_row)
        layout.addWidget(continue_btn)
        layout.addWidget(label_result)
        layout.addWidget(triumph_wrap)
        layout.addWidget(munition_box)
        layout.addWidget(kampfmod_box)
        layout.addWidget(waffeig_box)
        layout.addStretch()

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        return {
            "widget": widget, "label_probe": label_probe,
            "radio1W20": radio1W20, "radio3W20": radio3W20, "options_box": options_box,
            "reach_box": reach_box, "reach_malus": reach_malus_check, "reach_bonus": reach_bonus_check,
            "manöver_box": manöver_box,
            "manöver_layout": manöver_layout,
            "manöver_inner": manöver_inner,
            "waffeig_box": waffeig_box,
            "waffeig_browser": waffeig_browser,
            "waffeig_toggle": waffeig_toggle,
            "waffeig_body": waffeig_body,
            "kampfmod_box": kampfmod_box,
            "munition_box": munition_box,
            "munition_host": munition_host,
            "nk_panel": nk_panel,
            "fk_panel": fk_panel,
            "nk_combos": {"position": nk_pos, "reichweite": nk_rw, "untergrund": nk_ug, "dunkelheit": nk_dk},
            "fk_combos": {"groesse": fk_gr, "licht": fk_li, "wind": fk_wi, "bewegung": fk_be, "deckung": fk_de},
            "nk_checks": nk_checks,
            "fk_checks": fk_checks,
            "manöver_widgets": {},
            "manöver_wuchtschlag": manöver_wuchtschlag,
            "manöver_wuchtschlag_spin": manöver_wuchtschlag_spin,
            "manöver_hammerschlag": manöver_hammerschlag,
            "manöver_todesstoß": manöver_todesstoß,
            "manöver_rüstungsbrecher": manöver_rüstungsbrecher,
            "label_mod": label_mod, "increase_btn": increase_mod_btn, "decrease_btn": decrease_mod_btn,
            "atemtechnik_check": atemtechnik_check, "hammerschlag_check": hammerschlag_check,
            "zweite_einfache_check": zweite_einfache_check,
            "aktionen_box": aktionen_box,
            "volle_off_check": volle_off_check,
            "volle_def_check": volle_def_check,
            "präzision_label": präzision_label,
            "auflaufen_gs_label": auflaufen_gs_label,
            "auflaufen_gs_spin": auflaufen_gs_spin,
            "execute_btn": execute_roll_btn,
            "reaktion_btn": reaktion_btn,
            "free_reaktion_btn": free_reaktion_btn,
            "continue_btn": continue_btn,
            "label_result": label_result,
            "triumph_wrap": triumph_wrap,
            "triumph_label": triumph_label,
            "manöver_merken_btn": manöver_merken_btn,
            "manöver_reset_btn": manöver_reset_btn,
            "kampfmod_merken_btn": kampfmod_merken_btn,
            "kampfmod_reset_btn": kampfmod_reset_btn,
        }

    def _create_notizen_tab(self):
        tab = QWidget()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_widget = QWidget(); left_layout = QVBoxLayout(left_widget)
        
        free_roll_box = QGroupBox("Freies Würfeln"); free_roll_layout = QVBoxLayout(free_roll_box)
        input_layout = QHBoxLayout()
        self.lineFreeRoll = QLineEdit(); self.lineFreeRoll.setPlaceholderText("z.B. 2W6+3 oder W20")
        self.buttonFreeRoll = QPushButton("🎲"); self.buttonFreeRoll.setFixedWidth(40)
        input_layout.addWidget(self.lineFreeRoll); input_layout.addWidget(self.buttonFreeRoll)
        self.labelFreeRollResult = QLabel("Ergebnis: "); self.labelFreeRollResult.setWordWrap(True)
        free_roll_layout.addLayout(input_layout); free_roll_layout.addWidget(self.labelFreeRollResult)
        left_layout.addWidget(free_roll_box)
        
        tagebuch_box = QGroupBox("Themen"); themen_box_layout = QVBoxLayout(tagebuch_box)
        self.listThemen = QListWidget(); self.listThemen.setToolTip("Doppelklicken zum Umbenennen")
        themen_buttons_layout = QHBoxLayout()
        self.buttonAddThema = QPushButton("Hinzufügen"); self.buttonRemoveThema = QPushButton("Entfernen")
        themen_buttons_layout.addWidget(self.buttonAddThema); themen_buttons_layout.addWidget(self.buttonRemoveThema)
        themen_box_layout.addWidget(self.listThemen); themen_box_layout.addLayout(themen_buttons_layout)
        left_layout.addWidget(tagebuch_box)
        
        right_widget = QWidget(); right_layout = QVBoxLayout(right_widget)
        self.stackedThemaInhalt = QStackedWidget()
        right_layout.addWidget(self.stackedThemaInhalt)
        splitter.addWidget(left_widget); splitter.addWidget(right_widget); splitter.setSizes([200, 400])
        main_layout = QHBoxLayout(tab); main_layout.addWidget(splitter)
        return tab

    def roll_free_dice(self):
        dice_string = self.lineFreeRoll.text()
        if not dice_string: self.labelFreeRollResult.setText("Ergebnis: Bitte eine Würfelnotation eingeben."); return
        total, result_string = parse_and_roll_dice_string(dice_string)
        self.labelFreeRollResult.setText(result_string)

    def load_tagebuch(self):
        self.listThemen.blockSignals(True)
        while self.stackedThemaInhalt.count() > 0: 
            self.stackedThemaInhalt.removeWidget(self.stackedThemaInhalt.widget(0))
        self.thema_text_edits.clear(); self.listThemen.clear()
        
        data = self.master_data["notizen"]
        for i, t in enumerate(data): self._add_thema_widgets(i, t)
        self.listThemen.blockSignals(False)
        if self.listThemen.count() > 0: self.listThemen.setCurrentRow(0)

    def _add_thema_widgets(self, index, thema_data):
        widget = QWidget(); layout = QHBoxLayout(widget); layout.setContentsMargins(4, 2, 4, 2); layout.setSpacing(5)
        move_buttons_layout = QVBoxLayout(); move_buttons_layout.setSpacing(0)
        up_button = QToolButton(); up_button.setArrowType(Qt.ArrowType.UpArrow); up_button.clicked.connect(lambda _, i=index: self.move_thema(i, -1))
        down_button = QToolButton(); down_button.setArrowType(Qt.ArrowType.DownArrow); down_button.clicked.connect(lambda _, i=index: self.move_thema(i, 1))
        move_buttons_layout.addWidget(up_button); move_buttons_layout.addWidget(down_button)
        label = QLabel(thema_data["titel"]); layout.addLayout(move_buttons_layout); layout.addWidget(label); layout.addStretch()
        item = QListWidgetItem(); item.setSizeHint(widget.sizeHint())
        self.listThemen.addItem(item); self.listThemen.setItemWidget(item, widget)
        text_edit = QPlainTextEdit(); text_edit.setPlainText(thema_data["inhalt"]); text_edit.textChanged.connect(self.thema_inhalt_geaendert)
        self.thema_text_edits.append(text_edit); self.stackedThemaInhalt.addWidget(text_edit)

    def move_thema(self, index, direction):
        data = self.master_data["notizen"]
        new_index = index + direction
        if new_index < 0 or new_index >= len(data): return
        data[index], data[new_index] = data[new_index], data[index]
        self.load_tagebuch(); self.listThemen.setCurrentRow(new_index); self.modified.emit()

    def add_thema(self):
        self.master_data["notizen"].append({"titel": "Neues Thema", "inhalt": ""})
        self.load_tagebuch(); self.listThemen.setCurrentRow(self.listThemen.count() - 1); self.modified.emit()

    def remove_thema(self):
        row = self.listThemen.currentRow()
        if row != -1: 
            del self.master_data["notizen"][row]
            self.load_tagebuch()
            self.modified.emit()

    def thema_doppelgeklickt(self, item):
        row = self.listThemen.row(item)
        if row == -1: return
        thema = self.master_data["notizen"][row]
        new_title, ok = QInputDialog.getText(self.form, "Thema umbenennen", "Neuer Titel:", QLineEdit.EchoMode.Normal, thema["titel"])
        if ok and new_title: thema["titel"] = new_title; self.load_tagebuch(); self.modified.emit()

    def thema_gewechselt(self, current, previous):
        if current: self.stackedThemaInhalt.setCurrentIndex(self.listThemen.row(current))

    def thema_inhalt_geaendert(self):
        if self.currentlyLoading: return
        row = self.stackedThemaInhalt.currentIndex()
        if row != -1 and row < len(self.master_data["notizen"]): 
            self.master_data["notizen"][row]["inhalt"] = self.thema_text_edits[row].toPlainText(); self.modified.emit()

    # --- SC Tab Logic ---
    def _create_sc_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_area = QScrollArea()
        left_area.setWidgetResizable(True)
        self.sc_container = QWidget()
        self.sc_layout = QVBoxLayout(self.sc_container)
        self.sc_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.sc_layout.addStretch() 
        left_area.setWidget(self.sc_container)
        
        left_wrapper = QWidget()
        left_wrapper_layout = QVBoxLayout(left_wrapper)
        self.btn_add_sc = QPushButton("SC hinzufügen")
        self.btn_add_sc.clicked.connect(self.add_sc)
        left_wrapper_layout.addWidget(self.btn_add_sc)
        left_wrapper_layout.addWidget(left_area)
        
        self.dice_roller = self._create_dice_roll_widget()
        self.dice_roller["widget"].setEnabled(False)
        
        splitter.addWidget(left_wrapper)
        splitter.addWidget(self.dice_roller["widget"])
        splitter.setSizes([400, 300])
        main_layout.addWidget(splitter)
        return tab

    def load_scs(self):
        while self.sc_layout.count() > 1:
            item = self.sc_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.sc_widgets.clear()
        
        data = self.master_data["scs"]
        
        for i, sc_data in enumerate(data):
            widget = SCWidget(sc_data)
            widget._plugin_ref = self
            widget.rollRequested.connect(self.prepare_master_roll)
            widget.dataChanged.connect(self.modified.emit)
            widget.removeRequested.connect(partial(self.remove_sc, i))
            widget.moveUpRequested.connect(partial(self.move_sc, i, -1))
            widget.moveDownRequested.connect(partial(self.move_sc, i, 1))
            self.sc_layout.insertWidget(i, widget)
            self.sc_widgets.append(widget)

    def add_sc(self):
        new_sc = {
            "name": "Neuer SC", "notizen": "", "alle_wuerfeln": False, "wunden_ignorieren": False,
            "val_ini": 0, "val_mr": 0, "val_in": 0, "val_wachsamkeit": 0, "val_menschenkenntnis": 0,
            "wunden": [None]*8, "effekte": []
        }
        self.master_data["scs"].append(new_sc)
        self.load_scs()
        self.modified.emit()

    def remove_sc(self, index):
        if 0 <= index < len(self.master_data["scs"]):
            del self.master_data["scs"][index]
            self.load_scs()
            self.modified.emit()

    def move_sc(self, index, direction):
        data = self.master_data["scs"]
        new_index = index + direction
        if new_index < 0 or new_index >= len(data): return
        data[index], data[new_index] = data[new_index], data[index]
        self.load_scs()
        self.modified.emit()
    
    # --- NSC Tab Logic ---
    def _create_nsc_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_area = QScrollArea()
        left_area.setWidgetResizable(True)
        self.nsc_container = QWidget()
        self.nsc_layout = QVBoxLayout(self.nsc_container)
        self.nsc_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.nsc_layout.addStretch() 
        left_area.setWidget(self.nsc_container)
        
        left_wrapper = QWidget()
        left_wrapper_layout = QVBoxLayout(left_wrapper)
        self.btn_add_nsc = QPushButton("NSC hinzufügen")
        self.btn_add_nsc.clicked.connect(self.add_nsc)
        left_wrapper_layout.addWidget(self.btn_add_nsc)
        left_wrapper_layout.addWidget(left_area)
        
        # NSC Roll Widget
        self.nsc_dice_roller = self._create_nsc_roll_widget()
        self.nsc_dice_roller["widget"].setEnabled(False)
        self.nsc_dice_roller["increase_btn"].clicked.connect(self.increase_mod_nsc)
        self.nsc_dice_roller["decrease_btn"].clicked.connect(self.decrease_mod_nsc)
        self.nsc_dice_roller["continue_btn"].clicked.connect(self.continue_to_damage_nsc)
        self._bind_reaktion_buttons(self.nsc_dice_roller, ini=False)
        
        splitter.addWidget(left_wrapper)
        splitter.addWidget(self.nsc_dice_roller["widget"])
        splitter.setSizes([400, 300])
        main_layout.addWidget(splitter)
        return tab
    
    def load_nscs(self):
        while self.nsc_layout.count() > 1:
            item = self.nsc_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        self.nsc_widgets.clear()
        data = self.master_data["nscs"]
        
        for i, nsc_data in enumerate(data):
            widget = NSCWidget(nsc_data)
            widget._plugin_ref = self
            widget.rollRequested.connect(self.prepare_master_roll_nsc)
            widget.atRollRequested.connect(self.prepare_at_roll_nsc)
            widget.tpRollRequested.connect(self.roll_tp_nsc)
            widget.dataChanged.connect(self.modified.emit)
            widget.removeRequested.connect(partial(self.remove_nsc, i))
            widget.moveUpRequested.connect(partial(self.move_nsc, i, -1))
            widget.moveDownRequested.connect(partial(self.move_nsc, i, 1))
            
            self.nsc_layout.insertWidget(i, widget)
            self.nsc_widgets.append(widget)

    def add_nsc(self):
        new_nsc = {
            "name": "Neuer NSC", "notizen": "", "alle_wuerfeln": False, "wunden_ignorieren": False,
            "wunden_modus": 0, 
            "val_asp": 0, "val_kap": 0,
            "attributes": {"MU":0, "KL":0, "IN":0, "CH":0, "FF":0, "GE":0, "KO":0, "KK":0, "INI":0, "MR":0, "WS":0, "WS*":0, "GS":0},
            # Standard-Fertigkeiten für jeden neuen NSC
            "skills": [
                {"name": "Selbstbeherrschung", "val": 0},
                {"name": "Wahrnehmung", "val": 0},
            ],
            "powers": [], "weapons": [],
            "wunden": [None]*8, "effekte": []
        }
        self.master_data["nscs"].append(new_nsc)
        self.load_nscs()
        self.modified.emit()

    def remove_nsc(self, index):
        if 0 <= index < len(self.master_data["nscs"]):
            del self.master_data["nscs"][index]
            self.load_nscs()
            self.modified.emit()

    def move_nsc(self, index, direction):
        data = self.master_data["nscs"]
        new_index = index + direction
        if new_index < 0 or new_index >= len(data): return
        data[index], data[new_index] = data[new_index], data[index]
        self.load_nscs()
        self.modified.emit()

    # --- Monster Tab Logic (Idee A, Iteration 1) ---
    def _create_monster_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_area = QScrollArea()
        left_area.setWidgetResizable(True)
        self.monster_container = QWidget()
        self.monster_layout = QVBoxLayout(self.monster_container)
        self.monster_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.monster_layout.addStretch()
        left_area.setWidget(self.monster_container)

        left_wrapper = QWidget()
        left_wrapper_layout = QVBoxLayout(left_wrapper)
        self.btn_add_monster = QPushButton("Monster hinzufügen")
        self.btn_add_monster.clicked.connect(self.add_monster)
        left_wrapper_layout.addWidget(self.btn_add_monster)
        # Warnung, falls MonsterWidget.py / MonsterHelper.py fehlen
        if not _MONSTER_WIDGET_OK:
            warn = QLabel(
                "<b>Monster-Modul fehlt oder fehlerhaft.</b><br>"
                "Bitte im Plugin-Ordner ablegen:<br>"
                "<code>MonsterWidget.py</code>, <code>MonsterHelper.py</code>, "
                "<code>monster_katalog.json</code><br>"
                + (f"<span style='color:#a33'>{_MONSTER_IMPORT_ERROR}</span>" if _MONSTER_IMPORT_ERROR else "")
            )
            warn.setWordWrap(True)
            warn.setStyleSheet(
                "background:#3a2020; color:#fcc; padding:8px; border-radius:4px;"
            )
            left_wrapper_layout.addWidget(warn)
        left_wrapper_layout.addWidget(left_area)

        # Eigener Würfelbereich (gleiche Logik wie NSC)
        self.monster_dice_roller = self._create_nsc_roll_widget()
        self.monster_dice_roller["widget"].setEnabled(False)
        self.monster_dice_roller["increase_btn"].clicked.connect(self.increase_mod_monster)
        self.monster_dice_roller["decrease_btn"].clicked.connect(self.decrease_mod_monster)
        self.monster_dice_roller["continue_btn"].clicked.connect(self.continue_to_damage_monster)
        self._bind_reaktion_buttons(self.monster_dice_roller, ini=False)
        # Execute/Reaktion müssen den Monster-Roller nutzen (Swap auf nsc_dice_roller)
        for key, mode in (
            ("execute_btn", "normal"),
            ("reaktion_btn", "reaktion"),
            ("free_reaktion_btn", "freie_reaktion"),
        ):
            btn = self.monster_dice_roller.get(key)
            if btn is None:
                continue
            try:
                btn.clicked.disconnect()
            except TypeError:
                pass
            btn.clicked.connect(
                lambda checked=False, m=mode: self._execute_monster_with_mode(m)
            )

        splitter.addWidget(left_wrapper)
        splitter.addWidget(self.monster_dice_roller["widget"])
        splitter.setSizes([400, 300])
        main_layout.addWidget(splitter)
        return tab

    def load_monsters(self):
        while self.monster_layout.count() > 1:
            item = self.monster_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.monster_widgets.clear()
        data = self.master_data.setdefault("monsters", [])
        for i, mdata in enumerate(data):
            mdata.setdefault("kind", "monster")
            widget = MonsterWidget(mdata)
            widget._plugin_ref = self
            widget.rollRequested.connect(self.prepare_master_roll_monster)
            widget.atRollRequested.connect(self.prepare_at_roll_monster)
            widget.tpRollRequested.connect(self.roll_tp_monster)
            widget.dataChanged.connect(self.modified.emit)
            widget.removeRequested.connect(partial(self.remove_monster, i))
            widget.moveUpRequested.connect(partial(self.move_monster, i, -1))
            widget.moveDownRequested.connect(partial(self.move_monster, i, 1))
            self.monster_layout.insertWidget(i, widget)
            self.monster_widgets.append(widget)

    def add_monster(self):
        self.master_data.setdefault("monsters", []).append(default_monster_data("Neues Monster"))
        self.load_monsters()
        self.modified.emit()

    def remove_monster(self, index):
        data = self.master_data.setdefault("monsters", [])
        if 0 <= index < len(data):
            del data[index]
            self.load_monsters()
            self.modified.emit()

    def move_monster(self, index, direction):
        data = self.master_data.setdefault("monsters", [])
        new_index = index + direction
        if new_index < 0 or new_index >= len(data):
            return
        data[index], data[new_index] = data[new_index], data[index]
        self.load_monsters()
        self.modified.emit()

    def increase_mod_monster(self):
        self.custom_mod_value += 1
        self.monster_dice_roller["label_mod"].setText(str(self.custom_mod_value))

    def decrease_mod_monster(self):
        self.custom_mod_value -= 1
        self.monster_dice_roller["label_mod"].setText(str(self.custom_mod_value))

    def _with_monster_roller(self, fn):
        """Führt NSC-Roll-Logik auf dem Monster-Würfelbereich aus."""
        backup = self.nsc_dice_roller
        self.nsc_dice_roller = self.monster_dice_roller
        try:
            return fn()
        finally:
            self.nsc_dice_roller = backup

    def prepare_master_roll_monster(self, widget, name, value):
        self._with_monster_roller(lambda: self.prepare_master_roll_nsc(widget, name, value))

    def prepare_at_roll_monster(self, widget, name, value, tp_string):
        self._with_monster_roller(
            lambda: self.prepare_at_roll_nsc(widget, name, value, tp_string)
        )

    def roll_tp_monster(self, widget, name, tp_string):
        self._with_monster_roller(lambda: self.roll_tp_nsc(widget, name, tp_string))

    def continue_to_damage_monster(self):
        self._with_monster_roller(self.continue_to_damage_nsc)

    def execute_monster_roll(self):
        self._with_monster_roller(self.execute_master_roll_nsc)

    def _execute_monster_with_mode(self, mode):
        self._roll_mode = mode or "normal"
        self.execute_monster_roll()

    # --- INI TAB LOGIC ---
    def _create_ini_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # LINKS: Kampfverlauf (Liste der Widgets)
        left_wrapper = QWidget()
        left_wrapper_layout = QVBoxLayout(left_wrapper)
        
        # Header Controls
        control_layout = QHBoxLayout()
        btn_add = QPushButton("+ Kämpfer")
        btn_add.clicked.connect(self.add_selected_to_ini)
        control_layout.addWidget(btn_add)

        btn_sort = QPushButton("Sortieren (INI)")
        btn_sort.clicked.connect(self.sort_ini)
        control_layout.addWidget(btn_sort)
        
        btn_next = QPushButton("Nächste INI")
        btn_next.setStyleSheet("font-weight: bold; padding: 5px;")
        btn_next.clicked.connect(self.next_initiative)
        control_layout.addWidget(btn_next)
        
        left_wrapper_layout.addLayout(control_layout)
        
        # Scroll Area for INI entries
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.ini_container = QWidget()
        self.ini_layout = QVBoxLayout(self.ini_container)
        self.ini_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.ini_layout.addStretch() # Push items up
        scroll.setWidget(self.ini_container)
        left_wrapper_layout.addWidget(scroll)

        # RECHTS: Würfelbereich (Wie NSC Roller)
        self.ini_dice_roller = self._create_nsc_roll_widget()
        self.ini_dice_roller["widget"].setEnabled(False)
        self.ini_dice_roller["increase_btn"].clicked.connect(self.increase_mod_ini)
        self.ini_dice_roller["decrease_btn"].clicked.connect(self.decrease_mod_ini)
        self.ini_dice_roller["execute_btn"].clicked.connect(self.execute_ini_roll)
        self.ini_dice_roller["continue_btn"].clicked.connect(self.continue_to_damage_ini)
        self._bind_reaktion_buttons(self.ini_dice_roller, ini=True)
        
        splitter.addWidget(left_wrapper)
        splitter.addWidget(self.ini_dice_roller["widget"])
        splitter.setSizes([450, 350])
        main_layout.addWidget(splitter)
        return tab

    def load_ini_tab(self):
        self.update_ini_list_ui()

    def add_selected_to_ini(self):
        # Öffne Popup Dialog
        dlg = IniSelectorDialog(
            self.master_data.get("scs") or [],
            self.master_data.get("nscs") or [],
            self.form,
            monster_list=self.master_data.get("monsters") or [],
        )
        # Verbinde das Signal mit unserer neuen Verarbeitungs-Funktion
        dlg.entrySelected.connect(self.process_ini_selection)
        # exec() blockiert nur das UI, schließt aber nicht mehr bei Auswahl
        dlg.exec()

    def process_ini_selection(self, data_ref):
        if not data_ref: return
        
        source_data = None
        entry_type = data_ref.get("type") or "sc"
        idx = data_ref.get("index", 0)
        if entry_type == "sc":
            source_data = self.master_data["scs"][idx]
        elif entry_type == "monster":
            source_data = self.master_data.setdefault("monsters", [])[idx]
        else:
            source_data = self.master_data["nscs"][idx]
        
        # Echte KOPIE erstellen
        new_entry = copy.deepcopy(source_data)
        
        # Name eindeutig machen (Nummerierung bei NSC/Monster)
        base_name = new_entry.get("name", "Unbekannt")
        if entry_type != "sc":
            count = 0
            for entry in self.master_data["ini"]:
                if entry.get("name", "").startswith(base_name):
                    count += 1
            if count > 0:
                new_entry["name"] = f"{base_name} #{count+1}"

        # Metadaten für INI hinzufügen
        new_entry["ini_type"] = entry_type  # sc | nsc | monster
        if entry_type == "monster":
            new_entry["kind"] = "monster"
        new_entry["active"] = False
        
        self.master_data["ini"].append(new_entry)
        self.modified.emit()
        self.update_ini_list_ui()

    def update_ini_list_ui(self):
        # UI neu aufbauen basierend auf self.master_data["ini"]
        while self.ini_layout.count() > 1: # 1 wegen stretch
            child = self.ini_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        self.ini_widgets = []
        
        for i, entry in enumerate(self.master_data["ini"]):
            ini_type = entry.get("ini_type", "sc")
            widget = None
            
            if ini_type == "sc":
                widget = SCWidget(entry, show_ini_header=True)
                widget._plugin_ref = self
                widget.check_roll_all.setVisible(False)
                widget.rollRequested.connect(self.prepare_ini_roll)
            elif ini_type == "monster":
                entry.setdefault("kind", "monster")
                widget = MonsterWidget(entry, show_ini_header=True)
                widget._plugin_ref = self
                if hasattr(widget, "check_roll_all"):
                    widget.check_roll_all.setVisible(False)
                widget.rollRequested.connect(self.prepare_ini_roll)
                widget.atRollRequested.connect(self.prepare_at_roll_ini)
                widget.tpRollRequested.connect(self.prepare_ini_tp_roll)
            else:
                widget = NSCWidget(entry, show_ini_header=True)
                widget._plugin_ref = self
                widget.check_roll_all.setVisible(False)
                widget.rollRequested.connect(self.prepare_ini_roll)
                widget.atRollRequested.connect(self.prepare_at_roll_ini)
                widget.tpRollRequested.connect(self.prepare_ini_tp_roll)
            
            # Signale verbinden
            widget.removeRequested.connect(partial(self.remove_ini_entry, i))
            widget.moveUpRequested.connect(partial(self.move_ini_entry, i, -1))
            widget.moveDownRequested.connect(partial(self.move_ini_entry, i, 1))
            widget.dataChanged.connect(self.modified.emit)
            
            self.ini_layout.insertWidget(i, widget)
            self.ini_widgets.append(widget)

    def remove_ini_entry(self, index):
        if 0 <= index < len(self.master_data["ini"]):
            del self.master_data["ini"][index]
            self.modified.emit()
            self.update_ini_list_ui()

    def move_ini_entry(self, index, direction):
        data = self.master_data["ini"]
        new_index = index + direction
        if new_index < 0 or new_index >= len(data): return
        data[index], data[new_index] = data[new_index], data[index]
        self.modified.emit()
        self.update_ini_list_ui()

    def sort_ini(self):
        # Alle UI Werte speichern bevor wir sortieren!
        for w in self.ini_widgets:
            w.save_data()
            
        def sort_key(entry):
            # INI wert holen. SCs und NSCs speichern das nun dank "Header Sync" verlässlich in 'val_ini'
            val = entry.get("val_ini", 0)
            # Typ Score: SC (0) < NSC (1) -> SC kommt zuerst bei gleichem INI Wert
            type_score = 0 if entry.get("ini_type") == "sc" else 1
            return (-val, type_score)
            
        self.master_data["ini"].sort(key=sort_key)
        self.modified.emit()
        self.update_ini_list_ui()

    def next_initiative(self):
        data = self.master_data["ini"]
        if not data: return
        
        # Finde aktuellen Index
        current_idx = -1
        for i, entry in enumerate(data):
            if entry.get("active", False):
                current_idx = i
                break
        
        # Setze aktuellen inaktiv und klappe ihn zu (Übersicht behalten)
        if current_idx != -1:
            data[current_idx]["active"] = False
            if current_idx < len(self.ini_widgets):
                self.ini_widgets[current_idx].update_style()
                self.ini_widgets[current_idx].set_expanded(False)
            
        # Suche nächsten (inklusive wrap-around)
        start_idx = current_idx + 1
        found_idx = -1
        
        for i in range(len(data) * 2):
            idx = (start_idx + i) % len(data)
            if not data[idx].get("ko", False):
                found_idx = idx
                break
        
        if found_idx != -1:
            data[found_idx]["active"] = True
            data[found_idx]["reaktionen"] = 0  # neue eigene Phase → Reaktionen zurück
            if found_idx < len(self.ini_widgets):
                w = self.ini_widgets[found_idx]
                w.update_style()
                # Effekte ticken, wenn der Charakter wieder an der Reihe ist
                if hasattr(w, "decrement_all_effects"):
                    w.decrement_all_effects()
                if hasattr(w, "reset_reaktionen"):
                    w.reset_reaktionen()
                w.set_expanded(True)
                w.setFocus()
        
        self.modified.emit()

    # --- INI Rolling Logic (Reusing NSC Logic but separate state) ---
    def prepare_ini_roll(self, widget, attr_name, value):
        self.ini_dice_roller["widget"].setEnabled(True)
        self.active_ini_widget = widget
        self.active_attribute_name = attr_name
        self.active_attribute_value = value
        self.active_tp_string = None
        self._reset_nsc_roller_ui(self.ini_dice_roller)

        name = widget.data.get("name", "Kämpfer")
        self.ini_dice_roller["label_probe"].setText(f"<h3>Probe: {name} - {attr_name} ({value})</h3>")

        # Vorteile vor Manöver-Filter speichern
        widget.save_data()
        is_combat = "AT " in attr_name or "VT " in attr_name
        if is_combat:
            self.ini_dice_roller["radio1W20"].setChecked(True)
            self.ini_dice_roller["options_box"].setVisible(False)
            self.ini_dice_roller["reach_box"].setVisible(False)
            if "AT " in attr_name or "VT " in attr_name:
                self.ini_dice_roller["manöver_box"].setVisible(True)
                ptype = "VT" if "VT " in attr_name else "AT"
                self._apply_manöver_availability_nsc(self.ini_dice_roller, widget, probe_type=ptype)
                if self._merken_manöver:
                    self._restore_manöver_from_memory(self.ini_dice_roller)
            self._show_kampfmod_for_probe(self.ini_dice_roller, attr_name, widget)
            if self._merken_kampfmod:
                self._restore_kampfmod_from_memory(self.ini_dice_roller)
            self._update_reaktion_buttons(self.ini_dice_roller, attr_name)
        else:
            self.ini_dice_roller["radio3W20"].setChecked(True)
            self.ini_dice_roller["options_box"].setVisible(True)
            self.ini_dice_roller["reach_box"].setVisible(False)
            if "kampfmod_box" in self.ini_dice_roller:
                self.ini_dice_roller["kampfmod_box"].setVisible(False)
            self._update_reaktion_buttons(self.ini_dice_roller, attr_name)

    def prepare_ini_tp_roll(self, widget, name, tp_string):
        self._last_nsc_prepare = {
            "kind": "tp_ini",
            "name": name,
            "tp_string": tp_string or "",
        }
        self.ini_dice_roller["widget"].setEnabled(True)
        self.active_ini_widget = widget
        self.active_tp_string = tp_string
        self.active_attribute_name = f"TP {name}"
        self._reset_nsc_roller_ui(self.ini_dice_roller)
        self.ini_dice_roller["options_box"].setVisible(False)
        self.ini_dice_roller["reach_box"].setVisible(False)
        self.ini_dice_roller["manöver_box"].setVisible(False)
        if "reaktion_btn" in self.ini_dice_roller:
            self.ini_dice_roller["reaktion_btn"].setVisible(False)
        if "free_reaktion_btn" in self.ini_dice_roller:
            self.ini_dice_roller["free_reaktion_btn"].setVisible(False)
        self.ini_dice_roller["hammerschlag_check"].setVisible(False)
        self._sync_aktionen_checks_nsc(
            self.ini_dice_roller, widget, is_tp=True, is_at=False, is_vt=False
        )
        self.ini_dice_roller["label_probe"].setText(f"<h3>Schaden: {name} ({tp_string})</h3>")
        self.ini_dice_roller["label_result"].setText("Bereit...")
        widget.save_data()

    def increase_mod_ini(self): 
        self.custom_mod_value += 1; self.ini_dice_roller["label_mod"].setText(str(self.custom_mod_value))
    def decrease_mod_ini(self):
        self.custom_mod_value -= 1; self.ini_dice_roller["label_mod"].setText(str(self.custom_mod_value))

    def execute_ini_roll(self):
        # Wir leiten an die NSC Logik weiter, setzen aber temporär die NSC Variablen
        
        backup_widget = self.active_sc_widget
        backup_nsc_roller = self.nsc_dice_roller
        
        self.active_sc_widget = self.active_ini_widget
        self.nsc_dice_roller = self.ini_dice_roller # Pointer Swapping für die Funktion
        
        try:
            self.execute_master_roll_nsc()
        finally:
            self.active_sc_widget = backup_widget
            self.nsc_dice_roller = backup_nsc_roller


    # --- Rolling Logic ---

    def prepare_master_roll(self, sc_widget, attr_name, value):
        self.dice_roller["widget"].setEnabled(True)
        self.active_sc_widget = sc_widget
        self.active_attribute_name = attr_name
        self.active_attribute_value = value
        self.custom_mod_value = 0
        self.dice_roller["label_mod"].setText("0")
        self.dice_roller["label_result"].setText("Bereit...")
        sc_name = sc_widget.data.get("name", "SC")
        self.dice_roller["label_probe"].setText(f"<h3>Probe: {sc_name} - {attr_name} ({value})</h3>")
        
        sc_widget.save_data()

    def _bind_reaktion_buttons(self, roller, ini=False):
        """Verbindet Reaktion-/Freie-Reaktion-Tasten mit dem passenden Execute-Pfad."""
        if not roller:
            return
        if ini:
            roller["execute_btn"].clicked.disconnect()
            roller["execute_btn"].clicked.connect(lambda: self._execute_with_roll_mode("normal", ini=True))
            roller["reaktion_btn"].clicked.connect(lambda: self._execute_with_roll_mode("reaktion", ini=True))
            roller["free_reaktion_btn"].clicked.connect(lambda: self._execute_with_roll_mode("freie_reaktion", ini=True))
        else:
            # execute_btn already connected to execute_master_roll_nsc – rebind for mode
            try:
                roller["execute_btn"].clicked.disconnect()
            except TypeError:
                pass
            roller["execute_btn"].clicked.connect(lambda: self._execute_with_roll_mode("normal", ini=False))
            roller["reaktion_btn"].clicked.connect(lambda: self._execute_with_roll_mode("reaktion", ini=False))
            roller["free_reaktion_btn"].clicked.connect(lambda: self._execute_with_roll_mode("freie_reaktion", ini=False))
        if roller.get("manöver_merken_btn"):
            try:
                roller["manöver_merken_btn"].clicked.disconnect()
            except TypeError:
                pass
            roller["manöver_merken_btn"].clicked.connect(
                lambda checked=False, r=roller: self._merken_manöver_snapshot(r)
            )
        if roller.get("manöver_reset_btn"):
            try:
                roller["manöver_reset_btn"].clicked.disconnect()
            except TypeError:
                pass
            roller["manöver_reset_btn"].clicked.connect(
                lambda checked=False, r=roller: self._reset_manöver_ui(r, clear_memory=True)
            )
        if roller.get("kampfmod_merken_btn"):
            try:
                roller["kampfmod_merken_btn"].clicked.disconnect()
            except TypeError:
                pass
            roller["kampfmod_merken_btn"].clicked.connect(
                lambda checked=False, r=roller: self._merken_kampfmod_snapshot(r)
            )
        if roller.get("kampfmod_reset_btn"):
            try:
                roller["kampfmod_reset_btn"].clicked.disconnect()
            except TypeError:
                pass
            roller["kampfmod_reset_btn"].clicked.connect(
                lambda checked=False, r=roller: self._reset_kampfmod_ui(r, clear_memory=True)
            )

    def _execute_with_roll_mode(self, mode, ini=False):
        self._roll_mode = mode or "normal"
        if ini:
            self.execute_ini_roll()
        else:
            self.execute_master_roll_nsc()

    def _update_reaktion_buttons(self, roller, attr_name):
        """AT → Reaktion würfeln; VT → Freie Reaktion; sonst aus."""
        if not roller:
            return
        is_at = "AT " in (attr_name or "")
        is_vt = "VT " in (attr_name or "")
        if "reaktion_btn" in roller:
            roller["reaktion_btn"].setVisible(is_at)
        if "free_reaktion_btn" in roller:
            roller["free_reaktion_btn"].setVisible(is_vt)
        self._roll_mode = "normal"

    def _update_triumph_ui(self, roller, dice_result, is_at, is_vt):
        if not roller or "triumph_wrap" not in roller:
            return
        use_1w20 = bool(roller.get("radio1W20") and roller["radio1W20"].isChecked())
        combat = bool(is_at or is_vt)
        msg = ""
        if use_1w20 and combat and dice_result in (1, 20):
            msg = triumph_patzer_message(dice_result, is_at, is_vt)
        if roller.get("triumph_label"):
            roller["triumph_label"].setText(msg)
        roller["triumph_wrap"].setVisible(bool(msg))

    def _merken_manöver_snapshot(self, roller):
        snap = {"checked": {}, "spins": {}, "modes": {}}
        for mid, info in (roller.get("manöver_widgets") or {}).items():
            cb = info.get("cb")
            if cb is None:
                continue
            snap["checked"][mid] = bool(cb.isChecked())
            sp = info.get("spin")
            if sp is not None:
                try:
                    snap["spins"][mid] = int(sp.value())
                except Exception:
                    pass
            mode = info.get("mode")
            if mode is not None:
                try:
                    snap["modes"][mid] = mode.currentData()
                except Exception:
                    pass
        self._merken_manöver = snap
        if roller.get("manöver_merken_btn"):
            roller["manöver_merken_btn"].setText("Merken ✓")

    def _restore_manöver_from_memory(self, roller):
        snap = self._merken_manöver
        if not snap or not roller:
            return
        for mid, info in (roller.get("manöver_widgets") or {}).items():
            cb = info.get("cb")
            if cb is None:
                continue
            want = bool((snap.get("checked") or {}).get(mid, False))
            cb.blockSignals(True)
            cb.setChecked(want)
            cb.blockSignals(False)
            if want:
                try:
                    cb.toggled.emit(True)
                except Exception:
                    pass
            mode = info.get("mode")
            if mode is not None and mid in (snap.get("modes") or {}):
                data = snap["modes"][mid]
                idx = mode.findData(data)
                if idx >= 0:
                    mode.setCurrentIndex(idx)
            sp = info.get("spin")
            if sp is not None and mid in (snap.get("spins") or {}):
                try:
                    sp.setValue(int(snap["spins"][mid]))
                except Exception:
                    pass
        if roller.get("manöver_merken_btn"):
            roller["manöver_merken_btn"].setText("Merken ✓")

    def _reset_manöver_ui(self, roller, clear_memory=False):
        if clear_memory:
            self._merken_manöver = None
        for mid, info in (roller.get("manöver_widgets") or {}).items():
            cb = info.get("cb")
            if cb is not None:
                try:
                    cb.setChecked(False)
                except RuntimeError:
                    pass
            sp = info.get("spin")
            if sp is not None:
                try:
                    if (info.get("def") or {}).get("mod") == "variable":
                        sp.setValue(2)
                    else:
                        sp.setValue(self._get_nsc_gs(self.active_sc_widget))
                    sp.setVisible(False)
                except RuntimeError:
                    pass
            mode = info.get("mode")
            if mode is not None:
                try:
                    mode.setCurrentIndex(0)
                    mode.setVisible(False)
                except RuntimeError:
                    pass
        if roller.get("manöver_merken_btn"):
            roller["manöver_merken_btn"].setText("Merken")

    def _merken_kampfmod_snapshot(self, roller):
        snap = {"nk_combos": {}, "fk_combos": {}, "nk_checks": {}, "fk_checks": {}}
        for key, combo in (roller.get("nk_combos") or {}).items():
            try:
                snap["nk_combos"][key] = combo.currentIndex()
            except Exception:
                pass
        for key, combo in (roller.get("fk_combos") or {}).items():
            try:
                snap["fk_combos"][key] = combo.currentIndex()
            except Exception:
                pass
        for key, cb in (roller.get("nk_checks") or {}).items():
            try:
                snap["nk_checks"][key] = bool(cb.isChecked())
            except Exception:
                pass
        for key, cb in (roller.get("fk_checks") or {}).items():
            try:
                snap["fk_checks"][key] = bool(cb.isChecked())
            except Exception:
                pass
        self._merken_kampfmod = snap
        if roller.get("kampfmod_merken_btn"):
            roller["kampfmod_merken_btn"].setText("Merken ✓")

    def _restore_kampfmod_from_memory(self, roller):
        snap = self._merken_kampfmod
        if not snap or not roller:
            return
        for key, combo in (roller.get("nk_combos") or {}).items():
            if key in (snap.get("nk_combos") or {}):
                try:
                    combo.setCurrentIndex(int(snap["nk_combos"][key]))
                except Exception:
                    pass
        for key, combo in (roller.get("fk_combos") or {}).items():
            if key in (snap.get("fk_combos") or {}):
                try:
                    combo.setCurrentIndex(int(snap["fk_combos"][key]))
                except Exception:
                    pass
        for key, cb in (roller.get("nk_checks") or {}).items():
            if key in (snap.get("nk_checks") or {}):
                try:
                    cb.setChecked(bool(snap["nk_checks"][key]))
                except Exception:
                    pass
        for key, cb in (roller.get("fk_checks") or {}).items():
            if key in (snap.get("fk_checks") or {}):
                try:
                    cb.setChecked(bool(snap["fk_checks"][key]))
                except Exception:
                    pass
        if roller.get("kampfmod_merken_btn"):
            roller["kampfmod_merken_btn"].setText("Merken ✓")

    def _reset_kampfmod_ui(self, roller, clear_memory=False):
        if clear_memory:
            self._merken_kampfmod = None
        for combo in (roller.get("nk_combos") or {}).values():
            try:
                combo.setCurrentIndex(0)
            except Exception:
                pass
        for combo in (roller.get("fk_combos") or {}).values():
            try:
                combo.setCurrentIndex(0)
            except Exception:
                pass
        for cb in (roller.get("nk_checks") or {}).values():
            try:
                cb.setChecked(False)
            except Exception:
                pass
        for cb in (roller.get("fk_checks") or {}).values():
            try:
                cb.setChecked(False)
            except Exception:
                pass
        if roller.get("kampfmod_merken_btn"):
            roller["kampfmod_merken_btn"].setText("Merken")

    def _refresh_aktionen_from_widget(self, nsc_widget):
        """Nach Effekt-Tick: Aktions-Haekchen an aktuelle Effekte anpassen."""
        if not nsc_widget:
            return
        off_on = bool(
            hasattr(nsc_widget, "_has_active_volle") and nsc_widget._has_active_volle("off")
        )
        def_on = bool(
            hasattr(nsc_widget, "_has_active_volle") and nsc_widget._has_active_volle("def")
        )
        atem_on = bool(
            hasattr(nsc_widget, "_has_active_atemtechnik") and nsc_widget._has_active_atemtechnik()
        )
        nsc_widget._aktionen_busy = True
        try:
            for roller in (
                getattr(self, "nsc_dice_roller", None),
                getattr(self, "ini_dice_roller", None),
            ):
                if not roller:
                    continue
                off_cb = roller.get("volle_off_check")
                def_cb = roller.get("volle_def_check")
                atem_cb = roller.get("atemtechnik_check")
                if off_cb is not None:
                    off_cb.blockSignals(True)
                    off_cb.setChecked(bool(off_on))
                    off_cb.blockSignals(False)
                if def_cb is not None:
                    def_cb.blockSignals(True)
                    def_cb.setChecked(bool(def_on))
                    def_cb.blockSignals(False)
                if atem_cb is not None:
                    atem_cb.blockSignals(True)
                    atem_cb.setChecked(bool(atem_on))
                    atem_cb.blockSignals(False)
        finally:
            nsc_widget._aktionen_busy = False

    def _on_nsc_atemtechnik_toggled(self, checked):
        w = getattr(self, "active_sc_widget", None) or getattr(self, "active_ini_widget", None)
        if w is None:
            return
        # Busy nur für programmatische Syncs – User-Klick muss immer durchkommen
        w._aktionen_busy = False
        for roller in (
            getattr(self, "nsc_dice_roller", None),
            getattr(self, "ini_dice_roller", None),
        ):
            if not roller:
                continue
            cb = roller.get("atemtechnik_check")
            if cb is not None:
                cb.blockSignals(True)
                cb.setChecked(bool(checked))
                cb.blockSignals(False)
        if hasattr(w, "apply_atemtechnik"):
            w.apply_atemtechnik(bool(checked))

    def _on_nsc_volle_offensive_toggled(self, checked):
        w = getattr(self, "active_sc_widget", None) or getattr(self, "active_ini_widget", None)
        if w is None:
            return
        w._aktionen_busy = False
        # Gegenseite abwählen
        for roller in (
            getattr(self, "nsc_dice_roller", None),
            getattr(self, "ini_dice_roller", None),
        ):
            if not roller:
                continue
            def_cb = roller.get("volle_def_check")
            if def_cb is not None:
                def_cb.blockSignals(True)
                def_cb.setChecked(False)
                def_cb.blockSignals(False)
            off_cb = roller.get("volle_off_check")
            if off_cb is not None:
                off_cb.blockSignals(True)
                off_cb.setChecked(bool(checked))
                off_cb.blockSignals(False)
        if hasattr(w, "apply_volle_offensive"):
            w.apply_volle_offensive(bool(checked))

    def _on_nsc_volle_defensive_toggled(self, checked):
        w = getattr(self, "active_sc_widget", None) or getattr(self, "active_ini_widget", None)
        if w is None:
            return
        w._aktionen_busy = False
        for roller in (
            getattr(self, "nsc_dice_roller", None),
            getattr(self, "ini_dice_roller", None),
        ):
            if not roller:
                continue
            off_cb = roller.get("volle_off_check")
            if off_cb is not None:
                off_cb.blockSignals(True)
                off_cb.setChecked(False)
                off_cb.blockSignals(False)
            def_cb = roller.get("volle_def_check")
            if def_cb is not None:
                def_cb.blockSignals(True)
                def_cb.setChecked(bool(checked))
                def_cb.blockSignals(False)
        if hasattr(w, "apply_volle_defensive"):
            w.apply_volle_defensive(bool(checked))

    def _sync_aktionen_checks_nsc(self, roller, nsc_widget, *, is_tp=False, is_at=False, is_vt=False):
        if not roller or not nsc_widget:
            return
        atem = roller.get("atemtechnik_check")
        off_cb = roller.get("volle_off_check")
        def_cb = roller.get("volle_def_check")
        box = roller.get("aktionen_box")
        # VT = Reaktion, TP = Schaden bereits deklariert → keine Aktionen
        if is_vt or is_tp:
            if box is not None:
                box.setVisible(False)
            for cb in (atem, off_cb, def_cb):
                if cb is not None:
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.setVisible(False)
                    cb.blockSignals(False)
            return
        has_atem = self._nsc_has_vorteil(nsc_widget, "Atemtechnik")
        atem_active = bool(hasattr(nsc_widget, "_has_active_atemtechnik") and nsc_widget._has_active_atemtechnik())
        show_atem = (has_atem or atem_active) and is_at
        is_fk_w = False
        try:
            is_fk_w = bool(self._weapon_is_fernkampf_obj(
                self._resolve_nsc_weapon(getattr(self, "pending_weapon_name", "") or "", nsc_widget)
            ))
        except Exception:
            is_fk_w = False
        show_volle = is_at and not is_fk_w  # keine VO/VD im Fernkampf
        if atem is not None:
            atem.setVisible(show_atem)
            if show_atem and atem_active:
                atem.setChecked(True)
        off_active = bool(hasattr(nsc_widget, "_has_active_volle") and nsc_widget._has_active_volle("off"))
        def_active = bool(hasattr(nsc_widget, "_has_active_volle") and nsc_widget._has_active_volle("def"))
        has_ok = _has_named_vorteil(
            getattr(nsc_widget, "vorteile_list_data", None) or [], "Offensiver Kampfstil"
        )
        if off_cb is not None:
            off_cb.blockSignals(True)
            off_cb.setVisible(show_volle)
            if show_volle:
                off_cb.setChecked(off_active)
                off_cb.setText(
                    "Volle Offensive (+4 AT / −4 VT)" if (off_active and has_ok) or (show_volle and has_ok)
                    else "Volle Offensive (+4 AT / −8 VT)"
                )
            else:
                off_cb.setChecked(False)
            off_cb.blockSignals(False)
        if def_cb is not None:
            def_cb.blockSignals(True)
            def_cb.setVisible(show_volle)
            def_cb.setChecked(def_active if show_volle else False)
            def_cb.blockSignals(False)
        if box is not None:
            box.setVisible(show_atem or show_volle)

    def _reset_nsc_roller_ui(self, roller):
        """Gemeinsames Zurücksetzen der NSC/INI-Roller-UI."""
        self._roll_mode = "normal"
        if roller.get("triumph_wrap"):
            roller["triumph_wrap"].setVisible(False)
        roller["reach_malus"].setChecked(False)
        roller["reach_bonus"].setChecked(False)
        # blockSignals: sonst toggled(False) → apply_* entfernt aktive Effekte
        for key in (
            "atemtechnik_check", "hammerschlag_check", "zweite_einfache_check",
            "volle_off_check", "volle_def_check",
        ):
            cb = roller.get(key)
            if cb is not None:
                cb.blockSignals(True)
                cb.setChecked(False)
                cb.setVisible(False)
                cb.blockSignals(False)
        if roller.get("aktionen_box"):
            roller["aktionen_box"].setVisible(False)
        if "reaktion_btn" in roller:
            roller["reaktion_btn"].setVisible(False)
        if "free_reaktion_btn" in roller:
            roller["free_reaktion_btn"].setVisible(False)
        roller["manöver_box"].setVisible(False)
        if not self._merken_manöver:
            self._reset_manöver_ui(roller, clear_memory=False)
        if not self._merken_kampfmod:
            self._reset_kampfmod_ui(roller, clear_memory=False)
        roller["präzision_label"].setVisible(False)
        roller["präzision_label"].setText("")
        if "auflaufen_gs_spin" in roller:
            roller["auflaufen_gs_spin"].setVisible(False)
            roller["auflaufen_gs_label"].setVisible(False)
        if "kampfmod_box" in roller:
            roller["kampfmod_box"].setVisible(False)
        roller["continue_btn"].setVisible(False)
        roller["continue_btn"].setText("Weiter → Schaden")
        roller["label_result"].setText("Bereit...")
        roller["label_mod"].setText("0")
        self.custom_mod_value = 0
        self.präzision_ge_bonus = 0
        self.last_at_die = 0
        # pending_weapon_name / pending_weapon_is_fk / pending_tp_string
        # hier NICHT löschen – prepare_at_roll_nsc setzt sie vor prepare_master_roll_nsc
        self._pending_wuchtschlag_tp = 0
        self._pending_rüstungsbrecher = False
        self._pending_todesstoß = False
        self._pending_manöver_notes = []
        self._pending_no_damage = False
        self._pending_auflaufen = False
        self._pending_riposte = False
        self._last_at_ew = None

    def prepare_master_roll_nsc(self, nsc_widget, attr_name, value):
        self.nsc_dice_roller["widget"].setEnabled(True)
        self.active_sc_widget = nsc_widget
        self.active_attribute_name = attr_name
        self.active_attribute_value = value
        self.active_tp_string = None
        # Stuck-Flag freigeben (sonst bleiben Aktionen wirkungslos)
        nsc_widget._aktionen_busy = False
        # Vorteile (Schnellwahl/Tree) vor Manöver-Filter speichern
        nsc_widget.save_data()
        self._reset_nsc_roller_ui(self.nsc_dice_roller)

        sc_name = nsc_widget.data.get("name", "NSC")
        self.nsc_dice_roller["label_probe"].setText(f"<h3>Probe: {sc_name} - {attr_name} ({value})</h3>")

        if "AT " in attr_name or "VT " in attr_name:
            self.nsc_dice_roller["radio1W20"].setChecked(True)
            self.nsc_dice_roller["options_box"].setVisible(False)
            self.nsc_dice_roller["reach_box"].setVisible(False)
            self.nsc_dice_roller["manöver_box"].setVisible(True)
            ptype = "VT" if "VT " in attr_name else "AT"
            # Pending ggf. aus attr_name ableiten (falls noch nicht gesetzt)
            if not getattr(self, "pending_weapon_name", None):
                self.pending_weapon_name = attr_name.replace("AT ", "", 1).replace("VT ", "", 1)
            if getattr(self, "pending_weapon_is_fk", None) is None:
                self.pending_weapon_is_fk = bool(self._weapon_is_fernkampf_obj(
                    self._resolve_nsc_weapon(self.pending_weapon_name, nsc_widget)
                ))
            self._apply_manöver_availability_nsc(
                self.nsc_dice_roller, nsc_widget, probe_type=ptype
            )
            if self._merken_manöver:
                self._restore_manöver_from_memory(self.nsc_dice_roller)
            self._show_kampfmod_for_probe(self.nsc_dice_roller, attr_name, nsc_widget)
            if self._merken_kampfmod:
                self._restore_kampfmod_from_memory(self.nsc_dice_roller)
            self._update_reaktion_buttons(self.nsc_dice_roller, attr_name)
        else:
            self.nsc_dice_roller["radio3W20"].setChecked(True)
            self.nsc_dice_roller["options_box"].setVisible(True)
            self.nsc_dice_roller["reach_box"].setVisible(False)
            if "kampfmod_box" in self.nsc_dice_roller:
                self.nsc_dice_roller["kampfmod_box"].setVisible(False)
            self._update_reaktion_buttons(self.nsc_dice_roller, attr_name)


    def _weapon_eigenschaft_tips(self):
        tips = {}
        try:
            from MonsterHelper import load_monster_katalog
            for p in load_monster_katalog().get("waffeneigenschaften") or []:
                if p.get("name"):
                    tips[p["name"].lower()] = (p.get("name"), p.get("tooltip") or "")
                if p.get("id"):
                    tips[p["id"].lower()] = (p.get("name") or p["id"], p.get("tooltip") or "")
        except Exception:
            pass
        return tips

    def _fill_waffeig_panel(self, roller, nsc_widget, weapon_name):
        """Kompakte Waffeneigenschaften bei AT/VT/TP befüllen."""
        box = roller.get("waffeig_box")
        body = roller.get("waffeig_body") or roller.get("waffeig_browser")
        toggle = roller.get("waffeig_toggle")
        if box is None or body is None:
            return
        eig_text = ""
        info_text = ""
        try:
            if nsc_widget is not None:
                try:
                    nsc_widget.save_data()
                except Exception:
                    pass
                for w in (getattr(nsc_widget, "data", None) or {}).get("weapons") or []:
                    if (w.get("name") or "") == (weapon_name or ""):
                        eig_text = w.get("eigenschaften") or ""
                        info_text = w.get("info") or ""
                        break
                if not eig_text:
                    for entry in getattr(nsc_widget, "combat_widgets", []) or []:
                        try:
                            if entry["name"].text() == (weapon_name or ""):
                                eig_text = entry["eigenschaften"].text()
                                info_text = (entry.get("info_store") or {}).get("text", "")
                                break
                        except Exception:
                            pass
        except Exception:
            pass
        tips = self._weapon_eigenschaft_tips()
        names = [x.strip() for x in (eig_text or "").split(",") if x.strip()]
        if not names and not info_text:
            box.setVisible(False)
            if toggle is not None:
                toggle.blockSignals(True)
                toggle.setChecked(False)
                toggle.blockSignals(False)
            body.setHtml("")
            body.setVisible(False)
            return
        parts = []
        if info_text:
            parts.append("<b>Info:</b> " + info_text.replace(chr(10), "<br>"))
        for n in names:
            disp, tip = tips.get(n.lower(), (n, ""))
            tip_html = (tip or "").replace(chr(10), "<br>")
            if tip_html:
                parts.append(f"<b>{disp}</b> — {tip_html}")
            else:
                parts.append(f"<b>{disp}</b>")
        body.setHtml("<br>".join(parts))
        box.setVisible(True)
        if toggle is not None:
            toggle.blockSignals(True)
            toggle.setChecked(False)
            toggle.setText("▸ Waffeneigenschaften")
            toggle.blockSignals(False)
        body.setVisible(False)


    def prepare_at_roll_nsc(self, nsc_widget, attr_name, value, tp_string):
        """AT- oder VT-Wurf mit TP-String und Manöver-Auswahl."""
        self._last_nsc_prepare = {
            "kind": "at_nsc",
            "attr_name": attr_name,
            "value": value,
            "tp_string": tp_string or "",
        }
        if attr_name.startswith("VT "):
            wname = attr_name.replace("VT ", "", 1)
            ptype = "VT"
        else:
            wname = attr_name.replace("AT ", "", 1)
            ptype = "AT"
        # Waffe + FK-Flag VOR dem UI-Reset setzen
        try:
            if nsc_widget is not None:
                nsc_widget.save_data()
        except Exception:
            pass
        self.pending_tp_string = tp_string or ""
        self.pending_weapon_name = wname
        weapon = self._resolve_nsc_weapon(wname, nsc_widget)
        self.pending_weapon_is_fk = bool(self._weapon_is_fernkampf_obj(weapon))

        self.prepare_master_roll_nsc(nsc_widget, attr_name, value)

        # Nach prepare_master erneut setzen (falls etwas überschrieben wurde)
        self.pending_tp_string = tp_string or ""
        self.pending_weapon_name = wname
        self.pending_weapon_is_fk = bool(self._weapon_is_fernkampf_obj(
            self._resolve_nsc_weapon(wname, nsc_widget)
        ))

        self.nsc_dice_roller["manöver_box"].setVisible(True)
        self._fill_waffeig_panel(self.nsc_dice_roller, nsc_widget, wname)
        self._apply_manöver_availability_nsc(self.nsc_dice_roller, nsc_widget, probe_type=ptype)
        if self._merken_manöver:
            self._restore_manöver_from_memory(self.nsc_dice_roller)
        self._show_kampfmod_for_probe(self.nsc_dice_roller, attr_name, nsc_widget)
        self._sync_aktionen_checks_nsc(
            self.nsc_dice_roller,
            nsc_widget,
            is_tp=False,
            is_at=(ptype == "AT"),
            is_vt=(ptype == "VT"),
        )
        atem_active = bool(
            hasattr(nsc_widget, "_has_active_atemtechnik") and nsc_widget._has_active_atemtechnik()
        )
        self._pending_atemtechnik = bool(ptype == "AT" and atem_active)
        zec = self.nsc_dice_roller.get("zweite_einfache_check")
        if zec is not None:
            zec.setVisible(ptype == "AT")
            if ptype == "AT" and hasattr(nsc_widget, "_has_active_volle") and nsc_widget._has_active_volle("def"):
                zec.blockSignals(True)
                zec.setChecked(True)
                zec.blockSignals(False)

    def roll_tp_nsc(self, nsc_widget, name, tp_string):
        self._last_nsc_prepare = {
            "kind": "tp_nsc",
            "name": name,
            "tp_string": tp_string or "",
        }
        self.nsc_dice_roller["widget"].setEnabled(True)
        self.active_sc_widget = nsc_widget
        self.active_tp_string = tp_string
        self.active_attribute_name = name
        self._reset_nsc_roller_ui(self.nsc_dice_roller)
        self.nsc_dice_roller["options_box"].setVisible(False)
        self.nsc_dice_roller["reach_box"].setVisible(False)
        self.nsc_dice_roller["manöver_box"].setVisible(False)
        self.nsc_dice_roller["hammerschlag_check"].setVisible(False)
        zec = self.nsc_dice_roller.get("zweite_einfache_check")
        if zec is not None:
            zec.blockSignals(True)
            zec.setChecked(False)
            zec.setVisible(False)
            zec.blockSignals(False)
        self._sync_aktionen_checks_nsc(
            self.nsc_dice_roller, nsc_widget, is_tp=True, is_at=False, is_vt=False
        )
        # Waffe aus Name "TP xyz" extrahieren
        wpn = name
        if isinstance(name, str) and name.startswith("TP "):
            wpn = name[3:].strip()
        self._fill_waffeig_panel(self.nsc_dice_roller, nsc_widget, wpn)
        # Pending-Atemtechnik stillschweigend übernehmen (kein UI im TP-Bereich)
        if getattr(self, "_pending_atemtechnik", False) and self.nsc_dice_roller.get("atemtechnik_check"):
            self.nsc_dice_roller["atemtechnik_check"].blockSignals(True)
            self.nsc_dice_roller["atemtechnik_check"].setChecked(True)
            self.nsc_dice_roller["atemtechnik_check"].setVisible(False)
            self.nsc_dice_roller["atemtechnik_check"].blockSignals(False)
        self.nsc_dice_roller["label_probe"].setText(f"<h3>Schaden: {name} ({tp_string})</h3>")
        self.nsc_dice_roller["label_result"].setText("Bereit...")
        nsc_widget.save_data()

    def increase_mod(self): 
        self.custom_mod_value += 1; self.dice_roller["label_mod"].setText(str(self.custom_mod_value))
    def decrease_mod(self):
        self.custom_mod_value -= 1; self.dice_roller["label_mod"].setText(str(self.custom_mod_value))
        
    def increase_mod_nsc(self): 
        self.custom_mod_value += 1; self.nsc_dice_roller["label_mod"].setText(str(self.custom_mod_value))
    def decrease_mod_nsc(self):
        self.custom_mod_value -= 1; self.nsc_dice_roller["label_mod"].setText(str(self.custom_mod_value))

    def execute_master_roll(self):
        if self.active_sc_widget:
            try:
                blocker = has_blocking_probe_effect(self.active_sc_widget._get_effects())
            except Exception:
                blocker = None
            if blocker:
                QMessageBox.information(
                    None, str(blocker),
                    f"Keine Probe möglich: Effekt „{blocker}“ aktiv.",
                )
                return
        self._execute_roll_generic(self.dice_roller, self.sc_widgets)

    def _nsc_has_vorteil(self, widget, name):
        """Prüft Vorteile bei NSC/SC: aktuelle UI-Liste, gespeicherte Liste, Flags, Freitext."""
        if not widget:
            return False
        key = (name or "").lower().strip()
        if not key:
            return False

        def _match(v):
            s = str(v).lower().strip()
            return s == key or key in s or s in key

        # 1) Live-UI (Schnellwahl / Tree), noch nicht gespeichert
        for v in getattr(widget, "vorteile_list_data", None) or []:
            if _match(v):
                return True
        if hasattr(widget, "vorteil_checks"):
            cb = widget.vorteil_checks.get(name)
            if cb is not None:
                try:
                    if cb.isChecked():
                        return True
                except RuntimeError:
                    pass
            # Fuzzy: Name als Teilstring im Checkbox-Key
            for vname, cb in widget.vorteil_checks.items():
                try:
                    if cb.isChecked() and _match(vname):
                        return True
                except RuntimeError:
                    pass

        data = getattr(widget, "data", None) or {}
        for v in data.get("vorteile_list", []) or []:
            if _match(v):
                return True
        if data.get(key.replace(" ", "_"), False) or data.get(name, False):
            return True
        blob = (
            (data.get("vorteile_text") or "")
            + " "
            + (data.get("notizen") or "")
        ).lower()
        return key in blob

    def _has_präzision(self, widget):
        return self._nsc_has_vorteil(widget, "Präzision")

    def _resolve_nsc_weapon(self, weapon_name, nsc_widget=None):
        """Waffe aus NSC-Liste / Live-UI / DB auflösen (fernkampf + Eigenschaften)."""
        if not weapon_name:
            return None
        # 1) Live-Combat-Zeilen (eigene Waffen inkl. fernkampf-Flag)
        if nsc_widget:
            for entry in getattr(nsc_widget, "combat_widgets", []) or []:
                try:
                    n = entry["name"].text() if "name" in entry else ""
                except Exception:
                    n = ""
                if n == weapon_name or (n and weapon_name and n.strip() == weapon_name.strip()):
                    eig = ""
                    try:
                        eig = entry["eigenschaften"].text() if "eigenschaften" in entry else ""
                    except Exception:
                        pass
                    info = ""
                    store = entry.get("info_store")
                    if isinstance(store, dict):
                        info = store.get("text", "") or ""
                    is_fk = bool(entry.get("fernkampf", False))
                    return {
                        "name": n,
                        "eigenschaften": eig,
                        "info": info,
                        "fernkampf": is_fk,
                        "fk": 1 if is_fk else 0,
                    }
            # 2) Gespeicherte Waffenliste am NSC
            for c in (getattr(nsc_widget, "data", None) or {}).get("weapons") or []:
                n = c.get("name") or c.get("anzeigename") or ""
                if n == weapon_name or c.get("anzeigename") == weapon_name:
                    # Eigene / gespeicherte Daten haben Vorrang vor reinem DB-Objekt
                    if "fernkampf" in c or "fk" in c or "is_fk" in c or c.get("info"):
                        return c
                    db_name = c.get("db_name") or c.get("name") or ""
                    if hasattr(Wolke, "DB") and Wolke.DB and db_name in getattr(Wolke.DB, "waffen", {}):
                        return Wolke.DB.waffen[db_name]
                    return c
        # 3) Direkter DB-Treffer
        if hasattr(Wolke, "DB") and Wolke.DB and weapon_name in getattr(Wolke.DB, "waffen", {}):
            return Wolke.DB.waffen[weapon_name]
        # 4) Fuzzy DB
        if hasattr(Wolke, "DB") and Wolke.DB:
            for db_name, w in Wolke.DB.waffen.items():
                if weapon_name in db_name or db_name in weapon_name:
                    return w
        return None

    @staticmethod
    def _coerce_fernkampf_flag(val) -> bool:
        """DB nutzt fk=\"0\"/\"1\" (siehe datenbank.xml). bool(\"0\") wäre True – daher strikt parsen."""
        if val is None:
            return False
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return int(val) != 0
        s = str(val).strip().lower()
        if s in ("", "0", "false", "nein", "no", "nk", "nahkampf"):
            return False
        if s in ("1", "true", "ja", "yes", "fk", "fernkampf"):
            return True
        return bool(val)

    def _weapon_is_fernkampf_obj(self, w):
        """Wie datenbank.xml: fk=\"0\"|\"1\" ist maßgeblich; fernkampf nur Fallback."""
        if w is None:
            return False
        if isinstance(w, dict):
            # Eigenes Flag zuerst (NSC/Monster-Waffe)
            if "fernkampf" in w and w.get("fernkampf") is not None:
                return self._coerce_fernkampf_flag(w.get("fernkampf"))
            if "is_fk" in w and w.get("is_fk") is not None:
                return self._coerce_fernkampf_flag(w.get("is_fk"))
            if "fk" in w and w.get("fk") is not None:
                return self._coerce_fernkampf_flag(w.get("fk"))
            return False
        # Sephrasto-DB: XML-Attribut fk hat Vorrang (kann parallel fernkampf=False existieren)
        for attr in ("fk", "fernkampf", "is_fk", "isFk"):
            if hasattr(w, attr):
                try:
                    val = getattr(w, attr)
                except Exception:
                    continue
                # fk=0 zählt als gesetzter Wert → nicht überspringen
                if attr == "fk" or val is not None:
                    return self._coerce_fernkampf_flag(val)
        return False

    def _weapon_has_eigenschaft_obj(self, w, prop):
        if w is None:
            return False
        if isinstance(w, dict):
            eig = w.get("eigenschaften") or []
        else:
            eig = getattr(w, "eigenschaften", None) or []
        prop_l = prop.lower()
        for e in eig:
            if prop_l in str(e).lower():
                return True
        return False

    def _clear_manöver_layout_nsc(self, roller):
        layout = roller.get("manöver_layout")
        if not layout:
            return
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
            elif item.layout() is not None:
                sub = item.layout()
                while sub.count():
                    si = sub.takeAt(0)
                    if si.widget():
                        si.widget().deleteLater()
        roller["manöver_widgets"] = {}
        for k in (
            "riposte_combo", "riposte_combo_spin", "riposte_combo_wrap",
            "_riposte_combo_defs", "riposte_kombi_widgets", "riposte_kombi_box",
        ):
            roller.pop(k, None)

    def _clear_bewegung_manöver(self):
        """Sturmangriff/Überrennen neu berechnen (ein- oder ausblenden je nach Volle Off/Def)."""
        self._refresh_manöver_after_volle()

    def _set_zweite_einfache_checks(self, on: bool):
        """Modifikator „Zweite einfache Aktion (−4 AT)“ in allen Master-Rollern setzen/lösen."""
        for roller in (
            getattr(self, "nsc_dice_roller", None),
            getattr(self, "ini_dice_roller", None),
            getattr(self, "monster_dice_roller", None),
        ):
            if not roller:
                continue
            cb = roller.get("zweite_einfache_check")
            if cb is None:
                continue
            try:
                cb.blockSignals(True)
                cb.setChecked(bool(on))
                if on:
                    cb.setVisible(True)
                cb.blockSignals(False)
            except RuntimeError:
                pass

    def _refresh_manöver_after_volle(self):
        """Manöver-Grid neu laden, damit Sturmangriff/Überrennen korrekt ein-/ausgeblendet werden."""
        attr = getattr(self, "active_attribute_name", "") or ""
        if "AT " in attr:
            ptype = "AT"
        elif "VT " in attr:
            ptype = "VT"
        else:
            return
        pairs = []
        nsc_r = getattr(self, "nsc_dice_roller", None)
        nsc_w = getattr(self, "active_sc_widget", None)
        if nsc_r and nsc_w:
            pairs.append((nsc_r, nsc_w))
        ini_r = getattr(self, "ini_dice_roller", None)
        ini_w = getattr(self, "active_ini_widget", None)
        if ini_r and ini_w:
            pairs.append((ini_r, ini_w))
        mon_r = getattr(self, "monster_dice_roller", None)
        if mon_r and nsc_w and is_monster_widget(nsc_w):
            pairs.append((mon_r, nsc_w))
        for roller, widget in pairs:
            try:
                if "manöver_box" not in roller or not roller["manöver_box"].isVisible():
                    continue
            except RuntimeError:
                continue
            self._apply_manöver_availability_nsc(roller, widget, probe_type=ptype)
            if self._merken_manöver:
                self._restore_manöver_from_memory(roller)

    def _wire_manöver_mutex_nsc(self, main_widgets: dict, kombi_widgets: dict):
        """Schildspalter / Umklammern / Entwaffnen / Umreißen schließen sich aus."""
        sources = []
        for mid in MUTUALLY_EXCLUSIVE_MANOEVER:
            for pool in (main_widgets, kombi_widgets):
                info = (pool or {}).get(mid)
                if info and info.get("cb"):
                    sources.append((mid, info["cb"], info.get("spin")))

        def _on_mutex(checked, origin_mid, origin_cb):
            if not checked:
                return
            for mid, cb, spin in sources:
                if mid == origin_mid or cb is origin_cb:
                    continue
                if cb.isChecked():
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
                    if spin is not None:
                        spin.setVisible(False)

        for mid, cb, _spin in sources:
            cb.toggled.connect(
                lambda checked, m=mid, c=cb: _on_mutex(checked, m, c)
            )

    def _apply_manöver_availability_nsc(self, roller, widget, probe_type="AT"):
        """Dynamische Manöver-Liste für NSC – analog Spieler."""
        if "manöver_layout" not in roller:
            return

        weapon = self._resolve_nsc_weapon(getattr(self, "pending_weapon_name", None), widget)
        if getattr(self, "pending_weapon_is_fk", None) is not None:
            is_fk = bool(self.pending_weapon_is_fk)
        else:
            is_fk = self._weapon_is_fernkampf_obj(weapon)
        has_atem = self._nsc_has_vorteil(widget, "Atemtechnik")

        def has_v(name):
            return self._nsc_has_vorteil(widget, name)

        # Monster: Manöver-Freigabe ersetzt fehlende Vorteile
        if is_monster_widget(widget):
            freigabe = []
            if hasattr(widget, "get_manöver_freigabe"):
                freigabe = widget.get_manöver_freigabe()
            else:
                freigabe = list((getattr(widget, "data", None) or {}).get("manöver_freigabe") or [])
            has_v = make_monster_has_vorteil(has_v, freigabe, MANOEVER)

        def has_eig(prop):
            if self._weapon_has_eigenschaft_obj(weapon, prop):
                return True
            if self._weapon_is_fernkampf_obj(weapon):
                ammo = selected_ammo(normalize_ammo_list(
                    getattr(widget, "munition_data", None)
                    or (getattr(widget, "data", None) or {}).get("munition")
                    or []
                ))
                return ammo_has_eigenschaft(ammo, prop)
            return False

        # Waffenlos-Heuristik
        is_waffenlos = False
        if weapon is None:
            is_waffenlos = True
        elif isinstance(weapon, dict):
            n = (weapon.get("name") or weapon.get("anzeigename") or "").lower()
            is_waffenlos = "unbewaffnet" in n or "waffenlos" in n
        else:
            n = (getattr(weapon, "name", "") or "").lower()
            is_waffenlos = "unbewaffnet" in n or "waffenlos" in n

        self._clear_manöver_layout_nsc(roller)
        layout = roller["manöver_layout"]
        widgets = {}

        available = [
            m for m in MANOEVER
            if manöver_available(
                m,
                probe_type=probe_type,
                is_fk=is_fk,
                has_vorteil=has_v,
                weapon_has_eigenschaft=has_eig,
                is_waffenlos=is_waffenlos,
            )
        ]
        # Volle Offensive/Defensive = Aktion verbraucht → keine Bewegungs-Manöver
        volle_active = False
        try:
            volle_active = bool(
                (hasattr(widget, "_has_active_volle") and widget._has_active_volle("off"))
                or (hasattr(widget, "_has_active_volle") and widget._has_active_volle("def"))
            )
        except Exception:
            volle_active = False
        if volle_active:
            available = [
                m for m in available
                if m.get("id") not in ("sturmangriff", "ueberrennen")
                and m.get("effekt") not in ("sturmangriff", "ueberrennen")
            ]

        if not available:
            layout.addWidget(QLabel("<i>Keine Manöver</i>"), 0, 0)
            roller["manöver_widgets"] = widgets
            roller["_has_atemtechnik"] = has_atem
            return

        cols = 2
        for i, m in enumerate(available):
            r, c = divmod(i, cols)
            cell = QHBoxLayout()
            cell.setContentsMargins(0, 0, 0, 0)
            cell.setSpacing(2)
            # Kompaktes Label im Grid; voller Text nur im Tooltip/Popup
            cb = QCheckBox(manöver_label(m, compact=True))
            if m.get("tooltip"):
                tip_parts = [m["tooltip"]]
            else:
                tip_parts = [manöver_label(m, compact=False)]
            reqs_txt = []
            for req in m.get("reqs") or []:
                if req.startswith("vorteil:"):
                    reqs_txt.append(f"Vorteil {req[8:]}")
                elif req.startswith("vorteil_any:"):
                    reqs_txt.append("Vorteil " + " oder ".join(req[12:].split("|")))
                elif req.startswith("waffe:"):
                    reqs_txt.append(f"Waffeneigenschaft {req[6:]}")
                elif req == "waffenlos":
                    reqs_txt.append("waffenlos")
                elif req == "fernkampf":
                    reqs_txt.append("Fernkampfwaffe")
                elif req == "nahkampf":
                    reqs_txt.append("Nahkampfwaffe")
                elif req.startswith("situativ:"):
                    reqs_txt.append(req[9:])
            if reqs_txt:
                tip_parts.append("Voraussetzungen: " + "; ".join(reqs_txt))
            tip = "\n".join(tip_parts)
            cb.setToolTip(tip)
            cell.addWidget(cb)
            spin = None
            mode_combo = None
            if m.get("mod") == "variable":
                spin = QSpinBox()
                spin.setRange(1, 8)
                spin.setValue(2)
                spin.setPrefix("–")
                spin.setFixedWidth(48)
                spin.setToolTip(tip)
                cell.addWidget(spin)
            if m.get("effekt") in ("sturmangriff", "ueberrennen") or m["id"] in ("sturmangriff", "ueberrennen"):
                mode_combo = QComboBox()
                mode_combo.addItem("GS*", "gs")
                mode_combo.addItem("x", "x")
                mode_combo.setFixedWidth(56)
                mode_combo.setToolTip("GS* = NSC-GS; x = festen Bonus wählen")
                gs0 = self._get_nsc_gs(widget)
                spin = QSpinBox()
                spin.setRange(0, 40)
                spin.setValue(gs0)
                spin.setFixedWidth(44)
                spin.setEnabled(False)
                spin.setToolTip("TP-Bonus durch Sturmangriff/Überrennen")

                def _sync_sturm_mode(_idx, sp=spin, combo=mode_combo, w=widget):
                    try:
                        use_x = combo.currentData() == "x"
                        sp.setEnabled(use_x)
                        if not use_x:
                            sp.setValue(self._get_nsc_gs(w))
                    except RuntimeError:
                        pass

                mode_combo.currentIndexChanged.connect(_sync_sturm_mode)

                def _on_sturm_cb(checked, sp=spin, combo=mode_combo, w=widget):
                    try:
                        sp.setVisible(checked)
                        combo.setVisible(checked)
                        if checked and combo.currentData() == "gs":
                            sp.setValue(self._get_nsc_gs(w))
                    except RuntimeError:
                        pass

                cb.toggled.connect(_on_sturm_cb)
                mode_combo.setVisible(False)
                spin.setVisible(False)
                cell.addWidget(mode_combo)
                cell.addWidget(spin)
            cell.addStretch()
            wrap = QWidget()
            wrap.setLayout(cell)
            layout.addWidget(wrap, r, c)
            widgets[m["id"]] = {"cb": cb, "spin": spin, "mode": mode_combo, "def": m}
            if m["id"] in ("wuchtschlag", "scharfschuss"):
                roller["manöver_wuchtschlag"] = cb
                if spin:
                    roller["manöver_wuchtschlag_spin"] = spin
            elif m["id"] == "hammerschlag":
                roller["manöver_hammerschlag"] = cb
            elif m["id"] in ("todesstoss", "meisterschuss"):
                roller["manöver_todesstoß"] = cb
            elif m["id"] in ("ruestungsbrecher_nk", "ruestungsbrecher_fk"):
                roller["manöver_rüstungsbrecher"] = cb

        # Riposte: Kombinationskasten mit Checkboxen (mehrere AT-Manöver)
        for k in (
            "riposte_combo", "riposte_combo_spin", "riposte_combo_wrap",
            "_riposte_combo_defs", "riposte_kombi_widgets", "riposte_kombi_box",
        ):
            roller.pop(k, None)
        if probe_type == "VT" and "riposte" in widgets:
            combo_list = riposte_combinable_manöver(
                is_fk=is_fk,
                has_vorteil=has_v,
                weapon_has_eigenschaft=has_eig,
                is_waffenlos=is_waffenlos,
            )
            riposte_cb = widgets["riposte"]["cb"]
            kombi_box = QGroupBox("Riposte kombinieren mit AT-Manövern")
            kombi_box.setStyleSheet("QGroupBox { font-weight: normal; color: #444; }")
            kombi_grid = QGridLayout(kombi_box)
            kombi_grid.setContentsMargins(6, 6, 6, 6)
            kombi_grid.setSpacing(2)
            kombi_widgets = {}
            kcols = 2
            for i, cm in enumerate(combo_list):
                kr, kc = divmod(i, kcols)
                cell = QHBoxLayout()
                cell.setContentsMargins(0, 0, 0, 0)
                cell.setSpacing(2)
                cb = QCheckBox(manöver_label(cm, compact=True))
                tip = cm.get("tooltip") or manöver_label(cm, compact=False)
                cb.setToolTip(tip)
                cell.addWidget(cb)
                spin = None
                if cm.get("mod") == "variable":
                    spin = QSpinBox()
                    spin.setRange(1, 8)
                    spin.setValue(2)
                    spin.setPrefix("–")
                    spin.setFixedWidth(48)
                    spin.setToolTip(tip)
                    spin.setVisible(False)
                    cell.addWidget(spin)

                    def _on_var(checked, sp=spin):
                        sp.setVisible(checked)

                    cb.toggled.connect(_on_var)
                cell.addStretch()
                wrap = QWidget()
                wrap.setLayout(cell)
                kombi_grid.addWidget(wrap, kr, kc)
                kombi_widgets[cm["id"]] = {"cb": cb, "spin": spin, "def": cm}

            if not combo_list:
                kombi_grid.addWidget(QLabel("<i>Keine AT-Manöver verfügbar</i>"), 0, 0)

            n_rows = (len(available) + cols - 1) // cols if available else 0
            kombi_box.setVisible(False)
            layout.addWidget(kombi_box, n_rows, 0, 1, cols)

            def _show_kombi(checked, box=kombi_box, kws=kombi_widgets):
                box.setVisible(checked)
                if not checked:
                    for info in kws.values():
                        cb = info.get("cb")
                        if cb:
                            cb.blockSignals(True)
                            cb.setChecked(False)
                            cb.blockSignals(False)
                        sp = info.get("spin")
                        if sp is not None:
                            sp.setVisible(False)

            riposte_cb.toggled.connect(_show_kombi)
            self._wire_manöver_mutex_nsc(widgets, kombi_widgets)

            roller["riposte_kombi_widgets"] = kombi_widgets
            roller["riposte_kombi_box"] = kombi_box
            roller["_riposte_combo_defs"] = {cm["id"]: cm for cm in combo_list}
        else:
            self._wire_manöver_mutex_nsc(widgets, {})

        roller["manöver_widgets"] = widgets
        roller["_has_atemtechnik"] = has_atem

    def _get_nsc_gs(self, widget):
        """
        GS* wie in „Abgeleitete Kampfwerte“:
        GS* = max(1, GS − BE) falls GS > 0, sonst 0; plus Effekt-Mod auf GS.
        """
        if not widget:
            return 4
        gs = 0
        be = 0
        # Basis-GS aus Attribut-Spins (wie _update_kampf_derived)
        try:
            if hasattr(widget, "attr_spins") and "GS" in widget.attr_spins:
                gs = int(widget.attr_spins["GS"].value() or 0)
            else:
                data = getattr(widget, "data", None) or {}
                attrs = data.get("attributes", data) or {}
                gs = int(attrs.get("GS", attrs.get("gs", 0)) or 0)
        except (TypeError, ValueError, RuntimeError):
            # RuntimeError: C++-Spin schon gelöscht → Fallback aus data
            try:
                data = getattr(widget, "data", None) or {}
                attrs = data.get("attributes", data) or {}
                gs = int(attrs.get("GS", attrs.get("gs", 0)) or 0)
            except (TypeError, ValueError):
                gs = 0
        # BE aus Rüstung
        try:
            if hasattr(widget, "ruest_be"):
                be = int(widget.ruest_be.value() or 0)
            else:
                data = getattr(widget, "data", None) or {}
                be = int(data.get("be", data.get("ruest_be", 0)) or 0)
        except (TypeError, ValueError, RuntimeError):
            try:
                data = getattr(widget, "data", None) or {}
                ru = data.get("ruestung") or {}
                be = int(ru.get("be", data.get("be", 0)) or 0) if isinstance(ru, dict) else int(data.get("be", 0) or 0)
            except (TypeError, ValueError):
                be = 0
        # gleiche Formel wie Anzeige GS*
        gs_stern = max(1, gs - be) if gs > 0 else 0
        # Effekt-Mods
        try:
            if hasattr(widget, "get_effect_mods"):
                gs_stern += int(widget.get_effect_mods().get("gs", 0) or 0)
        except Exception:
            pass
        return max(0, int(gs_stern))

    def _get_ge_for_präzision(self, widget):
        """
        GE-Attributwert (Wert) für Präzision – nicht der PW.
        PW = 2 × Wert; Präzision addiert den echten GE-Wert als TP.
        """
        if not widget:
            return 0
        attrs = widget.data.get("attributes", {})
        ge = int(attrs.get("GE", 0) or 0)
        # Falls noch alter PW-Wert gespeichert (>20), halbieren
        if ge > 20:
            ge = ge // 2
        return ge

    def _sum_combat_mods_nsc(self, roller, *, is_at=False):
        """Summiert NK-/FK-Kampfmodifikatoren im Master-Roller."""
        total = 0
        parts = []
        if not roller:
            return 0, []
        use_fk = bool(roller.get("fk_panel") and roller["fk_panel"].isVisible())
        combos = roller.get("fk_combos" if use_fk else "nk_combos") or {}
        checks = roller.get("fk_checks" if use_fk else "nk_checks") or {}
        for combo in combos.values():
            val, label = combat_mod_from_combo(combo)
            if val:
                total += val
                parts.append(label)
        for cb in checks.values():
            try:
                if cb.isChecked():
                    val = int(cb.property("mod_val") or 0)
                    total += val
                    parts.append(cb.text())
            except RuntimeError:
                pass
        return total, parts

    def _show_kampfmod_for_probe(self, roller, attr_name, widget=None):
        """Zeigt NK- oder FK-Modifikatoren je nach Waffe/Probe."""
        if "kampfmod_box" not in roller:
            return
        is_combat = "AT " in (attr_name or "") or "VT " in (attr_name or "")
        roller["kampfmod_box"].setVisible(is_combat)
        if not is_combat:
            return
        is_vt = "VT " in (attr_name or "")
        is_fk = False
        if not is_vt:
            if getattr(self, "pending_weapon_is_fk", None) is not None:
                is_fk = bool(self.pending_weapon_is_fk)
            else:
                wname = getattr(self, "pending_weapon_name", None) or ""
                if not wname and attr_name:
                    wname = attr_name.replace("AT ", "", 1).replace("VT ", "", 1)
                weapon = self._resolve_nsc_weapon(wname, widget or self.active_sc_widget)
                is_fk = self._weapon_is_fernkampf_obj(weapon)
        roller["nk_panel"].setVisible(not is_fk)
        roller["fk_panel"].setVisible(is_fk)
        roller["kampfmod_box"].setTitle(
            "Kampf-Modifikatoren (Fernkampf)" if is_fk else "Kampf-Modifikatoren (Nahkampf)"
        )
        if self._merken_kampfmod:
            self._restore_kampfmod_from_memory(roller)
        if roller.get("kampfmod_merken_btn"):
            roller["kampfmod_merken_btn"].setText(
                "Merken ✓" if self._merken_kampfmod else "Merken"
            )
        self._fill_munition_panel_nsc(roller, widget or self.active_sc_widget, is_fk=is_fk, is_at=not is_vt)

    def _fill_munition_panel_nsc(self, roller, widget, *, is_fk=False, is_at=False):
        box = roller.get("munition_box") if roller else None
        host = roller.get("munition_host") if roller else None
        if box is None or host is None:
            return
        try:
            if widget is not None:
                widget.objectName()
        except RuntimeError:
            widget = None
        show = bool(is_fk and is_at and widget is not None)
        box.setVisible(show)
        lay = host.layout()
        if lay is None:
            lay = QVBoxLayout(host)
            lay.setContentsMargins(0, 0, 0, 0)
        while lay.count():
            child = lay.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        if not show:
            return
        items = normalize_ammo_list(
            getattr(widget, "munition_data", None)
            or (getattr(widget, "data", None) or {}).get("munition")
            or []
        )
        if not items:
            lay.addWidget(QLabel("<i>Keine Munition – im Kampf-Tab hinzufügen.</i>"))
            return
        group = QButtonGroup(host)
        group.setExclusive(True)
        for a in items:
            n = int(a.get("anzahl", 0) or 0)
            label = f"{a.get('name') or 'Munition'}  ({n})"
            extra = []
            if a.get("tp"):
                extra.append(f"TP {a['tp']}")
            if a.get("rw"):
                extra.append(f"RW {a['rw']}")
            if a.get("lz"):
                extra.append(f"LZ {a['lz']}")
            if extra:
                label += "  – " + ", ".join(extra)
            cb = QCheckBox(label)
            cb.setEnabled(n > 0)
            cb.setChecked(bool(a.get("selected")) and n > 0)
            tip = a.get("eigenschaften") or ""
            if tip:
                cb.setToolTip(tip)
            aid = a.get("id")
            cb.toggled.connect(
                lambda checked=False, i=aid, w=widget, r=roller: self._on_nsc_munition_toggled(w, i, checked, r)
            )
            lay.addWidget(cb)
            group.addButton(cb)
        roller["_munition_group"] = group

    def _on_nsc_munition_toggled(self, widget, ammo_id, checked, roller):
        if not checked or widget is None:
            return
        items = set_selected_ammo(widget._get_munition() if hasattr(widget, "_get_munition") else [], ammo_id)
        if hasattr(widget, "_set_munition"):
            widget._set_munition(items)
            widget._rebuild_munition_ui()
        ptype = "AT"
        if "VT " in (getattr(self, "active_attribute_name", "") or ""):
            ptype = "VT"
        self._apply_manöver_availability_nsc(roller, widget, probe_type=ptype)

    def _nsc_be(self, widget):
        """BE der NSC-Rüstung aus data.ruestung."""
        if not widget:
            return 0
        data = getattr(widget, "data", None) or {}
        ru = data.get("ruestung") or {}
        if isinstance(ru, dict):
            return int(ru.get("be", 0) or 0)
        return int(data.get("be", 0) or 0)

    def _manöver_at_mod(self, roller, widget=None):
        """Berechnet den AT/VT/FK-Mod inkl. –BE aus den gewählten Manövern."""
        mod = 0
        be = self._nsc_be(widget if widget is not None else self.active_sc_widget)
        widgets = roller.get("manöver_widgets") or {}
        if widgets:
            for mid, info in widgets.items():
                cb = info.get("cb")
                if not cb or not cb.isChecked():
                    continue
                mdef = info.get("def") or {}
                m = mdef.get("mod")
                if m == "variable":
                    spin = info.get("spin")
                    val = spin.value() if spin is not None else 2
                    mod -= val
                elif isinstance(m, (int, float)):
                    mod += int(m)
                if mdef.get("mod_be"):
                    mod -= be
            mod += self._riposte_combo_mod_nsc(roller, widget)
            return mod
        try:
            if roller.get("manöver_wuchtschlag") and roller["manöver_wuchtschlag"].isChecked():
                sp = roller.get("manöver_wuchtschlag_spin")
                mod -= sp.value() if sp is not None else 2
            if roller.get("manöver_hammerschlag") and roller["manöver_hammerschlag"].isChecked():
                mod -= 8
            if roller.get("manöver_todesstoß") and roller["manöver_todesstoß"].isChecked():
                mod -= 8
            if roller.get("manöver_rüstungsbrecher") and roller["manöver_rüstungsbrecher"].isChecked():
                mod -= 4
        except RuntimeError:
            pass
        return mod

    def _riposte_combo_mod_nsc(self, roller, widget=None) -> int:
        """Zusätzlicher VT-Malus durch alle mit Riposte kombinierten AT-Manöver (NSC)."""
        widgets = roller.get("manöver_widgets") or {}
        riposte = widgets.get("riposte")
        if not riposte or not riposte.get("cb") or not riposte["cb"].isChecked():
            return 0
        be = self._nsc_be(widget if widget is not None else self.active_sc_widget)
        extra = 0
        for mid, info in (roller.get("riposte_kombi_widgets") or {}).items():
            cb = info.get("cb")
            if not cb or not cb.isChecked():
                continue
            mdef = info.get("def") or {}
            m = mdef.get("mod")
            if m == "variable":
                sp = info.get("spin")
                val = sp.value() if sp is not None else 2
                extra -= val
            elif isinstance(m, (int, float)):
                extra += int(m)
            if mdef.get("mod_be"):
                extra -= be
        return extra

    def _selected_manöver_flags_nsc(self, roller):
        flags = {
            "no_damage": False,
            "auflaufen": False,
            "riposte": False,
            "any": False,
            "notes": [],
            "wucht": 0,
            "rüst": False,
            "tod": False,
            "hammerschlag": False,
            "sturm_tp": 0,
        }
        widgets = roller.get("manöver_widgets") or {}
        for mid, info in widgets.items():
            cb = info.get("cb")
            if not cb or not cb.isChecked():
                continue
            flags["any"] = True
            mdef = info.get("def") or {}
            effekt = mdef.get("effekt")
            spin_val = info.get("spin").value() if info.get("spin") is not None else 0
            if effekt in ("sturmangriff", "ueberrennen"):
                mode = info.get("mode")
                if mode is not None and mode.currentData() == "gs":
                    spin_val = self._get_nsc_gs(self.active_sc_widget)
                    if info.get("spin") is not None:
                        info["spin"].setValue(spin_val)
            h = manöver_tp_hinweis(mdef, spin_val=spin_val, at_ew=self._last_at_ew)
            if h:
                flags["notes"].append(h)
            if effekt == "schaden_0":
                flags["no_damage"] = True
            if effekt == "auflaufen" or mid == "auflaufen_lassen":
                flags["auflaufen"] = True
            if effekt == "riposte" or mid == "riposte":
                flags["riposte"] = True
            if effekt == "tp_bonus":
                flags["wucht"] = spin_val or 2
            elif effekt == "sp_statt_tp":
                flags["rüst"] = True
            elif effekt == "extra_wunden_2":
                flags["tod"] = True
            elif effekt == "waffe_x2":
                flags["hammerschlag"] = True
            elif effekt in ("sturmangriff", "ueberrennen"):
                flags["sturm_tp"] = max(flags["sturm_tp"], int(spin_val or 0))

        if flags["riposte"]:
            for mid, info in (roller.get("riposte_kombi_widgets") or {}).items():
                cb = info.get("cb")
                if not cb or not cb.isChecked():
                    continue
                flags["any"] = True
                mdef = info.get("def") or {}
                effekt = mdef.get("effekt")
                spin_val = info.get("spin").value() if info.get("spin") is not None else 0
                h = manöver_tp_hinweis(mdef, spin_val=spin_val, at_ew=self._last_at_ew)
                if h:
                    flags["notes"].append(f"Kombi: {h}")
                if effekt == "schaden_0":
                    flags["no_damage"] = True
                if effekt == "tp_bonus":
                    flags["wucht"] = max(flags["wucht"], spin_val or 2)
                elif effekt == "sp_statt_tp":
                    flags["rüst"] = True
                elif effekt == "extra_wunden_2":
                    flags["tod"] = True
                elif effekt == "waffe_x2":
                    flags["hammerschlag"] = True
        return flags

    def execute_master_roll_nsc(self):
        if not self.active_sc_widget:
            return
        try:
            blocker = has_blocking_probe_effect(self.active_sc_widget._get_effects())
        except Exception:
            blocker = None
        if blocker and not getattr(self, "active_tp_string", None):
            QMessageBox.information(
                None,
                str(blocker),
                f"Keine Probe möglich: Effekt „{blocker}“ aktiv.",
            )
            return
        # Volle Defensive ohne Defensiver Kampfstil: nur AT blockieren (VT/Riposte/Auflaufen ok)
        attr = getattr(self, "active_attribute_name", "") or ""
        is_at_probe = "AT " in attr and not getattr(self, "active_tp_string", None)
        if is_at_probe:
            try:
                at_blocker = has_blocking_at_effect(self.active_sc_widget._get_effects())
            except Exception:
                at_blocker = None
            if at_blocker:
                QMessageBox.information(
                    None,
                    str(at_blocker),
                    f"Keine Attacke möglich: Effekt „{at_blocker}“ aktiv "
                    f"(Volle Defensive belegt die Aktion).",
                )
                return
            if getattr(self, "pending_weapon_is_fk", False) and self.active_sc_widget:
                w = self.active_sc_widget
                data = getattr(w, "data", None) or {}
                items = normalize_ammo_list(
                    getattr(w, "munition_data", None) or data.get("munition") or []
                )
                items, used = consume_selected_ammo(items)
                if used:
                    data["munition"] = items
                    try:
                        if hasattr(w, "_set_munition"):
                            w._set_munition(items, notify=False)
                        if hasattr(w, "_rebuild_munition_ui"):
                            w._rebuild_munition_ui()
                    except RuntimeError:
                        pass
                    try:
                        self._fill_munition_panel_nsc(
                            self.nsc_dice_roller, w, is_fk=True, is_at=True
                        )
                    except RuntimeError:
                        pass
        roller = self.nsc_dice_roller

        # 1. Fall: TP-Wurf
        if self.active_tp_string:
            dice_parts = re.findall(r"([+-]?\s*\d*[wWdD]\d+|\s*[+-]?\s*\d+)", self.active_tp_string.replace(" ", ""))
            base_sum = 0
            base_str_parts = []

            for part in dice_parts:
                part = part.strip()
                if not part:
                    continue
                dice_pattern = re.match(r"([+-])?(\d+)?[wWdD](\d+)", part)
                mod_pattern = re.match(r"([+-])?(\d+)", part)

                if dice_pattern:
                    sign = -1 if dice_pattern.group(1) == '-' else 1
                    num = int(dice_pattern.group(2)) if dice_pattern.group(2) else 1
                    sides = int(dice_pattern.group(3))
                    rolls = [random.randint(1, sides) for _ in range(num)]
                    s = sum(rolls)
                    base_sum += sign * s
                    base_str_parts.append(f"{part} ({s})")
                elif mod_pattern and not re.search(r'[wWdD]', part):
                    sign = -1 if mod_pattern.group(1) == '-' else 1
                    val = int(mod_pattern.group(2))
                    base_sum += sign * val
                    base_str_parts.append(part)

            gift_notes = []
            wpn = getattr(self, "pending_weapon_name", None) or ""
            # Waffenschaden VOR Hammerschlag
            if self.active_sc_widget and hasattr(self.active_sc_widget, "_get_effects"):
                for te in collect_tp_dice_effects(self.active_sc_widget._get_effects(), wpn):
                    wsch = te.get("waffenschaden") or ""
                    if wsch:
                        dmg, detail = parse_tp_dice_string(wsch)
                        if dmg:
                            base_sum += dmg
                            base_str_parts.append(
                                f"{dmg:+d} ({detail}, Waffenschaden/{te.get('name')})"
                            )

            if roller["hammerschlag_check"].isChecked():
                base_sum *= 2
                base_str_parts.append("(x2 Hammerschlag)")

            # Atemtechnik +1W6 nur noch ueber Aktive Effekte (tp_dice), nicht ueber Haken.

            # TP-Bonus NACH Hammerschlag / Waffengift
            if self.active_sc_widget and hasattr(self.active_sc_widget, "_get_effects"):
                for te in collect_tp_dice_effects(self.active_sc_widget._get_effects(), wpn):
                    dice_expr = te.get("dice") or ""
                    if dice_expr:
                        dmg, detail = parse_tp_dice_string(dice_expr)
                        if dmg:
                            base_sum += dmg
                            base_str_parts.append(
                                f"{'+' if dmg >= 0 else ''}{dmg} ({detail}, {te.get('name')})"
                            )
                    if te.get("info") or te.get("is_waffengift"):
                        note = te.get("info") or te.get("name") or "Waffengift"
                        gift_notes.append(
                            f"{te.get('name')}: {note}" if te.get("info") else str(te.get("name"))
                        )
            ammo = None
            if self.active_sc_widget:
                ammo = selected_ammo(normalize_ammo_list(
                    getattr(self.active_sc_widget, "munition_data", None)
                    or (self.active_sc_widget.data or {}).get("munition")
                    or []
                ))
            if ammo and (ammo.get("tp") or "").strip():
                dmg, detail = parse_tp_dice_string(ammo.get("tp") or "")
                if dmg:
                    base_sum += dmg
                    base_str_parts.append(
                        f"{'+' if dmg >= 0 else ''}{dmg} ({detail}, {ammo.get('name')})"
                    )
            if self.active_sc_widget and hasattr(self.active_sc_widget, "_get_effects"):
                new_list, evs = tick_effects_on_tp(self.active_sc_widget._get_effects(), wpn)
                self.active_sc_widget._set_effects(new_list)
                self.active_sc_widget._rebuild_effects_ui()
                if hasattr(self.active_sc_widget, "_handle_effect_events"):
                    self.active_sc_widget._handle_effect_events(evs)

            if getattr(self, "_pending_no_damage", False):
                notes = getattr(self, "_pending_manöver_notes", None) or []
                lines = ["<b>Kein Schaden</b> – Manöverwirkung statt TP:"]
                lines.extend(f"• {n}" for n in notes)
                roller["label_result"].setText("<br>".join(lines))
                return

            wucht = getattr(self, "_pending_wuchtschlag_tp", 0) or 0
            if wucht:
                base_sum += wucht
                base_str_parts.append(f"+{wucht} (Wuchtschlag)")
            sturm = getattr(self, "_pending_sturm_tp", 0) or 0
            if sturm:
                base_sum += sturm
                base_str_parts.append(f"+{sturm} (Sturmangriff/Überrennen)")

            if self.präzision_ge_bonus > 0:
                base_sum += self.präzision_ge_bonus
                base_str_parts.append(f"+{self.präzision_ge_bonus} (Präzision/GE)")

            if getattr(self, "_pending_auflaufen", False):
                gs = 0
                if "auflaufen_gs_spin" in roller:
                    gs = int(roller["auflaufen_gs_spin"].value() or 0)
                base_sum += gs
                base_str_parts.append(f"+{gs} (Gegner-GS / Auflaufen)")

            if self.custom_mod_value != 0:
                base_sum += self.custom_mod_value
                base_str_parts.append(f"{'+' if self.custom_mod_value > 0 else ''}{self.custom_mod_value} (Mod)")

            html = f"Schaden: {' '.join(base_str_parts)} = <b>{base_sum}</b>"
            notes = getattr(self, "_pending_manöver_notes", None) or []
            extra = [n for n in notes if not (n.startswith("+") and "TP" in n)]
            if extra:
                html += "<br><i>" + " · ".join(extra) + "</i>"
            else:
                if getattr(self, "_pending_rüstungsbrecher", False):
                    html += " <i>(SP statt TP)</i>"
            if gift_notes:
                html += "<br><i>" + " · ".join(gift_notes) + "</i>"
                if getattr(self, "_pending_todesstoß", False):
                    html += " <i>(+2 Wunden)</i>"
            roller["label_result"].setText(html)
            return

        # 2. Fall: Attribut / Kampf-Wurf
        val = self.active_attribute_value
        mod = self.custom_mod_value

        manöver_mod = 0
        manöver_text = ""
        is_at_pre = "AT " in (self.active_attribute_name or "")
        is_vt_pre = "VT " in (self.active_attribute_name or "")
        if is_at_pre or is_vt_pre:
            manöver_mod = self._manöver_at_mod(roller, self.active_sc_widget)
            if manöver_mod != 0:
                be = self._nsc_be(self.active_sc_widget)
                be_used = False
                for mid, info in (roller.get("manöver_widgets") or {}).items():
                    cb = info.get("cb")
                    if cb and cb.isChecked() and (info.get("def") or {}).get("mod_be"):
                        be_used = True
                        break
                if be_used and be:
                    manöver_text = f" {manöver_mod:+d} (Manöver, inkl. –{be} BE)".replace("+-", "-")
                else:
                    manöver_text = f" {manöver_mod:+d} (Manöver)".replace("+-", "-")

        wunden = self.active_sc_widget.data.get("wunden", [])
        wunden_modus = self.active_sc_widget.data.get("wunden_modus", 0)
        ignore_wounds = self.active_sc_widget.data.get("wunden_ignorieren", False)
        malus = 0
        wunden_text = ""
        if not ignore_wounds:
            cnt = 0
            if wunden_modus == 0:
                cnt = len([w for w in wunden if w in ["X", "/"]])
            elif wunden_modus == 1:
                cnt = len([w for w in wunden if w in ["/", "II"]])
            elif wunden_modus == 2:
                cnt = len([w for w in wunden if w in ["/", "IV"]])
            if cnt >= 3:
                malus = (cnt - 2) * 2
                wunden_text = f" - {malus} (Wunden)"

        is_at = "AT " in (self.active_attribute_name or "")
        combat_mod, combat_parts = self._sum_combat_mods_nsc(roller, is_at=is_at)
        reach_mod = combat_mod

        # Reaktions-Malus: VT (normal) und AT-Reaktion (Passierschlag)
        # Freie Reaktion: weder Malus noch Zähler
        roll_mode = getattr(self, "_roll_mode", "normal") or "normal"
        is_vt_probe = "VT " in (self.active_attribute_name or "")
        apply_reaction = False
        if roll_mode == "freie_reaktion":
            apply_reaction = False
        elif roll_mode == "reaktion":
            # Passierschlag / bewusste Reaktion
            apply_reaction = True
        elif is_vt_probe:
            # normale VT = Reaktion
            apply_reaction = True
        # normale AT: kein Reaktionsmalus

        reaktion_mod = 0
        reaktion_text = ""
        if apply_reaction and self.active_sc_widget and hasattr(self.active_sc_widget, "get_reaktion_malus"):
            if getattr(self.active_sc_widget, "show_ini_header", False) or getattr(
                self.active_sc_widget, "reaktion_spin", None
            ) is not None:
                reaktion_mod = int(self.active_sc_widget.get_reaktion_malus() or 0)
                if reaktion_mod:
                    reaktion_text = f" {reaktion_mod} (Reaktionen)"
                elif roll_mode == "reaktion":
                    reaktion_text = " (Reaktion)"
        elif roll_mode == "freie_reaktion":
            reaktion_text = " (Freie Reaktion)"
        elif roll_mode == "reaktion":
            reaktion_text = " (Reaktion)"

        if roller["radio1W20"].isChecked():
            roll_res = random.randint(1, 20)
            roll_detail = format_roll_info_1w20(roll_res)
        else:
            rolls = sorted([random.randint(1, 20) for _ in range(3)])
            roll_res = rolls[1]
            roll_detail = format_roll_info_3w20(rolls, roll_res)

        self.last_at_die = roll_res
        is_at = "AT " in (self.active_attribute_name or "")
        is_vt = "VT " in (self.active_attribute_name or "")

        effect_mod = 0
        effect_text = ""
        if hasattr(self.active_sc_widget, "get_effect_mods"):
            em = self.active_sc_widget.get_effect_mods()
            effect_mod = int(em.get("proben", 0) or 0)
            if is_at:
                effect_mod += int(em.get("at", 0) or 0)
            if is_vt:
                effect_mod += int(em.get("vt", 0) or 0)
            if effect_mod:
                effect_text = f" {'+' if effect_mod > 0 else ''}{effect_mod} (Effekte)"

        zweite_mod = 0
        zweite_text = ""
        if is_at:
            zec = roller.get("zweite_einfache_check")
            try:
                if zec is not None and zec.isChecked():
                    zweite_mod = -4
                    zweite_text = " −4 (2. einf. Aktion)"
            except RuntimeError:
                pass

        total = val + roll_res - malus + mod + reach_mod + manöver_mod + effect_mod + reaktion_mod + zweite_mod
        if is_at:
            self._last_at_ew = total

        mod_text = f" {'+' if mod >= 0 else ''}{mod} (Mod)" if mod != 0 else ""
        if combat_parts:
            reach_text = f" {reach_mod:+d} (Kampf: {', '.join(combat_parts)})".replace("+-", "-")
        else:
            reach_text = ""

        html = (
            f"{self.active_attribute_name} ({val}) + {roll_detail}{wunden_text}"
            f"{reach_text}{manöver_text}{reaktion_text}{zweite_text}{mod_text}{effect_text} = <b>{total}</b>"
        )
        flags = self._selected_manöver_flags_nsc(roller)
        if flags["notes"]:
            html += "<br><i>" + " · ".join(flags["notes"]) + "</i>"
        if is_vt and self.active_sc_widget and self._nsc_has_vorteil(self.active_sc_widget, "Gegenhalten"):
            html += (
                "<br><b>Gegenhalten</b>: Wenn du eine Attacke abwehrst, die mit einem "
                "Manöver verstärkt wurde, darfst du sofort einen Passierschlag gegen "
                "den Angreifer ausführen."
            )
        roller["label_result"].setText(html)
        self._update_triumph_ui(roller, roll_res, is_at, is_vt)

        if is_at:
            atem_on = bool(
                roller.get("atemtechnik_check") and roller["atemtechnik_check"].isChecked()
            )
            if not atem_on and self.active_sc_widget and hasattr(self.active_sc_widget, "_has_active_atemtechnik"):
                atem_on = bool(self.active_sc_widget._has_active_atemtechnik())
                if atem_on and roller.get("atemtechnik_check"):
                    roller["atemtechnik_check"].setVisible(True)
                    roller["atemtechnik_check"].setChecked(True)
            self._pending_atemtechnik = atem_on
            if atem_on and hasattr(self.active_sc_widget, "ensure_atemtechnik_effect"):
                self.active_sc_widget.ensure_atemtechnik_effect()
        if is_at and self._has_präzision(self.active_sc_widget) and roll_res >= 16:
            ge = self._get_ge_for_präzision(self.active_sc_widget)
            self.präzision_ge_bonus = ge
            roller["präzision_label"].setText(
                f"Präzision ausgelöst (W{roll_res} ≥ 16)! +{ge} GE TP beim Schaden."
            )
            roller["präzision_label"].setVisible(True)
        else:
            if not is_at:
                self.präzision_ge_bonus = 0
            roller["präzision_label"].setVisible(bool(self.präzision_ge_bonus and is_at))

        # Weiter → Schaden steuern
        show_continue = False
        if flags["no_damage"]:
            show_continue = False
        elif is_at and self.pending_tp_string:
            show_continue = True
        elif is_vt and (flags["auflaufen"] or flags.get("riposte")) and self.pending_tp_string:
            show_continue = True
        if "continue_btn" in roller:
            roller["continue_btn"].setVisible(show_continue)
            if flags["auflaufen"]:
                roller["continue_btn"].setText("Weiter → Schaden (Auflaufen)")
            elif flags.get("riposte"):
                roller["continue_btn"].setText("Weiter → Schaden (Riposte)")
            else:
                roller["continue_btn"].setText("Weiter → Schaden")

        # Zähler erhöhen bei normaler VT und bei „Reaktion würfeln“ (nicht bei freier Reaktion)
        roll_mode = getattr(self, "_roll_mode", "normal") or "normal"
        should_inc = False
        if roll_mode == "freie_reaktion":
            should_inc = False
        elif roll_mode == "reaktion":
            should_inc = True
        elif is_vt:
            should_inc = True
        if should_inc and self.active_sc_widget and hasattr(self.active_sc_widget, "increment_reaktion"):
            if getattr(self.active_sc_widget, "reaktion_spin", None) is not None:
                self.active_sc_widget.increment_reaktion()
        self._roll_mode = "normal"

        if is_at and self.active_sc_widget and hasattr(self.active_sc_widget, "_get_effects"):
            new_list, evs = tick_effects_on_at(self.active_sc_widget._get_effects())
            self.active_sc_widget._set_effects(new_list)
            self.active_sc_widget._rebuild_effects_ui()
            if hasattr(self.active_sc_widget, "_handle_effect_events"):
                self.active_sc_widget._handle_effect_events(evs)

    def continue_to_damage_nsc(self):
        """Wechselt von AT/VT-Ergebnis in die Schadensphase und übernimmt Manöver-Haken."""
        if not self.pending_tp_string or not self.active_sc_widget:
            return
        roller = self.nsc_dice_roller
        flags = self._selected_manöver_flags_nsc(roller)

        if flags["no_damage"]:
            lines = ["<b>Kein Schaden</b> – Manöverwirkung:"]
            lines.extend(f"• {n}" for n in flags["notes"])
            roller["label_result"].setText("<br>".join(lines))
            roller["continue_btn"].setVisible(False)
            return

        wucht = flags["wucht"]
        rüst = flags["rüst"]
        tod = flags["tod"]
        hammerschlag_selected = flags["hammerschlag"]
        notes = list(flags["notes"])
        auflaufen = flags["auflaufen"]
        riposte = flags.get("riposte", False)

        self._pending_wuchtschlag_tp = wucht
        self._pending_rüstungsbrecher = rüst
        self._pending_todesstoß = tod
        self._pending_manöver_notes = notes
        self._pending_no_damage = False
        self._pending_auflaufen = auflaufen
        self._pending_riposte = riposte
        self._pending_sturm_tp = int(flags.get("sturm_tp", 0) or 0)

        atem_selected = bool(
            roller.get("atemtechnik_check") and roller["atemtechnik_check"].isChecked()
        )
        atem_active = bool(
            hasattr(self.active_sc_widget, "_has_active_atemtechnik")
            and self.active_sc_widget._has_active_atemtechnik()
        )
        atem_on = bool(
            atem_selected
            or atem_active
            or getattr(self, "_pending_atemtechnik", False)
        )
        self._pending_atemtechnik = atem_on

        self.active_tp_string = self.pending_tp_string
        self.active_attribute_name = f"TP {self.pending_weapon_name or ''}"
        self._roll_mode = "normal"
        # Schaden ist weder Aktion noch Reaktion
        if "reaktion_btn" in roller:
            roller["reaktion_btn"].setVisible(False)
        if "free_reaktion_btn" in roller:
            roller["free_reaktion_btn"].setVisible(False)
        roller["options_box"].setVisible(False)
        roller["reach_box"].setVisible(False)
        roller["manöver_box"].setVisible(False)
        if "kampfmod_box" in roller:
            roller["kampfmod_box"].setVisible(False)
        roller["continue_btn"].setVisible(False)
        # TP: keine Aktionen-/Hammerschlag-UI – Zustand nur intern merken
        if atem_on and hasattr(self.active_sc_widget, "ensure_atemtechnik_effect"):
            self.active_sc_widget.ensure_atemtechnik_effect()
        if roller.get("atemtechnik_check"):
            roller["atemtechnik_check"].blockSignals(True)
            roller["atemtechnik_check"].setChecked(bool(atem_on))
            roller["atemtechnik_check"].setVisible(False)
            roller["atemtechnik_check"].blockSignals(False)
        if roller.get("aktionen_box"):
            roller["aktionen_box"].setVisible(False)
        for key in ("volle_off_check", "volle_def_check"):
            cb = roller.get(key)
            if cb is not None:
                cb.blockSignals(True)
                cb.setVisible(False)
                cb.blockSignals(False)
        roller["hammerschlag_check"].blockSignals(True)
        roller["hammerschlag_check"].setChecked(bool(hammerschlag_selected))
        roller["hammerschlag_check"].setVisible(False)
        roller["hammerschlag_check"].blockSignals(False)
        zec = roller.get("zweite_einfache_check")
        if zec is not None:
            zec.blockSignals(True)
            zec.setChecked(False)
            zec.setVisible(False)
            zec.blockSignals(False)
        self._fill_waffeig_panel(roller, self.active_sc_widget, self.pending_weapon_name)
        if "auflaufen_gs_spin" in roller:
            roller["auflaufen_gs_spin"].setVisible(auflaufen)
            roller["auflaufen_gs_label"].setVisible(auflaufen)
        roller["label_mod"].setText("0")
        self.custom_mod_value = 0
        if auflaufen:
            roller["label_probe"].setText(
                f"<h3>Auflaufen lassen: {self.pending_weapon_name} ({self.pending_tp_string}) + Gegner-GS</h3>"
            )
        elif riposte:
            roller["label_probe"].setText(
                f"<h3>Riposte: {self.pending_weapon_name} ({self.pending_tp_string})</h3>"
            )
        else:
            roller["label_probe"].setText(
                f"<h3>Schaden: {self.pending_weapon_name} ({self.pending_tp_string})</h3>"
            )
        if notes:
            roller["label_result"].setText("Manöver: " + " · ".join(notes))
        else:
            roller["label_result"].setText("Bereit zum Schadenswurf …")

    def continue_to_damage_ini(self):
        """INI-Variante: nutzt denselben Flow über Pointer-Tausch."""
        backup_widget = self.active_sc_widget
        backup_roller = self.nsc_dice_roller
        self.active_sc_widget = self.active_ini_widget
        self.nsc_dice_roller = self.ini_dice_roller
        try:
            self.continue_to_damage_nsc()
        finally:
            self.active_sc_widget = backup_widget
            self.nsc_dice_roller = backup_roller

    def prepare_at_roll_ini(self, widget, attr_name, value, tp_string):
        """AT/VT im INI-Tab mit Manöver-Flow."""
        self._last_nsc_prepare = {
            "kind": "at_ini",
            "attr_name": attr_name,
            "value": value,
            "tp_string": tp_string or "",
        }
        if attr_name.startswith("VT "):
            wname = attr_name.replace("VT ", "", 1)
            ptype = "VT"
        else:
            wname = attr_name.replace("AT ", "", 1)
            ptype = "AT"
        try:
            if widget is not None:
                widget.save_data()
        except Exception:
            pass
        self.pending_tp_string = tp_string or ""
        self.pending_weapon_name = wname
        self.pending_weapon_is_fk = bool(self._weapon_is_fernkampf_obj(
            self._resolve_nsc_weapon(wname, widget)
        ))
        self.prepare_ini_roll(widget, attr_name, value)
        self.pending_tp_string = tp_string or ""
        self.pending_weapon_name = wname
        self.pending_weapon_is_fk = bool(self._weapon_is_fernkampf_obj(
            self._resolve_nsc_weapon(wname, widget)
        ))
        self.ini_dice_roller["manöver_box"].setVisible(True)
        self._fill_waffeig_panel(self.ini_dice_roller, widget, wname)
        self._apply_manöver_availability_nsc(self.ini_dice_roller, widget, probe_type=ptype)
        self._show_kampfmod_for_probe(self.ini_dice_roller, attr_name, widget)
        self._sync_aktionen_checks_nsc(
            self.ini_dice_roller,
            widget,
            is_tp=False,
            is_at=(ptype == "AT"),
            is_vt=(ptype == "VT"),
        )

    def _execute_roll_generic(self, roller_dict, widgets_list):
        if not self.active_sc_widget or not self.active_attribute_name: return
        
        check_global = roller_dict["widget"].findChild(QCheckBox, "checkGlobalRoll")
        roll_everyone_checked = check_global.isChecked() if check_global else False
        
        results = []

        def perform_roll(name, val, ignore_wounds, current_wounds, wunden_modus=0, is_main_target=False):
            roll_method = "1W20" if roller_dict["radio1W20"].isChecked() else "3W20"
            rolls = []
            final_roll = 0
            roll_detail = ""
            
            if roll_method == "1W20":
                r = random.randint(1, 20)
                rolls = [r]
                final_roll = r
                roll_detail = format_die_html(r, 20)
            else:
                rolls = sorted([random.randint(1, 20) for _ in range(3)])
                final_roll = rolls[1]
                roll_detail = f"{format_w20_list(rolls)} → <b>{format_die_html(final_roll, 20)}</b>"

            malus = 0
            wunden_text = ""
            
            if not ignore_wounds:
                cnt = 0
                if wunden_modus == 0:
                    cnt = len([w for w in current_wounds if w in ["X", "/"]])
                elif wunden_modus == 1:
                    cnt = len([w for w in current_wounds if w in ["/", "II"]])
                elif wunden_modus == 2:
                    cnt = len([w for w in current_wounds if w in ["/", "IV"]])

                if cnt >= 3: 
                    malus = (cnt - 2) * 2
                    wunden_text = f" - {malus} (Wunden)"

            mod = self.custom_mod_value 
            mod_text = f" {'+' if mod >= 0 else ''}{mod} (Mod)" if mod != 0 else ""

            total = val + final_roll - malus + mod
            
            detail_html = f"{val} + {roll_detail} (W20){wunden_text}{mod_text}"
            return {"name": name, "total": total, "detail": detail_html}

        if roll_everyone_checked:
            for widget in widgets_list:
                widget.save_data() # Ensure data is fresh
                sc_data = widget.data
                should_roll = sc_data.get("alle_wuerfeln", False) or (widget == self.active_sc_widget)
                
                if should_roll:
                    attr_val = 0
                    if "attributes" in sc_data and self.active_attribute_name in sc_data["attributes"]:
                         attr_val = sc_data["attributes"][self.active_attribute_name]
                         # Basis-Attribute: gespeichert ist Wert, Probe nutzt PW = 2×Wert
                         if self.active_attribute_name in ["MU","KL","IN","CH","FF","GE","KO","KK"]:
                             attr_val = attr_val * 2
                    else:
                        val_map = {
                            "INI": "val_ini", "MR": "val_mr", "IN": "val_in", 
                            "Wachsamkeit": "val_wachsamkeit", "Menschenkenntnis": "val_menschenkenntnis"
                        }
                        key = val_map.get(self.active_attribute_name, "")
                        attr_val = sc_data.get(key, 0)
                    
                    res = perform_roll(
                        sc_data.get("name", "Unbekannt"), attr_val, 
                        sc_data.get("wunden_ignorieren", False), 
                        sc_data.get("wunden", []),
                        wunden_modus=sc_data.get("wunden_modus", 0),
                        is_main_target=(widget == self.active_sc_widget)
                    )
                    results.append(res)
        else:
            self.active_sc_widget.save_data() # Ensure data is fresh
            sc_data = self.active_sc_widget.data
            results.append(perform_roll(
                sc_data.get("name", "Ziel"), self.active_attribute_value, 
                sc_data.get("wunden_ignorieren", False), 
                sc_data.get("wunden", []),
                wunden_modus=sc_data.get("wunden_modus", 0),
                is_main_target=True
            ))

        results.sort(key=lambda x: x["total"], reverse=True)
        
        html = f"<h3>Wurf: {self.active_attribute_name}</h3>"
        for r in results: 
            html += f"<b>{r['name']}: {r['total']}</b> <span style='color:gray; font-size:small'>({r['detail']})</span><br>"
        
        roller_dict["label_result"].setText(html)