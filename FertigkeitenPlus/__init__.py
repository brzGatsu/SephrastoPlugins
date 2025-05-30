from EventBus import EventBus
from Wolke import Wolke
import os
from PySide6 import QtWidgets, QtCore
from Core.Talent import Talent
from Core.DatenbankEinstellung import DatenbankEinstellung

# Patch Talent class
def setUnerfahren(self, value):
    self._unerfahren = value
    self._updateAnzeigenameExt()

Talent.unerfahren = property(lambda self: self._unerfahren if hasattr(self, "_unerfahren") else False).setter(setUnerfahren)

aktualisierenOld = Talent.aktualisieren

def aktualisieren(self):
    aktualisierenOld(self)
    # PW und Hauptferigkeit
    self.probenwert = -1
    fertigkeiten = self.charakter.fertigkeiten
    if self.spezialTalent:
        fertigkeiten = self.charakter.übernatürlicheFertigkeiten

    for fertName in self.fertigkeiten:
        if not fertName in fertigkeiten:
            continue
        nextFert = fertigkeiten[fertName]
        fertPW = nextFert.probenwert if self.unerfahren else nextFert.probenwertTalent
        self.probenwert = max(self.probenwert, fertPW + nextFert.basiswertMod)

Talent.aktualisieren = aktualisieren

nameOld = Talent._updateAnzeigenameExt

def updateAnzeigeName(self):
    nameOld(self)
    if self.unerfahren:
        self.anzeigenameExt += " (unerfahren)"


Talent._updateAnzeigenameExt = updateAnzeigeName

class Plugin:
    def __init__(self):
        EventBus.addAction("datenbank_laden", self.datenbankLadenHook)
        EventBus.addFilter("class_talentpicker_wrapper", self.talentPickerFilter)
        EventBus.addAction("talent_serialisiert", self.talentSerialisiertHook)
        EventBus.addAction("talent_deserialisiert", self.talentDeserialisiertHook)
        EventBus.addAction("post_charakter_aktualisieren", self.postCharakterAktualisierenHook)

    def changesCharacter(self):
        return True

    def changesDatabase(self):
        return True

    def datenbankLadenHook(self, params):
        self.db = params["datenbank"]
          
        e = DatenbankEinstellung()
        e.name = "FertigkeitenPlus Plugin: Talente Erfahrungsgrade Aktivieren"
        e.beschreibung = "Wenn aktiviert, steht beim Auswahlfenster von übernatürlichen Talenten die Option zur Verfügung, "+\
            "ein Talent nur auf der Stufe 'Unerfahren' zu erwerben. "+\
            "Dieses kostet dann nur die Hälfte der EP. Dafür steht damit nur der PW und nicht der PW(T) zur Verfügung."
        e.text = "False"
        e.typ = "Bool"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "FertigkeitenPlus Plugin: Talente Unerfahren EP Multi"
        e.beschreibung = "Der EP-Kosten Multiplikator für Talent, die auf 'Unerfahren' erworben wurden."
        e.text = "0.5"
        e.typ = "Float"
        self.db.loadElement(e)

    def talentSerialisiertHook(self, params):
        ser = params["serializer"]
        talent = params["object"]

        ser.set("unerfahren", talent.unerfahren)

    def talentDeserialisiertHook(self, params):
        ser = params["deserializer"]
        talent = params["object"]
        talent.unerfahren = ser.getBool('unerfahren', talent.unerfahren)

    def postCharakterAktualisierenHook(self, params):
        char = params["charakter"]
        for talent in char.talente.values():
            if not talent.unerfahren:
                continue
            
            erfahrenKosten = talent.kosten
            unerfahrenKosten = int(erfahrenKosten * self.db.einstellungen["FertigkeitenPlus Plugin: Talente Unerfahren EP Multi"].wert)
            gutschrift = erfahrenKosten - unerfahrenKosten
            char.epAusgegeben -= gutschrift
            if talent.spezialTalent:
                char.epÜbernatürlichTalente -= gutschrift
            else:
                char.epFertigkeitenTalente -= gutschrift

    def talentPickerFilter(self, talentPickerClass, params):
        enable = self.db.einstellungen["FertigkeitenPlus Plugin: Talente Erfahrungsgrade Aktivieren"].wert
        if not enable:
            return talentPickerClass

        class FertigkeitenPlusTalentPickerWrapper(talentPickerClass):
            def __init__(self, fert, ueber):
                self.erfahrungsgrad = enable
                if not ueber:
                    self.erfahrungsgrad = False
                    self.talenteUnerfahren = []
                else:
                    self.talenteUnerfahren = [t.name for t in Wolke.Char.talente.values() if t.unerfahren]
                super().__init__(fert, ueber)

                if self.gekaufteTalente is not None:
                    for talent in self.gekaufteTalente:
                        Wolke.Char.talente[talent].unerfahren = talent in self.talenteUnerfahren

            def onSetupUi(self):
                super().onSetupUi()
                if not self.erfahrungsgrad:
                    return

                self.gbErfahrungsgrad = QtWidgets.QGroupBox("Grad")
                self.gbErfahrungsgrad.setVisible(False)
                layout = QtWidgets.QVBoxLayout()
                self.rbUnerfahren = QtWidgets.QRadioButton("Unerfahren (PW)")
                self.rbUnerfahren.toggled.connect(self.unerfahrenToggled)
                self.rbTalent = QtWidgets.QRadioButton("Erfahren (PW(T))")
                self.rbTalent.setChecked(True)
                layout.addWidget(self.rbUnerfahren)
                layout.addWidget(self.rbTalent)
                self.gbErfahrungsgrad.setLayout(layout)

                layout = self.ui.scrollAreaWidgetContents.layout()
                layout.addWidget(self.gbErfahrungsgrad, layout.rowCount(), 0, 1, -1)

            def unerfahrenToggled(self, checked):
                if checked:
                    if self.currentTalent not in self.talenteUnerfahren:
                        self.talenteUnerfahren.append(self.currentTalent)
                else:
                    if self.currentTalent in self.talenteUnerfahren:
                        self.talenteUnerfahren.remove(self.currentTalent)

            def updateErfahrungsgradLabels(self):
                if not self.erfahrungsgrad:
                    return
                if not self.currentTalent:
                    return
                kosten = self.talentKosten[self.currentTalent]
                self.rbUnerfahren.setText(f"Unerfahren (PW): {str(int(kosten/2))} EP")
                self.rbTalent.setText(f"Erfahren (PW(T)): {str(kosten)} EP")

            def spinChanged(self):
                super().spinChanged()
                self.updateErfahrungsgradLabels()

            def updateFields(self, tal):
                super().updateFields(tal)
                if not self.erfahrungsgrad:
                    return
                if tal is None:
                    self.gbErfahrungsgrad.setVisible(False)
                    return
                showErfahrungsgrad = not tal.lower().endswith("(passiv)")

                self.gbErfahrungsgrad.setVisible(showErfahrungsgrad)
                if not showErfahrungsgrad:
                    self.rbUnerfahren.setChecked(False)
                    self.rbTalent.setChecked(True)

                self.rbUnerfahren.setChecked(tal in self.talenteUnerfahren)
                self.rbTalent.setChecked(tal not in self.talenteUnerfahren)
                self.updateErfahrungsgradLabels()

        return FertigkeitenPlusTalentPickerWrapper