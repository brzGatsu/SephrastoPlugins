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
# - Für den VT Wert wird immer der hächste Werte aus Haupthand, Nebenhand und Ausweichen genommen
# - Fernkampf wird nicht unterstützt
# - Kampfstile: Alle außer Reiterkampf werden unterstützt (ohne Stufe IV). KVKIII, SKIII und BKII sind nicht implementiert, da nicht relevant in Duellen.
# - Profane Vorteile: Körperbeherrschung
# - Vorteile: Alle, außer Kommandos, Durchatmen, Atemtechnik. Sturmangriff wird nur mit zweihändigen Waffen genutzt und nur wenn kein SNK II. Mit Defensiver/Offensiver Kampfstil werden die entsprechenden Aktionen IMMER genutzt.
# - Manöver: Alle, außer Halten (werden automatisch eingesetzt auf basis einer simplen AI)
# - Waffeneigenschaften: Alle, außer Reittier, Stumpf und Zerbrechlich

# Global
vtPassiv = True # falls True wird kein W20 sondern 10 zur VT addiert
vtPassivMod = -10 # wieviel soll von der VT abgezogen werden bei vtPassiv = True (z.b. weil die 10 schon in Sephrasto hinzugefügt wird)
wundschmerz = False # sollen die Wundschmerzregeln verwendet werden? Betäubt wird mit Kampf verloren gleichgesetzt
samples = 1000 # wieviele Kämpfe sollen simuliert werden
useSchildspalter = False
kvk3ExtraAttack = True # behandelt kvk3 wie snk3 für eine bessere vergleichbarkeit
testManeuvers = False # Der Kampf wird einmal für jedes Manöver durchgeführt. Das Manöver wird bei jedem Angriff genutzt, aber nur von Kämpfer 1. Kämpfer 2 nutzt keine Manöver. Die Einstellung wird in Vebrindung mit simulate_all (s. u.) nicht verwendet

logFighters = True # sollen die Charakterwerte einmal am Anfang ausgegeben werden.
logFights = True # sollen die Kampfwürfe ausgegeben werden

simulate_all = [] # Hiermit können mehrere Simulaitonen nacheinander durchgeführt werden, dabei tritt jeder einmal gegen jeden an.
                  # Angabe als kommagetrennte Dateinamen ohne Dateiendung, die im Charakter-Ordner liegen,
                  # z. B. ["bhk_s3", "bsk_s3", "kvk_s3", "pwk_s3", "sk_s3", "snk_s3"].

fighter1Path = "" # Wird nur verwendet, wenn simulate_all leer ist. Pfad für charakter xml von Kämpfer 1 im Charakterordner ohne .xml Endung - falls leer, geht ein Datei-Auswahldialog auf
fighter1WaffeIndex = 2 # welche Waffe soll Kämpfer 1 verwenden - entspricht der Position im Waffen Tab, beginnend bei 0
fighter1NebenhandIndex = 3 # wird ignoriert, wenn fighter2WaffeIndex zweihändig ist
fighter1AusweichenIndex = 1 # bei -1 wird ausweichen nicht verwendet

fighter2Path = "" # Wird nur verwendet, wenn simulate_all leer ist. Pfad für charakter xml von Kämpfer 2 im Charakterordner ohne .xml Endung - falls leer, geht ein Datei-Auswahldialog auf
fighter2WaffeIndex = 2 # welche Waffe soll Kämpfer 2 verwenden - entspricht der Position im Waffen Tab, beginnend bei 0
fighter2NebenhandIndex = 3 # wird ignoriert, wenn fighter2WaffeIndex zweihändig ist
fighter2AusweichenIndex = 1 # bei -1 wird ausweichen nicht verwendet

# Stats
fighter1Mods = {"AT" : 0, "VT" : 0, "TP" : 0, "WS" : 0, "RS" : 0, "VolleOffensive" : False }
fighter2Mods = {"AT" : 0, "VT" : 0, "TP" : 0, "WS" : 0, "RS" : 0, "VolleOffensive" : False }
zähigkeitOverride = 18 # setzt die Zähigkeit bei allen Kämpfern auf den angegebenen Wert; setze es auf -1, um den Wert aus der Charakterdatei zu nehmen
iniOverride = 0 # setzt die INI bei allen Kämpfern auf den angegebenen Wert; setze es auf -1, um den Wert aus der Charakterdatei zu nehmen

if testManeuvers:
    logFights = False
if len(simulate_all) > 0:
    logFighters = False
    logFights = False

assert os.path.splitext(os.path.basename(datenbank.hausregelDatei))[0].startswith("Drachentöter"), "Bitte wähle die Drachentöter-Regeln aus"

#========== Implementation ===========

class Action:
    Aktion = "Aktion"
    Bonusaktion = "Bonusaktion"
    Reaktion = "Reaktion"
    ExtraAngriff = "Extra Angriff"
    NebenhandAngriffKostenlos = "Kostenloser Nebenhand Angriff"
    SchildwallKostenlos = "Kostenloser Schildwall"
    TückischeKlinge = "Tückische Klinge"
    Aufmerksamkeit = "Aufmerksamkeit"
    Präzision = "Präzision"

# Attack Types
class NormalerAngriff:
    name = "Normaler Angriff"
    def isUsable(attacker, defender): return attacker.isAlive() and defender.isAlive() and attacker.actionUsable(Action.Aktion) and attacker.myTurn
    def mod(fighter): return 0
    def isManeuverAllowed(fighter, maneuver): return True    
    def use(attacker, defender, tpMod = 0):
        for feat in attacker.feats:
            if hasattr(feat, "trigger_onNormalerAngriff"):
                feat.trigger_onNormalerAngriff(attacker, defender)
        attacker.useAction(Action.Aktion)
        attacker.attack(defender, NormalerAngriff, tpMod)

class NebenhandAngriff:
    name = "Nebenhandangriff"
    def isUsable(attacker, defender):
        if attacker.waffeIndex == attacker.nebenhandIndex:
            return False
        if attacker.isShieldBroken():
            return False
        return attacker.isAlive() and defender.isAlive() and attacker.actionUsable(Action.Bonusaktion) and attacker.myTurn
    def mod(fighter):
        mod = -4
        if fighter.kampfstil == "Beidhändiger Kampf" and "Beidhändiger Kampf II" in fighter.char.vorteile:
            mod = 0
        return mod
    def isManeuverAllowed(fighter, maneuver):
        if fighter.kampfstil == "Schildkampf" and "Schildkampf II" in fighter.char.vorteile:
            return maneuver.name.startswith("Wuchtschlag") or maneuver == Niederwerfen or maneuver == Umreißen
        return maneuver.name.startswith("Wuchtschlag")
    def use(attacker, defender, tpMod = 0):
        attacker.useAction(Action.Bonusaktion)
        attacker.attack(defender, NebenhandAngriff, tpMod)

class BonusAngriff:
    name = "Angriff in Bonusaktion"
    def isUsable(attacker, defender): return attacker.isAlive() and defender.isAlive() and attacker.actionUsable(Action.Bonusaktion) and attacker.myTurn
    def mod(fighter): return 0
    def isManeuverAllowed(fighter, maneuver): return True    
    def use(attacker, defender, tpMod = 0):
        attacker.useAction(Action.Bonusaktion)
        attacker.attack(defender, BonusAngriff, tpMod)

class ExtraAngriff:
    name = "Extra Angriff"
    def isUsable(attacker, defender): return attacker.isAlive() and defender.isAlive() and attacker.actionUsable(Action.ExtraAngriff) and attacker.myTurn
    def mod(fighter): return 0
    def isManeuverAllowed(fighter, maneuver): return True    
    def use(attacker, defender, tpMod = 0):
        attacker.useAction(Action.ExtraAngriff)
        attacker.attack(defender, ExtraAngriff, tpMod)

class Passierschlag:
    name = "Passierschlag"
    def isUsable(attacker, defender): return attacker.isAlive() and defender.isAlive() and attacker.actionUsable(Passierschlag.__getActionType(attacker))
    def mod(fighter): return 0
    def isManeuverAllowed(fighter, maneuver): return True    
    def use(attacker, defender, tpMod = 0):
        attacker.useAction(Passierschlag.__getActionType(attacker))
        attacker.attack(defender, Passierschlag, tpMod)
    def __getActionType(fighter):
        if "Aufmerksamkeit" in fighter.char.vorteile and fighter.actionUsable(Action.Aufmerksamkeit):
            return Action.Aufmerksamkeit
        return Action.Reaktion

# Maneuvers and Feats trigger order
# trigger_onMove (attacker)
# trigger_onEnemyMoveIntoReach (defender, only first iniphase)
# trigger_onMoveIntoReach (attacker, only first iniphase)
# trigger_onNormalerAngriff (attacker)
# trigger_onAT (attacker)
# if at > vt:
#     trigger_onVTFailing (defender)
# if still at > vt:
#     trigger_onATSuccess (attacker)
#     trigger_onVTFailed (defender)
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
    def isUnlocked(fighter): return True
    def mod(fighter): return -2
    def score(attacker, defender, attackType, atMod): return 2
    def trigger_onAT(attacker, defender, attackType, atRoll, maneuvers):
        atRoll.modify(Wuchtschlag2.mod(attacker))
    def trigger_onATSuccess(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        tpRoll.modify(2)

class Wuchtschlag4:
    name = "Wuchtschlag +4"
    def isUnlocked(fighter): return True
    def mod(fighter): return -4
    def score(attacker, defender, attackType, atMod): return 4
    def trigger_onAT(attacker, defender, attackType, atRoll, maneuvers):
        atRoll.modify(Wuchtschlag4.mod(attacker))
    def trigger_onATSuccess(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        tpRoll.modify(4)

class Wuchtschlag6:
    name = "Wuchtschlag +6"
    def isUnlocked(fighter): return True
    def mod(fighter): return -6
    def score(attacker, defender, attackType, atMod): return 6
    def trigger_onAT(attacker, defender, attackType, atRoll, maneuvers):
        atRoll.modify(Wuchtschlag6.mod(attacker))
    def trigger_onATSuccess(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        tpRoll.modify(6)

class Wuchtschlag8:
    name = "Wuchtschlag +8"
    def isUnlocked(fighter): return True
    def mod(fighter): return -8
    def score(attacker, defender, attackType, atMod): return 8   
    def trigger_onAT(attacker, defender, attackType, atRoll, maneuvers):
        atRoll.modify(Wuchtschlag8.mod(attacker))
    def trigger_onATSuccess(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        tpRoll.modify(8)

class Hammerschlag:
    name = "Hammerschlag"
    def isUnlocked(fighter): return "Hammerschlag" in fighter.char.vorteile
    def mod(fighter): return -8
    def score(attacker, defender, attackType, atMod): return 10
    def trigger_onAT(attacker, defender, attackType, atRoll, maneuvers):
        atRoll.modify(Hammerschlag.mod(attacker))
    def trigger_onATSuccess(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        tpRoll.multiplier = 2

class Todesstoß:
    name = "Todesstoß"
    def isUnlocked(fighter): return "Todesstoß" in fighter.char.vorteile
    def mod(fighter): return -8
    def score(attacker, defender, attackType, atMod): return 10
    def trigger_onAT(attacker, defender, attackType, atRoll, maneuvers):
        atRoll.modify(Todesstoß.mod(attacker))
    def trigger_onDealWounds(fighter, wounds, maneuvers):
        return wounds+2

class Schildspalter:
    name = "Schildspalter"
    def isUnlocked(fighter): return True
    def mod(fighter):
        mod = 2
        if "Zerstörerisch I"  in fighter.char.vorteile:
            mod += 4
        if "Zerstörerisch II"  in fighter.char.vorteile:
            mod += 4
        return mod
    def score(attacker, defender, attackType, atMod): return 5 if useSchildspalter and defender.kampfstil == "Schildkampf" and not defender.isShieldBroken() else -1
    def trigger_onAT(attacker, defender, attackType, atRoll, maneuvers):
        atRoll.modify(Schildspalter.mod(attacker))
    def trigger_onATSuccess(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        tpRoll.noDamage = True
        tpRoll = attacker.rollTP()
        for feat in maneuvers:
            if feat in [Wuchtschlag2, Wuchtschlag4, Wuchtschlag6, Wuchtschlag8, Hammerschlag]:
                feat.trigger_onATSuccess(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers)
        defender.takeShieldDamage(tpRoll)

class Rüstungsbrecher:
    name = "Rüstungsbrecher"
    def isUnlocked(fighter): return "Rüstungsbrechend" in fighter.waffenEigenschaften
    def mod(fighter): return -4
    def score(attacker, defender, attackType, atMod):
        rs = defender.wsStern - defender.ws
        if rs <= 2:
            return -1
        return rs
    def trigger_onAT(attacker, defender, attackType, atRoll, maneuvers):
        atRoll.modify(Rüstungsbrecher.mod(attacker))
    def trigger_onATSuccess(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        tpRoll.isSP = True

class Umreißen:
    name = "Umreißen"
    def isUnlocked(fighter): return True
    def mod(fighter): return 0
    def score(attacker, defender, attackType, atMod):
        if defender.amBoden:
            return -1
        if attackType != NebenhandAngriff or attacker.kampfstil != "Schildkampf":
            return -1
        score = 0
        standfestMod = 4 if "Standfest" in defender.char.vorteile else 0
        gegenprobeMod = defender.modAttribut("GE") + standfestMod
        score += (atMod - gegenprobeMod)
        if score < 0:
            return -1
        return score
    def score_iscombinable(): return False
    def trigger_onAT(attacker, defender, attackType, atRoll, maneuvers):
        atRoll.modify(Umreißen.mod(attacker))
    def trigger_onATSuccess(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        tpRoll.noDamage = True
        gegenprobe = D20Roll(defender.modAttribut("GE"))
        gegenprobe.setAdvantageDisadvantage("Standfest" in defender.char.vorteile, False)
        gegenprobe.roll()
        if gegenprobe.result() >= atRoll.result():
            if logFights: print(">", defender.name, "hat die Umreißen-Gegenprobe geschafft mit einer", gegenprobe.str())
            return
        defender.amBoden = True
        defender.disadvantage.append(Fighter.DurationEndNextPhase)
        defender.advantageForEnemy.append(Fighter.DurationStartNextPhase)
        if logFights: print(">", defender.name, "hat die Umreißen-Gegenprobe nicht geschafft mit einer", gegenprobe.str(), "und liegt am Boden")

class Niederwerfen:
    name = "Niederwerfen"
    def isUnlocked(fighter): return "Niederwerfen" in fighter.char.vorteile
    def mod(fighter): return -2
    def score(attacker, defender, attackType, atMod):
        if defender.amBoden:
            return -1 
        score = 2
        standfestMod = 4 if "Standfest" in defender.char.vorteile else 0
        gegenprobeMod = defender.modAttribut("KK") + standfestMod
        score += (atMod - gegenprobeMod)
        if score < 0:
            return -1
        return score
    def trigger_onAT(attacker, defender, attackType, atRoll, maneuvers):
        atRoll.modify(Niederwerfen.mod(attacker))
    def trigger_onATSuccess(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        gegenprobe = D20Roll(defender.modAttribut("KK"))
        gegenprobe.setAdvantageDisadvantage("Standfest" in defender.char.vorteile, False)
        gegenprobe.roll()
        if gegenprobe.result() >= atRoll.result():
            if logFights: print(">", defender.name, "hat die Niederwerfen-Gegenprobe geschafft mit einer", gegenprobe.str())
            return
        defender.amBoden = True
        defender.disadvantage.append(Fighter.DurationEndNextPhase)
        defender.advantageForEnemy.append(Fighter.DurationStartNextPhase)
        if logFights: print(">", defender.name, "hat die Niederwerfen-Gegenprobe nicht geschafft mit einer", gegenprobe.str(), "und liegt am Boden")

class Ausfall:
    name = "Ausfall"
    def isUnlocked(fighter): return "Ausfall" in fighter.char.vorteile
    def mod(fighter): return -2
    def score(attacker, defender, attackType, atMod):
        if defender.bedrängt:
            return -1
        score = 2
        gegenprobeMod = defender.modAttribut("MU")
        score += (atMod - gegenprobeMod)
        if score < 0:
            return -1
        return score
    def trigger_onAT(attacker, defender, attackType, atRoll, maneuvers):
        atRoll.modify(Ausfall.mod(attacker))
    def trigger_onATSuccess(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        gegenprobe = D20Roll(defender.modAttribut("MU"))
        gegenprobe.roll()
        if gegenprobe.result() >= atRoll.result():
            if logFights: print(">", defender.name, "hat die Ausfall-Gegenprobe geschafft mit einer", gegenprobe.str())
            return
        defender.bedrängt = True
        if logFights: print(">", defender.name, "hat die Ausfall-Gegenprobe nicht geschafft mit einer", gegenprobe.str(), "und ist bedrängt")

CombatManeuvers = [Wuchtschlag2, Wuchtschlag4, Wuchtschlag6, Wuchtschlag8, Hammerschlag, Todesstoß, Schildspalter, Rüstungsbrecher, Umreißen, Niederwerfen, Ausfall]

# Feats (offensive)
class SNKII:
    name = "Finte"
    def isUnlocked(fighter): return "Schneller Kampf II" in fighter.char.vorteile and fighter.kampfstil == "Schneller Kampf"
    def trigger_onAT(attacker, defender, attackType, atRoll, maneuvers):
        if not attacker.actionUsable(Action.Bonusaktion) or not attacker.myTurn:
            return
        if not atRoll.couldProfitFromAdvantage:
            return
        attacker.useAction(Action.Bonusaktion)
        attacker.advantage.append(Fighter.DurationEndPhaseOneRoll)
        if logFights: print(attacker.name, "gibt sich als Bonusaktion Vorteil durch", SNKII.name)

class SNKIII:
    name = "Unterlaufen"
    def isUnlocked(fighter): return "Schneller Kampf III" in fighter.char.vorteile and fighter.kampfstil == "Schneller Kampf"
    def trigger_onDamageDealt(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        if not ExtraAngriff.isUsable(attacker, defender):
            return
        if logFights: print(">", attacker.name, "macht einen weiteren Angriff durch", SNKIII.name)
        ExtraAngriff.use(attacker, defender)

class KVKII:
    name = "Durchbrechen"
    def isUnlocked(fighter): return "Kraftvoller Kampf II" in fighter.char.vorteile and fighter.kampfstil == "Kraftvoller Kampf"
    def trigger_onDamageDealt(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        if not atRoll.isCrit() or not BonusAngriff.isUsable(attacker, defender):
            return
        if logFights: print(">", attacker.name, "macht als Bonusaktion einen weiteren Angriff durch", KVKII.name)
        BonusAngriff.use(attacker, defender)

class KVKIII:
    name = "KVKIII (SNK III variante)"
    def isUnlocked(fighter): return kvk3ExtraAttack and "Kraftvoller Kampf III" in fighter.char.vorteile and fighter.kampfstil == "Kraftvoller Kampf"
    def trigger_onDamageDealt(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        if not ExtraAngriff.isUsable(attacker, defender):
            return
        if logFights: print(">", attacker.name, "macht einen weiteren Angriff durch", KVKIII.name)
        ExtraAngriff.use(attacker, defender)

class BHKIII:
    name = "BHK III"
    def isUnlocked(fighter): return "Beidhändiger Kampf III" in fighter.char.vorteile and fighter.kampfstil == "Beidhändiger Kampf"           
    def trigger_onATDone(attacker, defender, attackType, atRoll, vtRoll, maneuvers):
        if not ExtraAngriff.isUsable(attacker, defender):
            return
        if logFights: print(attacker.name, "macht einen weiteren Angriff durch", BHKIII.name)
        ExtraAngriff.use(attacker, defender)

class PWKII:
    name = "Tückische Klinge"
    def isUnlocked(fighter): return "Parierwaffenkampf II" in fighter.char.vorteile and fighter.kampfstil == "Parierwaffenkampf"
    def trigger_onATSuccess(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        if not atRoll.advantage or not attacker.actionUsable(Action.TückischeKlinge):
            return
        attacker.useAction(Action.TückischeKlinge)
        bonus = random.randint(1,6)
        tpRoll.modify(bonus)
        if logFights: print(">", attacker.name, "verursacht +", bonus, "TP durch", PWKII.name)

class Präzision:
    name = "Präzision"
    def isUnlocked(fighter): return "Präzision" in fighter.char.vorteile

    def trigger_onATSuccess(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        if not atRoll.advantage or not attacker.actionUsable(Action.Präzision):
            return
        attacker.useAction(Action.Präzision)
        bonus = random.randint(1,6) + random.randint(1,6)
        tpRoll.modify(bonus)
        if logFights: print(">", attacker.name, "erhält TP +", bonus, "durch", Präzision.name)        

class Unaufhaltsam:
    name = "Unaufhaltsam"
    def isUnlocked(fighter): return "Unaufhaltsam" in fighter.char.vorteile
    def trigger_onAT(attacker, defender, attackType, atRoll, maneuvers):
        atRoll.modifyCrit(-2)

class KalteWut:
    name = "Kalte Wut"
    def isUnlocked(fighter): return "Kalte Wut" in fighter.char.vorteile
    def trigger_onFirstIniphase(attacker, defender):
        if attacker.wundenIgnorieren:
            return False
        attacker.wunden += 1
        attacker.wundenIgnorieren = True
        attacker.useAction(Action.Bonusaktion)
        if logFights: print(attacker.name, "nutzt Kalte Wut.")   

class Sturmangriff:
    name = "Sturmangriff"
    def isUnlocked(fighter): return "Sturmangriff" in fighter.char.vorteile
    def trigger_onMoveIntoReach(attacker, defender):
        if not attacker.actionUsable(Action.Aktion) or not BonusAngriff.isUsable(attacker, defender):
            return
        if "Zweihändig" not in attacker.char.waffen[attacker.waffeIndex].eigenschaften:
            return
        if "Schneller Kampf II" in attacker.char.vorteile and attacker.kampfstil == "Schneller Kampf":
            return

        attacker.useAction(Action.Aktion)
        attacker.useAction(Action.ExtraAngriff)
        bonusTP = min(abs(attacker.deltaPosition), attacker.char.abgeleiteteWerte["GS"].finalwert)
        print(attacker.name, "nutzt", Sturmangriff.name, "für +" + str(bonusTP), "TP")
        BonusAngriff.use(attacker, defender, bonusTP)

class Klingentanz:
    name = "Klingentanz"
    def isUnlocked(fighter): return "Klingentanz" in fighter.char.vorteile
    def trigger_onMove(attacker, defender):
        # Wenn der Gegner Gegenhalten hat, Lösen sofort einsetzen
        if "Gegenhalten" not in defender.char.vorteile or "Klingentanz" in defender.char.vorteile or defender.isInReach(attacker):
            return
        if not attacker.actionUsable(Action.Bonusaktion):
            return
        if logFights: print(attacker.name, "nutzt Lösen als Bonusaktion durch", Klingentanz.name, "da der Gegner Gegenhalten hat")
        attacker.useAction(Action.Bonusaktion)
        attacker.lösen = True
    def trigger_onATDone(attacker, defender, attackType, atRoll, vtRoll, maneuvers):
        # Wenn ich Gegenhalten habe und der Gegner kein Klingentanz, am ende der Iniphase einsetzen und dann wegbewegen
        if "Gegenhalten" not in attacker.char.vorteile or "Klingentanz" in defender.char.vorteile or not attacker.actionUsable(Action.Bonusaktion):
            return
        if logFights: print(attacker.name, "nutzt Lösen als Bonusaktion durch", Klingentanz.name)
        attacker.useAction(Action.Bonusaktion)
        attacker.lösen = True

# Feats (defensive)
class SK:
    name = "Schildwall"
    def isUnlocked(fighter): return "Schildkampf I" in fighter.char.vorteile and fighter.kampfstil == "Schildkampf"
    def trigger_onVTFailing(attacker, defender, attackType, atRoll, vtRoll, maneuvers):
        if defender.isShieldBroken():
            return
        if not defender.actionUsable(Action.Reaktion):
            return
        bonus = 2
        if "Schildkampf II" in defender.char.vorteile:
            bonus = 4

        if atRoll.result() - vtRoll.result() > bonus:
            return
        defender.useAction(Action.Reaktion)
        vtRoll.modify(bonus)
        if logFights: print(defender.name, "verbessert als Reaktion die VT nachträglich um", bonus, "durch",  SK.name)

class PWKI:
    name = "Binden"
    def isUnlocked(fighter): return "Parierwaffenkampf I" in fighter.char.vorteile and fighter.kampfstil == "Parierwaffenkampf"
    def trigger_onVTSuccess(attacker, defender, attackType, atRoll, vtRoll, maneuvers):
        if not defender.actionUsable(Action.Reaktion):
            return
        defender.useAction(Action.Reaktion)
        attacker.advantageForEnemy.append(Fighter.DurationStartNextPhaseOneRoll)
        if logFights: print(">", defender.name, "verleiht als Reaktion dem nächsten Angriff gegen" , attacker.name, "Vorteil durch",  PWKI.name)

class PWKIII:
    name = "Kreuzblock"
    def isUnlocked(fighter): return "Parierwaffenkampf III" in fighter.char.vorteile and fighter.kampfstil == "Parierwaffenkampf"
    def trigger_onVTFailed(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        if not defender.actionUsable(Action.Reaktion):
            return
        defender.useAction(Action.Reaktion)
        tpRoll.overallMultiplier = 0.5
        if logFights: print(defender.name, "halbiert den erlittenen Schaden durch",  PWKIII.name)

class BKIII:
    name = "Vergeltung"
    def isUnlocked(fighter): return "Berserkerkampf III" in fighter.char.vorteile and fighter.kampfstil == "Berserkerkampf"
    def trigger_onDamageReceived(attacker, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers):
        if not Passierschlag.isUsable(defender, attacker):
            return
        if logFights: print(">", defender.name, "macht als Reaktion einen Angriff durch", BKIII.name)
        Passierschlag.use(defender, attacker)

class Gegenhalten:
    name = "Gegenhalten"
    def isUnlocked(fighter): return "Gegenhalten" in fighter.char.vorteile
    def trigger_onEnemyMoveIntoReach(attacker, defender):
        if not Passierschlag.isUsable(defender, attacker):
            return
        if logFights: print(defender.name, "führt Passierschlag aus durch", Gegenhalten.name)
        Passierschlag.use(defender, attacker)

class Körperbeherrschung:
    name = "Körperbeherrschung"
    def isUnlocked(fighter): return "Körperbeherrschung" in fighter.char.vorteile
    def trigger_onVTFailing(attacker, defender, attackType, atRoll, vtRoll, maneuvers):
        if atRoll.result() <= vtRoll.result():
            return # i. e. shieldwall could cause this
        gePW = defender.modAttribut("GE")
        ws = defender.wsStern
        if Rüstungsbrecher in maneuvers:
            ws = defender.ws
        estimatedWounds = math.floor((attacker.averageDamage - 1) / ws)
        if estimatedWounds < 2:
            return
        if gePW + 8 + min(estimatedWounds * 2, 12) < atRoll.result():
            return
        roll = random.randint(1,20) + gePW
        defender.wunden += 1
        if roll >= atRoll.result():
            if logFights: print(">", defender.name, "nutzt", Körperbeherrschung.name + " (+1 Wunde), um dem Angriff zu entgehen")
            vtRoll.special = "Körperbeherrschung"
        else:
            if logFights: print(">", defender.name, "nutzt", Körperbeherrschung.name + "(+1 Wunde), um dem Angriff zu entgehen, schafft die Gegenprobe aber nicht")


# Important: Körpebeherrschung needs to be evaluated last, so keep it at the end of the list
Feats = [SNKII, SNKIII, KVKII, KVKIII, BHKIII, PWKII, Präzision, KalteWut, Unaufhaltsam, Sturmangriff, SK, PWKI, PWKIII, BKIII, Gegenhalten, Klingentanz, Körperbeherrschung]

# "AI"
currentTestManeuver = None
def ai_chooseManeuvers(attacker, defender, attackType):
    if currentTestManeuver is not None:
        if attacker.index == 0:
            if currentTestManeuver in [Ausfall, Niederwerfen, Umreißen]:
                return [currentTestManeuver] if not defender.hasDisadvantage() else []
            else:
                return [currentTestManeuver]
        else:
            return []

    atMod = attackType.mod(attacker) + attacker.modATEstimation(defender)
    budget = atMod - defender.modVT() - 4
    budget = max(budget, defender.wsStern * 1.5 - attacker.maxDamage) #increase budget if our damage is too low
    if defender.wunden >= 6:
        budget -= 4 #dont overkill

    maneuversAvailable = [m for m in CombatManeuvers if m.isUnlocked(attacker) and m.score(attacker, defender, attackType, atMod) != -1 and attackType.isManeuverAllowed(attacker, m)]
    maneuversAvailable.sort(key = lambda m: m.score(attacker, defender, attackType, atMod))
    maneuvers = []
    while len(maneuversAvailable) > 0:
        maneuver = maneuversAvailable.pop()
        ignoreBudget = maneuver.mod(attacker) == 0
        if hasattr(maneuver, "score_ignorebudget"):
            ignoreBudget = maneuver.score_ignorebudget(attacker, defender, attackType, atMod)
        if not ignoreBudget and budget + maneuver.mod(attacker) < 0:
            continue
        if hasattr(maneuver, "score_iscombinable") and not maneuver.score_iscombinable():
            return [maneuver]
        if maneuver.name.startswith("Wuchtschlag"):
            maneuversAvailable = [m for m in maneuversAvailable if not m.name.startswith("Wuchtschlag")]
        budget += maneuver.mod(attacker)
        maneuvers.append(maneuver)
    return maneuvers

def ai_addCritManeuvers(attacker, defender, attackType, maneuvers):
    if logFights: print("Bestätigter Triumph für", attacker.name)
    atMod = attackType.mod(attacker) + attacker.modATEstimation(defender) + 10
    maneuversAvailable = [m for m in CombatManeuvers if m.isUnlocked(attacker) and m.score(attacker, defender, attackType, atMod) != -1 and attackType.isManeuverAllowed(attacker, m) and m != Wuchtschlag8 and m != Wuchtschlag6 and (m not in maneuvers or m == Wuchtschlag4)]
    maneuversAvailable.sort(key = lambda m: m.score(attacker, defender, attackType, atMod))
    maneuver = maneuversAvailable.pop()
    if logFights: print(">", maneuver.name)
    maneuvers.append(maneuver)

# Rolls

class TPRoll():
    def __init__(self, würfel, würfelSeiten, plus):
        self.würfel = würfel
        self.würfelSeiten = würfelSeiten
        self.plus = plus
        self.mod = 0
        self.multiplier = 1
        self.overallMultiplier = 1
        self.isSP = False
        self.noDamage = False
        self.lastRoll = -1

    def roll(self): self.lastRoll = self.würfel * random.randint(1,self.würfelSeiten) + self.plus
    def modify(self, value): self.mod += value
    def result(self):
        assert(self.lastRoll != -1)
        return round((round(self.lastRoll * self.multiplier) + self.mod) * self.overallMultiplier)
    def str(self): return str(self.result()) + (" SP" if self.isSP else " TP")

class D20Roll:
    def __init__(self, pw, passive=False):
        self.mod = pw
        self.passive = passive
        self.advantage = False
        self.disadvantage = False
        self.couldProfitFromAdvantage = True
        self.special = "" # i. e. Schildspalter, Körperbeherrschung
        self.critChance = 20
        self.failChance = 1
        self.lastRoll = -1

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

    def modEstimation(self):
        if self.advantage:
            return self.mod + 4
        elif self.disadvantage:
            return self.mod - 4
        return self.mod

    def modifyCrit(self, mod): self.critChance += mod
    def modifyFail(self, mod): self.failChance += mod
    def result(self):
        assert(self.lastRoll != -1)
        return self.lastRoll + self.mod
    def isFail(self): return self.lastRoll <= self.failChance
    def isConfirmedFail(self, difficulty): return self.isFail() and self.result() < difficulty
    def isCrit(self): return self.lastRoll >= self.critChance
    def isConfirmedCrit(self, difficulty): return self.isCrit() and self.result() >= difficulty
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

    def __init__(self, charPath, index, startPositionX, waffeIndex, nebenhandIndex, ausweichenIndex, mods):
        self.index = index
        self.char = Char()
        self.char.loadFile(charPath)
        self.char.aktualisieren()
        self.name = self.char.name or os.path.splitext(os.path.basename(charPath))[0]
        self.mods = mods
        self.ws = self.char.abgeleiteteWerte["WS"].wert + self.mods["WS"]
        self.wsStern = self.char.abgeleiteteWerte["WS"].finalwert + self.mods["WS"]  + self.mods["RS"]
        self.ini = self.char.abgeleiteteWerte["INI"].finalwert
        if iniOverride != -1:
            self.ini = iniOverride
        self.startPositionX = startPositionX
        self.reset()

        if logFighters: print("\n=====", self.name, "=====")
        attribute = "Attribute: "
        for attr in self.char.attribute.values():
            attribute += attr.name + " " + str(attr.probenwert) + " | "
        attribute = attribute[:-3]
        if logFighters: print(attribute)
        abgeleiteteWerte = "Abgeleitete Werte: "
        for aw in self.char.abgeleiteteWerte.values():
            abgeleiteteWerte += aw.name + " " + str(aw.finalwert) + " | "
        abgeleiteteWerte = abgeleiteteWerte[:-3]
        if logFighters: print(abgeleiteteWerte)

        self.zähigkeitPW = self.char.fertigkeiten["Selbstbeherrschung"].probenwert
        if "Zähigkeit" in self.char.talente:
            self.zähigkeitPW = self.char.fertigkeiten["Selbstbeherrschung"].probenwertTalent
        if zähigkeitOverride != -1:
            self.zähigkeitPW = zähigkeitOverride

        if logFighters: print("Talente: Zähigkeit", self.zähigkeitPW)
        self.waffeIndex = waffeIndex
        self.nebenhandIndex = nebenhandIndex
        self.ausweichenIndex = ausweichenIndex
        self.equip(waffeIndex, log=logFighters)
        self.vtWaffe = self.vt
        self.vtNebenhand = self.vt
        self.highestRW = self.rw
        self.ausweichen = 0
        if "Zweihändig" in self.waffenEigenschaften:
            self.nebenhandIndex = self.waffeIndex
        if self.waffeIndex != self.nebenhandIndex:
            self.equip(nebenhandIndex, log=logFighters)
            self.vtNebenhand = self.vt
            if self.rw > self.highestRW:
                self.highestRW = self.rw
        if self.ausweichenIndex != -1:
            self.equip(self.ausweichenIndex, log=logFighters)
            self.ausweichen = self.vt
        self.equip(waffeIndex)

        self.feats = []
        for feat in Feats:
            if feat.isUnlocked(self):
                self.feats.append(feat)
        if logFighters: print("Vorteile:", ", ".join(self.char.vorteile.keys()))

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
        self.schildWunden = 0
        self.usedActions = {}
        self.advantage = []
        self.disadvantage = []
        self.advantageForEnemy = []
        self.disadvantageForEnemy = []
        self.myTurn = False
        self.position = self.startPositionX
        self.deltaPosition = 0
        self.lösen = False
        self.bedrängt = False
        self.amBoden = False
        self.wundenIgnorieren = False
        self.iniphase = 0

    def actionUsable(self, action):
        return action not in self.usedActions

    def useAction(self, action):
        self.usedActions[action] = True
        
    def isAlive(self):
        return self.wunden < 9

    def wundmalus(self):
        return 0 if self.wundenIgnorieren else -(max(self.wunden -2, 0))*2

    def shieldmalus(self):
        return -(max(self.schildWunden -2, 0))*2

    def isShieldBroken(self):
        return self.schildWunden > 4

    def equip(self, index, log = False):
        self.waffeAktiv = index
        waffe = self.char.waffen[index]
        waffenwerte = self.char.waffenwerte[index]
        self.fertigkeit = waffe.fertigkeit
        self.kampfstil = waffenwerte.kampfstil
        self.at = waffenwerte.at + self.mods["AT"]
        self.vt = waffenwerte.vt + self.mods["VT"]
        self.rw = waffenwerte.rw
        self.tpWürfel = waffenwerte.würfel
        self.tpSeiten = waffe.würfelSeiten
        self.tpPlus = waffenwerte.plus + self.mods["TP"]
        self.waffenEigenschaften = waffe.eigenschaften
        self.averageDamage = (self.tpWürfel* ((self.tpSeiten / 2) + 0.5)) + self.tpPlus
        self.maxDamage = (self.tpWürfel * self.tpSeiten) + self.tpPlus
        if log:
            print(waffe.name, "mit", waffe.kampfstil or "keinem Kampfstil", "RW", self.rw, "AT", self.at, "VT", self.vt, "TP", str(self.tpWürfel) + "W" + str(self.tpSeiten) + ("+" if self.tpPlus >= 0 else "") + str(self.tpPlus), ", ".join(waffe.eigenschaften))

    def switchWeapons(self):
        if self.waffeAktiv == self.waffeIndex:
            self.equip(self.nebenhandIndex)
        else:
            self.equip(self.waffeIndex)

    def modAttribut(self, attribut):
        return self.char.attribute[attribut].probenwert + self.wundmalus()
        
    def modAT(self):
        at = self.at + self.wundmalus()
        if self.waffeAktiv == self.nebenhandIndex:
            at += self.shieldmalus()
        return at

    def modATEstimation(self, defender):
        roll = D20Roll(self.modAT())
        roll.setAdvantageDisadvantage(self.hasAdvantage() or defender.enemyHasAdvantage(), self.hasDisadvantage() or defender.enemyHasDisadvantage())
        return roll.modEstimation()
        
    def modVT(self):
        vt = self.vtWaffe
        if not self.isShieldBroken():
            if self.vtNebenhand + self.shieldmalus() > vt:
                vt = self.vtNebenhand + self.shieldmalus()
        if self.ausweichen > vt:
            vt = self.ausweichen
        return vt + self.wundmalus() + vtPassivMod

    def modAusweichen(self):
        return self.ausweichen + self.wundmalus() + vtPassivMod

    def rollTP(self):
        tp = TPRoll(self.tpWürfel, self.tpSeiten, self.tpPlus)
        tp.roll()
        return tp

    def rollINI(self):
        ini = D20Roll(self.ini)
        ini.setAdvantageDisadvantage("Klingentanz" in self.char.vorteile, False)
        ini.roll()
        return ini.result()
            
    def rollWundschmerz(self, wundenNeu):
        if not wundschmerz: return False
        if wundenNeu < 2: return False
        return random.randint(1,20) + self.char.attribute["KO"].probenwert + self.wundmalus() - (4 * max(wundenNeu - 2, 0)) < 20
        
    def rollKampfunfähig(self):
        if self.wunden < 5: return False
        return random.randint(1,20) + self.zähigkeitPW + self.wundmalus() < 12

    def isInReach(self, position):
        return abs(position - self.position) <= self.highestRW

    def move(self, position):
        self.deltaPosition = self.position - position
        self.position = position

    def moveInReach(self, position):
        if position > self.position:
            self.move(position - self.highestRW)
        else:
            self.move(position + self.highestRW)

    def onIniphase(self, defender):
        self.iniphase += 1
        self.myTurn = True
        self.lösen = False
        self.usedActions = {}
        self.pruneAdvantageDisadvantage(Fighter.DurationStartNextPhase)
        self.pruneAdvantageDisadvantage(Fighter.DurationStartNextPhaseOneRoll)
        if self.iniphase == 1:
            for feat in self.feats:
                if hasattr(feat, "trigger_onFirstIniphase"):
                    feat.trigger_onFirstIniphase(self, defender)

        if self.amBoden:
            if logFights: print(self.name, "steht auf")
            self.amBoden = False

        if not self.isInReach(defender.position):
            for feat in self.feats:
                if hasattr(feat, "trigger_onMove"):
                    feat.trigger_onMove(self, defender)

            if logFights: print(self.name, "bewegt sich zu", defender.name, "auf Distanz", self.highestRW)
            wasInDefenderReach = defender.isInReach(self.position)
            self.moveInReach(defender.position)

            # trigger_onEnemyEnterReach
            if not wasInDefenderReach and defender.isInReach(self.position):
                for feat in defender.feats:
                    if hasattr(feat, "trigger_onEnemyMoveIntoReach"):
                        feat.trigger_onEnemyMoveIntoReach(self, defender)

            # trigger_onMoveIntoReach
            for feat in self.feats:
                if hasattr(feat, "trigger_onMoveIntoReach"):
                    feat.trigger_onMoveIntoReach(self, defender)

        if (defender.actionUsable(Action.Reaktion) and self.bedrängt) or "Defensiver Kampfstil" in self.char.vorteile:
            if logFights: print(self.name, "nutzt volle Defensive")
            self.useAction(Action.Aktion)
            self.disadvantageForEnemy.append(Fighter.DurationStartNextPhase)
            self.disadvantage.append(Fighter.DurationEndPhaseOneRoll)
            if "Defensiver Kampfstil" in self.char.vorteile:
                self.useAction(Action.ExtraAngriff)
                BonusAngriff.use(self, defender)
        elif NormalerAngriff.isUsable(self, defender):
            if (self.actionUsable(Action.Reaktion) and self.mods["VolleOffensive"]) or "Offensiver Kampfstil" in self.char.vorteile:
                if logFights: print(self.name, "nutzt volle Offensive")
                if "Offensiver Kampfstil" not in self.char.vorteile:
                    self.useAction(Action.Reaktion)
                self.advantage.append(Fighter.DurationEndPhase)
                self.advantageForEnemy.append(Fighter.DurationStartNextPhase)
            NormalerAngriff.use(self, defender)
            if NebenhandAngriff.isUsable(self, defender):
                self.switchWeapons()
                NebenhandAngriff.use(self, defender)
                self.switchWeapons()

        if self.isAlive() and Gegenhalten in self.feats and (self.lösen or not defender.isInReach(self.position)):
            if logFights: print(self.name, "bewegt sich weg von", defender.name, "für", Gegenhalten.name)
            if defender.position > self.position:
                self.move(self.position - 1)
            else:
                self.move(self.position + 1)

        self.pruneAdvantageDisadvantage(Fighter.DurationEndPhase)
        self.pruneAdvantageDisadvantage(Fighter.DurationEndPhaseOneRoll)
        self.myTurn = False
        self.bedrängt = False

    def attack(self, defender, attackType, tpMod = 0):
        maneuvers = ai_chooseManeuvers(self, defender, attackType)
        featsAndManeuvers = self.feats + maneuvers
        unberechenbar = "Unberechenbar" in self.waffenEigenschaften
        # trigger_onAT
        atRoll = D20Roll(self.modAT())
        atRoll.modify(attackType.mod(self))
        atRoll.setAdvantageDisadvantage(self.hasAdvantage() or defender.enemyHasAdvantage(), self.hasDisadvantage() or defender.enemyHasDisadvantage())
        for feat in featsAndManeuvers:
            if hasattr(feat, "trigger_onAT"):
                feat.trigger_onAT(self, defender, attackType, atRoll, maneuvers)
        # Feats may give advantage onAT, so set again
        atRoll.setAdvantageDisadvantage(self.hasAdvantage() or defender.enemyHasAdvantage(), self.hasDisadvantage() or defender.enemyHasDisadvantage())
        atRoll.modifyFail(2 if unberechenbar else 0)
        atRoll.roll()
        for duration in [Fighter.DurationStartNextPhaseOneRoll, Fighter.DurationEndPhaseOneRoll, Fighter.DurationEndNextPhaseOneRoll]:
            self.pruneAdvantageDisadvantage(duration)
            defender.pruneAdvantageDisadvantage(duration, enemyRoll=True)

        vtRoll = D20Roll(defender.modVT(), passive=vtPassiv) 
        vtRoll.roll()

        # trigger_onVTFailing
        if atRoll.result() > vtRoll.result():
            for feat in defender.feats:
                if hasattr(feat, "trigger_onVTFailing"):
                    feat.trigger_onVTFailing(self, defender, attackType, atRoll, vtRoll, maneuvers)
        # evaluate
        if not vtRoll.special == "Körperbeherrschung":
            if atRoll.isCrit() and not atRoll.isConfirmedCrit(vtRoll.result() +1):
                if logFights: print(self.name + "s", attackType.name, "landet einen automatischen Treffer, allerdings ohne eventuelle Manöver:", ", ".join([s.name for s in maneuvers]) if len(maneuvers) > 0 else "keine")
                maneuvers = []
                featsAndManeuvers = self.feats
            if not atRoll.isFail() and (atRoll.isCrit() or atRoll.result() > vtRoll.result()):
                if logFights: print(self.name + "s", attackType.name, "trifft mit", atRoll.str(), "gegen", vtRoll.str(), "| Manöver:", ", ".join([s.name for s in maneuvers]) if len(maneuvers) > 0 else "keine")
                
                # trigger_onATSucess
                if atRoll.isConfirmedCrit(vtRoll.result() + 1):
                    ai_addCritManeuvers(self, defender, attackType, featsAndManeuvers)     
                tpRoll = self.rollTP()
                tpRoll.modify(tpMod)
                for feat in featsAndManeuvers:
                    if hasattr(feat, "trigger_onATSuccess"):
                        feat.trigger_onATSuccess(self, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers)
                for feat in defender.feats:
                  if hasattr(feat, "trigger_onVTFailed"):
                      feat.trigger_onVTFailed(self, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers)
                defender.takeDamage(tpRoll, featsAndManeuvers)

                # trigger_onDamageReceived
                for feat in defender.feats:
                    if hasattr(feat, "trigger_onDamageReceived"):
                        feat.trigger_onDamageReceived(self, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers)
                # trigger_onDamageDealt
                for feat in featsAndManeuvers:
                    if hasattr(feat, "trigger_onDamageDealt"):
                        feat.trigger_onDamageDealt(self, defender, attackType, atRoll, vtRoll, tpRoll, maneuvers)
            else:
                if logFights: print(self.name + "s", attackType.name, "trifft nicht mit", atRoll.str(), "gegen", vtRoll.str(), "| Manöver:", ", ".join([s.name for s in maneuvers]) if len(maneuvers) > 0 else "keine")
                
                # trigger_onVTSuccess
                for feat in defender.feats:
                    if hasattr(feat, "trigger_onVTSuccess"):
                        feat.trigger_onVTSuccess(self, defender, attackType, atRoll, vtRoll, maneuvers)
                # trigger_onATFailed
                for feat in featsAndManeuvers:
                    if hasattr(feat, "trigger_onATFailed"):
                        feat.trigger_onATFailed(self, defender, attackType, atRoll, vtRoll, maneuvers)

                if atRoll.isFail() and self.isAlive():
                    if atRoll.isConfirmedFail(vtRoll.result() +1):
                        if logFights: print("Bestätigter Patzer für", self.name)
                        if Passierschlag.isUsable(defender, self):            
                            if logFights: print("> Passierschlag")
                            Passierschlag.use(defender, self)
                        else:
                            if logFights: print(">", defender.name, "kann aber keinen Passierschlag mehr ausführen")
                    elif logFights: print("Unbestätigter Patzer für", self.name)
        # trigger_onATDone
        for feat in featsAndManeuvers:
            if hasattr(feat, "trigger_onATDone"):
                feat.trigger_onATDone(self, defender, attackType, atRoll, vtRoll, maneuvers)

    def takeShieldDamage(self, tpRoll):
        schild = self.char.waffen[self.nebenhandIndex]
        if "Schild" not in schild.eigenschaften:
            return
        wundenNeu = math.floor((tpRoll.result() - 1) / schild.härte)
        if wundenNeu == 0:
            if logFights: print(">", self.name + "s", "Schild erleidet", tpRoll.str(), ", es reicht nicht für eine Beschädigung", "(Härte " + str(schild.härte) + ")")
            return
        self.schildWunden += wundenNeu
        if logFights: print(">", self.name + "s", "Schild erleidet", tpRoll.str(), "und", wundenNeu, "Beschädigung" if wundenNeu == 1 else "Beschädigungen",  "(Härte " + str(schild.härte) + "), insgesamt", self.schildWunden, "Beschädigungen")

    def takeDamage(self, tpRoll, featsAndManeuvers):
        if tpRoll.noDamage:
            return

        ws = self.wsStern
        if tpRoll.isSP:
            ws = self.ws
        wundenNeu = math.floor((tpRoll.result() - 1) / ws)

        # trigger_onDealWounds
        for feat in featsAndManeuvers:
            if hasattr(feat, "trigger_onDealWounds"):
                wundenNeu = feat.trigger_onDealWounds(self, wundenNeu, featsAndManeuvers)

        if wundenNeu == 0:
            if logFights: print(">", self.name, "erleidet", tpRoll.str(), ", es reicht nicht für eine Wunde", "(WS " + str(ws) + ")")
            return

        self.wunden += wundenNeu
        if logFights: print(">", self.name, "erleidet", tpRoll.str(), "und", wundenNeu, "Wunde" if wundenNeu == 1 else "Wunden",  "(WS " + str(ws) + "), insgesamt", self.wunden, "Wunden")

        betäubt = self.rollWundschmerz(wundenNeu)
        kampfunfähig = self.rollKampfunfähig()
        if betäubt:
            if logFights: print(">", self.name, "ist betäubt und verliert dadurch")
            self.wunden = 9
        elif self.wunden > 8 or kampfunfähig:
            if logFights: print(">", self.name, "ist kampfunfähig")
            self.wunden = 9

# Simulation

def simulate(fighter1, fighter2):
    if logFights: print("\n==== Starte Simulation ====")
    totalRounds = 0
    fighter1Wins = 0
    fighter2Wins = 0

    # Start
    for i in range(samples):
        if logFights: print("\n==== Neuer Kampf ====")
        fighter1.reset()
        fighter2.reset()

        ini1 = fighter1.rollINI()
        ini2 = fighter2.rollINI()
        while(ini1 == ini2):
            ini2 = fighter2.rollINI()
        fighter2First = ini2 > ini1

        if logFights: print("INI:", fighter1.name, ini1, ",", fighter2.name, ini2)
        if logFights: print(fighter1.name, "und", fighter2.name, "treten in", abs(fighter1.position - fighter2.position), "Schritt Distanz zueinander an.")
        rounds = 0       
        while fighter1.isAlive() and fighter2.isAlive():
            if ini1 > ini2:
                fighter1.onIniphase(fighter2)
                if fighter2.isAlive():
                    fighter2.onIniphase(fighter1)
            else:
                fighter2.onIniphase(fighter1)
                if fighter1.isAlive():
                    fighter1.onIniphase(fighter2)
            rounds += 1
            assert rounds < 50, "Kampf dauert zu lang, breche ab"
        
        if fighter1.isAlive():
            fighter1Wins += 1
        else:
            fighter2Wins += 1
        totalRounds += rounds
    if logFights: print("\n==== Simulation beendet ====")
    print(fighter1.name, "vs", fighter2.name + ":", "Winratio", round(fighter1Wins/samples * 100, 1), "zu", round(fighter2Wins/samples * 100, 1), "| Ø", round(totalRounds/samples, 1), "INI-Phasen")
    return fighter1Wins, fighter2Wins

if len(simulate_all) > 0:
    index = 0
    leaderboard = {}
    for fighter in simulate_all:
        leaderboard[fighter] = []

    for i in range(len(simulate_all)-1):
        for j in range(i+1, len(simulate_all)):
            fighter1 = Fighter(os.path.join(Wolke.Settings['Pfad-Chars'], simulate_all[i] + ".xml"), 0, 0, fighter1WaffeIndex, fighter1NebenhandIndex, fighter1AusweichenIndex, fighter1Mods)
            fighter2 = Fighter(os.path.join(Wolke.Settings['Pfad-Chars'], simulate_all[j] + ".xml"), 1, 6, fighter2WaffeIndex, fighter2NebenhandIndex, fighter2AusweichenIndex, fighter2Mods)
            fighter1Wins, fighter2Wins = simulate(fighter1, fighter2)
            leaderboard[simulate_all[i]].append(fighter1Wins)
            leaderboard[simulate_all[j]].append(fighter2Wins)

    print("==== Ø Win vs all ====")
    for fighter in leaderboard:
        avgWins = sum(leaderboard[fighter]) / len(leaderboard[fighter])
        print(fighter, round(avgWins/samples * 100, 1), "%")
else:    
    if os.path.isdir(Wolke.Settings['Pfad-Chars']):
        startDir = Wolke.Settings['Pfad-Chars']
    else:
        startDir = ""
    if not fighter1Path:
        fighter1Path, _ = QtWidgets.QFileDialog.getOpenFileName(None,"Charakterdatei für Kämpfer 1...", startDir, "XML Datei (*.xml)")
        assert fighter1Path is not None, "Du hast keine Charakterdatei gewählt."
    else:
         fighter1Path = os.path.join(startDir, fighter1Path + ".xml")
    if fighter1Path and not fighter2Path:
        fighter2Path, _ = QtWidgets.QFileDialog.getOpenFileName(None,"Charakterdatei für Kämpfer 2...", startDir, "XML Datei (*.xml)")
        assert fighter2Path is not None, "Du hast keine Charakterdatei gewählt."
    elif fighter2Path:
        fighter2Path = os.path.join(startDir, fighter2Path + ".xml")
 
    fighter1 = Fighter(fighter1Path, 0, 0, fighter1WaffeIndex, fighter1NebenhandIndex, fighter1AusweichenIndex, fighter1Mods)
    fighter2 = Fighter(fighter2Path, 1, 6, fighter2WaffeIndex, fighter2NebenhandIndex, fighter2AusweichenIndex, fighter2Mods)
    if testManeuvers:
        for m in CombatManeuvers:
            print("\n==== Teste", m.name,"====")
            currentTestManeuver = m
            simulate(fighter1, fighter2)
    else:
        simulate(fighter1, fighter2)