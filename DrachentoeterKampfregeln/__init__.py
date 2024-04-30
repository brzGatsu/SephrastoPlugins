from PySide6 import QtWidgets, QtCore, QtGui
import shutil
import os
from Wolke import Wolke
from EinstellungenWrapper import EinstellungenWrapper

class Plugin:
    def __init__(self):
        rulesPath = Wolke.Settings["Pfad-Regeln"]
        rulesFile = "DrachentöterKampfregeln7.1.xml"
        rootdir = os.path.dirname(os.path.abspath(__file__))
        rulesFilePath = os.path.join(rootdir, "Data", rulesFile)
        rulesTargetPath = os.path.join(rulesPath, rulesFile)

        if os.path.isfile(rulesFilePath) and os.path.isdir(rulesPath):
            #copy rules file to rules path
            if not os.path.isfile(rulesTargetPath):
                shutil.copy2(rulesFilePath, rulesTargetPath)
                messagebox = QtWidgets.QMessageBox()
                messagebox.setWindowTitle("Drachentöter Hausregeln aktivieren?")
                messagebox.setText("Die Drachentöter Hausregeln wurden in den Regelpfad kopiert (siehe Sephrasto-Einstellungen).\n"\
                    "Sollen sie jetzt in den Einstellungen als Standard für neue Charaktere gesetzt werden?")
                messagebox.setIcon(QtWidgets.QMessageBox.Question)
                messagebox.addButton("Ja", QtWidgets.QMessageBox.YesRole)
                messagebox.addButton("Nein", QtWidgets.QMessageBox.NoRole)
                result = messagebox.exec()
                if result == 0:
                    Wolke.Settings["Datenbank"] = rulesFile
                    EinstellungenWrapper.save()