from PySide6.QtWidgets import (
    QWidget,
    QDialog,
    QLabel,
    QVBoxLayout,
    QCheckBox,
    QPushButton,
    QProgressBar,
    QApplication,
    QScrollArea,
)
from PySide6.QtCore import Qt, QTimer
import sys


class ProgressDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("Charakter Synchronisieren")
        # self.setWindowModality(Qt.NonModal)  # Make it non-blocking
        self.setWindowModality(Qt.WindowModal)  # Make it modal to the parent window
        self.resize(400, 300)
        self.layout = QVBoxLayout(self)
        self.progressBar = QProgressBar(self)
        self.layout.addWidget(self.progressBar)
        self.messageBox = QScrollArea(self)
        self.messageBox.setWidgetResizable(True)
        self.messageBox.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.messageBox.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.messageContainer = QWidget()
        self.messageLayout = QVBoxLayout(self.messageContainer, alignment=Qt.AlignTop)
        self.messageBox.setWidget(self.messageContainer)
        self.layout.addWidget(self.messageBox)

        # OK button
        self.ok_button = QPushButton("OK")
        # self.ok_button.setEnabled(False)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

    def addMessage(self, message: str, bar: float | None = None, style=None):
        label = QLabel(message)
        self.messageLayout.addWidget(label)
        if bar is not None:
            self.progressBar.setValue(int(bar * 100))
        if style is not None:
            label.setStyleSheet(style)

    def accept(self):
        print("ACCEPTED")
        self.progressBar.setValue(100)
        super().accept()


    def enable(self):
        self.progressBar.setValue(100)
        self.ok_button.setEnabled(True)
