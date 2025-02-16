import lxml.etree as etree
import os.path
from Tierbegleiter import Tierbegleiter

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
            vorteil = Tierbegleiter.Modifikator()
            vorteil.deserialize(node)
            result.update({vorteil.name: vorteil})

        return result

    def xmlTierbegleiterLaden(self, file):
        result = {}
        root = etree.parse(file).getroot()

        tierNodes = root.findall('Tierbegleiter')
        for node in tierNodes:
            tier = Tierbegleiter.TierbegleiterDefinition()
            tier.deserialize(node, self)
            result.update({tier.name: tier})

            for mod in tier.modifikatoren:
                if mod.mod is not None and mod.name not in self.talente:
                    self.talente.append(mod.name)
        return result