# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'RSDatenbankEditRuestungseigenschaft.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QDialog,
    QDialogButtonBox, QGridLayout, QLabel, QLineEdit,
    QPlainTextEdit, QSizePolicy, QTabWidget, QTextBrowser,
    QVBoxLayout, QWidget)

class Ui_ruestungseigenschaftDialog(object):
    def setupUi(self, ruestungseigenschaftDialog):
        if not ruestungseigenschaftDialog.objectName():
            ruestungseigenschaftDialog.setObjectName(u"ruestungseigenschaftDialog")
        ruestungseigenschaftDialog.setWindowModality(Qt.ApplicationModal)
        ruestungseigenschaftDialog.resize(440, 356)
        self.gridLayout_2 = QGridLayout(ruestungseigenschaftDialog)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_2 = QLabel(ruestungseigenschaftDialog)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 3, 0, 1, 1)

        self.checkOnlyFirst = QCheckBox(ruestungseigenschaftDialog)
        self.checkOnlyFirst.setObjectName(u"checkOnlyFirst")

        self.gridLayout.addWidget(self.checkOnlyFirst, 4, 1, 1, 1)

        self.leName = QLineEdit(ruestungseigenschaftDialog)
        self.leName.setObjectName(u"leName")

        self.gridLayout.addWidget(self.leName, 1, 1, 1, 1)

        self.label = QLabel(ruestungseigenschaftDialog)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)

        self.label_5 = QLabel(ruestungseigenschaftDialog)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 2, 0, 1, 1)

        self.tabWidget = QTabWidget(ruestungseigenschaftDialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout = QVBoxLayout(self.tab)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.teBeschreibung = QPlainTextEdit(self.tab)
        self.teBeschreibung.setObjectName(u"teBeschreibung")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.teBeschreibung.sizePolicy().hasHeightForWidth())
        self.teBeschreibung.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.teBeschreibung)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_2 = QVBoxLayout(self.tab_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.tbBeschreibung = QTextBrowser(self.tab_2)
        self.tbBeschreibung.setObjectName(u"tbBeschreibung")

        self.verticalLayout_2.addWidget(self.tbBeschreibung)

        self.tabWidget.addTab(self.tab_2, "")

        self.gridLayout.addWidget(self.tabWidget, 2, 1, 1, 1)

        self.warning = QLabel(ruestungseigenschaftDialog)
        self.warning.setObjectName(u"warning")
        self.warning.setVisible(False)
        self.warning.setStyleSheet(u"background-color: rgb(255, 255, 0); color: black;")
        self.warning.setWordWrap(True)

        self.gridLayout.addWidget(self.warning, 0, 0, 1, 2)

        self.leScript = QLineEdit(ruestungseigenschaftDialog)
        self.leScript.setObjectName(u"leScript")

        self.gridLayout.addWidget(self.leScript, 3, 1, 1, 1)


        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.buttonBox = QDialogButtonBox(ruestungseigenschaftDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)
        self.buttonBox.setCenterButtons(True)

        self.gridLayout_2.addWidget(self.buttonBox, 1, 0, 1, 1)


        self.retranslateUi(ruestungseigenschaftDialog)
        self.buttonBox.accepted.connect(ruestungseigenschaftDialog.accept)
        self.buttonBox.rejected.connect(ruestungseigenschaftDialog.reject)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ruestungseigenschaftDialog)
    # setupUi

    def retranslateUi(self, ruestungseigenschaftDialog):
        ruestungseigenschaftDialog.setWindowTitle(QCoreApplication.translate("ruestungseigenschaftDialog", u"Sephrasto - R\u00fcstungseigenschaft bearbeiten...", None))
        self.label_2.setText(QCoreApplication.translate("ruestungseigenschaftDialog", u"Script", None))
        self.checkOnlyFirst.setText(QCoreApplication.translate("ruestungseigenschaftDialog", u"Script nur bei erster R\u00fcstung ausf\u00fchren", None))
        self.label.setText(QCoreApplication.translate("ruestungseigenschaftDialog", u"Name", None))
        self.label_5.setText(QCoreApplication.translate("ruestungseigenschaftDialog", u"Beschreibung", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("ruestungseigenschaftDialog", u"HTML", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("ruestungseigenschaftDialog", u"Vorschau", None))
        self.warning.setText(QCoreApplication.translate("ruestungseigenschaftDialog", u"<html><head/><body><p>Dies ist eine Standard-R\u00fcstungseigenschaft. Sobald du hier etwas ver\u00e4nderst, bekommst du eine pers\u00f6nliche Kopie und das Original wird in den Hausregeln gel\u00f6scht. Damit erh\u00e4ltst du f\u00fcr dies R\u00fcstungseigenschaft keine automatischen Updates mehr mit neuen R\u00fcstungenPlus-Plugin-Versionen.</p></body></html>", None))
    # retranslateUi

