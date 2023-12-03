# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Historie.ui'
##
## Created by: Qt User Interface Compiler version 6.5.3
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QGridLayout,
    QHeaderView, QLabel, QScrollArea, QSizePolicy,
    QSplitter, QTableWidget, QTableWidgetItem, QTextBrowser,
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
        self.splitter.setOrientation(Qt.Horizontal)
        self.historieTable = QTableWidget(self.splitter)
        if (self.historieTable.columnCount() < 3):
            self.historieTable.setColumnCount(3)
        __qtablewidgetitem = QTableWidgetItem()
        self.historieTable.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.historieTable.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.historieTable.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        self.historieTable.setObjectName(u"historieTable")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.historieTable.sizePolicy().hasHeightForWidth())
        self.historieTable.setSizePolicy(sizePolicy)
        self.historieTable.setMaximumSize(QSize(16777215, 16777215))
        self.historieTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.historieTable.setTabKeyNavigation(True)
        self.historieTable.setProperty("showDropIndicator", False)
        self.historieTable.setAlternatingRowColors(True)
        self.historieTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.splitter.addWidget(self.historieTable)
        self.historieTable.horizontalHeader().setStretchLastSection(True)
        self.historieTable.verticalHeader().setVisible(False)
        self.scrollArea = QScrollArea(self.splitter)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setMinimumSize(QSize(0, 0))
        self.scrollArea.setMaximumSize(QSize(16777215, 16777215))
        self.scrollArea.setFrameShape(QFrame.StyledPanel)
        self.scrollArea.setMidLineWidth(0)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 277, 418))
        self.gridLayout_2 = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.labelTitelDetail = QLabel(self.scrollAreaWidgetContents)
        self.labelTitelDetail.setObjectName(u"labelTitelDetail")
        font = QFont()
        font.setBold(True)
        self.labelTitelDetail.setFont(font)

        self.gridLayout_2.addWidget(self.labelTitelDetail, 0, 0, 1, 2)

        self.label_3 = QLabel(self.scrollAreaWidgetContents)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout_2.addWidget(self.label_3, 2, 0, 1, 1)

        self.labelEpGewinn = QLabel(self.scrollAreaWidgetContents)
        self.labelEpGewinn.setObjectName(u"labelEpGewinn")
        self.labelEpGewinn.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.labelEpGewinn.setWordWrap(True)

        self.gridLayout_2.addWidget(self.labelEpGewinn, 2, 1, 1, 1)

        self.plainText = QTextBrowser(self.scrollAreaWidgetContents)
        self.plainText.setObjectName(u"plainText")

        self.gridLayout_2.addWidget(self.plainText, 4, 0, 1, 2)

        self.labelDatum = QLabel(self.scrollAreaWidgetContents)
        self.labelDatum.setObjectName(u"labelDatum")
        self.labelDatum.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_2.addWidget(self.labelDatum, 1, 1, 1, 1)

        self.label_2 = QLabel(self.scrollAreaWidgetContents)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_2.addWidget(self.label_2, 1, 0, 1, 1)

        self.label = QLabel(self.scrollAreaWidgetContents)
        self.label.setObjectName(u"label")

        self.gridLayout_2.addWidget(self.label, 3, 0, 1, 1)

        self.labelEpAusgabe = QLabel(self.scrollAreaWidgetContents)
        self.labelEpAusgabe.setObjectName(u"labelEpAusgabe")
        self.labelEpAusgabe.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_2.addWidget(self.labelEpAusgabe, 3, 1, 1, 1)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.splitter.addWidget(self.scrollArea)

        self.gridLayout.addWidget(self.splitter, 1, 0, 1, 1)

        QWidget.setTabOrder(self.historieTable, self.scrollArea)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        ___qtablewidgetitem = self.historieTable.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("Form", u"EP Gesamt", None));
        ___qtablewidgetitem1 = self.historieTable.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("Form", u"Datum", None));
        ___qtablewidgetitem2 = self.historieTable.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("Form", u"Notiz", None));
        self.labelTitelDetail.setText(QCoreApplication.translate("Form", u"\u00c4nderungen in diesem Eintrag", None))
        self.labelTitelDetail.setProperty("class", QCoreApplication.translate("Form", u"h4", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"EP Zugewinn", None))
        self.labelEpGewinn.setText(QCoreApplication.translate("Form", u"0", None))
        self.labelDatum.setText(QCoreApplication.translate("Form", u"01.01.2000", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Datum", None))
        self.label.setText(QCoreApplication.translate("Form", u"EP Ausgaben", None))
        self.labelEpAusgabe.setText(QCoreApplication.translate("Form", u"0", None))
    # retranslateUi

