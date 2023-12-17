import datetime as dt
from Wolke import Wolke


def span(text, color):
    return f"<span style='color: {color}'>{text}</span>"

def colorize(number):
    if number > 0:
        return span(f"+{number}", COLOR_POSITIVE)
    if number < 0:
        return span(number, COLOR_NEGATIVE)

COLOR_DEFAULT = "black"
COLOR_POSITIVE = "green"
COLOR_NEGATIVE = "red"
HINZUGEFÜGT = span("hinzugefügt", COLOR_POSITIVE)
ENTFERNT = span("entfernt", COLOR_NEGATIVE)
GEKAUFT = span("gekauft", COLOR_POSITIVE)
GELÖSCHT = span("gelöscht", COLOR_NEGATIVE)


class Eintrag():

    def __init__(self, ep) -> None:
        self.datum = dt.datetime.now()
        self.ep = ep
        self.epGewinn = 0
        self.epAusgabe = 0
        self.notiz = ""
        self.eigenheiten = []
        self.attribute = []
        self.energien = []
        self.vorteile = []
        self.freieFertigkeiten = []
        self.fertigkeiten = []
        self.übernatürlicheFertigkeiten = []
        self.talente = []
    
    def compare(self, alt, neu, reset=True):
        if reset:
            self.epGewinn = 0
            self.epAusgabe = 0
        self.epGewinn += neu.epGesamt - alt.epGesamt
        self.epAusgabe += neu.epAusgegeben - alt.epAusgegeben
        self.compareEigenheiten(alt, neu, reset)
        self.compareAttribute(alt, neu, reset)
        self.compareEnergien(alt, neu, reset)
        self.compareVorteile(alt, neu, reset)
        self.compareFreieFertigkeiten(alt, neu, reset)
        self.compareFertigkeiten(alt, neu, reset)
        self.compareÜbernatürlicheFertigkeiten(alt, neu, reset)
        self.compareTalente(alt, neu, reset)

    @property
    def totalChanges(self):
        return (
            abs(int(self.epGewinn)) +
            len(self.eigenheiten) + 
            len(self.attribute) +
            len(self.energien) +
            len(self.vorteile) +
            len(self.freieFertigkeiten) +
            len(self.fertigkeiten) +
            len(self.übernatürlicheFertigkeiten) +
            len(self.talente)
        )
    
    def compareEnergien(self, alt, neu, reset=True):
        if reset:
            self.energien = []
        for en in sorted(Wolke.DB.energien):
            neuNamen = neu.energien.keys() # [e.name for e in neu.energien] 
            altNamen = neu.energien.keys() # [e.name for e in alt.energien]
            delta = 0
            if en not in neuNamen and en not in altNamen:
                continue
            if en in neuNamen and en not in altNamen:
                self.energien.append(f"{en}: {colorize('hinzugefügt')}")
                delta = neu.energien[en.name].wert
            elif en not in neuNamen and en in altNamen:
                self.energien.append(f"{en}: {colorize('entfernt')}")
            if en in neuNamen and en in altNamen:
                delta = neu.energien[en].wert - alt.energien[en].wert
            if delta:
                self.energien.append(f"{en}: {colorize(delta)}")
                
    
    def compareVorteile(self, alt, neu, reset=True):
        if reset:
            self.vorteile = []
        for vorteil in sorted(Wolke.DB.vorteile):
            if vorteil not in alt.vorteile and vorteil not in neu.vorteile:
                continue
            elif vorteil in neu.vorteile and vorteil not in alt.vorteile:
                self.vorteile.append(f"{vorteil}: {HINZUGEFÜGT}")
            elif vorteil not in neu.vorteile and vorteil in alt.vorteile:
                self.vorteile.append(f"{vorteil}: {ENTFERNT}")
            elif neu.vorteile[vorteil].kosten != alt.vorteile[vorteil].kosten:
                self.vorteile.append(f"{vorteil}: geändert (Kosten {neu.vorteile[vorteil].kosten - alt.vorteile[vorteil].kosten} EP)")

    def compareTalente(self, alt, neu, reset=True):
        if reset:
            self.talente = []
        for talent in sorted(Wolke.DB.talente):
            if talent not in alt.talente and talent not in neu.talente:
                continue
            elif talent in neu.talente and talent not in alt.talente:
                self.talente.append(f"{talent}: {GEKAUFT}")
            elif talent not in neu.talente and talent in alt.talente:
                self.talente.append(f"{talent}: {ENTFERNT}")
            elif neu.talente[talent].kosten != alt.talente[talent].kosten:
                self.talente.append(f"{talent}: geändert (Kosten {neu.talente[talent].kosten - alt.talente[talent].kosten} EP)")
         
    def compareFreieFertigkeiten(self, alt, neu, reset=True):
        if reset:
            self.freieFertigkeiten = []
        for freie in sorted(Wolke.DB.freieFertigkeiten):
            if freie not in alt.freieFertigkeiten and freie not in neu.freieFertigkeiten:
                continue
            elif freie in neu.freieFertigkeiten and freie not in alt.freieFertigkeiten:
                self.freieFertigkeiten.append(f"{freie}: {GEKAUFT}")
            elif freie not in neu.freieFertigkeiten and freie in alt.freieFertigkeiten:
                self.freieFertigkeiten.append(f"{freie}: {ENTFERNT}")
            elif neu.freieFertigkeiten[freie].wert != alt.freieFertigkeiten[freie].wert:
                delta = neu.freieFertigkeiten[freie].wert - alt.freieFertigkeiten[freie].wert
                self.freieFertigkeiten.append(f"{freie}: {colorize(delta)}")

    def compareFertigkeiten(self, alt, neu, reset=True):
        if reset:
            self.fertigkeiten = []
        for fertigkeit in sorted(Wolke.DB.fertigkeiten):
            if fertigkeit not in alt.fertigkeiten and fertigkeit not in neu.fertigkeiten:
                continue
            elif fertigkeit in neu.fertigkeiten and fertigkeit not in alt.fertigkeiten:
                self.fertigkeiten.append(f"{fertigkeit}: {GEKAUFT}")
            elif fertigkeit not in neu.fertigkeiten and fertigkeit in alt.fertigkeiten:
                self.fertigkeiten.append(f"{fertigkeit}: {ENTFERNT}")
            elif neu.fertigkeiten[fertigkeit].wert != alt.fertigkeiten[fertigkeit].wert:
                delta = neu.fertigkeiten[fertigkeit].wert - alt.fertigkeiten[fertigkeit].wert
                self.fertigkeiten.append(f"{fertigkeit}: {colorize(delta)}")
                
    def compareÜbernatürlicheFertigkeiten(self, alt, neu, reset=True):
        if reset:
            self.übernatürlicheFertigkeiten = []
        for fert in sorted(Wolke.DB.übernatürlicheFertigkeiten):
            if (fert not in alt.übernatürlicheFertigkeiten 
            and fert not in neu.übernatürlicheFertigkeiten):
                continue
            elif fert in neu.übernatürlicheFertigkeiten and fert not in alt.übernatürlicheFertigkeiten:
                self.übernatürlicheFertigkeiten.append(f"{fert}: {GEKAUFT}")
            elif fert not in neu.übernatürlicheFertigkeiten and fert in alt.übernatürlicheFertigkeiten:
                self.übernatürlicheFertigkeiten.append(f"{fert}: {ENTFERNT}")
            elif neu.übernatürlicheFertigkeiten[fert].wert != alt.übernatürlicheFertigkeiten[fert].wert:
                delta = neu.übernatürlicheFertigkeiten[fert].wert - alt.übernatürlicheFertigkeiten[fert].wert
                self.übernatürlicheFertigkeiten.append(f"{fert}: {colorize(delta)}")
       
    def compareAttribute(self, alt, neu, reset=True):
        if reset:
            self.attribute = []
        for attr in sorted(Wolke.DB.attribute):
            if attr not in alt.attribute and attr not in neu.attribute:
                continue
            elif attr in neu.attribute and attr not in alt.attribute:
                self.attribute.append(f"{attr}: {GEKAUFT}")
            elif attr not in neu.attribute and attr in alt.attribute:
                self.attribute.append(f"{attr}: {ENTFERNT}")
            elif neu.attribute[attr].wert != alt.attribute[attr].wert:
                delta = neu.attribute[attr].wert - alt.attribute[attr].wert
                self.attribute.append(f"{attr}: {colorize(delta)}")

    def compareEigenheiten(self, alt, neu, reset=True):
        if reset:
            self.eigenheiten = []
        for eig in neu.eigenheiten:
            if eig and eig not in alt.eigenheiten:
                self.eigenheiten.append(f"{eig}: {HINZUGEFÜGT}")
        for eig in alt.eigenheiten:
            if eig and eig not in neu.eigenheiten:
                self.eigenheiten.append(f"{eig}: {ENTFERNT}")

    def __str__(self) -> str:
        return f"{self.ep} EP ({self.datum.strftime('%d.%m.%Y')})"
    
    @property
    def text(self) -> str:
        text = ""
        if len(self.eigenheiten) > 0:
            text += f"<p><h3>Eigenheiten:</h3>{'<br>'.join(self.eigenheiten)}</p>"
        if len(self.attribute) > 0:
            text += f"<p><h3>Attribute:</h3>{'<br>'.join(self.attribute)}</p>"
        if len(self.energien) > 0:
            text += f"<p><h3>Energien:</h3>{'<br>'.join(self.energien)}</p>"
        if len(self.vorteile) > 0:
            text += f"<p><h3>Vorteile:</h3>{'<br>'.join(self.vorteile)}</p>"
        if len(self.freieFertigkeiten) > 0:
            text += f"<p><h3>Freie Fertigkeiten:</h3>{'<br>'.join(self.freieFertigkeiten)}</p>"
        if len(self.fertigkeiten) > 0:
            text += f"<p><h3>Fertigkeiten:</h3>{'<br>'.join(self.fertigkeiten)}</p>"
        if len(self.übernatürlicheFertigkeiten) > 0:
            text += f"<p><h3>Übernatürliche Fertigkeiten:</h3>{'<br>'.join(self.übernatürlicheFertigkeiten)}</p>"
        if len(self.talente) > 0:  
            text += f"<p><h3>Talente/Zauber/Liturgien:</h3>{'<br>'.join(self.talente)}</p>"
        return text
    
    def serialize(self, ser):
        if self.totalChanges == 0:
            return ser  # Should not happen anyays
        ser.begin("Eintrag")
        ser.set("ep", self.ep)
        ser.set("epGewinn", self.epGewinn)
        ser.set("epAusgabe", self.epAusgabe)
        ser.set("notiz", self.notiz)
        ser.set("datum", self.datum.strftime("%d.%m.%Y"))
        ser.set("vorteile", ";".join(self.vorteile))
        ser.set("fertigkeiten", ";".join(self.fertigkeiten))
        ser.set("freieFertigkeiten", ";".join(self.freieFertigkeiten))
        ser.set("attribute", ";".join(self.attribute))
        ser.set("energien", ";".join(self.energien))
        ser.set("talente", ";".join(self.talente))
        ser.set("eigenheiten", ";".join(self.eigenheiten))
        ser.end() # Eintrag
        return ser
    

    def deserialize(self, deser):
        self.ep = int(deser.get('ep', 0))
        self.epGewinn = int(deser.get('epGewinn', 0))
        self.epAusgabe = int(deser.get('epAusgabe', 0))
        self.notiz = deser.get('notiz')
        self.datum = dt.datetime.strptime(deser.get('datum', '01.01.0001'), "%d.%m.%Y")
        self.eigenheiten = deser.get('eigenheiten', '').split(';') if deser.get('eigenheiten') else []
        self.vorteile = deser.get('vorteile', '').split(';') if deser.get('vorteile') else []
        self.fertigkeiten = deser.get('fertigkeiten', '').split(';') if deser.get('fertigkeiten') else []
        self.freieFertigkeiten = deser.get('freieFertigkeiten', '').split(';') if deser.get('freieFertigkeiten') else []
        self.attribute = deser.get('attribute', '').split(';') if deser.get('attribute') else []
        self.energien = deser.get('energien', '').split(';') if deser.get('energien') else []
        self.talente = deser.get('talente', '').split(';') if deser.get('talente') else []

