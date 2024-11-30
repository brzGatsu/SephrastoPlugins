# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'RSCharakterRuestung.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QGridLayout,
    QGroupBox, QLabel, QLayout, QLineEdit,
    QScrollArea, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout, QWidget)

class Ui_formAusruestung(object):
    def setupUi(self, formAusruestung):
        if not formAusruestung.objectName():
            formAusruestung.setObjectName(u"formAusruestung")
        formAusruestung.resize(971, 735)
        formAusruestung.setMinimumSize(QSize(802, 0))
        self.verticalLayout = QVBoxLayout(formAusruestung)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollArea = QScrollArea(formAusruestung)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 969, 733))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(20, 20, 20, 20)
        self.gbRstungen = QGroupBox(self.scrollAreaWidgetContents)
        self.gbRstungen.setObjectName(u"gbRstungen")
        self.verticalLayout_3 = QVBoxLayout(self.gbRstungen)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(20, 20, 20, 20)
        self.Ruestungen = QGridLayout()
        self.Ruestungen.setObjectName(u"Ruestungen")
        self.Ruestungen.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.labelRarm = QLabel(self.gbRstungen)
        self.labelRarm.setObjectName(u"labelRarm")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelRarm.sizePolicy().hasHeightForWidth())
        self.labelRarm.setSizePolicy(sizePolicy)
        self.labelRarm.setMinimumSize(QSize(35, 0))
        font = QFont()
        font.setBold(True)
        self.labelRarm.setFont(font)
        self.labelRarm.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.Ruestungen.addWidget(self.labelRarm, 0, 6, 1, 1)

        self.spinGesamtBauch = QSpinBox(self.gbRstungen)
        self.spinGesamtBauch.setObjectName(u"spinGesamtBauch")
        self.spinGesamtBauch.setMinimumSize(QSize(44, 0))
        self.spinGesamtBauch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinGesamtBauch.setReadOnly(True)
        self.spinGesamtBauch.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinGesamtBauch.setMaximum(999)

        self.Ruestungen.addWidget(self.spinGesamtBauch, 1, 7, 1, 1)

        self.spinGesamtKopf = QSpinBox(self.gbRstungen)
        self.spinGesamtKopf.setObjectName(u"spinGesamtKopf")
        self.spinGesamtKopf.setMinimumSize(QSize(44, 0))
        self.spinGesamtKopf.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinGesamtKopf.setReadOnly(True)
        self.spinGesamtKopf.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinGesamtKopf.setMaximum(999)

        self.Ruestungen.addWidget(self.spinGesamtKopf, 1, 9, 1, 1)

        self.label = QLabel(self.gbRstungen)
        self.label.setObjectName(u"label")
        self.label.setFont(font)

        self.Ruestungen.addWidget(self.label, 2, 0, 1, 2)

        self.labelPunkte = QLabel(self.gbRstungen)
        self.labelPunkte.setObjectName(u"labelPunkte")
        self.labelPunkte.setFont(font)
        self.labelPunkte.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.Ruestungen.addWidget(self.labelPunkte, 0, 10, 1, 1)

        self.label_2 = QLabel(self.gbRstungen)
        self.label_2.setObjectName(u"label_2")

        self.Ruestungen.addWidget(self.label_2, 1, 0, 1, 1)

        self.spinGesamtLarm = QSpinBox(self.gbRstungen)
        self.spinGesamtLarm.setObjectName(u"spinGesamtLarm")
        self.spinGesamtLarm.setMinimumSize(QSize(44, 0))
        self.spinGesamtLarm.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinGesamtLarm.setReadOnly(True)
        self.spinGesamtLarm.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinGesamtLarm.setMaximum(999)

        self.Ruestungen.addWidget(self.spinGesamtLarm, 1, 5, 1, 1)

        self.labelRS = QLabel(self.gbRstungen)
        self.labelRS.setObjectName(u"labelRS")
        self.labelRS.setFont(font)
        self.labelRS.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.Ruestungen.addWidget(self.labelRS, 0, 3, 1, 1)

        self.labelLarm = QLabel(self.gbRstungen)
        self.labelLarm.setObjectName(u"labelLarm")
        self.labelLarm.setMinimumSize(QSize(35, 0))
        self.labelLarm.setFont(font)
        self.labelLarm.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.Ruestungen.addWidget(self.labelLarm, 0, 5, 1, 1)

        self.spinGesamtPunkte = QSpinBox(self.gbRstungen)
        self.spinGesamtPunkte.setObjectName(u"spinGesamtPunkte")
        self.spinGesamtPunkte.setMinimumSize(QSize(44, 0))
        self.spinGesamtPunkte.setFrame(False)
        self.spinGesamtPunkte.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinGesamtPunkte.setReadOnly(True)
        self.spinGesamtPunkte.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinGesamtPunkte.setMaximum(999)

        self.Ruestungen.addWidget(self.spinGesamtPunkte, 1, 10, 1, 1)

        self.labelKopf = QLabel(self.gbRstungen)
        self.labelKopf.setObjectName(u"labelKopf")
        self.labelKopf.setMinimumSize(QSize(35, 0))
        self.labelKopf.setFont(font)
        self.labelKopf.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.Ruestungen.addWidget(self.labelKopf, 0, 9, 1, 1)

        self.labelBE = QLabel(self.gbRstungen)
        self.labelBE.setObjectName(u"labelBE")
        self.labelBE.setMinimumSize(QSize(35, 0))
        self.labelBE.setFont(font)
        self.labelBE.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.Ruestungen.addWidget(self.labelBE, 0, 2, 1, 1)

        self.spinGesamtBein = QSpinBox(self.gbRstungen)
        self.spinGesamtBein.setObjectName(u"spinGesamtBein")
        self.spinGesamtBein.setMinimumSize(QSize(44, 0))
        self.spinGesamtBein.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinGesamtBein.setReadOnly(True)
        self.spinGesamtBein.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinGesamtBein.setMaximum(999)

        self.Ruestungen.addWidget(self.spinGesamtBein, 1, 4, 1, 1)

        self.editGesamtName = QLineEdit(self.gbRstungen)
        self.editGesamtName.setObjectName(u"editGesamtName")

        self.Ruestungen.addWidget(self.editGesamtName, 1, 1, 1, 1)

        self.spinGesamtRS = QSpinBox(self.gbRstungen)
        self.spinGesamtRS.setObjectName(u"spinGesamtRS")
        self.spinGesamtRS.setMinimumSize(QSize(44, 0))
        self.spinGesamtRS.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinGesamtRS.setReadOnly(True)
        self.spinGesamtRS.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinGesamtRS.setMaximum(999)

        self.Ruestungen.addWidget(self.spinGesamtRS, 1, 3, 1, 1)

        self.spinGesamtBrust = QSpinBox(self.gbRstungen)
        self.spinGesamtBrust.setObjectName(u"spinGesamtBrust")
        self.spinGesamtBrust.setMinimumSize(QSize(44, 0))
        self.spinGesamtBrust.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinGesamtBrust.setReadOnly(True)
        self.spinGesamtBrust.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinGesamtBrust.setMaximum(999)

        self.Ruestungen.addWidget(self.spinGesamtBrust, 1, 8, 1, 1)

        self.spinGesamtBE = QSpinBox(self.gbRstungen)
        self.spinGesamtBE.setObjectName(u"spinGesamtBE")
        self.spinGesamtBE.setMinimumSize(QSize(44, 0))
        self.spinGesamtBE.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinGesamtBE.setReadOnly(False)
        self.spinGesamtBE.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.spinGesamtBE.setMaximum(999)

        self.Ruestungen.addWidget(self.spinGesamtBE, 1, 2, 1, 1)

        self.labelBauch = QLabel(self.gbRstungen)
        self.labelBauch.setObjectName(u"labelBauch")
        sizePolicy.setHeightForWidth(self.labelBauch.sizePolicy().hasHeightForWidth())
        self.labelBauch.setSizePolicy(sizePolicy)
        self.labelBauch.setMinimumSize(QSize(35, 0))
        self.labelBauch.setFont(font)
        self.labelBauch.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.Ruestungen.addWidget(self.labelBauch, 0, 7, 1, 1)

        self.labelBrust = QLabel(self.gbRstungen)
        self.labelBrust.setObjectName(u"labelBrust")
        self.labelBrust.setMinimumSize(QSize(35, 0))
        self.labelBrust.setFont(font)
        self.labelBrust.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.Ruestungen.addWidget(self.labelBrust, 0, 8, 1, 1)

        self.labelBein = QLabel(self.gbRstungen)
        self.labelBein.setObjectName(u"labelBein")
        self.labelBein.setMinimumSize(QSize(35, 0))
        self.labelBein.setFont(font)
        self.labelBein.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.Ruestungen.addWidget(self.labelBein, 0, 4, 1, 1)

        self.label_3 = QLabel(self.gbRstungen)
        self.label_3.setObjectName(u"label_3")

        self.Ruestungen.addWidget(self.label_3, 1, 11, 1, 1)

        self.spinGesamtRarm = QSpinBox(self.gbRstungen)
        self.spinGesamtRarm.setObjectName(u"spinGesamtRarm")
        self.spinGesamtRarm.setMinimumSize(QSize(44, 0))
        self.spinGesamtRarm.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinGesamtRarm.setReadOnly(True)
        self.spinGesamtRarm.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinGesamtRarm.setMaximum(999)

        self.Ruestungen.addWidget(self.spinGesamtRarm, 1, 6, 1, 1)

        self.labelRName = QLabel(self.gbRstungen)
        self.labelRName.setObjectName(u"labelRName")
        self.labelRName.setFont(font)

        self.Ruestungen.addWidget(self.labelRName, 0, 1, 1, 1)


        self.verticalLayout_3.addLayout(self.Ruestungen)

        self.checkZonen = QCheckBox(self.gbRstungen)
        self.checkZonen.setObjectName(u"checkZonen")
        self.checkZonen.setMinimumSize(QSize(0, 18))
        self.checkZonen.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.checkZonen.setChecked(True)

        self.verticalLayout_3.addWidget(self.checkZonen)

        self.labelHinweis = QLabel(self.gbRstungen)
        self.labelHinweis.setObjectName(u"labelHinweis")
        self.labelHinweis.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.verticalLayout_3.addWidget(self.labelHinweis)

        self.verticalSpacer_4 = QSpacerItem(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_4)


        self.verticalLayout_2.addWidget(self.gbRstungen)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)


        self.retranslateUi(formAusruestung)

        QMetaObject.connectSlotsByName(formAusruestung)
    # setupUi

    def retranslateUi(self, formAusruestung):
        formAusruestung.setWindowTitle(QCoreApplication.translate("formAusruestung", u"Form", None))
        self.scrollArea.setProperty(u"class", QCoreApplication.translate("formAusruestung", u"transparent", None))
        self.gbRstungen.setTitle("")
        self.labelRarm.setText(QCoreApplication.translate("formAusruestung", u"R. Arm", None))
        self.labelRarm.setProperty(u"class", QCoreApplication.translate("formAusruestung", u"h4", None))
#if QT_CONFIG(tooltip)
        self.spinGesamtBauch.setToolTip(QCoreApplication.translate("formAusruestung", u"Die R\u00fcstungswerte werden automatisch aus allen Slots berechnet.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.spinGesamtKopf.setToolTip(QCoreApplication.translate("formAusruestung", u"Die R\u00fcstungswerte werden automatisch aus allen Slots berechnet.", None))
#endif // QT_CONFIG(tooltip)
        self.label.setText(QCoreApplication.translate("formAusruestung", u"Slots", None))
        self.label.setProperty(u"class", QCoreApplication.translate("formAusruestung", u"h4", None))
        self.labelPunkte.setText(QCoreApplication.translate("formAusruestung", u"Punkte", None))
        self.labelPunkte.setProperty(u"class", QCoreApplication.translate("formAusruestung", u"h4", None))
        self.label_2.setText(QCoreApplication.translate("formAusruestung", u"Gesamte R\u00fcstung", None))
#if QT_CONFIG(tooltip)
        self.spinGesamtLarm.setToolTip(QCoreApplication.translate("formAusruestung", u"Die R\u00fcstungswerte werden automatisch aus allen Slots berechnet.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.labelRS.setToolTip(QCoreApplication.translate("formAusruestung", u"R\u00fcstungsschutz", None))
#endif // QT_CONFIG(tooltip)
        self.labelRS.setText(QCoreApplication.translate("formAusruestung", u"RS", None))
        self.labelRS.setProperty(u"class", QCoreApplication.translate("formAusruestung", u"h4", None))
        self.labelLarm.setText(QCoreApplication.translate("formAusruestung", u"L. Arm", None))
        self.labelLarm.setProperty(u"class", QCoreApplication.translate("formAusruestung", u"h4", None))
        self.labelKopf.setText(QCoreApplication.translate("formAusruestung", u"Kopf", None))
        self.labelKopf.setProperty(u"class", QCoreApplication.translate("formAusruestung", u"h4", None))
#if QT_CONFIG(tooltip)
        self.labelBE.setToolTip(QCoreApplication.translate("formAusruestung", u"Behinderung", None))
#endif // QT_CONFIG(tooltip)
        self.labelBE.setText(QCoreApplication.translate("formAusruestung", u"BE", None))
        self.labelBE.setProperty(u"class", QCoreApplication.translate("formAusruestung", u"h4", None))
#if QT_CONFIG(tooltip)
        self.spinGesamtBein.setToolTip(QCoreApplication.translate("formAusruestung", u"Die R\u00fcstungswerte werden automatisch aus allen Slots berechnet.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.editGesamtName.setToolTip("")
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.spinGesamtRS.setToolTip(QCoreApplication.translate("formAusruestung", u"Die R\u00fcstungswerte werden automatisch aus allen Slots berechnet.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.spinGesamtBrust.setToolTip(QCoreApplication.translate("formAusruestung", u"Die R\u00fcstungswerte werden automatisch aus allen Slots berechnet.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.spinGesamtBE.setToolTip(QCoreApplication.translate("formAusruestung", u"Die R\u00fcstungswerte werden automatisch aus allen Slots berechnet.", None))
#endif // QT_CONFIG(tooltip)
        self.labelBauch.setText(QCoreApplication.translate("formAusruestung", u"Bauch", None))
        self.labelBauch.setProperty(u"class", QCoreApplication.translate("formAusruestung", u"h4", None))
        self.labelBrust.setText(QCoreApplication.translate("formAusruestung", u"Brust", None))
        self.labelBrust.setProperty(u"class", QCoreApplication.translate("formAusruestung", u"h4", None))
        self.labelBein.setText(QCoreApplication.translate("formAusruestung", u"Bein", None))
        self.labelBein.setProperty(u"class", QCoreApplication.translate("formAusruestung", u"h4", None))
        self.label_3.setText("")
#if QT_CONFIG(tooltip)
        self.spinGesamtRarm.setToolTip(QCoreApplication.translate("formAusruestung", u"Die R\u00fcstungswerte werden automatisch aus allen Slots berechnet.", None))
#endif // QT_CONFIG(tooltip)
        self.labelRName.setText(QCoreApplication.translate("formAusruestung", u"Name", None))
        self.labelRName.setProperty(u"class", QCoreApplication.translate("formAusruestung", u"h4", None))
        self.checkZonen.setText(QCoreApplication.translate("formAusruestung", u"Zonenr\u00fcstungssystem bei allen R\u00fcstungen benutzen", None))
        self.labelHinweis.setText(QCoreApplication.translate("formAusruestung", u"Hinweis: Nur R\u00fcstung 1 wird zur Berechnung der WS* usw. verwendet.", None))
    # retranslateUi

