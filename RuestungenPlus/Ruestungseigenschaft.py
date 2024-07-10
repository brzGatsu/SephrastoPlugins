# -*- coding: utf-8 -*-
from EventBus import EventBus
from RestrictedPython import compile_restricted

class Ruestungseigenschaft:
    displayName = "Rüstungseigenschaft"
    serializationName = "Rüstungseigenschaft"

    def __init__(self):
        # Serialized properties
        self.name = ''
        self.text = ''
        self.script = ''
        self.scriptOnlyFirst = False

        # Derived properties after deserialization
        self.scriptCompiled = ''

    def deepequals(self, other): 
        if self.__class__ != other.__class__: return False
        return self.name == other.name and \
            self.text == other.text and \
            self.script == other.script and \
            self.scriptOnlyFirst == other.scriptOnlyFirst

    def finalize(self, db):
        self.scriptCompiled = compile_restricted(self.script or "", self.name + " Script", "exec")

    def executeScript(self, api):
        try:
            exec(self.scriptCompiled, api)
        except Exception as e:
            raise type(e)(f"\nScriptfehler in Rüstungseigenschaft \"{self.name}\". Vermutlich hast du hier Änderungen in den Hausregeln vorgenommen, die das Problem verursachen.\n\nFehler: {str(e)}")

    def details(self, db):
        if self.script:
            return f"{self.text}\nScript: {self.script}"
        return self.text

    def serialize(self, ser):
        ser.set('name', self.name)
        ser.set('text', self.text)
        if self.script:
            ser.set('script', self.script)
            ser.set('scriptOnlyFirst', self.scriptOnlyFirst)
        EventBus.doAction("ruestungseigenschaft_serialisiert", { "object" : self, "serializer" : ser})

    def deserialize(self, ser, referenceDB = None):
        self.name = ser.get('name')
        self.text = ser.get('text')
        self.script = ser.get('script', self.script)
        self.scriptOnlyFirst = ser.getBool('scriptOnlyFirst', self.scriptOnlyFirst)
        EventBus.doAction("ruestungseigenschaft_deserialisiert", { "object" : self, "deserializer" : ser})