from EventBus import EventBus
from Wolke import Wolke
import os
from PySide6 import QtWidgets, QtCore
from Core.Talent import Talent
from Core.DatenbankEinstellung import DatenbankEinstellung

Talent.grundwissen = property(lambda self: self._grundwissen if hasattr(self, "_grundwissen") else False).setter(lambda self, v: setattr(self, "_grundwissen", v))

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
        fertPW = nextFert.probenwert if self.grundwissen else nextFert.probenwertTalent
        self.probenwert = max(self.probenwert, fertPW + nextFert.basiswertMod)

Talent.aktualisieren = aktualisieren

class Plugin:
    def __init__(self):
        EventBus.addAction("basisdatenbank_geladen", self.basisDatenbankGeladenHook)
        EventBus.addFilter("dbe_class_fertigkeitdefinition_wrapper", self.dbeClassFertigkeitFilter)
        EventBus.addFilter("dbe_class_ueberfertigkeitdefinition_wrapper", self.dbeClassFertigkeitFilter)
        EventBus.addFilter("class_talentpicker_wrapper", self.talentPickerFilter)
        EventBus.addAction("talent_serialisiert", self.talentSerialisiertHook)
        EventBus.addAction("talent_deserialisiert", self.talentDeserialisiertHook)
        EventBus.addFilter("talent_kosten", self.talentKostenFilter)

    def changesCharacter(self):
        return True

    def changesDatabase(self):
        return True

    def basisDatenbankGeladenHook(self, params):
        self.db = params["datenbank"]

        e = self.db.einstellungen["Fertigkeiten: BW Script"]
        e.text = "round(sum(sorted(getAttribute(), reverse=True)[:3])/3)"

        e = DatenbankEinstellung()
        e.name = "FertigkeitenPlus Plugin: Talente Grundwissen Aktivieren"
        e.beschreibung = ""
        e.text = "False"
        e.typ = "Bool"
        self.db.loadElement(e)

        e = DatenbankEinstellung()
        e.name = "FertigkeitenPlus Plugin: Talente Grundwissen EP Multi"
        e.beschreibung = ""
        e.text = "0.5"
        e.typ = "Float"
        self.db.loadElement(e)
        
    def talentSerialisiertHook(self, params):
        ser = params["serializer"]
        talent = params["object"]

        ser.set("grundwissen", talent.grundwissen)

    def talentKostenFilter(self, kosten, params):
        charakter = params["charakter"]
        talentName = params["talent"]
        if talentName in charakter.talente and charakter.talente[talentName].grundwissen:
            return int(kosten * self.db.einstellungen["FertigkeitenPlus Plugin: Talente Grundwissen EP Multi"].wert)
        return kosten

    def talentDeserialisiertHook(self, params):
        ser = params["deserializer"]
        talent = params["object"]
        talent.grundwissen = ser.getBool('grundwissen', talent.grundwissen)

    def talentPickerFilter(self, talentPickerClass, params):
        enable = self.db.einstellungen["FertigkeitenPlus Plugin: Talente Grundwissen Aktivieren"].wert
        if not enable:
            return talentPickerClass

        class FertigkeitenPlusTalentPickerWrapper(talentPickerClass):
            def __init__(self, fert, ueber):
                self.erfahrungsgrad = enable
                if not ueber:
                    self.erfahrungsgrad = False
                    self.talenteGrundwissen = []
                else:
                    self.talenteGrundwissen = [t.name for t in Wolke.Char.talente.values() if t.grundwissen]
                super().__init__(fert, ueber)

                if self.gekaufteTalente is not None:
                    for talent in self.gekaufteTalente:
                        Wolke.Char.talente[talent].grundwissen = talent in self.talenteGrundwissen

            def onSetupUi(self):
                super().onSetupUi()
                if not self.erfahrungsgrad:
                    return

                self.gbErfahrungsgrad = QtWidgets.QGroupBox("Erfahrungsgrad")
                layout = QtWidgets.QVBoxLayout()
                self.rbGrundwissen = QtWidgets.QRadioButton("Grundwissen (PW)")
                self.rbGrundwissen.toggled.connect(self.grundwissenToggled)
                self.rbTalent = QtWidgets.QRadioButton("Talent (PW(T))")
                self.rbTalent.setChecked(True)
                layout.addWidget(self.rbGrundwissen)
                layout.addWidget(self.rbTalent)
                self.gbErfahrungsgrad.setLayout(layout)

                layout = self.ui.scrollAreaWidgetContents.layout()
                layout.addWidget(self.gbErfahrungsgrad, layout.rowCount(), 0, 1, -1)

            def grundwissenToggled(self, checked):
                if checked:
                    if self.currentTalent not in self.talenteGrundwissen:
                        self.talenteGrundwissen.append(self.currentTalent)
                else:
                    if self.currentTalent in self.talenteGrundwissen:
                        self.talenteGrundwissen.remove(self.currentTalent)

            def updateFields(self, tal):
                super().updateFields(tal)
                if not self.erfahrungsgrad:
                    return
                if tal is None:
                    return

                self.rbGrundwissen.setChecked(tal in self.talenteGrundwissen)
                self.rbTalent.setChecked(tal not in self.talenteGrundwissen)
                
                talent = Wolke.DB.talente[tal]
                self.rbGrundwissen.setText(f"Grundwissen (PW): {str(int(talent.kosten/2))} EP")
                self.rbTalent.setText(f"Talent (PW(T)): {str(talent.kosten)} EP")


        return FertigkeitenPlusTalentPickerWrapper

    def dbeClassFertigkeitFilter(self, editorType, params):
        class DatenbankEditFertigkeitWrapperPlus(editorType):
            def __init__(self, datenbank, fertigkeit=None):
                super().__init__(datenbank, fertigkeit)

            def onSetupUi(self):
                super().onSetupUi()
                self.ui.comboAttribut4Separator = QtWidgets.QLabel()
                self.ui.comboAttribut4Separator.setText(" Optional:")
                self.ui.comboAttribut4 = QtWidgets.QComboBox()
                self.ui.comboAttribut4.setMinimumSize(QtCore.QSize(45, 0))
                attribute = [a.name for a in sorted(self.datenbank.attribute.values(), key=lambda value: value.sortorder)]
                self.ui.comboAttribut4.addItems(["-"] + attribute)
                self.ui.horizontalLayout.insertWidget(5, self.ui.comboAttribut4Separator)
                self.ui.horizontalLayout.insertWidget(6, self.ui.comboAttribut4)
                
                self.registerInput(self.ui.comboAttribut4, self.ui.labelAttribute)

            def load(self, fertigkeit):
                super().load(fertigkeit)
                if len(fertigkeit.attribute) >= 4:
                    self.ui.comboAttribut4.setCurrentText(fertigkeit.attribute[3])

            def update(self, fertigkeit):
                super().update(fertigkeit)
                if self.ui.comboAttribut4.currentText() == "-":
                    if len(fertigkeit.attribute) >= 4:
                        fertigkeit.attribute.pop()
                else:
                    if len(fertigkeit.attribute) < 4:
                        fertigkeit.attribute.append(self.ui.comboAttribut4.currentText())
                    else:
                        fertigkeit.attribute[3] = self.ui.comboAttribut4.currentText()

        return DatenbankEditFertigkeitWrapperPlus

    def dbeClassUeberFertigkeitFilter(self, editorType):
        return editorType

