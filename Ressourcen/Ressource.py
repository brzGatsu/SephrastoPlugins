class Ressource:
    def __init__(self):
        self.name = ""
        self.kommentar = ""
        self.wert = 0

    def serialize(self, ser):
        ser.set('name', self.name)
        ser.set('kommentar', self.kommentar)
        ser.set('wert', self.wert)
        #EventBus.doAction("freiefertigkeit_serialisiert", { "object" : self, "serializer" : ser})

    def deserialize(self, ser):
        name = ser.get('name')
        #if name in Wolke.DB.freieFertigkeiten:
        #    definition = db[name]
        #else:
        #    definition = FreieFertigkeitDefinition()
        #    definition.name = name
        self.__init__()
        self.name = name
        self.kommentar = ser.get('kommentar', self.kommentar)
        self.wert = ser.getInt('wert', self.wert)
        #EventBus.doAction("freiefertigkeit_deserialisiert", { "object" : self, "deserializer" : ser})
        return True