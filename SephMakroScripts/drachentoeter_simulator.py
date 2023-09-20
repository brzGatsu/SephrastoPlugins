from Charakter import Char
import random
import math
import os
from Wolke import Wolke
from PySide6 import QtWidgets

#========== Settings ===========
# Dies ist eine Simulation für die Drachentöter-Kampfregeln für Ilaris
# Drachentöter kann hier gefunden werden: https://dsaforum.de/viewtopic.php?t=59615
# Besonderheiten:
# - Betäubt durch Wundschmerz beendet den Kampf
# - AT gelingen nur wenn sie HÖHER als die VT sind (also keine Sonderbehandlungen bei Gleichstand)
# - Bei gleicher INI wechseln der Start-Kämpfer sich ab in jedem neuen Kampf
# - Für den VT Wert wird immer der hächste Werte aus Haupthand, Nebenhand und Ausweichen genommen
# - Fernkampf wird nicht unterstützt
# - Aktionen: es wird IMMER die Aktion Angriff durchgeführt und immer ohne volle Offensive.
# - Kampfstile: alle außer Reiterkampf werden unterstützt (ohne Stufe IV). KVKIII, SKII und BKII sind (abseits passiver Bonusse) nicht implementiert, da nicht relevant in Duellen.
# - Vorteile: Nur Todesstoß, Hammerschlag, Waffenloser Kampf, Kampfreflexe, (verb.) Rüstungsgewöhnung, Kalte Wut, Präzision, Gegenhalten, Unaufhaltsam (es wird automatisch ausgewichen, wenn die VT hoch genug ist NACH dem AT Wurf)
# - Manöver: Nur Wuchtschlag, Todesstoß, Hammerschlag und Rüstungsbrecher (werden automatisch eingesetzt auf basis einer simplen AI)
# - Waffeneigenschaften: Alles außer Reittier, Stumpf und Zerbrechlich

vtPassiv = True # falls True wird kein W20 sondern 10 zur VT addiert
vtPassivMod = -10 # wieviel soll von der VT abgezogen werden bei vtPassiv = True (z.b. weil die 10 schon in Sephrasto hinzugefügt wird)
wundschmerz = False # sollen die Wundschmerzregeln verwendet werden? Betäubt wird mit Kampf verloren gleichgesetzt
samples = 1000 # wieviele Kämpfe sollen simuliert werden
logFights = True # sollen die Kampfwürfe ausgegeben werden

fighter1Path = "" # pfad für charakter xml von Kämpfer 1 - falls leer, geht ein Datei-Auswahldialog auf
fighter1Name = "Alrik"
fighter1WaffeIndex = 2 # welche Waffe soll Kämpfer 1 verwenden - entspricht der Position im Waffen Tab, beginnend bei 0
fighter1NebenhandIndex = 3 # wird ignoriert, wenn fighter2WaffeIndex zweihändig ist
fighter1AusweichenIndex = 1 # bei -1 wird ausweichen nicht verwendet

fighter2Path = "" # pfad für charakter xml von Kämpfer 2 - falls leer, geht ein Datei-Auswahldialog auf
fighter2Name = "Elissa"
fighter2WaffeIndex = 2 # welche Waffe soll Kämpfer 2 verwenden - entspricht der Position im Waffen Tab, beginnend bei 0
fighter2NebenhandIndex = 3 # wird ignoriert, wenn fighter2WaffeIndex zweihändig ist
fighter2AusweichenIndex = 1 # bei -1 wird ausweichen nicht verwendet

zähigkeitOverride = 10 # setzt die Zähigkeit bie allen Kämpfern auf den angegebenen Wert, falls nicht -1

#========== Implementation ===========

class Action:
    Aktion = "Aktion"
    Bonusaktion = "Bonusaktion"
    Reaktion = "Reaktion"
    ExtraAngriff = "Extra Angriff"
    NebenhandAngriffKostenlos = "Kostenloser Nebenhand Angriff"
    SchildwallKostenlos = "Kostenloser Schildwall"
    TückischeKlinge = "Tückische Klinge"

# Attack Types
class NormalerAngriff:
    name = "Normaler Angriff"
    def isUsable(fighter): return fighter.actionUsable(Action.Aktion) and fighter.myTurn
    def mod(fighter): return 0
    def isManeuverAllowed(fighter, maneuver): return True    
    def use(attacker, defender): attacker.useAction(Action.Aktion)

class NebenhandAngriff:
    name = "Nebenhandangriff"
    def isUsable(fighter):
        if fighter.waffeIndex == fighter.nebenhandIndex:
            return False
        return fighter.actionUsable(NebenhandAngriff.__getActionType(fighter)) and fighter.myTurn
    def mod(fighter):
        if fighter.kampfstil == "Beidhändiger Kampf" and "Beidhändiger Kampf II" in fighter.char.vorteile:
            return 0
        return -4
    def isManeuverAllowed(fighter, maneuver): return maneuver.name.startswith("Wuchtschlag")
    def use(attacker, defender): attacker.useAction(NebenhandAngriff.__getActionType(attacker))
    def __getActionType(fighter):
        if fighter.kampfstil == "Beidhändiger Kampf" and "Beidhändiger Kampf II" in fighter.char.vorteile and fighter.char.waffen[fighter.waffeIndex].name == fighter.char.waffen[fighter.nebenhandIndex].name:
            return Action.NebenhandAngriffKostenlos
        else:
            return Action.Bonusaktion

class BonusAngriff:
    name = "Normaler Angriff (Bonusaktion)"
    def isUsable(fighter): fighter.actionUsable(Action.Bonusaktion) and fighter.myTurn
    def mod(fighter): return 0
    def isManeuverAllowed(fighter, maneuver): return True    
    def use(attacker, defender): attacker.useAction(Action.Bonusaktion)

class ExtraAngriff:
    name = "Extra Angriff"
    def isUsable(fighter): return fighter.actionUsable(Action.ExtraAngriff) and fighter.myTurn
    def mod(fighter): return 0
    def isManeuverAllowed(fighter, maneuver): return True    
    def use(attacker, defender): attacker.useAction(Action.ExtraAngriff)

class Passierschlag:
    name = "Passierschlag"
    def isUsable(fighter): return fighter.actionUsable(Action.Reaktion)
    def mod(fighter): return 0
    def isManeuverAllowed(fighter, maneuver): return True    
    def use(attacker, defender): attacker.useAction(Action.Reaktion)

# Maneuvers and Feats trigger order
# trigger_onEnemyEnterReach (defender, only first iniphase)
# trigger_onAT (attacker)
# if at > vt:
#     trigger_onVTFailing (defender)
# if still at > vt:
#     trigger_onATSuccess (attacker)
#     trigger_onDealWounds (attacker)
#     trigger_onDamageReceived (defender)
#     trigger_onDamageDealt (attacker)
# else:
#     trigger_onVTSuccess (defender)
#     trigger_onATFailed (attacker)
# trigger_onATDone (attacker)

# Maneuvers
class Wuchtschlag2:
    name = "Wuchtschlag +2"
    def isUsable(fighter): return True
    def trigger_onAT(attacker, defender, atRoll):
        atRoll.modify(-2)
    def trigger_onATSuccess(attacker, defender, atRoll, vtRoll, tpRoll):
        tpRoll.modify(2)

class Wuchtschlag4:
    name = "Wuchtschlag +4"
    def isUsable(fighter): return True
    def trigger_onAT(attacker, defender, atRoll):
        atRoll.modify(-4)
    def trigger_onATSuccess(attacker, defender, atRoll, vtRoll, tpRoll):
        tpRoll.modify(4)

class Wuchtschlag6:
    name = "Wuchtschlag +6"
    def isUsable(fighter): return True
    def trigger_onAT(attacker, defender, atRoll):
        atRoll.modify(-6)
    def trigger_onATSuccess(attacker, defender, atRoll, vtRoll, tpRoll):
        tpRoll.modify(6)

class Wuchtschlag8:
    name = "Wuchtschlag +8"
    def isUsable(fighter): return True
    def trigger_onAT(attacker, defender, atRoll):
        atRoll.modify(-8)
    def trigger_onATSuccess(attacker, defender, atRoll, vtRoll, tpRoll):
        tpRoll.modify(8)

class Hammerschlag:
    name = "Hammerschlag"
    def isUsable(fighter): return "Hammerschlag" in fighter.char.vorteile
    def trigger_onAT(attacker, defender, atRoll):
        atRoll.modify(-8)
    def trigger_onATSuccess(attacker, defender, atRoll, vtRoll, tpRoll):
        tpRoll.multiplier = 2

class Todesstoß:
    name = "Todesstoß"
    def isUsable(fighter): return "Todesstoß" in fighter.char.vorteile
    def trigger_onAT(attacker, defender, atRoll):
        atRoll.modify(-8)
    def trigger_onDealWounds(fighter, wounds):
        return wounds+2

class Rüstungsbrecher:
    name = "Rüstungsbrecher"
    def isUsable(fighter): return "Rüstungsbrechend" in fighter.waffenEigenschaften
    def trigger_onAT(attacker, defender, atRoll):
        atRoll.modify(-4)
    def trigger_onATSuccess(attacker, defender, atRoll, vtRoll, tpRoll):
        tpRoll.isSP = True

# Feats (offensive)
class SNKII:
    name = "Finte"
    def isUsable(fighter): return "Schneller Kampf II" in fighter.char.vorteile and fighter.kampfstil == "Schneller Kampf"
    def trigger_onAT(attacker, defender, atRoll):
        if not attacker.actionUsable(Action.Bonusaktion) or not attacker.myTurn:
            return
        if not atRoll.couldProfitFromAdvantage:
            return
        attacker.useAction(Action.Bonusaktion)
        attacker.advantage.append(Fighter.DurationEndPhaseOneRoll)
        if logFights: print(attacker.name, "gibt sich als Bonusaktion Vorteil durch", SNKII.name)

class SNKIII:
    name = "Unterlaufen"
    def isUsable(fighter): return "Schneller Kampf III" in fighter.char.vorteile and fighter.kampfstil == "Schneller Kampf"
    def trigger_onDamageDealt(attacker, defender, atRoll, vtRoll, tpRoll):
        if not defender.isAlive() or not ExtraAngriff.isUsable(attacker) or not attacker.myTurn:
            return
        if logFights: print(">", attacker.name, "macht einen weiteren Angriff durch", SNKIII.name)
        attacker.attack(defender, ExtraAngriff)

class KVKII:
    name = "Durchbrechen"
    def isUsable(fighter): return "Kraftvoller Kampf II" in fighter.char.vorteile and fighter.kampfstil == "Kraftvoller Kampf"
    def trigger_onDamageDealt(attacker, defender, atRoll, vtRoll, tpRoll):
        if not atRoll.isCrit() or not defender.isAlive() or not BonusAngriff.isUsable(attacker) or not attacker.myTurn:
            return
        if logFights: print(">", attacker.name, "macht als Bonusaktion einen weiteren Angriff durch", KVKII.name)
        attacker.attack(defender, BonusAngriff)

class BHKIII:
    name = "BHK III"
    def isUsable(fighter): return "Beidhändiger Kampf III" in fighter.char.vorteile and fighter.kampfstil == "Beidhändiger Kampf"
    def trigger_onATDone(attacker, defender, atRoll, vtRoll):
        if not defender.isAlive() or not ExtraAngriff.isUsable(attacker) or not attacker.myTurn:
            return
        if logFights: print(attacker.name, "macht einen weiteren Angriff durch", BHKIII.name)
        attacker.attack(defender, ExtraAngriff)

class PWKII:
    name = "Tückische Klinge"
    def isUsable(fighter): return "Parierwaffenkampf II" in fighter.char.vorteile and fighter.kampfstil == "Parierwaffenkampf"
    def trigger_onATSuccess(attacker, defender, atRoll, vtRoll, tpRoll):
        if not atRoll.advantage or not attacker.actionUsable(Action.TückischeKlinge):
            return
        attacker.useAction(Action.TückischeKlinge)
        bonus = random.randint(1,6) + random.randint(1,6)
        tpRoll.modify(bonus)
        if logFights: print(">", attacker.name, "verursacht +", bonus, "TP durch", PWKII.name)

class Präzision:
    name = "Präzision"
    def isUsable(fighter): return "Präzision" in fighter.char.vorteile
    def trigger_onATSuccess(attacker, defender, atRoll, vtRoll, tpRoll):
        if atRoll.lastRoll >= 16:
            tpRoll.modify(attacker.char.attribute["GE"].wert)
            if logFights: print(">", attacker.name, "verursacht +", attacker.char.attribute["GE"].wert, "TP durch", Präzision.name)

class Unaufhaltsam:
    name = "Unaufhaltsam"
    def isUsable(fighter): return "Unaufhaltsam" in fighter.char.vorteile
    def trigger_onATFailed(attacker, defender, atRoll, vtRoll):
        ausweichen = (vtRoll.result() - defender.modVT()) + defender.modAusweichen()        
        if ausweichen < atRoll.result():
            if logFights: print(">", attacker.name, "verursacht dennoch halben Schaden durch", Unaufhaltsam.name)
            tpRoll = attacker.rollTP()
            tpRoll.multiplier = 0.5
            defender.takeDamage(tpRoll, [Unaufhaltsam])

# Feats (defensive)
class Schild:
    name = "Schildwall (ohne SK)"
    def isUsable(fighter): return "Schildkampf I" not in fighter.char.vorteile and "Schild" in fighter.char.waffen[fighter.nebenhandIndex].eigenschaften
    def trigger_onVTFailing(attacker, defender, atRoll, vtRoll):
        if "Unberechenbar" in attacker.waffenEigenschaften:
            return
        if not defender.actionUsable(Action.Reaktion):
            return
        if atRoll.result() - vtRoll.result() > 3:
            return
        defender.useAction(Action.Reaktion)
        bonus = random.randint(1,3)
        vtRoll.modify(bonus)
        if logFights: print(defender.name, "verbessert als Reaktion die VT nachträglich um", bonus, "durch",  Schild.name)

class SK:
    name = "Verbesserter Schildwall"
    def isUsable(fighter): return "Schildkampf I" in fighter.char.vorteile and fighter.kampfstil == "Schildkampf"
    def trigger_onVTFailing(attacker, defender, atRoll, vtRoll):
        if "Unberechenbar" in attacker.waffenEigenschaften:
            return
        if not defender.actionUsable(SK.__getActionType(defender)):
            return
        if atRoll.result() - vtRoll.result() > 6:
            return
        defender.useAction(SK.__getActionType(defender))
        bonus = random.randint(1,6)
        vtRoll.modify(bonus)
        if logFights: print(defender.name, "verbessert als Reaktion die VT nachträglich um", bonus, "durch",  SK.name)

    def __getActionType(fighter):
        if "Schildkampf III" in fighter.char.vorteile and fighter.actionUsable(Action.SchildwallKostenlos):
            return Action.SchildwallKostenlos
        else:
            return Action.Reaktion

class PWKI:
    name = "Binden"
    def isUsable(fighter): return "Parierwaffenkampf I" in fighter.char.vorteile and fighter.kampfstil == "Parierwaffenkampf"
    def trigger_onVTSuccess(attacker, defender, atRoll, vtRoll):
        if not defender.actionUsable(Action.Reaktion):
            return
        defender.useAction(Action.Reaktion)
        attacker.advantageForEnemy.append(Fighter.DurationStartNextPhaseOneRoll)
        if logFights: print(">", defender.name, "verleiht als Reaktion dem nächsten Angriff gegen" , attacker.name, "Vorteil durch",  PWKI.name)

class PWKIII:
    name = "Kreuzblock"
    def isUsable(fighter): return "Parierwaffenkampf III" in fighter.char.vorteile and fighter.kampfstil == "Parierwaffenkampf"
    def trigger_onVTFailing(attacker, defender, atRoll, vtRoll):
        if "Unberechenbar" in attacker.waffenEigenschaften:
            return
        if not defender.actionUsable(Action.Reaktion):
            return
        if atRoll.result() <= vtRoll.result():
            return
        defender.useAction(Action.Reaktion)
        oldRoll = atRoll.result()
        atRoll.roll()
        if logFights: print(defender.name, "lässt als Reaktion die gegnerischen AT neu würfeln von" , oldRoll, "zu",  atRoll.result(), "durch", PWKIII.name)

class BKIII:
    name = "Vergeltung"
    def isUsable(fighter): return "Berserkerkampf III" in fighter.char.vorteile and fighter.kampfstil == "Berserkerkampf"
    def trigger_onDamageReceived(attacker, defender, atRoll, vtRoll, tpRoll):
        if not defender.isAlive() or not Passierschlag.isUsable(defender):
            return
        if logFights: print(">", defender.name, "macht als Reaktion einen Angriff durch", BKIII.name)
        defender.attack(attacker, Passierschlag)

class Gegenhalten:
    name = "Gegenhalten"
    def isUsable(fighter): return "Gegenhalten" in fighter.char.vorteile
    def trigger_onEnemyEnterReach(attacker, defender):
        if not defender.isAlive() or not Passierschlag.isUsable(defender):
            return
        if logFights: print(defender.name, "führt Passierschlag aus durch", Gegenhalten.name)
        defender.attack(attacker, Passierschlag)

Feats = [SNKII, SNKIII, KVKII, BHKIII, PWKII, Präzision, Unaufhaltsam, Schild, SK, PWKI, PWKIII, BKIII, Gegenhalten]

# "AI"

def ai_chooseManeuvers(attacker, defender, attackType):
    maneuvers = []
    statDiff = (attackType.mod(attacker) + attacker.modAT()) - defender.modVT()
    wsDiff = defender.wsStern - attacker.maxDamage
    rs = defender.wsStern - defender.ws
    if (statDiff >= 14 and defender.wunden <= 4) or wsDiff >= 6:
        if Hammerschlag.isUsable(attacker) and attackType.isManeuverAllowed(attacker, Hammerschlag) and attacker.averageDamage > 8:
            maneuvers += [Hammerschlag]
        elif Todesstoß.isUsable(attacker) and attackType.isManeuverAllowed(attacker, Todesstoß):
            maneuvers += [Todesstoß]
        else:
            if Rüstungsbrecher.isUsable(attacker) and attackType.isManeuverAllowed(attacker, Rüstungsbrecher) and rs >= 4:
                maneuvers += [Rüstungsbrecher, Wuchtschlag4]
            else:
                maneuvers += [Wuchtschlag8]
    elif statDiff >= 12 or wsDiff >= 4:
        if Rüstungsbrecher.isUsable(attacker) and attackType.isManeuverAllowed(attacker, Rüstungsbrecher) and rs >= 6:
            maneuvers += [Rüstungsbrecher, Wuchtschlag2]
        else:
            maneuvers += [Wuchtschlag6]
    elif statDiff >= 10 or wsDiff >= 2:
        if Rüstungsbrecher.isUsable(attacker) and attackType.isManeuverAllowed(attacker, Rüstungsbrecher) and rs >= 4:
            maneuvers += [Rüstungsbrecher]
        else:
            maneuvers += [Wuchtschlag4]
    elif statDiff >= 8 or wsDiff >= 0:
        maneuvers += [Wuchtschlag2]
    return maneuvers

def ai_addCritManeuvers(attacker, defender, attackType, maneuvers):
    if logFights: print("Triumph für", attacker.name)
    if Hammerschlag.isUsable(attacker) and attackType.isManeuverAllowed(attacker, Hammerschlag) and Hammerschlag not in maneuvers and attacker.averageDamage > 4:
        maneuvers.append(Hammerschlag)
        if logFights: print(">", Hammerschlag.name)
    elif Todesstoß.isUsable(attacker) and attackType.isManeuverAllowed(attacker, Todesstoß) and Todesstoß not in maneuvers:
        maneuvers.append(Todesstoß)
        if logFights: print(">", Todesstoß.name)
    elif Rüstungsbrecher.isUsable(attacker) and attackType.isManeuverAllowed(attacker, Rüstungsbrecher) and Rüstungsbrecher not in maneuvers and (defender.wsStern - defender.ws >= 4):
        maneuvers.append(Rüstungsbrecher)
        if logFights: print(">", Rüstungsbrecher.name)
    elif Wuchtschlag4 not in maneuvers:
        maneuvers.append(Wuchtschlag4)
        if logFights: print(">", Wuchtschlag4.name)
    else:
        maneuvers.remove(Wuchtschlag4)
        maneuvers.append(Wuchtschlag8)
        if logFights: print(">", Wuchtschlag4.name)

# Rolls

class TPRoll():
    def __init__(self, würfel, würfelSeiten, plus):
        self.würfel = würfel
        self.würfelSeiten = würfelSeiten
        self.plus = plus
        self.mod = 0
        self.multiplier = 1
        self.isSP = False
        self.roll()

    def roll(self): self.lastRoll = self.würfel * random.randint(1,self.würfelSeiten) + self.plus
    def modify(self, value): self.mod += value
    def result(self): return round(self.lastRoll * self.multiplier) + self.mod
    def str(self): return str(self.result()) + (" SP" if self.isSP else " TP")

class D20Roll:
    def __init__(self, pw, passive=False):
        self.mod = pw
        self.passive = passive
        self.advantage = False
        self.disadvantage = False
        self.couldProfitFromAdvantage = True
        self.roll()

    def setAdvantageDisadvantage(self, advantage, disadvantage):
        self.advantage = advantage
        self.disadvantage = disadvantage
        self.couldProfitFromAdvantage = not advantage
        if self.advantage and self.disadvantage:
            self.advantage = False
            self.disadvantage = False
            self.couldProfitFromAdvantage = False

    def roll(self):
        self.lastRoll = random.randint(1,20)
        if self.passive:
            self.lastRoll = 10
        elif self.advantage:
            self.lastRoll = max(self.lastRoll, random.randint(1,20))
        elif self.disadvantage:
            self.lastRoll = min(self.lastRoll, random.randint(1,20))

    def result(self): return self.lastRoll + self.mod
    def isCrit(self): return self.lastRoll == 20
    def isCritFail(self): return self.lastRoll == 1
    def modify(self, value): self.mod += value
    def str(self): return str(self.result()) + " (" + str(self.lastRoll) + ("+" if self.mod >= 0 else "") + str(self.mod) + (", Vorteil" if self.advantage else "") + (", Nachteil" if self.disadvantage else "") + ")"

# Fighter

class Fighter:
    DurationStartNextPhase = 0
    DurationEndPhase = 1
    DurationEndNextPhase = 2
    DurationStartNextPhaseOneRoll = 3
    DurationEndPhaseOneRoll = 4
    DurationEndNextPhaseOneRoll = 5

    def __init__(self, name, charPath, startPositionX, waffeIndex, nebenhandIndex, ausweichenIndex):
        self.name = name
        self.char = Char()
        self.char.xmlLesen(charPath)
        self.char.aktualisieren()
        self.wunden = 0
        self.ws = self.char.abgeleiteteWerte["WS"].wert
        self.wsStern = self.char.abgeleiteteWerte["WS"].finalwert
        self.ini = self.char.abgeleiteteWerte["INI"].finalwert
        self.usedActions = {}
        self.advantage = []
        self.disadvantage = []
        self.advantageForEnemy = []
        self.disadvantageForEnemy = []
        self.myTurn = False
        self.startPositionX = startPositionX
        self.position = self.startPositionX

        print("\n=====", self.name, "=====")
        attribute = "Attribute: "
        for attr in self.char.attribute.values():
            attribute += attr.name + " " + str(attr.probenwert) + " | "
        attribute = attribute[:-3]
        print(attribute)
        abgeleiteteWerte = "Abgeleitete Werte: "
        for aw in self.char.abgeleiteteWerte.values():
            abgeleiteteWerte += aw.name + " " + str(aw.finalwert) + " | "
        abgeleiteteWerte = abgeleiteteWerte[:-3]
        print(abgeleiteteWerte)

        self.zähigkeitPW = self.char.fertigkeiten["Selbstbeherrschung"].probenwert
        if "Zähigkeit" in self.char.talente:
            self.zähigkeitPW = self.char.fertigkeiten["Selbstbeherrschung"].probenwertTalent
        if zähigkeitOverride != -1:
            self.zähigkeitPW = zähigkeitOverride

        print("Talente: Zähigkeit", self.zähigkeitPW)
        self.waffeIndex = waffeIndex
        self.nebenhandIndex = nebenhandIndex
        self.ausweichenIndex = ausweichenIndex
        self.equip(waffeIndex, log=True)
        self.highestVT = self.vt
        self.ausweichen = 0
        if "Zweihändig" in self.waffenEigenschaften:
            self.nebenhandIndex = self.waffeIndex
        if self.waffeIndex != self.nebenhandIndex:
            self.equip(nebenhandIndex, log=True)
            if self.vt > self.highestVT:
                self.highestVT = self.vt
        if self.ausweichenIndex != -1:
            self.equip(self.ausweichenIndex, log=True)
            self.ausweichen = self.vt
            if self.vt > self.highestVT:
                self.highestVT = self.vt
        self.equip(waffeIndex)

        self.feats = []
        for feat in Feats:
            if feat.isUsable(self):
                self.feats.append(feat)
        print("Vorteile:", ", ".join(self.char.vorteile.keys()))

    def pruneAdvantageDisadvantage(self, duration, enemyRoll = False):
        def filterDuration(d):
            if d == Fighter.DurationEndNextPhase:
                return Fighter.DurationEndPhase
            elif d == Fighter.DurationEndNextPhaseOneRoll:
                return Fighter.DurationEndPhaseOneRoll
            return d

        pruneOwn = True
        pruneEnemy = True
        if duration in [Fighter.DurationStartNextPhaseOneRoll, Fighter.DurationEndPhaseOneRoll, Fighter.DurationEndNextPhaseOneRoll]:
            pruneOwn = not enemyRoll
            pruneEnemy = enemyRoll           
        if pruneOwn:
            self.advantage = [filterDuration(d) for d in self.advantage if d != duration]
            self.disadvantage = [filterDuration(d) for d in self.disadvantage if d != duration]
        if pruneEnemy:
            self.advantageForEnemy = [filterDuration(d) for d in self.advantageForEnemy if d != duration]
            self.disadvantageForEnemy = [filterDuration(d) for d in self.disadvantageForEnemy if d != duration]

    def hasAdvantage(self): return len(self.advantage) > 0
    def hasDisadvantage(self): return len(self.disadvantage) > 0
    def enemyHasAdvantage(self): return len(self.advantageForEnemy) > 0
    def enemyHasDisadvantage(self): return len(self.disadvantageForEnemy) > 0

    def reset(self):
        self.wunden = 0
        self.usedActions = {}
        self.advantage = []
        self.disadvantage = []
        self.advantageForEnemy = []
        self.disadvantageForEnemy = []
        self.myTurn = False
        self.position = self.startPositionX

    def actionUsable(self, action):
        return action not in self.usedActions

    def useAction(self, action):
        self.usedActions[action] = True

    def isAlive(self):
        return self.wunden < 9

    def wundmalus(self):
        return 0 if "Kalte Wut" in self.char.vorteile else -(max(self.wunden -2, 0))*2
        
    def equip(self, index, log = False):
        self.waffeAktiv = index
        waffe = self.char.waffen[index]
        waffenwerte = self.char.waffenwerte[index]
        self.kampfstil = waffenwerte.kampfstil
        self.at = waffenwerte.at
        self.vt = waffenwerte.vt
        self.rw = waffenwerte.rw
        self.tpWürfel = waffenwerte.würfel
        self.tpSeiten = waffe.würfelSeiten
        self.tpPlus = waffenwerte.plus
        self.waffenEigenschaften = waffe.eigenschaften
        self.averageDamage = (waffenwerte.würfel * ((waffe.würfelSeiten / 2) + 0.5)) + self.tpPlus
        self.maxDamage = (waffenwerte.würfel * waffe.würfelSeiten) + self.tpPlus
        if log:
            print(self.name, "verwendet", waffe.name, "mit", waffe.kampfstil or "keinem Kampfstil", "AT", self.at, "VT", self.vt, "TP", str(self.tpWürfel) + "W" + str(self.tpSeiten) + ("+" if self.tpPlus >= 0 else "") + str(self.tpPlus), ", ".join(waffe.eigenschaften))

    def switchWeapons(self):
        if self.waffeAktiv == self.waffeIndex:
            self.equip(self.nebenhandIndex)
        else:
            self.equip(self.waffeIndex)
        
    def modAT(self):
        return self.at + self.wundmalus()
        
    def modVT(self):
        return self.highestVT + self.wundmalus() + (vtPassivMod if vtPassiv else 0)

    def modAusweichen(self):
        return self.ausweichen + self.wundmalus() + (vtPassivMod if vtPassiv else 0)

    def rollTP(self):
        return TPRoll(self.tpWürfel, self.tpSeiten, self.tpPlus)
        
    def rollWundschmerz(self, wundenNeu):
        if not wundschmerz: return False
        if wundenNeu < 2: return False
        return random.randint(1,20) + self.char.attribute["KO"].probenwert + self.wundmalus() - (4 * max(wundenNeu - 2, 0)) < 20
        
    def rollKampfunfähig(self):
        if self.wunden < 5: return False
        return random.randint(1,20) + self.zähigkeitPW + self.wundmalus() < 12

    def onIniphase(self, defender):
        self.myTurn = True
        self.usedActions = {}
        self.pruneAdvantageDisadvantage(Fighter.DurationStartNextPhase)
        self.pruneAdvantageDisadvantage(Fighter.DurationStartNextPhaseOneRoll)

        if self.position != defender.position:
            # todo: movement and reach rules, not so relevant for the simulation...
            self.position = defender.position
            # trigger_onEnemyEnterReach
            for feat in defender.feats:
                if hasattr(feat, "trigger_onEnemyEnterReach"):
                    feat.trigger_onEnemyEnterReach(self, defender)

        if NormalerAngriff.isUsable(self):
            self.attack(defender, NormalerAngriff)
            if self.isAlive() and defender.isAlive() and NebenhandAngriff.isUsable(self):
                self.switchWeapons()
                self.attack(defender, NebenhandAngriff)
                self.switchWeapons()
        self.pruneAdvantageDisadvantage(Fighter.DurationEndPhase)
        self.pruneAdvantageDisadvantage(Fighter.DurationEndPhaseOneRoll)
        self.myTurn = False

    def attack(self, defender, attackType):
        attackType.use(self, defender)
        maneuvers = ai_chooseManeuvers(self, defender, attackType)
        featsAndManeuvers = self.feats + maneuvers

        # trigger_onAT
        atRoll = D20Roll(self.modAT())
        atRoll.modify(attackType.mod(self))
        atRoll.setAdvantageDisadvantage(self.hasAdvantage() or defender.enemyHasAdvantage(), self.hasDisadvantage() or defender.enemyHasDisadvantage())
        for feat in featsAndManeuvers:
            if hasattr(feat, "trigger_onAT"):
                feat.trigger_onAT(self, defender, atRoll)
        # Feats may give advantage onAT, so set again
        atRoll.setAdvantageDisadvantage(self.hasAdvantage() or defender.enemyHasAdvantage(), self.hasDisadvantage() or defender.enemyHasDisadvantage())
        at = atRoll.result()
        for duration in [Fighter.DurationStartNextPhaseOneRoll, Fighter.DurationEndPhaseOneRoll, Fighter.DurationEndNextPhaseOneRoll]:
            self.pruneAdvantageDisadvantage(duration)
            defender.pruneAdvantageDisadvantage(duration, enemyRoll=True)

        vtRoll = D20Roll(defender.modVT(), passive=vtPassiv) 
        vt = vtRoll.result()

        # trigger_onVTFailing
        if at > vt:
            for feat in defender.feats:
                if hasattr(feat, "trigger_onVTFailing"):
                    feat.trigger_onVTFailing(self, defender, atRoll, vtRoll)
        at = atRoll.result()
        vt = vtRoll.result()

        # evaluate
        if at > vt:
            if logFights: print(self.name + "s", attackType.name, "trifft mit", atRoll.str(), "gegen", vtRoll.str(), "| Manöver:", ", ".join([s.name for s in maneuvers]) if len(maneuvers) > 0 else "keine")
            
            # trigger_onATSucess
            if atRoll.isCrit():
                ai_addCritManeuvers(self, defender, attackType, featsAndManeuvers)     
            tpRoll = self.rollTP()
            for feat in featsAndManeuvers:
                if hasattr(feat, "trigger_onATSuccess"):
                    feat.trigger_onATSuccess(self, defender, atRoll, vtRoll, tpRoll)  
            defender.takeDamage(tpRoll, featsAndManeuvers)

            # trigger_onDamageReceived
            for feat in defender.feats:
                if hasattr(feat, "trigger_onDamageReceived"):
                    feat.trigger_onDamageReceived(self, defender, atRoll, vtRoll, tpRoll)
            # trigger_onDamageDealt
            for feat in featsAndManeuvers:
                if hasattr(feat, "trigger_onDamageDealt"):
                    feat.trigger_onDamageDealt(self, defender, atRoll, vtRoll, tpRoll)
        else:
            if logFights: print(self.name + "s", attackType.name, "trifft nicht mit", atRoll.str(), "gegen", vtRoll.str(), "| Manöver:", ", ".join([s.name for s in maneuvers]) if len(maneuvers) > 0 else "keine")
            
            # trigger_onVTSuccess
            for feat in defender.feats:
                if hasattr(feat, "trigger_onVTSuccess"):
                    feat.trigger_onVTSuccess(self, defender, atRoll, vtRoll)
            # trigger_onATFailed
            for feat in featsAndManeuvers:
                if hasattr(feat, "trigger_onATFailed"):
                    feat.trigger_onATFailed(self, defender, atRoll, vtRoll)
            if atRoll.isCritFail():
                if logFights: print("Patzer für", self.name)
                if "Unberechenbar" in self.waffenEigenschaften:
                    if logFights: print("> Eigentreffer durch unberechenbare Waffe")
                    self.takeDamage(self.rollTP(), [])
                if self.isAlive():
                    if Passierschlag.isUsable(defender):            
                        if logFights: print("> Passierschlag")
                        defender.attack(self, Passierschlag)
                    else:
                        if logFights: print(">", defender.name, "kann aber keinen Passierschlag mehr ausführen")

        # trigger_onATDone
        for feat in featsAndManeuvers:
            if hasattr(feat, "trigger_onATDone"):
                feat.trigger_onATDone(self, defender, atRoll, vtRoll)

    def takeDamage(self, tpRoll, featsAndManeuvers):
        ws = self.wsStern
        if tpRoll.isSP:
            ws = self.ws
        wundenNeu = math.floor((tpRoll.result() - 1) / ws)

        # trigger_onDealWounds
        for feat in featsAndManeuvers:
            if hasattr(feat, "trigger_onDealWounds"):
                wundenNeu = feat.trigger_onDealWounds(self, wundenNeu)

        if wundenNeu == 0:
            if logFights: print(">", self.name, "erleidet", tpRoll.str(), ", es reicht nicht für eine Wunde", "(WS " + str(ws) + ")")
            return
        if logFights: print(">", self.name, "erleidet", tpRoll.str(), "und", wundenNeu, "Wunde" if wundenNeu == 1 else "Wunden",  "(WS " + str(ws) + ")")
        self.wunden += wundenNeu
        betäubt = self.rollWundschmerz(wundenNeu)
        kampfunfähig = self.rollKampfunfähig()
        if betäubt:
            if logFights: print(">", self.name, "ist betäubt und verliert dadurch")
            self.wunden = 9
        if kampfunfähig:
            if logFights: print(">", self.name, "ist kampfunfähig")
            self.wunden = 9

# Simulation

def simulate(fighter1, fighter2):
    print("\n==== Starte Simulation ====")
    totalRounds = 0
    fighter1Wins = 0
    fighter2Wins = 0
    fighter2First = fighter2.ini > fighter1.ini
    for i in range(samples):
        if logFights: print("\n==== Neuer Kampf ====")
        fighter1.reset()
        fighter2.reset()
        rounds = 0       
        while fighter1.isAlive() and fighter2.isAlive():
            if not fighter2First:
                fighter1.onIniphase(fighter2)
                if fighter2.isAlive():
                    fighter2.onIniphase(fighter1)
            else:
                fighter2.onIniphase(fighter1)
                if fighter1.isAlive():
                    fighter1.onIniphase(fighter2)
            rounds += 1
            if rounds > 50:
                print("Kampf dauert zu lang, breche ab")
                return
        
        if fighter1.isAlive():
            fighter1Wins += 1
        else:
            fighter2Wins += 1
        totalRounds += rounds
        if fighter1.ini == fighter2.ini:
            fighter2First = not fighter2First
    print("\n==== Simulation beendet ====")
    print("\nDurchschnittliche Anzahl Initiativephasen:", totalRounds/samples)
    print("Win-Ratio", fighter1.name, "vs", fighter2.name, ":", fighter1Wins/samples * 100, "zu", fighter2Wins/samples * 100)
     
if os.path.isdir(Wolke.Settings['Pfad-Chars']):
    startDir = Wolke.Settings['Pfad-Chars']
else:
    startDir = ""
if not fighter1Path:
    fighter1Path, _ = QtWidgets.QFileDialog.getOpenFileName(None,"Charakterdatei für Kämpfer 1...", startDir, "XML Datei (*.xml)")
    if not fighter1Path:
        print("Du hast keine Charakterdatei gewählt.")
if not fighter2Path:
    fighter2Path, _ = QtWidgets.QFileDialog.getOpenFileName(None,"Charakterdatei für Kämpfer 2...", startDir, "XML Datei (*.xml)")
    if not fighter2Path:
        print("Du hast keine Charakterdatei gewählt.")
 
if fighter1Path and fighter2Path:
    fighter1 = Fighter(fighter1Name, fighter1Path, 0, fighter1WaffeIndex, fighter1NebenhandIndex, fighter1AusweichenIndex)
    fighter2 = Fighter(fighter2Name, fighter2Path, 6, fighter2WaffeIndex, fighter2NebenhandIndex, fighter2AusweichenIndex)
    simulate(fighter1, fighter2)