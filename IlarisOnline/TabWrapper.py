from PySide6 import QtWidgets, QtCore, QtGui
from IlarisOnline import Tab
from Wolke import Wolke

class TabWrapper(QtCore.QObject):
    modified = QtCore.Signal()
    
    def __init__(self):
        super().__init__()
        self.form = QtWidgets.QWidget()
        self.ui = Tab.Ui_Form()
        self.ui.setupUi(self.form)
    
    def changed(self):
        self.modified.emit()
        
    def load(self):
        pass
        
