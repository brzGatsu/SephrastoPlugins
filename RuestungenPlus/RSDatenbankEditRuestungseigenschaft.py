# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'RSDatenbankEditRuestungseigenschaft.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QScrollArea, QSizePolicy, QTabWidget, QTextBrowser,
    QVBoxLayout, QWidget)

class Ui_ruestungseigenschaftDialog(object):
    def setupUi(self, ruestungseigenschaftDialog):
        if not ruestungseigenschaftDialog.objectName():
            ruestungseigenschaftDialog.setObjectName(u"ruestungseigenschaftDialog")
        ruestungseigenschaftDialog.resize(483, 595)
        self.verticalLayout_3 = QVBoxLayout(ruestungseigenschaftDialog)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.scrollArea = QScrollArea(ruestungseigenschaftDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName(u"scrollAreaWidgetContents_2")
        self.scrollAreaWidgetContents_2.setGeometry(QRect(0, 0, 459, 571))
        self.gridLayout = QGridLayout(self.scrollAreaWidgetContents_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.labelName = QLabel(self.scrollAreaWidgetContents_2)
        self.labelName.setObjectName(u"labelName")

        self.gridLayout.addWidget(self.labelName, 0, 0, 1, 1)

        self.leName = QLineEdit(self.scrollAreaWidgetContents_2)
        self.leName.setObjectName(u"leName")

        self.gridLayout.addWidget(self.leName, 0, 1, 1, 1)

        self.checkOnlyFirst = QCheckBox(self.scrollAreaWidgetContents_2)
        self.checkOnlyFirst.setObjectName(u"checkOnlyFirst")

        self.gridLayout.addWidget(self.checkOnlyFirst, 4, 1, 1, 1)

        self.tabWidget = QTabWidget(self.scrollAreaWidgetContents_2)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout = QVBoxLayout(self.tab)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.teBeschreibung = QPlainTextEdit(self.tab)
        self.teBeschreibung.setObjectName(u"teBeschreibung")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
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

        self.gridLayout.addWidget(self.tabWidget, 1, 1, 1, 1)

        self.labelScript = QLabel(self.scrollAreaWidgetContents_2)
        self.labelScript.setObjectName(u"labelScript")

        self.gridLayout.addWidget(self.labelScript, 2, 0, 1, 1)

        self.labelBeschreibung = QLabel(self.scrollAreaWidgetContents_2)
        self.labelBeschreibung.setObjectName(u"labelBeschreibung")

        self.gridLayout.addWidget(self.labelBeschreibung, 1, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.teScript = QPlainTextEdit(self.scrollAreaWidgetContents_2)
        self.teScript.setObjectName(u"teScript")

        self.horizontalLayout.addWidget(self.teScript)

        self.buttonPickScript = QPushButton(self.scrollAreaWidgetContents_2)
        self.buttonPickScript.setObjectName(u"buttonPickScript")
        font = QFont()
        font.setHintingPreference(QFont.PreferNoHinting)
        self.buttonPickScript.setFont(font)

        self.horizontalLayout.addWidget(self.buttonPickScript)


        self.gridLayout.addLayout(self.horizontalLayout, 2, 1, 1, 1)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents_2)

        self.verticalLayout_3.addWidget(self.scrollArea)


        self.retranslateUi(ruestungseigenschaftDialog)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ruestungseigenschaftDialog)
    # setupUi

    def retranslateUi(self, ruestungseigenschaftDialog):
        ruestungseigenschaftDialog.setWindowTitle(QCoreApplication.translate("ruestungseigenschaftDialog", u"Sephrasto - R\u00fcstungseigenschaft bearbeiten...", None))
        self.labelName.setText(QCoreApplication.translate("ruestungseigenschaftDialog", u"Name", None))
        self.checkOnlyFirst.setText(QCoreApplication.translate("ruestungseigenschaftDialog", u"Script nur bei erster R\u00fcstung ausf\u00fchren", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("ruestungseigenschaftDialog", u"HTML", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("ruestungseigenschaftDialog", u"Vorschau", None))
        self.labelScript.setText(QCoreApplication.translate("ruestungseigenschaftDialog", u"Script", None))
        self.labelBeschreibung.setText(QCoreApplication.translate("ruestungseigenschaftDialog", u"Beschreibung", None))
        self.buttonPickScript.setText(QCoreApplication.translate("ruestungseigenschaftDialog", u"+", None))
        self.buttonPickScript.setProperty(u"class", QCoreApplication.translate("ruestungseigenschaftDialog", u"iconSmall", None))
    # retranslateUi

