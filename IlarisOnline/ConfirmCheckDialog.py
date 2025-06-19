
from PySide6 import QtWidgets, QtCore, QtGui

class ConfirmCheckDialog(QtWidgets.QDialog):
    def __init__(self, message, box_label, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ilaris-Online")
        self.setModal(True)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.label = QtWidgets.QLabel(message)
        self.layout().addWidget(self.label)
        self.checkbox = QtWidgets.QCheckBox(box_label)
        self.layout().addWidget(self.checkbox)
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Yes | QtWidgets.QDialogButtonBox.No)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout().addWidget(self.buttonBox)
    
    def isChecked(self):
        return self.checkbox.isChecked()