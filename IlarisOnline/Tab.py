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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QLabel,
    QScrollArea, QSizePolicy, QSplitter, QTextBrowser,
    QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(701, 460)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(20, 20, 20, 20)
        self.splitter = QSplitter(Form)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.scrollArea = QScrollArea(self.splitter)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setMinimumSize(QSize(0, 0))
        self.scrollArea.setMaximumSize(QSize(16777215, 16777215))
        self.scrollArea.setFrameShape(QFrame.Shape.StyledPanel)
        self.scrollArea.setMidLineWidth(0)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 659, 418))
        self.gridLayout_2 = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.labelAlias = QLabel(self.scrollAreaWidgetContents)
        self.labelAlias.setObjectName(u"labelAlias")
        self.labelAlias.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.labelAlias, 1, 1, 1, 1)

        self.labelApiUrl = QLabel(self.scrollAreaWidgetContents)
        self.labelApiUrl.setObjectName(u"labelApiUrl")
        self.labelApiUrl.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.labelApiUrl.setWordWrap(True)

        self.gridLayout_2.addWidget(self.labelApiUrl, 2, 1, 1, 1)

        self.label_2 = QLabel(self.scrollAreaWidgetContents)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_2.addWidget(self.label_2, 1, 0, 1, 1)

        self.labelWebUrl = QLabel(self.scrollAreaWidgetContents)
        self.labelWebUrl.setObjectName(u"labelWebUrl")
        self.labelWebUrl.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout_2.addWidget(self.labelWebUrl, 3, 1, 1, 1)

        self.label = QLabel(self.scrollAreaWidgetContents)
        self.label.setObjectName(u"label")

        self.gridLayout_2.addWidget(self.label, 3, 0, 1, 1)

        self.label_3 = QLabel(self.scrollAreaWidgetContents)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.gridLayout_2.addWidget(self.label_3, 2, 0, 1, 1)

        self.labelTitelDetail = QLabel(self.scrollAreaWidgetContents)
        self.labelTitelDetail.setObjectName(u"labelTitelDetail")
        font = QFont()
        font.setBold(True)
        self.labelTitelDetail.setFont(font)

        self.gridLayout_2.addWidget(self.labelTitelDetail, 0, 0, 1, 2)

        self.plainText = QTextBrowser(self.scrollAreaWidgetContents)
        self.plainText.setObjectName(u"plainText")

        self.gridLayout_2.addWidget(self.plainText, 4, 0, 1, 2)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.splitter.addWidget(self.scrollArea)

        self.gridLayout.addWidget(self.splitter, 1, 0, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.labelAlias.setText(QCoreApplication.translate("Form", u"0", None))
        self.labelApiUrl.setText(QCoreApplication.translate("Form", u"0", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Datenbank-ID", None))
        self.labelWebUrl.setText(QCoreApplication.translate("Form", u"0", None))
        self.label.setText(QCoreApplication.translate("Form", u"Web-Ansicht", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"API-URL", None))
        self.labelTitelDetail.setText(QCoreApplication.translate("Form", u"Ilaris-Online Daten", None))
        self.labelTitelDetail.setProperty(u"class", QCoreApplication.translate("Form", u"h4", None))
    # retranslateUi

