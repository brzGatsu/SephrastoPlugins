from Wolke import Wolke
import lxml.etree as etree
import copy
import re
import base64

Attribute = ["KO", "MU", "GE", "KK", "IN", "KL", "CH", "FF", "WS", "RS", "BE", "MR", "GS", "TP", "INI", "AT", "VT"]

class Modifikator:
    def __init__(self):
        self.name = ''
        self.wirkung = ''
        self.manöver = False
        self.mod = None
        self.reiterkampf = 0

    def deserialize(self, root):
        self.name = root.get('name')
        self.wirkung = root.text
        if root.get('mod'):
            self.mod = int(root.get('mod'))
        if root.get('reiterkampf'):
            self.reiterkampf = int(root.get('reiterkampf'))
        if root.get('manöver'):
            self.manöver = root.get('manöver') == "1"

    def serialize(self, root):
        root.attrib['name'] = self.name
        if self.mod is not None:
            root.attrib['mod'] = str(self.mod)

class Waffe:
    def __init__(self):
        self.name = ''
        self.rw = 0
        self.at = 0
        self.vt = 0
        self.w6 = 0
        self.w20 = 0
        self.plus = 0
        self.eigenschaften = ""

    def deserialize(self, root):
        self.name = root.get('name')
        self.rw = int(root.get('rw'))
        self.vt = int(root.get('vt')) if root.get('vt') else None
        self.at = int(root.get('at')) if root.get('at') else None
        self.w6 = int(root.get('w6')) if root.get('w6') else None
        self.w20 = int(root.get('w20')) if root.get('w20') else None
        self.plus = int(root.get('plus')) if root.get('plus') else None
        self.eigenschaften = root.get('eigenschaften') or ''

    def getTP(self):
        tp = ""
        if self.w6 is not None:
            tp += str(self.w6) + "W6"
        elif self.w20 is not None:
            tp += str(self.w20) + "W20"
        else:
            tp += "-"
                
        if self.plus is not None:
            if self.plus >= 0:
                tp += "+"
            tp += str(self.plus)

        return tp

class TierbegleiterDefinition:
    def __init__(self):
        self.name = ''
        self.preis = 0
        self.groesse = 0
        self.modifikatoren = []
        self.rassen = ""
        self.futter = ""
        self.kategorie = 0
        self.preis = 0
        self.reittier = 0
        self.waffen = []

    def deserialize(self, root, datenbank):
        self.name = root.get('name')
        self.groesse = int(root.get('groesse'))
        self.preis = int(root.get('preis')) if root.get('preis') else 0
        self.futter = root.get('futter') or ''
        self.rassen = root.get('rassen') or ''
        self.kategorie = int(root.get('kategorie')) if root.get('kategorie') else 0
        self.reittier = int(root.get('reittier')) if root.get('reittier') else 0

        for attribut in ["ws", "rs", "mr", "ini", "gs", "gs2", "ko", "ge", "kk", "mu", "in", "ch", "kl", "ff"]:
            if root.get(attribut):
                mod = Modifikator()
                mod.name = str.upper(attribut)
                mod.mod = int(root.get(attribut))
                self.modifikatoren.append(mod)

        modNodes = root.findall('Modifikatoren/Modifikator')
        for modNode in modNodes:
            mod = Modifikator()
            mod.deserialize(modNode)
            if mod.name in datenbank.tiervorteile:
                tiervorteil = datenbank.tiervorteile[mod.name]
                mod.wirkung = tiervorteil.wirkung
                mod.manöver = tiervorteil.manöver

            self.modifikatoren.append(mod)

        waffenNodes = root.findall('Waffen/Waffe')
        for waffeNode in waffenNodes:
            waffe = Waffe()
            waffe.deserialize(waffeNode)
            self.waffen.append(waffe)

class Tierbegleiter:
    def __init__(self):
        self.definition = None
        self.bild = None
        self.name = ""
        self.nahrung = ""
        self.hintergrund = ""
        self.aussehen = ""

        self.reitenPW = 0
        self.reiterkampfStufe = 0
        self.reiterkampf4AT = 0
        self.reiterkampf4VT = 0
        self.reiterkampf4TP = 0

        self.attributMods = {}
        for attribut in Attribute:
            self.attributMods[attribut] = 0

        self.talentMods = []
        self.vorteilMods = []
        self.ausruestung = []

        self.regelnAnhaengen = Wolke.Settings['Cheatsheet']
        self.regelnGroesse = Wolke.Settings['Cheatsheet-Fontsize']
        self.formularEditierbar = Wolke.Settings['Formular-Editierbarkeit']
        
        # PDF Export values, merged with definition
        self.attributModsMerged = {}
        self.talentModsMerged = []
        self.vorteilModsMerged = []
        self.waffenMerged = []

    def aktualisieren(self):
        # main purpose of this function is to merge modifiers with TierbegleiterDefinition stats
        self.attributModsMerged = copy.deepcopy(self.attributMods)
        self.talentModsMerged = [copy.deepcopy(mod) for mod in self.talentMods if mod.name.strip()]
        self.vorteilModsMerged = [copy.deepcopy(mod) for mod in self.vorteilMods if mod.name.strip()]
        self.waffenMerged = []

        # remember the gs mod and then delete it - it will be reapplied after adding
        # the definition values. This is becasue some creatures have a GS2 value (e.g. flying speed)
        # and we want GS mods to only apply to GS2 then.
        modGS = self.attributModsMerged["GS"]
        del self.attributModsMerged["GS"]

        # now add definition values
        for mod in self.definition.modifikatoren:
            # case 1: mod is Vorteil
            if mod.mod is None:
                self.vorteilModsMerged.append(copy.copy(mod))
                continue

            # case 2: mod is Attribut
            if mod.name in Attribute + ["GS2"]:
                if mod.name not in self.attributModsMerged:
                    self.attributModsMerged[mod.name] = 0
                self.attributModsMerged[mod.name] += mod.mod
                continue

            # case 3: mod is Talent
            el = next((m for m in self.talentModsMerged if m.name == mod.name), None)
            if el is None:
                self.talentModsMerged.append(copy.copy(mod))
            else:
                el.mod += mod.mod
                
        # merge GS and GS2 to a single entry and reapply GS mod
        if "GS2" in self.attributModsMerged:
            self.attributModsMerged["GS"] = str(self.attributModsMerged["GS"]) + "/" + str(self.attributModsMerged["GS2"] + modGS)
            del self.attributModsMerged["GS2"]
        else:
            self.attributModsMerged["GS"] += modGS

        # calculate WS* from WS and RS mods
        self.attributModsMerged["WS*"] = self.attributModsMerged["WS"] + self.attributModsMerged["RS"]

        # remove vorteile that expect a higher reiterkampfstil level
        for vorteil in copy.copy(self.vorteilModsMerged):
            if vorteil.reiterkampf > self.reiterkampfStufe:
                self.vorteilModsMerged.remove(vorteil)

        # calculate waffen stats
        self.waffenMerged = copy.deepcopy(self.definition.waffen)
        for waffe in self.waffenMerged:
            if waffe.plus is not None:
                waffe.plus += self.attributModsMerged["TP"]
            if waffe.at is not None:
                waffe.at += self.attributModsMerged["AT"] - self.attributModsMerged["BE"]
            if waffe.vt is not None:
                waffe.vt += self.attributModsMerged["VT"] - self.attributModsMerged["BE"]

        # create variants of existing waffen for mounted combat
        if self.definition.reittier == 1:
            for waffe in self.waffenMerged.copy():
                if not "Reiterkampf" in waffe.eigenschaften:
                    continue

                # extract reiterkampf wm from eigenschaften and then remove it
                reiterkampfMod = 0
                match = re.search(r"Reiterkampf\s*\((-?\d+)\)", waffe.eigenschaften)
                if match:
                    reiterkampfMod = int(match.group(1))

                eigenschaften = list(map(str.strip, waffe.eigenschaften.split(",")))
                for eig in eigenschaften:
                    if eig.startswith("Reiterkampf"):
                        eigenschaften.remove(eig)
                        break
                waffe.eigenschaften = ", ".join(eigenschaften)

                # create waffe
                reitenWaffe = copy.copy(waffe)
                reitenWaffe.name = "Reiterkampf (" + reitenWaffe.name + ")"
                reitenWaffe.at = self.reitenPW + reiterkampfMod + min(self.reiterkampfStufe, 3) + self.attributModsMerged["AT"] - self.attributModsMerged["BE"]
                reitenWaffe.vt = self.reitenPW + reiterkampfMod + min(self.reiterkampfStufe, 3) + self.attributModsMerged["VT"] - self.attributModsMerged["BE"]
                reitenWaffe.plus += min(self.reiterkampfStufe, 3)
                if self.reiterkampfStufe >= 4:
                    reitenWaffe.at += self.reiterkampf4AT
                    reitenWaffe.vt += self.reiterkampf4VT
                    reitenWaffe.plus += self.reiterkampf4TP

                if reitenWaffe.eigenschaften:
                    reitenWaffe.eigenschaften += ", "
                reitenWaffe.eigenschaften += "AT +4 gegen kleinere Gegner"
                self.waffenMerged.append(reitenWaffe)

        # remove mods that have already been factored into other mods or that are zero so they dont show up
        del self.attributModsMerged["TP"]
        del self.attributModsMerged["AT"]
        del self.attributModsMerged["VT"]
        del self.attributModsMerged["RS"]
        del self.attributModsMerged["BE"]

        for (key, value) in list(self.attributModsMerged.items()):
            if value == 0:
                del self.attributModsMerged[key]

        for mod in copy.copy(self.talentModsMerged):
            if mod.mod == 0:
                self.talentModsMerged.remove(mod)

        # sort final merged lists
        order = ["KO", "MU", "GE", "KK", "IN", "KL", "CH", "FF", "WS", "WS*", "MR", "GS", "INI"]
        self.attributModsMerged = dict(sorted(self.attributModsMerged.items(), key = lambda x: order.index(x[0])))
        self.vorteilModsMerged.sort(key = lambda mod : mod.name)
        self.talentModsMerged.sort(key = lambda mod : mod.name)

    def serialize(self, root):
        etree.SubElement(root, 'Name').text = self.name
        etree.SubElement(root, 'Nahrung').text = self.nahrung
        etree.SubElement(root, 'Aussehen').text = self.aussehen
        etree.SubElement(root, 'Tier').text = self.definition.name
        etree.SubElement(root, 'Hintergrund').text = self.hintergrund

        etree.SubElement(root, 'Reiterkampf').text = str(self.reiterkampfStufe)
        etree.SubElement(root, 'Reiterkampf4AT').text = str(self.reiterkampf4AT)
        etree.SubElement(root, 'Reiterkampf4VT').text = str(self.reiterkampf4VT)
        etree.SubElement(root, 'Reiterkampf4TP').text = str(self.reiterkampf4TP)
        etree.SubElement(root, 'ReitenPW').text = str(self.reitenPW)

        attributeNode = etree.SubElement(root, 'Attribute')
        for attribut, mod in self.attributMods.items():
            attributNode = etree.SubElement(attributeNode, 'Attribut')
            attributNode.attrib['name'] = attribut
            attributNode.attrib['mod'] = str(mod)
        
        vorteileNode = etree.SubElement(root, 'Vorteile')
        for vorteil in self.vorteilMods:
            vorteilNode = etree.SubElement(vorteileNode, 'Vorteil')
            vorteil.serialize(vorteilNode)

        talenteNode = etree.SubElement(root, 'Talente')
        for talent in self.talentMods:
            talentNode = etree.SubElement(talenteNode, 'Talent')
            talent.serialize(talentNode)

        ausruestungNode = etree.SubElement(root, 'Ausrüstung')
        for gegenstand in self.ausruestung:
            etree.SubElement(ausruestungNode, 'Gegenstand').text = gegenstand

        if self.bild:
            etree.SubElement(root,'bild').text = base64.b64encode(self.bild)

        etree.SubElement(root, 'RegelnAnhängen').text = "1" if self.regelnAnhaengen else "0"
        etree.SubElement(root, 'RegelnGrösse').text = str(self.regelnGroesse)
        etree.SubElement(root, 'FormularEditierbarkeit').text = "1" if self.formularEditierbar else "0"

    def deserialize(self, root, datenbank):
        self.name = root.find('Name').text
        self.aussehen = root.find('Aussehen').text
        self.nahrung = root.find('Nahrung').text
        self.hintergrund = root.find('Hintergrund').text
        self.definition = datenbank.tierbegleiter[root.find('Tier').text]

        self.reiterkampfStufe = int(root.find('Reiterkampf').text)
        self.reiterkampf4AT = int(root.find('Reiterkampf4AT').text)
        self.reiterkampf4VT = int(root.find('Reiterkampf4VT').text)
        self.reiterkampf4TP = int(root.find('Reiterkampf4TP').text)
        self.reitenPW = int(root.find('ReitenPW').text)

        self.attributMods = {}
        for attribut in Attribute:
            self.attributMods[attribut] = 0
        for attributNode in root.findall('Attribute/'):
            self.attributMods[attributNode.attrib['name']] = int(attributNode.attrib['mod'])

        self.vorteilMods = []
        for vorteilNode in root.findall('Vorteile/'):
            mod = Modifikator()
            mod.deserialize(vorteilNode)
            self.vorteilMods.append(mod)

        self.talentMods = []
        for talentNode in root.findall('Talente/'):
            mod = Modifikator()
            mod.deserialize(talentNode)
            self.talentMods.append(mod)
    
        self.ausruestung = []
        for gegenstandNode in root.findall('Ausrüstung/Gegenstand'):
            self.ausruestung.append(gegenstandNode.text)

        bildNode = root.find('bild')
        if bildNode is not None:
            byteArray = bytes(bildNode.text, 'utf-8')
            self.bild = base64.b64decode(byteArray)

        self.regelnAnhaengen = root.find('RegelnAnhängen').text == "1"
        self.regelnGroesse = int(root.find('RegelnGrösse').text)
        self.formularEditierbar = root.find('FormularEditierbarkeit').text == "1"

        self.aktualisieren()

    def modifiersToString(self, summary = False):
        lineStart = ""
        lineEnd = ". "
        boldStart = ""
        boldEnd = ""
        if summary:
            lineStart = "<p>"
            lineEnd = "</p>"
            boldStart = '<b>'
            boldEnd = '</b>'

        text = ""
        addTitle = len(self.attributModsMerged) + len(self.talentModsMerged) + len(self.vorteilModsMerged) > 1

        if len(self.attributModsMerged) > 0:
            text += lineStart
            if addTitle:
                text += boldStart + "Attribute: " + boldEnd
            text += ", ".join([f'{k}: {v}' if summary or v < 0 else f'{k}: +{v}' for k,v in self.attributModsMerged.items()]) + lineEnd
        if len(self.talentModsMerged) > 0:
            text += lineStart
            if addTitle:
                text += boldStart + "Talente: " + boldEnd
            text += ", ".join(['%s: %s' % (mod.name, mod.mod) if mod.mod < 0 else '%s: +%s' % (mod.name, mod.mod) for mod in self.talentModsMerged]) + lineEnd
        if len(self.vorteilModsMerged) > 0:
            text += lineStart
            if addTitle:
                text += boldStart + "Vorteile: " + boldEnd
            text += ", ".join([mod.name if (summary or not mod.wirkung) else mod.wirkung for mod in self.vorteilModsMerged]) + lineEnd
        if len(self.waffenMerged) > 0:
            text += lineStart + boldStart + "Waffen: " + boldEnd + lineEnd
            for w in self.waffenMerged:
                text +=  lineStart + w.name + " (RW " + str(w.rw)
                text += ", AT " + (str(w.at) if w.at is not None else "-")
                text += ", VT " + (str(w.vt) if w.vt is not None else  "-" )
                text += ", TP "
                text += w.getTP()
                if w.eigenschaften:
                    text += ", " + w.eigenschaften
                text += ")" + lineEnd

        return text