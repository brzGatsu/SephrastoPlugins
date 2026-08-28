# -*- coding: utf-8 -*-
"""Munition für Dice- und Master-Plugin."""
from __future__ import annotations

import copy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
    QSpinBox, QVBoxLayout, QWidget,
)

from EffectsHelper import new_id


def blank_ammo(name: str = "Munition") -> dict:
    return {
        "id": new_id(),
        "name": name or "Munition",
        "anzahl": 10,
        "tp": "",
        "rw": 0,
        "lz": 0,
        "eigenschaften": "",
        "selected": False,
    }


def normalize_ammo(raw) -> dict:
    if not isinstance(raw, dict):
        return blank_ammo(str(raw) if raw else "Munition")
    out = blank_ammo(raw.get("name") or "Munition")
    out["id"] = raw.get("id") or out["id"]
    try:
        out["anzahl"] = max(0, int(raw.get("anzahl", 0) or 0))
    except (TypeError, ValueError):
        out["anzahl"] = 0
    out["tp"] = str(raw.get("tp") or "").strip()
    try:
        out["rw"] = int(raw.get("rw", 0) or 0)
    except (TypeError, ValueError):
        out["rw"] = 0
    try:
        out["lz"] = int(raw.get("lz", 0) or 0)
    except (TypeError, ValueError):
        out["lz"] = 0
    eig = raw.get("eigenschaften") or ""
    if isinstance(eig, (list, tuple)):
        eig = ", ".join(str(x) for x in eig if x)
    out["eigenschaften"] = str(eig).strip()
    out["selected"] = bool(raw.get("selected"))
    return out


def normalize_ammo_list(items) -> list:
    out = []
    for it in items or []:
        if isinstance(it, dict) and not (it.get("name") or "").strip() and not it.get("anzahl"):
            continue
        out.append(normalize_ammo(it))
    return out


def ammo_has_eigenschaft(ammo, prop: str) -> bool:
    if not ammo or not prop:
        return False
    text = str(ammo.get("eigenschaften") or "").lower()
    return prop.lower() in text


def selected_ammo(items):
    for a in items or []:
        if a.get("selected") and int(a.get("anzahl", 0) or 0) > 0:
            return a
    for a in items or []:
        if a.get("selected"):
            return a
    return None


def set_selected_ammo(items, ammo_id):
    out = []
    for a in items or []:
        b = dict(a)
        b["selected"] = bool(ammo_id) and str(b.get("id")) == str(ammo_id)
        out.append(b)
    return out


def ensure_selected_ammo(items):
    """Bereits gewählte Munition behalten, sonst erste mit Bestand merken."""
    items = normalize_ammo_list(items)
    if any(a.get("selected") for a in items):
        return items
    for a in items:
        if int(a.get("anzahl", 0) or 0) > 0:
            return set_selected_ammo(items, a.get("id"))
    if items:
        return set_selected_ammo(items, items[0].get("id"))
    return items


def consume_selected_ammo(items):
    """Zieht 1 Stück der angewählten Munition ab."""
    used = None
    out = []
    for a in items or []:
        b = dict(a)
        if used is None and b.get("selected") and int(b.get("anzahl", 0) or 0) > 0:
            b["anzahl"] = int(b.get("anzahl", 0) or 0) - 1
            used = dict(b)
            used["anzahl"] = used["anzahl"] + 1  # vor Verbrauch
        out.append(b)
    return out, used


def _wrap_tip(text: str) -> str:
    if not text:
        return ""
    t = text.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return t.replace("\n", "<br>")


class AmmoEditDialog(QDialog):
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Munition")
        self.setMinimumWidth(460)
        data = normalize_ammo(data or {})
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.name_ed = QLineEdit(data.get("name") or "")
        self.anzahl_sp = QSpinBox()
        self.anzahl_sp.setRange(0, 999)
        self.anzahl_sp.setValue(int(data.get("anzahl", 0) or 0))
        self.tp_ed = QLineEdit(data.get("tp") or "")
        self.tp_ed.setPlaceholderText("z. B. +1, −2, 1W6")
        self.rw_sp = QSpinBox()
        self.rw_sp.setRange(0, 200)
        self.rw_sp.setValue(int(data.get("rw", 0) or 0))
        self.lz_sp = QSpinBox()
        self.lz_sp.setRange(0, 20)
        self.lz_sp.setValue(int(data.get("lz", 0) or 0))
        self.eig_ed = QLineEdit(data.get("eigenschaften") or "")
        self.eig_ed.setPlaceholderText("z. B. Rüstungsbrechend")
        form.addRow("Name:", self.name_ed)
        form.addRow("Anzahl:", self.anzahl_sp)
        form.addRow("TP-Bonus:", self.tp_ed)
        form.addRow("RW:", self.rw_sp)
        form.addRow("LZ:", self.lz_sp)
        eig_row = QHBoxLayout()
        eig_row.addWidget(self.eig_ed, 1)
        pick_btn = QPushButton("Eigenschaften…")
        pick_btn.clicked.connect(self._pick_eigenschaften)
        eig_row.addWidget(pick_btn)
        form.addRow("Eigenschaften:", eig_row)
        lay.addLayout(form)
        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        lay.addWidget(box)
        self._id = data.get("id")
        self._selected = bool(data.get("selected"))

    def _pick_eigenschaften(self):
        try:
            from MonsterWidget import WeaponEigenschaftPicker
        except Exception:
            WeaponEigenschaftPicker = None
        if WeaponEigenschaftPicker is None:
            return
        dlg = WeaponEigenschaftPicker(self.eig_ed.text(), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.eig_ed.setText(dlg.selected_text())

    def result_data(self) -> dict:
        return {
            "id": self._id or new_id(),
            "name": self.name_ed.text().strip() or "Munition",
            "anzahl": int(self.anzahl_sp.value()),
            "tp": self.tp_ed.text().strip(),
            "rw": int(self.rw_sp.value()),
            "lz": int(self.lz_sp.value()),
            "eigenschaften": self.eig_ed.text().strip(),
            "selected": self._selected,
        }
