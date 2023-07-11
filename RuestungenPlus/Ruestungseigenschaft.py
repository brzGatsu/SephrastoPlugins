# -*- coding: utf-8 -*-

class Ruestungseigenschaft():
    displayName = "Rüstungseigenschaft"

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
        return self.__dict__ == other.__dict__

    def finalize(self, db):
        self.scriptCompiled = compile(self.script or "", self.name + " Script", "exec")

    def executeScript(self, api):
        exec(self.scriptCompiled, api)

    def details(self, db):
        if self.script:
            return f"{self.text}\nScript: {self.script}"
        return self.text