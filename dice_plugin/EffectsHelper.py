# dice_plugin/EffectsHelper.py
"""Gemeinsame Effekt-Logik für Spieler- und NSC-Tabs."""
from __future__ import annotations
import copy
import random
import time

# --- Vorlagen ---
EFFECT_PRESETS = {
    "furcht_1": {
        "name": "Furcht 1",
        "has_timer": False,
        "duration": 0,
        "mods": {"proben": -2, "at": 0, "vt": 0, "tp": 0, "gs": 0, "rs": 0},
        "flags": {"flucht": False, "rueckzug": False},
        "info_text": "Proben −2",
        "info_roll": "",
        "notify_at": 0,
        "source": "preset",
    },
    "furcht_2": {
        "name": "Furcht 2",
        "has_timer": False,
        "duration": 0,
        "mods": {"proben": -4, "at": 0, "vt": 0, "tp": 0, "gs": 0, "rs": 0},
        "flags": {"flucht": False, "rueckzug": True},
        "info_text": "Proben −4 und wenn möglich Rückzug vor Auslöser",
        "info_roll": "",
        "notify_at": 0,
        "source": "preset",
    },
    "furcht_3": {
        "name": "Furcht 3",
        "has_timer": False,
        "duration": 0,
        "mods": {"proben": -8, "at": 0, "vt": 0, "tp": 0, "gs": 0, "rs": 0},
        "flags": {"flucht": True, "rueckzug": False},
        "info_text": "Proben −8 und Flucht, bis Auslöser außer Sicht",
        "info_roll": "",
        "notify_at": 0,
        "source": "preset",
    },
    "furcht_4": {
        "name": "Furcht 4",
        "has_timer": False,
        "duration": 0,
        "mods": {"proben": -8, "at": 0, "vt": 0, "tp": 0, "gs": 0, "rs": 0},
        "flags": {"flucht": True, "rueckzug": False},
        "info_text": "Proben −8 und nur noch zur Flucht erlaubt",
        "info_roll": "",
        "notify_at": 0,
        "source": "preset",
    },
    "atemtechnik": {
        "name": "Atemtechnik",
        "has_timer": True,
        "duration": 1,
        "mods": {"proben": 0, "at": 0, "vt": 0, "tp": 0, "gs": 0, "rs": 0},
        "flags": {"flucht": False, "rueckzug": False},
        "info_text": (
            "+1W6 TP. Freie Aktion. Endet bei 2 Wunden auf einen Schlag "
            "oder nach KO Initiativephasen → 1 Erschöpfung."
        ),
        "info_roll": "",
        "notify_at": 0,
        "source": "manöver",
        "on_end": "erschöpfung",
        "tp_dice": "1W6",
        "tick_mode": "runde",
        "premature_mode": "wunden",
        "premature_x": 2,
        "premature_interrupt_text": "Atemtechnik endet (2 Wunden auf einen Schlag) → 1 Erschöpfung.",
    },
    "konzentration": {
        "name": "Konzentration (voll)",
        "has_timer": True,
        "duration": 1,
        "mods": {"proben": 0, "at": 0, "vt": 0, "tp": 0, "gs": 0, "rs": 0},
        "flags": {"flucht": False, "rueckzug": False},
        "info_text": (
            "Volle Konzentration: bis zur nächsten eigenen INI keine freien "
            "Aktionen/Reaktionen; bei Störungen Willenskraft (16, I), "
            "+4 je soeben erlittener Wunde. Misslingen → aufgewendete "
            "Konzentrations-Aktionen verfallen."
        ),
        "info_roll": "",
        "notify_at": 0,
        "source": "preset",
        "focus": "",
        "on_end": "notify",
        "on_end_notify_text": "Konzentration beendet – bereit.",
        "tick_mode": "runde",
        # Störung → Info (Probe erlaubt), Timer läuft weiter
        "condition_info_mode": "einschr",
        "condition_info_x": 1,
    },
    "volle_offensive": {
        "name": "Volle Offensive",
        "has_timer": True,
        "duration": 1,
        "mods": {"proben": 0, "at": 4, "vt": -8, "tp": 0, "gs": 0, "rs": 0},
        "flags": {"flucht": False, "rueckzug": False},
        "info_text": (
            "Volle Aktion: Nahkampfangriffe +4 AT. "
            "Verteidigungen bis zur nächsten eigenen INI −8 VT "
            "(mit Offensiver Kampfstil −4)."
        ),
        "info_roll": "",
        "notify_at": 0,
        "source": "preset",
        "tick_mode": "runde",
    },
    "volle_defensive": {
        "name": "Volle Defensive",
        "has_timer": True,
        "duration": 1,
        "mods": {"proben": 0, "at": 0, "vt": 4, "tp": 0, "gs": 0, "rs": 0},
        "flags": {"flucht": False, "rueckzug": False},
        "info_text": (
            "Volle Aktion: Verteidigungen bis zur nächsten eigenen INI +4 VT. "
            "Mit Defensiver Kampfstil: einfache Aktion."
        ),
        "info_roll": "",
        "notify_at": 0,
        "source": "preset",
        "tick_mode": "runde",
    },
    "handlungsunfaehig": {
        "name": "Handlungsunfähig",
        "has_timer": True,
        "duration": 1,
        "mods": {"proben": 0, "at": 0, "vt": 0, "tp": 0, "gs": 0, "rs": 0},
        "flags": {"flucht": False, "rueckzug": False},
        "info_text": (
            "Betaubt / handlungsunfahig: keine Proben, Aktionen oder Reaktionen "
            "bis zur ubernachsten Initiativephase (Standard: 1 Runde im Plugin)."
        ),
        "info_roll": "",
        "notify_at": 0,
        "source": "preset",
        "tick_mode": "runde",
        "blocks_probes": True,
    },
    "blutend": {
        "name": "Blutend",
        "has_timer": True,
        "duration": 99,
        "mods": {"proben": 0, "at": 0, "vt": 0, "tp": 0, "gs": 0, "rs": 0},
        "flags": {"flucht": False, "rueckzug": False},
        "info_text": "Blutung aktiv (Details spater).",
        "info_roll": "",
        "notify_at": 0,
        "source": "preset",
        "tick_mode": "runde",
    },
}


def new_id() -> str:
    # Kein uuid-Modul (Sephrasto-Python kann knapper sein)
    return f"{int(time.time() * 1000):x}{random.randint(0, 0xFFFF):04x}"


def blank_effect(name: str = "") -> dict:
    return {
        "id": new_id(),
        "name": name or "Neuer Effekt",
        "has_timer": True,
        "duration": 1,
        "mods": {"proben": 0, "at": 0, "vt": 0, "tp": 0, "gs": 0, "rs": 0},
        "flags": {"flucht": False, "rueckzug": False},
        "info_text": "",
        "info_roll": "",
        "notify_at": 0,
        "notify_fired": False,
        "source": "custom",
        "on_end": None,  # None | "erschöpfung" | "wunde" | "probe" | "notify"
        "on_end_wounds": 1,  # 1–8 Einschränkungen bei on_end == "wunde"
        "on_end_einsch_art": "wunde",  # wunde | ersch
        "on_end_notify_text": "",
        # Ende-Probe (wenn on_end == "probe")
        "on_end_probe_type": "attr",  # attr | fertigkeit | talent
        "on_end_probe_name": "KO",
        "on_end_probe_value": 14,
        "on_end_probe_info": "",
        "on_end_probe_ok_text": "",
        "on_end_probe_fail_text": "",
        "on_end_probe_fail_wounds": 0,
        "on_end_probe_fail_art": "wunde",  # wunde | ersch
        # Zwischen-Trigger: nach x Timer-/Ladungs-Abzügen
        "mid_trigger_at": 0,  # 0 = aus; nach so vielen Ticks auslösen
        "mid_ticks_elapsed": 0,
        "mid_trigger_action": None,  # None | "erschöpfung" | "wunde" | "probe" | "notify"
        "mid_trigger_fired": False,
        "mid_wounds": 1,
        "mid_einsch_art": "wunde",  # wunde | ersch
        "mid_notify_text": "",
        "mid_probe_type": "attr",
        "mid_probe_name": "KO",
        "mid_probe_value": 14,
        "mid_probe_info": "",
        "mid_probe_ok_text": "",
        "mid_probe_fail_text": "",
        "mid_probe_fail_wounds": 0,
        "mid_probe_fail_art": "wunde",
        # TP-Bonus (fest/Würfel, nach Hammerschlag): z. B. "+3", "1W6", "2W6+1"
        "tp_dice": "",
        # Waffenschaden-Bonus (fest/Würfel, vor Hammerschlag)
        "waffenschaden": "",
        # Timer-Tick: "runde" | "at_erfolg" | "tp_waffe"
        "tick_mode": "runde",
        # Waffengift: an ausgerüstete Waffe koppeln
        "is_waffengift": False,
        "weapon_name": "",
        # Gegenstand der Konzentration / Aktion
        "focus": "",
        # Vorzeitiges Timer-Ende (eine Source = ein Schlag)
        # None | "einschr" | "wunden" | "ersch"
        "premature_mode": None,
        "premature_x": 1,
        "premature_interrupt_text": "",
        "premature_fired": False,
        # Bei Bedingung nur Info-Text (Timer bleibt)
        "condition_info_mode": None,  # None | "einschr" | "wunden" | "ersch"
        "condition_info_x": 1,
    }


CUSTOM_EFFECT_PRESETS: dict = {}

# Persistenz: gemeinsam mit Master-Plugin in dice_master_data.json
_PRESET_JSON_NAME = "dice_master_data.json"
_PRESET_KEY = "effect_presets"


def _preset_json_path() -> str:
    import os
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), _PRESET_JSON_NAME)


def load_custom_presets_from_file() -> None:
    """Lädt Benutzer-Vorlagen aus dice_master_data.json."""
    import json
    import os
    path = _preset_json_path()
    raw = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                raw = data.get(_PRESET_KEY) or []
        except Exception as e:
            print(f"Effekt-Vorlagen laden fehlgeschlagen: {e}")
    load_custom_presets(raw)


def save_custom_presets_to_file() -> None:
    """Schreibt Benutzer-Vorlagen nach dice_master_data.json (restliche Keys bleiben)."""
    import json
    import os
    path = _preset_json_path()
    data = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data = loaded
        except Exception:
            data = {}
    data[_PRESET_KEY] = dump_custom_presets()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Effekt-Vorlagen speichern fehlgeschlagen: {e}")


def effect_as_preset(eff: dict, name: str | None = None) -> dict:
    src = normalize_effect(eff)
    out = copy.deepcopy(src)
    out.pop("id", None)
    out.pop("notify_fired", None)
    out.pop("mid_trigger_fired", None)
    out.pop("mid_ticks_elapsed", None)
    out["source"] = "user_preset"
    if name:
        out["name"] = name
    return out


def register_custom_preset(name: str, eff: dict) -> str:
    key = f"user:{(name or '').strip()}"
    CUSTOM_EFFECT_PRESETS[key] = effect_as_preset(eff, name=(name or "").strip() or "Vorlage")
    return key


def delete_custom_preset(key: str) -> bool:
    if key in CUSTOM_EFFECT_PRESETS:
        del CUSTOM_EFFECT_PRESETS[key]
        return True
    return False


def all_presets() -> dict:
    out = dict(EFFECT_PRESETS)
    out.update(CUSTOM_EFFECT_PRESETS)
    return out


def load_custom_presets(raw_list) -> None:
    CUSTOM_EFFECT_PRESETS.clear()
    for it in raw_list or []:
        if not isinstance(it, dict):
            continue
        name = (it.get("name") or "Vorlage").strip()
        CUSTOM_EFFECT_PRESETS[f"user:{name}"] = effect_as_preset(it, name=name)


def dump_custom_presets() -> list:
    return [copy.deepcopy(v) for v in CUSTOM_EFFECT_PRESETS.values()]


def from_preset(key: str, **overrides) -> dict:
    base = EFFECT_PRESETS.get(key) or CUSTOM_EFFECT_PRESETS.get(key)
    if not base:
        return blank_effect(key)
    eff = copy.deepcopy(base)
    eff["id"] = new_id()
    eff["notify_fired"] = False
    eff["mid_trigger_fired"] = False
    eff["mid_ticks_elapsed"] = 0
    for k, v in overrides.items():
        if k == "mods" and isinstance(v, dict):
            eff.setdefault("mods", {}).update(v)
        elif k == "flags" and isinstance(v, dict):
            eff.setdefault("flags", {}).update(v)
        else:
            eff[k] = v
    return eff


def normalize_effect(raw) -> dict:
    """Alte {name, duration}-Einträge und unvollständige Dicts normalisieren."""
    if not isinstance(raw, dict):
        return blank_effect(str(raw) if raw else "")
    # Legacy 2-Felder
    if "mods" not in raw and "name" in raw:
        eff = blank_effect(raw.get("name") or "")
        dur = int(raw.get("duration", 0) or 0)
        eff["duration"] = dur
        eff["has_timer"] = dur > 0
        return eff
    eff = blank_effect(raw.get("name") or "")
    for k in (
        "id", "name", "has_timer", "duration", "info_text", "info_roll",
        "notify_at", "notify_fired", "source", "on_end",
        "on_end_probe_type", "on_end_probe_name", "on_end_probe_value",
        "on_end_probe_info", "on_end_probe_ok_text", "on_end_probe_fail_text",
        "on_end_probe_fail_wounds", "on_end_probe_fail_art",
        "on_end_wounds", "on_end_einsch_art", "on_end_notify_text",
        "mid_trigger_at", "mid_ticks_elapsed", "mid_trigger_action", "mid_trigger_fired",
        "mid_wounds", "mid_einsch_art", "mid_notify_text",
        "mid_probe_type", "mid_probe_name", "mid_probe_value",
        "mid_probe_info", "mid_probe_ok_text", "mid_probe_fail_text",
        "mid_probe_fail_wounds", "mid_probe_fail_art",
        "tp_dice", "waffenschaden", "tick_mode", "is_waffengift", "weapon_name",
        "focus", "premature_mode", "premature_x", "premature_interrupt_text",
        "premature_fired", "condition_info_mode", "condition_info_x",
    ):
        if k in raw:
            eff[k] = raw[k]
    if "mods" in raw and isinstance(raw["mods"], dict):
        for mk in ("proben", "at", "vt", "tp", "gs", "rs"):
            if mk in raw["mods"]:
                try:
                    eff["mods"][mk] = int(raw["mods"][mk])
                except (TypeError, ValueError):
                    pass
    if "flags" in raw and isinstance(raw["flags"], dict):
        for fk in ("flucht", "rueckzug"):
            if fk in raw["flags"]:
                eff["flags"][fk] = bool(raw["flags"][fk])
    # Defaults / Migration
    if not eff.get("tick_mode"):
        if eff.get("is_waffengift"):
            eff["tick_mode"] = "tp_waffe"
        else:
            eff["tick_mode"] = "runde"
    if not eff.get("id"):
        eff["id"] = new_id()
    return eff


def normalize_list(items) -> list:
    if not items:
        return []
    out = []
    for it in items:
        if isinstance(it, dict) and (it.get("name") or "").strip() == "" and not it.get("mods"):
            continue
        out.append(normalize_effect(it))
    return out


def sum_mods(effects: list) -> dict:
    total = {"proben": 0, "at": 0, "vt": 0, "tp": 0, "gs": 0, "rs": 0}
    for e in effects or []:
        mods = e.get("mods") or {}
        for k in total:
            try:
                total[k] += int(mods.get(k, 0) or 0)
            except (TypeError, ValueError):
                pass
    return total


def effect_summary_line(eff: dict) -> str:
    parts = []
    mods = eff.get("mods") or {}
    labels = {
        "proben": "Proben", "at": "AT", "vt": "VT", "tp": "TP", "gs": "GS", "rs": "RS",
    }
    for k, lab in labels.items():
        v = int(mods.get(k, 0) or 0)
        if v:
            parts.append(f"{lab} {v:+d}")
    flags = eff.get("flags") or {}
    if flags.get("rueckzug"):
        parts.append("Rückzug")
    if flags.get("flucht"):
        parts.append("Flucht")
    tp_dice = (eff.get("tp_dice") or "").strip()
    if tp_dice:
        parts.append(f"TP {tp_dice if tp_dice.startswith(('+', '-')) else '+' + tp_dice}")
    wsch = (eff.get("waffenschaden") or "").strip()
    if wsch:
        parts.append(f"Waffe {wsch if wsch.startswith(('+', '-')) else '+' + wsch}")
    if eff.get("is_waffengift"):
        w = (eff.get("weapon_name") or "").strip()
        parts.append(f"Gift→{w}" if w else "Waffengift")
    tick = eff.get("tick_mode") or "runde"
    if tick == "at_erfolg":
        parts.append("Tick: AT")
    elif tick == "tp_waffe":
        parts.append("Tick: TP/Waffe")
    on_end = eff.get("on_end")
    if on_end == "erschöpfung":
        parts.append("Ende→Erschöpfung")
    elif on_end == "wunde":
        parts.append("Ende→Wunde")
    elif on_end == "probe":
        pn = eff.get("on_end_probe_name") or "?"
        pv = eff.get("on_end_probe_value") or "?"
        parts.append(f"Ende→Probe {pn} vs {pv}")
    mid_at = int(eff.get("mid_trigger_at", 0) or 0)
    if mid_at > 0:
        ma = eff.get("mid_trigger_action") or "Hinweis"
        parts.append(f"alle {mid_at} INI→{ma}")
    info = (eff.get("info_text") or "").strip()
    if info and not parts:
        parts.append(info[:60])
    return " · ".join(parts) if parts else (info[:60] if info else "—")


def _mid_events(eff: dict) -> list:
    """Wirkung wenn Dauer einen Zwischenwert erreicht (Effekt bleibt bestehen)."""
    action = eff.get("mid_trigger_action")
    name = eff.get("name") or "Effekt"
    dur = int(eff.get("duration", 0) or 0)
    hint = (eff.get("mid_notify_text") or "").strip()
    if not action:
        msg = hint or f"„{name}“: Zwischen-Effekt bei noch {dur} Runde(n)."
        return [{"type": "notify", "effect": eff, "message": msg}]
    if action == "erschöpfung":
        return [{
            "type": "erschöpfung",
            "effect": eff,
            "message": f"„{name}“ (Zwischen-Effekt):\n1 Erschöpfung (/) hinzugefügt. Effekt läuft weiter ({dur}).",
        }]
    if action == "wunde":
        n = max(1, min(8, int(eff.get("mid_wounds", 1) or 1)))
        art = eff.get("mid_einsch_art") or "wunde"
        if art == "ersch":
            return [{
                "type": "erschöpfung",
                "effect": eff,
                "count": n,
                "message": (
                    f"„{name}“ (Zwischen-Effekt):\n"
                    f"{n} Erschöpfung(en) hinzugefügt. Effekt läuft weiter ({dur})."
                ),
            }]
        return [{
            "type": "wunde",
            "effect": eff,
            "count": n,
            "message": f"„{name}“ (Zwischen-Effekt):\n{n} Wunde(n) hinzugefügt. Effekt läuft weiter ({dur}).",
        }]
    if action == "probe":
        ptype = eff.get("mid_probe_type") or eff.get("on_end_probe_type") or "attr"
        pname = eff.get("mid_probe_name") or eff.get("on_end_probe_name") or "?"
        pval = eff.get("mid_probe_value") if eff.get("mid_probe_value") is not None else (eff.get("on_end_probe_value") or 0)
        kind = {"attr": "Attribut", "fertigkeit": "Fertigkeit", "talent": "Talent"}.get(ptype, "Probe")
        info = (eff.get("mid_probe_info") or eff.get("mid_notify_text") or "").strip()
        return [{
            "type": "probe",
            "effect": eff,
            "phase": "mid",
            "message": (
                f"„{name}“ (Zwischen-Effekt):\n"
                f"Probe erforderlich: {kind} {pname} gegen {pval}.\n"
                f"Effekt läuft weiter ({dur})."
            ),
            "probe_type": ptype,
            "probe_name": pname,
            "probe_value": pval,
            "probe_info": info,
            "probe_ok_text": (eff.get("mid_probe_ok_text") or "").strip(),
            "probe_fail_text": (eff.get("mid_probe_fail_text") or "").strip(),
            "fail_wounds": int(eff.get("mid_probe_fail_wounds", 0) or 0),
            "fail_art": eff.get("mid_probe_fail_art") or "wunde",
        }]
    # notify
    msg = hint or f"„{name}“: Zwischen-Hinweis – noch {dur} Runde(n)."
    return [{"type": "notify", "effect": eff, "message": msg}]


def _tick_one(eff: dict) -> tuple[dict | None, list]:
    """
    Verringert duration um 1. Returns (eff_or_None_if_removed, events).
    """
    events = []
    if not eff.get("has_timer"):
        return eff, events
    dur = int(eff.get("duration", 0) or 0)
    if dur <= 0:
        events.extend(_end_events(eff))
        return None, events
    dur -= 1
    eff["duration"] = dur
    unit = "Ladung(en)" if (eff.get("is_waffengift") or eff.get("tick_mode") in ("at_erfolg", "tp_waffe")) else "Runde(n)"
    notify_at = int(eff.get("notify_at", 0) or 0)
    if notify_at > 0 and dur <= notify_at and not eff.get("notify_fired"):
        eff["notify_fired"] = True
        events.append({
            "type": "notify",
            "effect": eff,
            "message": f"Hinweis: „{eff.get('name', 'Effekt')}“ – noch {dur} {unit}.",
        })
    # Zwischen-Trigger als Intervall: alle x Timer-/Ladungs-Abzüge erneut
    mid_at = int(eff.get("mid_trigger_at", 0) or 0)
    if mid_at > 0:
        ticks = int(eff.get("mid_ticks_elapsed", 0) or 0) + 1
        if ticks >= mid_at:
            eff["mid_ticks_elapsed"] = 0
            events.extend(_mid_events(eff))
        else:
            eff["mid_ticks_elapsed"] = ticks
    if dur <= 0:
        events.extend(_end_events(eff))
        return None, events
    return eff, events


def tick_effects(effects: list) -> tuple[list, list]:
    """
    Dauer aller Timer-Effekte mit tick_mode „runde“ um 1 verringern.
    Waffengift / AT-Tick werden hier übersprungen.
    """
    events = []
    new_list = []
    for raw in effects or []:
        eff = normalize_effect(raw)
        mode = eff.get("tick_mode") or "runde"
        if not eff.get("has_timer") or mode != "runde":
            new_list.append(eff)
            continue
        kept, ev = _tick_one(eff)
        events.extend(ev)
        if kept is not None:
            new_list.append(kept)
    return new_list, events


def tick_effects_on_at(effects: list) -> tuple[list, list]:
    """Timer mit tick_mode „at_erfolg“ bei erfolgreicher AT verringern."""
    events = []
    new_list = []
    for raw in effects or []:
        eff = normalize_effect(raw)
        mode = eff.get("tick_mode") or "runde"
        if not eff.get("has_timer") or mode != "at_erfolg":
            new_list.append(eff)
            continue
        kept, ev = _tick_one(eff)
        events.extend(ev)
        if kept is not None:
            new_list.append(kept)
    return new_list, events


def tick_effects_on_tp(effects: list, weapon_name: str = "") -> tuple[list, list]:
    """
    Waffengift / tick_mode „tp_waffe“: Ladung nur bei TP mit passender Waffe.
    """
    events = []
    new_list = []
    wname = (weapon_name or "").strip().lower()
    for raw in effects or []:
        eff = normalize_effect(raw)
        mode = eff.get("tick_mode") or "runde"
        if not eff.get("has_timer") or mode != "tp_waffe":
            new_list.append(eff)
            continue
        link = (eff.get("weapon_name") or "").strip().lower()
        # ohne Waffenname: bei jedem TP; sonst nur passende Waffe
        if link and wname and link not in wname and wname not in link:
            new_list.append(eff)
            continue
        kept, ev = _tick_one(eff)
        events.extend(ev)
        if kept is not None:
            new_list.append(kept)
    return new_list, events


def collect_tp_dice_effects(effects: list, weapon_name: str = "") -> list:
    """
    Effekte die beim TP-Wurf Zusatz (nach Hammerschlag) / Hinweise liefern.
    Returns list of {name, dice, info, is_waffengift, waffenschaden}.
    """
    out = []
    wname = (weapon_name or "").strip().lower()
    for raw in effects or []:
        eff = normalize_effect(raw)
        dice = (eff.get("tp_dice") or "").strip()
        # Legacy: fester mods.tp → in Ausdruck übernehmen
        try:
            flat = int((eff.get("mods") or {}).get("tp", 0) or 0)
        except (TypeError, ValueError):
            flat = 0
        if flat and not dice:
            dice = f"{flat:+d}"
        elif flat and dice:
            dice = f"{dice}{flat:+d}"
        wsch = (eff.get("waffenschaden") or "").strip()
        info = (eff.get("info_text") or "").strip()
        is_gift = bool(eff.get("is_waffengift"))
        link = (eff.get("weapon_name") or "").strip().lower()
        if is_gift or link:
            if link and wname and link not in wname and wname not in link:
                continue
            if dice or info or is_gift or wsch:
                out.append({
                    "name": eff.get("name") or "Effekt",
                    "dice": dice,
                    "waffenschaden": wsch,
                    "info": info,
                    "is_waffengift": is_gift,
                    "id": eff.get("id"),
                })
        elif dice or wsch:
            out.append({
                "name": eff.get("name") or "Effekt",
                "dice": dice,
                "waffenschaden": wsch,
                "info": info,
                "is_waffengift": False,
                "id": eff.get("id"),
            })
    return out


def parse_tp_dice_string(expr: str) -> tuple[int, str]:
    """
    Würfelt einen TP-Zusatzausdruck wie '1W6', '+1W6', '2W6+1'.
    Returns (total, detail_html).
    """
    import re
    s = (expr or "").strip()
    if not s:
        return 0, ""
    # führendes + entfernen fürs Parsen, Vorzeichen merken
    sign = 1
    if s.startswith("+"):
        s = s[1:].strip()
    elif s.startswith("-"):
        sign = -1
        s = s[1:].strip()
    total = 0
    parts = []
    # dice parts
    for m in re.finditer(r"(\d*)[wWdD](\d+)", s):
        n = int(m.group(1) or 1)
        sides = int(m.group(2))
        rolls = [random.randint(1, sides) for _ in range(n)]
        sub = sum(rolls)
        total += sub
        parts.append(f"{n}W{sides}({','.join(map(str, rolls))})={sub}")
    # flat modifiers after dice
    rest = re.sub(r"(\d*)[wWdD](\d+)", "", s)
    for m in re.finditer(r"([+-]?\d+)", rest):
        v = int(m.group(1))
        total += v
        parts.append(f"{v:+d}")
    total *= sign
    detail = " ".join(parts) if parts else str(total)
    if sign < 0 and not detail.startswith("-"):
        detail = f"-({detail})"
    return total, detail


def _end_events(eff: dict) -> list:
    events = []
    name = eff.get("name") or "Effekt"
    on_end = eff.get("on_end")
    hint = (eff.get("on_end_notify_text") or "").strip()
    if on_end == "erschöpfung" or (isinstance(name, str) and name.lower().startswith("atemtechnik")):
        events.append({
            "type": "erschöpfung",
            "effect": eff,
            "message": f"„{name}“ ist beendet.\nEs wurde 1 Erschöpfung (/) hinzugefügt.",
        })
    elif on_end == "wunde":
        n = max(1, min(8, int(eff.get("on_end_wounds", 1) or 1)))
        art = eff.get("on_end_einsch_art") or "wunde"
        if art == "ersch":
            events.append({
                "type": "erschöpfung",
                "effect": eff,
                "count": n,
                "message": f"„{name}“ ist beendet.\nEs wurden {n} Erschöpfung(en) hinzugefügt.",
            })
        else:
            events.append({
                "type": "wunde",
                "effect": eff,
                "count": n,
                "message": f"„{name}“ ist beendet.\nEs wurden {n} Wunde(n) hinzugefügt.",
            })
    elif on_end == "probe":
        ptype = eff.get("on_end_probe_type") or "attr"
        pname = eff.get("on_end_probe_name") or "?"
        pval = eff.get("on_end_probe_value") or 0
        kind = {"attr": "Attribut", "fertigkeit": "Fertigkeit", "talent": "Talent"}.get(ptype, "Probe")
        info = (eff.get("on_end_probe_info") or hint or "").strip()
        events.append({
            "type": "probe",
            "effect": eff,
            "phase": "end",
            "message": (
                f"„{name}“ ist beendet.\n"
                f"Probe erforderlich: {kind} {pname} gegen {pval}."
            ),
            "probe_type": ptype,
            "probe_name": pname,
            "probe_value": pval,
            "probe_info": info,
            "probe_ok_text": (eff.get("on_end_probe_ok_text") or "").strip(),
            "probe_fail_text": (eff.get("on_end_probe_fail_text") or "").strip(),
            "fail_wounds": int(eff.get("on_end_probe_fail_wounds", 0) or 0),
            "fail_art": eff.get("on_end_probe_fail_art") or "wunde",
        })
    elif on_end == "notify":
        events.append({
            "type": "notify",
            "effect": eff,
            "message": hint or f"„{name}“ ist beendet.",
        })
    else:
        events.append({
            "type": "removed",
            "effect": eff,
            "message": hint or f"„{name}“ ist abgelaufen und wurde entfernt.",
        })
    return events


def make_atemtechnik_effect(ko_wert: int) -> dict:
    ko = max(1, int(ko_wert or 1))
    eff = from_preset("atemtechnik", name=f"Atemtechnik (KO {ko})")
    # Dauer = KO Initiativephasen; vorzeitig bei 2 Wunden auf einen Schlag
    eff["has_timer"] = True
    eff["duration"] = ko
    eff["info_text"] = (
        f"+1W6 TP. Freie Aktion. Endet bei 2 Wunden auf einen Schlag "
        f"oder nach {ko} Initiativephasen → 1 Erschöpfung."
    )
    eff["on_end"] = "erschöpfung"
    eff["premature_mode"] = "wunden"
    eff["premature_x"] = 2
    eff["premature_interrupt_text"] = (
        "Atemtechnik endet (2 Wunden auf einen Schlag) → 1 Erschöpfung."
    )
    return eff


def _has_named_vorteil(vorteil_names, *wanted) -> bool:
    """Prüft Vorteil-Namen (case-insensitive, Teilstring ok)."""
    if not vorteil_names:
        return False
    lower = []
    for v in vorteil_names:
        if isinstance(v, str):
            lower.append(v.lower())
        elif isinstance(v, dict) and v.get("name"):
            lower.append(str(v["name"]).lower())
        else:
            lower.append(str(v).lower())
    for w in wanted:
        wl = w.lower()
        if any(wl == n or wl in n for n in lower):
            return True
    return False


def make_volle_offensive_effect(has_offensiver_kampfstil: bool = False) -> dict:
    """
    Volle Offensive bis nächste eigene INI.
    Offensiver Kampfstil: VT-Malus nur −4 statt −8.
    """
    vt = -4 if has_offensiver_kampfstil else -8
    name = "Volle Offensive"
    if has_offensiver_kampfstil:
        name = "Volle Offensive (Offensiver Kampfstil)"
    eff = from_preset("volle_offensive", name=name)
    eff["has_timer"] = True
    eff["duration"] = 1
    eff["tick_mode"] = "runde"
    eff["mods"] = {"proben": 0, "at": 4, "vt": vt, "tp": 0, "gs": 0, "rs": 0}
    if has_offensiver_kampfstil:
        eff["info_text"] = (
            "Volle Aktion: Nahkampfangriffe +4 AT. "
            "Verteidigungen bis zur nächsten eigenen INI −4 VT "
            "(Offensiver Kampfstil)."
        )
    else:
        eff["info_text"] = (
            "Volle Aktion: Nahkampfangriffe +4 AT. "
            "Verteidigungen bis zur nächsten eigenen INI −8 VT. "
            "Mit Offensiver Kampfstil wäre der Malus nur −4."
        )
    return eff


def make_volle_defensive_effect(has_defensiver_kampfstil: bool = False) -> dict:
    """
    Volle Defensive bis nächste eigene INI.
    VT +4. AT-Malus (−4) kommt über Kampfmod „Zweite einfache Aktion“,
    den die UI bei aktiver Voller Defensive setzt.
    Ohne Defensiver Kampfstil: volle Aktion → AT blockiert (blocks_at).
    Mit Defensiver Kampfstil: einfache Aktion, AT weiter möglich.
    VT (inkl. Auflaufen/Riposte) bleibt immer erlaubt.
    """
    name = "Volle Defensive"
    if has_defensiver_kampfstil:
        name = "Volle Defensive (Defensiver Kampfstil)"
    eff = from_preset("volle_defensive", name=name)
    eff["has_timer"] = True
    eff["duration"] = 1
    eff["tick_mode"] = "runde"
    eff["mods"] = {"proben": 0, "at": 0, "vt": 4, "tp": 0, "gs": 0, "rs": 0}
    if has_defensiver_kampfstil:
        eff["blocks_at"] = False
        eff["info_text"] = (
            "Einfache Aktion (Defensiver Kampfstil): Verteidigungen bis zur "
            "nächsten eigenen INI +4 VT. Zusätzlich z. B. Konflikt / AT möglich "
            "(AT dann oft als zweite einfache Aktion −4)."
        )
    else:
        # Volle Aktion verbraucht – keine weiteren Aktionen (AT), VT bleibt ok
        eff["blocks_at"] = True
        eff["info_text"] = (
            "Volle Aktion: Verteidigungen bis zur nächsten eigenen INI +4 VT. "
            "Keine weiteren Aktionen (AT blockiert). "
            "Mit Defensiver Kampfstil wäre dies eine einfache Aktion."
        )
    return eff


def is_volle_kampfhaltung(eff: dict) -> bool:
    n = (eff.get("name") or "").lower()
    return n.startswith("volle offensive") or n.startswith("volle defensive")

def make_handlungsunfaehig_effect(duration: int = 1) -> dict:
    eff = from_preset("handlungsunfaehig", name="Handlungsunfähig")
    eff["has_timer"] = True
    eff["duration"] = max(1, int(duration or 1))
    eff["tick_mode"] = "runde"
    eff["blocks_probes"] = True
    eff["info_text"] = (
        "Betäubt / handlungsunfähig: keine Proben, Aktionen oder Reaktionen "
        f"({eff['duration']} Runde(n))."
    )
    return eff


def make_blutend_effect(ws: int = 4) -> dict:
    """Blutung: alle WS Initiativephasen KO-Probe (12, I); Misslingen → +1 Wunde."""
    ws = max(1, int(ws or 4))
    eff = from_preset("blutend", name="Blutend")
    eff["has_timer"] = True
    # lange Dauer, damit Intervall mehrfach feuern kann
    eff["duration"] = max(ws * 20, 40)
    eff["tick_mode"] = "runde"
    eff["mid_trigger_at"] = ws
    eff["mid_ticks_elapsed"] = 0
    eff["mid_trigger_action"] = "probe"
    eff["mid_probe_type"] = "attr"
    eff["mid_probe_name"] = "KO"
    eff["mid_probe_value"] = 12
    eff["mid_probe_info"] = (
        f"Blutung (alle {ws} WS-Runden): KO-Probe (12, I).\n"
        "Misslingen → +1 Wunde."
    )
    eff["mid_probe_ok_text"] = "Probe gelungen – keine weitere Wunde."
    eff["mid_probe_fail_text"] = "Probe misslungen – +1 Wunde durch Blutung."
    eff["mid_probe_fail_wounds"] = 1
    eff["mid_notify_text"] = (
        f"Blutung (alle {ws} WS-Runden): erneut KO-Probe (12, I); "
        "Misslingen → +1 Wunde"
    )
    eff["info_text"] = (
        f"Blutung aktiv – alle {ws} Initiativephasen (WS): "
        "erneut KO-Probe (12, I); Misslingen → +1 Wunde."
    )
    return eff


def _talent_fertigkeiten(t_def) -> list:
    ferts = getattr(t_def, "fertigkeiten", None) or []
    if isinstance(ferts, str):
        return [f.strip() for f in ferts.split(",") if f.strip()]
    return list(ferts)


def _char_talent_names(char) -> set:
    names = set()
    if char is None:
        return names
    raw = getattr(char, "talente", None)
    if isinstance(raw, dict):
        names.update(raw.keys())
    elif raw:
        names.update(raw)
    for fert in list((getattr(char, "fertigkeiten", None) or {}).values()) + list(
        (getattr(char, "übernatürlicheFertigkeiten", None) or {}).values()
    ):
        gekauft = getattr(fert, "gekaufteTalente", None) or []
        if isinstance(gekauft, dict):
            names.update(gekauft.keys())
        else:
            names.update(gekauft)
    return {str(n) for n in names if n}


def collect_player_probe_entries(char=None, db=None) -> list:
    """
    Attribut / Fertigkeit (PW + PW(T)) / Talent.
    Talent vorhanden → PW(T) der Fertigkeit; sonst PW der Fertigkeit.
    """
    entries = []
    try:
        if char is None:
            from Wolke import Wolke
            char = getattr(Wolke, "Char", None)
        if db is None:
            from Wolke import Wolke
            db = getattr(Wolke, "DB", None)
    except Exception:
        pass
    if char is None:
        for a in ("MU", "KL", "IN", "CH", "FF", "GE", "KO", "KK"):
            entries.append({"type": "attr", "name": a, "pw": 0, "label": a, "kind": "Attribut", "owned": True})
        return entries

    for a in ("MU", "KL", "IN", "CH", "FF", "GE", "KO", "KK"):
        pw = 0
        try:
            if a in (getattr(char, "attribute", None) or {}):
                pw = int(getattr(char.attribute[a], "probenwert", 0) or 0)
        except Exception:
            pw = 0
        entries.append({"type": "attr", "name": a, "pw": pw, "label": a, "kind": "Attribut", "owned": True})

    owned_talents = _char_talent_names(char)

    def _add_fert_block(fert_map, kind_fert, kind_pwt):
        for name, fert in (fert_map or {}).items():
            pw = int(getattr(fert, "probenwert", 0) or 0)
            pwt = int(getattr(fert, "probenwertTalent", 0) or 0)
            entries.append({
                "type": "fertigkeit", "name": name, "pw": pw,
                "label": f"{name}  PW {pw}", "kind": kind_fert, "owned": True,
            })
            if pwt and pwt != pw:
                entries.append({
                    "type": "talent", "name": name, "pw": pwt,
                    "label": f"{name}  PW(T) {pwt}", "kind": kind_pwt, "owned": True,
                })
            if db is not None and hasattr(db, "talente"):
                for t_name, t_def in db.talente.items():
                    ferts = _talent_fertigkeiten(t_def)
                    if name not in ferts:
                        continue
                    has = t_name in owned_talents
                    use_pw = pwt if has and pwt else pw
                    mark = "" if has else "  [ohne Talent → PW]"
                    entries.append({
                        "type": "talent", "name": t_name, "pw": use_pw,
                        "label": f"{t_name}  {'PW(T)' if has and pwt else 'PW'} {use_pw}{mark}",
                        "kind": "Talent", "owned": has, "fertigkeit": name,
                    })

    _add_fert_block(getattr(char, "fertigkeiten", None) or {}, "Fertigkeit", "PW(T)")
    _add_fert_block(getattr(char, "übernatürlicheFertigkeiten", None) or {}, "Übernatürlich", "Über/PW(T)")

    # Dedup talent names: keep owned first, then first occurrence
    seen = set()
    out = []
    for e in entries:
        key = (e["type"], e["name"], e.get("kind"))
        if e["type"] == "talent":
            key = ("talent", e["name"])
        if key in seen:
            # owned talent replaces unowned duplicate
            if e.get("owned"):
                for i, prev in enumerate(out):
                    if prev.get("type") == "talent" and prev.get("name") == e["name"] and not prev.get("owned"):
                        out[i] = e
                        break
            continue
        seen.add(key)
        out.append(e)
    return out


def collect_nsc_probe_entries(widget=None, skills=None, attributes=None, db=None) -> list:
    """NSC/Monster: Attribute (PW=2×Wert), Fertigkeiten, Talente aus DB zur Fertigkeit."""
    entries = []
    attrs = attributes or {}
    if widget is not None:
        spins = getattr(widget, "attr_spins", None) or {}
        data_attrs = ((getattr(widget, "data", None) or {}).get("attributes")) or {}
        for a in ("MU", "KL", "IN", "CH", "FF", "GE", "KO", "KK"):
            if a in spins:
                try:
                    attrs[a] = int(spins[a].value())
                except Exception:
                    attrs[a] = int(data_attrs.get(a, 0) or 0)
            elif a not in attrs:
                attrs[a] = int(data_attrs.get(a, 0) or 0)
        skills = skills if skills is not None else list(getattr(widget, "skills_data", None) or [])
    for a in ("MU", "KL", "IN", "CH", "FF", "GE", "KO", "KK"):
        val = int(attrs.get(a, 0) or 0)
        entries.append({
            "type": "attr", "name": a, "pw": val * 2,
            "label": f"{a}  (Wert {val}, PW {val * 2})", "kind": "Attribut", "owned": True,
        })
    if db is None:
        try:
            from Wolke import Wolke
            db = getattr(Wolke, "DB", None)
        except Exception:
            db = None
    owned = set()
    if widget is not None:
        for n in getattr(widget, "talents_data", None) or []:
            nn = n.get("name") if isinstance(n, dict) else str(n)
            if nn:
                owned.add(nn)
        for p in ((getattr(widget, "data", None) or {}).get("powers") or []):
            nn = p.get("name") if isinstance(p, dict) else str(p)
            if nn:
                owned.add(nn)
    for s in skills or []:
        name = s.get("name") or ""
        if not name:
            continue
        pw = int(s.get("val", 0) or 0)
        pwt = int(s.get("pwt") or s.get("val_t") or 0)
        entries.append({
            "type": "fertigkeit", "name": name, "pw": pw,
            "label": f"{name}  PW {pw}", "kind": "Fertigkeit", "owned": True,
        })
        if pwt and pwt != pw:
            entries.append({
                "type": "talent", "name": name, "pw": pwt,
                "label": f"{name}  PW(T) {pwt}", "kind": "PW(T)", "owned": True,
            })
        if db is not None and hasattr(db, "talente"):
            try:
                for t_name, t_def in db.talente.items():
                    ferts = _talent_fertigkeiten(t_def)
                    if name not in ferts:
                        continue
                    has = t_name in owned
                    use_pw = pwt if has and pwt else pw
                    mark = "" if has else "  [ohne Talent → PW]"
                    entries.append({
                        "type": "talent", "name": t_name, "pw": use_pw,
                        "label": f"{t_name}  {'PW(T)' if has and pwt else 'PW'} {use_pw}{mark}",
                        "kind": "Talent", "owned": has, "fertigkeit": name,
                    })
            except Exception:
                pass
    seen = set()
    out = []
    for e in entries:
        key = ("talent", e["name"]) if e["type"] == "talent" else (e["type"], e["name"], e.get("kind"))
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def resolve_probe_pw(entries, ptype, pname, fallback=0) -> int:
    want = (pname or "").strip().lower()
    for e in entries or []:
        if e.get("type") == ptype and (e.get("name") or "").strip().lower() == want:
            return int(e.get("pw", 0) or 0)
    for e in entries or []:
        if (e.get("name") or "").strip().lower() == want:
            return int(e.get("pw", 0) or 0)
    return int(fallback or 0)


def count_einschraenkungen(wunden) -> int:
    """Zählt belegte Einschränkungs-Slots (Wunde oder Erschöpfung)."""
    n = 0
    for w in wunden or []:
        if w is None:
            continue
        s = str(w).strip()
        if not s or s.lower() == "none":
            continue
        n += 1
    return n


def einschraenkung_malus(wunden, ignorieren=False) -> int:
    """Ilaris: ab der 3. Einschränkung −2 je weitere (3→−2, 4→−4, …)."""
    if ignorieren:
        return 0
    cnt = count_einschraenkungen(wunden)
    return (cnt - 2) * 2 if cnt >= 3 else 0


def is_legacy_blutend_event(ev) -> bool:
    """Alte gespeicherte Blutend-Effekte (nur Hinweis) als Probe behandeln."""
    if not ev:
        return False
    if ev.get("type") != "notify":
        return False
    eff = ev.get("effect") or {}
    name = (eff.get("name") or ev.get("name") or "").lower()
    if not name.startswith("blutend"):
        return False
    if (eff.get("mid_trigger_action") or "") == "probe":
        return False
    return True


def blutend_probe_overlay(ev) -> dict:
    """Ergänzt Event-Felder für Legacy-Blutend."""
    out = dict(ev or {})
    out["type"] = "probe"
    out["phase"] = "mid"
    out["probe_type"] = "attr"
    out["probe_name"] = "KO"
    out["probe_value"] = 12
    out["probe_info"] = out.get("message") or "KO-Probe (12, I). Misslingen → +1 Wunde."
    out["probe_ok_text"] = "Probe gelungen – keine weitere Wunde."
    out["probe_fail_text"] = "Probe misslungen – +1 Wunde durch Blutung."
    out["fail_wounds"] = 1
    return out


def has_blocking_probe_effect(effects: list):
    """Gibt Effektnamen zurück, wenn Proben blockiert sind."""
    for e in effects or []:
        if e.get("blocks_probes"):
            return e.get("name") or "Handlungsunfähig"
        n = (e.get("name") or "").lower()
        if "handlungsunfähig" in n or "handlungsunfaehig" in n:
            return e.get("name") or "Handlungsunfähig"
    return None


def has_blocking_at_effect(effects: list):
    """
    Gibt Effektnamen zurück, wenn nur AT blockiert ist (nicht VT/TP).
    z. B. Volle Defensive ohne Defensiver Kampfstil.
    """
    for e in effects or []:
        if e.get("blocks_at"):
            return e.get("name") or "Volle Defensive"
        n = (e.get("name") or "").lower()
        # Fallback: reine „Volle Defensive“ ohne Kampfstil-Zusatz
        if n.startswith("volle defensive") and "defensiver kampfstil" not in n:
            return e.get("name") or "Volle Defensive"
    return None


# =============================================================================
# Manöver-Katalog (Ilaris S. 40–41, 46)
# =============================================================================
# anwendbar: Menge aus {"AT", "VT", "FK"}
# mod: int (fix) | "variable" (1–8) | None
# effekt: Schlüssel für pending-Effekte
# reqs: Liste deklarativer Voraussetzungen (leer = immer)
#   "vorteil:Name"           – Charakter/NSC muss Vorteil besitzen
#   "waffe:Eigenschaft"      – Waffe muss Eigenschaft haben (Teilstring)
#   "fernkampf" / "nahkampf" – Waffentyp
#   "waffenlos"              – waffenloser Angriff
#   "situativ:Text"          – nicht prüfbar → Label-Hinweis in Klammern
#   "setting:trefferzonen"   – Optionalregel
# kategorie: "basis" | "eingeschränkt" | "aufbauend" | "fernkampf"

MANOEVER = [
    # --- Basismanöver ---
    {
        "id": "ausweichen",
        "name": "Ausweichen",
        "kategorie": "basis",
        "anwendbar": {"VT"},
        "mod": -2,
        "mod_be": True,  # zusätzlich –BE der Rüstung
        "mod_label": "VT –2–BE",
        "effekt": "ausweichen",
        "tooltip": "Angriff und Auswirkungen vollständig vermeiden.",
        "reqs": [],
    },
    {
        "id": "binden",
        "name": "Binden",
        "kategorie": "basis",
        "anwendbar": {"VT"},
        "mod": "variable",
        "mod_label": "VT –X",
        "effekt": "binden",
        "tooltip": "Bis Ende nächster eigener INI: VT des Gegners um –X (max. 8).",
        "reqs": [],
    },
    {
        "id": "entfernung_veraendern",
        "name": "Entfernung verändern",
        "kategorie": "basis",
        "anwendbar": {"AT"},
        "mod": 0,
        "mod_be": True,  # –BE der Rüstung
        "mod_label": "AT –BE",
        "effekt": "entfernung",
        "tooltip": "Aus Nahkampf lösen ohne Passierschläge.",
        "reqs": ["nahkampf"],
    },
    {
        "id": "entwaffnen",
        "name": "Entwaffnen",
        "kategorie": "basis",
        "anwendbar": {"AT", "VT"},
        "mod": -4,
        "mod_label": "AT/VT –4",
        "effekt": "schaden_0",
        "tooltip": "Waffe entreißen (Gegenprobe KK). Schaden = 0.",
        "reqs": ["nahkampf"],
    },
    {
        "id": "gezielter_schlag",
        "name": "Gezielter Schlag",
        "kategorie": "basis",
        "anwendbar": {"AT"},
        "mod": -2,
        "mod_label": "AT –2",
        "effekt": "trefferzone",
        "tooltip": "Trefferzone selbst bestimmen.",
        "reqs": ["nahkampf", "situativ:Trefferzonen"],
    },
    {
        "id": "umreissen",
        "name": "Umreißen",
        "kategorie": "basis",
        "anwendbar": {"AT"},
        "mod": 0,
        "mod_label": "AT",
        "effekt": "schaden_0",
        "tooltip": "Ziel stürzt (Gegenprobe GE/KO). Schaden = 0.",
        "reqs": ["nahkampf"],
    },
    {
        "id": "wuchtschlag",
        "name": "Wuchtschlag",
        "kategorie": "basis",
        "anwendbar": {"AT"},
        "mod": "variable",
        "mod_label": "AT –X",
        "effekt": "tp_bonus",
        "tooltip": "+X TP (max. 8).",
        "reqs": ["nahkampf"],
    },
    # --- Eingeschränkte Basismanöver ---
    {
        "id": "auflaufen_lassen",
        "name": "Auflaufen lassen",
        "kategorie": "eingeschränkt",
        "anwendbar": {"VT"},
        "mod": -4,
        "mod_label": "VT –4",
        "effekt": "auflaufen",
        "tooltip": "Angreifer erleidet deinen Waffenschaden + seine GS.",
        "reqs": ["nahkampf", "situativ:größere Reichweite; Gegner Bewegung+Konflikt"],
    },
    {
        "id": "ruestungsbrecher_nk",
        "name": "Rüstungsbrecher",
        "kategorie": "eingeschränkt",
        "anwendbar": {"AT"},
        "mod": -4,
        "mod_label": "AT –4",
        "effekt": "sp_statt_tp",
        "tooltip": "SP statt TP.",
        "reqs": ["nahkampf", "waffe:Rüstungsbrechend"],
    },
    {
        "id": "schildspalter",
        "name": "Schildspalter",
        "kategorie": "eingeschränkt",
        "anwendbar": {"AT"},
        "mod": 2,
        "mod_label": "AT +2",
        "effekt": "schild_schaden",
        "tooltip": "Schild des Gegners erleidet deinen Waffenschaden.",
        "reqs": ["nahkampf", "situativ:Gegner führt Schild"],
    },
    {
        "id": "stumpfer_schlag",
        "name": "Stumpfer Schlag",
        "kategorie": "eingeschränkt",
        "anwendbar": {"AT"},
        "mod": 0,
        "mod_label": "AT",
        "effekt": "erschoepfung",
        "tooltip": "Erschöpfung statt Wunden; keine Blutung bei Kampfunfähigkeit.",
        "reqs": ["nahkampf", "waffe:Stumpf"],
    },
    {
        "id": "umklammern",
        "name": "Umklammern",
        "kategorie": "eingeschränkt",
        "anwendbar": {"AT"},
        "mod": "variable",
        "mod_label": "AT –X",
        "effekt": "schaden_0",
        # Immer wählbar; Voraussetzungen nur im Tooltip (***-Markierung)
        "always": True,
        "mark": "***",
        "tooltip": (
            "Umklammern (AT –X)\n"
            "Wirkung: Handlungen des Umklammerten sind um –X erschwert und seine GS "
            "sinkt auf 0, solange die Umklammerung anhält. Bei mehrfachen "
            "Umklammerungen summieren sich die Malusse. Du kannst dein Ziel in einer "
            "Freien Aktion loslassen. Der Umklammerte kann eine Aktion Konflikt "
            "aufwenden und eine vergleichende GE- oder KK-Probe (I) gegen die GE oder "
            "KK des Umklammernden ablegen. Gelingt die Probe, lässt der Umklammernde "
            "sofort los. Das Manöver senkt den Schaden des Angriffes auf 0. Sollte der "
            "Angriff ohnehin keinen Schaden anrichten, ist das Manöver nicht möglich.\n"
            "Voraussetzungen: Angriff mit beiden Händen im waffenlosen Kampf; Ziel darf "
            "nicht einer höheren Größenklasse angehören."
        ),
        "reqs": [],
    },
    # --- Aufbauende Manöver ---
    {
        "id": "ausfall",
        "name": "Ausfall",
        "kategorie": "aufbauend",
        "anwendbar": {"AT"},
        "mod": -2,
        "mod_be": True,  # zusätzlich –BE der Rüstung
        "mod_label": "AT –2–BE",
        "effekt": "ausfall",
        "tooltip": "Ziel weicht bis 2 Schritt zurück; du folgst. Passierschlag bei anderem Ziel.",
        "reqs": ["nahkampf", "vorteil:Ausfall"],
    },
    {
        "id": "befreiungsschlag",
        "name": "Befreiungsschlag",
        "kategorie": "aufbauend",
        "anwendbar": {"AT"},
        "mod": -4,
        "mod_label": "AT –4",
        "effekt": "befreiungsschlag",
        "tooltip": (
            "Attacke gegen alle Ziele in 180° vor dir. "
            "Kein Befreiungsschlag seit letztem Beginn einer eigenen Initiativephase."
        ),
        "reqs": [
            "nahkampf",
            "vorteil:Kraftvoller Kampf III",
            "situativ:Kampf in diesem Stil; kein Befreiungsschlag seit letztem Beginn einer eigenen Initiativephase",
        ],
    },
    {
        "id": "doppelangriff",
        "name": "Doppelangriff",
        "kategorie": "aufbauend",
        "anwendbar": {"AT"},
        "mod": -4,
        "mod_label": "zwei AT –4",
        "effekt": "doppelangriff",
        "tooltip": (
            "Mit beiden Händen je eine unabhängige Attacke –4. "
            "Kein Doppelangriff seit letztem Beginn einer eigenen Initiativephase."
        ),
        "reqs": [
            "nahkampf",
            "vorteil:Beidhändiger Kampf III",
            "situativ:Kampf in diesem Stil; kein Doppelangriff seit letztem Beginn einer eigenen Initiativephase",
        ],
    },
    {
        "id": "hammerschlag",
        "name": "Hammerschlag",
        "kategorie": "aufbauend",
        "anwendbar": {"AT"},
        "mod": -8,
        "mod_label": "AT –8",
        "effekt": "waffe_x2",
        "tooltip": "Doppelter Waffenschaden (Zusatz-TP nicht verdoppelt).",
        "reqs": ["nahkampf", "vorteil:Hammerschlag"],
    },
    {
        "id": "klingentanz",
        "name": "Klingentanz",
        "kategorie": "aufbauend",
        "anwendbar": {"AT"},
        "mod": -4,
        "mod_label": "AT –4",
        "effekt": "klingentanz",
        "tooltip": (
            "Bei Erfolg sofort Folgeangriff (nicht erschwert). "
            "Kein Klingentanz seit letztem Beginn einer eigenen Initiativephase."
        ),
        "reqs": [
            "nahkampf",
            "vorteil:Klingentanz",
            "situativ:kein Klingentanz seit letztem Beginn einer eigenen Initiativephase",
        ],
    },
    {
        "id": "niederwerfen",
        "name": "Niederwerfen",
        "kategorie": "aufbauend",
        "anwendbar": {"AT"},
        "mod": -4,
        "mod_label": "AT –4",
        "effekt": "niederwerfen",
        "tooltip": "Ziel stürzt (Gegenprobe KK).",
        "reqs": ["nahkampf", "vorteil:Niederwerfen"],
    },
    {
        "id": "riposte",
        "name": "Riposte",
        "kategorie": "aufbauend",
        "anwendbar": {"VT"},
        "mod": -4,
        "mod_label": "VT –4",
        "effekt": "riposte",
        "tooltip": (
            "Dem Angreifer deinen Waffenschaden zufügen. "
            "Kombinierbar mit AT-Manövern (zusätzlicher VT-Malus + TP-Effekt). "
            "Keine Riposte seit letztem Beginn einer eigenen Initiativephase."
        ),
        "reqs": [
            "nahkampf",
            "vorteil:Parierwaffenkampf III",
            "situativ:Kampf in diesem Stil; keine Riposte seit letztem Beginn einer eigenen Initiativephase",
        ],
    },
    {
        "id": "schildwall",
        "name": "Schildwall",
        "kategorie": "aufbauend",
        "anwendbar": {"VT"},
        "mod": -4,
        "mod_label": "VT –4",
        "effekt": "schildwall",
        "tooltip": (
            "Angriff auf benachbarten Verbündeten abwehren. "
            "Kein Schildwall seit letztem Beginn einer eigenen Initiativephase."
        ),
        "reqs": [
            "nahkampf",
            "vorteil:Schildkampf III",
            "situativ:Kampf in diesem Stil; kein Schildwall seit letztem Beginn einer eigenen Initiativephase",
        ],
    },
    {
        "id": "sturmangriff",
        "name": "Sturmangriff",
        "kategorie": "aufbauend",
        "anwendbar": {"AT"},
        "mod": 0,
        "mod_label": "Bewegung + AT",
        "effekt": "sturmangriff",
        "tooltip": "Bewegung+Konflikt nicht erschwert; +GS TP.",
        "reqs": [
            "nahkampf",
            "vorteil_any:Sturmangriff|Reiterkampf I",
            "situativ:Bewegung vor dem Angriff",
        ],
    },
    {
        "id": "todesstoss",
        "name": "Todesstoß",
        "kategorie": "aufbauend",
        "anwendbar": {"AT"},
        "mod": -8,
        "mod_label": "AT –8",
        "effekt": "extra_wunden_2",
        "tooltip": "+2 Wunden (auch bei zu geringem Schaden).",
        "reqs": ["nahkampf", "vorteil:Todesstoß"],
    },
    {
        "id": "ueberrennen",
        "name": "Überrennen",
        "kategorie": "aufbauend",
        "anwendbar": {"AT"},
        "mod": 0,
        "mod_label": "Bewegung + AT",
        "effekt": "ueberrennen",
        "tooltip": (
            "Überrennen (Bewegung und AT)\n"
            "Wirkung: Das Reittier stürmt in die gegnerische Formation. Seine Attacke "
            "trifft (samt anderen Manövern) alle Gegner in seiner Bahn, bis es durch "
            "mindestens 2 erfolgreiche Verteidigungen gestoppt wird. Außerdem richtet "
            "die Attacke GS Trefferpunkte zusätzlich an. Die Kombination der Aktionen "
            "Bewegung und Konflikt ist nicht erschwert.\n"
            "Voraussetzungen: Vorteil Reiterkampf III und Kampf in diesem Stil; "
            "GS Schritt Anlauf; Ziele sind in einer kleineren Größenklasse als das Reittier."
        ),
        "reqs": [
            "nahkampf",
            "vorteil:Reiterkampf III",
            "situativ:Kampf in diesem Stil; GS Schritt Anlauf; Ziele kleinere Größenklasse",
        ],
    },
    {
        "id": "unterlaufen",
        "name": "Unterlaufen",
        "kategorie": "aufbauend",
        "anwendbar": {"VT"},
        "mod": -4,
        "mod_label": "VT –4",
        "effekt": "unterlaufen",
        "tooltip": (
            "Bei gelungener VT: Freie Aktion für weiteren Angriff nächste INI. "
            "Kein Unterlaufen seit letztem Beginn einer eigenen Initiativephase."
        ),
        "reqs": [
            "nahkampf",
            "vorteil:Schneller Kampf III",
            "situativ:Kampf in diesem Stil; kein Unterlaufen seit letztem Beginn einer eigenen Initiativephase",
        ],
    },
    # --- Fernkampfmanöver ---
    {
        "id": "gezielter_schuss",
        "name": "Gezielter Schuss",
        "kategorie": "fernkampf",
        "anwendbar": {"FK", "AT"},  # AT-Label wird bei FK-Waffen genutzt
        "mod": -2,
        "mod_label": "FK –2",
        "effekt": "trefferzone",
        "tooltip": "Trefferzone selbst bestimmen.",
        "reqs": ["fernkampf", "situativ:Trefferzonen"],
    },
    {
        "id": "reichweite_erhoehen",
        "name": "Reichweite erhöhen",
        "kategorie": "fernkampf",
        "anwendbar": {"FK", "AT"},
        "mod": -4,
        "mod_label": "FK –4",
        "effekt": "reichweite",
        "tooltip": "Reichweite verdoppelt sich (bis 2×).",
        "reqs": ["fernkampf"],
    },
    {
        "id": "scharfschuss",
        "name": "Scharfschuss",
        "kategorie": "fernkampf",
        "anwendbar": {"FK", "AT"},
        "mod": "variable",
        "mod_label": "FK –X",
        "effekt": "tp_bonus",
        "tooltip": "+X TP (max. 8).",
        "reqs": ["fernkampf"],
    },
    {
        "id": "zielen",
        "name": "Zielen",
        "kategorie": "fernkampf",
        "anwendbar": {"FK", "AT"},
        "mod": 2,
        "mod_label": "FK +2",
        "effekt": "zielen",
        "tooltip": "Vorbereitungszeit +1 Aktion (Ruhige Hand verdoppelt Bonus).",
        "reqs": ["fernkampf"],
    },
    {
        "id": "meisterschuss",
        "name": "Meisterschuss",
        "kategorie": "fernkampf",
        "anwendbar": {"FK", "AT"},
        "mod": -8,
        "mod_label": "FK –8",
        "effekt": "extra_wunden_2",
        "tooltip": "+2 Wunden (auch bei zu geringem Schaden).",
        "reqs": ["fernkampf", "vorteil:Meisterschuss"],
    },
    {
        "id": "ruestungsbrecher_fk",
        "name": "Rüstungsbrecher",
        "kategorie": "fernkampf",
        "anwendbar": {"FK", "AT"},
        "mod": -4,
        "mod_label": "FK –4",
        "effekt": "sp_statt_tp",
        "tooltip": "SP statt TP. Voraussetzung: Waffe oder Munition rüstungsbrechend.",
        "reqs": ["fernkampf", "waffe:Rüstungsbrechend"],
    },
    {
        "id": "schnellschuss",
        "name": "Schnellschuss",
        "kategorie": "fernkampf",
        "anwendbar": {"FK", "AT"},
        "mod": -4,
        "mod_label": "FK –4",
        "effekt": "schnellschuss",
        "tooltip": "Vorbereitungszeit halbieren (1→0). Bis 2× pro FK.",
        "reqs": ["fernkampf", "vorteil:Schnellziehen"],
    },
]


# Reine AT-Manöver für Riposte-Kombi (kein AT/VT, keine Bewegung).
# Sturmangriff/Überrennen ausgeschlossen (Bewegung nur in eigener Runde).
# Schaden-0-Manöver sind erlaubt – dann kein Weiter→Schaden.
RIPOSTE_EXCLUDE_IDS = frozenset({
    "sturmangriff", "ueberrennen", "entfernung_veraendern",
})
# Diese Manöver schließen sich gegenseitig aus (VT-Liste + Riposte-Kasten).
MUTUALLY_EXCLUSIVE_MANOEVER = frozenset({
    "schildspalter", "umklammern", "entwaffnen", "umreissen",
})


def riposte_combinable_manöver(
    *,
    is_fk: bool,
    has_vorteil,
    weapon_has_eigenschaft,
    is_waffenlos: bool = False,
) -> list:
    """
    Liste reiner AT-Manöver für den Riposte-Kombinationskasten.
    Keine AT/VT-Manöver (stehen schon bei VT), keine Bewegungs-Manöver.
    Schaden-0 ist erlaubt.
    """
    out = []
    for m in MANOEVER:
        anw = m.get("anwendbar") or set()
        if anw != {"AT"}:
            continue
        if m.get("id") in RIPOSTE_EXCLUDE_IDS:
            continue
        if not manöver_available(
            m,
            probe_type="AT",
            is_fk=is_fk,
            has_vorteil=has_vorteil,
            weapon_has_eigenschaft=weapon_has_eigenschaft,
            is_waffenlos=is_waffenlos,
        ):
            continue
        out.append(m)
    return out


def manöver_label(m: dict, compact: bool = False) -> str:
    """Anzeigename inkl. Mod und situativer Hinweise in Klammern."""
    situ = []
    for r in m.get("reqs") or []:
        if r.startswith("situativ:"):
            situ.append(r[9:])
    mark = m.get("mark") or ""
    if compact:
        mod = m.get("mod_label") or ""
        short_mod = mod
        for prefix in ("AT ", "VT ", "FK ", "zwei "):
            if short_mod.startswith(prefix):
                short_mod = short_mod[len(prefix):]
        if short_mod.startswith("Bewegung"):
            short_mod = "Bew+AT"
        label = m["name"]
        if short_mod:
            label = f"{label} ({short_mod})"
        if mark:
            label = f"{mark}{label}{mark}"
        elif situ:
            label = f"{label}*"
        return label
    parts = [m["name"]]
    if m.get("mod_label"):
        parts.append(f"({m['mod_label']})")
    if situ:
        parts.append("(" + "; ".join(situ) + ")")
    text = " ".join(parts)
    if mark:
        text = f"{mark}{text}{mark}"
    return text


def roll_gegenprobe(pw: int, against_ew, label: str = "Gegenprobe") -> tuple[int, str]:
    """
    Würfelt 1W20 + PW gegen against_ew.
    Returns (total, html_detail) inkl. Würfel und Erfolg/Misserfolg.
    """
    die = random.randint(1, 20)
    total = int(pw or 0) + die
    try:
        target = int(against_ew)
        ok = total >= target
        verdict = "<b style='color:#2a7a2a'>Erfolg</b>" if ok else "<b style='color:#a12323'>Misserfolg</b>"
        detail = (
            f"{label}: 1W20 ({die}) + PW {pw} = <b>{total}</b> "
            f"gegen {target} → {verdict}"
        )
    except (TypeError, ValueError):
        detail = f"{label}: 1W20 ({die}) + PW {pw} = <b>{total}</b> (Ziel-EW: {against_ew})"
    return total, detail


def manöver_tp_hinweis(m: dict, *, spin_val: int = 0, at_ew=None):
    """Text für TP-/Ergebnisanzeige zu einem aktiven Manöver."""
    effekt = m.get("effekt")
    name = m.get("name", "Manöver")
    if effekt == "tp_bonus":
        return f"+{spin_val or 'X'} TP ({name})"
    if effekt == "sp_statt_tp":
        return "SP statt TP (Rüstungsbrecher)"
    if effekt == "extra_wunden_2":
        return "+2 Wunden"
    if effekt == "waffe_x2":
        return "doppelter Waffenschaden (Hammerschlag)"
    if effekt == "schild_schaden":
        return "Schaden geht auf den Schild (Schildspalter)"
    if effekt == "erschoepfung":
        return "Erschöpfung statt Wunden (Stumpfer Schlag)"
    if effekt == "schaden_0":
        if m.get("id") == "umreissen":
            ew = at_ew if at_ew is not None else "AT-EW"
            return (
                f"Kein Schaden – Gegner: Gegenprobe gegen {ew} "
                f"(GE, bzw. KO bei großen/sehr großen Gegnern)"
            )
        if m.get("id") == "entwaffnen":
            ew = at_ew if at_ew is not None else "AT-EW"
            return f"Kein Schaden – Entwaffnen: Gegenprobe KK gegen {ew}"
        if m.get("id") == "umklammern":
            return f"Kein Schaden – Umklammern aktiv (–{spin_val or 'X'} Handlungen, GS 0)"
        return "Kein Schaden (Manöver)"
    if effekt == "trefferzone":
        return "Trefferzone selbst gewählt"
    if effekt == "ausfall":
        return "Ausfall: Ziel weicht bis 2 Schritt zurück"
    if effekt == "niederwerfen":
        ew = at_ew if at_ew is not None else "AT-EW"
        return f"Niederwerfen: Gegenprobe KK gegen {ew}"
    if effekt == "riposte":
        return "Riposte: Angreifer erleidet deinen Waffenschaden"
    if effekt == "auflaufen":
        return "Auflaufen lassen: Angreifer erleidet Waffenschaden + GS"
    if effekt == "binden":
        return f"Binden: Gegner-VT –{spin_val or 'X'} bis Ende nächster INI"
    if effekt == "ausweichen":
        return "Ausweichen: Angriff vollständig vermieden"
    if effekt == "sturmangriff":
        if spin_val:
            return f"Sturmangriff: +{spin_val} TP"
        return "Sturmangriff: +GS TP"
    if effekt == "ueberrennen":
        if spin_val:
            return f"Überrennen: +{spin_val} TP, alle in der Bahn"
        return "Überrennen: +GS TP, alle in der Bahn"
    if effekt == "klingentanz":
        return "Klingentanz: Folgeangriff (nicht erschwert)"
    if effekt == "unterlaufen":
        return "Unterlaufen: Freie Aktion Angriff nächste INI"
    if effekt == "schildwall":
        return "Schildwall: Angriff auf Verbündeten abgewehrt"
    if effekt == "schnellschuss":
        return "Schnellschuss: Vorbereitungszeit halbiert"
    if effekt == "reichweite":
        return "Reichweite verdoppelt"
    if effekt == "zielen":
        return "Zielen: Vorbereitungszeit +1"
    if effekt in ("befreiungsschlag", "doppelangriff", "entfernung"):
        return name
    return name


def manöver_available(
    m: dict,
    *,
    probe_type: str,
    is_fk: bool,
    has_vorteil,
    weapon_has_eigenschaft,
    is_waffenlos: bool = False,
) -> bool:
    """
    has_vorteil(name) -> bool
    weapon_has_eigenschaft(prop) -> bool
    probe_type: "AT" | "VT" | "FK"
    """
    anw = m.get("anwendbar") or set()
    # Bei FK-Waffen behandeln wir AT-Proben als FK-Kontext
    effective = "FK" if (probe_type == "AT" and is_fk) else probe_type
    if effective == "FK":
        if "FK" not in anw and not ("AT" in anw and "fernkampf" in (m.get("reqs") or [])):
            # Fernkampf-Manöver explizit oder AT-fähig mit fernkampf-req
            if "FK" not in anw:
                return False
    else:
        if effective not in anw:
            return False

    # Immer verfügbar (z. B. Umklammern) – Voraussetzungen nur im Tooltip
    if m.get("always"):
        return True

    for req in m.get("reqs") or []:
        if req == "fernkampf":
            if not is_fk:
                return False
        elif req == "nahkampf":
            if is_fk:
                return False
        elif req == "waffenlos":
            if not is_waffenlos:
                return False
        elif req.startswith("vorteil:"):
            if not has_vorteil(req[8:]):
                return False
        elif req.startswith("vorteil_any:"):
            names = req[12:].split("|")
            if not any(has_vorteil(n.strip()) for n in names):
                return False
        elif req.startswith("waffe:"):
            if not weapon_has_eigenschaft(req[6:]):
                return False
        elif req.startswith("situativ:"):
            # immer anzeigen, Hinweis steht im Label
            pass
        elif req.startswith("setting:"):
            # Optionalregeln: anzeigen (Hinweis im Label falls situativ)
            pass
    return True


# =============================================================================
# Kampf-Modifikatoren (Ilaris Tabellen Nahkampf / Fernkampf)
# =============================================================================
# Combo-Einträge: (Anzeigetext, Wert)
# Checkbox-Einträge: (id, Anzeigetext, Wert)

NK_MOD_POSITION = [
    ("normal", 0),
    ("überlegen (+4)", 4),
    ("vorteilhaft (+2)", 2),
    ("kniend (–2)", -2),
    ("liegend (–4)", -4),
]
NK_MOD_REICHWEITE = [
    ("normale Reichweite", 0),
    ("ideale Reichweite (+2)", 2),
    ("unpassende Reichweite (–2)", -2),
]
NK_MOD_UNTERGRUND = [
    ("normal", 0),
    ("unsicher / knietiefes Wasser (–2)", -2),
    ("eisig / hüfttiefes Wasser (–4)", -4),
    ("schultertiefes Wasser (–8)", -8),
]
NK_MOD_DUNKELHEIT = [
    ("normal", 0),
    ("Dämmerung (–2)", -2),
    ("Mondlicht (–4)", -4),
    ("Sternenlicht (–8)", -8),
]
NK_MOD_CHECKS = [
    ("nk_nebenwaffe", "Nebenwaffe (–4)", -4),
]

FK_MOD_GROESSE = [
    ("mittel (Mensch, Zwerg)", 0),
    ("sehr groß (Elefant) (+8)", 8),
    ("groß (Pferd, Oger) (+4)", 4),
    ("klein (Wolf, Reh) (–4)", -4),
    ("sehr klein (Fasan, Hase) (–8)", -8),
    ("winzig (Maus) (–12)", -12),
]
FK_MOD_LICHT = [
    ("normal", 0),
    ("Dämmerung (–4)", -4),
    ("Mondlicht (–8)", -8),
    ("Sternenlicht (–16)", -16),
]
FK_MOD_WIND = [
    ("kein Wind", 0),
    ("Wind (–4)", -4),
    ("Sturm (–8)", -8),
]
FK_MOD_BEWEGUNG = [
    ("keine", 0),
    ("schnell / laufender Mensch (–4)", -4),
    ("sehr schnell / Pferd (–8)", -8),
    ("extrem schnell / Vogel (–12)", -12),
]
FK_MOD_DECKUNG = [
    ("keine Deckung", 0),
    ("halbe Deckung (–4)", -4),
    ("Dreivierteldeckung (–8)", -8),
]
FK_MOD_CHECKS = [
    ("fk_beritten", "berittener Schütze (–4)", -4),
]


def apply_wounds_batch(wunden_list, n_ersch=0, n_wunden=0, mode=0):
    """
    Fügt Erschöpfung (/) und Wunden in einem Rutsch hinzu (eine Source).
    mode: 0=Normal (X), 1=Koloss I (I), 2=Koloss II (I).
    Returns (neue_liste, delta_ersch, delta_wunden).
    """
    w = list(wunden_list or [])
    while len(w) < 8:
        w.append(None)
    wound_mark = "X" if mode == 0 else "I"
    d_e = d_w = 0
    for _ in range(max(0, int(n_ersch or 0))):
        try:
            i = w.index(None)
        except ValueError:
            break
        w[i] = "/"
        d_e += 1
    for _ in range(max(0, int(n_wunden or 0))):
        try:
            i = w.index(None)
        except ValueError:
            break
        w[i] = wound_mark
        d_w += 1
    rank = {None: 0, "/": 1, "I": 2, "II": 3, "III": 4, "IV": 5, "X": 6}
    w.sort(key=lambda x: rank.get(x, 0), reverse=True)
    return w, d_e, d_w


def check_premature_timers(effects, delta_ersch, delta_wunden, source_id=None):
    """
    Setzt duration=0 wenn Schwelle aus EINER Source erreicht.
    Returns Liste von Hinweis-Dicts {name, message, interrupted}.
    """
    msgs = []
    de = max(0, int(delta_ersch or 0))
    dw = max(0, int(delta_wunden or 0))
    if de + dw <= 0:
        return msgs
    for eff in effects or []:
        if not isinstance(eff, dict):
            continue
        if not eff.get("has_timer"):
            continue
        if int(eff.get("duration", 0) or 0) <= 0:
            continue
        mode = eff.get("premature_mode")
        if not mode:
            continue
        x = max(1, int(eff.get("premature_x", 1) or 1))
        hit = False
        if mode == "einschr":
            hit = (de + dw) >= x
        elif mode == "wunden":
            hit = dw >= x
        elif mode == "ersch":
            hit = de >= x
        if not hit:
            continue
        eff["duration"] = 0
        eff["premature_fired"] = True
        focus = (eff.get("focus") or "").strip()
        name = eff.get("name") or "Effekt"
        custom = (eff.get("premature_interrupt_text") or "").strip()
        if custom:
            text = custom
            if focus and "{focus}" in text:
                text = text.replace("{focus}", focus)
            elif focus and focus not in text:
                text = f"{text} ({focus})"
        else:
            text = f"„{name}“ vorzeitig beendet"
            if focus:
                text += f" – {focus}"
            text += "."
        msgs.append({"name": name, "message": text, "interrupted": True, "focus": focus})
    return msgs


def concentration_ready_text(eff: dict) -> str:
    focus = (eff.get("focus") or "").strip()
    custom = (eff.get("on_end_notify_text") or "").strip()
    if custom and "{focus}" in custom:
        return custom.replace("{focus}", focus or "…")
    if focus:
        return f"Konzentration beendet – „{focus}“ ist bereit."
    if custom:
        return custom
    return "Konzentration beendet – bereit."


def check_condition_info(effects, delta_ersch, delta_wunden, source_id=None):
    """
    Wie premature, aber Timer bleibt – liefert Info-Texte (i-Button-Inhalt).
    """
    msgs = []
    de = max(0, int(delta_ersch or 0))
    dw = max(0, int(delta_wunden or 0))
    if de + dw <= 0:
        return msgs
    for eff in effects or []:
        if not isinstance(eff, dict):
            continue
        mode = eff.get("condition_info_mode")
        if not mode:
            continue
        x = max(1, int(eff.get("condition_info_x", 1) or 1))
        hit = False
        if mode == "einschr":
            hit = (de + dw) >= x
        elif mode == "wunden":
            hit = dw >= x
        elif mode == "ersch":
            hit = de >= x
        if not hit:
            continue
        name = eff.get("name") or "Effekt"
        focus = (eff.get("focus") or "").strip()
        text = (eff.get("info_text") or "").strip()
        if not text:
            text = f"Hinweis zu „{name}“."
        if focus:
            text = f"{text}\n\nGegenstand: {focus}"
        msgs.append({"name": name, "message": text, "focus": focus})
    return msgs


def combat_mod_from_combo(combo) -> tuple:
    """(wert, label) aus QComboBox-Daten."""
    if combo is None:
        return 0, ""
    data = combo.currentData()
    if data is None:
        return 0, ""
    val = int(data)
    text = combo.currentText()
    if val == 0:
        return 0, ""
    return val, text


# --- Würfel-Darstellung / Triumph & Patzer ---

_DIE_GREEN = '#1a7f37'
_DIE_RED = '#c0392b'


def format_die_html(n: int, sides: int = 20) -> str:
    """Einzelwürfel: 20 grün, 1 rot (nur bei W20)."""
    try:
        n = int(n)
        sides = int(sides)
    except (TypeError, ValueError):
        return str(n)
    s = str(n)
    if sides == 20 and n == 20:
        return f'<span style="color:{_DIE_GREEN};font-weight:bold">{s}</span>'
    if sides == 20 and n == 1:
        return f'<span style="color:{_DIE_RED};font-weight:bold">{s}</span>'
    return s


def format_w20_list(rolls) -> str:
    """Komma-getrennte W20-Liste mit Färbung."""
    return ", ".join(format_die_html(r, 20) for r in (rolls or []))


def format_roll_info_1w20(die: int) -> str:
    return f"1W20 ({format_die_html(die, 20)})"


def format_roll_info_3w20(rolls, middle: int) -> str:
    return f"3W20 ({format_w20_list(rolls)}) → {format_die_html(middle, 20)}"


def colorize_dice_in_text(text: str) -> str:
    """
    Färbt in bereits formatierten Würfelstrings nackte 1/20 innerhalb von
    Klammern nach W20-Würfen. Vorsichtig: nur Zahlen 1 und 20 als eigene Tokens.
    """
    import re
    if not text:
        return text

    def _repl(m):
        n = int(m.group(0))
        return format_die_html(n, 20)

    # Nur isolierte 1 oder 20 (Wortgrenzen), nicht Teile von 10/12/21
    return re.sub(r'(?<![\d])(20|1)(?![\d])', _repl, text)


def triumph_patzer_message(die: int, is_at: bool, is_vt: bool) -> str:
    """HTML-Hinweis bei natürlicher 20 / 1 im Kampfwurf."""
    if die == 20:
        who = "Attacke" if is_at else ("Verteidigung" if is_vt else "Wurf")
        return (
            f'<b style="color:{_DIE_GREEN}">Triumph!</b> ({who}) '
            f'Manöver mit variabler Schwierigkeit um bis zu 4 verbessern '
            f'oder zusätzliches Manöver (bis –4) – EW sinkt nicht.'
        )
    if die == 1:
        who = "Attacke" if is_at else ("Verteidigung" if is_vt else "Wurf")
        return (
            f'<b style="color:{_DIE_RED}">Patzer!</b> ({who}) '
            f'gilt als Triumph für den Gegner (dessen EW wie bei einer 20). '
            f'Spektakuläres Misslingen.'
        )
    return ""
