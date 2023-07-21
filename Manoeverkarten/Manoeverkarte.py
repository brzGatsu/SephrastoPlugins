# -*- coding: utf-8 -*-
class KartenTyp:
   Invalid = -1
   Vorteil = 0
   Regel = 1
   Talent = 2
   Waffeneigenschaft = 3
   Deck = 4
   Benutzerdefiniert = 5

   TypNamen = ["Vorteil", "Regel", "Talent", "Waffeneigenschaft", "Deck", "Benutzerdefiniert"]

class KartenUtility:
    @staticmethod
    def getAnzeigename(name):
        anzeigename = name
        for typName in KartenTyp.TypNamen:
            anzeigename = anzeigename.replace(f" ({typName})", "")
        return anzeigename

    @staticmethod
    def isNew(db, name, typ):
        name = KartenUtility.getAnzeigename(name)
        if typ == KartenTyp.Vorteil:
            table = db.vorteile
        elif typ == KartenTyp.Regel:
            table = db.regeln
        elif typ == KartenTyp.Talent:
            table = db.talente
        elif typ == KartenTyp.Waffeneigenschaft:
            table = db.waffeneigenschaften
        else:
            return True
        if name in table:
            return False
        return True

    @staticmethod
    def getOriginalElement(db, name, typ):
        name = KartenUtility.getAnzeigename(name)
        if typ == KartenTyp.Vorteil:
            table = db.vorteile
        elif typ == KartenTyp.Regel:
            table = db.regeln
        elif typ == KartenTyp.Talent:
            table = db.talente
        elif typ == KartenTyp.Waffeneigenschaft:
            table = db.waffeneigenschaften
        else:
            return None
        if name in table:
            return table[name]
        return None

    @staticmethod
    def getBenutzerdefinierteTypen(db):
        tags = set()
        builtin = set()
        for r in db.einstellungen["Regelanhang: Reihenfolge"].wert:
            if r[0] == "T" and len(r) > 2:
                builtin.add(r[2:])

        for k in db.karten.values():
            if k.typ != KartenTyp.Deck:
                continue
            tags.add(k.name)
        return sorted(list(tags - builtin))

    @staticmethod
    def getDeckKarte(db, name):
        for k in db.karten.values():
            if k.typ != KartenTyp.Deck:
                continue
            if k.name == name:
                return k
        return None

class Karte:
    displayName = "Manöverkarte"

    def __init__(self):
        # Serialized properties
        self.name = ""
        self.typ = KartenTyp.Invalid
        self.subtyp = -1
        self.titel = "$original$"
        self.subtitel = "$original$"
        self.text = "$original$"
        self.fusszeile = "$original$"
        self.löschen = False
        self.voraussetzungen = []
        self.customData = {}
        self.isUserAdded = True

        # Derived properties after deserialization
        self.farbe = "#000000"

    def deepequals(self, other): 
        if self.__class__ != other.__class__: return False
        return self.__dict__ == other.__dict__

    def finalize(self, db):
        pass

    def typname(self, db):
        name = "n/a"
        if self.typ != KartenTyp.Invalid:
            name = KartenTyp.TypNamen[self.typ]
        if self.subtyp == -1:
            return name

        if self.typ == KartenTyp.Vorteil:
            name += f" ({db.einstellungen['Vorteile: Typen'].wert[self.subtyp]})"
        elif self.typ == KartenTyp.Regel:
            name += f" ({db.einstellungen['Regeln: Typen'].wert[self.subtyp]})"
        elif self.typ == KartenTyp.Talent:
            name += f" ({list(db.einstellungen['Talente: Spezialtalent Typen'].wert.keys())[self.subtyp]})"
        return name

    def details(self, db):
        if self.löschen:
            return "Gelöscht"

        status = "Geändert"
        if self.isNew(db):
            status = "Neu"
        titel = self.titel.replace("$original$", self.anzeigename)
        return f"{status}. Titel: {titel}.\nUntertitel: {self.subtitel}.\nText: {self.text}\nFußzeile: {self.fusszeile}"

    @property
    def anzeigename(self):
        return KartenUtility.getAnzeigename(self.name)

    def isNew(self, db):
        return KartenUtility.isNew(db, self.name, self.typ)

    def getOriginalElement(self, db):
        return KartenUtility.getOriginalElement(db, self.name, self.typ)

