# -*- coding: utf-8 -*-
from VoraussetzungenListe import VoraussetzungenListe
from EventBus import EventBus

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
    serializationName = "Karte"

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
        self.voraussetzungen = VoraussetzungenListe()

        # Derived properties after deserialization
        self.farbe = "#000000"
        self.customData = {}

    def deepequals(self, other): 
        if self.__class__ != other.__class__: return False
        
        farbeEquals = True
        if self.typ == KartenTyp.Deck:
            farbeEquals = self.farbe == other.farbe

        return self.name == other.name and \
            self.typ == other.typ and \
            self.subtyp == other.subtyp and \
            self.titel == other.titel and \
            self.subtitel == other.subtitel and \
            self.text == other.text and \
            self.fusszeile == other.fusszeile and \
            self.löschen == other.löschen and \
            self.voraussetzungen == other.voraussetzungen and \
            farbeEquals

    def finalize(self, db):
        pass

    def kategorieName(self, db):
        name = "n/a"
        if self.typ != KartenTyp.Invalid:
            name = KartenTyp.TypNamen[self.typ]
        if self.subtyp == -1:
            return name

        if self.typ == KartenTyp.Vorteil:
            name += f" ({db.einstellungen['Vorteile: Kategorien'].wert.keyAtIndex(self.subtyp)})"
        elif self.typ == KartenTyp.Regel:
            name += f" ({db.einstellungen['Regeln: Kategorien'].wert.keyAtIndex(self.subtyp)})"
        elif self.typ == KartenTyp.Talent:
            name += f" ({db.einstellungen['Talente: Kategorien'].wert.keyAtIndex(self.subtyp)})"
        elif self.typ == KartenTyp.Benutzerdefiniert:
            name = f"{self.subtyp}"
            if self.fusszeile and self.fusszeile != "$original$":
                name += f" ({self.fusszeile})"
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
        return not self.löschen and KartenUtility.isNew(db, self.name, self.typ)

    def getOriginalElement(self, db):
        return KartenUtility.getOriginalElement(db, self.name, self.typ)

    def serialize(self, ser):
        ser.set('name', self.name)
        ser.set('text', self.text)
        ser.set('voraussetzungen', self.voraussetzungen.text)
        ser.set('typ', self.typ)
        ser.set('subtyp', self.subtyp)
        if self.typ == KartenTyp.Deck:
            ser.set('farbe', self.farbe)
        ser.set('titel', self.titel)
        ser.set('subtitel', self.subtitel)
        ser.set('fusszeile', self.fusszeile)
        ser.set('löschen', self.löschen)
        EventBus.doAction("karte_serialisiert", { "object" : self, "serializer" : ser})

    def deserialize(self, ser, referenceDB = None):
        self.name = ser.get('name')
        self.text = ser.get('text')
        self.voraussetzungen.compile(ser.get('voraussetzungen', ''))
        self.typ = ser.getInt('typ')
        self.subtyp = ser.get('subtyp')
        if self.typ != KartenTyp.Benutzerdefiniert:
            self.subtyp = int(self.subtyp)
        if self.typ == KartenTyp.Deck:
            self.farbe = ser.get('farbe')
        self.titel = ser.get('titel')
        self.subtitel = ser.get('subtitel')
        self.fusszeile = ser.get('fusszeile')
        self.löschen = ser.getBool('löschen', False)
        EventBus.doAction("karte_deserialisiert", { "object" : self, "deserializer" : ser})