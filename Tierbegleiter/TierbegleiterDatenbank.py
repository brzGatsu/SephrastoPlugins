import lxml.etree as etree
import os.path
from Wolke import Wolke
from Tierbegleiter import TierbegleiterTypes
from Datenbank import Datenbank

class DatabaseException(Exception):
    pass

class TierbegleiterDatenbank():
    def __init__(self):
        sephrastoDB = Datenbank()
        self.iaZuchtAusbildung = sephrastoDB.einstellungen["Tierbegleiter Plugin: IA Zucht und Ausbildung"].wert

        self.guteZuchteigenschaften = {}
        self.schlechteZuchteigenschaften = {}
        self.ausbildungen = {}
        self.tierbegleiter = {}
        self.tiervorteile = {}
        self.xmlLaden()              

    def xmlLaden(self):
        rootdir = os.path.dirname(os.path.abspath(__file__))
        ausbildungenPath = os.path.join(rootdir, "Data", "Ausbildungen.xml")
        guteZuchteigenschaftenPath = os.path.join(rootdir, "Data", "GuteZuchteigenschaften.xml")
        schlechteZuchteigenschaftenPath = os.path.join(rootdir, "Data", "SchlechteZuchteigenschaften.xml")

        
        if self.iaZuchtAusbildung:
            tierbegleiterPath = os.path.join(rootdir, "Data", "IATierbegleiter.xml")
            vorteilePath = os.path.join(rootdir, "Data", "IATiervorteile.xml")
        else:
            tierbegleiterPath = os.path.join(rootdir, "Data", "Tierbegleiter.xml")
            vorteilePath = os.path.join(rootdir, "Data", "Tiervorteile.xml")
        
        if os.path.isfile(vorteilePath):
            self.tiervorteile = self.xmlTiervorteileLaden(vorteilePath)
        if os.path.isfile(ausbildungenPath):
            self.ausbildungen = self.xmlAusbildungenLaden(ausbildungenPath)
        if os.path.isfile(guteZuchteigenschaftenPath):
            self.guteZuchteigenschaften = self.xmlZuchteigenschaftenLaden(guteZuchteigenschaftenPath)
        if os.path.isfile(schlechteZuchteigenschaftenPath):
            self.schlechteZuchteigenschaften = self.xmlZuchteigenschaftenLaden(schlechteZuchteigenschaftenPath)
        if os.path.isfile(tierbegleiterPath):
            self.tierbegleiter = self.xmlTierbegleiterLaden(tierbegleiterPath)

    def xmlTiervorteileLaden(self, file):
        result = {}
        root = etree.parse(file).getroot()

        ausbildungNodes = root.findall('Vorteil')
        for node in ausbildungNodes:
            vorteil = TierbegleiterTypes.Modifikator()
            vorteil.name = node.get('name')
            vorteil.wirkung = node.text
            vorteil.manöver = node.get('manöver') == "1"
            result.update({vorteil.name: vorteil})
        return result

    def xmlAusbildungenLaden(self, file):
        result = {}
        root = etree.parse(file).getroot()

        ausbildungNodes = root.findall('Ausbildung')
        for node in ausbildungNodes:
            ausbildung = TierbegleiterTypes.Ausbildung()
            ausbildung.name = node.get('name')
            ausbildung.kategorie = int(node.get('kategorie')) if node.get('kategorie') else 0
            ausbildung.preis = int(node.get('preis')) if node.get('preis') else 0
            ausbildung.weiterevorteile = node.get('weiterevorteile')
            modNodes = node.findall('Modifikatoren/Modifikator')
            for modNode in modNodes:
                name = modNode.get('name')
                if name in self.tiervorteile:
                    ausbildung.modifikatoren.append(self.tiervorteile[name])
                else:
                    mod = TierbegleiterTypes.Modifikator()
                    mod.name = name
                    if modNode.get('mod'):
                        mod.mod = int(modNode.get('mod'))
                    mod.wirkung = modNode.text
                    ausbildung.modifikatoren.append(mod)
            result.update({ausbildung.name: ausbildung})
        return result

    def xmlZuchteigenschaftenLaden(self, file):
        result = {}
        root = etree.parse(file).getroot()

        zuchtNodes = root.findall('Zuchteigenschaft')
        for node in zuchtNodes:
            zucht = TierbegleiterTypes.Zuchteigenschaft()
            zucht.name = node.get('name')
            modNodes = node.findall('Modifikatoren/Modifikator')
            for modNode in modNodes:
                mod = TierbegleiterTypes.Modifikator()
                mod.name = modNode.get('name')
                if modNode.get('mod'):
                    mod.mod = int(modNode.get('mod'))
                mod.wirkung = modNode.text

                zucht.modifikatoren.append(mod)
            result.update({zucht.name: zucht})
        return result

    def xmlTierbegleiterLaden(self, file):
        result = {}
        root = etree.parse(file).getroot()

        attributes = ["ws", "rs", "mr", "ini", "gs", "gs2", "ko", "ge", "kk", "mu", "in", "ch", "kl", "ff"]

        tierNodes = root.findall('Tierbegleiter')
        for node in tierNodes:
            tier = TierbegleiterTypes.Tierbegleiter()
            tier.name = node.get('name')
            tier.groesse = int(node.get('groesse'))
            tier.preis = int(node.get('preis')) if node.get('preis') else 0
            tier.futter = node.get('futter') or ''
            tier.rassen = node.get('rassen') or ''
            tier.kategorie = int(node.get('kategorie')) if node.get('kategorie') else 0
            tier.reittier = int(node.get('reittier')) if node.get('reittier') else 0

            for attribute in attributes:
                if node.get(attribute):
                    mod = TierbegleiterTypes.Modifikator()
                    mod.name = str.upper(attribute)
                    mod.mod = int(node.get(attribute))
                    tier.modifikatoren.append(mod)

            modNodes = node.findall('Modifikatoren/Modifikator')
            for modNode in modNodes:
                name = modNode.get('name')
                if name in self.tiervorteile:
                    tier.modifikatoren.append(self.tiervorteile[name])
                else:
                    mod = TierbegleiterTypes.Modifikator()
                    mod.name = name
                    if modNode.get('mod'):
                        mod.mod = int(modNode.get('mod'))
                    tier.modifikatoren.append(mod)

            waffenNodes = node.findall('Waffen/Waffe')
            for waffeNode in waffenNodes:
                waffe = TierbegleiterTypes.Waffe()
                waffe.name = waffeNode.get('name')
                waffe.rw = int(waffeNode.get('rw'))
                waffe.vt = int(waffeNode.get('vt')) if waffeNode.get('vt') else None
                waffe.at = int(waffeNode.get('at')) if waffeNode.get('at') else None
                waffe.w6 = int(waffeNode.get('w6')) if waffeNode.get('w6') else None
                waffe.w20 = int(waffeNode.get('w20')) if waffeNode.get('w20') else None
                waffe.plus = int(waffeNode.get('plus')) if waffeNode.get('plus') else None
                waffe.eigenschaften = waffeNode.get('eigenschaften') or ''
                tier.waffen.append(waffe)

            result.update({tier.name: tier})
        return result