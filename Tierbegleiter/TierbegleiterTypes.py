class Modifikator(object):
    def __init__(self):
        self.name = ''
        self.wirkung = ''
        self.manöver = False
        self.mod = None       

class Ausbildung(object):
    def __init__(self):
        self.name = ''
        self.kategorie = 0 # 1 = pferde, 2 = kamele
        self.modifikatoren = []
        self.weiterevorteile = None

class Zuchteigenschaft(object):
    def __init__(self):
        self.name = ''
        self.modifikatoren = []

class Waffe(object):
    def __init__(self):
        self.name = ''
        self.rw = 0
        self.at = 0
        self.vt = 0
        self.w6 = 0
        self.w20 = 0
        self.plus = 0
        self.eigenschaften = ""

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

class Tierbegleiter(object):
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