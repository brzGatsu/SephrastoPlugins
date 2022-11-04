import os
import sys
from io import StringIO
import contextlib
from PySide6 import QtWidgets, QtCore
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
        Wolke.DB = Datenbank.Datenbank()
        EinstellungenWrapper.addSettings(["SephMakro_Pfad"])

    def setupMainForm(self):
        self.editor = TextEdit()
        self.numbers = NumberBar(self.editor)
        self.ui.horizontalLayout.layout().addWidget(self.numbers)
        self.ui.horizontalLayout.layout().addWidget(self.editor)

        self.editor.setStyleSheet(self.stylesheet2())

        self.completer = QCompleter(self.formMain)
        self.completer.setModel(self.modelFromFile(os.path.dirname(os.path.abspath(__file__)) + '/resources/wordlist.txt'))
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setWrapAround(False)
        self.completer.setCompletionRole(Qt.EditRole)
        self.editor.setCompleter(self.completer)

        self.highlighter = Highlighter(self.editor.document())

        self.ui.buttonRun.setIcon(self.formMain.style().standardIcon(QStyle.SP_MediaPlay))
        self.ui.buttonRun.clicked.connect(self.run)

        self.ui.buttonLoad.setIcon(self.formMain.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.ui.buttonLoad.clicked.connect(self.load)

        self.ui.buttonSave.setIcon(self.formMain.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.ui.buttonSave.clicked.connect(self.save)

        self.ui.buttonSaveOutput.clicked.connect(self.saveOutput)

        self.savePath = ""

        self.editor.setFocus()

        self.buttonRefs = []
        self.updateButtons()

    def run(self):
        with stdoutIO() as s:
            try:
                exec(self.editor.toPlainText(), {"datenbank" : Wolke.DB})
            except Exception as e:
                print("Error: " + str(e))
        self.ui.teOutput.setPlainText(s.getvalue())

    def updateButtons(self):
        self.buttonRefs = []
        layout = self.ui.makroListLayout.layout()
        for i in reversed(range(layout.count())):
            if layout.itemAt(i).widget():
                layout.itemAt(i).widget().setParent(None)
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

    def loadFile(self, path):
        dir = os.path.dirname(path)
        if dir != Wolke.Settings["SephMakro_Pfad"]:
            Wolke.Settings["SephMakro_Pfad"] = dir
            EinstellungenWrapper.save()
            self.updateButtons()

        self.savePath = path

        with open(path, 'r', encoding="utf-8") as file:
            self.editor.setPlainText(file.read())

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

    def stylesheet2(self):
        return """
QPlainTextEdit
{
font-family: Noto Sans;
font-size: 13px;
background: #E2E2E2;
color: #202020;
border: 1px solid #1EAE3D;
}
QTextEdit
{
background: #2e3436;
color: #729fcf;
font-family: Monospace;
font-size: 8pt;
padding-left: 6px;
border: 1px solid #1EAE3D;
}
QStatusBar
{
font-family: Noto Sans;
color: #204a87;
font-size: 8pt;
}
QLabel
{
font-family: Noto Sans;
color: #204a87;
font-size: 8pt;
}
QLineEdit
{
background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
    stop: 0 #E1E1E1, stop: 0.4 #e5e5e5,
    stop: 0.5 #e9e9e9, stop: 1.0 #d2d2d2);
font-family: Helvetica;
font-size: 8pt;
}
QPushButton
{
background: #D8D8D8;
font-family: Noto Sans;
font-size: 8pt;
}
QComboBox
{
background: #D8D8D8;
font-family: Noto Sans;
font-size: 8pt;
}
QMenuBar
{
font-family: Noto Sans;
font-size: 8pt;
border: 0px;
}
QMenu
{
font-family: Noto Sans;
font-size: 8pt;
}
QToolBar
{
border: 0px;
background: transparent;
}
QMainWindow
{
background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
    stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
    stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
}
    """ 