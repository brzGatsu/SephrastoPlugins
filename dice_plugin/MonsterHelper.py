# -*- coding: utf-8 -*-
"""
Monster-Katalog und Hilfsfunktionen für den Monster-Tab (Master-Plugin).
Lädt monster_katalog.json (kein xml-Modul nötig – Sephrasto-Umgebung).
"""
from __future__ import annotations

import json
import os
from typing import Callable, Optional

_BASE = os.path.dirname(os.path.abspath(__file__))
_KATALOG_JSON = os.path.join(_BASE, "monster_katalog.json")
_KATALOG_XML = os.path.join(_BASE, "monster_katalog.xml")  # optional, nur Fallback

_KATALOG_CACHE = None


def load_monster_katalog(path: Optional[str] = None, force: bool = False) -> dict:
    """Lädt Katalog → {klassen, eigenschaften, waffeneigenschaften, groessen}."""
    global _KATALOG_CACHE
    if _KATALOG_CACHE is not None and not force:
        return _KATALOG_CACHE

    empty = {
        "klassen": [{"id": "tier", "name": "Tier", "wissen": "", "eigenschaften": [],
                     "icon": "", "beschreibung": ""}],
        "eigenschaften": [],
        "waffeneigenschaften": [],
        "groessen": [
            {"id": "mittel", "name": "mittel"},
            {"id": "gross", "name": "groß"},
            {"id": "sehr_gross", "name": "sehr groß"},
        ],
    }

    # 1) JSON (bevorzugt, kein xml-Modul)
    json_path = path or _KATALOG_JSON
    if path and path.endswith(".xml"):
        json_path = _KATALOG_JSON
    try:
        if os.path.isfile(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            _KATALOG_CACHE = {
                "klassen": list(data.get("klassen") or []),
                "eigenschaften": list(data.get("eigenschaften") or []),
                "waffeneigenschaften": list(data.get("waffeneigenschaften") or []),
                "groessen": list(data.get("groessen") or empty["groessen"]),
            }
            return _KATALOG_CACHE
    except Exception as ex:
        print(f"MonsterHelper: JSON-Katalog fehlgeschlagen: {ex}")

    # 2) Optional XML nur wenn xml.etree verfügbar
    try:
        import xml.etree.ElementTree as ET  # noqa: WPS433
        if os.path.isfile(_KATALOG_XML):
            tree = ET.parse(_KATALOG_XML)
            root = tree.getroot()
            klassen, eigenschaften, waffeneigenschaften, groessen = [], [], [], []
            for k in root.findall("./Klassen/Klasse"):
                klassen.append({
                    "id": k.get("id") or "",
                    "name": k.get("name") or k.get("id") or "",
                    "wissen": k.get("wissen") or "",
                    "icon": k.get("icon") or "",
                    "beschreibung": (k.get("beschreibung") or "").strip(),
                    "eigenschaften": [
                        x.strip() for x in (k.get("eigenschaften") or "").split(",") if x.strip()
                    ],
                })
            for e in root.findall("./Eigenschaften/Eigenschaft"):
                eigenschaften.append({
                    "id": e.get("id") or "",
                    "name": e.get("name") or e.get("id") or "",
                    "tooltip": e.get("tooltip") or "",
                })
            for w in root.findall("./Waffeneigenschaften/Waffeneigenschaft"):
                waffeneigenschaften.append({
                    "id": w.get("id") or "",
                    "name": w.get("name") or w.get("id") or "",
                    "kategorie": w.get("kategorie") or "standard",
                    "tooltip": w.get("tooltip") or "",
                })
            for g in root.findall("./Groessen/Groesse"):
                groessen.append({
                    "id": g.get("id") or "",
                    "name": g.get("name") or g.get("id") or "",
                })
            _KATALOG_CACHE = {
                "klassen": klassen,
                "eigenschaften": eigenschaften,
                "waffeneigenschaften": waffeneigenschaften,
                "groessen": groessen or empty["groessen"],
            }
            return _KATALOG_CACHE
    except Exception as ex:
        print(f"MonsterHelper: XML-Fallback fehlgeschlagen: {ex}")

    _KATALOG_CACHE = empty
    return _KATALOG_CACHE


def default_monster_data(name: str = "Neues Monster") -> dict:
    return {
        "name": name,
        "kind": "monster",
        "notizen": "",
        "alle_wuerfeln": False,
        "wunden_ignorieren": False,
        "wunden_modus": 0,
        "monster_klasse": "tier",
        "monster_groesse": "mittel",
        "monster_typ": "normal",
        "kreatur_eigenschaften": [],
        "kreatur_eigenschaft_params": {},
        "manöver_freigabe": [],
        "val_asp": 0,
        "val_kap": 0,
        "attributes": {
            "MU": 0, "KL": 0, "IN": 0, "CH": 0, "FF": 0, "GE": 0, "KO": 0, "KK": 0,
            "INI": 0, "MR": 0, "WS": 4, "WS*": 4, "GS": 4,
        },
        "skills": [
            {"name": "Wachsamkeit", "val": 0},
            {"name": "Zähheit", "val": 0},
        ],
        "powers": [],
        "weapons": [],
        "wunden": [None] * 8,
        "effekte": [],
        "vorteile_list": [],
        "vorteile_text": "",
    }


def manöver_ids_mit_vorteil_req(manöver_list) -> list:
    out = []
    for m in manöver_list or []:
        reqs = m.get("reqs") or []
        if any(r.startswith("vorteil:") or r.startswith("vorteil_any:") for r in reqs):
            out.append(m)
    return out


def make_monster_has_vorteil(
    base_has_vorteil: Callable[[str], bool],
    freigabe_ids: list,
    manöver_list,
) -> Callable[[str], bool]:
    freigabe = set(freigabe_ids or [])

    def has_v(name: str) -> bool:
        if base_has_vorteil(name):
            return True
        if not freigabe:
            return False
        wanted = (name or "").strip().lower()
        for m in manöver_list or []:
            if m.get("id") not in freigabe:
                continue
            for r in m.get("reqs") or []:
                if r.startswith("vorteil:"):
                    if r[8:].strip().lower() == wanted:
                        return True
                elif r.startswith("vorteil_any:"):
                    names = [n.strip().lower() for n in r[12:].split("|")]
                    if wanted in names:
                        return True
        return False

    return has_v


def is_monster_widget(widget) -> bool:
    return bool(widget is not None and (
        getattr(widget, "is_monster", False)
        or (getattr(widget, "data", None) or {}).get("kind") == "monster"
        or (getattr(widget, "data", None) or {}).get("ini_type") == "monster"
    ))


def klasse_by_id(klasse_id: str) -> Optional[dict]:
    for k in load_monster_katalog().get("klassen") or []:
        if k.get("id") == klasse_id:
            return k
    return None


def icon_path_for_klasse(klasse_id: str) -> Optional[str]:
    k = klasse_by_id(klasse_id)
    if not k:
        return None
    rel = (k.get("icon") or "").strip()
    if not rel:
        return None
    if os.path.isabs(rel):
        return rel if os.path.isfile(rel) else None
    full = os.path.join(_BASE, rel)
    return full if os.path.isfile(full) else None
