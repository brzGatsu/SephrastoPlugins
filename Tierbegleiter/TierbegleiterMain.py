# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'TierbegleiterMain.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QComboBox,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLayout, QLineEdit, QPlainTextEdit,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QSpinBox, QTabWidget, QVBoxLayout, QWidget)

class Ui_formMain(object):
    def setupUi(self, formMain):
        if not formMain.objectName():
            formMain.setObjectName(u"formMain")
        formMain.setWindowModality(Qt.ApplicationModal)
        formMain.resize(1312, 810)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(formMain.sizePolicy().hasHeightForWidth())
        formMain.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(formMain)
        self.gridLayout.setObjectName(u"gridLayout")
        self.scrollArea = QScrollArea(formMain)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 1288, 749))
        self.gridLayout_4 = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.tabWidget = QTabWidget(self.scrollAreaWidgetContents)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_10 = QVBoxLayout(self.tab)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(20, 20, 20, 20)
        self.gridLayout_5 = QGridLayout()
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.groupBox_2 = QGroupBox(self.tab)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout_9 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(20, 20, 20, 20)
        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.teHintergrund = QPlainTextEdit(self.groupBox_2)
        self.teHintergrund.setObjectName(u"teHintergrund")
        self.teHintergrund.setMaximumSize(QSize(16777215, 70))

        self.gridLayout_2.addWidget(self.teHintergrund, 3, 1, 1, 1)

        self.teAussehen = QPlainTextEdit(self.groupBox_2)
        self.teAussehen.setObjectName(u"teAussehen")
        self.teAussehen.setMaximumSize(QSize(16777215, 70))

        self.gridLayout_2.addWidget(self.teAussehen, 5, 1, 1, 1)

        self.leName = QLineEdit(self.groupBox_2)
        self.leName.setObjectName(u"leName")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.leName.sizePolicy().hasHeightForWidth())
        self.leName.setSizePolicy(sizePolicy1)

        self.gridLayout_2.addWidget(self.leName, 0, 1, 1, 1)

        self.label_18 = QLabel(self.groupBox_2)
        self.label_18.setObjectName(u"label_18")
        font = QFont()
        font.setBold(True)
        self.label_18.setFont(font)
        self.label_18.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout_2.addWidget(self.label_18, 3, 0, 1, 1)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.sbCH = QSpinBox(self.groupBox_2)
        self.sbCH.setObjectName(u"sbCH")
        self.sbCH.setMaximumSize(QSize(50, 16777215))
        self.sbCH.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.sbCH.setMinimum(-99)

        self.gridLayout_3.addWidget(self.sbCH, 1, 5, 1, 1)

        self.sbGS = QSpinBox(self.groupBox_2)
        self.sbGS.setObjectName(u"sbGS")
        self.sbGS.setMaximumSize(QSize(50, 16777215))
        self.sbGS.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.sbGS.setMinimum(-99)

        self.gridLayout_3.addWidget(self.sbGS, 2, 3, 1, 1)

        self.label_11 = QLabel(self.groupBox_2)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_11, 0, 6, 1, 1)

        self.sbRS = QSpinBox(self.groupBox_2)
        self.sbRS.setObjectName(u"sbRS")
        self.sbRS.setMaximumSize(QSize(50, 16777215))
        self.sbRS.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.sbRS.setMinimum(-99)

        self.gridLayout_3.addWidget(self.sbRS, 2, 5, 1, 1)

        self.label_5 = QLabel(self.groupBox_2)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_5, 0, 0, 1, 1)

        self.label_13 = QLabel(self.groupBox_2)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_13, 2, 2, 1, 1)

        self.label_7 = QLabel(self.groupBox_2)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_7, 1, 4, 1, 1)

        self.sbIN = QSpinBox(self.groupBox_2)
        self.sbIN.setObjectName(u"sbIN")
        self.sbIN.setMaximumSize(QSize(50, 16777215))
        self.sbIN.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.sbIN.setMinimum(-99)

        self.gridLayout_3.addWidget(self.sbIN, 1, 1, 1, 1)

        self.sbMU = QSpinBox(self.groupBox_2)
        self.sbMU.setObjectName(u"sbMU")
        self.sbMU.setMaximumSize(QSize(50, 16777215))
        self.sbMU.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.sbMU.setMinimum(-99)

        self.gridLayout_3.addWidget(self.sbMU, 0, 3, 1, 1)

        self.sbKL = QSpinBox(self.groupBox_2)
        self.sbKL.setObjectName(u"sbKL")
        self.sbKL.setMaximumSize(QSize(50, 16777215))
        self.sbKL.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.sbKL.setMinimum(-99)

        self.gridLayout_3.addWidget(self.sbKL, 1, 3, 1, 1)

        self.sbFF = QSpinBox(self.groupBox_2)
        self.sbFF.setObjectName(u"sbFF")
        self.sbFF.setMaximumSize(QSize(50, 16777215))
        self.sbFF.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.sbFF.setMinimum(-99)

        self.gridLayout_3.addWidget(self.sbFF, 1, 7, 1, 1)

        self.label_6 = QLabel(self.groupBox_2)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_6, 1, 0, 1, 1)

        self.label_9 = QLabel(self.groupBox_2)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_9, 1, 6, 1, 1)

        self.label_8 = QLabel(self.groupBox_2)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_8, 0, 2, 1, 1)

        self.label_15 = QLabel(self.groupBox_2)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_15, 2, 4, 1, 1)

        self.label_16 = QLabel(self.groupBox_2)
        self.label_16.setObjectName(u"label_16")
        self.label_16.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_16, 2, 0, 1, 1)

        self.label_12 = QLabel(self.groupBox_2)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_12, 1, 2, 1, 1)

        self.sbGE = QSpinBox(self.groupBox_2)
        self.sbGE.setObjectName(u"sbGE")
        self.sbGE.setMaximumSize(QSize(50, 16777215))
        self.sbGE.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.sbGE.setMinimum(-99)

        self.gridLayout_3.addWidget(self.sbGE, 0, 5, 1, 1)

        self.label_10 = QLabel(self.groupBox_2)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_3.addWidget(self.label_10, 0, 4, 1, 1)

        self.sbKampfwerte = QSpinBox(self.groupBox_2)
        self.sbKampfwerte.setObjectName(u"sbKampfwerte")
        self.sbKampfwerte.setMaximumSize(QSize(50, 16777215))
        self.sbKampfwerte.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.sbKampfwerte.setMinimum(-99)

        self.gridLayout_3.addWidget(self.sbKampfwerte, 2, 1, 1, 1)

        self.sbKO = QSpinBox(self.groupBox_2)
        self.sbKO.setObjectName(u"sbKO")
        self.sbKO.setMinimumSize(QSize(0, 0))
        self.sbKO.setMaximumSize(QSize(50, 16777215))
        self.sbKO.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.sbKO.setMinimum(-99)

        self.gridLayout_3.addWidget(self.sbKO, 0, 1, 1, 1)

        self.sbKK = QSpinBox(self.groupBox_2)
        self.sbKK.setObjectName(u"sbKK")
        self.sbKK.setMaximumSize(QSize(50, 16777215))
        self.sbKK.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.sbKK.setMinimum(-99)

        self.gridLayout_3.addWidget(self.sbKK, 0, 7, 1, 1)


        self.gridLayout_2.addLayout(self.gridLayout_3, 7, 1, 1, 1)

        self.label = QLabel(self.groupBox_2)
        self.label.setObjectName(u"label")
        self.label.setFont(font)

        self.gridLayout_2.addWidget(self.label, 2, 0, 1, 1)

        self.leNahrung = QLineEdit(self.groupBox_2)
        self.leNahrung.setObjectName(u"leNahrung")

        self.gridLayout_2.addWidget(self.leNahrung, 2, 1, 1, 1)

        self.label_17 = QLabel(self.groupBox_2)
        self.label_17.setObjectName(u"label_17")
        self.label_17.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout_2.addWidget(self.label_17, 5, 0, 1, 1)

        self.label_4 = QLabel(self.groupBox_2)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMaximumSize(QSize(250, 16777215))

        self.gridLayout_2.addWidget(self.label_4, 7, 0, 1, 1)

        self.label_14 = QLabel(self.groupBox_2)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setMinimumSize(QSize(0, 0))
        self.label_14.setMaximumSize(QSize(250, 16777215))
        self.label_14.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout_2.addWidget(self.label_14, 1, 0, 1, 1)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.cbTier = QComboBox(self.groupBox_2)
        self.cbTier.setObjectName(u"cbTier")
        sizePolicy1.setHeightForWidth(self.cbTier.sizePolicy().hasHeightForWidth())
        self.cbTier.setSizePolicy(sizePolicy1)

        self.verticalLayout_5.addWidget(self.cbTier)

        self.lblTier = QLabel(self.groupBox_2)
        self.lblTier.setObjectName(u"lblTier")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lblTier.sizePolicy().hasHeightForWidth())
        self.lblTier.setSizePolicy(sizePolicy2)
        self.lblTier.setWordWrap(True)

        self.verticalLayout_5.addWidget(self.lblTier)

        self.hlReiten = QHBoxLayout()
        self.hlReiten.setObjectName(u"hlReiten")
        self.lblRK = QLabel(self.groupBox_2)
        self.lblRK.setObjectName(u"lblRK")
        self.lblRK.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.hlReiten.addWidget(self.lblRK)

        self.sbRK = QSpinBox(self.groupBox_2)
        self.sbRK.setObjectName(u"sbRK")
        self.sbRK.setMaximumSize(QSize(50, 16777215))
        self.sbRK.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.sbRK.setMaximum(3)

        self.hlReiten.addWidget(self.sbRK)

        self.lblReiten = QLabel(self.groupBox_2)
        self.lblReiten.setObjectName(u"lblReiten")
        sizePolicy.setHeightForWidth(self.lblReiten.sizePolicy().hasHeightForWidth())
        self.lblReiten.setSizePolicy(sizePolicy)
        self.lblReiten.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.hlReiten.addWidget(self.lblReiten)

        self.sbReiten = QSpinBox(self.groupBox_2)
        self.sbReiten.setObjectName(u"sbReiten")
        sizePolicy1.setHeightForWidth(self.sbReiten.sizePolicy().hasHeightForWidth())
        self.sbReiten.setSizePolicy(sizePolicy1)
        self.sbReiten.setMaximumSize(QSize(50, 16777215))
        self.sbReiten.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.sbReiten.setMinimum(-10)

        self.hlReiten.addWidget(self.sbReiten)


        self.verticalLayout_5.addLayout(self.hlReiten)


        self.gridLayout_2.addLayout(self.verticalLayout_5, 1, 1, 1, 1)

        self.label_2 = QLabel(self.groupBox_2)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMaximumSize(QSize(250, 16777215))

        self.gridLayout_2.addWidget(self.label_2, 0, 0, 1, 1)

        self.checkAutoHintergrund = QCheckBox(self.groupBox_2)
        self.checkAutoHintergrund.setObjectName(u"checkAutoHintergrund")
        self.checkAutoHintergrund.setLayoutDirection(Qt.RightToLeft)
        self.checkAutoHintergrund.setChecked(True)

        self.gridLayout_2.addWidget(self.checkAutoHintergrund, 4, 1, 1, 1)

        self.line = QFrame(self.groupBox_2)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout_2.addWidget(self.line, 6, 0, 1, 2)

        self.label_19 = QLabel(self.groupBox_2)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout_2.addWidget(self.label_19, 8, 0, 1, 1)

        self.leVorteile = QLineEdit(self.groupBox_2)
        self.leVorteile.setObjectName(u"leVorteile")

        self.gridLayout_2.addWidget(self.leVorteile, 8, 1, 1, 1)


        self.verticalLayout_9.addLayout(self.gridLayout_2)


        self.gridLayout_5.addWidget(self.groupBox_2, 0, 0, 2, 1)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_5.addItem(self.verticalSpacer_3, 2, 0, 1, 1)


        self.verticalLayout_10.addLayout(self.gridLayout_5)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout = QVBoxLayout(self.tab_2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.groupBox_4 = QGroupBox(self.tab_2)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.verticalLayout_18 = QVBoxLayout(self.groupBox_4)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.verticalLayout_18.setContentsMargins(20, 20, 20, 20)
        self.gridLayout_9 = QGridLayout()
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.cbZucht = QComboBox(self.groupBox_4)
        self.cbZucht.addItem("")
        self.cbZucht.addItem("")
        self.cbZucht.addItem("")
        self.cbZucht.addItem("")
        self.cbZucht.addItem("")
        self.cbZucht.addItem("")
        self.cbZucht.addItem("")
        self.cbZucht.addItem("")
        self.cbZucht.setObjectName(u"cbZucht")
        sizePolicy1.setHeightForWidth(self.cbZucht.sizePolicy().hasHeightForWidth())
        self.cbZucht.setSizePolicy(sizePolicy1)

        self.gridLayout_9.addWidget(self.cbZucht, 0, 1, 1, 1)

        self.label_3 = QLabel(self.groupBox_4)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMaximumSize(QSize(250, 16777215))

        self.gridLayout_9.addWidget(self.label_3, 7, 0, 1, 1)

        self.lblAusbildung = QLabel(self.groupBox_4)
        self.lblAusbildung.setObjectName(u"lblAusbildung")
        sizePolicy2.setHeightForWidth(self.lblAusbildung.sizePolicy().hasHeightForWidth())
        self.lblAusbildung.setSizePolicy(sizePolicy2)
        self.lblAusbildung.setWordWrap(True)

        self.gridLayout_9.addWidget(self.lblAusbildung, 8, 1, 1, 1)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.cbGuteEig2 = QComboBox(self.groupBox_4)
        self.cbGuteEig2.setObjectName(u"cbGuteEig2")
        sizePolicy1.setHeightForWidth(self.cbGuteEig2.sizePolicy().hasHeightForWidth())
        self.cbGuteEig2.setSizePolicy(sizePolicy1)

        self.verticalLayout_3.addWidget(self.cbGuteEig2)

        self.lblGuteEig2 = QLabel(self.groupBox_4)
        self.lblGuteEig2.setObjectName(u"lblGuteEig2")
        sizePolicy2.setHeightForWidth(self.lblGuteEig2.sizePolicy().hasHeightForWidth())
        self.lblGuteEig2.setSizePolicy(sizePolicy2)
        self.lblGuteEig2.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.lblGuteEig2)


        self.gridLayout_9.addLayout(self.verticalLayout_3, 2, 1, 1, 1)

        self.verticalLayout_19 = QVBoxLayout()
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.cbSchlechteEig2 = QComboBox(self.groupBox_4)
        self.cbSchlechteEig2.setObjectName(u"cbSchlechteEig2")
        sizePolicy1.setHeightForWidth(self.cbSchlechteEig2.sizePolicy().hasHeightForWidth())
        self.cbSchlechteEig2.setSizePolicy(sizePolicy1)

        self.verticalLayout_19.addWidget(self.cbSchlechteEig2)

        self.lblSchlechteEig2 = QLabel(self.groupBox_4)
        self.lblSchlechteEig2.setObjectName(u"lblSchlechteEig2")
        sizePolicy2.setHeightForWidth(self.lblSchlechteEig2.sizePolicy().hasHeightForWidth())
        self.lblSchlechteEig2.setSizePolicy(sizePolicy2)
        self.lblSchlechteEig2.setWordWrap(True)

        self.verticalLayout_19.addWidget(self.lblSchlechteEig2)


        self.gridLayout_9.addLayout(self.verticalLayout_19, 5, 1, 1, 1)

        self.lblSchlechteEig = QLabel(self.groupBox_4)
        self.lblSchlechteEig.setObjectName(u"lblSchlechteEig")
        self.lblSchlechteEig.setMaximumSize(QSize(250, 16777215))
        self.lblSchlechteEig.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.lblSchlechteEig.setIndent(0)

        self.gridLayout_9.addWidget(self.lblSchlechteEig, 4, 0, 1, 1)

        self.cbAusbildung = QComboBox(self.groupBox_4)
        self.cbAusbildung.setObjectName(u"cbAusbildung")
        sizePolicy1.setHeightForWidth(self.cbAusbildung.sizePolicy().hasHeightForWidth())
        self.cbAusbildung.setSizePolicy(sizePolicy1)

        self.gridLayout_9.addWidget(self.cbAusbildung, 7, 1, 1, 1)

        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.cbSchlechteEig1 = QComboBox(self.groupBox_4)
        self.cbSchlechteEig1.setObjectName(u"cbSchlechteEig1")
        sizePolicy1.setHeightForWidth(self.cbSchlechteEig1.sizePolicy().hasHeightForWidth())
        self.cbSchlechteEig1.setSizePolicy(sizePolicy1)

        self.verticalLayout_7.addWidget(self.cbSchlechteEig1)

        self.lblSchlechteEig1 = QLabel(self.groupBox_4)
        self.lblSchlechteEig1.setObjectName(u"lblSchlechteEig1")
        self.lblSchlechteEig1.setScaledContents(False)
        self.lblSchlechteEig1.setWordWrap(True)

        self.verticalLayout_7.addWidget(self.lblSchlechteEig1)


        self.gridLayout_9.addLayout(self.verticalLayout_7, 4, 1, 1, 1)

        self.line_7 = QFrame(self.groupBox_4)
        self.line_7.setObjectName(u"line_7")
        self.line_7.setFrameShape(QFrame.HLine)
        self.line_7.setFrameShadow(QFrame.Sunken)

        self.gridLayout_9.addWidget(self.line_7, 6, 0, 1, 2)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.cbGuteEig1 = QComboBox(self.groupBox_4)
        self.cbGuteEig1.setObjectName(u"cbGuteEig1")
        sizePolicy1.setHeightForWidth(self.cbGuteEig1.sizePolicy().hasHeightForWidth())
        self.cbGuteEig1.setSizePolicy(sizePolicy1)

        self.verticalLayout_2.addWidget(self.cbGuteEig1)

        self.lblGuteEig1 = QLabel(self.groupBox_4)
        self.lblGuteEig1.setObjectName(u"lblGuteEig1")
        self.lblGuteEig1.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.lblGuteEig1)


        self.gridLayout_9.addLayout(self.verticalLayout_2, 1, 1, 1, 1)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.cbGuteEig3 = QComboBox(self.groupBox_4)
        self.cbGuteEig3.setObjectName(u"cbGuteEig3")
        sizePolicy1.setHeightForWidth(self.cbGuteEig3.sizePolicy().hasHeightForWidth())
        self.cbGuteEig3.setSizePolicy(sizePolicy1)

        self.verticalLayout_4.addWidget(self.cbGuteEig3)

        self.lblGuteEig3 = QLabel(self.groupBox_4)
        self.lblGuteEig3.setObjectName(u"lblGuteEig3")
        sizePolicy2.setHeightForWidth(self.lblGuteEig3.sizePolicy().hasHeightForWidth())
        self.lblGuteEig3.setSizePolicy(sizePolicy2)
        self.lblGuteEig3.setWordWrap(True)

        self.verticalLayout_4.addWidget(self.lblGuteEig3)


        self.gridLayout_9.addLayout(self.verticalLayout_4, 3, 1, 1, 1)

        self.lblZucht = QLabel(self.groupBox_4)
        self.lblZucht.setObjectName(u"lblZucht")
        self.lblZucht.setMaximumSize(QSize(250, 16777215))

        self.gridLayout_9.addWidget(self.lblZucht, 0, 0, 1, 1)

        self.lblGuteEig = QLabel(self.groupBox_4)
        self.lblGuteEig.setObjectName(u"lblGuteEig")
        self.lblGuteEig.setMaximumSize(QSize(250, 16777215))
        self.lblGuteEig.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout_9.addWidget(self.lblGuteEig, 1, 0, 1, 1)


        self.verticalLayout_18.addLayout(self.gridLayout_9)


        self.verticalLayout.addWidget(self.groupBox_4)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.verticalLayout_6 = QVBoxLayout(self.tab_3)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(20, 20, 20, 20)
        self.gbInventar = QGroupBox(self.tab_3)
        self.gbInventar.setObjectName(u"gbInventar")
        self.gbInventar.setFlat(False)
        self.gridLayout_10 = QGridLayout(self.gbInventar)
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.gridLayout_10.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.gridLayout_10.setContentsMargins(20, 20, 20, 20)
        self.leAusruestung17 = QLineEdit(self.gbInventar)
        self.leAusruestung17.setObjectName(u"leAusruestung17")

        self.gridLayout_10.addWidget(self.leAusruestung17, 6, 1, 1, 1)

        self.leAusruestung20 = QLineEdit(self.gbInventar)
        self.leAusruestung20.setObjectName(u"leAusruestung20")

        self.gridLayout_10.addWidget(self.leAusruestung20, 9, 1, 1, 1)

        self.leAusruestung6 = QLineEdit(self.gbInventar)
        self.leAusruestung6.setObjectName(u"leAusruestung6")

        self.gridLayout_10.addWidget(self.leAusruestung6, 5, 0, 1, 1)

        self.leAusruestung14 = QLineEdit(self.gbInventar)
        self.leAusruestung14.setObjectName(u"leAusruestung14")

        self.gridLayout_10.addWidget(self.leAusruestung14, 3, 1, 1, 1)

        self.leAusruestung8 = QLineEdit(self.gbInventar)
        self.leAusruestung8.setObjectName(u"leAusruestung8")

        self.gridLayout_10.addWidget(self.leAusruestung8, 7, 0, 1, 1)

        self.leAusruestung11 = QLineEdit(self.gbInventar)
        self.leAusruestung11.setObjectName(u"leAusruestung11")
        self.leAusruestung11.setMinimumSize(QSize(320, 0))

        self.gridLayout_10.addWidget(self.leAusruestung11, 0, 1, 1, 1)

        self.leAusruestung10 = QLineEdit(self.gbInventar)
        self.leAusruestung10.setObjectName(u"leAusruestung10")

        self.gridLayout_10.addWidget(self.leAusruestung10, 9, 0, 1, 1)

        self.leAusruestung13 = QLineEdit(self.gbInventar)
        self.leAusruestung13.setObjectName(u"leAusruestung13")

        self.gridLayout_10.addWidget(self.leAusruestung13, 2, 1, 1, 1)

        self.leAusruestung2 = QLineEdit(self.gbInventar)
        self.leAusruestung2.setObjectName(u"leAusruestung2")

        self.gridLayout_10.addWidget(self.leAusruestung2, 1, 0, 1, 1)

        self.leAusruestung18 = QLineEdit(self.gbInventar)
        self.leAusruestung18.setObjectName(u"leAusruestung18")

        self.gridLayout_10.addWidget(self.leAusruestung18, 7, 1, 1, 1)

        self.leAusruestung1 = QLineEdit(self.gbInventar)
        self.leAusruestung1.setObjectName(u"leAusruestung1")
        self.leAusruestung1.setMinimumSize(QSize(320, 0))
        self.leAusruestung1.setCursor(QCursor(Qt.IBeamCursor))

        self.gridLayout_10.addWidget(self.leAusruestung1, 0, 0, 1, 1)

        self.leAusruestung12 = QLineEdit(self.gbInventar)
        self.leAusruestung12.setObjectName(u"leAusruestung12")

        self.gridLayout_10.addWidget(self.leAusruestung12, 1, 1, 1, 1)

        self.leAusruestung7 = QLineEdit(self.gbInventar)
        self.leAusruestung7.setObjectName(u"leAusruestung7")

        self.gridLayout_10.addWidget(self.leAusruestung7, 6, 0, 1, 1)

        self.leAusruestung19 = QLineEdit(self.gbInventar)
        self.leAusruestung19.setObjectName(u"leAusruestung19")

        self.gridLayout_10.addWidget(self.leAusruestung19, 8, 1, 1, 1)

        self.leAusruestung16 = QLineEdit(self.gbInventar)
        self.leAusruestung16.setObjectName(u"leAusruestung16")

        self.gridLayout_10.addWidget(self.leAusruestung16, 5, 1, 1, 1)

        self.leAusruestung15 = QLineEdit(self.gbInventar)
        self.leAusruestung15.setObjectName(u"leAusruestung15")

        self.gridLayout_10.addWidget(self.leAusruestung15, 4, 1, 1, 1)

        self.leAusruestung5 = QLineEdit(self.gbInventar)
        self.leAusruestung5.setObjectName(u"leAusruestung5")

        self.gridLayout_10.addWidget(self.leAusruestung5, 4, 0, 1, 1)

        self.leAusruestung4 = QLineEdit(self.gbInventar)
        self.leAusruestung4.setObjectName(u"leAusruestung4")

        self.gridLayout_10.addWidget(self.leAusruestung4, 3, 0, 1, 1)

        self.leAusruestung9 = QLineEdit(self.gbInventar)
        self.leAusruestung9.setObjectName(u"leAusruestung9")

        self.gridLayout_10.addWidget(self.leAusruestung9, 8, 0, 1, 1)

        self.leAusruestung3 = QLineEdit(self.gbInventar)
        self.leAusruestung3.setObjectName(u"leAusruestung3")

        self.gridLayout_10.addWidget(self.leAusruestung3, 2, 0, 1, 1)


        self.verticalLayout_6.addWidget(self.gbInventar)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer)

        self.tabWidget.addTab(self.tab_3, "")

        self.gridLayout_4.addWidget(self.tabWidget, 0, 0, 1, 1)

        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.groupBox_3 = QGroupBox(self.scrollAreaWidgetContents)
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
        self.labelImage.setAlignment(Qt.AlignCenter)

        self.gridLayout_6.addWidget(self.labelImage, 1, 0, 1, 2)


        self.verticalLayout_11.addWidget(self.groupBox_3)

        self.groupBox = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_8 = QVBoxLayout(self.groupBox)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.lblWerte = QLabel(self.groupBox)
        self.lblWerte.setObjectName(u"lblWerte")
        sizePolicy.setHeightForWidth(self.lblWerte.sizePolicy().hasHeightForWidth())
        self.lblWerte.setSizePolicy(sizePolicy)
        self.lblWerte.setTextFormat(Qt.RichText)
        self.lblWerte.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.lblWerte.setWordWrap(True)

        self.verticalLayout_8.addWidget(self.lblWerte)


        self.verticalLayout_11.addWidget(self.groupBox)

        self.groupBox_5 = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.gridLayout_7 = QGridLayout(self.groupBox_5)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.spinRegelnGroesse = QSpinBox(self.groupBox_5)
        self.spinRegelnGroesse.setObjectName(u"spinRegelnGroesse")
        self.spinRegelnGroesse.setMinimumSize(QSize(60, 0))
        self.spinRegelnGroesse.setMaximumSize(QSize(60, 16777215))
        self.spinRegelnGroesse.setButtonSymbols(QAbstractSpinBox.PlusMinus)
        self.spinRegelnGroesse.setMinimum(6)
        self.spinRegelnGroesse.setMaximum(18)
        self.spinRegelnGroesse.setValue(8)

        self.gridLayout_7.addWidget(self.spinRegelnGroesse, 2, 1, 1, 1)

        self.label_20 = QLabel(self.groupBox_5)
        self.label_20.setObjectName(u"label_20")

        self.gridLayout_7.addWidget(self.label_20, 2, 0, 1, 1)

        self.verticalSpacer_4 = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_7.addItem(self.verticalSpacer_4, 6, 1, 1, 1)

        self.checkRegeln = QCheckBox(self.groupBox_5)
        self.checkRegeln.setObjectName(u"checkRegeln")
        self.checkRegeln.setChecked(True)

        self.gridLayout_7.addWidget(self.checkRegeln, 1, 1, 1, 1)

        self.label_21 = QLabel(self.groupBox_5)
        self.label_21.setObjectName(u"label_21")

        self.gridLayout_7.addWidget(self.label_21, 1, 0, 1, 1)

        self.label_22 = QLabel(self.groupBox_5)
        self.label_22.setObjectName(u"label_22")

        self.gridLayout_7.addWidget(self.label_22, 4, 0, 1, 1)

        self.checkEditierbar = QCheckBox(self.groupBox_5)
        self.checkEditierbar.setObjectName(u"checkEditierbar")

        self.gridLayout_7.addWidget(self.checkEditierbar, 4, 1, 1, 1)


        self.verticalLayout_11.addWidget(self.groupBox_5)


        self.gridLayout_4.addLayout(self.verticalLayout_11, 0, 1, 1, 1)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout.addWidget(self.scrollArea, 1, 0, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.buttonLoad = QPushButton(formMain)
        self.buttonLoad.setObjectName(u"buttonLoad")

        self.horizontalLayout_3.addWidget(self.buttonLoad)

        self.buttonQuicksave = QPushButton(formMain)
        self.buttonQuicksave.setObjectName(u"buttonQuicksave")

        self.horizontalLayout_3.addWidget(self.buttonQuicksave)

        self.buttonSave = QPushButton(formMain)
        self.buttonSave.setObjectName(u"buttonSave")

        self.horizontalLayout_3.addWidget(self.buttonSave)

        self.btnSavePdf = QPushButton(formMain)
        self.btnSavePdf.setObjectName(u"btnSavePdf")
        self.btnSavePdf.setEnabled(True)
        self.btnSavePdf.setMinimumSize(QSize(100, 0))
        self.btnSavePdf.setMaximumSize(QSize(16777214, 16777215))

        self.horizontalLayout_3.addWidget(self.btnSavePdf)


        self.gridLayout.addLayout(self.horizontalLayout_3, 6, 0, 1, 1)

        QWidget.setTabOrder(self.leName, self.cbTier)
        QWidget.setTabOrder(self.cbTier, self.sbRK)
        QWidget.setTabOrder(self.sbRK, self.sbReiten)
        QWidget.setTabOrder(self.sbReiten, self.sbKO)
        QWidget.setTabOrder(self.sbKO, self.sbMU)
        QWidget.setTabOrder(self.sbMU, self.sbGE)
        QWidget.setTabOrder(self.sbGE, self.sbKK)
        QWidget.setTabOrder(self.sbKK, self.sbIN)
        QWidget.setTabOrder(self.sbIN, self.sbKL)
        QWidget.setTabOrder(self.sbKL, self.sbCH)
        QWidget.setTabOrder(self.sbCH, self.sbFF)
        QWidget.setTabOrder(self.sbFF, self.sbKampfwerte)
        QWidget.setTabOrder(self.sbKampfwerte, self.sbGS)
        QWidget.setTabOrder(self.sbGS, self.sbRS)
        QWidget.setTabOrder(self.sbRS, self.btnSavePdf)

        self.retranslateUi(formMain)

        self.tabWidget.setCurrentIndex(0)
        self.cbZucht.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(formMain)
    # setupUi

    def retranslateUi(self, formMain):
        formMain.setWindowTitle(QCoreApplication.translate("formMain", u"Sephrasto - Tierbegleiter erstellen", None))
        self.groupBox_2.setTitle("")
        self.label_18.setText(QCoreApplication.translate("formMain", u"Hintergrund", None))
        self.label_11.setText(QCoreApplication.translate("formMain", u"KK", None))
        self.label_5.setText(QCoreApplication.translate("formMain", u"KO", None))
        self.label_13.setText(QCoreApplication.translate("formMain", u"GS", None))
        self.label_7.setText(QCoreApplication.translate("formMain", u"CH", None))
        self.label_6.setText(QCoreApplication.translate("formMain", u"IN", None))
        self.label_9.setText(QCoreApplication.translate("formMain", u"FF", None))
        self.label_8.setText(QCoreApplication.translate("formMain", u"MU", None))
        self.label_15.setText(QCoreApplication.translate("formMain", u"RS", None))
        self.label_16.setText(QCoreApplication.translate("formMain", u"Kampfwerte", None))
        self.label_12.setText(QCoreApplication.translate("formMain", u"KL", None))
        self.label_10.setText(QCoreApplication.translate("formMain", u"GE", None))
        self.label.setText(QCoreApplication.translate("formMain", u"Nahrung", None))
        self.label_17.setText(QCoreApplication.translate("formMain", u"<html><head/><body><p><span style=\" font-weight:600;\">Aussehen</span></p></body></html>", None))
        self.label_4.setText(QCoreApplication.translate("formMain", u"<html><head/><body><p><span style=\" font-weight:600;\">Attributs-Anpassungen</span></p><p><span style=\" font-size:6pt;\">(z.B. f\u00fcr Vertrautenmagie oder R\u00fcstungen)</span></p></body></html>", None))
        self.label_14.setText(QCoreApplication.translate("formMain", u"<html><head/><body><p><span style=\" font-weight:600;\">Tier</span></p></body></html>", None))
        self.lblTier.setText("")
        self.lblRK.setText(QCoreApplication.translate("formMain", u"Reiterkampfstil-Stufe", None))
        self.lblReiten.setText(QCoreApplication.translate("formMain", u"Reiten-PW - BE", None))
#if QT_CONFIG(tooltip)
        self.sbReiten.setToolTip(QCoreApplication.translate("formMain", u"Trage hier deinen Reiten-PW abz\u00fcglich BE ein. Nicht vergessen - mit Reiterkampf II sinkt die BE um 1!", None))
#endif // QT_CONFIG(tooltip)
        self.label_2.setText(QCoreApplication.translate("formMain", u"<html><head/><body><p><span style=\" font-weight:600;\">Name</span></p></body></html>", None))
        self.checkAutoHintergrund.setText(QCoreApplication.translate("formMain", u"Automatisch bef\u00fcllen", None))
        self.label_19.setText(QCoreApplication.translate("formMain", u"<html><head/><body><p><span style=\" font-weight:600;\">Weitere Vorteile </span>(kommagetrennt)</p></body></html>", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("formMain", u"Beschreibung und Attribute", None))
        self.groupBox_4.setTitle("")
        self.cbZucht.setItemText(0, QCoreApplication.translate("formMain", u"Keine (1 Gute, 2 Schlechte Eigenschaften)", None))
        self.cbZucht.setItemText(1, QCoreApplication.translate("formMain", u"Keine (1 Schlechte Eigenschaft)", None))
        self.cbZucht.setItemText(2, QCoreApplication.translate("formMain", u"Gew\u00f6hnlich (1 Gute, 1 Schlechte Eigenschaft)", None))
        self.cbZucht.setItemText(3, QCoreApplication.translate("formMain", u"Gew\u00f6hnlich (keine Eigenschaften)", None))
        self.cbZucht.setItemText(4, QCoreApplication.translate("formMain", u"Aussergew\u00f6hnlich (2 Gute, 1 Schlechte Eigenschaft)", None))
        self.cbZucht.setItemText(5, QCoreApplication.translate("formMain", u"Aussergew\u00f6hnlich (1 Gute Eigenschaft)", None))
        self.cbZucht.setItemText(6, QCoreApplication.translate("formMain", u"Herausragend (2 Gute Eigenschaften)", None))
        self.cbZucht.setItemText(7, QCoreApplication.translate("formMain", u"Einzigartig (3 Gute Eigenschaften)", None))

        self.label_3.setText(QCoreApplication.translate("formMain", u"<html><head/><body><p><span style=\" font-weight:600;\">Ausbildung</span></p></body></html>", None))
        self.lblAusbildung.setText("")
        self.lblGuteEig2.setText("")
        self.lblSchlechteEig2.setText("")
        self.lblSchlechteEig.setText(QCoreApplication.translate("formMain", u"    Schlechte Tiereigenschaften", None))
        self.lblSchlechteEig1.setText("")
        self.lblGuteEig1.setText("")
        self.lblGuteEig3.setText("")
        self.lblZucht.setText(QCoreApplication.translate("formMain", u"<html><head/><body><p><span style=\" font-weight:600;\">Zuchtqualit\u00e4t</span></p></body></html>", None))
        self.lblGuteEig.setText(QCoreApplication.translate("formMain", u"    Gute Tiereigenschaften", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("formMain", u"Zucht und Ausbildung", None))
        self.gbInventar.setTitle("")
        self.leAusruestung1.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("formMain", u"Ausr\u00fcstung", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("formMain", u"Bild", None))
        self.buttonLoadImage.setText(QCoreApplication.translate("formMain", u"Bild Laden", None))
        self.buttonDeleteImage.setText(QCoreApplication.translate("formMain", u"Bild L\u00f6schen", None))
        self.labelImage.setText(QCoreApplication.translate("formMain", u"Bild-Aufl\u00f6sung: 193x254 px\n"
"(wird automatisch angepasst)", None))
        self.groupBox.setTitle(QCoreApplication.translate("formMain", u"Vorschau und Preis", None))
        self.lblWerte.setText(QCoreApplication.translate("formMain", u"<html><head/><body><p><br/></p></body></html>", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("formMain", u"Einstellungen", None))
        self.label_20.setText(QCoreApplication.translate("formMain", u"Regelschriftgr\u00f6\u00dfe", None))
        self.checkRegeln.setText("")
        self.label_21.setText(QCoreApplication.translate("formMain", u"Relevante Regeln anh\u00e4ngen", None))
        self.label_22.setText(QCoreApplication.translate("formMain", u"Formularfelder editierbar", None))
        self.checkEditierbar.setText("")
        self.buttonLoad.setText(QCoreApplication.translate("formMain", u"Laden", None))
        self.buttonQuicksave.setText(QCoreApplication.translate("formMain", u"Speichern", None))
        self.buttonSave.setText(QCoreApplication.translate("formMain", u"Speichern unter...", None))
        self.btnSavePdf.setText(QCoreApplication.translate("formMain", u"PDF erstellen", None))
    # retranslateUi

