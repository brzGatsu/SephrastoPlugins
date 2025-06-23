# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Tab.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QSizePolicy, QSpacerItem, QTextBrowser,
    QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(682, 460)
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(20, 20, 20, 20)
        self.groupBox = QGroupBox(Form)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.groupBox.setFlat(False)
        self.gridLayout_3 = QGridLayout(self.groupBox)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.labelHausregel = QLabel(self.groupBox)
        self.labelHausregel.setObjectName(u"labelHausregel")
        self.labelHausregel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_3.addWidget(self.labelHausregel, 3, 2, 1, 1)

        self.labelId = QLabel(self.groupBox)
        self.labelId.setObjectName(u"labelId")
        self.labelId.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_3.addWidget(self.labelId, 0, 2, 1, 1)

        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_3.addWidget(self.label_6, 5, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer, 7, 0, 1, 1)

        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.gridLayout_3.addWidget(self.label, 4, 0, 1, 1)

        self.labelBesitzer = QLabel(self.groupBox)
        self.labelBesitzer.setObjectName(u"labelBesitzer")
        self.labelBesitzer.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.labelBesitzer.setWordWrap(True)

        self.gridLayout_3.addWidget(self.labelBesitzer, 1, 2, 1, 1)

        self.labelGruppe = QLabel(self.groupBox)
        self.labelGruppe.setObjectName(u"labelGruppe")
        self.labelGruppe.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_3.addWidget(self.labelGruppe, 2, 2, 1, 1)

        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_3.addWidget(self.label_5, 3, 0, 1, 1)

        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.gridLayout_3.addWidget(self.label_3, 1, 0, 1, 1)

        self.labelUrl = QLabel(self.groupBox)
        self.labelUrl.setObjectName(u"labelUrl")
        self.labelUrl.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_3.addWidget(self.labelUrl, 4, 2, 1, 1)

        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_3.addWidget(self.label_2, 0, 0, 1, 1)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_3.addWidget(self.label_4, 2, 0, 1, 1)

        self.label_7 = QLabel(self.groupBox)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout_3.addWidget(self.label_7, 6, 0, 1, 1)

        self.labelBearbeitet = QLabel(self.groupBox)
        self.labelBearbeitet.setObjectName(u"labelBearbeitet")
        self.labelBearbeitet.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_3.addWidget(self.labelBearbeitet, 5, 2, 1, 1)

        self.labelErstellt = QLabel(self.groupBox)
        self.labelErstellt.setObjectName(u"labelErstellt")
        self.labelErstellt.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_3.addWidget(self.labelErstellt, 6, 2, 1, 1)


        self.horizontalLayout.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(Form)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout = QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.plainText = QTextBrowser(self.groupBox_2)
        self.plainText.setObjectName(u"plainText")

        self.verticalLayout.addWidget(self.plainText)


        self.horizontalLayout.addWidget(self.groupBox_2)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.groupBox.setTitle(QCoreApplication.translate("Form", u"Ilaris-Online Daten", None))
        self.labelHausregel.setText(QCoreApplication.translate("Form", u"-", None))
        self.labelId.setText(QCoreApplication.translate("Form", u"-", None))
        self.label_6.setText(QCoreApplication.translate("Form", u"Bearbeitet", None))
        self.label.setText(QCoreApplication.translate("Form", u"Web-Ansicht", None))
        self.labelBesitzer.setText(QCoreApplication.translate("Form", u"-", None))
        self.labelGruppe.setText(QCoreApplication.translate("Form", u"-", None))
        self.label_5.setText(QCoreApplication.translate("Form", u"Hausregeln", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"Besitzer", None))
        self.labelUrl.setText(QCoreApplication.translate("Form", u"-", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Datenbank-ID", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"Gruppe", None))
        self.label_7.setText(QCoreApplication.translate("Form", u"Erstellt", None))
        self.labelBearbeitet.setText(QCoreApplication.translate("Form", u"-", None))
        self.labelErstellt.setText(QCoreApplication.translate("Form", u"-", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("Form", u"Charakter Log", None))
    # retranslateUi

