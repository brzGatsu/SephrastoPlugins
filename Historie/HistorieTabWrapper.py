from PySide6 import QtWidgets, QtCore, QtGui
from Historie import HistorieTab

class HistorieTabWrapper(QtCore.QObject):
    modified = QtCore.Signal()
    
    def __init__(self):
        super().__init__()
        self.form = QtWidgets.QWidget()
        self.ui = HistorieTab.Ui_Form()
        self.ui.setupUi(self.form)
        # self.ui.lineEditName.textChanged.connect(self.changed)
        # self.layout = QtWidgets.QGridLayout()
        # self.form.setLayout(self.layout)
        # self.textEdit = QtWidgets.QPlainTextEdit()
        # self.textEdit.setPlainText("Hallo Welt")
        # self.layout.addWidget(self.textEdit, 0, 0)
    
    def changed(self):
        self.modified.emit()
        
    def load(self):
        pass
        
    def update(self):
        pass

