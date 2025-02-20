# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'TierbegleiterMain.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QComboBox,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLayout, QLineEdit, QPlainTextEdit,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QSpinBox, QSplitter, QTabWidget, QVBoxLayout,
    QWidget)

class Ui_formMain(object):
    def setupUi(self, formMain):
        if not formMain.objectName():
            formMain.setObjectName(u"formMain")
        formMain.setWindowModality(Qt.WindowModality.ApplicationModal)
        formMain.resize(1023, 745)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(formMain.sizePolicy().hasHeightForWidth())
        formMain.setSizePolicy(sizePolicy)
        self.verticalLayout_14 = QVBoxLayout(formMain)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.splitter = QSplitter(formMain)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.tabWidget = QTabWidget(self.splitter)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout = QVBoxLayout(self.tab)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.groupBox_2 = QGroupBox(self.tab)
        self.groupBox_2.setObjectName(u"groupBox_2")
        sizePolicy.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy)
        self.gridLayout_14 = QGridLayout(self.groupBox_2)
        self.gridLayout_14.setObjectName(u"gridLayout_14")
        self.gridLayout_14.setContentsMargins(20, 20, 20, 20)
        self.label_18 = QLabel(self.groupBox_2)
        self.label_18.setObjectName(u"label_18")
        font = QFont()
        font.setBold(True)
        self.label_18.setFont(font)
        self.label_18.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.gridLayout_14.addWidget(self.label_18, 5, 0, 1, 1)

        self.cbZucht = QComboBox(self.groupBox_2)
        self.cbZucht.setObjectName(u"cbZucht")

        self.gridLayout_14.addWidget(self.cbZucht, 2, 1, 1, 1)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.cbTier = QComboBox(self.groupBox_2)
        self.cbTier.setObjectName(u"cbTier")

        self.verticalLayout_5.addWidget(self.cbTier)

        self.lblTier = QLabel(self.groupBox_2)
        self.lblTier.setObjectName(u"lblTier")
        self.lblTier.setWordWrap(True)

        self.verticalLayout_5.addWidget(self.lblTier)

        self.hlReittier = QWidget(self.groupBox_2)
        self.hlReittier.setObjectName(u"hlReittier")
        self.horizontalLayout_2 = QHBoxLayout(self.hlReittier)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.lblReiten = QLabel(self.hlReittier)
        self.lblReiten.setObjectName(u"lblReiten")

        self.horizontalLayout_2.addWidget(self.lblReiten)

        self.sbReiten = QSpinBox(self.hlReittier)
        self.sbReiten.setObjectName(u"sbReiten")
        self.sbReiten.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbReiten.setMinimum(-10)

        self.horizontalLayout_2.addWidget(self.sbReiten)

        self.lblRK = QLabel(self.hlReittier)
        self.lblRK.setObjectName(u"lblRK")

        self.horizontalLayout_2.addWidget(self.lblRK)

        self.sbRK = QSpinBox(self.hlReittier)
        self.sbRK.setObjectName(u"sbRK")
        self.sbRK.setMinimumSize(QSize(44, 0))
        self.sbRK.setMaximumSize(QSize(50, 16777215))
        self.sbRK.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbRK.setMaximum(4)

        self.horizontalLayout_2.addWidget(self.sbRK)

        self.hlRK4 = QWidget(self.hlReittier)
        self.hlRK4.setObjectName(u"hlRK4")
        self.horizontalLayout = QHBoxLayout(self.hlRK4)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.label_30 = QLabel(self.hlRK4)
        self.label_30.setObjectName(u"label_30")

        self.horizontalLayout.addWidget(self.label_30)

        self.sbRK4TP = QSpinBox(self.hlRK4)
        self.sbRK4TP.setObjectName(u"sbRK4TP")
        self.sbRK4TP.setMinimumSize(QSize(44, 0))
        self.sbRK4TP.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)

        self.horizontalLayout.addWidget(self.sbRK4TP)

        self.sbRK4AT = QSpinBox(self.hlRK4)
        self.sbRK4AT.setObjectName(u"sbRK4AT")
        self.sbRK4AT.setMinimumSize(QSize(44, 0))
        self.sbRK4AT.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)

        self.horizontalLayout.addWidget(self.sbRK4AT)

        self.sbRK4VT = QSpinBox(self.hlRK4)
        self.sbRK4VT.setObjectName(u"sbRK4VT")
        self.sbRK4VT.setMinimumSize(QSize(44, 0))
        self.sbRK4VT.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)

        self.horizontalLayout.addWidget(self.sbRK4VT)


        self.horizontalLayout_2.addWidget(self.hlRK4)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)


        self.verticalLayout_5.addWidget(self.hlReittier)


        self.gridLayout_14.addLayout(self.verticalLayout_5, 1, 1, 1, 1)

        self.teHintergrund = QPlainTextEdit(self.groupBox_2)
        self.teHintergrund.setObjectName(u"teHintergrund")
        self.teHintergrund.setMaximumSize(QSize(16777215, 70))

        self.gridLayout_14.addWidget(self.teHintergrund, 5, 1, 1, 1)

        self.leName = QLineEdit(self.groupBox_2)
        self.leName.setObjectName(u"leName")

        self.gridLayout_14.addWidget(self.leName, 0, 1, 1, 1)

        self.teAussehen = QPlainTextEdit(self.groupBox_2)
        self.teAussehen.setObjectName(u"teAussehen")
        self.teAussehen.setMaximumSize(QSize(16777215, 70))

        self.gridLayout_14.addWidget(self.teAussehen, 6, 1, 1, 1)

        self.label_2 = QLabel(self.groupBox_2)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMaximumSize(QSize(250, 16777215))
        self.label_2.setFont(font)

        self.gridLayout_14.addWidget(self.label_2, 0, 0, 1, 1)

        self.label_17 = QLabel(self.groupBox_2)
        self.label_17.setObjectName(u"label_17")
        self.label_17.setFont(font)
        self.label_17.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.gridLayout_14.addWidget(self.label_17, 6, 0, 1, 1)

        self.leNahrung = QLineEdit(self.groupBox_2)
        self.leNahrung.setObjectName(u"leNahrung")

        self.gridLayout_14.addWidget(self.leNahrung, 3, 1, 1, 1)

        self.labelZucht = QLabel(self.groupBox_2)
        self.labelZucht.setObjectName(u"labelZucht")
        self.labelZucht.setFont(font)

        self.gridLayout_14.addWidget(self.labelZucht, 2, 0, 1, 1)

        self.label_14 = QLabel(self.groupBox_2)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setMinimumSize(QSize(0, 0))
        self.label_14.setMaximumSize(QSize(250, 16777215))
        self.label_14.setFont(font)
        self.label_14.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.gridLayout_14.addWidget(self.label_14, 1, 0, 1, 1)

        self.label = QLabel(self.groupBox_2)
        self.label.setObjectName(u"label")
        self.label.setFont(font)

        self.gridLayout_14.addWidget(self.label, 3, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox_2)

        self.verticalSpacer_3 = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_3)

        self.verticalSpacer_11 = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_11)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_2 = QVBoxLayout(self.tab_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.scrollArea_2 = QScrollArea(self.tab_2)
        self.scrollArea_2.setObjectName(u"scrollArea_2")
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 781, 670))
        self.gridLayout_3 = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(20, 20, 20, 20)
        self.label_23 = QLabel(self.scrollAreaWidgetContents)
        self.label_23.setObjectName(u"label_23")
        self.label_23.setFont(font)

        self.gridLayout_3.addWidget(self.label_23, 11, 0, 1, 1)

        self.verticalSpacer_7 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_3.addItem(self.verticalSpacer_7, 10, 0, 1, 1)

        self.label_3 = QLabel(self.scrollAreaWidgetContents)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font)

        self.gridLayout_3.addWidget(self.label_3, 5, 0, 1, 1)

        self.groupBox_4 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.gridLayout_5 = QGridLayout(self.groupBox_4)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setContentsMargins(20, 20, 20, 20)
        self.label_6 = QLabel(self.groupBox_4)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_6, 1, 9, 1, 1)

        self.sbMU = QSpinBox(self.groupBox_4)
        self.sbMU.setObjectName(u"sbMU")
        self.sbMU.setMaximumSize(QSize(50, 16777215))
        self.sbMU.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbMU.setMinimum(-99)

        self.gridLayout_5.addWidget(self.sbMU, 1, 3, 1, 1)

        self.label_25 = QLabel(self.groupBox_4)
        self.label_25.setObjectName(u"label_25")
        self.label_25.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_25, 4, 2, 1, 1)

        self.sbRS = QSpinBox(self.groupBox_4)
        self.sbRS.setObjectName(u"sbRS")
        self.sbRS.setMaximumSize(QSize(50, 16777215))
        self.sbRS.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbRS.setMinimum(0)
        self.sbRS.setMaximum(99)

        self.gridLayout_5.addWidget(self.sbRS, 4, 16, 1, 1)

        self.label_19 = QLabel(self.groupBox_4)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_19, 4, 13, 1, 1)

        self.sbWS = QSpinBox(self.groupBox_4)
        self.sbWS.setObjectName(u"sbWS")
        self.sbWS.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbWS.setMinimum(-99)

        self.gridLayout_5.addWidget(self.sbWS, 4, 5, 1, 1)

        self.sbFF = QSpinBox(self.groupBox_4)
        self.sbFF.setObjectName(u"sbFF")
        self.sbFF.setMaximumSize(QSize(50, 16777215))
        self.sbFF.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbFF.setMinimum(-99)

        self.gridLayout_5.addWidget(self.sbFF, 1, 16, 1, 1)

        self.sbKO = QSpinBox(self.groupBox_4)
        self.sbKO.setObjectName(u"sbKO")
        self.sbKO.setMinimumSize(QSize(0, 0))
        self.sbKO.setMaximumSize(QSize(50, 16777215))
        self.sbKO.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbKO.setMinimum(-99)

        self.gridLayout_5.addWidget(self.sbKO, 1, 1, 1, 1)

        self.sbGE = QSpinBox(self.groupBox_4)
        self.sbGE.setObjectName(u"sbGE")
        self.sbGE.setMaximumSize(QSize(50, 16777215))
        self.sbGE.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbGE.setMinimum(-99)

        self.gridLayout_5.addWidget(self.sbGE, 1, 5, 1, 1)

        self.sbBE = QSpinBox(self.groupBox_4)
        self.sbBE.setObjectName(u"sbBE")
        self.sbBE.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)

        self.gridLayout_5.addWidget(self.sbBE, 4, 17, 1, 1)

        self.sbKK = QSpinBox(self.groupBox_4)
        self.sbKK.setObjectName(u"sbKK")
        self.sbKK.setMaximumSize(QSize(50, 16777215))
        self.sbKK.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbKK.setMinimum(-99)

        self.gridLayout_5.addWidget(self.sbKK, 1, 7, 1, 1)

        self.sbKL = QSpinBox(self.groupBox_4)
        self.sbKL.setObjectName(u"sbKL")
        self.sbKL.setMaximumSize(QSize(50, 16777215))
        self.sbKL.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbKL.setMinimum(-99)

        self.gridLayout_5.addWidget(self.sbKL, 1, 12, 1, 1)

        self.verticalSpacer_8 = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_5.addItem(self.verticalSpacer_8, 2, 1, 1, 1)

        self.label_12 = QLabel(self.groupBox_4)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_12, 1, 11, 1, 1)

        self.label_8 = QLabel(self.groupBox_4)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_8, 1, 2, 1, 1)

        self.label_40 = QLabel(self.groupBox_4)
        self.label_40.setObjectName(u"label_40")
        self.label_40.setFont(font)

        self.gridLayout_5.addWidget(self.label_40, 3, 9, 1, 9)

        self.sbVT = QSpinBox(self.groupBox_4)
        self.sbVT.setObjectName(u"sbVT")
        self.sbVT.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbVT.setMinimum(-99)

        self.gridLayout_5.addWidget(self.sbVT, 4, 14, 1, 1)

        self.label_27 = QLabel(self.groupBox_4)
        self.label_27.setObjectName(u"label_27")
        self.label_27.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_27, 4, 6, 1, 1)

        self.label_5 = QLabel(self.groupBox_4)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_5, 1, 0, 1, 1)

        self.label_16 = QLabel(self.groupBox_4)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_16, 4, 11, 1, 1)

        self.label_41 = QLabel(self.groupBox_4)
        self.label_41.setObjectName(u"label_41")
        self.label_41.setFont(font)

        self.gridLayout_5.addWidget(self.label_41, 0, 0, 1, 17)

        self.sbAT = QSpinBox(self.groupBox_4)
        self.sbAT.setObjectName(u"sbAT")
        self.sbAT.setMaximumSize(QSize(50, 16777215))
        self.sbAT.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbAT.setMinimum(-99)

        self.gridLayout_5.addWidget(self.sbAT, 4, 12, 1, 1)

        self.label_15 = QLabel(self.groupBox_4)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_15, 4, 15, 1, 1)

        self.sbCH = QSpinBox(self.groupBox_4)
        self.sbCH.setObjectName(u"sbCH")
        self.sbCH.setMaximumSize(QSize(50, 16777215))
        self.sbCH.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbCH.setMinimum(-99)

        self.gridLayout_5.addWidget(self.sbCH, 1, 14, 1, 1)

        self.label_9 = QLabel(self.groupBox_4)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_9, 1, 15, 1, 1)

        self.label_11 = QLabel(self.groupBox_4)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_11, 1, 6, 1, 1)

        self.label_10 = QLabel(self.groupBox_4)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_10, 1, 4, 1, 1)

        self.label_13 = QLabel(self.groupBox_4)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_13, 4, 0, 1, 1)

        self.label_24 = QLabel(self.groupBox_4)
        self.label_24.setObjectName(u"label_24")
        self.label_24.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_24, 4, 9, 1, 1)

        self.label_7 = QLabel(self.groupBox_4)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_7, 1, 13, 1, 1)

        self.sbTP = QSpinBox(self.groupBox_4)
        self.sbTP.setObjectName(u"sbTP")
        self.sbTP.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbTP.setMinimum(-99)

        self.gridLayout_5.addWidget(self.sbTP, 4, 10, 1, 1)

        self.sbGS = QSpinBox(self.groupBox_4)
        self.sbGS.setObjectName(u"sbGS")
        self.sbGS.setMaximumSize(QSize(50, 16777215))
        self.sbGS.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbGS.setMinimum(-99)

        self.gridLayout_5.addWidget(self.sbGS, 4, 1, 1, 1)

        self.label_26 = QLabel(self.groupBox_4)
        self.label_26.setObjectName(u"label_26")
        self.label_26.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_5.addWidget(self.label_26, 4, 4, 1, 1)

        self.sbIN = QSpinBox(self.groupBox_4)
        self.sbIN.setObjectName(u"sbIN")
        self.sbIN.setMaximumSize(QSize(50, 16777215))
        self.sbIN.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbIN.setMinimum(-99)

        self.gridLayout_5.addWidget(self.sbIN, 1, 10, 1, 1)

        self.sbMR = QSpinBox(self.groupBox_4)
        self.sbMR.setObjectName(u"sbMR")
        self.sbMR.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbMR.setMinimum(-99)

        self.gridLayout_5.addWidget(self.sbMR, 4, 7, 1, 1)

        self.label_38 = QLabel(self.groupBox_4)
        self.label_38.setObjectName(u"label_38")
        self.label_38.setFont(font)

        self.gridLayout_5.addWidget(self.label_38, 3, 0, 1, 8)

        self.sbINI = QSpinBox(self.groupBox_4)
        self.sbINI.setObjectName(u"sbINI")
        self.sbINI.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbINI.setMinimum(-99)

        self.gridLayout_5.addWidget(self.sbINI, 4, 3, 1, 1)

        self.line = QFrame(self.groupBox_4)
        self.line.setObjectName(u"line")
        self.line.setFrameShadow(QFrame.Shadow.Plain)
        self.line.setFrameShape(QFrame.Shape.VLine)

        self.gridLayout_5.addWidget(self.line, 3, 8, 2, 1)


        self.gridLayout_3.addWidget(self.groupBox_4, 6, 0, 1, 2)

        self.verticalSpacer_6 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_3.addItem(self.verticalSpacer_6, 7, 0, 1, 1)

        self.label_4 = QLabel(self.scrollAreaWidgetContents)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font)

        self.gridLayout_3.addWidget(self.label_4, 8, 0, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer_2, 13, 0, 1, 1)

        self.groupBox_7 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_7.setObjectName(u"groupBox_7")
        self.gridLayout_2 = QGridLayout(self.groupBox_7)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(20, 20, 20, 20)
        self.leVorteil7 = QLineEdit(self.groupBox_7)
        self.leVorteil7.setObjectName(u"leVorteil7")

        self.gridLayout_2.addWidget(self.leVorteil7, 1, 1, 1, 1)

        self.leVorteil3 = QLineEdit(self.groupBox_7)
        self.leVorteil3.setObjectName(u"leVorteil3")

        self.gridLayout_2.addWidget(self.leVorteil3, 2, 0, 1, 1)

        self.leVorteil1 = QLineEdit(self.groupBox_7)
        self.leVorteil1.setObjectName(u"leVorteil1")

        self.gridLayout_2.addWidget(self.leVorteil1, 0, 0, 1, 1)

        self.leVorteil14 = QLineEdit(self.groupBox_7)
        self.leVorteil14.setObjectName(u"leVorteil14")

        self.gridLayout_2.addWidget(self.leVorteil14, 3, 2, 1, 1)

        self.leVorteil2 = QLineEdit(self.groupBox_7)
        self.leVorteil2.setObjectName(u"leVorteil2")

        self.gridLayout_2.addWidget(self.leVorteil2, 1, 0, 1, 1)

        self.leVorteil9 = QLineEdit(self.groupBox_7)
        self.leVorteil9.setObjectName(u"leVorteil9")

        self.gridLayout_2.addWidget(self.leVorteil9, 3, 1, 1, 1)

        self.leVorteil12 = QLineEdit(self.groupBox_7)
        self.leVorteil12.setObjectName(u"leVorteil12")

        self.gridLayout_2.addWidget(self.leVorteil12, 1, 2, 1, 1)

        self.leVorteil13 = QLineEdit(self.groupBox_7)
        self.leVorteil13.setObjectName(u"leVorteil13")

        self.gridLayout_2.addWidget(self.leVorteil13, 2, 2, 1, 1)

        self.leVorteil8 = QLineEdit(self.groupBox_7)
        self.leVorteil8.setObjectName(u"leVorteil8")

        self.gridLayout_2.addWidget(self.leVorteil8, 2, 1, 1, 1)

        self.leVorteil15 = QLineEdit(self.groupBox_7)
        self.leVorteil15.setObjectName(u"leVorteil15")

        self.gridLayout_2.addWidget(self.leVorteil15, 4, 2, 1, 1)

        self.leVorteil4 = QLineEdit(self.groupBox_7)
        self.leVorteil4.setObjectName(u"leVorteil4")

        self.gridLayout_2.addWidget(self.leVorteil4, 3, 0, 1, 1)

        self.leVorteil5 = QLineEdit(self.groupBox_7)
        self.leVorteil5.setObjectName(u"leVorteil5")

        self.gridLayout_2.addWidget(self.leVorteil5, 4, 0, 1, 1)

        self.leVorteil10 = QLineEdit(self.groupBox_7)
        self.leVorteil10.setObjectName(u"leVorteil10")

        self.gridLayout_2.addWidget(self.leVorteil10, 4, 1, 1, 1)

        self.leVorteil11 = QLineEdit(self.groupBox_7)
        self.leVorteil11.setObjectName(u"leVorteil11")

        self.gridLayout_2.addWidget(self.leVorteil11, 0, 2, 1, 1)

        self.leVorteil6 = QLineEdit(self.groupBox_7)
        self.leVorteil6.setObjectName(u"leVorteil6")

        self.gridLayout_2.addWidget(self.leVorteil6, 0, 1, 1, 1)


        self.gridLayout_3.addWidget(self.groupBox_7, 12, 0, 1, 2)

        self.groupBox_6 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.gridLayout = QGridLayout(self.groupBox_6)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(20, 20, 20, 20)
        self.sbTalent2 = QSpinBox(self.groupBox_6)
        self.sbTalent2.setObjectName(u"sbTalent2")
        self.sbTalent2.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbTalent2.setMinimum(-99)

        self.gridLayout.addWidget(self.sbTalent2, 1, 1, 1, 1)

        self.sbTalent3 = QSpinBox(self.groupBox_6)
        self.sbTalent3.setObjectName(u"sbTalent3")
        self.sbTalent3.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbTalent3.setMinimum(-99)

        self.gridLayout.addWidget(self.sbTalent3, 2, 1, 1, 1)

        self.leTalent3 = QLineEdit(self.groupBox_6)
        self.leTalent3.setObjectName(u"leTalent3")

        self.gridLayout.addWidget(self.leTalent3, 2, 0, 1, 1)

        self.leTalent1 = QLineEdit(self.groupBox_6)
        self.leTalent1.setObjectName(u"leTalent1")

        self.gridLayout.addWidget(self.leTalent1, 0, 0, 1, 1)

        self.sbTalent1 = QSpinBox(self.groupBox_6)
        self.sbTalent1.setObjectName(u"sbTalent1")
        self.sbTalent1.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbTalent1.setMinimum(-99)

        self.gridLayout.addWidget(self.sbTalent1, 0, 1, 1, 1)

        self.leTalent4 = QLineEdit(self.groupBox_6)
        self.leTalent4.setObjectName(u"leTalent4")

        self.gridLayout.addWidget(self.leTalent4, 0, 2, 1, 1)

        self.leTalent2 = QLineEdit(self.groupBox_6)
        self.leTalent2.setObjectName(u"leTalent2")

        self.gridLayout.addWidget(self.leTalent2, 1, 0, 1, 1)

        self.sbTalent4 = QSpinBox(self.groupBox_6)
        self.sbTalent4.setObjectName(u"sbTalent4")
        self.sbTalent4.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbTalent4.setMinimum(-99)

        self.gridLayout.addWidget(self.sbTalent4, 0, 3, 1, 1)

        self.leTalent5 = QLineEdit(self.groupBox_6)
        self.leTalent5.setObjectName(u"leTalent5")

        self.gridLayout.addWidget(self.leTalent5, 1, 2, 1, 1)

        self.sbTalent5 = QSpinBox(self.groupBox_6)
        self.sbTalent5.setObjectName(u"sbTalent5")
        self.sbTalent5.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbTalent5.setMinimum(-99)

        self.gridLayout.addWidget(self.sbTalent5, 1, 3, 1, 1)

        self.leTalent6 = QLineEdit(self.groupBox_6)
        self.leTalent6.setObjectName(u"leTalent6")

        self.gridLayout.addWidget(self.leTalent6, 2, 2, 1, 1)

        self.sbTalent6 = QSpinBox(self.groupBox_6)
        self.sbTalent6.setObjectName(u"sbTalent6")
        self.sbTalent6.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbTalent6.setMinimum(-99)

        self.gridLayout.addWidget(self.sbTalent6, 2, 3, 1, 1)

        self.leTalent7 = QLineEdit(self.groupBox_6)
        self.leTalent7.setObjectName(u"leTalent7")

        self.gridLayout.addWidget(self.leTalent7, 0, 4, 1, 1)

        self.sbTalent7 = QSpinBox(self.groupBox_6)
        self.sbTalent7.setObjectName(u"sbTalent7")
        self.sbTalent7.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbTalent7.setMinimum(-99)

        self.gridLayout.addWidget(self.sbTalent7, 0, 5, 1, 1)

        self.leTalent8 = QLineEdit(self.groupBox_6)
        self.leTalent8.setObjectName(u"leTalent8")

        self.gridLayout.addWidget(self.leTalent8, 1, 4, 1, 1)

        self.sbTalent8 = QSpinBox(self.groupBox_6)
        self.sbTalent8.setObjectName(u"sbTalent8")
        self.sbTalent8.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbTalent8.setMinimum(-99)

        self.gridLayout.addWidget(self.sbTalent8, 1, 5, 1, 1)

        self.leTalent9 = QLineEdit(self.groupBox_6)
        self.leTalent9.setObjectName(u"leTalent9")

        self.gridLayout.addWidget(self.leTalent9, 2, 4, 1, 1)

        self.sbTalent9 = QSpinBox(self.groupBox_6)
        self.sbTalent9.setObjectName(u"sbTalent9")
        self.sbTalent9.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbTalent9.setMinimum(-99)

        self.gridLayout.addWidget(self.sbTalent9, 2, 5, 1, 1)


        self.gridLayout_3.addWidget(self.groupBox_6, 9, 0, 1, 2)

        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_2.addWidget(self.scrollArea_2)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.verticalLayout_3 = QVBoxLayout(self.tab_3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.scrollArea_3 = QScrollArea(self.tab_3)
        self.scrollArea_3.setObjectName(u"scrollArea_3")
        self.scrollArea_3.setWidgetResizable(True)
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName(u"scrollAreaWidgetContents_2")
        self.scrollAreaWidgetContents_2.setGeometry(QRect(0, 0, 781, 619))
        self.gridLayout_8 = QGridLayout(self.scrollAreaWidgetContents_2)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.gridLayout_8.setContentsMargins(20, 20, 20, 20)
        self.groupBox_5 = QGroupBox(self.scrollAreaWidgetContents_2)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.gridLayout_7 = QGridLayout(self.groupBox_5)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_7.setContentsMargins(20, 20, 20, 20)
        self.label_34 = QLabel(self.groupBox_5)
        self.label_34.setObjectName(u"label_34")

        self.gridLayout_7.addWidget(self.label_34, 1, 0, 1, 1)

        self.checkEditierbar = QCheckBox(self.groupBox_5)
        self.checkEditierbar.setObjectName(u"checkEditierbar")

        self.gridLayout_7.addWidget(self.checkEditierbar, 5, 1, 1, 1)

        self.checkRegeln = QCheckBox(self.groupBox_5)
        self.checkRegeln.setObjectName(u"checkRegeln")
        self.checkRegeln.setChecked(True)

        self.gridLayout_7.addWidget(self.checkRegeln, 2, 1, 1, 1)

        self.label_21 = QLabel(self.groupBox_5)
        self.label_21.setObjectName(u"label_21")

        self.gridLayout_7.addWidget(self.label_21, 2, 0, 1, 1)

        self.label_20 = QLabel(self.groupBox_5)
        self.label_20.setObjectName(u"label_20")

        self.gridLayout_7.addWidget(self.label_20, 4, 0, 1, 1)

        self.sbRegelnGroesse = QSpinBox(self.groupBox_5)
        self.sbRegelnGroesse.setObjectName(u"sbRegelnGroesse")
        self.sbRegelnGroesse.setMinimumSize(QSize(60, 0))
        self.sbRegelnGroesse.setMaximumSize(QSize(60, 16777215))
        self.sbRegelnGroesse.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbRegelnGroesse.setMinimum(6)
        self.sbRegelnGroesse.setMaximum(18)
        self.sbRegelnGroesse.setValue(8)

        self.gridLayout_7.addWidget(self.sbRegelnGroesse, 4, 1, 1, 1)

        self.label_22 = QLabel(self.groupBox_5)
        self.label_22.setObjectName(u"label_22")

        self.gridLayout_7.addWidget(self.label_22, 5, 0, 1, 1)

        self.cbHausregeln = QComboBox(self.groupBox_5)
        self.cbHausregeln.setObjectName(u"cbHausregeln")

        self.gridLayout_7.addWidget(self.cbHausregeln, 1, 1, 1, 1)

        self.verticalSpacer_9 = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_7.addItem(self.verticalSpacer_9, 6, 0, 1, 1)


        self.gridLayout_8.addWidget(self.groupBox_5, 4, 1, 1, 1)

        self.verticalSpacer_5 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_8.addItem(self.verticalSpacer_5, 2, 0, 1, 1)

        self.label_37 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_37.setObjectName(u"label_37")
        self.label_37.setFont(font)

        self.gridLayout_8.addWidget(self.label_37, 0, 0, 1, 2)

        self.label_36 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_36.setObjectName(u"label_36")
        self.label_36.setFont(font)

        self.gridLayout_8.addWidget(self.label_36, 3, 0, 1, 1)

        self.label_35 = QLabel(self.scrollAreaWidgetContents_2)
        self.label_35.setObjectName(u"label_35")
        self.label_35.setFont(font)

        self.gridLayout_8.addWidget(self.label_35, 3, 1, 1, 1)

        self.groupBox_10 = QGroupBox(self.scrollAreaWidgetContents_2)
        self.groupBox_10.setObjectName(u"groupBox_10")
        self.verticalLayout_9 = QVBoxLayout(self.groupBox_10)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(20, 20, 20, 20)
        self.labelEPInfo = QLabel(self.groupBox_10)
        self.labelEPInfo.setObjectName(u"labelEPInfo")
        self.labelEPInfo.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.labelEPInfo.setWordWrap(True)

        self.verticalLayout_9.addWidget(self.labelEPInfo)

        self.verticalSpacer_10 = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_9.addItem(self.verticalSpacer_10)


        self.gridLayout_8.addWidget(self.groupBox_10, 4, 0, 1, 1)

        self.gbInventar = QGroupBox(self.scrollAreaWidgetContents_2)
        self.gbInventar.setObjectName(u"gbInventar")
        self.gbInventar.setFlat(False)
        self.gridLayout_10 = QGridLayout(self.gbInventar)
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.gridLayout_10.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.gridLayout_10.setContentsMargins(20, 20, 20, 20)
        self.leAusruestung10 = QLineEdit(self.gbInventar)
        self.leAusruestung10.setObjectName(u"leAusruestung10")

        self.gridLayout_10.addWidget(self.leAusruestung10, 10, 0, 1, 1)

        self.leAusruestung4 = QLineEdit(self.gbInventar)
        self.leAusruestung4.setObjectName(u"leAusruestung4")

        self.gridLayout_10.addWidget(self.leAusruestung4, 4, 0, 1, 1)

        self.leAusruestung5 = QLineEdit(self.gbInventar)
        self.leAusruestung5.setObjectName(u"leAusruestung5")

        self.gridLayout_10.addWidget(self.leAusruestung5, 5, 0, 1, 1)

        self.leAusruestung1 = QLineEdit(self.gbInventar)
        self.leAusruestung1.setObjectName(u"leAusruestung1")
        self.leAusruestung1.setCursor(QCursor(Qt.CursorShape.IBeamCursor))

        self.gridLayout_10.addWidget(self.leAusruestung1, 1, 0, 1, 1)

        self.leAusruestung8 = QLineEdit(self.gbInventar)
        self.leAusruestung8.setObjectName(u"leAusruestung8")

        self.gridLayout_10.addWidget(self.leAusruestung8, 8, 0, 1, 1)

        self.leAusruestung17 = QLineEdit(self.gbInventar)
        self.leAusruestung17.setObjectName(u"leAusruestung17")

        self.gridLayout_10.addWidget(self.leAusruestung17, 7, 1, 1, 1)

        self.leAusruestung19 = QLineEdit(self.gbInventar)
        self.leAusruestung19.setObjectName(u"leAusruestung19")

        self.gridLayout_10.addWidget(self.leAusruestung19, 9, 1, 1, 1)

        self.leAusruestung7 = QLineEdit(self.gbInventar)
        self.leAusruestung7.setObjectName(u"leAusruestung7")

        self.gridLayout_10.addWidget(self.leAusruestung7, 7, 0, 1, 1)

        self.leAusruestung2 = QLineEdit(self.gbInventar)
        self.leAusruestung2.setObjectName(u"leAusruestung2")

        self.gridLayout_10.addWidget(self.leAusruestung2, 2, 0, 1, 1)

        self.leAusruestung13 = QLineEdit(self.gbInventar)
        self.leAusruestung13.setObjectName(u"leAusruestung13")

        self.gridLayout_10.addWidget(self.leAusruestung13, 3, 1, 1, 1)

        self.leAusruestung3 = QLineEdit(self.gbInventar)
        self.leAusruestung3.setObjectName(u"leAusruestung3")

        self.gridLayout_10.addWidget(self.leAusruestung3, 3, 0, 1, 1)

        self.leAusruestung20 = QLineEdit(self.gbInventar)
        self.leAusruestung20.setObjectName(u"leAusruestung20")

        self.gridLayout_10.addWidget(self.leAusruestung20, 10, 1, 1, 1)

        self.leAusruestung18 = QLineEdit(self.gbInventar)
        self.leAusruestung18.setObjectName(u"leAusruestung18")

        self.gridLayout_10.addWidget(self.leAusruestung18, 8, 1, 1, 1)

        self.leAusruestung15 = QLineEdit(self.gbInventar)
        self.leAusruestung15.setObjectName(u"leAusruestung15")

        self.gridLayout_10.addWidget(self.leAusruestung15, 5, 1, 1, 1)

        self.leAusruestung9 = QLineEdit(self.gbInventar)
        self.leAusruestung9.setObjectName(u"leAusruestung9")

        self.gridLayout_10.addWidget(self.leAusruestung9, 9, 0, 1, 1)

        self.leAusruestung12 = QLineEdit(self.gbInventar)
        self.leAusruestung12.setObjectName(u"leAusruestung12")

        self.gridLayout_10.addWidget(self.leAusruestung12, 2, 1, 1, 1)

        self.leAusruestung14 = QLineEdit(self.gbInventar)
        self.leAusruestung14.setObjectName(u"leAusruestung14")

        self.gridLayout_10.addWidget(self.leAusruestung14, 4, 1, 1, 1)

        self.leAusruestung6 = QLineEdit(self.gbInventar)
        self.leAusruestung6.setObjectName(u"leAusruestung6")

        self.gridLayout_10.addWidget(self.leAusruestung6, 6, 0, 1, 1)

        self.leAusruestung11 = QLineEdit(self.gbInventar)
        self.leAusruestung11.setObjectName(u"leAusruestung11")

        self.gridLayout_10.addWidget(self.leAusruestung11, 1, 1, 1, 1)

        self.leAusruestung16 = QLineEdit(self.gbInventar)
        self.leAusruestung16.setObjectName(u"leAusruestung16")

        self.gridLayout_10.addWidget(self.leAusruestung16, 6, 1, 1, 1)


        self.gridLayout_8.addWidget(self.gbInventar, 1, 0, 1, 2)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_8.addItem(self.verticalSpacer, 5, 1, 1, 1)

        self.scrollArea_3.setWidget(self.scrollAreaWidgetContents_2)

        self.verticalLayout_3.addWidget(self.scrollArea_3)

        self.tabWidget.addTab(self.tab_3, "")
        self.splitter.addWidget(self.tabWidget)
        self.scrollArea = QScrollArea(self.splitter)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_3 = QWidget()
        self.scrollAreaWidgetContents_3.setObjectName(u"scrollAreaWidgetContents_3")
        self.scrollAreaWidgetContents_3.setGeometry(QRect(0, 0, 200, 454))
        self.verticalLayout_13 = QVBoxLayout(self.scrollAreaWidgetContents_3)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.verticalLayout_13.setContentsMargins(0, 0, -1, 0)
        self.groupBox_3 = QGroupBox(self.scrollAreaWidgetContents_3)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.gridLayout_6 = QGridLayout(self.groupBox_3)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.buttonLoadImage = QPushButton(self.groupBox_3)
        self.buttonLoadImage.setObjectName(u"buttonLoadImage")

        self.gridLayout_6.addWidget(self.buttonLoadImage, 2, 0, 1, 1)

        self.buttonDeleteImage = QPushButton(self.groupBox_3)
        self.buttonDeleteImage.setObjectName(u"buttonDeleteImage")

        self.gridLayout_6.addWidget(self.buttonDeleteImage, 2, 1, 1, 1)

        self.labelImage = QLabel(self.groupBox_3)
        self.labelImage.setObjectName(u"labelImage")
        self.labelImage.setMinimumSize(QSize(0, 200))
        self.labelImage.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_6.addWidget(self.labelImage, 1, 0, 1, 2)


        self.verticalLayout_13.addWidget(self.groupBox_3)

        self.groupBox = QGroupBox(self.scrollAreaWidgetContents_3)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_8 = QVBoxLayout(self.groupBox)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.lblWerte = QLabel(self.groupBox)
        self.lblWerte.setObjectName(u"lblWerte")
        sizePolicy.setHeightForWidth(self.lblWerte.sizePolicy().hasHeightForWidth())
        self.lblWerte.setSizePolicy(sizePolicy)
        self.lblWerte.setTextFormat(Qt.TextFormat.RichText)
        self.lblWerte.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.lblWerte.setWordWrap(True)

        self.verticalLayout_8.addWidget(self.lblWerte)

        self.verticalSpacer_4 = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_8.addItem(self.verticalSpacer_4)


        self.verticalLayout_13.addWidget(self.groupBox)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents_3)
        self.splitter.addWidget(self.scrollArea)

        self.verticalLayout_14.addWidget(self.splitter)

        self.layoutBottomBar = QHBoxLayout()
        self.layoutBottomBar.setObjectName(u"layoutBottomBar")
        self.label_31 = QLabel(formMain)
        self.label_31.setObjectName(u"label_31")
        self.label_31.setFont(font)

        self.layoutBottomBar.addWidget(self.label_31)

        self.sbEP = QSpinBox(formMain)
        self.sbEP.setObjectName(u"sbEP")
        self.sbEP.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sbEP.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.sbEP.setMaximum(100000)

        self.layoutBottomBar.addWidget(self.sbEP)

        self.label_32 = QLabel(formMain)
        self.label_32.setObjectName(u"label_32")
        self.label_32.setFont(font)

        self.layoutBottomBar.addWidget(self.label_32)

        self.sbSpent = QSpinBox(formMain)
        self.sbSpent.setObjectName(u"sbSpent")
        self.sbSpent.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sbSpent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sbSpent.setReadOnly(True)
        self.sbSpent.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.sbSpent.setMinimum(-100000)
        self.sbSpent.setMaximum(100000)

        self.layoutBottomBar.addWidget(self.sbSpent)

        self.label_33 = QLabel(formMain)
        self.label_33.setObjectName(u"label_33")
        self.label_33.setFont(font)

        self.layoutBottomBar.addWidget(self.label_33)

        self.sbRemaining = QSpinBox(formMain)
        self.sbRemaining.setObjectName(u"sbRemaining")
        self.sbRemaining.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sbRemaining.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sbRemaining.setReadOnly(True)
        self.sbRemaining.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.sbRemaining.setMinimum(-100000)
        self.sbRemaining.setMaximum(100000)

        self.layoutBottomBar.addWidget(self.sbRemaining)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layoutBottomBar.addItem(self.horizontalSpacer_2)


        self.verticalLayout_14.addLayout(self.layoutBottomBar)

        QWidget.setTabOrder(self.cbTier, self.buttonLoadImage)
        QWidget.setTabOrder(self.buttonLoadImage, self.buttonDeleteImage)
        QWidget.setTabOrder(self.buttonDeleteImage, self.scrollArea)
        QWidget.setTabOrder(self.scrollArea, self.leAusruestung1)
        QWidget.setTabOrder(self.leAusruestung1, self.leAusruestung2)
        QWidget.setTabOrder(self.leAusruestung2, self.leAusruestung3)
        QWidget.setTabOrder(self.leAusruestung3, self.leAusruestung4)
        QWidget.setTabOrder(self.leAusruestung4, self.leAusruestung5)
        QWidget.setTabOrder(self.leAusruestung5, self.leAusruestung6)
        QWidget.setTabOrder(self.leAusruestung6, self.leAusruestung7)
        QWidget.setTabOrder(self.leAusruestung7, self.leAusruestung8)
        QWidget.setTabOrder(self.leAusruestung8, self.leAusruestung9)
        QWidget.setTabOrder(self.leAusruestung9, self.leAusruestung10)
        QWidget.setTabOrder(self.leAusruestung10, self.leAusruestung11)
        QWidget.setTabOrder(self.leAusruestung11, self.leAusruestung12)
        QWidget.setTabOrder(self.leAusruestung12, self.leAusruestung13)
        QWidget.setTabOrder(self.leAusruestung13, self.leAusruestung14)
        QWidget.setTabOrder(self.leAusruestung14, self.leAusruestung15)
        QWidget.setTabOrder(self.leAusruestung15, self.leAusruestung16)
        QWidget.setTabOrder(self.leAusruestung16, self.leAusruestung17)
        QWidget.setTabOrder(self.leAusruestung17, self.leAusruestung18)
        QWidget.setTabOrder(self.leAusruestung18, self.leAusruestung19)
        QWidget.setTabOrder(self.leAusruestung19, self.leAusruestung20)
        QWidget.setTabOrder(self.leAusruestung20, self.tabWidget)

        self.retranslateUi(formMain)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(formMain)
    # setupUi

    def retranslateUi(self, formMain):
        formMain.setWindowTitle(QCoreApplication.translate("formMain", u"Sephrasto - Tierbegleiter erstellen", None))
        self.tabWidget.setProperty(u"class", QCoreApplication.translate("formMain", u"tabNavigation", None))
        self.groupBox_2.setTitle("")
        self.label_18.setText(QCoreApplication.translate("formMain", u"Hintergrund", None))
        self.label_18.setProperty(u"class", QCoreApplication.translate("formMain", u"h4", None))
        self.lblTier.setText("")
        self.lblReiten.setText(QCoreApplication.translate("formMain", u"Reiten-PW - BE", None))
#if QT_CONFIG(tooltip)
        self.sbReiten.setToolTip(QCoreApplication.translate("formMain", u"Trage hier deinen Reiten-PW abz\u00fcglich BE ein. Nicht vergessen - mit Reiterkampf II sinkt die BE um 1!", None))
#endif // QT_CONFIG(tooltip)
        self.lblRK.setText(QCoreApplication.translate("formMain", u"Reiterkampfstil-Stufe", None))
        self.label_30.setText(QCoreApplication.translate("formMain", u"Stufe IV Bonus TP/AT/VT", None))
        self.label_2.setText(QCoreApplication.translate("formMain", u"Name", None))
        self.label_2.setProperty(u"class", QCoreApplication.translate("formMain", u"h4", None))
        self.label_17.setText(QCoreApplication.translate("formMain", u"Aussehen", None))
        self.label_17.setProperty(u"class", QCoreApplication.translate("formMain", u"h4", None))
        self.labelZucht.setText(QCoreApplication.translate("formMain", u"Zucht", None))
        self.label_14.setText(QCoreApplication.translate("formMain", u"Tier", None))
        self.label_14.setProperty(u"class", QCoreApplication.translate("formMain", u"h4", None))
        self.label.setText(QCoreApplication.translate("formMain", u"Nahrung", None))
        self.label.setProperty(u"class", QCoreApplication.translate("formMain", u"h4", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("formMain", u"Beschreibung", None))
        self.scrollArea_2.setProperty(u"class", QCoreApplication.translate("formMain", u"transparent", None))
        self.label_23.setText(QCoreApplication.translate("formMain", u"Vorteile", None))
        self.label_23.setProperty(u"class", QCoreApplication.translate("formMain", u"h2", None))
        self.label_3.setText(QCoreApplication.translate("formMain", u"Werte", None))
        self.label_3.setProperty(u"class", QCoreApplication.translate("formMain", u"h2", None))
        self.groupBox_4.setTitle("")
        self.label_6.setText(QCoreApplication.translate("formMain", u"IN", None))
        self.label_25.setText(QCoreApplication.translate("formMain", u"INI", None))
        self.label_19.setText(QCoreApplication.translate("formMain", u"VT", None))
        self.label_12.setText(QCoreApplication.translate("formMain", u"KL", None))
        self.label_8.setText(QCoreApplication.translate("formMain", u"MU", None))
        self.label_40.setText(QCoreApplication.translate("formMain", u"Kampfwerte", None))
        self.label_40.setProperty(u"class", QCoreApplication.translate("formMain", u"h4", None))
        self.label_27.setText(QCoreApplication.translate("formMain", u"MR", None))
        self.label_5.setText(QCoreApplication.translate("formMain", u"KO", None))
        self.label_16.setText(QCoreApplication.translate("formMain", u"AT", None))
        self.label_41.setText(QCoreApplication.translate("formMain", u"Attribute", None))
        self.label_41.setProperty(u"class", QCoreApplication.translate("formMain", u"h4", None))
        self.label_15.setText(QCoreApplication.translate("formMain", u"RS/BE", None))
        self.label_9.setText(QCoreApplication.translate("formMain", u"FF", None))
        self.label_11.setText(QCoreApplication.translate("formMain", u"KK", None))
        self.label_10.setText(QCoreApplication.translate("formMain", u"GE", None))
        self.label_13.setText(QCoreApplication.translate("formMain", u"GS", None))
        self.label_24.setText(QCoreApplication.translate("formMain", u"TP", None))
        self.label_7.setText(QCoreApplication.translate("formMain", u"CH", None))
        self.label_26.setText(QCoreApplication.translate("formMain", u"WS", None))
        self.label_38.setText(QCoreApplication.translate("formMain", u"Abgeleitete Werte", None))
        self.label_38.setProperty(u"class", QCoreApplication.translate("formMain", u"h4", None))
        self.label_4.setText(QCoreApplication.translate("formMain", u"Talente", None))
        self.label_4.setProperty(u"class", QCoreApplication.translate("formMain", u"h2", None))
        self.groupBox_7.setTitle("")
        self.groupBox_6.setTitle("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("formMain", u"Werte anpassen", None))
        self.scrollArea_3.setProperty(u"class", QCoreApplication.translate("formMain", u"transparent", None))
        self.groupBox_5.setTitle("")
        self.label_34.setText(QCoreApplication.translate("formMain", u"Hausregeln", None))
        self.checkEditierbar.setText("")
        self.checkRegeln.setText("")
        self.label_21.setText(QCoreApplication.translate("formMain", u"Relevante Regeln anh\u00e4ngen", None))
        self.label_20.setText(QCoreApplication.translate("formMain", u"Regelschriftgr\u00f6\u00dfe", None))
        self.label_22.setText(QCoreApplication.translate("formMain", u"Formularfelder editierbar", None))
        self.label_37.setText(QCoreApplication.translate("formMain", u"Ausr\u00fcstung", None))
        self.label_37.setProperty(u"class", QCoreApplication.translate("formMain", u"h2", None))
        self.label_36.setText(QCoreApplication.translate("formMain", u"Erfahrungspunkte", None))
        self.label_36.setProperty(u"class", QCoreApplication.translate("formMain", u"h2", None))
        self.label_35.setText(QCoreApplication.translate("formMain", u"Einstellungen", None))
        self.label_35.setProperty(u"class", QCoreApplication.translate("formMain", u"h2", None))
        self.groupBox_10.setTitle("")
        self.labelEPInfo.setText("")
        self.gbInventar.setTitle("")
        self.leAusruestung1.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("formMain", u"Ausr\u00fcstung && Info", None))
        self.scrollArea.setProperty(u"class", QCoreApplication.translate("formMain", u"transparent", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("formMain", u"Bild", None))
        self.buttonLoadImage.setText(QCoreApplication.translate("formMain", u"Bild Laden", None))
        self.buttonDeleteImage.setText(QCoreApplication.translate("formMain", u"Bild L\u00f6schen", None))
        self.labelImage.setText(QCoreApplication.translate("formMain", u"Bild-Aufl\u00f6sung: 193x254 px\n"
"(wird automatisch angepasst)", None))
        self.groupBox.setTitle(QCoreApplication.translate("formMain", u"Vorschau", None))
        self.lblWerte.setText(QCoreApplication.translate("formMain", u"<html><head/><body><p><br/></p></body></html>", None))
        self.label_31.setText(QCoreApplication.translate("formMain", u"    Total:    ", None))
        self.label_31.setProperty(u"class", QCoreApplication.translate("formMain", u"h4", None))
        self.sbEP.setSuffix(QCoreApplication.translate("formMain", u" EP", None))
        self.label_32.setText(QCoreApplication.translate("formMain", u"    Ausgegeben:    ", None))
        self.label_32.setProperty(u"class", QCoreApplication.translate("formMain", u"h4", None))
        self.sbSpent.setSuffix(QCoreApplication.translate("formMain", u" EP", None))
        self.label_33.setText(QCoreApplication.translate("formMain", u"    Verbleibend:    ", None))
        self.label_33.setProperty(u"class", QCoreApplication.translate("formMain", u"h4", None))
        self.sbRemaining.setSuffix(QCoreApplication.translate("formMain", u" EP", None))
    # retranslateUi

