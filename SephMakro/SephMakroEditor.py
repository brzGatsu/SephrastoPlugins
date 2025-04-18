import os
import sys
from io import StringIO
import contextlib
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QCompleter, QApplication, QStyle
from PySide6.QtGui import QCursor
from PySide6.QtCore import Qt, QFile, QStringListModel
from QtUtils.PyEdit2 import TextEdit, NumberBar
import Datenbank
from Wolke import Wolke
from EinstellungenWrapper import EinstellungenWrapper
import PathHelper
from Hilfsmethoden import Hilfsmethoden
import traceback

@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

class SephMakroEditor(object):
    def __init__(self):
        EinstellungenWrapper.addSettings({"SephMakro_Pfad" : "", "WindowSize-SephMakro" : [1000, 800]})

    def setupMainForm(self):
        windowSize = Wolke.Settings["WindowSize-SephMakro"]
        self.formMain.resize(windowSize[0], windowSize[1])

        Wolke.DB = Datenbank.Datenbank()
        self.editor = TextEdit()
        self.numbers = NumberBar(self.editor)
        self.ui.horizontalLayout.layout().addWidget(self.numbers)
        self.ui.horizontalLayout.layout().addWidget(self.editor)

        # Just monospace doesn't work, have to specify fonts... seems to be an issue in chromium
        self.ui.teOutput.setProperty("class", "monospace")

        self.loadedText = ""

        buttonSize = Hilfsmethoden.emToPixels(3.2)
        self.ui.buttonRun.setFixedSize(buttonSize, buttonSize)
        self.ui.buttonRun.setText("\uf04b")
        self.setButtonShortcut(self.ui.buttonRun, "F5")
        self.ui.buttonRun.clicked.connect(self.run)

        self.ui.buttonNew.setFixedSize(buttonSize, buttonSize)
        self.ui.buttonNew.setText("\uf15b")
        self.setButtonShortcut(self.ui.buttonNew, "CTRL+N")
        self.ui.buttonNew.clicked.connect(self.new)

        self.ui.buttonLoad.setFixedSize(buttonSize, buttonSize)
        self.ui.buttonLoad.setText("\uf07c")
        self.setButtonShortcut(self.ui.buttonLoad, "CTRL+O")
        self.ui.buttonLoad.clicked.connect(self.load)

        self.ui.buttonSave.setFixedSize(buttonSize, buttonSize)
        self.ui.buttonSave.setText("\uf0c7")
        self.setButtonShortcut(self.ui.buttonSave, "CTRL+S")
        self.ui.buttonSave.clicked.connect(self.save)

        self.ui.buttonSaveOutput.clicked.connect(self.saveOutput)

        self.savePath = ""
        self.updateWindowTitle()
        self.editor.textChanged.connect(self.updateWindowTitle)

        self.editor.setFocus()
        self.formMain.activateWindow()
        self.buttonRefs = []
        self.updateButtons()

        optionsList = EinstellungenWrapper.getDatenbanken(Wolke.Settings['Pfad-Regeln'])
        self.ui.comboDB.addItems(optionsList)
        if Wolke.Settings['Datenbank'] in optionsList:
            self.ui.comboDB.setCurrentText(Wolke.Settings['Datenbank'])
        self.ui.comboDB.currentIndexChanged.connect(self.onDbChange)
        self.onDbChange()
        self.formMain.closeEvent = self.closeEvent

    def onDbChange(self):
        Wolke.DB.loadFile(hausregeln = self.ui.comboDB.currentText(), isCharakterEditor = False)

    def setButtonShortcut(self, button, shortcutStr):
        button.setShortcut(shortcutStr)
        button.setToolTip(button.toolTip() + " (" + button.shortcut().toString(QtGui.QKeySequence.NativeText) + ")")

    def updateWindowTitle(self):
        if self.savePath == "":
            self.formMain.setWindowTitle("SephMakro - Neues Makro")
        elif self.loadedText != self.editor.toPlainText():
            self.formMain.setWindowTitle("SephMakro - " + os.path.basename(self.savePath) + "*")
        else:
            self.formMain.setWindowTitle("SephMakro - " + os.path.basename(self.savePath))

    def run(self):
        prevText = self.ui.buttonRun.text()
        prevShortcut = self.ui.buttonRun.shortcut()
        self.ui.buttonRun.setText("\uf254")
        QtWidgets.QApplication.processEvents()
        with stdoutIO() as s:
            try:
                exec(self.editor.toPlainText(), {"datenbank" : Wolke.DB})
            except SyntaxError as e:
                print("Error: " + str(e))
            except Exception as e:
                cl, exc, tb = sys.exc_info()
                print("Error: " + str(e) + " (line " + str(traceback.extract_tb(tb)[-1][1]) + ")")
        self.ui.teOutput.setPlainText(s.getvalue())
        self.ui.buttonRun.setText(prevText)
        self.ui.buttonRun.setShortcut(prevShortcut)
        self.formMain.activateWindow()

    def updateButtons(self):
        self.buttonRefs = []
        layout = self.ui.makroListLayout.layout()
        for i in reversed(range(layout.count())):
            if layout.itemAt(i).widget():
                layout.itemAt(i).widget().setParent(None)
            else:
                layout.removeItem(layout.itemAt(i))

        if not os.path.isdir(Wolke.Settings["SephMakro_Pfad"]):
            return

        for file in PathHelper.listdir(Wolke.Settings["SephMakro_Pfad"]):
            if not file.endswith(".py"):
                continue
            button = QtWidgets.QPushButton()
            button.setText(os.path.splitext(os.path.basename(file))[0])
            button.clicked.connect(lambda a=False, f=os.path.join(Wolke.Settings["SephMakro_Pfad"], file): self.loadFile(f))
            self.buttonRefs.append(button)
            layout.addWidget(button)

        layout.addStretch()

    def cancelDueToPendingChanges(self, action):
        if self.loadedText != self.editor.toPlainText():
            messagebox = QtWidgets.QMessageBox()
            messagebox.setWindowTitle(action)
            messagebox.setText("Sollen die ausstehenden Änderungen gespeichert werden?")
            messagebox.setIcon(QtWidgets.QMessageBox.Question)
            messagebox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
            messagebox.setDefaultButton(QtWidgets.QMessageBox.Yes)
            result = messagebox.exec()
            if result == QtWidgets.QMessageBox.Yes:
                self.save()
            elif result == QtWidgets.QMessageBox.Cancel:
                return True
        return False

    def closeEvent(self,event):
        self.formMain.setFocus() #make sure editingfinished is called on potential line edits in focus
        if self.cancelDueToPendingChanges("Beenden"):
            event.ignore()
        else:
            Wolke.Settings["WindowSize-SephMakro"] = [self.formMain.size().width(), self.formMain.size().height()]
            Wolke.DB = None

    def loadFile(self, path):
        if self.cancelDueToPendingChanges("Makro laden"):
            return
        dir = os.path.dirname(path)
        if dir != Wolke.Settings["SephMakro_Pfad"]:
            Wolke.Settings["SephMakro_Pfad"] = dir
            EinstellungenWrapper.save()
            self.updateButtons()

        self.savePath = path

        with open(path, 'r', encoding="utf-8") as file:
            self.loadedText = file.read()
            self.editor.setPlainText(self.loadedText)
        self.updateWindowTitle()

    def new(self):
        if self.cancelDueToPendingChanges("Neues Makro"):
            return
        self.savePath = ""
        self.editor.setPlainText("")
        self.loadedText = ""
        self.updateWindowTitle()

    def load(self):
        startDir = Wolke.Settings["SephMakro_Pfad"]
        spath, _ = QtWidgets.QFileDialog.getOpenFileName(None,"Code laden...", startDir, "Python Datei (*.py)")

        if spath == "":
            return

        self.loadFile(spath)

    def save(self):
        if not self.savePath:
            self.savePath, _ = QtWidgets.QFileDialog.getSaveFileName(None,"Code speichern...","","Python Datei (*.py)")
            if self.savePath == "":
                return
        if not self.savePath.endswith(".py"):
            self.savePath = self.savePath + ".py"

        with open(self.savePath, "w", encoding="utf-8") as file:
            file.write(self.editor.toPlainText())

        self.loadedText = self.editor.toPlainText()
        self.updateWindowTitle()

    def saveOutput(self):
        spath, _ = QtWidgets.QFileDialog.getSaveFileName(None,"Ausgabe speichern...","","Textdatei (*.txt)")
        if spath == "":
            return
        if not spath.endswith(".txt"):
            spath = spath + ".txt"

        with open(spath, "w", encoding="utf-8") as file:
            file.write(self.ui.teOutput.toPlainText())