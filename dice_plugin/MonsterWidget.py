# -*- coding: utf-8 -*-
"""
MonsterWidget – erbt NSC (Fertigkeiten, Vorteile, Übernatürliches, Kampf),
ergänzt Klasse/Größe/Typ, Kreatureneigenschaften mit Parametern, Manöver-Freigabe.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
    QComboBox, QCheckBox, QScrollArea, QFrame, QDialog, QDialogButtonBox,
    QPushButton, QLineEdit, QSizePolicy,
)

from MonsterHelper import (
    load_monster_katalog, manöver_ids_mit_vorteil_req, icon_path_for_klasse, klasse_by_id,
)
from EffectsHelper import MANOEVER, manöver_label


def _wrap_tooltip(text: str) -> str:
    """Lange Tooltips als HTML mit Zeilenumbruechen."""
    if not text:
        return ""
    t = text.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = t.replace(chr(10), "<br>")
    return t


class WeaponEigenschaftPicker(QDialog):
    """Standard- + Kreaturen-Waffeneigenschaften → kommagetrennter Text."""

    def __init__(self, current_text: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Waffeneigenschaften (Angriff)")
        self.setMinimumSize(520, 480)
        lay = QVBoxLayout(self)

        info = QLabel(
            "Standard-Eigenschaften (S. 47) und Kreaturen-Eigenschaften\n"
            "(Flächenangriff, Erfrieren, Ertränken, …)."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #555;")
        lay.addWidget(info)

        current = {x.strip().lower() for x in (current_text or "").split(",") if x.strip()}
        props = load_monster_katalog().get("waffeneigenschaften") or []

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        host = QWidget()
        grid = QGridLayout(host)
        grid.setContentsMargins(4, 4, 4, 4)
        self._checks = []
        row = 0
        last_kat = None
        for p in props:
            kat_name = p.get("kategorie") or "standard"
            if kat_name != last_kat:
                title = "Standard (Regelwerk)" if kat_name == "standard" else "Kreatur"
                grid.addWidget(QLabel(f"<b>{title}</b>"), row, 0, 1, 2)
                row += 1
                last_kat = kat_name
            name = p.get("name") or p.get("id") or ""
            cb = QCheckBox(name)
            tip = _wrap_tooltip(p.get("tooltip") or "")
            if tip:
                cb.setToolTip(tip)
            n, i = name.lower(), (p.get("id") or "").lower()
            if n in current or i in current:
                cb.setChecked(True)
            grid.addWidget(cb, row, 0, 1, 2)
            self._checks.append((cb, name))
            row += 1
        scroll.setWidget(host)
        lay.addWidget(scroll, 1)

        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        lay.addWidget(box)

    def selected_text(self) -> str:
        return ", ".join(name for cb, name in self._checks if cb.isChecked())


def build_monster_widget_class(NSCWidget):
    class MonsterWidget(NSCWidget):
        is_monster = True

        def _init_ui(self):
            super()._init_ui()
            self.is_monster = True
            self.data["kind"] = "monster"
            self.eigenschaft_checks = {}
            self.eigenschaft_params = {}  # eid -> QLineEdit
            self.manöver_freigabe_checks = {}

            try:
                self.edit_name.setPlaceholderText("Name des Monsters")
            except Exception:
                pass

            self._add_monster_badge()
            self._init_monster_meta_bar()
            # Fertigkeiten / Vorteile / Übernatürliches bleiben (nicht entfernen)
            self._init_monster_eigenschaften_tab()
            self._init_monster_manöver_tab()
            self._patch_kampf_for_monster()

        def _add_monster_badge(self):
            """Klassen-Icon/-Buchstabe direkt links neben dem Namen."""
            try:
                badge = QLabel("?")
                badge.setFixedSize(26, 26)
                badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                badge.setStyleSheet(
                    "QLabel { background:#5a3d1e; color:#fff; border-radius:4px; "
                    "font-weight:bold; font-size:12px; }"
                )
                # edit_name sitzt im Header – Icon davor
                parent = self.edit_name.parentWidget()
                lay = parent.layout() if parent is not None else None
                if lay is not None:
                    # Index von edit_name finden
                    idx = lay.indexOf(self.edit_name)
                    if idx < 0:
                        idx = 0
                    lay.insertWidget(idx, badge)
                else:
                    hl = self.header_frame.layout()
                    if hl is not None:
                        hl.insertWidget(3, badge)
                self._monster_badge = badge
                self.lbl_klasse_icon = badge  # gleiche Referenz für Updates
            except Exception:
                self._monster_badge = None

        def _init_monster_meta_bar(self):
            kat = load_monster_katalog()
            bar = QFrame()
            bar.setObjectName("monsterMeta")
            bar.setStyleSheet(
                "QFrame#monsterMeta { background: rgba(90,61,30,40); "
                "border: 1px solid rgba(90,61,30,80); border-radius: 4px; }"
            )
            lay = QHBoxLayout(bar)
            lay.setContentsMargins(8, 6, 8, 6)
            lay.setSpacing(8)

            # Klassen-Icon (ändert sich mit Auswahl)
            lay.addWidget(QLabel("<b>Klasse</b>"))
            self.combo_monster_klasse = QComboBox()
            for k in kat.get("klassen") or []:
                self.combo_monster_klasse.addItem(k["name"], k["id"])
                tip = _wrap_tooltip(k.get("beschreibung") or k.get("name") or "")
                self.combo_monster_klasse.setItemData(
                    self.combo_monster_klasse.count() - 1, tip, Qt.ItemDataRole.ToolTipRole
                )
            self.combo_monster_klasse.currentIndexChanged.connect(self._on_monster_klasse_changed)
            lay.addWidget(self.combo_monster_klasse, 1)

            lay.addWidget(QLabel("<b>Größe</b>"))
            self.combo_monster_groesse = QComboBox()
            for g in kat.get("groessen") or []:
                self.combo_monster_groesse.addItem(g["name"], g["id"])
                tip = _wrap_tooltip(g.get("tooltip") or "")
                if tip:
                    self.combo_monster_groesse.setItemData(
                        self.combo_monster_groesse.count() - 1, tip, Qt.ItemDataRole.ToolTipRole
                    )
            self.combo_monster_groesse.setToolTip(
                _wrap_tooltip((kat.get("hinweise") or {}).get("grosse_gegner") or "")
            )
            self.combo_monster_groesse.currentIndexChanged.connect(lambda *_: self.changed())
            lay.addWidget(self.combo_monster_groesse)

            lay.addWidget(QLabel("<b>Typ</b>"))
            self.combo_monster_typ = QComboBox()
            self.combo_monster_typ.addItem("Normal", "normal")
            self.combo_monster_typ.addItem("Schwarm", "schwarm")
            schw = _wrap_tooltip((kat.get("hinweise") or {}).get("schwarm") or "")
            self.combo_monster_typ.setItemData(1, schw, Qt.ItemDataRole.ToolTipRole)
            self.combo_monster_typ.setToolTip(schw or "Normal oder Schwarm")
            self.combo_monster_typ.currentIndexChanged.connect(self._on_monster_typ_changed)
            lay.addWidget(self.combo_monster_typ)

            try:
                idx = self.content_layout.indexOf(self.tabs)
                if idx < 0:
                    idx = max(0, self.content_layout.count() - 1)
                self.content_layout.insertWidget(idx, bar)
            except Exception:
                self.content_layout.insertWidget(0, bar)
            self._monster_meta_bar = bar

        def _init_monster_eigenschaften_tab(self):
            kat = load_monster_katalog()
            tab = QWidget()
            outer = QVBoxLayout(tab)
            outer.setContentsMargins(4, 4, 4, 4)

            info = QLabel(
                "Kreatureneigenschaften. Bei parametrisierten Einträgen "
                "(Resistenz, Verwundbarkeit, Empfindlichkeit, Immunität, Aura, Explosion) "
                "bitte den Wert im Textfeld angeben. Hover = voller Regeltext."
            )
            info.setWordWrap(True)
            info.setStyleSheet("color:#555; font-style:italic;")
            outer.addWidget(info)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            host = QWidget()
            grid = QGridLayout(host)
            grid.setContentsMargins(2, 2, 2, 2)
            grid.setHorizontalSpacing(6)
            grid.setVerticalSpacing(3)

            self.eigenschaft_checks = {}
            self.eigenschaft_params = {}
            row = 0
            for e in kat.get("eigenschaften") or []:
                eid = e.get("id") or ""
                cb = QCheckBox(e.get("name") or eid)
                tip = _wrap_tooltip(e.get("tooltip") or "")
                if tip:
                    cb.setToolTip(tip)
                cb.stateChanged.connect(self._on_eigenschaft_changed)
                grid.addWidget(cb, row, 0)
                self.eigenschaft_checks[eid] = cb

                if e.get("needs_param"):
                    ed = QLineEdit()
                    ed.setPlaceholderText(e.get("param_label") or "Parameter")
                    ed.setMinimumWidth(140)
                    extra = _wrap_tooltip(e.get("param_extra_tooltip") or "")
                    if extra:
                        ed.setToolTip(extra)
                    elif tip:
                        ed.setToolTip(tip)
                    ed.textChanged.connect(self._on_eigenschaft_changed)
                    ed.setEnabled(False)
                    def _toggle(state, line=ed):
                        try:
                            on = int(state) == 2 or state == Qt.CheckState.Checked
                        except Exception:
                            on = bool(state)
                        line.setEnabled(bool(on))
                    cb.stateChanged.connect(_toggle)
                    grid.addWidget(ed, row, 1)
                    self.eigenschaft_params[eid] = ed
                else:
                    grid.addWidget(QLabel(""), row, 1)

                row += 1

            grid.setColumnStretch(1, 1)
            scroll.setWidget(host)
            outer.addWidget(scroll, 1)

            # Nach Attribute einfügen
            insert = 1
            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == "Attribute":
                    insert = i + 1
                    break
            self.tabs.insertTab(insert, tab, "Eigenschaften")

        def _init_monster_manöver_tab(self):
            tab = QWidget()
            outer = QVBoxLayout(tab)
            outer.setContentsMargins(4, 4, 4, 4)
            info = QLabel(
                "Manöver freigeben, die normalerweise einen Vorteil brauchen\n"
                "(z. B. Überrennen ohne Reiterkampf III).\n"
                "Basis-Manöver ohne Vorteil sind immer verfügbar.\n"
                "Intelligente Monster können zusätzlich echte Vorteile "
                "(z. B. Offensiver Kampfstil) unter Vorteile führen."
            )
            info.setWordWrap(True)
            info.setStyleSheet("color:#555; font-style:italic;")
            outer.addWidget(info)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            host = QWidget()
            grid = QGridLayout(host)
            self.manöver_freigabe_checks = {}
            need = manöver_ids_mit_vorteil_req(MANOEVER)
            cols = 2
            for i, m in enumerate(need):
                mid = m.get("id") or ""
                cb = QCheckBox(manöver_label(m, compact=True))
                tip = _wrap_tooltip(m.get("tooltip") or "")
                reqs = [r for r in (m.get("reqs") or []) if r.startswith("vorteil")]
                if reqs:
                    tip = (tip + "\n\n" if tip else "") + "Normal: " + ", ".join(reqs)
                if tip:
                    cb.setToolTip(tip)
                cb.stateChanged.connect(self._on_manöver_freigabe_changed)
                r, c = divmod(i, cols)
                grid.addWidget(cb, r, c)
                self.manöver_freigabe_checks[mid] = cb
            scroll.setWidget(host)
            outer.addWidget(scroll, 1)
            self.tabs.addTab(tab, "Manöver-Freigabe")

        def _patch_kampf_for_monster(self):
            try:
                for i in range(self.tabs.count()):
                    if self.tabs.tabText(i) == "Kampf":
                        w = self.tabs.widget(i)
                        for box in w.findChildren(QGroupBox):
                            if box.title() in ("Waffen", "Angriffe (natürliche Waffen)"):
                                box.setTitle("Waffen")
                        break
            except Exception:
                pass
            # + Waffe / Eigenschaften kommen aus NSCWidget (_init_kampf_tab)
            # Buttons behalten NSC-Beschriftung: + Waffe / + Eigene Waffe

        def add_list_item(self, type_str, data=None):
            super().add_list_item(type_str, data)
            if type_str == "combat" and self.combat_widgets:
                try:
                    self.combat_widgets[-1]["name"].setPlaceholderText("Waffe / Angriff")
                except Exception:
                    pass

        def _update_klasse_icon(self):
            """Klassen-Buchstabe/Icon neben dem Namen + Tooltip."""
            kid = ""
            try:
                kid = self.combo_monster_klasse.currentData() or ""
            except Exception:
                kid = self.data.get("monster_klasse") or ""
            k = klasse_by_id(kid) or {}
            tip = _wrap_tooltip(k.get("beschreibung") or k.get("name") or kid)
            lbl = getattr(self, "lbl_klasse_icon", None) or getattr(self, "_monster_badge", None)
            path = icon_path_for_klasse(kid)
            try:
                self.combo_monster_klasse.setToolTip(tip)
            except Exception:
                pass
            if lbl is None:
                return
            lbl.setToolTip(tip)
            if path:
                pm = QPixmap(path)
                if not pm.isNull():
                    lbl.setPixmap(pm.scaled(
                        26, 26,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    ))
                    lbl.setText("")
                    return
            name = (k.get("name") or "?")[:1].upper()
            lbl.setPixmap(QPixmap())
            lbl.setText(name)

        def _apply_klasse_preset(self, force=False):
            """Klassen-Eigenschaften setzen, wenn leer oder force."""
            kid = self.combo_monster_klasse.currentData()
            preset = []
            params = {}
            for k in load_monster_katalog().get("klassen") or []:
                if k.get("id") == kid:
                    preset = list(k.get("eigenschaften") or [])
                    params = dict(k.get("eigenschaft_params") or {})
                    break
            current = [
                eid for eid, cb in (self.eigenschaft_checks or {}).items() if cb.isChecked()
            ]
            if not preset:
                return
            if current and not force:
                return
            for eid, cb in self.eigenschaft_checks.items():
                cb.blockSignals(True)
                cb.setChecked(eid in preset)
                cb.blockSignals(False)
                ed = self.eigenschaft_params.get(eid)
                if ed is not None:
                    ed.blockSignals(True)
                    ed.setEnabled(eid in preset)
                    if eid in params:
                        ed.setText(params[eid])
                    elif eid not in preset:
                        ed.clear()
                    ed.blockSignals(False)

        def _on_monster_klasse_changed(self, *_):
            if getattr(self, "isLoading", False):
                return
            self._apply_klasse_preset(force=False)
            self._update_klasse_icon()
            self.changed()

        def _on_monster_typ_changed(self, *_):
            if getattr(self, "isLoading", False):
                return
            if self.combo_monster_typ.currentData() == "schwarm":
                if hasattr(self, "combo_wunden_modus") and self.combo_wunden_modus.currentIndex() == 0:
                    self.combo_wunden_modus.setCurrentIndex(2)  # Koloss II
                # Schwarm-Standard-Eigenschaften vorschlagen, wenn leer
                current = [
                    eid for eid, cb in (self.eigenschaft_checks or {}).items() if cb.isChecked()
                ]
                if not current:
                    preset = {
                        "schmerzimmun_2": "",
                        "resistenz_2": "Stichwaffen",
                        "verwundbarkeit_4": "Flächenschaden",
                    }
                    for eid, cb in self.eigenschaft_checks.items():
                        on = eid in preset
                        cb.blockSignals(True)
                        cb.setChecked(on)
                        cb.blockSignals(False)
                        ed = self.eigenschaft_params.get(eid)
                        if ed is not None:
                            ed.blockSignals(True)
                            ed.setEnabled(on)
                            if on:
                                ed.setText(preset[eid])
                            ed.blockSignals(False)
            self.changed()

        def _on_eigenschaft_changed(self, *_):
            if not getattr(self, "isLoading", False):
                self.changed()

        def _on_manöver_freigabe_changed(self, *_):
            if not getattr(self, "isLoading", False):
                self.changed()

        def get_manöver_freigabe(self) -> list:
            out = []
            for mid, cb in (getattr(self, "manöver_freigabe_checks", None) or {}).items():
                try:
                    if cb.isChecked():
                        out.append(mid)
                except RuntimeError:
                    pass
            return out or list(self.data.get("manöver_freigabe") or [])

        def get_kreatur_eigenschaften(self) -> list:
            out = []
            for eid, cb in (getattr(self, "eigenschaft_checks", None) or {}).items():
                try:
                    if cb.isChecked():
                        out.append(eid)
                except RuntimeError:
                    pass
            return out or list(self.data.get("kreatur_eigenschaften") or [])

        def get_kreatur_eigenschaft_params(self) -> dict:
            out = {}
            for eid, ed in (getattr(self, "eigenschaft_params", None) or {}).items():
                try:
                    cb = self.eigenschaft_checks.get(eid)
                    if cb is not None and cb.isChecked():
                        txt = (ed.text() or "").strip()
                        if txt:
                            out[eid] = txt
                except RuntimeError:
                    pass
            return out or dict(self.data.get("kreatur_eigenschaft_params") or {})

        def load_data(self):
            super().load_data()
            was = self.isLoading
            self.isLoading = True
            try:
                self.data["kind"] = "monster"
                kid = self.data.get("monster_klasse") or "tier"
                idx = self.combo_monster_klasse.findData(kid)
                if idx >= 0:
                    self.combo_monster_klasse.setCurrentIndex(idx)

                gid = self.data.get("monster_groesse") or "mittel"
                idx = self.combo_monster_groesse.findData(gid)
                if idx >= 0:
                    self.combo_monster_groesse.setCurrentIndex(idx)

                tid = self.data.get("monster_typ") or "normal"
                idx = self.combo_monster_typ.findData(tid)
                if idx >= 0:
                    self.combo_monster_typ.setCurrentIndex(idx)

                eig = set(self.data.get("kreatur_eigenschaften") or [])
                params = dict(self.data.get("kreatur_eigenschaft_params") or {})
                for eid, cb in (self.eigenschaft_checks or {}).items():
                    cb.blockSignals(True)
                    cb.setChecked(eid in eig)
                    cb.blockSignals(False)
                    ed = self.eigenschaft_params.get(eid)
                    if ed is not None:
                        ed.blockSignals(True)
                        ed.setEnabled(eid in eig)
                        ed.setText(params.get(eid, ""))
                        ed.blockSignals(False)

                freig = set(self.data.get("manöver_freigabe") or [])
                for mid, cb in (self.manöver_freigabe_checks or {}).items():
                    cb.blockSignals(True)
                    cb.setChecked(mid in freig)
                    cb.blockSignals(False)

                self._update_klasse_icon()
            finally:
                if not was:
                    self.isLoading = False

        def save_data(self):
            super().save_data()
            try:
                self.data["kind"] = "monster"
                self.data["monster_klasse"] = self.combo_monster_klasse.currentData() or "tier"
                self.data["monster_groesse"] = self.combo_monster_groesse.currentData() or "mittel"
                self.data["monster_typ"] = self.combo_monster_typ.currentData() or "normal"
                self.data["kreatur_eigenschaften"] = self.get_kreatur_eigenschaften()
                self.data["kreatur_eigenschaft_params"] = self.get_kreatur_eigenschaft_params()
                self.data["manöver_freigabe"] = self.get_manöver_freigabe()
            except RuntimeError:
                pass

    return MonsterWidget
