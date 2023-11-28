import os
import sys
from io import StringIO
import contextlib
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QCompleter, QApplication, QStyle
from PySide6.QtGui import QCursor
from PySide6.QtCore import Qt, QFile, QStringListModel
from SephMakro.PyEdit2 import TextEdit
from SephMakro.PyEdit2 import NumberBar
from SephMakro.syntax_py import *
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
        cssEditor = """\
        QPlainTextEdit
        {
        font-family: Consolas,'Lucida Console','Liberation Mono','DejaVu Sans Mono','Bitstream Vera Sans Mono','Courier New',monospace,sans-serif;
        background: #E2E2E2;
        color: #202020;
        border: 1px solid #1EAE3D;
        }"""
        self.editor.setStyleSheet(cssEditor)

        cssOutput = """\
        QPlainTextEdit
        {
        font-family: Consolas,'Lucida Console','Liberation Mono','DejaVu Sans Mono','Bitstream Vera Sans Mono','Courier New',monospace,sans-serif;
        }"""
        self.ui.teOutput.setStyleSheet(cssOutput)

        self.completer = QCompleter(self.formMain)
        self.completer.setModel(self.modelFromFile(os.path.dirname(os.path.abspath(__file__)) + '/resources/wordlist.txt'))
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setWrapAround(False)
        self.completer.setCompletionRole(Qt.EditRole)
        self.editor.setCompleter(self.completer)

        self.highlighter = Highlighter(self.editor.document())

        self.loadedText = ""

        buttonSize = Hilfsmethoden.emToPixels(3.2)
        self.ui.buttonRun.setFixedSize(buttonSize, buttonSize)
        self.ui.buttonRun.setText("\uf04b")
        self.ui.buttonRun.clicked.connect(self.run)

        self.ui.buttonNew.setFixedSize(buttonSize, buttonSize)
        self.ui.buttonNew.setText("\uf15b")
        self.ui.buttonNew.clicked.connect(self.new)

        self.ui.buttonLoad.setFixedSize(buttonSize, buttonSize)
        self.ui.buttonLoad.setText("\uf07c")
        self.ui.buttonLoad.clicked.connect(self.load)

        self.ui.buttonSave.setFixedSize(buttonSize, buttonSize)
        self.ui.buttonSave.setText("\uf0c7")
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
        Wolke.DB.loadFile(hausregeln = self.ui.comboDB.currentText(), isCharakterEditor = True)

    def updateWindowTitle(self):
        if self.savePath == "":
            self.formMain.setWindowTitle("SephMakro - Neues Makro")
        elif self.loadedText != self.editor.toPlainText():
            self.formMain.setWindowTitle("SephMakro - " + os.path.basename(self.savePath) + "*")
        else:
            self.formMain.setWindowTitle("SephMakro - " + os.path.basename(self.savePath))

    def run(self):
        prevText = self.ui.buttonRun.text()
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
            messagebox.addButton("Ja", QtWidgets.QMessageBox.YesRole)
            messagebox.addButton("Nein", QtWidgets.QMessageBox.NoRole)
            messagebox.addButton("Abbrechen", QtWidgets.QMessageBox.RejectRole)
            result = messagebox.exec()
            if result == 0:
                self.save()
            elif result == 2:
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

    def modelFromFile(self, fileName):
        f = QFile(fileName)
        if not f.open(QFile.ReadOnly):
            return QStringListModel(self.completer)

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        self.words = []
        while not f.atEnd():
            line = f.readLine().trimmed()
            if line.length() != 0:
                try:
                    line = str(line, encoding='ascii')
                except TypeError:
                    line = str(line)

                self.words.append(line)

        QApplication.restoreOverrideCursor()

        return QStringListModel(self.words, self.completer)