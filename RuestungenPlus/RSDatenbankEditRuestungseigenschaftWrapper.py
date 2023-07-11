# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtCore
from Wolke import Wolke
from RuestungenPlus import RSDatenbankEditRuestungseigenschaft, Ruestungseigenschaft
from DatenbankElementEditorBase import DatenbankElementEditorBase, BeschreibungEditor, ScriptEditor
from QtUtils.HtmlToolbar import HtmlToolbar

class RSDatenbankEditRuestungseigenschaftWrapper(DatenbankElementEditorBase):
    def __init__(self, datenbank, ruestungseigenschaft=None, readonly = False):
        super().__init__()
        self.beschreibungEditor = BeschreibungEditor(self)
        self.scriptEditor = ScriptEditor(self, "script")
        self.setupAndShow(datenbank, RSDatenbankEditRuestungseigenschaft.Ui_ruestungseigenschaftDialog(), Ruestungseigenschaft.Ruestungseigenschaft, ruestungseigenschaft, readonly)

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