# -*- coding: utf-8 -*-

from PySide6 import QtCore, QtWidgets, QtGui
from Wolke import Wolke
from EventBus import EventBus
from EinstellungenWrapper import EinstellungenWrapper
from IlarisOnline import LoginDialog
from IlarisOnline.IlarisOnlineApi import APIClient

class LoginDialogWrapper(QtCore.QObject):
    loginSuccessful = QtCore.Signal()

    def __init__(self, callback=None):
        super().__init__()

        # self.parent = parent
        self.form = QtWidgets.QDialog()
        self.ui = LoginDialog.Ui_Dialog()
        self.ui.setupUi(self.form)

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText("Login")
        # self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setDisabled(True)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText("Abbrechen")
        
        self.ui.leBenutzer.setText(Wolke.Settings.get("IOUsername", "admin"))
        if callback:
            self.loginSuccessful.connect(callback)
        self.form.setModal(True)
        self.form.show()
        # self.form.activateWindow()
        self.cancel = self.form.exec() != QtWidgets.QDialog.Accepted
        if not self.cancel:
            self.login(self.ui.leBenutzer.text(), self.ui.lePasswort.text())
    
    def login(self, username, password):
        client = APIClient()
        print("starting login")
        def on_login(data, error=False, status=None):
            print(data)
            if error:
                print("Error in login")
                print(error)
                error_dia = QtWidgets.QMessageBox.critical(self.form, "Fehler", "Login fehlgeschlagen")
                return
            print("logged in")
            print(data)
            if "token" in data:
                token = data["token"]
                Wolke.Settings["IO_APIToken"] = token
                Wolke.Settings["IO_Username"] = username
                self.form.accept()
                self.loginSuccessful.emit()
            else:
                box = QtWidgets.QMessageBox.critical(self.form, "Fehler", "Login fehlgeschlagen")
                # box.setModal(True)
                # box.show()
        client.login(username, password, on_login)
            
        # if not self.cancel:
        #     self.selected = self.ui.treeKreaturen.currentItem().io_id
            # print(kreatur)
