import lxml.etree as etree
import os.path
from Tierbegleiter import TierbegleiterTypes

class TierbegleiterDatenbank():
    def __init__(self):
        self.tierbegleiter = {}
        self.tiervorteile = {}
        self.talente = []
        self.xmlLaden()              

    def xmlLaden(self):
        rootdir = os.path.dirname(os.path.abspath(__file__))
        tierbegleiterPath = os.path.join(rootdir, "Data", "Tierbegleiter.xml")
        vorteilePath = os.path.join(rootdir, "Data", "Tiervorteile.xml")
        
        if os.path.isfile(vorteilePath):
            self.tiervorteile = self.xmlTiervorteileLaden(vorteilePath)
        if os.path.isfile(tierbegleiterPath):
            self.tierbegleiter = self.xmlTierbegleiterLaden(tierbegleiterPath)

    def xmlTiervorteileLaden(self, file):
        result = {}
        root = etree.parse(file).getroot()

        vorteilNodes = root.findall('Vorteil')
        for node in vorteilNodes:
            vorteil = TierbegleiterTypes.Modifikator()
            vorteil.name = node.get('name')
            vorteil.wirkung = node.text
            vorteil.manöver = node.get('manöver') == "1"
            result.update({vorteil.name: vorteil})
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
                        if mod.name not in self.talente:
                            self.talente.append(mod.name)
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