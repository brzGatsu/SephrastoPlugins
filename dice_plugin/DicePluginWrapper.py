# dice_plugin/DicePluginWrapper.py (Korrigierte Version 13 - Atemtechnik und Hammerschlag nur bei TP*)
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import (QCoreApplication, Qt, QEvent, QObject)
from PySide6.QtWidgets import QApplication, QAbstractSpinBox
from PySide6.QtGui import (QFont, QCursor)
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QGroupBox, QTabWidget, QPushButton, QToolButton, QLabel, QCheckBox, QSpinBox, QSizePolicy, QAbstractSpinBox,
    QPlainTextEdit, QListWidget, QListWidgetItem, QStackedWidget, QLineEdit, QComboBox,
    QSplitter, QScrollArea, QToolButton, QInputDialog, QTreeWidget, QTreeWidgetItem,
    QAbstractItemView, QHeaderView, QRadioButton, QButtonGroup, QTextBrowser,
    QDialog, QDialogButtonBox, QMenu, QMessageBox, QFrame)
from EffectsHelper import (
    EFFECT_PRESETS, blank_effect, from_preset, normalize_effect, normalize_list,
    sum_mods, effect_summary_line, tick_effects, tick_effects_on_at, tick_effects_on_tp,
    collect_tp_dice_effects, parse_tp_dice_string, make_atemtechnik_effect,
    make_volle_offensive_effect, make_volle_defensive_effect, is_volle_kampfhaltung,
    make_handlungsunfaehig_effect, make_blutend_effect, has_blocking_probe_effect,
    has_blocking_at_effect,
    _has_named_vorteil,
    all_presets, register_custom_preset, delete_custom_preset,
    load_custom_presets, dump_custom_presets, CUSTOM_EFFECT_PRESETS,
    load_custom_presets_from_file, save_custom_presets_to_file,
    MANOEVER, manöver_label, manöver_available, manöver_tp_hinweis, roll_gegenprobe,
    riposte_combinable_manöver, MUTUALLY_EXCLUSIVE_MANOEVER,
    combat_mod_from_combo,
    format_die_html, format_w20_list, format_roll_info_1w20, format_roll_info_3w20,
    colorize_dice_in_text, triumph_patzer_message,
    apply_wounds_batch, check_premature_timers, check_condition_info,
    concentration_ready_text, new_id,
    collect_player_probe_entries, collect_nsc_probe_entries, resolve_probe_pw,
    einschraenkung_malus, count_einschraenkungen,
    is_legacy_blutend_event, blutend_probe_overlay,
    NK_MOD_POSITION, NK_MOD_REICHWEITE, NK_MOD_UNTERGRUND, NK_MOD_DUNKELHEIT, NK_MOD_CHECKS,
    FK_MOD_GROESSE, FK_MOD_LICHT, FK_MOD_WIND, FK_MOD_BEWEGUNG, FK_MOD_DECKUNG, FK_MOD_CHECKS,
)
from Wolke import Wolke
from functools import partial
import re
import random
from Hilfsmethoden import Hilfsmethoden, SortedCategoryToListDict
from TalentInfoDialog import TalentInfoDialog
from AmmoHelper import (
    blank_ammo, normalize_ammo, normalize_ammo_list, ammo_has_eigenschaft,
    selected_ammo, set_selected_ammo, consume_selected_ammo, AmmoEditDialog,
    ensure_selected_ammo,
)
from QtUtils.AutoResizingTextBrowser import AutoResizingTextBrowser
from QtUtils.Section import Section
from Core.Vorteil import Vorteil
import UI.CharakterVorteile

class _NoWheelFilter(QObject):
    """Mausrad ändert keine SpinBox-/ComboBox-Werte – nur Scrollbereiche scrollen."""
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and isinstance(obj, (QAbstractSpinBox, QComboBox)):
            return True
        return False


_NO_WHEEL_FILTER = None


def _install_no_wheel_globally():
    global _NO_WHEEL_FILTER
    app = QApplication.instance()
    if app is None:
        return
    if getattr(app, "_ilaris_no_wheel_installed", False):
        return
    _NO_WHEEL_FILTER = _NoWheelFilter(app)
    app.installEventFilter(_NO_WHEEL_FILTER)
    app._ilaris_no_wheel_installed = True


class DicePluginWrapper(QtCore.QObject):
    modified = QtCore.Signal()

    def __init__(self):
        super().__init__()
        _install_no_wheel_globally()
        self.form = QWidget()
        self.currentlyLoading = False
        self.attributes = ["CH", "IN", "KL", "MU", "FF", "GE", "KO", "KK"]
        self.wunden_buttons = []
        self.container_text_edits = []
        self.thema_text_edits = []
        self.effect_name_edits = []  # legacy
        self.effect_duration_spins = []  # legacy
        self.effects_list_layout = None
        self._effects_rows = []
        self.pw_labels = {}
        self.attribute_buttons = {}
        self.active_dice_roller = None
        self.current_probe_name = None
        self.current_probe_pw = 0
        self.current_probe_type_str = ""
        self.custom_mod_value = 0
        self.is_tp_roll = False
        self.pending_tp_string = None
        self.pending_weapon_name = None
        self.präzision_ge_bonus = 0
        self._pending_wuchtschlag_tp = 0
        self._pending_rüstungsbrecher = False
        self._pending_todesstoß = False
        self._pending_manöver_notes = []  # Liste von Hinweis-Strings für TP-Anzeige
        self._pending_no_damage = False  # Umreißen/Entwaffnen/Umklammern
        self._pending_auflaufen = False  # VT-Manöver → TP mit Gegner-GS
        self._pending_riposte = False    # VT-Manöver → TP (eigener Waffenschaden)
        self._pending_sturm_tp = 0  # Sturmangriff / Überrennen +x TP
        # Session-Merker für Manöver / Kampfmods (Tab-/Char-wechsel, nicht zwingend disk)
        self._merken_manöver = None
        self._merken_kampfmod = None
        self._last_at_ew = None  # Erfolgswert der letzten AT für Gegenproben
        
        self.kampf_ws_label = None
        self.kampf_ws_stern_label = None
        self.kampf_gs_stern_label = None
        self.kampf_dh_stern_label = None
        self.kampf_ini_label = None
        self.kampf_ruestung_layout = None
        self.kampf_waffen_layout = None
        self.kampf_dice_roller = None
        self.kampf_stack = None
        self.kampf_dice_roller_index = 0
        self.nah_manöver_index = 1
        self.fern_manöver_index = 2
        self.nah_manöver_browser = None
        self.fern_manöver_browser = None

        self.vorteile_ui = None
        self.vorteile_treeWidget = None
        self.vorteile_plainText = None
        self.vorteile_labelVorteil = None
        self.vorteile_labelTyp = None
        self.vorteile_labelKosten = None
        self.vorteile_labelNachkauf = None
        self.vorteile_labelVoraussetzungen = None
        self.vorteile_vlQuerverweise = None
        self.vorteile_qvSlots = {}
        self.vorteile_qvTexts = {}
        self.vorteile_qvSections = {}
        self.vorteile_currentVort = None

        self._init_ui()
        self._connect_signals()
            
    def _init_ui(self):
        layout = QVBoxLayout(self.form)
        layout.addWidget(self._create_effects_box())
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.tabs.addTab(self._create_ressourcen_tab(), "Ressourcen")
        self.tabs.addTab(self._create_notizen_tab(), "Notizen")
        self.tabs.addTab(self._create_attribute_tab(), "Attribute")
        self.tabs.addTab(self._create_skills_tab(), "Fertigkeiten")
        self.tabs.addTab(self._create_supernatural_tab(), "Übernatürliches")
        self.tabs.addTab(self._create_kampf_tab(), "Kampf")
        self.tabs.addTab(self._create_vorteile_tab(), "Vorteile")

    def _connect_signals(self):
        self.tabs.currentChanged.connect(self.load_active_tab)
        self.checkEinschraenkungenIgnorieren.stateChanged.connect(self.update_einschraenkungen_ignorieren)
        # btn_dec_effects ist bereits in _create_effects_box verbunden

        self.spinSchips.valueChanged.connect(self.update_ressourcen)
        self.spinDukaten.valueChanged.connect(self.update_ressourcen)
        self.spinSilber.valueChanged.connect(self.update_ressourcen)
        self.spinHeller.valueChanged.connect(self.update_ressourcen)
        self.spinKreuzer.valueChanged.connect(self.update_ressourcen)
        self.textKleidung.textChanged.connect(self.update_kleidung)
        self.listContainers.itemDoubleClicked.connect(self.container_doppelgeklickt)
        self.buttonAddContainer.clicked.connect(self.add_container)
        self.buttonRemoveContainer.clicked.connect(self.remove_container)
        self.listContainers.currentItemChanged.connect(self.container_gewechselt)
        self.listThemen.itemDoubleClicked.connect(self.thema_doppelgeklickt)
        self.buttonAddThema.clicked.connect(self.add_thema)
        self.buttonRemoveThema.clicked.connect(self.remove_thema)
        self.listThemen.currentItemChanged.connect(self.thema_gewechselt)
        self.buttonFreeRoll.clicked.connect(self.roll_free_dice)
        self.lineFreeRoll.returnPressed.connect(self.roll_free_dice)
        
        for attr, button in self.attribute_buttons.items():
            button.clicked.connect(partial(self.prepare_dice_roll, attr))
        self.mr_button.clicked.connect(partial(self.prepare_dice_roll, "MR"))

        if hasattr(self, "spin_asp_current"):
            self.spin_asp_current.valueChanged.connect(self.update_supernatural_energies)
        if hasattr(self, "spin_kap_current"):
            self.spin_kap_current.valueChanged.connect(self.update_supernatural_energies)

        for roller in [self.attr_dice_roller, self.skill_dice_roller, self.supernatural_dice_roller, self.kampf_dice_roller]:
            if roller:
                roller['increase_btn'].clicked.connect(self.increase_mod)
                roller['decrease_btn'].clicked.connect(self.decrease_mod)
                roller['execute_btn'].clicked.connect(
                    lambda checked=False: self._execute_with_roll_mode("normal")
                )
                if 'continue_btn' in roller:
                    roller['continue_btn'].clicked.connect(self.continue_to_damage)
                if roller.get("reaktion_btn"):
                    roller["reaktion_btn"].clicked.connect(
                        lambda checked=False: self._execute_with_roll_mode("reaktion")
                    )
                if roller.get("free_reaktion_btn"):
                    roller["free_reaktion_btn"].clicked.connect(
                        lambda checked=False: self._execute_with_roll_mode("freie_reaktion")
                    )
                if roller.get("manöver_merken_btn"):
                    roller["manöver_merken_btn"].clicked.connect(
                        lambda checked=False, r=roller: self._merken_manöver_snapshot(r)
                    )
                if roller.get("manöver_reset_btn"):
                    roller["manöver_reset_btn"].clicked.connect(
                        lambda checked=False, r=roller: self._reset_manöver_ui(r, clear_memory=True)
                    )
                if roller.get("kampfmod_merken_btn"):
                    roller["kampfmod_merken_btn"].clicked.connect(
                        lambda checked=False, r=roller: self._merken_kampfmod_snapshot(r)
                    )
                if roller.get("kampfmod_reset_btn"):
                    roller["kampfmod_reset_btn"].clicked.connect(
                        lambda checked=False, r=roller: self._reset_kampfmod_ui(r, clear_memory=True)
                    )

    def load(self):
        if not hasattr(Wolke.Char, "dicePlugin_wunden"): Wolke.Char.dicePlugin_wunden = [None] * 8
        if not hasattr(Wolke.Char, "dicePlugin_wunden_ignorieren"): Wolke.Char.dicePlugin_wunden_ignorieren = False
        if not hasattr(Wolke.Char, "dicePlugin_wunden_modus"): Wolke.Char.dicePlugin_wunden_modus = 0
        if not hasattr(Wolke.Char, "dicePlugin_reaktionen"):
            Wolke.Char.dicePlugin_reaktionen = 0
        if hasattr(self, "reaktion_spin") and self.reaktion_spin is not None:
            self.reaktion_spin.blockSignals(True)
            self.reaktion_spin.setValue(int(Wolke.Char.dicePlugin_reaktionen or 0))
            self.reaktion_spin.blockSignals(False)
            self._update_reaktion_label()
        if not hasattr(Wolke.Char, "dicePlugin_effekte"):
            Wolke.Char.dicePlugin_effekte = []
        else:
            Wolke.Char.dicePlugin_effekte = normalize_list(Wolke.Char.dicePlugin_effekte)
        # Benutzer-Vorlagen aus dice_master_data.json (geteilt mit Master)
        load_custom_presets_from_file()
        if hasattr(self, "btn_add_preset"):
            self._rebuild_preset_menu()
        
        if not hasattr(Wolke.Char, "dicePlugin_schips"): Wolke.Char.dicePlugin_schips = 4
        if not hasattr(Wolke.Char, "dicePlugin_geld"): Wolke.Char.dicePlugin_geld = {'Dukaten': 0, 'Silber': 0, 'Heller': 0, 'Kreuzer': 0}
        if not hasattr(Wolke.Char, "dicePlugin_kleidung"): Wolke.Char.dicePlugin_kleidung = ""
        if not hasattr(Wolke.Char, "dicePlugin_inventar"): Wolke.Char.dicePlugin_inventar = [{"name": "Am Körper", "inhalt": ""}]
        if not hasattr(Wolke.Char, "dicePlugin_tagebuch"): Wolke.Char.dicePlugin_tagebuch = [{"titel": "Allgemein", "inhalt": ""}]
        if not hasattr(Wolke.Char, "dicePlugin_current_asp"): Wolke.Char.dicePlugin_current_asp = -1
        if not hasattr(Wolke.Char, "dicePlugin_current_kap"): Wolke.Char.dicePlugin_current_kap = -1
        if not hasattr(Wolke.Char, "dicePlugin_munition"):
            Wolke.Char.dicePlugin_munition = []
        else:
            Wolke.Char.dicePlugin_munition = normalize_ammo_list(Wolke.Char.dicePlugin_munition)
        self.load_active_tab(self.tabs.currentIndex())

    def load_active_tab(self, index):
        self.currentlyLoading = True
        try:
            tab_name = self.tabs.tabText(index)
            if tab_name == "Ressourcen": self.load_ressourcen_non_inventory(); self.load_inventar()
            elif tab_name == "Notizen": self.load_tagebuch()
            elif tab_name == "Attribute": self.load_attributes()
            elif tab_name == "Fertigkeiten": self.load_skills()
            elif tab_name == "Übernatürliches": self.load_supernatural_energies(); self.load_supernatural_skills()
            elif tab_name == "Kampf": self.load_kampf_tab()
            elif tab_name == "Vorteile": self.load_vorteile_tab()
            self.load_einschraenkungen()
            self.load_effects()
        finally:
            self.currentlyLoading = False

    def _create_effects_box(self):
        main_box = QGroupBox()
        main_layout = QVBoxLayout(main_box)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)

        # --- Einschränkungen ---
        einschraenkungen_box = QGroupBox("Einschränkungen")
        einschraenkungen_layout = QVBoxLayout(einschraenkungen_box)
        self.combo_wunden_modus = QComboBox()
        self.combo_wunden_modus.addItems(["Normal", "Koloss I", "Koloss II"])
        self.combo_wunden_modus.setToolTip("Koloss I/II: mehr Wundstufen bei Verwandlung")
        self.combo_wunden_modus.currentIndexChanged.connect(self._on_wunden_modus_changed)
        einschraenkungen_layout.addWidget(self.combo_wunden_modus)
        wunden_button_layout = QHBoxLayout()
        wunden_button_layout.setSpacing(2)
        wunden_button_layout.addStretch()
        self.wunden_buttons.clear()
        for i in range(8):
            button = QPushButton("")
            button.setFixedSize(35, 35)
            button.setToolTip("Klicken, um Zustand zu ändern (Wunde/Erschöpfung)")
            button.clicked.connect(partial(self.wunde_clicked, i))
            wunden_button_layout.addWidget(button)
            self.wunden_buttons.append(button)
        self.btn_add_einschraenkung = QPushButton("+")
        self.btn_add_einschraenkung.setFixedWidth(28)
        self.btn_add_einschraenkung.setToolTip(
            "Mehrere Erschöpfungen/Wunden auf einmal (eine Quelle) hinzufügen"
        )
        self.btn_add_einschraenkung.clicked.connect(self._modal_add_einschraenkungen)
        wunden_button_layout.addWidget(self.btn_add_einschraenkung)
        wunden_button_layout.addStretch()
        self.checkEinschraenkungenIgnorieren = QCheckBox("Einschränkungen ignorieren")
        einschraenkungen_layout.addLayout(wunden_button_layout)
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.addWidget(self.checkEinschraenkungenIgnorieren)
        bottom_row.addStretch()
        self.btn_wunden_info = QPushButton("i")
        self.btn_wunden_info.setFixedSize(32, 32)
        self.btn_wunden_info.setToolTip("Wundregeln / Proben (Wundschmerz, Kampfunfahigkeit, Blutung)")
        self.btn_wunden_info.clicked.connect(self._show_wunden_info_dialog)
        bottom_row.addWidget(self.btn_wunden_info)
        einschraenkungen_layout.addLayout(bottom_row)
        content_layout.addWidget(einschraenkungen_box)

        # --- Aktive Effekte (dynamisch) ---
        effekte_box = QGroupBox("Aktive Effekte")
        eff_outer = QVBoxLayout(effekte_box)
        btn_row = QHBoxLayout()
        self.btn_add_preset = QPushButton("+ Vorlage ▾")
        self.btn_add_preset.setToolTip("Vorgefertigten Effekt hinzufügen")
        self.btn_add_custom = QPushButton("+ Eigener Effekt")
        self.btn_dec_effects = QPushButton("− Runde")
        self.btn_dec_effects.setToolTip(
            "Dauer aller Timer-Effekte um 1 verringern und Reaktionszähler zurücksetzen"
        )
        self.btn_dec_effects.clicked.connect(self.decrement_effects)
        btn_row.addWidget(self.btn_add_preset)
        btn_row.addWidget(self.btn_add_custom)
        btn_row.addWidget(self.btn_dec_effects)

        # Reaktionszähler (neben − Runde)
        btn_row.addSpacing(12)
        btn_row.addWidget(QLabel("Reakt.:"))
        self.reaktion_spin = QSpinBox()
        self.reaktion_spin.setRange(0, 20)
        self.reaktion_spin.setValue(int(getattr(Wolke.Char, "dicePlugin_reaktionen", 0) or 0))
        self.reaktion_spin.setFixedWidth(46)
        self.reaktion_spin.setToolTip(
            "Reaktionen seit eigener Initiativephase.\n"
            "1. Reaktion: kein Malus, 2.: –4, 3.: –8, …\n"
            "Reset bei „− Runde“."
        )
        self.reaktion_spin.valueChanged.connect(self._on_reaktion_changed)
        btn_row.addWidget(self.reaktion_spin)
        self.reaktion_malus_label = QLabel("VT ±0")
        self.reaktion_malus_label.setStyleSheet("color: #666; min-width: 42px;")
        btn_row.addWidget(self.reaktion_malus_label)
        self._update_reaktion_label()

        btn_row.addStretch()
        eff_outer.addLayout(btn_row)

        self.effects_scroll = QScrollArea()
        self.effects_scroll.setWidgetResizable(True)
        # ~4 Effektzeilen sichtbar, bevor gescrollt werden muss
        self.effects_scroll.setMinimumHeight(160)
        self.effects_scroll.setMaximumHeight(220)
        self.effects_container = QWidget()
        self.effects_list_layout = QVBoxLayout(self.effects_container)
        self.effects_list_layout.setContentsMargins(0, 0, 0, 0)
        self.effects_list_layout.setSpacing(3)
        self.effects_list_layout.addStretch()
        self.effects_scroll.setWidget(self.effects_container)
        eff_outer.addWidget(self.effects_scroll)
        content_layout.addWidget(effekte_box, 1)

        self.wundenPenaltyLabel = QLabel("")
        self.wundenPenaltyLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wundenPenaltyLabel.setStyleSheet("font-weight: bold; color: #a12323;")
        self.wundenHinweisLabel = QLabel("")
        self.wundenHinweisLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wundenHinweisLabel.setStyleSheet("font-style: italic; color: #666;")
        self.effectsModLabel = QLabel("")
        self.effectsModLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.effectsModLabel.setStyleSheet("font-weight: bold; color: #236fa1;")

        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.wundenPenaltyLabel)
        main_layout.addWidget(self.wundenHinweisLabel)
        main_layout.addWidget(self.effectsModLabel)

        # Preset-Menü (Built-in + Benutzer)
        self._rebuild_preset_menu()
        self.btn_add_custom.clicked.connect(self._add_custom_effect)

        return main_box

    def _rebuild_preset_menu(self):
        menu = QMenu(self.form)
        builtins = menu.addMenu("Standard")
        for key, preset in EFFECT_PRESETS.items():
            act = builtins.addAction(preset["name"])
            act.triggered.connect(partial(self._add_effect_from_preset, key))
        user_menu = menu.addMenu("Eigene Vorlagen")
        if CUSTOM_EFFECT_PRESETS:
            for key, preset in sorted(CUSTOM_EFFECT_PRESETS.items(), key=lambda kv: kv[1].get("name") or ""):
                act = user_menu.addAction(preset.get("name") or key)
                act.triggered.connect(partial(self._add_effect_from_preset, key))
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
        # optional weiterhin am Charakter spiegeln (Kompatibilität)
        try:
            Wolke.Char.dicePlugin_effect_presets = dump_custom_presets()
        except Exception:
            pass
        if not self.currentlyLoading:
            self.modified.emit()

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
            self.form, "Als Vorlage speichern",
            "Name der Vorlage:",
            text=eff.get("name") or "Vorlage",
        )
        if not ok or not (name or "").strip():
            return
        register_custom_preset(name.strip(), eff)
        self._persist_custom_presets()
        self._rebuild_preset_menu()
        QMessageBox.information(self.form, "Vorlage", f"„{name.strip()}“ gespeichert.")

    def _get_effects(self):
        return normalize_list(getattr(Wolke.Char, "dicePlugin_effekte", []) or [])

    def _set_effects(self, effects):
        Wolke.Char.dicePlugin_effekte = normalize_list(effects)
        if not self.currentlyLoading:
            self.modified.emit()

    def load_effects(self):
        self._rebuild_effects_ui()
        self._update_effects_mod_label()

    def _rebuild_effects_ui(self):
        if self.effects_list_layout is None:
            return
        # clear
        while self.effects_list_layout.count():
            item = self.effects_list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._effects_rows = []
        for eff in self._get_effects():
            self._add_effect_row(eff)
        self.effects_list_layout.addStretch()

    def _add_effect_row(self, eff):
        row = QFrame()
        row.setFrameShape(QFrame.Shape.StyledPanel)
        hl = QHBoxLayout(row)
        hl.setContentsMargins(4, 2, 4, 2)
        hl.setSpacing(4)

        name_lab = QLabel(f"<b>{eff.get('name', '?')}</b>")
        name_lab.setMinimumWidth(100)
        hl.addWidget(name_lab, 2)

        summary = QLabel(effect_summary_line(eff))
        summary.setStyleSheet("color: #555; font-size: 11px;")
        summary.setWordWrap(True)
        hl.addWidget(summary, 3)

        timer_btn = QPushButton("⏱" if eff.get("has_timer") else "∞")
        timer_btn.setFixedWidth(28)
        timer_btn.setToolTip("Timer an/aus")
        timer_btn.clicked.connect(partial(self._toggle_effect_timer, eff.get("id")))
        hl.addWidget(timer_btn)

        dur_spin = QSpinBox()
        dur_spin.setRange(0, 999)
        dur_spin.setValue(int(eff.get("duration", 0) or 0))
        dur_spin.setFixedWidth(44)
        dur_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        dur_spin.setEnabled(bool(eff.get("has_timer")))
        dur_spin.valueChanged.connect(partial(self._on_effect_duration, eff.get("id")))
        hl.addWidget(dur_spin)

        info_btn = QPushButton("i")
        info_btn.setFixedWidth(24)
        info_btn.setToolTip("Info / freier Wurf")
        info_btn.clicked.connect(partial(self._show_effect_info, eff.get("id")))
        hl.addWidget(info_btn)

        edit_btn = QPushButton("✎")
        edit_btn.setFixedWidth(24)
        edit_btn.setToolTip("Bearbeiten")
        edit_btn.clicked.connect(partial(self._edit_effect, eff.get("id")))
        hl.addWidget(edit_btn)

        save_btn = QPushButton("★")
        save_btn.setFixedWidth(24)
        save_btn.setToolTip("Als Vorlage speichern")
        save_btn.clicked.connect(partial(self._save_effect_as_preset, eff.get("id")))
        hl.addWidget(save_btn)

        del_btn = QPushButton("✕")
        del_btn.setFixedWidth(24)
        del_btn.setStyleSheet("color: #a33; font-weight: bold;")
        del_btn.clicked.connect(partial(self._remove_effect, eff.get("id")))
        hl.addWidget(del_btn)

        # insert before stretch
        stretch = self.effects_list_layout.takeAt(self.effects_list_layout.count() - 1) if self.effects_list_layout.count() else None
        self.effects_list_layout.addWidget(row)
        if stretch:
            self.effects_list_layout.addItem(stretch)
        else:
            self.effects_list_layout.addStretch()
        self._effects_rows.append(row)

    def _player_vorteil_names(self):
        vorteile = getattr(Wolke.Char, "vorteile", {}) or {}
        return list(vorteile.keys())

    def _add_effect_from_preset(self, key):
        effects = self._get_effects()
        if key == "atemtechnik":
            ko = 0
            try:
                ko = int(Wolke.Char.attribute["KO"].wert)
            except Exception:
                ko = 1
            effects = [e for e in effects if not (e.get("name") or "").lower().startswith("atemtechnik")]
            effects.append(make_atemtechnik_effect(ko))
        elif key == "volle_offensive":
            has_ok = _has_named_vorteil(self._player_vorteil_names(), "Offensiver Kampfstil")
            # gegenseitig ersetzen
            effects = [e for e in effects if not is_volle_kampfhaltung(e)]
            effects.append(make_volle_offensive_effect(has_ok))
        elif key == "volle_defensive":
            has_dk = _has_named_vorteil(self._player_vorteil_names(), "Defensiver Kampfstil")
            effects = [e for e in effects if not is_volle_kampfhaltung(e)]
            effects.append(make_volle_defensive_effect(has_dk))
        elif key == "blutend":
            effects.append(make_blutend_effect(self._char_ws_wert()))
        else:
            effects.append(from_preset(key))
        self._set_effects(effects)
        self._rebuild_effects_ui()
        self._update_effects_mod_label()
        self._sync_atemtechnik_checks()

    def _add_custom_effect(self):
        eff = blank_effect("Neuer Effekt")

        def _done(edited):
            if not edited:
                return
            effects = self._get_effects()
            effects.append(edited)
            self._set_effects(effects)
            self._rebuild_effects_ui()
            self._update_effects_mod_label()

        self._effect_editor_dialog(eff, on_done=_done)

    def _remove_effect(self, eid):
        effects = [e for e in self._get_effects() if e.get("id") != eid]
        self._set_effects(effects)
        self._rebuild_effects_ui()
        self._update_effects_mod_label()

    def _toggle_effect_timer(self, eid):
        effects = self._get_effects()
        for e in effects:
            if e.get("id") == eid:
                e["has_timer"] = not e.get("has_timer")
                break
        self._set_effects(effects)
        self._rebuild_effects_ui()

    def _on_effect_duration(self, eid, val):
        if self.currentlyLoading:
            return
        effects = self._get_effects()
        for e in effects:
            if e.get("id") == eid:
                e["duration"] = int(val)
                break
        self._set_effects(effects)

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
                    self._update_effects_mod_label()

                self._effect_editor_dialog(e, on_done=_done)
                break

    def _show_effect_info(self, eid):
        effects = self._get_effects()
        eff = next((e for e in effects if e.get("id") == eid), None)
        if not eff:
            return
        dlg = QDialog(self.form)
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
        def do_roll():
            s = roll_ed.text().strip()
            if not s:
                return
            # simple W-dice
            import re as _re
            m = _re.search(r"(\d*)[wWdD](\d+)", s)
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
        box.rejected.connect(dlg.close)
        box.accepted.connect(dlg.close)
        lay.addWidget(box)
        dlg.setModal(False)
        dlg.setWindowModality(Qt.WindowModality.NonModal)
        dlg.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()
        if not hasattr(self, "_info_boxes"):
            self._info_boxes = []
        self._info_boxes.append(dlg)

    def _player_weapon_names(self):
        names = []
        try:
            for w in getattr(Wolke.Char, "waffen", []) or []:
                n = getattr(w, "anzeigename", None) or getattr(w, "name", None) or ""
                if n:
                    names.append(str(n))
        except Exception:
            pass
        return names

    def _probe_selector_dialog(self, current_type="attr", current_name="KO"):
        """Suchdialog: Attribut / Fertigkeit / Talent mit aktuellem PW."""
        dlg = QDialog(self.form)
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
            entries = collect_player_probe_entries(getattr(Wolke, "Char", None), getattr(Wolke, "DB", None))
        except Exception:
            entries = collect_player_probe_entries(None, None)

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

    def _effect_editor_dialog(self, eff, on_done=None):
        """
        Effekt-Editor. on_done(result|None) → nicht-modal (Sephrasto bleibt bedienbar).
        Ohne on_done: klassisches exec() (Rückgabewert).
        """
        dlg = QDialog(self.form)
        dlg.setWindowTitle("Effekt bearbeiten")
        toggle_w, full_h = 36, 800
        try:
            screen = dlg.screen() or QApplication.primaryScreen()
            if screen is not None:
                geo = screen.availableGeometry()
                full_h = max(560, geo.height() - 60)
                # möglichst volle Breite nutzen, Seiten 1:1
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
        # Normale Fensterflags – kein WindowStaysOnTopHint
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

        # --- Allgemein ---
        g_all = QGroupBox("Allgemein")
        f_all = QFormLayout(g_all)
        name_ed = QLineEdit(eff.get("name") or "")
        f_all.addRow("Name:", name_ed)
        info_ed = QPlainTextEdit(eff.get("info_text") or "")
        info_ed.setMaximumHeight(70)
        info_ed.setPlaceholderText("Beschreibung / Giftwirkung / Hinweistext…")
        f_all.addRow("Info-Text:", info_ed)
        roll_ed = QLineEdit(eff.get("info_roll") or "")
        roll_ed.setPlaceholderText("optional, z. B. 1W6 oder KO")
        f_all.addRow("Info-Wurf:", roll_ed)
        focus_ed = QLineEdit(eff.get("focus") or "")
        focus_ed.setPlaceholderText("z. B. Zauber X laden, Falle entschärfen…")
        f_all.addRow("Gegenstand:", focus_ed)
        form.addWidget(g_all)

        # --- Timer / Ladungen ---
        g_tim = QGroupBox("Timer / Ladungen")
        f_tim = QFormLayout(g_tim)
        timer_cb = QCheckBox("Timer / Ladungen aktiv")
        timer_cb.setChecked(bool(eff.get("has_timer")))
        dur_spin = QSpinBox()
        dur_spin.setRange(0, 999)
        dur_spin.setValue(int(eff.get("duration", 0) or 0))
        f_tim.addRow(timer_cb, dur_spin)
        tick_combo = QComboBox()
        tick_combo.addItem("Jede Runde (− Runde / eigene INI)", "runde")
        tick_combo.addItem("Bei erfolgreicher AT", "at_erfolg")
        tick_combo.addItem("Bei TP mit verknüpfter Waffe", "tp_waffe")
        mode = eff.get("tick_mode") or "runde"
        idx = max(0, tick_combo.findData(mode))
        tick_combo.setCurrentIndex(idx)
        f_tim.addRow("Tick-Modus:", tick_combo)
        notify_spin = QSpinBox()
        notify_spin.setRange(0, 99)
        notify_spin.setValue(int(eff.get("notify_at", 0) or 0))
        notify_spin.setToolTip("0 = aus; Hinweis wenn Dauer/Ladungen ≤ diesem Wert")
        f_tim.addRow("Hinweis bei Dauer ≤", notify_spin)
        form.addWidget(g_tim)

        # --- Waffengift ---
        g_gift = QGroupBox("Waffengift")
        f_gift = QFormLayout(g_gift)
        gift_cb = QCheckBox("Ist Waffengift (Ladung bei TP der Waffe)")
        gift_cb.setChecked(bool(eff.get("is_waffengift")))
        f_gift.addRow(gift_cb)
        wpn_combo = QComboBox()
        wpn_combo.setEditable(True)
        wpn_combo.addItem("— keine —", "")
        for wn in self._player_weapon_names():
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
            if gift_cb.isChecked():
                if tick_combo.currentData() == "runde":
                    tick_combo.setCurrentIndex(tick_combo.findData("tp_waffe"))
        gift_cb.toggled.connect(_sync_gift)

        # --- Modifikatoren ---
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
        # ein Feld: fest oder Würfel (z. B. +3, 1W6, 2W6+1)
        tp_legacy = int(mods.get("tp", 0) or 0)
        tp_init = (eff.get("tp_dice") or "").strip()
        if not tp_init and tp_legacy:
            tp_init = f"{tp_legacy:+d}"
        tp_dice_ed = QLineEdit(tp_init)
        tp_dice_ed.setPlaceholderText("z. B. +3, 1W6 oder 2W6+1 (nach Hammerschlag)")
        f_mod.addRow("TP:", tp_dice_ed)
        wsch_ed = QLineEdit(eff.get("waffenschaden") or "")
        wsch_ed.setPlaceholderText("z. B. +2, 1W6 (vor Hammerschlag auf den Waffenwurf)")
        f_mod.addRow("Waffenschaden:", wsch_ed)
        flucht_cb = QCheckBox("Nur Flucht")
        flucht_cb.setChecked(bool((eff.get("flags") or {}).get("flucht")))
        rueck_cb = QCheckBox("Rückzug wenn möglich")
        rueck_cb.setChecked(bool((eff.get("flags") or {}).get("rueckzug")))
        flag_row = QHBoxLayout()
        flag_row.addWidget(flucht_cb)
        flag_row.addWidget(rueck_cb)
        f_mod.addRow(flag_row)
        form.addWidget(g_mod)
        form.addStretch()

        def _make_probe_picker(initial_type, initial_name, initial_val, parent_form):
            """Zeile: [Probe-Button] [Gegen Wert]. Button öffnet Suchdialog."""
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
                pw = ""
                try:
                    entries = collect_player_probe_entries(
                        getattr(Wolke, "Char", None), getattr(Wolke, "DB", None)
                    )
                    val = resolve_probe_pw(entries, state["type"], state["name"], 0)
                    if val:
                        pw = f"  (PW {val})"
                except Exception:
                    pass
                kind = {"attr": "Attr", "fertigkeit": "Fert", "talent": "Tal"}.get(state["type"], "?")
                return f"{kind}: {state['name']}{pw}"

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

        # --- Zwischen-Effekt ---
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
        mid_fail_wounds.setToolTip("0 = keine automatische Einschränkung, nur Text + optionale Taste")
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

        # --- Bei Ablauf ---
        g_end = QGroupBox("Bei Ablauf / letzter Ladung")
        f_end = QFormLayout(g_end)
        end_combo = QComboBox()
        end_combo.addItem("Nur entfernen", None)
        end_combo.addItem("1 Erschöpfung (/)", "erschöpfung")
        end_combo.addItem("Einschränkung(en)", "wunde")
        end_combo.addItem("Probe fordern", "probe")
        end_combo.addItem("Hinweis-Popup", "notify")
        on_end = eff.get("on_end")
        ei = end_combo.findData(on_end)
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

        # --- Vorzeitig Timer auf 0 ---
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
        pre_hint.setPlaceholderText("Abbruch-Text, z. B. Konzentration unterbrochen…")
        f_pre.addRow("Abbruch-Text:", pre_hint)
        pre_note = QLabel(
            "Zählt nur +Modal / Effekt-Quellen (eine Quelle = ein Schlag). "
            "Bei Auslösen: Timer → 0 (kein normales on_end außer explizit)."
        )
        pre_note.setWordWrap(True)
        pre_note.setStyleSheet("color:#666; font-size: 11px;")
        f_pre.addRow(pre_note)

        # --- Bei Bedingung Info-Text ---
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
            "Timer bleibt. Es erscheint der Info-Text (wie die i-Taste) – "
            "z. B. Konzentrations-Störung / Willenskraft-Probe."
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

        # Experten-Panel (rechts, wie Buchseite)
        expert_scroll = QScrollArea()
        expert_scroll.setWidgetResizable(True)
        expert_body = QWidget()
        expert_form = QVBoxLayout(expert_body)
        expert_title = QLabel("<b>Expertenmodus</b>")
        expert_form.addWidget(expert_title)
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
        toggle_bar._toggle_filter = _tf  # ref halten

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
            # Konzentration: Ablauf-Text mit Gegenstand füllen
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
            box.accepted.disconnect()
            box.accepted.connect(accept_and_close)
            box.rejected.connect(reject)
            dlg.finished.connect(lambda code: None)
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
        parts = []
        for k, lab in [("proben", "Proben"), ("at", "AT"), ("vt", "VT"), ("tp", "TP"), ("gs", "GS"), ("rs", "RS")]:
            if mods.get(k):
                parts.append(f"{lab} {mods[k]:+d}")
        if parts:
            self.effectsModLabel.setText("Effekte: " + " · ".join(parts))
            self.effectsModLabel.show()
        else:
            self.effectsModLabel.hide()

    def get_effect_mods(self):
        return sum_mods(self._get_effects())

    def add_erschopfung(self):
        """Fügt eine Erschöpfung (/) hinzu."""
        wunden = list(getattr(Wolke.Char, "dicePlugin_wunden", [None] * 8))
        while len(wunden) < 8:
            wunden.append(None)
        for i in range(8):
            if wunden[i] is None:
                wunden[i] = "/"
                break
        rank = {None: 0, "/": 1, "I": 2, "II": 3, "III": 4, "IV": 5, "X": 6}
        wunden.sort(key=lambda x: rank.get(x, 0), reverse=True)
        Wolke.Char.dicePlugin_wunden = wunden
        self.load_einschraenkungen()
        self.modified.emit()
        self._apply_premature_from_source(1, 0, source_id=f"effect:ersch:{new_id()}")

    def remove_erschopfung(self, count=1):
        """Entfernt bis zu count Erschöpfungen (/)."""
        count = max(1, int(count or 1))
        wunden = list(getattr(Wolke.Char, "dicePlugin_wunden", [None] * 8))
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
        Wolke.Char.dicePlugin_wunden = wunden
        self.load_einschraenkungen()
        self.modified.emit()
        return removed

    def remove_wunde(self, count=1):
        """Entfernt bis zu count Wunden (X bzw. höchste Koloss-Stufe)."""
        count = max(1, int(count or 1))
        mode = int(getattr(Wolke.Char, "dicePlugin_wunden_modus", 0) or 0)
        wunden = list(getattr(Wolke.Char, "dicePlugin_wunden", [None] * 8))
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
                # höchste Stufe zuerst abbauen
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
        Wolke.Char.dicePlugin_wunden = wunden
        self.load_einschraenkungen()
        self.modified.emit()
        return removed

    def add_wunde(self, count=1):
        """
        Fügt count Wunden hinzu.
        Normal: X. Koloss I: Kratzer I→II. Koloss II: I→II→III→IV.
        Erschöpfung (/) wird nie überschrieben – neues Feld.
        """
        count = max(1, min(8, int(count or 1)))
        mode = int(getattr(Wolke.Char, "dicePlugin_wunden_modus", 0) or 0)
        wunden = list(getattr(Wolke.Char, "dicePlugin_wunden", [None] * 8))
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
            # Koloss: Kratzer-Stufen, Erschöpfung überspringen
            if mode == 1:
                ladder = ["I", "II"]
            else:
                ladder = ["I", "II", "III", "IV"]
            # bestehende Kratzer upgraden (nie /)
            for step_i, cur in enumerate(ladder[:-1]):
                nxt = ladder[step_i + 1]
                for i in range(8):
                    if wunden[i] == cur:
                        wunden[i] = nxt
                        return
            # neues Feld mit I
            for i in range(8):
                if wunden[i] is None:
                    wunden[i] = "I"
                    return

        for _ in range(count):
            _one()

        rank = {None: 0, "/": 1, "I": 2, "II": 3, "III": 4, "IV": 5, "X": 6}
        wunden.sort(key=lambda x: rank.get(x, 0), reverse=True)
        Wolke.Char.dicePlugin_wunden = wunden
        self.load_einschraenkungen()
        self.modified.emit()
        # Effekt-Quellen zählen als ein Schlag
        self._apply_premature_from_source(0, count, source_id=f"effect:wunde:{new_id()}")

    def _resolve_player_probe_pw(self, ptype, pname):
        try:
            entries = collect_player_probe_entries(
                getattr(Wolke, "Char", None), getattr(Wolke, "DB", None)
            )
            return resolve_probe_pw(entries, ptype, pname, 0)
        except Exception:
            return 0

    def _show_probe_event_dialog(self, ev, resolve_pw, add_wunde_fn):
        """Probe-Popup: Info, Würfeln, Gelingen/Misslingen, optional +Wunde."""
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
                return int(self.get_wound_penalty() or 0)
            except Exception:
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

        parent = self.form if hasattr(self, "form") else self
        dlg = QDialog(parent)
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

        state = {"done": False}

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
            state["done"] = True

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
                    ev, self._resolve_player_probe_pw, self.add_wunde
                )
            elif t == "notify":
                self._show_top_info(ename, ev.get("message") or "")
            elif t == "removed":
                if ev.get("message"):
                    self._show_top_info(ename, ev.get("message"))

    def decrement_effects(self):
        effects = self._get_effects()
        new_list, events = tick_effects(effects)
        self._set_effects(new_list)
        self._rebuild_effects_ui()
        self._update_effects_mod_label()
        self.reset_reaktionen()
        self._handle_effect_events(events)
        self._refresh_aktionen_checkboxes()

    def _refresh_aktionen_checkboxes(self):
        """Haekchen aller Roller an aktuelle Aktions-Effekte anpassen."""
        off_on = self._has_active_volle("off")
        def_on = self._has_active_volle("def")
        atem_on = self._has_active_atemtechnik()
        self._aktionen_busy = True
        try:
            for r in self._all_dice_rollers():
                off_cb = r.get("volle_off_check")
                def_cb = r.get("volle_def_check")
                atem_cb = r.get("atemtechnik_check")
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
            self._aktionen_busy = False

    def _on_reaktion_changed(self, val):
        Wolke.Char.dicePlugin_reaktionen = int(val)
        self._update_reaktion_label()

    def _update_reaktion_label(self):
        if not hasattr(self, "reaktion_malus_label") or self.reaktion_malus_label is None:
            return
        n = int(getattr(Wolke.Char, "dicePlugin_reaktionen", 0) or 0)
        malus = -4 * n
        if malus == 0:
            self.reaktion_malus_label.setText("VT ±0")
            self.reaktion_malus_label.setStyleSheet("color: #666; min-width: 42px;")
        else:
            self.reaktion_malus_label.setText(f"VT {malus}")
            self.reaktion_malus_label.setStyleSheet(
                "color: #a12323; font-weight: bold; min-width: 42px;"
            )

    def get_reaktion_malus(self):
        return -4 * int(getattr(Wolke.Char, "dicePlugin_reaktionen", 0) or 0)

    def increment_reaktion(self):
        n = int(getattr(Wolke.Char, "dicePlugin_reaktionen", 0) or 0) + 1
        Wolke.Char.dicePlugin_reaktionen = n
        if hasattr(self, "reaktion_spin") and self.reaktion_spin is not None:
            self.reaktion_spin.blockSignals(True)
            self.reaktion_spin.setValue(n)
            self.reaktion_spin.blockSignals(False)
        self._update_reaktion_label()

    def reset_reaktionen(self):
        Wolke.Char.dicePlugin_reaktionen = 0
        if hasattr(self, "reaktion_spin") and self.reaktion_spin is not None:
            self.reaktion_spin.blockSignals(True)
            self.reaktion_spin.setValue(0)
            self.reaktion_spin.blockSignals(False)
        self._update_reaktion_label()


    def _char_ko_pw(self) -> int:
        try:
            return int(Wolke.Char.attribute["KO"].probenwert)
        except Exception:
            return 0

    def _char_zaehigkeit_pw(self) -> int:
        """PW(T) nur wenn Talent Zähigkeit gekauft, sonst PW Selbstbeherrschung."""
        try:
            fert = Wolke.Char.fertigkeiten.get("Selbstbeherrschung")
            if fert is None:
                return 0
            pw = int(getattr(fert, "probenwert", 0) or 0)
            pwt = int(getattr(fert, "probenwertTalent", 0) or 0)
            gekauft = getattr(fert, "gekaufteTalente", None) or set()
            if isinstance(gekauft, dict):
                names = set(gekauft.keys())
            else:
                names = set(gekauft)
            # global talente set fallback
            for n in (getattr(Wolke.Char, "talente", None) or set()):
                names.add(n)
            has_z = any(
                str(n).lower() in ("zähigkeit", "zahigkeit") or "zähigkeit" in str(n).lower()
                for n in names
            )
            if has_z:
                return pwt
            return pw
        except Exception:
            return 0

    def _char_ws_wert(self) -> int:
        """Wundschwelle WS (nicht WS*)."""
        try:
            ab = getattr(Wolke.Char, "abgeleiteteWerte", None) or {}
            ws = ab.get("WS")
            if ws is not None:
                return max(1, int(getattr(ws, "wert", None) or getattr(ws, "finalwert", None) or 4))
        except Exception:
            pass
        return 4

    def _show_wunden_info_dialog(self):
        dlg = QDialog(self.form)
        dlg.setWindowTitle("Wundregeln & Proben")
        dlg.setMinimumSize(1000, 640)
        dlg.resize(1100, 720)
        root = QHBoxLayout(dlg)

        # --- Links: Stichpunkte ---
        left = QTextBrowser()
        left.setOpenExternalLinks(False)
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
<li>Optional: <b>Zähigkeits-Probe (12, I)</b> gegen den Wundabzug</li>
<li>Misslingen → +1 Erschöpfung und trotzdem kampfunfähig</li>
<li>Endet nach ca. 1 Stunde oder wenn eine Einschränkung geheilt wurde (ohne schädliche Effekte)</li>
</ul>
<h3>Blutungen und Tod</h3>
<ul>
<li>Blutung bei Kampfunfähigkeit durch Waffengewalt o.Ä. oder weitere Verletzung im kampfunfähigen Zustand</li>
<li>Dann: <b>KO-Probe (12, I)</b> – Misslingen → Blutung beginnt</li>
<li>Bei Blutung: alle WS Initiativephasen erneut KO-Probe (12, I); Misslingen → +1 Wunde</li>
<li>Blutung endet bei erfolgreicher Erster Hilfe</li>
<li>Bei 8 Einschränkungen ist die Grenze erreicht; eine weitere = Tod</li>
</ul>
<h3>Regeneration</h3>
<ul>
<li>Ruhe/Schlaf und keine schädlichen Effekte</li>
<li>1 Wunde pro durchschlafener Nacht (≥6 h) oder 1 Erschöpfung pro Stunde</li>
</ul>
<h3>Heilkunde</h3>
<ul>
<li><b>Erste Hilfe</b>: Blutung stoppen / Gift & Krankheit mildern; mind. 4 INI Konzentration</li>
<li><b>Heilungsfördernde Maßnahmen</b>: 1 Wunde sofort, 1×/Tag, Probe 16+Wundmod.</li>
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

        # --- Rechts: Proben ---
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setSpacing(10)

        def _probe_box(title, pw, target, extra_widget=None):
            box = QGroupBox(title)
            lay = QVBoxLayout(box)
            info = QLabel(f"PW {pw} → Ziel {target} (1W20+PW+Mod −Wunden ±Effekte ≥ Ziel)")
            info.setWordWrap(True)
            lay.addWidget(info)
            if extra_widget is not None:
                lay.addWidget(extra_widget)
            row = QHBoxLayout()
            btn = QPushButton("Würfeln")
            res = QLabel("–")
            res.setWordWrap(True)
            row.addWidget(btn)
            row.addWidget(res, 1)
            lay.addLayout(row)
            return box, btn, res

        # Wundschmerz
        extra_w = QWidget()
        ew = QHBoxLayout(extra_w)
        ew.setContentsMargins(0, 0, 0, 0)
        ew.addWidget(QLabel("Zus. ab 3. Einschränkung (−4 je):"))
        spin_extra = QSpinBox()
        spin_extra.setRange(0, 6)
        spin_extra.setValue(0)
        spin_extra.setToolTip("Anzahl Einschränkungen ab der dritten in diesem Schlag")
        ew.addWidget(spin_extra)
        ew.addStretch()
        ko_pw = self._char_ko_pw()
        box1, btn1, res1 = _probe_box("Wundschmerz – KO-Probe (20, I)", ko_pw, 20, extra_w)
        btn_fail1 = QPushButton(
            "Misslingen → betäubt (Handlungsunfähig, 1 Runde)"
        )
        btn_fail1.setToolTip(
            "Effekt Handlungsunfähig: blockiert Proben bis −Runde"
        )
        box1.layout().addWidget(btn_fail1)
        rv.addWidget(box1)

        # Kampfunfahigkeit
        z_pw = self._char_zaehigkeit_pw()
        box2, btn2, res2 = _probe_box("Kampfunfähigkeit – Zähigkeits-Probe (12, I)", z_pw, 12)
        btn_fail2 = QPushButton("Misslingen → +1 Erschöpfung und kampfunfähig")
        box2.layout().addWidget(btn_fail2)
        rv.addWidget(box2)

        # Blutung
        box3, btn3, res3 = _probe_box("Blutungen und Tod – KO-Probe (12, I)", ko_pw, 12)
        btn_fail3 = QPushButton("Misslingen → Blutung beginnt")
        box3.layout().addWidget(btn_fail3)
        rv.addWidget(box3)

        # Durchatmen – 3W20 Median Zähigkeit (16)
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

        def _roll(pw, target, extra_mod, res_label, *, median3=False):
            wound = int(self.get_wound_penalty() or 0)
            emods = self.get_effect_mods() or {}
            eff_mod = int(emods.get("proben", 0) or 0)
            if median3:
                rolls = sorted([random.randint(1, 20) for _ in range(3)])
                die = rolls[1]
                die_html = (
                    f"[{rolls[0]}, <b>{rolls[1]}</b>, {rolls[2]}]"
                )
                parts = [f"3W20 {die_html} + PW {pw}"]
            else:
                die = random.randint(1, 20)
                die_html = f"<b style='color:#2a7a2a'>{die}</b>" if die == 20 else (
                    f"<b style='color:#a12323'>{die}</b>" if die == 1 else str(die)
                )
                parts = [f"1W20 ({die_html}) + PW {pw}"]
            total = int(pw) + die + int(extra_mod) - wound + eff_mod
            ok = total >= int(target)
            color = "#2a7a2a" if ok else "#a12323"
            verdict = "Erfolg" if ok else "Misserfolg"
            if extra_mod:
                parts.append(f"{extra_mod:+d} (Mod)")
            if wound:
                parts.append(f"-{wound} (Wunden)")
            if eff_mod:
                parts.append(f"{eff_mod:+d} (Effekte)")
            res_label.setText(
                " ".join(parts) + f" = <b>{total}</b> gegen {target} → "
                f"<b style='color:{color}'>{verdict}</b>"
            )
            return ok, total

        def roll_w():
            mod = -4 * int(spin_extra.value())
            _roll(ko_pw, 20, mod, res1)

        def roll_z():
            _roll(z_pw, 12, 0, res2)

        def roll_b():
            _roll(ko_pw, 12, 0, res3)

        def roll_durchatmen():
            _roll(z_pw, 16, 0, res4, median3=True)

        def heal_wunde():
            n = self.remove_wunde(1)
            if n:
                self._show_top_info("Durchatmen", "1 Wunde regeneriert.")
            else:
                self._show_top_info("Durchatmen", "Keine Wunde zum Regenerieren vorhanden.")

        def heal_ersch():
            n = self.remove_erschopfung(2)
            if n:
                self._show_top_info("Durchatmen", f"{n} Erschöpfung regeneriert.")
            else:
                self._show_top_info("Durchatmen", "Keine Erschöpfung zum Regenerieren vorhanden.")

        btn1.clicked.connect(roll_w)
        btn2.clicked.connect(roll_z)
        btn3.clicked.connect(roll_b)
        btn4.clicked.connect(roll_durchatmen)
        btn_heal_w.clicked.connect(heal_wunde)
        btn_heal_e.clicked.connect(heal_ersch)

        def fail_w():
            effects = self._get_effects()
            effects = [e for e in effects if "handlungsunfähig" not in (e.get("name") or "").lower()]
            effects.append(make_handlungsunfaehig_effect(1))
            self._set_effects(effects)
            self._rebuild_effects_ui()
            self._update_effects_mod_label()
            self._show_top_info("Handlungsunfähig", "Betäubt – keine Proben bis −Runde.")

        def fail_z():
            self.add_erschopfung()
            self._show_top_info("Kampfunfähig", "+1 Erschöpfung – Charakter ist kampfunfähig.")

        def fail_b():
            effects = self._get_effects()
            if not any((e.get("name") or "").lower().startswith("blutend") for e in effects):
                effects.append(make_blutend_effect(self._char_ws_wert()))
                self._set_effects(effects)
                self._rebuild_effects_ui()
            ws = self._char_ws_wert()
            self._show_top_info(
                "Blutend",
                f"Blutung hat begonnen – alle {ws} WS-Runden: erneut KO-Probe (12, I); Misslingen → +1 Wunde",
            )

        btn_fail1.clicked.connect(fail_w)
        btn_fail2.clicked.connect(fail_z)
        btn_fail3.clicked.connect(fail_b)

        root.addWidget(right, 1)
        dlg.setModal(False)
        dlg.show()

    def ensure_atemtechnik_effect(self):
        """Legt Atemtechnik-Effekt an, falls noch nicht vorhanden."""
        ko = 0
        try:
            ko = int(Wolke.Char.attribute["KO"].wert)
        except Exception:
            ko = 0
        effects = self._get_effects()
        for e in effects:
            if (e.get("name") or "").lower().startswith("atemtechnik"):
                return  # schon da
        effects.append(make_atemtechnik_effect(ko))
        self._set_effects(effects)
        self._rebuild_effects_ui()

    def _apply_atemtechnik_from_checkbox(self, on: bool):
        """Effekt sofort anlegen/entfernen - analog zu Volle Offensive/Defensive."""
        if getattr(self, "_aktionen_busy", False):
            return
        self._aktionen_busy = True
        try:
            effects = [
                e for e in self._get_effects()
                if not (e.get("name") or "").lower().startswith("atemtechnik")
            ]
            if on:
                ko = 0
                try:
                    ko = int(Wolke.Char.attribute["KO"].wert)
                except Exception:
                    ko = 1
                effects.append(make_atemtechnik_effect(ko))
            self._set_effects(effects)
            self._rebuild_effects_ui()
            self._update_effects_mod_label()
            for r in self._all_dice_rollers():
                cb = r.get("atemtechnik_check")
                if cb is not None:
                    cb.blockSignals(True)
                    cb.setChecked(bool(on))
                    cb.blockSignals(False)
        finally:
            self._aktionen_busy = False

    def _on_atemtechnik_toggled(self, checked):
        self._apply_atemtechnik_from_checkbox(bool(checked))

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
        """kind=None: beide; 'off' / 'def' nur eine Seite. Kein Würfel-Refresh (sonst Haken-Chaos)."""
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
        self._update_effects_mod_label()

    def _all_dice_rollers(self):
        return [
            r for r in (
                getattr(self, "attr_dice_roller", None),
                getattr(self, "skill_dice_roller", None),
                getattr(self, "supernatural_dice_roller", None),
                getattr(self, "kampf_dice_roller", None),
                getattr(self, "active_dice_roller", None),
            ) if r
        ]

    def _set_zweite_einfache_checks(self, on: bool):
        """Modifikator „Zweite einfache Aktion (−4 AT)“ in allen Rollern setzen/lösen."""
        for r in self._all_dice_rollers():
            cb = r.get("zweite_einfache_check")
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

    def _apply_volle_from_checkbox(self, kind: str, on: bool):
        """kind: 'off' | 'def'. Guard gegen rekursive Signal-Schleifen."""
        if getattr(self, "_aktionen_busy", False):
            return
        self._aktionen_busy = True
        try:
            effects = [e for e in self._get_effects() if not is_volle_kampfhaltung(e)]
            if on:
                if kind == "off":
                    has_ok = _has_named_vorteil(self._player_vorteil_names(), "Offensiver Kampfstil")
                    effects.append(make_volle_offensive_effect(has_ok))
                else:
                    has_dk = _has_named_vorteil(self._player_vorteil_names(), "Defensiver Kampfstil")
                    effects.append(make_volle_defensive_effect(has_dk))
            self._set_effects(effects)
            self._rebuild_effects_ui()
            self._update_effects_mod_label()
            # Alle Roller-Haken an Zielzustand angleichen
            for r in self._all_dice_rollers():
                off_cb = r.get("volle_off_check")
                def_cb = r.get("volle_def_check")
                if off_cb is not None:
                    off_cb.blockSignals(True)
                    off_cb.setChecked(bool(on and kind == "off"))
                    off_cb.blockSignals(False)
                if def_cb is not None:
                    def_cb.blockSignals(True)
                    def_cb.setChecked(bool(on and kind == "def"))
                    def_cb.blockSignals(False)
            # Volle Defensive → AT als zweite einfache Aktion (−4)
            if kind == "def":
                self._set_zweite_einfache_checks(bool(on))
            # Manöver-Liste neu aufbauen (Sturm/Überrennen je nach Volle Off/Def)
            self._refresh_manöver_after_volle()
        finally:
            self._aktionen_busy = False

    def _refresh_manöver_after_volle(self):
        """Manöver-Grid neu laden, damit Sturmangriff/Überrennen korrekt ein-/ausgeblendet werden."""
        roller = getattr(self, "active_dice_roller", None)
        if not roller or "manöver_box" not in roller:
            return
        try:
            if not roller["manöver_box"].isVisible():
                return
        except RuntimeError:
            return
        name = getattr(self, "current_probe_name", None) or ""
        if name.startswith("AT") or "AT (" in name:
            ptype = "AT"
        elif name.startswith("VT") or "VT (" in name:
            ptype = "VT"
        else:
            return
        self._apply_manöver_availability(roller, probe_type=ptype)
        if self._merken_manöver:
            self._restore_manöver_from_memory(roller)

    def _clear_bewegung_manöver(self):
        """Sturmangriff/Überrennen abwählen bei Volle Offensive/Defensive."""
        self._refresh_manöver_after_volle()

    def _on_volle_offensive_toggled(self, checked):
        self._apply_volle_from_checkbox("off", bool(checked))

    def _on_volle_defensive_toggled(self, checked):
        self._apply_volle_from_checkbox("def", bool(checked))

    def _sync_aktionen_checks(self, roller, *, is_tp=False, is_at=False, is_vt=False):
        """Sichtbarkeit + Zustand der Aktions-Haken im Würfelbereich."""
        if not roller:
            return
        atem = roller.get("atemtechnik_check")
        off_cb = roller.get("volle_off_check")
        def_cb = roller.get("volle_def_check")
        box = roller.get("aktionen_box")
        # VT = Reaktion, TP = Schaden schon deklariert → keine Aktionen
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
        has_atem = self._player_has_vorteil("Atemtechnik") or self._has_active_atemtechnik()
        show_atem = has_atem and is_at
        show_volle = is_at and not self._weapon_is_fernkampf()  # keine VO/VD im Fernkampf
        if atem is not None:
            atem.setVisible(show_atem)
            if show_atem and self._has_active_atemtechnik():
                atem.setChecked(True)
        if off_cb is not None:
            off_cb.blockSignals(True)
            off_cb.setVisible(show_volle)
            if show_volle:
                active = self._has_active_volle("off")
                off_cb.setChecked(active)
                if active and _has_named_vorteil(self._player_vorteil_names(), "Offensiver Kampfstil"):
                    off_cb.setText("Volle Offensive (+4 AT / −4 VT)")
                else:
                    off_cb.setText("Volle Offensive (+4 AT / −8 VT)")
            else:
                off_cb.setChecked(False)
            off_cb.blockSignals(False)
        if def_cb is not None:
            def_cb.blockSignals(True)
            def_cb.setVisible(show_volle)
            if show_volle:
                def_cb.setChecked(self._has_active_volle("def"))
            else:
                def_cb.setChecked(False)
            def_cb.blockSignals(False)
        if box is not None:
            box.setVisible(show_atem or show_volle)

    def _sync_atemtechnik_checks(self):
        """Solange Atemtechnik-Effekt aktiv: Häkchen in AT/TP setzen."""
        active = self._has_active_atemtechnik()
        has_vorteil = self._player_has_vorteil("Atemtechnik")
        for roller in (
            getattr(self, "attr_dice_roller", None),
            getattr(self, "skill_dice_roller", None),
            getattr(self, "supernatural_dice_roller", None),
            getattr(self, "kampf_dice_roller", None),
            getattr(self, "active_dice_roller", None),
        ):
            if not roller or "atemtechnik_check" not in roller:
                continue
            if has_vorteil or active:
                roller["atemtechnik_check"].setVisible(True)
            if active and (has_vorteil or active):
                roller["atemtechnik_check"].setChecked(True)

    def _create_dice_roll_widget(self):
        # Äußerer Rahmen + ScrollArea: bei AT/VT/TP (Manöver, Kampfmod, Waffeneig.)
        # bleibt der rechte Bereich bedienbar und gestaucht nicht alles zusammen.
        widget = QWidget()
        outer_layout = QVBoxLayout(widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        try:
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        except Exception:
            pass

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        label_probe = QLabel("<h3>Probe: -</h3>")
        
        options_box = QGroupBox("Optionen"); options_layout = QVBoxLayout(options_box)
        radio3W20 = QRadioButton("3W20 (mittlerer Wurf)")
        radio1W20 = QRadioButton("1W20")
        radio3W20.setChecked(True)
        options_layout.addWidget(radio3W20)
        options_layout.addWidget(radio1W20)

        # Legacy-Keys (Reichweite in neue NK-Combos integriert)
        reach_malus_check = QCheckBox()
        reach_bonus_check = QCheckBox()
        reach_box = QGroupBox("Kampf-Modifikatoren")
        reach_box.setVisible(False)

        # Manöver – kompaktes Grid (2 Spalten, kein Scroll)
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
        manöver_merken_btn.setToolTip("Aktuelle Manöver-Auswahl merken (bleibt bei Tab-/Charakterwechsel)")
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

        mod_box = QGroupBox("Modifikatoren"); mod_layout = QHBoxLayout(mod_box)
        decrease_mod_btn = QPushButton("-"); label_mod = QLabel("0"); label_mod.setFixedWidth(30); label_mod.setAlignment(Qt.AlignmentFlag.AlignCenter); increase_mod_btn = QPushButton("+")
        mod_layout.addWidget(decrease_mod_btn); mod_layout.addWidget(label_mod); mod_layout.addWidget(increase_mod_btn)
        hammerschlag_check = QCheckBox("Hammerschlag (x2 Waffe)")
        hammerschlag_check.setStyleSheet("margin-left: 10px;")
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

        # Aktionen (keine Manöver): Atemtechnik, Volle Offensive/Defensive
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
        atemtechnik_check.toggled.connect(self._on_atemtechnik_toggled)
        volle_off_check.toggled.connect(self._on_volle_offensive_toggled)
        volle_def_check.toggled.connect(self._on_volle_defensive_toggled)
        
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

        munition_box = QGroupBox("Munition")
        munition_outer = QVBoxLayout(munition_box)
        munition_outer.setContentsMargins(4, 4, 4, 4)
        munition_host = QWidget()
        munition_host_l = QVBoxLayout(munition_host)
        munition_host_l.setContentsMargins(0, 0, 0, 0)
        munition_outer.addWidget(munition_host)
        munition_box.setVisible(False)

        # --- Kampf-Modifikatoren NK / FK (Tabellen) ---
        kampfmod_box = QGroupBox("Kampf-Modifikatoren")
        kampfmod_outer = QVBoxLayout(kampfmod_box)
        kampfmod_outer.setContentsMargins(4, 4, 4, 4)
        kampfmod_outer.setSpacing(4)

        def _fill_combo(items):
            cb = QComboBox()
            for text, val in items:
                cb.addItem(text, val)
            cb.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            return cb

        # NK-Panel
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

        # FK-Panel
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
        kampfmod_merken_btn.setToolTip("Aktuelle Kampf-Modifikatoren merken (bleibt bei Tab-/Charakterwechsel)")
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
        reaktion_btn = QPushButton("Reaktion würfeln")
        reaktion_btn.setToolTip(
            "Reaktion (z. B. Passierschlag): –4 je bereits verbrauchter Reaktion, "
            "Zähler danach +1."
        )
        reaktion_btn.setVisible(False)
        free_reaktion_btn = QPushButton("Freie Reaktion")
        free_reaktion_btn.setToolTip(
            "Freie Reaktion: kein Reaktionsmalus, Zähler unverändert."
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
        label_result = QLabel("Ergebnis: "); label_result.setWordWrap(True)

        # Triumph / Patzer (nur Hinweistext)
        triumph_wrap = QWidget()
        triumph_layout = QHBoxLayout(triumph_wrap)
        triumph_layout.setContentsMargins(0, 2, 0, 2)
        triumph_label = QLabel("")
        triumph_label.setWordWrap(True)
        triumph_layout.addWidget(triumph_label, 1)
        triumph_wrap.setVisible(False)

        layout.addWidget(label_probe)
        layout.addWidget(options_box)
        layout.addWidget(manöver_box)
        layout.addWidget(aktionen_box)
        layout.addWidget(mod_box)
        layout.addWidget(präzision_label)
        layout.addLayout(auflaufen_row)
        layout.addLayout(roll_btn_row)
        layout.addWidget(continue_btn)
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
        waffeig_body = QLabel("")
        waffeig_body.setWordWrap(True)
        waffeig_body.setTextFormat(Qt.TextFormat.RichText)
        waffeig_body.setStyleSheet("color:#333; padding:2px 4px 4px 12px;")
        waffeig_body.setVisible(False)
        # keine Höhenbegrenzung – äußerer Scroll zeigt alle Eigenschaften
        def _toggle_waffeig(on, body=waffeig_body, btn=waffeig_toggle):
            body.setVisible(bool(on))
            btn.setText(("▾" if on else "▸") + " Waffeneigenschaften")
        waffeig_toggle.toggled.connect(_toggle_waffeig)
        waffeig_v.addWidget(waffeig_toggle)
        waffeig_v.addWidget(waffeig_body)
        waffeig_wrap.setVisible(False)

        layout.addWidget(label_result)
        layout.addWidget(triumph_wrap)
        layout.addWidget(munition_box)
        layout.addWidget(kampfmod_box)
        layout.addWidget(waffeig_wrap)
        layout.addStretch()

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)
        widget.setEnabled(False)

        return {
            "widget": widget, "label_probe": label_probe, "radio1W20": radio1W20, 
            "radio3W20": radio3W20, "options_box": options_box,
            "label_mod": label_mod, "label_result": label_result, 
            "increase_btn": increase_mod_btn, "decrease_btn": decrease_mod_btn,
            "execute_btn": execute_roll_btn,
            "reaktion_btn": reaktion_btn,
            "free_reaktion_btn": free_reaktion_btn,
            "continue_btn": continue_btn,
            "triumph_wrap": triumph_wrap,
            "triumph_label": triumph_label,
            "manöver_merken_btn": manöver_merken_btn,
            "manöver_reset_btn": manöver_reset_btn,
            "kampfmod_merken_btn": kampfmod_merken_btn,
            "kampfmod_reset_btn": kampfmod_reset_btn,
            "reach_box": reach_box,
            "reach_malus": reach_malus_check, "reach_bonus": reach_bonus_check,
            "manöver_box": manöver_box,
            "manöver_layout": manöver_layout,
            "manöver_inner": manöver_inner,
            "manöver_widgets": {},
            "manöver_wuchtschlag": manöver_wuchtschlag,
            "manöver_wuchtschlag_spin": manöver_wuchtschlag_spin,
            "manöver_hammerschlag": manöver_hammerschlag,
            "manöver_todesstoß": manöver_todesstoß,
            "manöver_rüstungsbrecher": manöver_rüstungsbrecher,
            "atemtechnik_check": atemtechnik_check,
            "hammerschlag_check": hammerschlag_check,
            "zweite_einfache_check": zweite_einfache_check,
            "waffeig_box": waffeig_wrap,
            "waffeig_toggle": waffeig_toggle,
            "waffeig_body": waffeig_body,
            "aktionen_box": aktionen_box,
            "volle_off_check": volle_off_check,
            "volle_def_check": volle_def_check,
            "präzision_label": präzision_label,
            "auflaufen_gs_label": auflaufen_gs_label,
            "auflaufen_gs_spin": auflaufen_gs_spin,
            "kampfmod_box": kampfmod_box,
            "munition_box": munition_box,
            "munition_host": munition_host,
            "nk_panel": nk_panel,
            "fk_panel": fk_panel,
            "nk_combos": {"position": nk_pos, "reichweite": nk_rw, "untergrund": nk_ug, "dunkelheit": nk_dk},
            "fk_combos": {"groesse": fk_gr, "licht": fk_li, "wind": fk_wi, "bewegung": fk_be, "deckung": fk_de},
            "nk_checks": nk_checks,
            "fk_checks": fk_checks,
        }

    def _create_attribute_tab(self):
        tab = QWidget(); main_layout = QHBoxLayout(tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_widget = QScrollArea(); left_widget.setWidgetResizable(True)
        left_content = QWidget(); left_layout = QVBoxLayout(left_content); left_widget.setWidget(left_content)
        attributes_box = QGroupBox("Attribute"); attributes_layout = QGridLayout(attributes_box)
        self.attribute_buttons.clear(); self.pw_labels.clear()
        for i, attr in enumerate(self.attributes):
            attr_label = QLabel(f"<b>{attr}</b>"); self.pw_labels[attr] = QLabel("0"); button = QPushButton("🎲")
            self.attribute_buttons[attr] = button
            attributes_layout.addWidget(attr_label, i, 0); attributes_layout.addWidget(self.pw_labels[attr], i, 1); attributes_layout.addWidget(button, i, 2)
        attributes_layout.setColumnStretch(3, 1)
        left_layout.addWidget(attributes_box)
        mr_box = QGroupBox("Abgeleitete Werte"); mr_layout = QGridLayout(mr_box)
        mr_label_text = QLabel("<b>MR</b>"); self.mr_label = QLabel("0"); self.mr_button = QPushButton("🎲")
        mr_layout.addWidget(mr_label_text, 0, 0); mr_layout.addWidget(self.mr_label, 0, 1); mr_layout.addWidget(self.mr_button, 0, 2)
        mr_layout.setColumnStretch(3, 1)
        left_layout.addWidget(mr_box); left_layout.addStretch()
        self.attr_dice_roller = self._create_dice_roll_widget()
        splitter.addWidget(left_widget); splitter.addWidget(self.attr_dice_roller["widget"])
        splitter.setSizes([250, 450])
        main_layout.addWidget(splitter)
        return tab

    def _create_skills_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.skills_tree = QTreeWidget()
        self.skills_tree.setAlternatingRowColors(True)
        self.skills_tree.setHeaderLabels(["Fertigkeit", "PW", "PW(T)"])
        header = self.skills_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        fixed_width = Hilfsmethoden.emToPixels(10)
        header.resizeSection(1, fixed_width)
        header.resizeSection(2, fixed_width)
        
        left_layout.addWidget(self.skills_tree)
        
        self.skill_dice_roller = self._create_dice_roll_widget()
        
        splitter.addWidget(left_widget)
        splitter.addWidget(self.skill_dice_roller["widget"])
        splitter.setSizes([450, 250])
        main_layout.addWidget(splitter)
        return tab

    def _create_supernatural_tab(self):
        tab = QWidget()
        main_layout = QVBoxLayout(tab)

        energie_box = QGroupBox("Energien")
        energie_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        energie_layout = QFormLayout(energie_box)
        
        self.asp_layout_widget = QWidget()
        asp_layout = QHBoxLayout(self.asp_layout_widget); asp_layout.setContentsMargins(0,0,0,0)
        asp_layout.addWidget(QLabel("Max:")); self.label_asp_max = QLabel("0"); asp_layout.addWidget(self.label_asp_max)
        asp_layout.addSpacing(20); asp_layout.addWidget(QLabel("Aktuell:")); self.spin_asp_current = QSpinBox()
        self.spin_asp_current.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus); self.spin_asp_current.setMaximumWidth(Hilfsmethoden.emToPixels(8))
        asp_layout.addWidget(self.spin_asp_current); asp_layout.addStretch()
        energie_layout.addRow("Astralenergie (AsP):", self.asp_layout_widget)

        self.kap_layout_widget = QWidget()
        kap_layout = QHBoxLayout(self.kap_layout_widget); kap_layout.setContentsMargins(0,0,0,0)
        kap_layout.addWidget(QLabel("Max:")); self.label_kap_max = QLabel("0"); kap_layout.addWidget(self.label_kap_max)
        kap_layout.addSpacing(20); asp_layout.addWidget(QLabel("Aktuell:")); self.spin_kap_current = QSpinBox()
        self.spin_kap_current.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus); self.spin_kap_current.setMaximumWidth(Hilfsmethoden.emToPixels(8))
        kap_layout.addWidget(self.spin_kap_current); kap_layout.addStretch()
        energie_layout.addRow("Karmaenergie (KaP):", self.kap_layout_widget)
        main_layout.addWidget(energie_box)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.supernatural_tree = QTreeWidget()
        self.supernatural_tree.setAlternatingRowColors(True)
        self.supernatural_tree.setHeaderLabels(["Fertigkeit", "PW"])
        header = self.supernatural_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, Hilfsmethoden.emToPixels(10))
        left_layout.addWidget(self.supernatural_tree)
        
        self.supernatural_dice_roller = self._create_dice_roll_widget()
        
        splitter.addWidget(left_widget)
        splitter.addWidget(self.supernatural_dice_roller["widget"])
        splitter.setSizes([450, 250])
        main_layout.addWidget(splitter)
        return tab

    def _create_ressourcen_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        schips_box = QGroupBox("Schicksalspunkte"); schips_layout = QHBoxLayout(schips_box)
        self.spinSchips = QSpinBox(); self.spinSchips.setRange(0, 20); schips_layout.addWidget(self.spinSchips)
        geld_box = QGroupBox("Geld"); geld_layout = QFormLayout(geld_box)
        self.spinDukaten = QSpinBox(); self.spinDukaten.setRange(0, 99999); geld_layout.addRow("Dukaten:", self.spinDukaten)
        self.spinSilber = QSpinBox(); self.spinSilber.setRange(0, 99999); geld_layout.addRow("Silber:", self.spinSilber)
        self.spinHeller = QSpinBox(); self.spinHeller.setRange(0, 99999); geld_layout.addRow("Heller:", self.spinHeller)
        self.spinKreuzer = QSpinBox(); self.spinKreuzer.setRange(0, 99999); geld_layout.addRow("Kreuzer:", self.spinKreuzer)
        kleidung_box = QGroupBox("Kleidung und Aussehen"); kleidung_layout = QVBoxLayout(kleidung_box)
        self.textKleidung = QPlainTextEdit(); self.textKleidung.setPlaceholderText("Beschreibe hier Kleidung, Rüstung und das generelle Aussehen deines Charakters...")
        kleidung_layout.addWidget(self.textKleidung)
        inventar_splitter = QSplitter(Qt.Orientation.Horizontal)
        left_widget = QWidget(); left_layout = QVBoxLayout(left_widget)
        container_box = QGroupBox("Inventar"); container_box_layout = QVBoxLayout(container_box)
        self.listContainers = QListWidget(); self.listContainers.setToolTip("Doppelklicken zum Umbenennen")
        container_buttons_layout = QHBoxLayout()
        self.buttonAddContainer = QPushButton("Hinzufügen"); self.buttonRemoveContainer = QPushButton("Entfernen")
        container_buttons_layout.addWidget(self.buttonAddContainer); container_buttons_layout.addWidget(self.buttonRemoveContainer)
        container_box_layout.addWidget(self.listContainers); container_box_layout.addLayout(container_buttons_layout)
        left_layout.addWidget(container_box)
        right_widget = QWidget(); right_layout = QVBoxLayout(right_widget)
        self.stackedContainerInhalt = QStackedWidget(); right_layout.addWidget(self.stackedContainerInhalt)
        inventar_splitter.addWidget(left_widget); inventar_splitter.addWidget(right_widget); inventar_splitter.setSizes([200, 400])
        layout.addWidget(schips_box); layout.addWidget(geld_box); layout.addWidget(kleidung_box, stretch=1); layout.addWidget(inventar_splitter, stretch=3)
        return tab
        
    def _create_notizen_tab(self):
        tab = QWidget(); splitter = QSplitter(Qt.Orientation.Horizontal)
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
        self.stackedThemaInhalt = QStackedWidget(); right_layout.addWidget(self.stackedThemaInhalt)
        splitter.addWidget(left_widget); splitter.addWidget(right_widget); splitter.setSizes([200, 400])
        main_layout = QHBoxLayout(tab); main_layout.addWidget(splitter)
        return tab

    def get_wound_penalty(self):
        ignore = False
        wunden_liste = []
        try:
            ignore = bool(getattr(Wolke.Char, "dicePlugin_wunden_ignorieren", False))
            wunden_liste = list(getattr(Wolke.Char, "dicePlugin_wunden", []) or [])
        except Exception:
            wunden_liste = []
        if not wunden_liste and getattr(self, "wunden_buttons", None):
            try:
                wunden_liste = [b.text() or None for b in self.wunden_buttons]
            except Exception:
                pass
        return einschraenkung_malus(wunden_liste, ignore)

    def load_einschraenkungen(self):
        wunden_ignorieren = getattr(Wolke.Char, "dicePlugin_wunden_ignorieren", False)
        self.checkEinschraenkungenIgnorieren.setChecked(wunden_ignorieren)
        mode = int(getattr(Wolke.Char, "dicePlugin_wunden_modus", 0) or 0)
        if hasattr(self, "combo_wunden_modus"):
            self.combo_wunden_modus.blockSignals(True)
            self.combo_wunden_modus.setCurrentIndex(max(0, min(mode, 2)))
            self.combo_wunden_modus.blockSignals(False)
        count = 0
        erschöpfung = 0
        wunden_liste = getattr(Wolke.Char, "dicePlugin_wunden", [None] * 8)
        while len(wunden_liste) < 8:
            wunden_liste.append(None)
        for i, state in enumerate(wunden_liste):
            btn = self.wunden_buttons[i]
            btn.setText("")
            btn.setStyleSheet("")
            if state is None:
                continue
            if state == "/":
                btn.setText("/")
                btn.setStyleSheet("background-color: #236fa1; color: white; font-weight: bold;")
                erschöpfung += 1
            elif state in ("X", "I", "II", "III", "IV"):
                btn.setText(state)
                is_end = (
                    (mode == 0 and state == "X")
                    or (mode == 1 and state == "II")
                    or (mode == 2 and state == "IV")
                )
                if is_end:
                    btn.setStyleSheet("background-color: #a12323; color: white; font-weight: bold;")
                else:
                    btn.setStyleSheet("background-color: #d4a017; color: white; font-weight: bold;")
                count += 1
            else:
                btn.setText(str(state))
                btn.setStyleSheet("background-color: #d4a017; color: white; font-weight: bold;")
                count += 1
        total_malus = count + erschöpfung
        penalty = self.get_wound_penalty()
        if penalty > 0:
            self.wundenPenaltyLabel.setText(f"Abzug: -{penalty} auf alle Proben")
            self.wundenPenaltyLabel.show()
        else:
            self.wundenPenaltyLabel.hide()
        hinweis_parts = [f"Einschränkungen: {total_malus}"]
        if mode == 1:
            hinweis_parts.append("Koloss I")
        elif mode == 2:
            hinweis_parts.append("Koloss II")
        if wunden_ignorieren:
            hinweis_parts.append("(werden ignoriert)")
        else:
            if 4 <= total_malus < 8:
                hinweis_parts.append("Zähigkeitsprobe (I 12) bei jeder weiteren!")
            elif total_malus >= 8:
                hinweis_parts.append("⚠ Nächste = TOD!")
        self.wundenHinweisLabel.setText(" | ".join(hinweis_parts))

    def load_attributes(self):
        for attr in self.attributes:
            if attr in Wolke.Char.attribute: self.pw_labels[attr].setText(str(Wolke.Char.attribute[attr].probenwert))
        if 'MR' in Wolke.Char.abgeleiteteWerte: self.mr_label.setText(str(Wolke.Char.abgeleiteteWerte['MR'].wert))

    def show_talent_info(self, talent_name):
        dialog = TalentInfoDialog(talent_name, self.form)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        if not hasattr(self, "_talent_dialogs"):
            self._talent_dialogs = []
        self._talent_dialogs = [d for d in self._talent_dialogs if d is not None]
        self._talent_dialogs.append(dialog)
        
    def load_skills(self):
        tree = self.skills_tree
        tree.clear()

        kategorien = Wolke.DB.einstellungen["Fertigkeiten: Kategorien profan"].wert.copy()
        fertigkeiten_by_kategorie = SortedCategoryToListDict(kategorien)

        for fert_name, fert_data in Wolke.Char.fertigkeiten.items():
            if fert_name in Wolke.DB.fertigkeiten:
                fert_def = Wolke.DB.fertigkeiten[fert_name]
                fertigkeiten_by_kategorie.append(fert_def.kategorie, fert_name)
        fertigkeiten_by_kategorie.sortValues()

        font_header = QFont(Wolke.Settings["Font"], Wolke.FontHeadingSizeL3)
        font_header.setBold(True)
        font_header.setCapitalization(QFont.Capitalization.SmallCaps)

        for kategorie_name, fert_names_in_kategorie in fertigkeiten_by_kategorie.items():
            if not fert_names_in_kategorie: continue
            
            kategorie_item = QTreeWidgetItem(tree)
            kategorie_item.setText(0, kategorie_name)
            kategorie_item.setFont(0, font_header)
            kategorie_item.setFlags(kategorie_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            
            for fert_name in fert_names_in_kategorie:
                fert_data = Wolke.Char.fertigkeiten[fert_name]
                
                fert_item = QTreeWidgetItem(kategorie_item)
                fert_item.setText(0, fert_name)
                
                pw_button = QPushButton(f"{fert_data.probenwert} 🎲")
                pw_button.clicked.connect(partial(self.prepare_dice_roll, f"{fert_name}_PW"))
                tree.setItemWidget(fert_item, 1, pw_button)

                pwt_button = QPushButton(f"{fert_data.probenwertTalent} 🎲")
                pwt_button.clicked.connect(partial(self.prepare_dice_roll, f"{fert_name}_PWT"))
                tree.setItemWidget(fert_item, 2, pwt_button)
                
                if fert_data.gekaufteTalente:
                    fert_item.setExpanded(False)
                    for talent_name in fert_data.gekaufteTalente:
                        talent_item = QTreeWidgetItem(fert_item)
                        talent_button = QPushButton(f"- {talent_name}")
                        talent_button.setFlat(True)
                        talent_button.setStyleSheet("text-align: left; border: none; background-color: transparent; padding-left: 10px; font-style: italic;")
                        talent_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                        talent_button.clicked.connect(partial(self.show_talent_info, talent_name=talent_name))
                        tree.setItemWidget(talent_item, 0, talent_button)
                        talent_item.setFlags(talent_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            tree.expandItem(kategorie_item)

    def load_supernatural_skills(self):
        tree = self.supernatural_tree
        tree.clear()

        kategorien = Wolke.DB.einstellungen["Fertigkeiten: Kategorien übernatürlich"].wert.copy()
        fertigkeiten_by_kategorie = SortedCategoryToListDict(kategorien)

        if hasattr(Wolke.Char, "übernatürlicheFertigkeiten"):
            for fert_name, fert_data in Wolke.Char.übernatürlicheFertigkeiten.items():
                if fert_data.gekaufteTalente:
                    if fert_name in Wolke.DB.übernatürlicheFertigkeiten:
                        fert_def = Wolke.DB.übernatürlicheFertigkeiten[fert_name]
                        fertigkeiten_by_kategorie.append(fert_def.kategorie, fert_name)
        fertigkeiten_by_kategorie.sortValues()

        font_header = QFont(Wolke.Settings["Font"], Wolke.FontHeadingSizeL3)
        font_header.setBold(True)
        font_header.setCapitalization(QFont.Capitalization.SmallCaps)

        for kategorie_name, fert_names_in_kategorie in fertigkeiten_by_kategorie.items():
            if not fert_names_in_kategorie: continue

            kategorie_item = QTreeWidgetItem(tree)
            kategorie_item.setText(0, kategorie_name)
            kategorie_item.setFont(0, font_header)
            kategorie_item.setFlags(kategorie_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            
            for fert_name in fert_names_in_kategorie:
                fert_data = Wolke.Char.übernatürlicheFertigkeiten[fert_name]
                
                fert_item = QTreeWidgetItem(kategorie_item)
                fert_item.setText(0, fert_name)

                pwt_button = QPushButton(f"{fert_data.probenwertTalent} 🎲")
                pwt_button.clicked.connect(partial(self.prepare_dice_roll, f"{fert_name}_PWT"))
                tree.setItemWidget(fert_item, 1, pwt_button)

                if fert_data.gekaufteTalente:
                    fert_item.setExpanded(False)
                    for talent_name in fert_data.gekaufteTalente:
                        talent_item = QTreeWidgetItem(fert_item)
                        talent_button = QPushButton(f"- {talent_name}")
                        talent_button.setFlat(True)
                        talent_button.setStyleSheet("text-align: left; border: none; background-color: transparent; padding-left: 10px; font-style: italic;")
                        talent_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                        talent_button.clicked.connect(partial(self.show_talent_info, talent_name=talent_name))
                        tree.setItemWidget(talent_item, 0, talent_button)
                        talent_item.setFlags(talent_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            tree.expandItem(kategorie_item)
    
    def load_supernatural_energies(self):
        asp_widget = self.asp_layout_widget.parentWidget()
        kap_widget = self.kap_layout_widget.parentWidget()
        if 'AsP' in Wolke.Char.energien and Wolke.Char.energien['AsP'].wertFinal > 0:
            asp_max = Wolke.Char.energien['AsP'].wertFinal
            self.label_asp_max.setText(f"<b>{asp_max}</b>")
            self.spin_asp_current.setRange(0, asp_max)
            current_asp = getattr(Wolke.Char, 'dicePlugin_current_asp', -1)
            if current_asp == -1:
                current_asp = asp_max
                Wolke.Char.dicePlugin_current_asp = current_asp
            self.spin_asp_current.setValue(current_asp)
            asp_widget.show()
        else:
            asp_widget.hide()
        if 'KaP' in Wolke.Char.energien and Wolke.Char.energien['KaP'].wertFinal > 0:
            kap_max = Wolke.Char.energien['KaP'].wertFinal
            self.label_kap_max.setText(f"<b>{kap_max}</b>")
            self.spin_kap_current.setRange(0, kap_max)
            current_kap = getattr(Wolke.Char, 'dicePlugin_current_kap', -1)
            if current_kap == -1:
                current_kap = kap_max
                Wolke.Char.dicePlugin_current_kap = current_kap
            self.spin_kap_current.setValue(current_kap)
            kap_widget.show()
        else:
            kap_widget.hide()

    def update_supernatural_energies(self):
        if self.currentlyLoading: return
        if 'AsP' in Wolke.Char.energien and Wolke.Char.energien['AsP'].wertFinal > 0:
            Wolke.Char.dicePlugin_current_asp = self.spin_asp_current.value()
        if 'KaP' in Wolke.Char.energien and Wolke.Char.energien['KaP'].wertFinal > 0:
            Wolke.Char.dicePlugin_current_kap = self.spin_kap_current.value()
        self.modified.emit()

    def load_ressourcen_non_inventory(self):
        self.spinSchips.setValue(getattr(Wolke.Char, "dicePlugin_schips", 4))
        geld = getattr(Wolke.Char, "dicePlugin_geld", {}); self.spinDukaten.setValue(geld.get('Dukaten', 0)); self.spinSilber.setValue(geld.get('Silber', 0))
        self.spinHeller.setValue(geld.get('Heller', 0)); self.spinKreuzer.setValue(geld.get('Kreuzer', 0))
        self.textKleidung.setPlainText(getattr(Wolke.Char, "dicePlugin_kleidung", ""))

    def load_inventar(self):
        self.listContainers.blockSignals(True)
        while self.stackedContainerInhalt.count() > 0: self.stackedContainerInhalt.removeWidget(self.stackedContainerInhalt.widget(0))
        self.container_text_edits.clear(); self.listContainers.clear()
        for i,c in enumerate(getattr(Wolke.Char,"dicePlugin_inventar",[])): self._add_container_widgets(i,c)
        self.listContainers.blockSignals(False)
        if self.listContainers.count() > 0: self.listContainers.setCurrentRow(0)

    def load_tagebuch(self):
        self.listThemen.blockSignals(True)
        while self.stackedThemaInhalt.count() > 0: self.stackedThemaInhalt.removeWidget(self.stackedThemaInhalt.widget(0))
        self.thema_text_edits.clear(); self.listThemen.clear()
        for i,t in enumerate(getattr(Wolke.Char,"dicePlugin_tagebuch",[])): self._add_thema_widgets(i,t)
        self.listThemen.blockSignals(False)
        if self.listThemen.count() > 0: self.listThemen.setCurrentRow(0)

    def roll_free_dice(self):
        dice_string = self.lineFreeRoll.text()
        if not dice_string: self.labelFreeRollResult.setText("Ergebnis: Bitte eine Würfelnotation eingeben."); return
        total, result_string = self.parse_and_roll_dice_string(dice_string)
        self.labelFreeRollResult.setText(result_string)

    def parse_and_roll_dice_string(self, dice_string):
        total_result = 0; result_parts = []
        pattern = r"([+-]?\s*\d*[wWdD]\d+|\s*[+-]?\s*\d+)"; parts = re.findall(pattern, dice_string.replace(" ",""))
        for part in parts:
            part = part.strip()
            if not part: continue
            dice_pattern = re.match(r"([+-])?(\d+)?[wWdD](\d+)", part)
            mod_pattern = re.match(r"([+-])?(\d+)", part)
            if dice_pattern:
                sign = -1 if dice_pattern.group(1) == '-' else 1; num_dice = int(dice_pattern.group(2)) if dice_pattern.group(2) else 1; sides = int(dice_pattern.group(3))
                current_rolls = [random.randint(1, sides) for _ in range(num_dice)]; sum_of_rolls = sum(current_rolls)
                total_result += sign * sum_of_rolls
                colored = ", ".join(format_die_html(r, sides) for r in current_rolls)
                roll_str = f"{num_dice}W{sides} ({colored})"; result_parts.append(f"{dice_pattern.group(1) or '+'} {roll_str}")
            elif mod_pattern and not re.search(r'[wWdD]', part):
                sign = -1 if mod_pattern.group(1) == '-' else 1; value = int(mod_pattern.group(2)); total_result += sign * value
                result_parts.append(f"{mod_pattern.group(1) or '+'} {value}")
        if not result_parts: return 0, "Ergebnis: Ungültige Eingabe."
        full_result_str = " ".join(result_parts).lstrip('+ '); return total_result, f"Ergebnis: {full_result_str} = {total_result}"

    def _get_char_gs(self):
        """GS* aus Abgeleitete Kampfwerte (finalwert), inkl. Effekt-Mod auf GS."""
        try:
            ab = getattr(Wolke.Char, "abgeleiteteWerte", None) or {}
            gs_obj = ab.get("GS") if isinstance(ab, dict) else None
            base = None
            if gs_obj is not None:
                # finalwert = GS* (wie in der Kampfwerte-Anzeige)
                if hasattr(gs_obj, "finalwert"):
                    base = int(gs_obj.finalwert or 0)
                elif hasattr(gs_obj, "wert"):
                    base = int(gs_obj.wert or 0)
                else:
                    base = int(gs_obj)
            if base is None:
                # Fallback: Label-Text parsen, falls schon gerendert
                lab = getattr(self, "kampf_gs_stern_label", None)
                if lab is not None:
                    import re as _re
                    m = _re.search(r"(-?\d+)", lab.text() or "")
                    if m:
                        base = int(m.group(1))
            if base is None:
                base = 4
            # Effekt-Mods auf GS (wie andere Kampfwerte)
            try:
                base += int(self.get_effect_mods().get("gs", 0) or 0)
            except Exception:
                pass
            return max(0, int(base))
        except Exception:
            return 4

    def _player_has_vorteil(self, name):
        if not hasattr(Wolke, "Char") or Wolke.Char is None:
            return False
        vorteile = getattr(Wolke.Char, "vorteile", {}) or {}
        if name in vorteile:
            return True
        # Fallbacks für Namensvarianten
        lower = {str(k).lower() for k in vorteile.keys()}
        return name.lower() in lower

    def _get_pending_weapon(self):
        """Aktuelle Waffe aus pending_weapon_name (anzeigename) auflösen."""
        if not self.pending_weapon_name or not hasattr(Wolke, "Char") or Wolke.Char is None:
            return None
        name = self.pending_weapon_name
        for w in getattr(Wolke.Char, "waffen", []) or []:
            if not getattr(w, "name", None):
                continue
            if getattr(w, "anzeigename", None) == name or w.name == name:
                return w
        return None

    def _weapon_is_fernkampf(self, weapon=None):
        w = weapon if weapon is not None else self._get_pending_weapon()
        if w is None:
            return False
        # datenbank.xml: fk hat Vorrang
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

    def _weapon_has_eigenschaft(self, prop, weapon=None):
        """Prüft Waffeneigenschaft (Teilstring-Match, case-insensitive)."""
        w = weapon if weapon is not None else self._get_pending_weapon()
        prop_l = (prop or "").lower()
        if w is not None:
            eig = getattr(w, "eigenschaften", None) or []
            for e in eig:
                if prop_l in str(e).lower():
                    return True
        if self._weapon_is_fernkampf(w):
            ammo = self._selected_munition()
            if ammo_has_eigenschaft(ammo, prop):
                return True
        return False

    def _weapon_is_waffenlos(self, weapon=None):
        w = weapon if weapon is not None else self._get_pending_weapon()
        if w is None:
            # Keine Waffe gewählt → waffenlos möglich
            return True
        name = (getattr(w, "name", "") or getattr(w, "anzeigename", "") or "").lower()
        fert = (getattr(w, "fertigkeit", "") or "").lower()
        if "unbewaffnet" in name or "waffenlos" in name:
            return True
        if "handgemenge" in fert and ("unbewaffnet" in name or not name):
            return True
        return False

    def _clear_manöver_layout(self, roller):
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

    def _wire_manöver_mutex(self, main_widgets: dict, kombi_widgets: dict):
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

    def _apply_manöver_availability(self, roller, probe_type="AT"):
        """Kompaktes 2-Spalten-Grid aller verfügbaren Manöver (ohne Scroll)."""
        if "manöver_layout" not in roller:
            return

        weapon = self._get_pending_weapon()
        is_fk = self._weapon_is_fernkampf(weapon)
        is_waffenlos = self._weapon_is_waffenlos(weapon)

        def has_v(name):
            return self._player_has_vorteil(name)

        def has_eig(prop):
            return self._weapon_has_eigenschaft(prop, weapon)

        self._clear_manöver_layout(roller)
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
        if self._has_active_volle("off") or self._has_active_volle("def"):
            available = [
                m for m in available
                if m.get("id") not in ("sturmangriff", "ueberrennen")
                and m.get("effekt") not in ("sturmangriff", "ueberrennen")
            ]

        if not available:
            layout.addWidget(QLabel("<i>Keine Manöver</i>"), 0, 0)
            roller["manöver_widgets"] = widgets
            if "atemtechnik_check" in roller:
                roller["_has_atemtechnik"] = self._player_has_vorteil("Atemtechnik")
            return

        # 2-Spalten-Grid: kompakte Labels, voller Text im Tooltip
        cols = 2
        for i, m in enumerate(available):
            row, col = divmod(i, cols)
            cell = QHBoxLayout()
            cell.setContentsMargins(0, 0, 0, 0)
            cell.setSpacing(2)
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
            # Sturmangriff / Überrennen: GS* oder fester Wert x
            if m.get("effekt") in ("sturmangriff", "ueberrennen") or m["id"] in ("sturmangriff", "ueberrennen"):
                mode_combo = QComboBox()
                mode_combo.addItem("GS*", "gs")
                mode_combo.addItem("x", "x")
                mode_combo.setFixedWidth(56)
                mode_combo.setToolTip("GS* = eigene GS; x = festen Bonus wählen")
                spin = QSpinBox()
                spin.setRange(0, 40)
                spin.setValue(self._get_char_gs())
                spin.setFixedWidth(44)
                spin.setToolTip("TP-Bonus durch Sturmangriff/Überrennen")
                spin.setEnabled(False)  # GS*-Modus: Wert aus Charakter
                def _sync_sturm_mode(idx, sp=spin, combo=mode_combo):
                    try:
                        use_x = combo.currentData() == "x"
                        sp.setEnabled(use_x)
                        if not use_x:
                            sp.setValue(self._get_char_gs())
                    except RuntimeError:
                        pass
                mode_combo.currentIndexChanged.connect(_sync_sturm_mode)
                def _on_sturm_cb(checked, sp=spin, combo=mode_combo):
                    try:
                        sp.setVisible(checked)
                        combo.setVisible(checked)
                        if checked and combo.currentData() == "gs":
                            sp.setValue(self._get_char_gs())
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
            layout.addWidget(wrap, row, col)
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

            # Gegenseitiger Ausschluss: Schildspalter / Umklammern / Entwaffnen / Umreißen
            self._wire_manöver_mutex(widgets, kombi_widgets)

            roller["riposte_kombi_widgets"] = kombi_widgets
            roller["riposte_kombi_box"] = kombi_box
            roller["_riposte_combo_defs"] = {cm["id"]: cm for cm in combo_list}
        else:
            # Auch ohne Riposte: Mutex in der Hauptliste verdrahten
            self._wire_manöver_mutex(widgets, {})

        roller["manöver_widgets"] = widgets
        if "atemtechnik_check" in roller:
            roller["_has_atemtechnik"] = self._player_has_vorteil("Atemtechnik")


    def _weapon_eigenschaft_tips_dice(self):
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

    def _fill_waffeig_panel_dice(self, roller, weapon=None, eig_override=None, info_text=""):
        box = roller.get("waffeig_box")
        body = roller.get("waffeig_body")
        toggle = roller.get("waffeig_toggle")
        if box is None or body is None:
            return
        eig_text = eig_override or ""
        if not eig_text and weapon is not None:
            eig = getattr(weapon, "eigenschaften", None) or []
            if isinstance(eig, (list, tuple)):
                eig_text = ", ".join(str(x) for x in eig)
            else:
                eig_text = str(eig) if eig else ""
        tips = self._weapon_eigenschaft_tips_dice()
        names = [x.strip() for x in (eig_text or "").split(",") if x.strip()]
        if not names and not info_text:
            box.setVisible(False)
            if toggle is not None:
                toggle.blockSignals(True)
                toggle.setChecked(False)
                toggle.blockSignals(False)
            body.setVisible(False)
            body.setText("")
            return
        parts = []
        if info_text:
            parts.append("<b>Info:</b> " + str(info_text).replace(chr(10), "<br>"))
        for n in names:
            disp, tip = tips.get(n.lower(), (n, ""))
            tip_html = (tip or "").replace(chr(10), "<br>")
            parts.append(f"<b>{disp}</b>" + (f" — {tip_html}" if tip_html else ""))
        body.setText("<br>".join(parts))
        box.setVisible(True)
        if toggle is not None:
            toggle.blockSignals(True)
            toggle.setChecked(False)
            toggle.setText("▸ Waffeneigenschaften")
            toggle.blockSignals(False)
        body.setVisible(False)

    def prepare_dice_roll(self, probe_name, fixed_pw=None, is_tp_roll=False, tp_string_base=""):
        self._last_prepare = {
            "probe_name": probe_name,
            "fixed_pw": fixed_pw,
            "is_tp_roll": is_tp_roll,
            "tp_string_base": tp_string_base or "",
        }
        active_tab_text = self.tabs.tabText(self.tabs.currentIndex())
        if active_tab_text == "Attribute": self.active_dice_roller = self.attr_dice_roller
        elif active_tab_text == "Fertigkeiten": self.active_dice_roller = self.skill_dice_roller
        elif active_tab_text == "Übernatürliches": self.active_dice_roller = self.supernatural_dice_roller
        elif active_tab_text == "Kampf": self.active_dice_roller = self.kampf_dice_roller; self.kampf_stack.setCurrentIndex(self.kampf_dice_roller_index)
        else: return
        roller = self.active_dice_roller
        roller["widget"].setEnabled(True)
        self.custom_mod_value = 0
        roller["label_mod"].setText("0")
        roller["label_result"].setText("Ergebnis: ")
        self._roll_mode = "normal"
        if roller.get("triumph_wrap"):
            roller["triumph_wrap"].setVisible(False)
        roller["radio1W20"].show()
        roller["radio3W20"].show()
        if "options_box" in roller:
            roller["options_box"].setVisible(True)
        if roller.get("reaktion_btn"):
            roller["reaktion_btn"].setVisible(False)
        if roller.get("free_reaktion_btn"):
            roller["free_reaktion_btn"].setVisible(False)

        roller["reach_malus"].setChecked(False)
        roller["reach_bonus"].setChecked(False)
        roller["atemtechnik_check"].setChecked(False)
        roller["hammerschlag_check"].setChecked(False)
        roller["atemtechnik_check"].setVisible(False)
        roller["hammerschlag_check"].setVisible(False)
        zec = roller.get("zweite_einfache_check")
        if zec is not None:
            zec.blockSignals(True)
            zec.setChecked(False)
            zec.setVisible(False)
            zec.blockSignals(False)
        if roller.get("aktionen_box"):
            roller["aktionen_box"].setVisible(False)
        for key in ("volle_off_check", "volle_def_check"):
            cb = roller.get(key)
            if cb is not None:
                cb.blockSignals(True)
                cb.setChecked(False)
                cb.setVisible(False)
                cb.blockSignals(False)
        if "manöver_box" in roller:
            roller["manöver_box"].setVisible(False)
            # Nur leeren, wenn nichts gemerkt – sonst nach Availability wiederherstellen
            if not self._merken_manöver:
                self._reset_manöver_ui(roller, clear_memory=False)
        if "präzision_label" in roller:
            roller["präzision_label"].setVisible(False)
            roller["präzision_label"].setText("")
        if "continue_btn" in roller:
            roller["continue_btn"].setVisible(False)

        self.is_tp_roll = is_tp_roll
        # Pending-Werte nur zurücksetzen, wenn NICHT in den TP-Modus aus dem AT-Flow gewechselt wird
        if not is_tp_roll:
            self.präzision_ge_bonus = 0
            self._pending_wuchtschlag_tp = 0
            self._pending_sturm_tp = 0
            self._pending_rüstungsbrecher = False
            self._pending_todesstoß = False
            self._pending_manöver_notes = []
            self._pending_no_damage = False
            self._pending_auflaufen = False
            self._pending_riposte = False
            self._last_at_ew = None
            if fixed_pw is None:
                self.pending_tp_string = None
                self.pending_weapon_name = None
            # GS-Spin für Auflaufen ausblenden
            if "auflaufen_gs_spin" in roller:
                roller["auflaufen_gs_spin"].setVisible(False)
                roller["auflaufen_gs_label"].setVisible(False)

        self.current_probe_pw = 0
        display_name = ""
        is_at_vt_probe = False
        is_at_probe = False
        is_vt_probe = False

        if is_tp_roll:
            display_name = f"Schaden ({tp_string_base})"
            roller["radio1W20"].hide()
            roller["radio3W20"].hide()
            # TP: keine Optionen, keine Aktionen, kein Hammerschlag-Haken
            if "options_box" in roller:
                roller["options_box"].setVisible(False)
            roller["hammerschlag_check"].setVisible(False)
            zec = roller.get("zweite_einfache_check")
            if zec is not None:
                zec.blockSignals(True)
                zec.setChecked(False)
                zec.setVisible(False)
                zec.blockSignals(False)
            self._sync_aktionen_checks(roller, is_tp=True, is_at=False, is_vt=False)
            if "manöver_box" in roller:
                roller["manöver_box"].setVisible(False)
            if "kampfmod_box" in roller:
                roller["kampfmod_box"].setVisible(False)
            self._fill_waffeig_panel_dice(roller, self._get_pending_weapon())
        elif fixed_pw is not None:
            self.current_probe_pw = fixed_pw
            display_name = probe_name
            self.current_probe_type_str = probe_name.split(" ")[0]
            roller["radio1W20"].setChecked(True)
            roller["radio3W20"].hide()
            is_at_vt_probe = "AT" in probe_name or "VT" in probe_name
            is_at_probe = probe_name.startswith("AT") or "AT (" in probe_name
            is_vt_probe = probe_name.startswith("VT") or "VT (" in probe_name
            # AT/VT: nur 1W20 – Optionen ausblenden
            if is_at_vt_probe and "options_box" in roller:
                roller["options_box"].setVisible(False)
            if roller.get("reaktion_btn"):
                roller["reaktion_btn"].setVisible(is_at_probe)
            if roller.get("free_reaktion_btn"):
                roller["free_reaktion_btn"].setVisible(is_vt_probe)
            if (is_at_probe or is_vt_probe) and "manöver_box" in roller:
                roller["manöver_box"].setVisible(True)
                ptype = "VT" if is_vt_probe else "AT"
                self._apply_manöver_availability(roller, probe_type=ptype)
                if self._merken_manöver:
                    self._restore_manöver_from_memory(roller)
                self._sync_aktionen_checks(
                    roller, is_tp=False, is_at=is_at_probe, is_vt=is_vt_probe
                )
                self._fill_waffeig_panel_dice(roller, self._get_pending_weapon())
            zec = roller.get("zweite_einfache_check")
            if zec is not None:
                zec.setVisible(bool(is_at_probe))
                # Volle Defensive aktiv → Haken setzen
                if is_at_probe and self._has_active_volle("def"):
                    zec.blockSignals(True)
                    zec.setChecked(True)
                    zec.blockSignals(False)
        elif "_" in probe_name:
            skill_id, probe_type = probe_name.split("_")
            fertigkeiten = Wolke.Char.fertigkeiten
            if self.tabs.tabText(self.tabs.currentIndex()) == "Übernatürliches":
                fertigkeiten = Wolke.Char.übernatürlicheFertigkeiten
            if skill_id in fertigkeiten:
                skill_data = fertigkeiten[skill_id]
                if probe_type == "PW":
                    self.current_probe_pw = skill_data.probenwert
                    self.current_probe_type_str = "PW"
                    display_name = f"{skill_id} (PW {self.current_probe_pw})"
                else: #PWT
                    self.current_probe_pw = skill_data.probenwertTalent
                    self.current_probe_type_str = "PW(T)"
                    display_name = f"{skill_id} (PW(T) {self.current_probe_pw})"
        else:
            display_name = probe_name
            self.current_probe_type_str = "PW"
            if probe_name == "MR":
                if 'MR' in Wolke.Char.abgeleiteteWerte: self.current_probe_pw = Wolke.Char.abgeleiteteWerte['MR'].wert
            elif probe_name in Wolke.Char.attribute: 
                self.current_probe_pw = Wolke.Char.attribute[probe_name].probenwert
            display_name = f"{display_name} (PW {self.current_probe_pw})"

        self.current_probe_name = display_name
        roller["label_probe"].setText(f"<h3>Probe: {self.current_probe_name}</h3>")

        roller["reach_box"].setVisible(False)
        is_fk = self._weapon_is_fernkampf()
        is_vt_only = bool(is_vt_probe) or (
            (self.current_probe_type_str == "VT")
            or ("VT" in (display_name or "") and "AT" not in (display_name or ""))
        )
        if roller.get("munition_box"):
            roller["munition_box"].setVisible(False)
        if "kampfmod_box" in roller:
            show_km = is_at_vt_probe
            roller["kampfmod_box"].setVisible(show_km)
            if show_km:
                use_fk = is_fk and not is_vt_only
                roller["nk_panel"].setVisible(not use_fk)
                roller["fk_panel"].setVisible(use_fk)
                roller["kampfmod_box"].setTitle(
                    "Kampf-Modifikatoren (Fernkampf)" if use_fk else "Kampf-Modifikatoren (Nahkampf)"
                )
                if self._merken_kampfmod:
                    self._restore_kampfmod_from_memory(roller)
                if roller.get("kampfmod_merken_btn"):
                    roller["kampfmod_merken_btn"].setText(
                        "Merken ✓" if self._merken_kampfmod else "Merken"
                    )
            self._fill_munition_panel(
                roller, is_fk=is_fk, is_at=bool(is_at_probe) and not is_vt_only
            )

    def prepare_at_with_tp(self, weapon_name, at_value, tp_string):
        """AT-Wurf aus dem Kampf-Tab inkl. TP für den Weiter-Flow."""
        self.pending_tp_string = tp_string or ""
        self.pending_weapon_name = weapon_name
        self.prepare_dice_roll(f"AT ({weapon_name})", at_value, False)

    def prepare_vt_with_tp(self, weapon_name, vt_value, tp_string):
        """VT-Wurf inkl. TP (für Auflaufen lassen → Schaden)."""
        self.pending_tp_string = tp_string or ""
        self.pending_weapon_name = weapon_name
        self.prepare_dice_roll(f"VT ({weapon_name})", vt_value, False)
    
    def _get_munition(self):
        if not hasattr(Wolke.Char, "dicePlugin_munition"):
            Wolke.Char.dicePlugin_munition = []
        Wolke.Char.dicePlugin_munition = ensure_selected_ammo(
            normalize_ammo_list(Wolke.Char.dicePlugin_munition)
        )
        return Wolke.Char.dicePlugin_munition

    def _set_munition(self, items):
        Wolke.Char.dicePlugin_munition = ensure_selected_ammo(normalize_ammo_list(items))
        self.modified.emit()

    def _add_munition(self):
        dlg = AmmoEditDialog(blank_ammo("Neue Munition"), self.form)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            items = self._get_munition()
            items.append(dlg.result_data())
            self._set_munition(items)
            self._rebuild_munition_ui()
            self._refresh_roller_munition()

    def _edit_munition(self, ammo_id):
        items = self._get_munition()
        cur = next((a for a in items if a.get("id") == ammo_id), None)
        if not cur:
            return
        dlg = AmmoEditDialog(cur, self.form)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.result_data()
            items = [data if a.get("id") == ammo_id else a for a in items]
            self._set_munition(items)
            self._rebuild_munition_ui()
            self._refresh_roller_munition()

    def _remove_munition(self, ammo_id):
        items = [a for a in self._get_munition() if a.get("id") != ammo_id]
        self._set_munition(items)
        self._rebuild_munition_ui()
        self._refresh_roller_munition()

    def _on_munition_count_changed(self, ammo_id, val):
        items = self._get_munition()
        for a in items:
            if a.get("id") == ammo_id:
                a["anzahl"] = int(val)
        self._set_munition(items)
        self._refresh_roller_munition()

    def _rebuild_munition_ui(self):
        layout = getattr(self, "kampf_munition_layout", None)
        if layout is None:
            return
        for i in reversed(range(1, layout.rowCount())):
            for j in range(layout.columnCount()):
                item = layout.itemAtPosition(i, j)
                if item and item.widget():
                    item.widget().deleteLater()
        row = 1
        for a in self._get_munition():
            sel = QLabel("●" if a.get("selected") else "")
            sel.setToolTip("Aktuell angelegt")
            layout.addWidget(sel, row, 0)
            name_btn = QPushButton(a.get("name") or "Munition")
            name_btn.setFlat(True)
            name_btn.setStyleSheet("text-align:left;")
            name_btn.clicked.connect(partial(self._edit_munition, a.get("id")))
            layout.addWidget(name_btn, row, 1)
            spin = QSpinBox()
            spin.setRange(0, 999)
            spin.setValue(int(a.get("anzahl", 0) or 0))
            spin.setFixedWidth(56)
            spin.valueChanged.connect(partial(self._on_munition_count_changed, a.get("id")))
            layout.addWidget(spin, row, 2)
            layout.addWidget(QLabel(a.get("tp") or "—"), row, 3)
            layout.addWidget(QLabel(str(a.get("rw") or 0)), row, 4)
            layout.addWidget(QLabel(str(a.get("lz") or 0)), row, 5)
            eig = QLabel(a.get("eigenschaften") or "")
            eig.setWordWrap(True)
            layout.addWidget(eig, row, 6)
            del_btn = QPushButton("✕")
            del_btn.setFlat(True)
            del_btn.setFixedWidth(22)
            del_btn.clicked.connect(partial(self._remove_munition, a.get("id")))
            layout.addWidget(del_btn, row, 7)
            row += 1

    def _refresh_roller_munition(self):
        roller = getattr(self, "active_dice_roller", None) or getattr(self, "kampf_dice_roller", None)
        if roller:
            self._fill_munition_panel(roller)

    def _fill_munition_panel(self, roller, *, is_fk=None, is_at=None):
        box = roller.get("munition_box") if roller else None
        host = roller.get("munition_host") if roller else None
        if box is None or host is None:
            return
        if is_fk is None:
            is_fk = self._weapon_is_fernkampf()
        if is_at is None:
            name = self.current_probe_name or ""
            is_at = bool(("AT" in name) and ("VT" not in name))
        show = bool(is_fk and is_at)
        box.setVisible(show)
        lay = host.layout()
        if lay is None:
            lay = QVBoxLayout(host)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(2)
        while lay.count():
            child = lay.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        if not show:
            return
        items = self._get_munition()
        if not items:
            lay.addWidget(QLabel("<i>Keine Munition angelegt – im Kampf-Tab hinzufügen.</i>"))
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
            tip_parts = []
            if a.get("eigenschaften"):
                tip_parts.append(str(a.get("eigenschaften")))
            if tip_parts:
                cb.setToolTip(" · ".join(tip_parts))
            aid = a.get("id")
            cb.toggled.connect(partial(self._on_roller_munition_toggled, aid))
            lay.addWidget(cb)
            group.addButton(cb)
        roller["_munition_group"] = group

    def _on_roller_munition_toggled(self, ammo_id, checked):
        if not checked:
            return
        items = set_selected_ammo(self._get_munition(), ammo_id)
        self._set_munition(items)
        self._rebuild_munition_ui()
        # Rüstungsbrecher-Verfügbarkeit neu
        roller = self.active_dice_roller
        if roller and not self.is_tp_roll:
            ptype = "AT"
            if self.current_probe_name and "VT" in self.current_probe_name:
                ptype = "VT"
            self._apply_manöver_availability(roller, probe_type=ptype)

    def _selected_munition(self):
        return selected_ammo(self._get_munition())

    def increase_mod(self): 
        if not self.active_dice_roller: return
        self.custom_mod_value += 1; self.active_dice_roller["label_mod"].setText(str(self.custom_mod_value))
    def decrease_mod(self):
        if not self.active_dice_roller: return
        self.custom_mod_value -= 1; self.active_dice_roller["label_mod"].setText(str(self.custom_mod_value))

    def _player_has_präzision(self):
        return hasattr(Wolke, "Char") and Wolke.Char is not None and "Präzision" in getattr(Wolke.Char, "vorteile", {})

    def _player_ge_wert(self):
        """Echter GE-Attributwert (Wert), nicht Probenwert."""
        if not hasattr(Wolke, "Char") or Wolke.Char is None:
            return 0
        attr = Wolke.Char.attribute.get("GE")
        if attr is None:
            return 0
        return int(getattr(attr, "wert", 0) or 0)

    def _sum_combat_mods(self, roller, *, is_at=False):
        """Summiert NK- oder FK-Kampfmodifikatoren. Rückgabe: (total, [labels])."""
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

    def _player_be(self):
        """BE der getragenen Rüstung (Summe/erste Rüstung mit getBEFinal)."""
        if not hasattr(Wolke, "Char") or Wolke.Char is None:
            return 0
        abgeleitete = getattr(Wolke.Char, "abgeleiteteWerte", None) or {}
        total = 0
        found = False
        for ruestung in getattr(Wolke.Char, "rüstung", []) or []:
            if not getattr(ruestung, "name", None):
                continue
            try:
                be = int(ruestung.getBEFinal(abgeleitete) or 0)
            except Exception:
                be = int(getattr(ruestung, "be", 0) or getattr(ruestung, "BE", 0) or 0)
            total += be
            found = True
        if found:
            return total
        # Fallback: abgeleiteter Wert BE falls vorhanden
        be_obj = abgeleitete.get("BE") if isinstance(abgeleitete, dict) else None
        if be_obj is not None:
            return int(getattr(be_obj, "wert", be_obj) or 0)
        return 0

    def _manöver_at_mod_player(self, roller):
        """Summiert fixe/variable Mods inkl. –BE aus allen gewählten Manövern."""
        mod = 0
        be = self._player_be()
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
                    mod += int(m)  # +2 bei Schildspalter, sonst negativ
                if mdef.get("mod_be"):
                    mod -= be
            # Riposte-Kombi: zusätzlicher AT-Manöver-Malus auf die VT
            mod += self._riposte_combo_mod(roller)
            return mod
        # Legacy-Fallback
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

    def _riposte_combo_mod(self, roller) -> int:
        """Zusätzlicher VT-Malus durch alle mit Riposte kombinierten AT-Manöver."""
        widgets = roller.get("manöver_widgets") or {}
        riposte = widgets.get("riposte")
        if not riposte or not riposte.get("cb") or not riposte["cb"].isChecked():
            return 0
        be = self._player_be()
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

    def _selected_manöver_flags(self, roller):
        """Flags zu aktuell gewählten Manövern."""
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
            # Sturmangriff/Überrennen: bei GS* aktuelle GS nachziehen
            if effekt in ("sturmangriff", "ueberrennen"):
                mode = info.get("mode")
                if mode is not None and mode.currentData() == "gs":
                    spin_val = self._get_char_gs()
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

        # Riposte-Kombi: alle angehakten AT-Manöver übernehmen
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

    def _execute_with_roll_mode(self, mode):
        self._roll_mode = mode or "normal"
        self.execute_dice_roll()

    def execute_dice_roll(self):
        if self.current_probe_name is None or not self.active_dice_roller:
            return
        blocker = has_blocking_probe_effect(self._get_effects())
        if blocker:
            self._show_top_info(
                blocker,
                f"Keine Probe moglich: Effekt „{blocker}“ aktiv.",
            )
            return
        # Volle Defensive ohne Defensiver Kampfstil blockiert nur AT (nicht VT/TP)
        is_at_probe = bool(
            not self.is_tp_roll
            and self.current_probe_name
            and (
                self.current_probe_name.startswith("AT")
                or "AT (" in self.current_probe_name
            )
        )
        if is_at_probe:
            at_blocker = has_blocking_at_effect(self._get_effects())
            if at_blocker:
                self._show_top_info(
                    at_blocker,
                    f"Keine Attacke möglich: Effekt „{at_blocker}“ aktiv "
                    f"(Volle Defensive belegt die Aktion).",
                )
                return
            if self._weapon_is_fernkampf():
                items, used = consume_selected_ammo(self._get_munition())
                if used:
                    self._set_munition(items)
                    self._rebuild_munition_ui()
                    self._fill_munition_panel(self.active_dice_roller)
        roller = self.active_dice_roller
        
        if self.is_tp_roll:
            tp_string_match = re.search(r'\((.*?)\)', self.current_probe_name)
            tp_string_base = tp_string_match.group(1) if tp_string_match else ""
            
            base_total, base_result_str = self.parse_and_roll_dice_string(tp_string_base)
            base_display = base_result_str.split("Ergebnis: ")[1] if "Ergebnis: " in base_result_str else base_result_str

            wpn_for_tp = getattr(self, "pending_weapon_name", None) or ""
            gift_notes = []
            # Waffenschaden-Effekte VOR Hammerschlag auf den Waffenwurf
            for te in collect_tp_dice_effects(self._get_effects(), wpn_for_tp):
                wsch = te.get("waffenschaden") or ""
                if wsch:
                    dmg, detail = parse_tp_dice_string(wsch)
                    if dmg:
                        base_total += dmg
                        base_display = f"{base_display} {dmg:+d} ({detail}, Waffenschaden/{te.get('name')})"
            
            if roller["hammerschlag_check"].isChecked():
                base_total *= 2
                base_display = f"({base_display}) x 2 = {base_total} (Hammerschlag)"
            
            additional_total = 0
            additional_parts = []
            
            if self.custom_mod_value != 0:
                sign = '+' if self.custom_mod_value > 0 else ''
                additional_total += self.custom_mod_value
                additional_parts.append(f"{sign}{self.custom_mod_value} (Mod)")
            
            # Atemtechnik +1W6 kommt nur noch ueber Aktive Effekte (tp_dice),
            # nicht zusaetzlich ueber den Haken (sonst Doppelung).

            # TP-Bonus-Effekte NACH Hammerschlag + Waffengift-Hinweise
            for te in collect_tp_dice_effects(self._get_effects(), wpn_for_tp):
                dice_expr = te.get("dice") or ""
                if dice_expr:
                    dmg, detail = parse_tp_dice_string(dice_expr)
                    if dmg:
                        additional_total += dmg
                        additional_parts.append(
                            f"{'+' if dmg >= 0 else ''}{dmg} ({detail}, {te.get('name')})"
                        )
                if te.get("info") or te.get("is_waffengift"):
                    note = te.get("info") or te.get("name") or "Waffengift"
                    gift_notes.append(f"{te.get('name')}: {note}" if te.get("info") else str(te.get("name")))

            ammo = self._selected_munition()
            if ammo and (ammo.get("tp") or "").strip():
                dmg, detail = parse_tp_dice_string(ammo.get("tp") or "")
                if dmg:
                    additional_total += dmg
                    additional_parts.append(
                        f"{'+' if dmg >= 0 else ''}{dmg} ({detail}, {ammo.get('name')})"
                    )
                elif detail:
                    additional_parts.append(f"{ammo.get('name')}: {detail}")

            # Ladungen Waffengift / tp_waffe bei diesem TP
            new_list, evs = tick_effects_on_tp(self._get_effects(), wpn_for_tp)
            self._set_effects(new_list)
            self._rebuild_effects_ui()
            self._update_effects_mod_label()
            self._handle_effect_events(evs)

            # Manöver ohne normalen Schaden (Umreißen, Entwaffnen, Umklammern)
            if getattr(self, "_pending_no_damage", False):
                notes = getattr(self, "_pending_manöver_notes", None) or []
                lines = ["<b>Kein Schaden</b> – Manöverwirkung statt TP:"]
                lines.extend(f"• {n}" for n in notes)
                roller["label_result"].setText("<br>".join(lines))
            else:
                if self._pending_wuchtschlag_tp:
                    additional_total += self._pending_wuchtschlag_tp
                    additional_parts.append(f"+{self._pending_wuchtschlag_tp} (Wuchtschlag/Scharfschuss)")
                if getattr(self, "_pending_sturm_tp", 0):
                    additional_total += self._pending_sturm_tp
                    additional_parts.append(f"+{self._pending_sturm_tp} (Sturmangriff/Überrennen)")

                if self.präzision_ge_bonus > 0:
                    additional_total += self.präzision_ge_bonus
                    additional_parts.append(f"+{self.präzision_ge_bonus} (Präzision/GE)")

                if getattr(self, "_pending_auflaufen", False):
                    gs = 0
                    if "auflaufen_gs_spin" in roller:
                        gs = int(roller["auflaufen_gs_spin"].value() or 0)
                    additional_total += gs
                    additional_parts.append(f"+{gs} (Gegner-GS / Auflaufen)")

                total = base_total + additional_total
                additional_str = ' '.join(additional_parts) if additional_parts else ""
                if additional_str and additional_str[0] not in ['+', '-']:
                    additional_str = ' ' + additional_str

                result_string = f"Schaden: {base_display}{additional_str} = <b>{total}</b>"
                notes = getattr(self, "_pending_manöver_notes", None) or []
                # Hinweise die nicht schon als Zahl verrechnet sind
                extra = []
                for n in notes:
                    if n.startswith("+") and "TP" in n:
                        continue  # schon in additional_parts
                    extra.append(n)
                if extra:
                    result_string += "<br><i>" + " · ".join(extra) + "</i>"
                elif self._pending_rüstungsbrecher:
                    result_string += " <i>(SP statt TP)</i>"
                if self._pending_todesstoß and not any("+2 Wunden" in n for n in notes):
                    result_string += " <i>(+2 Wunden)</i>"
                if gift_notes:
                    result_string += "<br><i>" + " · ".join(gift_notes) + "</i>"
                roller["label_result"].setText(result_string)
        else:
            if roller["radio1W20"].isChecked():
                rolls = [random.randint(1, 20)]; dice_result = rolls[0]
                roll_info = format_roll_info_1w20(dice_result)
            else:
                rolls = sorted([random.randint(1, 20) for _ in range(3)]); dice_result = rolls[1]
                roll_info = format_roll_info_3w20(rolls, dice_result)
            
            wound_penalty = self.get_wound_penalty()
            is_at = (self.current_probe_type_str == "AT") or (self.current_probe_name or "").startswith("AT")
            is_vt = (self.current_probe_type_str == "VT") or "VT" in (self.current_probe_name or "")
            combat_mod, combat_parts = self._sum_combat_mods(roller, is_at=is_at)
            reach_mod = combat_mod  # ersetzt alte Reichweiten-Checkboxen

            manöver_mod = 0
            manöver_text = ""
            if is_at or is_vt:
                manöver_mod = self._manöver_at_mod_player(roller)
                if manöver_mod != 0:
                    be = self._player_be()
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

            # Reaktions-Malus: normale VT + „Reaktion würfeln“; nicht bei freier Reaktion / normaler AT
            roll_mode = getattr(self, "_roll_mode", "normal") or "normal"
            apply_reaction = False
            if roll_mode == "freie_reaktion":
                apply_reaction = False
            elif roll_mode == "reaktion":
                apply_reaction = True
            elif is_vt:
                apply_reaction = True
            reaktion_mod = 0
            reaktion_text = ""
            if apply_reaction:
                reaktion_mod = int(self.get_reaktion_malus() or 0)
                if reaktion_mod:
                    reaktion_text = f" {reaktion_mod} (Reaktionen)"
                elif roll_mode == "reaktion":
                    reaktion_text = " (Reaktion)"
            elif roll_mode == "freie_reaktion":
                reaktion_text = " (Freie Reaktion)"
            elif roll_mode == "reaktion":
                reaktion_text = " (Reaktion)"

            # Effekt-Mods: Proben auf alles außer Schaden; AT/VT gezielt
            emods = self.get_effect_mods()
            effect_mod = int(emods.get("proben", 0) or 0)
            if is_at:
                effect_mod += int(emods.get("at", 0) or 0)
            if is_vt:
                effect_mod += int(emods.get("vt", 0) or 0)

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
            
            total = (
                self.current_probe_pw + dice_result - wound_penalty
                + self.custom_mod_value + reach_mod + manöver_mod + effect_mod
                + reaktion_mod + zweite_mod
            )
            if is_at:
                self._last_at_ew = total
            result_str = f"{self.current_probe_type_str} ({self.current_probe_pw}) + {roll_info}"
            if wound_penalty > 0: result_str += f" - {wound_penalty} (Wunden)"
            if combat_parts:
                result_str += f" {reach_mod:+d} (Kampf: {', '.join(combat_parts)})".replace("+-", "-")
            if manöver_text: result_str += manöver_text
            if reaktion_text: result_str += reaktion_text
            if zweite_text: result_str += zweite_text
            if effect_mod != 0:
                sign = '+' if effect_mod > 0 else ''
                result_str += f" {sign}{effect_mod} (Effekte)"
            if self.custom_mod_value != 0:
                sign = '+' if self.custom_mod_value > 0 else ''; result_str += f" {sign}{self.custom_mod_value} (Mod)"
            result_str += f" = <b>{total}</b>"
            # Sofort-Hinweise für gewählte Manöver (auch VT)
            notes = self._collect_manöver_notes(roller, at_ew=total if is_at else None)
            if notes:
                result_str += "<br><i>" + " · ".join(notes) + "</i>"
            if is_vt and self._player_has_vorteil("Gegenhalten"):
                result_str += (
                    "<br><b>Gegenhalten</b>: Wenn du eine Attacke abwehrst, die mit einem "
                    "Manöver verstärkt wurde, darfst du sofort einen Passierschlag gegen "
                    "den Angreifer ausführen."
                )
            roller["label_result"].setText(result_str)

            # Triumph / Patzer (Kampfwurf 1W20)
            self._update_triumph_ui(roller, dice_result, is_at, is_vt)

            # Präzision: nur wenn Vorteil gekauft und gewerteter Würfel ≥ 16
            if is_at and self._player_has_präzision() and dice_result >= 16:
                ge = self._player_ge_wert()
                self.präzision_ge_bonus = ge
                if "präzision_label" in roller:
                    roller["präzision_label"].setText(
                        f"Präzision ausgelöst (W{dice_result} ≥ 16)! +{ge} GE (Wert) TP beim Schaden."
                    )
                    roller["präzision_label"].setVisible(True)
            else:
                if is_at:
                    self.präzision_ge_bonus = 0
                if "präzision_label" in roller:
                    roller["präzision_label"].setVisible(False)

            if is_at and roller.get("atemtechnik_check") and roller["atemtechnik_check"].isChecked():
                self.ensure_atemtechnik_effect()

            # Weiter → Schaden steuern
            flags = self._selected_manöver_flags(roller)
            show_continue = False
            if "continue_btn" in roller:
                if flags["no_damage"]:
                    # Umreißen / Entwaffnen / Umklammern: kein TP
                    show_continue = False
                elif is_at and self.pending_tp_string:
                    show_continue = True
                elif is_vt and (flags["auflaufen"] or flags["riposte"]) and self.pending_tp_string:
                    # Auflaufen / Riposte: Verteidiger richtet Schaden an
                    show_continue = True
                roller["continue_btn"].setVisible(show_continue)
                if flags["auflaufen"]:
                    roller["continue_btn"].setText("Weiter → Schaden (Auflaufen)")
                elif flags["riposte"]:
                    roller["continue_btn"].setText("Weiter → Schaden (Riposte)")
                else:
                    roller["continue_btn"].setText("Weiter → Schaden")

            # Reaktionszähler: normale VT und „Reaktion würfeln“
            roll_mode = getattr(self, "_roll_mode", "normal") or "normal"
            should_inc = False
            if roll_mode == "freie_reaktion":
                should_inc = False
            elif roll_mode == "reaktion":
                should_inc = True
            elif is_vt:
                should_inc = True
            if should_inc:
                self.increment_reaktion()
            self._roll_mode = "normal"

            # Timer-Tick „bei erfolgreicher AT“
            if is_at:
                new_list, evs = tick_effects_on_at(self._get_effects())
                self._set_effects(new_list)
                self._rebuild_effects_ui()
                self._update_effects_mod_label()
                self._handle_effect_events(evs)

    def _collect_manöver_notes(self, roller, at_ew=None):
        """Hinweise zu allen aktivierten Manövern."""
        notes = []
        widgets = roller.get("manöver_widgets") or {}
        for mid, info in widgets.items():
            cb = info.get("cb")
            if not cb or not cb.isChecked():
                continue
            mdef = info.get("def") or {}
            spin_val = 0
            sp = info.get("spin")
            if sp is not None:
                spin_val = sp.value()
            h = manöver_tp_hinweis(mdef, spin_val=spin_val, at_ew=at_ew)
            if h:
                notes.append(h)
        return notes

    def _update_triumph_ui(self, roller, dice_result, is_at, is_vt):
        """Zeigt Triumph-/Patzer-Hinweis bei Kampfwurf 1W20."""
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
            # Sichtbarkeit von GS/x-Controls triggern
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
                    # variable Manöver-Mod vs. Sturm-GS
                    if (info.get("def") or {}).get("mod") == "variable":
                        sp.setValue(2)
                    else:
                        sp.setValue(self._get_char_gs())
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

    def continue_to_damage(self):
        """AT/VT → Schaden: Manöver übernehmen und TP-Phase starten."""
        if not self.pending_tp_string or not self.active_dice_roller:
            return
        roller = self.active_dice_roller
        flags = self._selected_manöver_flags(roller)
        # Schaden-0-Manöver: kein TP-Flow
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

        atem_selected = bool(
            roller.get("atemtechnik_check") and roller["atemtechnik_check"].isChecked()
        )
        präz = self.präzision_ge_bonus
        tp = self.pending_tp_string
        wname = self.pending_weapon_name or ""
        last_ew = self._last_at_ew
        self.prepare_dice_roll(f"TP* ({tp})", 0, True, tp)
        self._pending_wuchtschlag_tp = wucht
        self._pending_rüstungsbrecher = rüst
        self._pending_todesstoß = tod
        self._pending_manöver_notes = notes
        self._pending_no_damage = False
        self._pending_auflaufen = auflaufen
        self._pending_riposte = riposte
        self._pending_sturm_tp = int(flags.get("sturm_tp", 0) or 0)
        self._last_at_ew = last_ew
        self.präzision_ge_bonus = präz
        # Hammerschlag/Atemtechnik: Zustand merken, aber im TP-Bereich nicht anzeigen
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
        atem_active = self._has_active_atemtechnik()
        if atem_selected or atem_active:
            self.ensure_atemtechnik_effect()
        if roller.get("atemtechnik_check"):
            roller["atemtechnik_check"].blockSignals(True)
            roller["atemtechnik_check"].setChecked(bool(atem_selected or atem_active))
            roller["atemtechnik_check"].setVisible(False)
            roller["atemtechnik_check"].blockSignals(False)
        if roller.get("aktionen_box"):
            roller["aktionen_box"].setVisible(False)
        if "options_box" in roller:
            roller["options_box"].setVisible(False)
        if präz > 0 and "präzision_label" in roller:
            roller["präzision_label"].setText(
                f"Präzision aktiv: +{präz} GE TP werden verrechnet."
            )
            roller["präzision_label"].setVisible(True)
        # Auflaufen: GS-Eingabe zeigen (bei Riposte nicht)
        if "auflaufen_gs_spin" in roller:
            roller["auflaufen_gs_spin"].setVisible(auflaufen)
            roller["auflaufen_gs_label"].setVisible(auflaufen)
        if notes:
            roller["label_result"].setText("Manöver: " + " · ".join(notes))
        if auflaufen:
            roller["label_probe"].setText(
                f"<h3>Auflaufen lassen: {wname} ({tp}) + Gegner-GS</h3>"
            )
        elif riposte:
            roller["label_probe"].setText(
                f"<h3>Riposte: {wname} ({tp})</h3>"
            )
        else:
            roller["label_probe"].setText(f"<h3>Schaden: {wname} ({tp})</h3>")

    def update_einschraenkungen_ignorieren(self):
        if self.currentlyLoading: return
        Wolke.Char.dicePlugin_wunden_ignorieren = self.checkEinschraenkungenIgnorieren.isChecked()
        self.load_einschraenkungen()
        self.modified.emit()

    def _on_wunden_modus_changed(self, index):
        if self.currentlyLoading:
            return
        Wolke.Char.dicePlugin_wunden_modus = int(index)
        # Bei Moduswechsel Wunden zurücksetzen (wie im Master Plugin)
        Wolke.Char.dicePlugin_wunden = [None] * 8
        self.load_einschraenkungen()
        self.modified.emit()

    def wunde_clicked(self, index):
        if self.currentlyLoading:
            return
        wunden = list(getattr(Wolke.Char, "dicePlugin_wunden", [None] * 8))
        while len(wunden) < 8:
            wunden.append(None)
        current = wunden[index]
        mode = int(getattr(Wolke.Char, "dicePlugin_wunden_modus", 0) or 0)
        if mode == 0:
            new_val = "/" if current is None else ("X" if current == "/" else None)
        elif mode == 1:
            if current is None:
                new_val = "/"
            elif current == "/":
                new_val = "I"
            elif current == "I":
                new_val = "II"
            else:
                new_val = None
        else:  # Koloss II
            cycle = [None, "/", "I", "II", "III", "IV"]
            try:
                idx = cycle.index(current)
                new_val = cycle[idx + 1] if idx + 1 < len(cycle) else None
            except ValueError:
                new_val = "/"
        wunden[index] = new_val
        rank = {None: 0, "/": 1, "I": 2, "II": 3, "III": 4, "IV": 5, "X": 6}
        wunden.sort(key=lambda x: rank.get(x, 0), reverse=True)
        Wolke.Char.dicePlugin_wunden = wunden
        self.load_einschraenkungen()
        self.modified.emit()
        # Einzelklicks zählen NICHT als Source für vorzeitige Timer

    def _modal_add_einschraenkungen(self):
        """Mehrere Erschöpfungen/Wunden in einer Source (für vorzeitige Timer)."""
        dlg = QDialog(self.form)
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
        mode = int(getattr(Wolke.Char, "dicePlugin_wunden_modus", 0) or 0)
        cur = list(getattr(Wolke.Char, "dicePlugin_wunden", [None] * 8))
        new_w, de, dw = apply_wounds_batch(cur, n_e, n_w, mode)
        Wolke.Char.dicePlugin_wunden = new_w
        self.load_einschraenkungen()
        self._apply_premature_from_source(de, dw, source_id=f"modal:{new_id()}")
        self.modified.emit()

    def _show_top_info(self, title, text):
        """
        Hinweis-Popup: Titel = Effektname, blockiert Sephrasto nicht.
        """
        name = (title or "Hinweis").strip() or "Hinweis"
        body = (text or "").strip()
        # Name immer sichtbar: im Fenstertitel und ggf. in der Nachricht
        if body and name not in body and f"„{name}“" not in body:
            body = f"<b>{name}</b><br><br>{body}"
        elif not body:
            body = name

        # Nicht-modal, mit Parent, ohne StaysOnTop – schließbar und bedienbar
        box = QMessageBox(self.form)
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
        self._info_boxes = [b for b in self._info_boxes if b is not None]
        self._info_boxes.append(box)

    def _apply_premature_from_source(self, delta_ersch, delta_wunden, source_id=""):
        # Korrekter Speicherkey: dicePlugin_effekte (nicht ..._effects)
        effects = self._get_effects()
        # Zuerst Info-Bedingungen (Timer bleibt)
        for m in check_condition_info(effects, delta_ersch, delta_wunden, source_id):
            self._show_top_info(m.get("name") or "Hinweis", m.get("message") or "")
        msgs = check_premature_timers(effects, delta_ersch, delta_wunden, source_id)
        if not msgs:
            self._set_effects(effects)  # falls normalize geändert hat
            return
        # Atemtechnik-Regel: vorzeitig → trotzdem 1 Erschöpfung (on_end)
        end_events = []
        kept = []
        for e in effects:
            if e.get("premature_fired") and int(e.get("duration", 0) or 0) <= 0:
                # spezielles Ende: Erschöpfung bei Atemtechnik
                name = (e.get("name") or "").lower()
                if name.startswith("atemtechnik") or e.get("on_end") == "erschöpfung":
                    end_events.append({
                        "type": "erschöpfung",
                        "message": (e.get("premature_interrupt_text")
                                    or "Atemtechnik endet → 1 Erschöpfung."),
                    })
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
        self._refresh_aktionen_checkboxes()
        # Erschöpfung ohne rekursives premature auf denselben Effekt
        for ev in end_events:
            # add_erschopfung triggert premature erneut – ok für andere Effekte
            self.add_erschopfung()
            self._show_top_info("Effekt beendet", ev.get("message") or "")

    def update_ressourcen(self):
        if self.currentlyLoading: return
        Wolke.Char.dicePlugin_schips = self.spinSchips.value(); Wolke.Char.dicePlugin_geld = {'Dukaten': self.spinDukaten.value(), 'Silber': self.spinSilber.value(), 'Heller': self.spinHeller.value(), 'Kreuzer': self.spinKreuzer.value()}; self.modified.emit()
    
    def update_kleidung(self):
        if self.currentlyLoading: return
        Wolke.Char.dicePlugin_kleidung = self.textKleidung.toPlainText(); self.modified.emit()

    def _add_container_widgets(self, index, container_data):
        widget = QWidget(); layout = QHBoxLayout(widget); layout.setContentsMargins(4, 2, 4, 2); layout.setSpacing(5)
        move_buttons_layout = QVBoxLayout(); move_buttons_layout.setSpacing(0)
        up_button = QToolButton(); up_button.setArrowType(Qt.ArrowType.UpArrow); up_button.clicked.connect(lambda _, i=index: self.move_container(i, -1))
        down_button = QToolButton(); down_button.setArrowType(Qt.ArrowType.DownArrow); down_button.clicked.connect(lambda _, i=index: self.move_container(i, 1))
        move_buttons_layout.addWidget(up_button); move_buttons_layout.addWidget(down_button)
        label = QLabel(container_data["name"]); layout.addLayout(move_buttons_layout); layout.addWidget(label); layout.addStretch()
        item = QListWidgetItem(); item.setSizeHint(widget.sizeHint())
        self.listContainers.addItem(item); self.listContainers.setItemWidget(item, widget)
        text_edit = QPlainTextEdit(); text_edit.setPlainText(container_data.get("inhalt", "")); text_edit.textChanged.connect(self.container_inhalt_geaendert)
        self.stackedContainerInhalt.addWidget(text_edit); self.container_text_edits.append(text_edit)

    def add_container(self):
        Wolke.Char.dicePlugin_inventar.append({"name": "Neuer Behälter", "inhalt": ""}); self.load_inventar(); self.listContainers.setCurrentRow(self.listContainers.count() - 1); self.modified.emit()

    def remove_container(self):
        row = self.listContainers.currentRow()
        if row != -1: del Wolke.Char.dicePlugin_inventar[row]; self.load_inventar(); self.modified.emit()

    def move_container(self, index, direction):
        inv = Wolke.Char.dicePlugin_inventar; new_index = index + direction
        if new_index < 0 or new_index >= len(inv): return
        inv[index], inv[new_index] = inv[new_index], inv[index]
        self.load_inventar(); self.listContainers.setCurrentRow(new_index); self.modified.emit()

    def container_doppelgeklickt(self, item):
        row = self.listContainers.row(item);
        if row == -1: return
        container = Wolke.Char.dicePlugin_inventar[row]
        new_name, ok = QInputDialog.getText(self.form, "Behälter umbenennen", "Neuer Name:", QLineEdit.EchoMode.Normal, container["name"])
        if ok and new_name:
            container["name"] = new_name; widget = self.listContainers.itemWidget(item)
            if widget: widget.findChild(QLabel).setText(new_name)
            self.modified.emit()

    def container_gewechselt(self, current, previous):
        if current: self.stackedContainerInhalt.setCurrentIndex(self.listContainers.row(current))

    def container_inhalt_geaendert(self):
        if self.currentlyLoading: return
        row = self.stackedContainerInhalt.currentIndex()
        if row != -1 and row < len(Wolke.Char.dicePlugin_inventar): Wolke.Char.dicePlugin_inventar[row]["inhalt"] = self.container_text_edits[row].toPlainText(); self.modified.emit()

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
        tagebuch = Wolke.Char.dicePlugin_tagebuch; new_index = index + direction
        if new_index < 0 or new_index >= len(tagebuch): return
        tagebuch[index], tagebuch[new_index] = tagebuch[new_index], tagebuch[index]
        self.load_tagebuch(); self.listThemen.setCurrentRow(new_index); self.modified.emit()

    def add_thema(self):
        Wolke.Char.dicePlugin_tagebuch.append({"titel": "Neues Thema", "inhalt": ""}); self.load_tagebuch(); self.listThemen.setCurrentRow(self.listThemen.count() - 1); self.modified.emit()
        
    def remove_thema(self):
        row = self.listThemen.currentRow()
        if row != -1: del Wolke.Char.dicePlugin_tagebuch[row]; self.load_tagebuch(); self.modified.emit()

    def thema_doppelgeklickt(self, item):
        row = self.listThemen.row(item)
        if row == -1: return
        thema = Wolke.Char.dicePlugin_tagebuch[row]
        new_title, ok = QInputDialog.getText(self.form, "Thema umbenennen", "Neuer Titel:", QLineEdit.EchoMode.Normal, thema["titel"])
        if ok and new_title:
            thema["titel"] = new_title; widget = self.listThemen.itemWidget(item)
            if widget: widget.findChild(QLabel).setText(new_title)
            self.modified.emit()

    def thema_gewechselt(self, current, previous):
        if current: self.stackedThemaInhalt.setCurrentIndex(self.listThemen.row(current))

    def thema_inhalt_geaendert(self):
        if self.currentlyLoading: return
        row = self.stackedThemaInhalt.currentIndex()
        if row != -1 and row < len(Wolke.Char.dicePlugin_tagebuch): Wolke.Char.dicePlugin_tagebuch[row]["inhalt"] = self.thema_text_edits[row].toPlainText(); self.modified.emit()

    def _create_kampf_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_widget = QScrollArea(); left_widget.setWidgetResizable(True)
        content_widget = QWidget(); left_widget.setWidget(content_widget)
        content_layout = QVBoxLayout(content_widget); content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        abgeleitete_box = QGroupBox("Abgeleitete Kampfwerte"); abgeleitete_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        abgeleitete_layout = QHBoxLayout(abgeleitete_box)
        self.kampf_ws_label = QLabel("<b>WS:</b> -"); self.kampf_ws_stern_label = QLabel("<b>WS*:</b> -"); self.kampf_gs_stern_label = QLabel("<b>GS*:</b> -"); self.kampf_dh_stern_label = QLabel("<b>DH*:</b> -"); self.kampf_ini_label = QLabel("<b>INI:</b> -")
        abgeleitete_layout.addWidget(self.kampf_ws_label); abgeleitete_layout.addWidget(self.kampf_ws_stern_label); abgeleitete_layout.addWidget(self.kampf_gs_stern_label); abgeleitete_layout.addWidget(self.kampf_dh_stern_label); abgeleitete_layout.addWidget(self.kampf_ini_label); abgeleitete_layout.addStretch(); content_layout.addWidget(abgeleitete_box)
        ruestung_box = QGroupBox("Rüstung"); ruestung_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.kampf_ruestung_layout = QVBoxLayout(ruestung_box); content_layout.addWidget(ruestung_box)
        waffen_box = QGroupBox("Waffen"); self.kampf_waffen_layout = QGridLayout(waffen_box); self.kampf_waffen_layout.setColumnStretch(4, 1)
        headers = ["Name", "TP", "RW", "WM/LZ", "Eigenschaften", "AT", "VT", "TP*"]
        for i, header in enumerate(headers): self.kampf_waffen_layout.addWidget(QLabel(f"<b>{header}</b>"), 0, i)
        content_layout.addWidget(waffen_box)

        munition_box = QGroupBox("Munition")
        mun_outer = QVBoxLayout(munition_box)
        self.kampf_munition_layout = QGridLayout()
        headers_m = ["", "Name", "Anz.", "TP", "RW", "LZ", "Eigenschaften", ""]
        for i, header in enumerate(headers_m):
            self.kampf_munition_layout.addWidget(QLabel(f"<b>{header}</b>"), 0, i)
        mun_outer.addLayout(self.kampf_munition_layout)
        mun_btns = QHBoxLayout()
        self.btn_add_munition = QPushButton("Hinzufügen")
        self.btn_add_munition.setToolTip("Neue Munition anlegen")
        self.btn_add_munition.clicked.connect(self._add_munition)
        mun_btns.addWidget(self.btn_add_munition)
        mun_btns.addStretch()
        mun_outer.addLayout(mun_btns)
        content_layout.addWidget(munition_box)
        
        content_layout.addStretch()
        self.kampf_dice_roller = self._create_dice_roll_widget()
        
        self.kampf_stack = QStackedWidget()
        self.kampf_dice_roller_index = self.kampf_stack.addWidget(self.kampf_dice_roller["widget"])
        # Legacy-Indizes beibehalten (falls noch referenziert)
        self.nah_manöver_browser = QTextBrowser()
        self.nah_manöver_index = self.kampf_stack.addWidget(self.nah_manöver_browser)
        self.fern_manöver_browser = QTextBrowser()
        self.fern_manöver_index = self.kampf_stack.addWidget(self.fern_manöver_browser)
        
        splitter.addWidget(left_widget); splitter.addWidget(self.kampf_stack); splitter.setSizes([550, 450])
        main_layout.addWidget(splitter)
        return tab

    def load_kampf_tab(self):
        abgeleitete = Wolke.Char.abgeleiteteWerte
        self.kampf_ws_label.setText(f"<b>WS:</b> {abgeleitete.get('WS', type('obj', (object,), {'wert': '-'})).wert}")
        self.kampf_ws_stern_label.setText(f"<b>WS*:</b> {abgeleitete.get('WS', type('obj', (object,), {'finalwert': '-'})).finalwert}")
        self.kampf_gs_stern_label.setText(f"<b>GS*:</b> {abgeleitete.get('GS', type('obj', (object,), {'finalwert': '-'})).finalwert}")
        self.kampf_dh_stern_label.setText(f"<b>DH*:</b> {abgeleitete.get('DH', type('obj', (object,), {'finalwert': '-'})).finalwert}")
        self.kampf_ini_label.setText(f"<b>INI:</b> {abgeleitete.get('INI', type('obj', (object,), {'finalwert': '-'})).finalwert}")
        
        layout = self.kampf_ruestung_layout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        for ruestung in Wolke.Char.rüstung:
            if not ruestung.name: continue
            rs = ruestung.getRSFinal(abgeleitete); be = ruestung.getBEFinal(abgeleitete); ws = ruestung.getWSFinal(abgeleitete)
            layout.addWidget(QLabel(f"{ruestung.name} (RS: {rs} | BE: {be} | WS*: {ws})"))

        layout = self.kampf_waffen_layout
        for i in reversed(range(1, layout.rowCount())):
            for j in range(layout.columnCount()):
                item = layout.itemAtPosition(i, j)
                if item and item.widget(): item.widget().deleteLater()
        row = 1
        for waffe in Wolke.Char.waffen:
            if not waffe.name: continue
            layout.addWidget(QLabel(waffe.anzeigename), row, 0)
            tp_str = f"{waffe.würfel}W{waffe.würfelSeiten}{'+' if waffe.plus >= 0 else ''}{waffe.plus}"
            layout.addWidget(QLabel(tp_str), row, 1)
            layout.addWidget(QLabel(str(waffe.rwFinal)), row, 2)
            wm_lz = f"{waffe.wm}" + (f" / {waffe.lzFinal}" if waffe.fernkampf else "")
            layout.addWidget(QLabel(wm_lz), row, 3)
            eig_label = QLabel(", ".join(waffe.eigenschaften)); eig_label.setWordWrap(True); layout.addWidget(eig_label, row, 4)
            tp_stern_str = f"{waffe.würfelFinal}W{waffe.würfelSeiten}{'+' if waffe.plusFinal >= 0 else ''}{waffe.plusFinal}"
            at_button = QPushButton(f"{waffe.at} 🎲"); at_button.clicked.connect(partial(self.prepare_at_with_tp, waffe.anzeigename, waffe.at, tp_stern_str)); at_button.setFlat(True); layout.addWidget(at_button, row, 5)
            is_fk_w = bool(getattr(waffe, "fernkampf", False))
            if is_fk_w:
                vt_placeholder = QLabel("–")
                vt_placeholder.setToolTip("Fernkampfwaffen haben keine VT")
                vt_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(vt_placeholder, row, 6)
            else:
                vt_button = QPushButton(f"{waffe.vt} 🎲")
                vt_button.clicked.connect(
                    partial(self.prepare_vt_with_tp, waffe.anzeigename, waffe.vt, tp_stern_str)
                )
                vt_button.setFlat(True)
                layout.addWidget(vt_button, row, 6)
            tp_button = QPushButton(f"{tp_stern_str} 🎲"); tp_button.clicked.connect(partial(self.prepare_dice_roll, f"TP* ({tp_stern_str})", 0, True, tp_stern_str)); tp_button.setFlat(True); layout.addWidget(tp_button, row, 7)
            row += 1
        
        self._rebuild_munition_ui()
        self.kampf_stack.setCurrentIndex(self.kampf_dice_roller_index)

    def show_nahkampf_manöver(self):
        self.kampf_stack.setCurrentIndex(self.nah_manöver_index)
        html_text = """
<h2>Nahkampfmanöver</h2>
<p>Zur besseren Übersicht haben wir die hier aufgeführten Nahkampfmanöver (Fernkampfmanöver siehe S. 46) aufgeteilt: Basismanöver kannst du jederzeit durchführen, während eingeschränkte Basismanöver eine bestimmte Situation oder Waffe erfordern und aufbauende Manöver sogar einen bestimmten Vorteil voraussetzen. Trotzdem sind alle Manöver miteinander kombinierbar, solange der gesunde Menschenverstand oder der Spielleiter das nicht ausschließen.</p>
<h3>Basismanöver</h3>
<p>Ausweichen (VT –2–BE)<br>Wirkung: Der Verteidiger entgeht dem Angriff und seinen Auswirkungen vollständig. Ausweichen ist die sinnvollste waffenlose Verteidigung gegen Bewaffnete (siehe Waffeneigenschaft Zerbrechlich auf S. 47).</p>
<p>Binden (VT –X)<br>Wirkung: Bis zum Ende der nächsten eigenen Initiativephase sind alle Verteidigungen des Gegners um –X (maximal 8) erschwert.</p>
<p>Entfernung verändern (AT –BE)<br>Wirkung: Du kannst dich aus dem Nahkampf lösen, ohne Passierschläge zu riskieren.<br>Besonderheiten: Beim Spiel mit Bodenplänen erhält das Ziel in dieser Runde keine Passierschläge durch deine Bewegung.</p>
<p>Entwaffnen (AT –4 oder VT –4)<br>Gegenprobe: KK<br>Wirkung: Dem Ziel wird eine Waffe deiner Wahl entrissen, die danach zwischen den Kämpfern am Boden liegt. Das Aufheben der Waffe benötigt eine Aktion Konflikt; falls ein anderer Kämpfer das in einer Reaktion verhindern möchte, ist zusätzlich eine vergleichende GE-Probe (I) notwendig. Das Manöver senkt den Schaden des Angriffes auf 0. Sollte der Angriff ohnehin keinen Schaden anrichten – etwa durch andere Manöver – ist das Manöver nicht möglich.</p>
<p>Optional: Gezielter Schlag (AT –2)<br>Wirkung: Du bestimmst, an welcher Trefferzone (S. 33) du den Gegner triffst. Nur beim Spiel mit Trefferzonen.</p>
<p>Umreißen (AT)<br>Gegenprobe: GE oder (für große und sehr große Gegner) KO <br>Wirkung: Dein Ziel stürzt und liegt am Boden. Das Manöver senkt den Schaden des Angriffes auf 0. Sollte der Angriff ohnehin keinen Schaden anrichten, ist das Manöver nicht möglich.</p>
<p>Wuchtschlag (AT –X)<br>Wirkung: Der Angriff richtet X (maximal 8) TP mehr an.</p>
<h3>Eingeschränkte Basismanöver</h3>
<p>Auflaufen lassen (VT –4)<br>Wirkung: Der Verteidiger fügt dem Angreifer seinen Waffenschaden plus die GS des Angreifers zu. <br>Voraussetzungen: größere Reichweite; Gegner kombiniert die Aktionen Bewegung und Konflikt, die Bewegung muss dabei vor dem Angriff ausgeführt werden.</p>
<p>Rüstungsbrecher (AT –4)<br>Wirkung: Der Angriff richtet SP statt TP an. <br>Voraussetzung: Waffeneigenschaft Rüstungsbrechend<br>Anmerkung: Das Manöver lohnt sich, wenn der Gegner schwere Rüstung trägt oder du mehrere Wunden anrichten kannst.</p>
<p>Schildspalter (AT +2)<br>Wirkung: Du fügst dem Schild deines Gegners deinen Waffenschaden zu.<br>Voraussetzung: Gegner führt Schild</p>
<p>Stumpfer Schlag (AT)<br>Wirkung: Der Angriff verursacht Erschöpfung statt Wunden. Wird das Ziel kampfunfähig, erleidet es keine Blutung. <br>Voraussetzung: Waffeneigenschaft Stumpf</p>
<p>Umklammern (AT –X)<br>Wirkung: Handlungen des Umklammerten sind um –X erschwert und seine GS sinkt auf 0, solange die Umklammerung anhält. Bei mehrfachen Umklammerungen summieren sich die Malusse. Du kannst dein Ziel in einer Freien Aktion loslassen. Der Umklammerte kann eine Aktion Konflikt aufwenden und eine vergleichenden GE-oder KK-Probe (I) gegen die GE oder KK des Umklammernden ablegen. Gelingt die Probe, lässt der Umklammernde sofort los. Das Manöver senkt den Schaden des Angriffes auf 0. Sollte der Angriff ohnehin keinen Schaden anrichten, ist das Manöver nicht möglich. <br>Voraussetzungen: Angriff mit beiden Händen im waffenlosen Kampf; Ziel darf nicht einer höheren Größenklasse angehören</p>
<h3>Aufbauende Manöver</h3>
<p>Ausfall (AT –2–BE)<br>Wirkung: Das Ziel muss in einer Freien Reaktion bis zu 2 Schritt zurückweichen, du folgst in einer Freien Aktion. Möchte es in seiner nächsten Initiativephase einen anderen Gegner als dich angreifen, darfst du einen Passierschlag ausführen. <br>Voraussetzung: Vorteil Ausfall</p>
<p>Befreiungsschlag (AT –4)<br>Wirkung: Du führst eine Attacke aus, die sich (samt anderen Manövern) gegen alle Ziele in einem Winkel von 180° vor dir richtet. Jedem Ziel steht eine eigene Verteidigung zu.<br>Voraussetzungen: Vorteil Kraftvoller Kampf III und Kampf in diesem Stil; kein Befreiungsschlag seit letztem Beginn einer eigenen Initiativephase</p>
<p>Doppelangriff (zwei AT –4)<br>Wirkung: Du führst mit beiden Händen je eine Attacke –4 aus. Beide Angriffe sind unabhängig voneinander; sie werden separat ausgewürfelt, können sich gegen verschiedene Ziele richten und mit unterschiedlichen Manövern versehen werden.<br>Voraussetzungen: Vorteil Beidhändiger Kampf III und Kampf in diesem Stil; kein Doppelangriff seit letztem Beginn einer eigenen Initiativephase</p>
<p>Hammerschlag (AT –8)<br>Wirkung: Der Angriff richtet doppelten Waffenschaden an. Zusätzliche Trefferpunkte aus Kommandos, anderen Manövern usw. werden nicht verdoppelt. <br>Voraussetzung: Vorteil Hammerschlag</p>
<p>Klingentanz (AT –4)<br>Wirkung: Wenn der Angriff gelingt, darfst du sofort noch einmal angreifen. Dieser Folgeangriff ist nicht erschwert. <br>Besonderheit: Bei einer Kombination von Klingentanz und Befreiungsschlag muss jedes Ziel getroffen werden, damit der Klingentanz gelingt.<br>Voraussetzung: Vorteil Klingentanz; kein Klingentanz seit letztem Beginn einer eigenen Initiativephase</p>
<p>Todesstoß (AT –8)<br>Wirkung: Der Angriff richtet zwei zusätzliche Wunden an, auch wenn der Schaden zu gering ist, um Wunden anzurichten. <br>Voraussetzung: Vorteil Todesstoß</p>
<p>Überrennen (Bewegung und AT)<br>Wirkung: Das Reittier stürmt in die gegnerische Formation. Seine Attacke trifft (samt anderen Manövern) alle Gegner in seiner Bahn, bis es durch mindestens 2 erfolgreiche Verteidigungen gestoppt wird. Außerdem richtet die Attacke GS Trefferpunkte zusätzlich an. Die Kombination der Aktionen Bewegung und Konflikt ist nicht erschwert. <br>Voraussetzungen: Vorteil Reiterkampf III und Kampf in diesem Stil; GS Schritt Anlauf; Ziele sind in einer kleineren Größenklasse als das Reittier</p>
<p>Unterlaufen (VT –4)<br>Wirkung: Wenn die Verteidigung gelingt, darfst du in der nächsten eigenen Initiativephase eine Freie Aktion nutzen, um deinen Gegner (ein weiteres Mal) anzugreifen.<br>Voraussetzungen: Vorteil Schneller Kampf III und Kampf in diesem Stil; kein Unterlaufen seit letztem Beginn einer eigenen Initiativephase</p>
<p>Niederwerfen (AT –4)<br>Gegenprobe: KK<br>Wirkung: Dein Ziel stürzt und liegt am Boden.<br>Voraussetzung: Vorteil Niederwerfen</p>
<p>Riposte (VT –4)<br>Wirkung: Du fügst dem Angreifer den Waffenschaden deiner Waffe zu. Die Riposte ist kombinierbar mit Attackemanövern, die in diesem Fall die Verteidigung zusätzlich erschweren. Zum Beispiel wäre eine Kombination aus Riposte und Hammerschlag um –12 erschwert, würde aber doppelten Schaden anrichten.<br>Voraussetzung: Vorteil Parierwaffenkampf III und Kampf in diesem Stil; keine Riposte seit letztem Beginn einer eigenen Initiativephase</p>
<p>Schildwall (VT –4)<br>Wirkung: Du kannst einen Angriff auf einen benachbarten Verbündeten abwehren. Das Manöver erfolgt vor der Verteidigung des Verbündeten. <br>Voraussetzungen: Vorteil Schildkampf III und Kampf in diesem Stil; kein Schildwall seit letztem Beginn einer eigenen Initiativephase</p>
<p>Sturmangriff (Bewegung und AT)<br>Die Kombination der Aktionen Bewegung und Konflikt ist nicht erschwert. Außerdem richtet die nächste Attacke GS Trefferpunkte zusätzlich an. <br>Voraussetzungen: Vorteil Sturmangriff oder Reiterkampf I und Kampf in diesem Stil; die Bewegung muss vor dem Angriff ausgeführt werden.<br>Anmerkung: Sturzflugangriffe von fliegenden Gegnern folgen denselben Regeln. Bei besonders kleinen Gegnern oder kurzem Anlauf sollte der Spielleiter den Schaden verringern.</p>
"""
        self.nah_manöver_browser.setHtml(html_text)

    def show_fernkampf_manöver(self):
        self.kampf_stack.setCurrentIndex(self.fern_manöver_index)
        html_text = """
<h2>Modifikatoren im Fernkampf</h2>
<table border="1">
<tr><th>Größenklasse des Ziels</th><th></th></tr>
<tr><td>sehr groß (Elefant)</td><td>+8</td></tr>
<tr><td>groß (Pferd, Oger)</td><td>+4</td></tr>
<tr><td>mittel (Mensch, Zwerg)</td><td>0</td></tr>
<tr><td>klein (Wolf, Reh)</td><td>–4</td></tr>
<tr><td>sehr klein (Fasan, Hase)</td><td>–8</td></tr>
<tr><td>winzig (Maus)</td><td>–12</td></tr>
<tr><th>Umgebung</th><th></th></tr>
<tr><td>Dämmerung</td><td>–4</td></tr>
<tr><td>Mondlicht</td><td>–8</td></tr>
<tr><td>Sternenlicht</td><td>–16</td></tr>
<tr><td>Wind</td><td>–4</td></tr>
<tr><td>Sturm</td><td>–8</td></tr>
<tr><th>Bewegung</th><th></th></tr>
<tr><td>schnell (laufender Mensch)</td><td>–4</td></tr>
<tr><td>sehr schnell (Pferd)</td><td>–8</td></tr>
<tr><td>extrem schnell (Vogel)</td><td>–12</td></tr>
<tr><th>Sonstiges</th><th></th></tr>
<tr><td>halbe Deckung</td><td>–4</td></tr>
<tr><td>Dreivierteldeckung</td><td>–8</td></tr>
<tr><td>berittener Schütze</td><td>–4</td></tr>
</table>
<h2>Fernkampfmanöver</h2>
<p>Optional: Gezielter Schuss (FK –2)<br>Wirkung: Du bestimmst, an welcher Trefferzone (S. 33) du den Gegner triffst. Nur beim Spiel mit Trefferzonen.</p>
<p>Reichweite erhöhen (FK –4)<br>Wirkung: Die Reichweite deines Fernkampfangriffes verdoppelt sich. Kann bis zu zweimal pro FK eingesetzt werden.</p>
<p>Scharfschuss (FK –X)<br>Wirkung: Der Angriff richtet X (maximal 8) Trefferpunkte mehr an.</p>
<p>Zielen (FK +2)<br>Wirkung: Erhöht die Vorbereitungszeit um 1 Aktion. Ruhige Hand (S. 42) verdoppelt den Bonus.</p>
<p>Meisterschuss (FK –8)<br>Wirkung: Der Angriff richtet zwei zusätzliche Wunden an – auch wenn der Schaden zu gering ist, um eine Wunde anzurichten. <br>Voraussetzung: Vorteil Meisterschuss</p>
<p>Rüstungsbrecher (FK –4)<br>Wirkung: Der Angriff ignoriert die gegnerische Rüstung und richtet SP statt TP an.<br>Voraussetzung: panzerbrechender Pfeil/Bolzen (Panzerbrechender Pfeil erfordert)</p>
<p>Schnellschuss (FK –4)<br>Wirkung: Verkürzt die Vorbereitungszeit um die Hälfte. Eine Vorbereitungszeit von 1 Aktion wird zu 0 Aktionen. Die Aktion Konflikt ist von dieser Modifikation nicht betroffen. Kann bis zu zweimal pro FK eingesetzt werden.<br>Voraussetzung: Vorteil Schnellziehen</p>
"""
        self.fern_manöver_browser.setHtml(html_text)

    def _create_vorteile_tab(self):
        tab = QWidget()
        self.vorteile_ui = UI.CharakterVorteile.Ui_Form()
        self.vorteile_ui.setupUi(tab)
        self.vorteile_treeWidget = self.vorteile_ui.treeWidget; self.vorteile_plainText = self.vorteile_ui.plainText; self.vorteile_labelVorteil = self.vorteile_ui.labelVorteil; self.vorteile_labelTyp = self.vorteile_ui.labelTyp; self.vorteile_labelKosten = self.vorteile_ui.labelKosten; self.vorteile_labelNachkauf = self.vorteile_ui.labelNachkauf; self.vorteile_labelVoraussetzungen = self.vorteile_ui.labelVoraussetzungen; self.vorteile_vlQuerverweise = self.vorteile_ui.vlQuerverweise
        self.vorteile_ui.buttonExpandToggle.hide(); self.vorteile_ui.nameFilterEdit.hide(); self.vorteile_ui.labelFilter.hide()
        self.vorteile_treeWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection); self.vorteile_treeWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.vorteile_treeWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.vorteile_treeWidget.setAlternatingRowColors(True)
        self.vorteile_treeWidget.headerItem().setText(0, "Vorteil"); self.vorteile_treeWidget.headerItem().setText(1, "Kosten"); self.vorteile_treeWidget.headerItem().setText(2, "")
        self.vorteile_treeWidget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch); self.vorteile_treeWidget.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed); self.vorteile_treeWidget.header().resizeSection(1, Hilfsmethoden.emToPixels(10)); self.vorteile_treeWidget.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed); self.vorteile_treeWidget.header().resizeSection(2, 0)
        self.vorteile_treeWidget.itemSelectionChanged.connect(self._vorteil_selected_in_plugin_tab)
        return tab

    def load_vorteile_tab(self):
        self.vorteile_treeWidget.blockSignals(True); self.vorteile_treeWidget.clear()
        vorteile_by_kategorie = SortedCategoryToListDict(Wolke.DB.einstellungen["Vorteile: Kategorien"].wert)
        for vorteil_name in sorted(Wolke.Char.vorteile.keys()):
            if vorteil_name in Wolke.DB.vorteile: vorteile_by_kategorie.append(Wolke.DB.vorteile[vorteil_name].kategorie, vorteil_name)
        vorteile_by_kategorie.sortValues()
        font = QFont(); font.setBold(True); font.setCapitalization(QFont.Capitalization.SmallCaps); font.setPointSize(Wolke.FontHeadingSizeL3)
        for kategorie_name, vorteil_names_in_kategorie in vorteile_by_kategorie.items():
            if not vorteil_names_in_kategorie: continue
            parent_item = QTreeWidgetItem(self.vorteile_treeWidget, [kategorie_name, ""]); parent_item.setExpanded(True); parent_item.setFont(0, font)
            for vorteil_name in vorteil_names_in_kategorie:
                vorteil_char_data = Wolke.Char.vorteile[vorteil_name]
                display_name = vorteil_char_data.anzeigenameExt if hasattr(vorteil_char_data, 'anzeigenameExt') else vorteil_name
                QTreeWidgetItem(parent_item, [display_name, f"{vorteil_char_data.kosten} EP"])
        self.vorteile_treeWidget.blockSignals(False)
        if self.vorteile_treeWidget.topLevelItemCount() > 0 and self.vorteile_treeWidget.topLevelItem(0).childCount() > 0:
            self.vorteile_treeWidget.setCurrentItem(self.vorteile_treeWidget.topLevelItem(0).child(0))
        self._vorteil_selected_in_plugin_tab()

    def _vorteil_selected_in_plugin_tab(self):
        selected_items = self.vorteile_treeWidget.selectedItems()
        if not selected_items or selected_items[0].parent() is None:
            self.vorteile_plainText.setText(""); return
        vorteil_name_in_tree = selected_items[0].text(0)
        found_original_name = next((name for name, vort in Wolke.Char.vorteile.items() if (hasattr(vort, 'anzeigenameExt') and vort.anzeigenameExt == vorteil_name_in_tree) or (name == vorteil_name_in_tree)), None)
        if not found_original_name or found_original_name not in Wolke.DB.vorteile: return
        vorteil_char = Wolke.Char.vorteile[found_original_name]; vorteil_db = Wolke.DB.vorteile[found_original_name]
        self.vorteile_labelVorteil.setText(vorteil_name_in_tree); self.vorteile_labelTyp.setText(vorteil_db.kategorieName(Wolke.DB)); self.vorteile_labelNachkauf.setText(vorteil_db.nachkauf)
        voraussetzungen_text = vorteil_char.voraussetzungen.anzeigetext(Wolke.DB) if hasattr(vorteil_char, 'voraussetzungen') else vorteil_db.voraussetzungen.anzeigetext(Wolke.DB)
        self.vorteile_labelVoraussetzungen.setText(voraussetzungen_text or "keine")
        self.vorteile_labelKosten.setText(f"{vorteil_char.kosten} EP")
        beschreibung = vorteil_db.text
        if vorteil_db.bedingungen: beschreibung = f"<i>Bedingungen</i>: {vorteil_db.bedingungen}<br><br>" + beschreibung
        if vorteil_db.info: beschreibung += f"<br><br><b>Sephrasto-Hinweis</b>: {vorteil_db.info}"
        if vorteil_char.kommentar: beschreibung += f"<br><br><i>Kommentar</i>: {vorteil_char.kommentar}"
        self.vorteile_plainText.setText(Hilfsmethoden.fixHtml(beschreibung))
        
        for qv_key in self.vorteile_qvSlots:
            self.vorteile_qvTexts[qv_key].sizeChanged.disconnect(self.vorteile_qvSlots[qv_key])
        self.vorteile_qvSlots = {}
        self.vorteile_qvTexts = {}
        self.vorteile_qvSections = {}

        for i in reversed(range(self.vorteile_vlQuerverweise.count())):
            widget = self.vorteile_vlQuerverweise.itemAt(i).widget()
            widget.setParent(None)
            del widget

        if len(vorteil_db.querverweiseResolved) > 0:
            header = QLabel()
            header.setText("Querverweise:")
            self.vorteile_vlQuerverweise.addWidget(header)

            for qv in vorteil_db.querverweiseResolved:
                section = Section(qv)
                self.vorteile_qvSections[qv] = section
                contentLayout = QVBoxLayout()
                contentLayout.setContentsMargins(0, 0, 0, 0)
                qvText = AutoResizingTextBrowser()
                self.vorteile_qvTexts[qv] = qvText
                qvText.setText(Hilfsmethoden.fixHtml(vorteil_db.querverweiseResolved[qv]))
                self.vorteile_qvSlots[qv] = partial(self._update_qv_section_height, qv=qv)
                qvText.sizeChanged.connect(self.vorteile_qvSlots[qv])
                contentLayout.addWidget(qvText)
                section.setContentLayout(contentLayout)
                self.vorteile_vlQuerverweise.addWidget(section)

    def _update_qv_section_height(self, width, height, qv):
        if qv in self.vorteile_qvSections:
            self.vorteile_qvSections[qv].updateHeight(height, True)