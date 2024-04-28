# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore
from Wolke import Wolke
from RuestungenPlus import RSDatenbankEditRuestungseigenschaft, Ruestungseigenschaft
from DatenbankElementEditorBase import DatenbankElementEditorBase, BeschreibungEditor, ScriptEditor
from QtUtils.HtmlToolbar import HtmlToolbar
from ScriptPickerWrapper import ScriptPickerWrapper
from EventBus import EventBus

class RSDatenbankEditRuestungseigenschaftWrapper(DatenbankElementEditorBase):

    ScriptContext = 82

    def __init__(self, datenbank, ruestungseigenschaft=None, readonly = False):
        super().__init__()
        self.beschreibungEditor = BeschreibungEditor(self)
        self.scriptEditor = ScriptEditor(self, lineLimit=2)
        self.setupAndShow(datenbank, RSDatenbankEditRuestungseigenschaft.Ui_ruestungseigenschaftDialog(), Ruestungseigenschaft.Ruestungseigenschaft, ruestungseigenschaft, readonly)

    def onSetupUi(self):
        super().onSetupUi()
        self.ui.buttonPickScript.setText("\uf121")
        self.ui.buttonPickScript.clicked.connect(self.openScriptPicker)

    def load(self, ruestungseigenschaft):
        super().load(ruestungseigenschaft)
        self.htmlToolbar = HtmlToolbar(self.ui.teBeschreibung)
        self.ui.tab.layout().insertWidget(0, self.htmlToolbar)
        self.beschreibungEditor.load(ruestungseigenschaft)
        self.ui.checkOnlyFirst.setChecked(ruestungseigenschaft.scriptOnlyFirst)
        self.scriptEditor.load(ruestungseigenschaft)

    def update(self, ruestungseigenschaft):
        super().update(ruestungseigenschaft)
        self.beschreibungEditor.update(ruestungseigenschaft)
        ruestungseigenschaft.scriptOnlyFirst = self.ui.checkOnlyFirst.isChecked()
        self.scriptEditor.update(ruestungseigenschaft)

    def openScriptPicker(self):
        pickerClass = EventBus.applyFilter("class_scriptpicker_wrapper", ScriptPickerWrapper)
        picker = pickerClass(self.datenbank, self.ui.teScript.toPlainText(), context=RSDatenbankEditRuestungseigenschaftWrapper.ScriptContext)
        if picker.script != None:
            self.ui.teScript.setPlainText(picker.script)