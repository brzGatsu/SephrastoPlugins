from EventBus import EventBus
from Wolke import Wolke
import os
import re
import json
from CharakterPrintUtility import CharakterPrintUtility
from Hilfsmethoden import Hilfsmethoden
import random
from Version import _sephrasto_version_major, _sephrasto_version_minor, _sephrasto_version_build

__version__ = "4.2.1.a"  # Plugin Version

def random_foundry_id():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choices(chars, k=16))

def getFoundryPackId(name):
    json_path = os.path.join(os.path.dirname(__file__), "foundry_advantage_id_names.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)  
    for key, value in data.items():
        if value == name:
            return key
    return ''

def create_item(name, type):
    if type == "vorteil":
        compendiumSource = "Compendium.Ilaris.vorteil.Item." + getFoundryPackId(name)
        return {
            "_id": random_foundry_id(),
            "name": name,
            "type": type,
            "img": "icons/svg/item-bag.svg",
            "data": {},
            "effects": [],
            "folder": None,
            "sort": 0,
            "permission": {},
            "flags": {},
            "_stats": {
                "compendiumSource": compendiumSource
            }
        }
    return {
        "_id": random_foundry_id(),
        "name": name,
        "type": type,
        "img": "icons/svg/item-bag.svg",
        "data": {},
        "effects": [],
        "folder": None,
        "sort": 0,
        "permission": {},
        "flags": {}
    }


def waffe_item(w):
    # dropped infos:
    # wafNode.set('id',waff.name)
    #     wafNode.set('kampfstil',waff.kampfstil)
    #         wafNode.set('lz',str(waff.lz))
    # print(w)
    wdata = {
        "haerte": w.härte,  # TODO
        "beschaedigung": 0,
        "dice_anzahl": w.würfel,
        "dice_plus": w.plus,
        "fertigkeit": w.fertigkeit,
        "talent": w.talent,
        "rw": w.rw,
        "hauptwaffe": False,
        "nebenwaffe": False,
        # TODO: make this a list in Foundry and write getters/checks if bools are required! #14
        # 'eigenschaften': w.eigenschaften,  # TODO: list of strings?
        # "eigenschaften": {
        #     "kopflastig": ("Kopflastig" in w.eigenschaften),
        #     "niederwerfen": ("Niederwerfen" in w.eigenschaften),
        #     "parierwaffe": ("Parierwaffe" in w.eigenschaften),
        #     "reittier": ("Reittier" in w.eigenschaften),
        #     "ruestungsbrechend": ("Rüstungsbrechend" in w.eigenschaften),
        #     "schild": ("Schild" in w.eigenschaften),
        #     "schwer_4": ("Schwer (4)" in w.eigenschaften),
        #     "schwer_8": ("Schwer (8)" in w.eigenschaften),
        #     "stumpf": ("Stumpf" in w.eigenschaften),
        #     "unberechenbar": ("Unberechenbar" in w.eigenschaften),
        #     "unzerstoerbar": ("Unzerstörbar" in w.eigenschaften),
        #     "wendig": ("Wendig" in w.eigenschaften),
        #     "zerbrechlich": ("Zerbrechlich" in w.eigenschaften),
        #     "zweihaendig": ("Zweihändig" in w.eigenschaften),
        #     "kein_malus_nebenwaffe": ("kein Malus als Nebenwaffe" in w.eigenschaften)
        # },
        "text": "",
        "aufbewahrungs_ort": "tragend",
        "bewahrt_auf": [],
        "gewicht_summe": 0,
        "gewicht": 0,
        "preis": 0,
        # TODO: is wm same for at/vt? Gatsu: yup
        "wm_at": w.wm,
        "wm_vt": w.wm,
        "mod_at": None,
        "mod_vt": None,
        "mod_schaden": ""
    }
    if w.nahkampf:
        # w.anzeigename  -> is empty
        waffe = create_item(w.anzeigename, "nahkampfwaffe")
        wdata['eigenschaften'] = {
            "kopflastig": ("Kopflastig" in w.eigenschaften),
            "niederwerfen": ("Niederwerfen" in w.eigenschaften),
            "parierwaffe": ("Parierwaffe" in w.eigenschaften),
            "reittier": ("Reittier" in w.eigenschaften),
            "ruestungsbrechend": ("Rüstungsbrechend" in w.eigenschaften),
            "schild": ("Schild" in w.eigenschaften),
            "schwer_4": ("Schwer (4)" in w.eigenschaften),
            "schwer_8": ("Schwer (8)" in w.eigenschaften),
            "stumpf": ("Stumpf" in w.eigenschaften),
            "unberechenbar": ("Unberechenbar" in w.eigenschaften),
            "unzerstoerbar": ("Unzerstörbar" in w.eigenschaften),
            "wendig": ("Wendig" in w.eigenschaften),
            "zerbrechlich": ("Zerbrechlich" in w.eigenschaften),
            "zweihaendig": ("Zweihändig" in w.eigenschaften),
            "kein_malus_nebenwaffe": ("kein Malus als Nebenwaffe" in w.eigenschaften)
        }
    else:
        waffe = create_item(w.anzeigename, "fernkampfwaffe")
        wdata['lz'] = w.lz
        wdata['eigenschaften'] = {
            "kein_reiter": ("kein Reittier" in w.eigenschaften),
            "niederwerfen": ("Niederwerfen" in w.eigenschaften),
            "niederwerfen_4": ("Niederwerfen (-4)" in w.eigenschaften),
            "niederwerfen_8": ("Niederwerfen (-8)" in w.eigenschaften),
            "schwer_4": ("Schwer (4)" in w.eigenschaften),
            "schwer_8": ("Schwer (8)" in w.eigenschaften),
            "stationaer": ("stationär" in w.eigenschaften),
            "stumpf": ("Stumpf" in w.eigenschaften),
            "umklammern_212": ("Umklammern (-2; 12)" in w.eigenschaften),
            "umklammern_416": ("Umklammern (-4; 16)" in w.eigenschaften),
            "umklammern_816": ("Umklammern (-8; 16)" in w.eigenschaften),
            "zweihaendig": ("Zweihändig" in w.eigenschaften)
        }
    waffe['data'] = wdata
    return waffe


class Plugin:
    def __init__(self):
        EventBus.addAction("charakter_geschrieben", self.json_schreiben)
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHandler)

    def json_schreiben_alt(self, params):
        params["filepath"] = params["filename"]
        params["charakter"] = Wolke.Char
        self.json_schreiben(None, params)

    def basisDatenbankGeladenHandler(self, params):
        self.db = params["datenbank"]

    def get_token(self, name):
        token = {
            "name": name,
            "img": "systems/Ilaris/assets/images/token/kreaturentypen/humanoid.png",
            "displayName": 20,
            "actorLink": False,
            "width": 1,
            "height": 1,
            "scale": 1,
            "mirrorX": False,
            "mirrorY": False,
            "lockRotation": False,
            "rotation": 0,
            "alpha": 1,
            "vision": True,
            "dimSight": 10,
            "brightSight": 5,
            "sightAngle": 0,
            "light": {
                "alpha": 0.5,
                "angle": 0,
                "bright": 0,
                "coloration": 1,
                "dim": 0,
                "gradual": True,
                "luminosity": 0.5,
                "saturation": 0,
                "contrast": 0,
                "shadows": 0,
                "animation": {
                    "speed": 5,
                    "intensity": 5,
                    "reverse": False
                },
                "darkness": {
                    "min": 0,
                    "max": 1
                }
            },
            "disposition": 1,
            "displayBars": 50,
            "bar1": {
                "attribute": "gesundheit.hp"
            },
            "bar2": {
                "attribute": None
            },
            "flags": {},
            "randomImg": False
        }
        return token

    def get_items(self):
        """ The data models defined in the Foundry system are called items.
        They use templates and are collected in a huge list with unique random id's.
        This function creates such items for:
        - Vorteil
        - Fertigkeit
        - Eigenheit
        - Waffe
        - Talent
        """
        items = []
        # -- Vorteile -- #
        for v in self.char.vorteile.values():
            item = create_item(v.name, "vorteil") # TODO: v.anzeigenameExt enthält mit dem Kommentar wichtige Infos, die in .name fehlen
            item["data"] = {
                # "voraussetzung": ", ".join(vorteil.voraussetzungen),
                "voraussetzung": v.voraussetzungen.anzeigetext(self.db),
                "gruppe": v.kategorie, # "Kampfvorteile" etc.
                "text": Hilfsmethoden.fixHtml(v.text)
            }
            # print(self.char.vorteileVariable)
            items.append(item)
        # # -- Eigenheiten -- #
        for e in self.char.eigenheiten:
            if e:
                item = create_item(e, "eigenheit")
                items.append(item)
        # # -- Fertigkeiten -- #
        for f in self.char.fertigkeiten.values():
            # ist das jetzt ein dict?
            item = create_item(f.name, "fertigkeit")
            item["data"] = {
                "basis": 0,
                "fw": f.wert,
                "pw": f.probenwert,
                "pwt": f.probenwertTalent,
                "attribut_0": f.attribute[0],
                "attribut_1": f.attribute[1],
                "attribut_2": f.attribute[2],
                "gruppe": f.kategorie, # "Nahkampffertigkeiten" etc.
                "text": Hilfsmethoden.fixHtml(f.text)
            }
            items.append(item)
        # -- Talente -- #
        for t in self.char.talente.values():
            if t.spezialTalent:
                continue
            item = create_item(t.name, "talent") # TODO: t.anzeigename enthält mit dem Kommentar wichtige Infos, die in .name fehlen
            item["data"] = {
                "fertigkeit": t.hauptfertigkeit.name, # TODO Gatsu: auch profane talente können theoretisch mehreren fertigkeiten zugewiesen werden
            }
            items.append(item)
        # -- Freie Fertigkeiten -- #
        for ff in self.char.freieFertigkeiten:
            if not ff.name:
                continue
            item = create_item(ff.name, "freie_fertigkeit")
            item['data'] = {
                "stufe": ff.wert,
                "text": ff.name,
                "gruppe": "1"
            }
            items.append(item)
        # -- Übernatürliche Fertigkeiten -- #
        for uef in self.char.übernatürlicheFertigkeiten.values():
            item = create_item(uef.name, "uebernatuerliche_fertigkeit")
            item["data"] = {
                "basis": uef.basiswert,
                "fw": uef.wert,
                "pw": uef.probenwertTalent,  # TODO: eigentlich pwt.. aber ist in fvtt einfach pw für übernat fix in foundry
                "attribut_0": uef.attribute[0],
                "attribut_1": uef.attribute[1],
                "attribut_2": uef.attribute[2],
                "gruppe": uef.kategorie, # "Traditionszauber" etc.
                "text": Hilfsmethoden.fixHtml(uef.text),
                "voraussetzung": uef.voraussetzungen.anzeigetext(self.db),
            }
            items.append(item)
        # -- Zauber -- #
        for t in self.char.talente.values():
            if not t.spezialTalent:
                continue
            item = create_item(t.name, "zauber") # TODO: t.anzeigename enthält mit dem Kommentar wichtige Infos, die in .name fehlen
            item["data"] = {
                "fertigkeit_ausgewaehlt": "auto",
                "fertigkeiten": ", ".join(t.fertigkeiten),
                "text": Hilfsmethoden.fixHtml(t.text),
                "gruppe": t.kategorie, # "Liturgien" etc.
                "pw": -1,  # TODO: warum hat talent/zauber ein pw?? sollte aus fertigkeit kommen. Gatsu: t.probenwert ist der höchste pw aller fertigkeiten des talents
                "vorbereitung" : t.vorbereitungszeit,
                "reichweite" : t.reichweite,
                "wirkungsdauer" : t.wirkungsdauer,
                "kosten" : t.energieKosten
            }

            items.append(item)

        # # -- Waffen -- #
        for w in self.char.waffen:
            if not w.anzeigename:
                continue
            item = waffe_item(w)
            items.append(item)
        # -- Rüstung -- #
        for r in self.char.rüstung:
            if not r.name:
                continue
            item = create_item(r.name, "ruestung")
            item["data"] = {
                "rs": r.getRSGesamtInt(),
                "be": r.be,
                "rs_beine": r.rs[0],
                "rs_larm": r.rs[1],
                "rs_rarm": r.rs[2],
                "rs_bauch": r.rs[3],
                "rs_brust": r.rs[4],
                "rs_kopf": r.rs[5],
                "aktiv": False,
                "text": Hilfsmethoden.fixHtml(r.text)
            }
            items.append(item)
        # -- Inventar -- #
        for a in self.char.ausrüstung:
            if not a:
                continue
            item = create_item(a, "gegenstand")
            item["data"] = {}
            items.append(item)
        return items

    def get_abgeleitet(self):
        item = {  # updated by foundry
            "globalermod": 0,
            "ws": 0,
            "ws_stern": 0,
            "be": 0,
            "be_traglast": 0,
            "ws_beine": 0,
            "ws_larm": 0,
            "ws_rarm": 0,
            "ws_bauch": 0,
            "ws_brust": 0,
            "ws_kopf": 0,
            "mr": 0,
            "gs": 0,
            "ini": 0,
            "dh": 0,
            "traglast_intervall": 0,
            "traglast": 0,
            # TODO: folgende werte werden nicht abgeleitet
            # "gasp": None,
            # "asp_stern": None,
            # "gkap": None,
            # "kap_stern": None,
        }

        for en in self.char.energien.values():
            item[en.name.lower() + "_zugekauft"] = en.wert

        return item

    def json_schreiben(self, params):
        """Funktion wird als Action in Charakter.saveFile (speichern)
        angewendet. Aus params['charakter'] wird die json file für foundry generiert und gespeichert.
        """
        self.char = params['charakter']
        self.actor = {}

        name = self.char.name
        if not name:
            name = os.path.splitext(os.path.basename(params["filepath"]))[0]

        # direct keys
        attribute = {attr: {
            "wert": self.char.attribute[attr].wert, "pw": 0} for attr in self.char.attribute}
        notes = self.char.notiz
        data = {
            "gesundheit": {
                "erschoepfung": 0,
                "wunden": 0,
                "wundabzuege": 0,
                "wundenignorieren": 0,
                "display": "Volle Gesundheit",
                "hp": {
                    "max": 9,
                    "value": 9,
                    "threshold": 0
                }
            },
            "attribute": attribute,
            "abgeleitete": self.get_abgeleitet(),
            "schips": {
                "schips": self.char.abgeleiteteWerte["SchiP"].wert,
                "schips_stern": self.char.abgeleiteteWerte["SchiP"].wert, #TODO Gatsu: .finalwert für den durch finanzen modifizierten "aktuellen" wert, vermutlich aber nciht so sinnvoll
            },
            "initiative": 0,
            "furcht": {
                "furchtstufe": 0,
                "furchtabzuege": 0,
                "display": ""
            },
            "modifikatoren": {
                "manuellermod": 0,
                "nahkampfmod": 0
            },
            "geld": {
                "dukaten": 0,
                "silbertaler": 0,
                "heller": 0,
                "kreuzer": 0
            },
            "getragen": 1,  # TODO: Tragend = welche nummer?
            "notes": notes,
            "misc": {
                "selected_kampfstil": "kvk"
            }
        }
        actor = {
            # TODO: include base encoded character image?
            # "_id": random_foundry_id(),
            "name": name,
            "type": "held",
            "img": "systems/Ilaris/assets/images/token/kreaturentypen/humanoid.png",
            "data": data,
            "token": self.get_token(name),
            "items": self.get_items(),
            "effects": []
        }
        # Dropped Infos
        # content.append("Spezies: " + char.rasse)
        # content.append("Status: " + Definitionen.Statusse[char.status])
        # content.append("Heimat: " + char.heimat)

        # content.append("\n=== Allgemeine und Profane Vorteile === ")
        # vorteile = CharakterPrintUtility.getVorteile(char)
        # (vorteileAllgemein, vorteileKampf, vorteileUeber) = CharakterPrintUtility.groupVorteile(char, vorteile, link = True)
        # for v in vorteileAllgemein:
        #     content.append(v)

        # content.append("\n=== Profane Fertigkeiten === ")

        # fertigkeitsTypen = Wolke.DB.einstellungen["Fertigkeiten: Typen profan"].toTextList()
        # lastType = -1
        # for f in CharakterPrintUtility.getFertigkeiten(char):
        #     fert = char.fertigkeiten[f]
        #     if lastType != fert.printclass:
        #         content.append("\n" + fertigkeitsTypen[fert.printclass] + ":")
        #         lastType = fert.printclass

        #     talente = CharakterPrintUtility.getTalente(char, fert)
        #     talentStr = " "
        #     if len(talente) > 0:
        #         talentStr = " (" + ", ".join([t.anzeigeName for t in talente]) + ") "
        #     content.append(fert.name + talentStr + str(fert.probenwert) + "/" + str(fert.probenwertTalent))

        # content.append("\nFreie Fertigkeiten:")
        # for fert in CharakterPrintUtility.getFreieFertigkeiten(char):
        #     content.append(fert)

        # content.append("\nVorteile:")
        # for v in vorteileKampf:
        #     content.append(v)

        # content.append("\nRüstungen:")
        # for rüstung in char.rüstung:
        #     if not rüstung.name:
        #         continue
        #     content.append(rüstung.name + " RS " + str(int(rüstung.getRSGesamt())) + " BE " + str(rüstung.be))

        # content.append("\nWaffen:")
        # count = 0
        # for waffe in char.waffen:
        #     if not waffe.name:
        #         continue

        #     werte = char.waffenwerte[count]
        #     keinSchaden = waffe.W6 == 0 and waffe.plus == 0
        #     sg = ""
        #     if waffe.plus >= 0:
        #         sg = "+"
        #     content.append(waffe.anzeigename + " AT " + str(werte.AT) + " VT " + str(werte.VT) + " " + ("-" if keinSchaden else str(werte.TPW6) + "W6" + sg + str(werte.TPPlus)))
        #     if len(waffe.eigenschaften) > 0:
        #         content.append(", ".join(waffe.eigenschaften))
        #     content.append("")
        #     count += 1
        # content.pop()

        # content.append("\n=== Übernatürliche Fertigkeiten und Talente ===")

        # content.append("\nÜbernatürliche Fertigkeiten:")
        # for f in CharakterPrintUtility.getÜberFertigkeiten(char):
        #     fert = char.übernatürlicheFertigkeiten[f]
        #     content.append(fert.name + " " + str(fert.probenwertTalent))

        # content.append("\nÜbernatürliche Talente:")
        # for talent in CharakterPrintUtility.getÜberTalente(char):
        #     content.append(talent.anzeigeName + " " + str(talent.pw))

        path = os.path.splitext(params["filepath"])[0] + "_foundryvtt.json"
        with open(path, 'w', encoding="utf-8") as f:
            json.dump(actor, f, indent=2)

        self.char = None
