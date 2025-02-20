import lxml.etree as etree
import os.path
from Tierbegleiter import Tierbegleiter
import Datenbank
from Core.Talent import TalentDefinition

class TierbegleiterDatenbank(Datenbank.Datenbank):
    def __init__(self):
        super().__init__()

        # Tiervorteile und -begleiter laden
        self.tiervorteile = {}
        self.tierbegleiter = {}

        rootdir = os.path.dirname(os.path.abspath(__file__))
        tierbegleiterPath = os.path.join(rootdir, "Data", "Tierbegleiter.xml")
        vorteilePath = os.path.join(rootdir, "Data", "Tiervorteile.xml")
        
        if os.path.isfile(vorteilePath):
            root = etree.parse(vorteilePath).getroot()

            vorteilNodes = root.findall('Vorteil')
            for node in vorteilNodes:
                vorteil = Tierbegleiter.Modifikator()
                vorteil.deserialize(node)
                self.tiervorteile.update({vorteil.name: vorteil})
        if os.path.isfile(tierbegleiterPath):
            root = etree.parse(tierbegleiterPath).getroot()

            tierNodes = root.findall('Tierbegleiter')
            for node in tierNodes:
                tier = Tierbegleiter.TierbegleiterDefinition()
                tier.deserialize(node, self)
                self.tierbegleiter.update({tier.name: tier})

    def getTalenteProfan(self):
        return [t.name for t in self.talente.values() if t.fertigkeitszuordnung == TalentDefinition.Fertigkeitszuordnung.Profan]
