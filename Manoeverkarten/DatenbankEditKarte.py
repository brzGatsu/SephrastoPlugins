# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'DatenbankEditKarte.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_karteDialog(object):
    def setupUi(self, karteDialog):
        if not karteDialog.objectName():
            karteDialog.setObjectName(u"karteDialog")
        karteDialog.setWindowModality(Qt.ApplicationModal)
        karteDialog.resize(1033, 764)
        self.gridLayout_2 = QGridLayout(karteDialog)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.buttonBox = QDialogButtonBox(karteDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)
        self.buttonBox.setCenterButtons(True)

        self.gridLayout_2.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gbPreview = QGroupBox(karteDialog)
        self.gbPreview.setObjectName(u"gbPreview")
        self.verticalLayout_2 = QVBoxLayout(self.gbPreview)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")

        self.gridLayout.addWidget(self.gbPreview, 1, 1, 1, 1)

        self.warning = QLabel(karteDialog)
        self.warning.setObjectName(u"warning")
        self.warning.setVisible(False)
        self.warning.setStyleSheet(u"background-color: rgb(255, 255, 0); color: black;")
        self.warning.setWordWrap(True)

        self.gridLayout.addWidget(self.warning, 0, 0, 1, 2)

        self.gbEditor = QGroupBox(karteDialog)
        self.gbEditor.setObjectName(u"gbEditor")
        self.gridLayout_4 = QGridLayout(self.gbEditor)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setHorizontalSpacing(12)
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.comboSubtyp = QComboBox(self.gbEditor)
        self.comboSubtyp.setObjectName(u"comboSubtyp")

        self.verticalLayout_4.addWidget(self.comboSubtyp)

        self.labelFarbe = QLabel(self.gbEditor)
        self.labelFarbe.setObjectName(u"labelFarbe")
        self.labelFarbe.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.verticalLayout_4.addWidget(self.labelFarbe)


        self.gridLayout_3.addLayout(self.verticalLayout_4, 0, 2, 1, 1)

        self.buttonFarbe = QPushButton(self.gbEditor)
        self.buttonFarbe.setObjectName(u"buttonFarbe")
        self.buttonFarbe.setMinimumSize(QSize(20, 20))
        self.buttonFarbe.setMaximumSize(QSize(20, 20))

        self.gridLayout_3.addWidget(self.buttonFarbe, 0, 4, 1, 1)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.labelSubtyp = QLabel(self.gbEditor)
        self.labelSubtyp.setObjectName(u"labelSubtyp")
        self.labelSubtyp.setMinimumSize(QSize(60, 0))
        self.labelSubtyp.setMaximumSize(QSize(60, 16777215))

        self.verticalLayout.addWidget(self.labelSubtyp)


        self.gridLayout_3.addLayout(self.verticalLayout, 0, 1, 1, 1)

        self.comboTyp = QComboBox(self.gbEditor)
        self.comboTyp.addItem("")
        self.comboTyp.addItem("")
        self.comboTyp.addItem("")
        self.comboTyp.addItem("")
        self.comboTyp.addItem("")
        self.comboTyp.addItem("")
        self.comboTyp.setObjectName(u"comboTyp")
        self.comboTyp.setMinimumSize(QSize(150, 0))
        self.comboTyp.setMaximumSize(QSize(140, 16777209))

        self.gridLayout_3.addWidget(self.comboTyp, 0, 0, 1, 1)

        self.labelFarbeGewaehlt = QLabel(self.gbEditor)
        self.labelFarbeGewaehlt.setObjectName(u"labelFarbeGewaehlt")
        self.labelFarbeGewaehlt.setMinimumSize(QSize(20, 20))
        self.labelFarbeGewaehlt.setMaximumSize(QSize(20, 20))

        self.gridLayout_3.addWidget(self.labelFarbeGewaehlt, 0, 3, 1, 1)


        self.gridLayout_4.addLayout(self.gridLayout_3, 1, 1, 1, 1)

        self.leUntertitel = QLineEdit(self.gbEditor)
        self.leUntertitel.setObjectName(u"leUntertitel")

        self.gridLayout_4.addWidget(self.leUntertitel, 5, 1, 1, 1)

        self.leName = QLineEdit(self.gbEditor)
        self.leName.setObjectName(u"leName")

        self.gridLayout_4.addWidget(self.leName, 0, 1, 1, 1)

        self.label = QLabel(self.gbEditor)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(140, 0))

        self.gridLayout_4.addWidget(self.label, 0, 0, 1, 1)

        self.labelText = QLabel(self.gbEditor)
        self.labelText.setObjectName(u"labelText")

        self.gridLayout_4.addWidget(self.labelText, 6, 0, 1, 1)

        self.labelUntertitel = QLabel(self.gbEditor)
        self.labelUntertitel.setObjectName(u"labelUntertitel")

        self.gridLayout_4.addWidget(self.labelUntertitel, 5, 0, 1, 1)

        self.leFusszeile = QLineEdit(self.gbEditor)
        self.leFusszeile.setObjectName(u"leFusszeile")

        self.gridLayout_4.addWidget(self.leFusszeile, 8, 1, 1, 1)

        self.labelTyp = QLabel(self.gbEditor)
        self.labelTyp.setObjectName(u"labelTyp")

        self.gridLayout_4.addWidget(self.labelTyp, 1, 0, 1, 1)

        self.vlBeschreibung = QVBoxLayout()
        self.vlBeschreibung.setSpacing(0)
        self.vlBeschreibung.setObjectName(u"vlBeschreibung")
        self.teBeschreibung = QPlainTextEdit(self.gbEditor)
        self.teBeschreibung.setObjectName(u"teBeschreibung")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.teBeschreibung.sizePolicy().hasHeightForWidth())
        self.teBeschreibung.setSizePolicy(sizePolicy)

        self.vlBeschreibung.addWidget(self.teBeschreibung)


        self.gridLayout_4.addLayout(self.vlBeschreibung, 6, 1, 1, 1)

        self.labelVoraussetzungen = QLabel(self.gbEditor)
        self.labelVoraussetzungen.setObjectName(u"labelVoraussetzungen")

        self.gridLayout_4.addWidget(self.labelVoraussetzungen, 3, 0, 1, 1)

        self.leTitel = QLineEdit(self.gbEditor)
        self.leTitel.setObjectName(u"leTitel")

        self.gridLayout_4.addWidget(self.leTitel, 4, 1, 1, 1)

        self.labelNewEditDelete = QLabel(self.gbEditor)
        self.labelNewEditDelete.setObjectName(u"labelNewEditDelete")

        self.gridLayout_4.addWidget(self.labelNewEditDelete, 2, 0, 1, 1)

        self.labelFusszeile = QLabel(self.gbEditor)
        self.labelFusszeile.setObjectName(u"labelFusszeile")

        self.gridLayout_4.addWidget(self.labelFusszeile, 8, 0, 1, 1)

        self.teVoraussetzungen = QPlainTextEdit(self.gbEditor)
        self.teVoraussetzungen.setObjectName(u"teVoraussetzungen")
        self.teVoraussetzungen.setMaximumSize(QSize(16777215, 50))

        self.gridLayout_4.addWidget(self.teVoraussetzungen, 3, 1, 1, 1)

        self.groupNewEditDelete = QWidget(self.gbEditor)
        self.groupNewEditDelete.setObjectName(u"groupNewEditDelete")
        self.layoutEditDelete = QHBoxLayout(self.groupNewEditDelete)
        self.layoutEditDelete.setObjectName(u"layoutEditDelete")
        self.layoutEditDelete.setContentsMargins(0, 0, 0, 0)
        self.labelInfo = QLabel(self.groupNewEditDelete)
        self.labelInfo.setObjectName(u"labelInfo")
        self.labelInfo.setMinimumSize(QSize(0, 20))
        self.labelInfo.setMaximumSize(QSize(16777215, 20))

        self.layoutEditDelete.addWidget(self.labelInfo)

        self.radioEdit = QRadioButton(self.groupNewEditDelete)
        self.radioEdit.setObjectName(u"radioEdit")
        self.radioEdit.setMinimumSize(QSize(0, 20))
        self.radioEdit.setMaximumSize(QSize(16777215, 20))

        self.layoutEditDelete.addWidget(self.radioEdit)

        self.radioDelete = QRadioButton(self.groupNewEditDelete)
        self.radioDelete.setObjectName(u"radioDelete")
        self.radioDelete.setMinimumSize(QSize(0, 20))
        self.radioDelete.setMaximumSize(QSize(16777215, 20))

        self.layoutEditDelete.addWidget(self.radioDelete)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.layoutEditDelete.addItem(self.horizontalSpacer)


        self.gridLayout_4.addWidget(self.groupNewEditDelete, 2, 1, 1, 1)

        self.labelTitel = QLabel(self.gbEditor)
        self.labelTitel.setObjectName(u"labelTitel")

        self.gridLayout_4.addWidget(self.labelTitel, 4, 0, 1, 1)


        self.gridLayout.addWidget(self.gbEditor, 1, 0, 1, 1)


        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)


        self.retranslateUi(karteDialog)
        self.buttonBox.accepted.connect(karteDialog.accept)
        self.buttonBox.rejected.connect(karteDialog.reject)

        QMetaObject.connectSlotsByName(karteDialog)
    # setupUi

    def retranslateUi(self, karteDialog):
        karteDialog.setWindowTitle(QCoreApplication.translate("karteDialog", u"Sephrasto - Man\u00f6verkarte bearbeiten...", None))
        self.gbPreview.setTitle(QCoreApplication.translate("karteDialog", u"Vorschau", None))
        self.warning.setText(QCoreApplication.translate("karteDialog", u"<html><head/><body><p>Dies ist eine Standard-Man\u00f6verkarte. Sobald du hier etwas ver\u00e4nderst, bekommst du eine pers\u00f6nliche Kopie und das Original wird in den Hausregeln gel\u00f6scht. Damit erh\u00e4ltst du f\u00fcr diese Man\u00f6verkarte keine automatischen Updates mehr mit neuen Man\u00f6verkarten-Plugin-Versionen.</p></body></html>", None))
        self.gbEditor.setTitle(QCoreApplication.translate("karteDialog", u"Editor", None))
        self.labelFarbe.setText(QCoreApplication.translate("karteDialog", u"Deckfarbe", None))
        self.buttonFarbe.setText(QCoreApplication.translate("karteDialog", u"W\u00e4hlen", None))
        self.buttonFarbe.setProperty("class", QCoreApplication.translate("karteDialog", u"icon", None))
        self.labelSubtyp.setText(QCoreApplication.translate("karteDialog", u"Subtyp", None))
        self.comboTyp.setItemText(0, QCoreApplication.translate("karteDialog", u"Vorteil", None))
        self.comboTyp.setItemText(1, QCoreApplication.translate("karteDialog", u"Regel", None))
        self.comboTyp.setItemText(2, QCoreApplication.translate("karteDialog", u"Talent", None))
        self.comboTyp.setItemText(3, QCoreApplication.translate("karteDialog", u"Waffeneigenschaft", None))
        self.comboTyp.setItemText(4, QCoreApplication.translate("karteDialog", u"Deck", None))
        self.comboTyp.setItemText(5, QCoreApplication.translate("karteDialog", u"Benutzerdefiniert", None))

        self.labelFarbeGewaehlt.setText("")
#if QT_CONFIG(tooltip)
        self.leUntertitel.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.leUntertitel.setText(QCoreApplication.translate("karteDialog", u"$original$", None))
        self.label.setText(QCoreApplication.translate("karteDialog", u"Name", None))
        self.labelText.setText(QCoreApplication.translate("karteDialog", u"Beschreibung", None))
        self.labelUntertitel.setText(QCoreApplication.translate("karteDialog", u"Untertitel", None))
#if QT_CONFIG(tooltip)
        self.leFusszeile.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.leFusszeile.setText(QCoreApplication.translate("karteDialog", u"$original$", None))
        self.labelTyp.setText(QCoreApplication.translate("karteDialog", u"Typ", None))
#if QT_CONFIG(tooltip)
        self.teBeschreibung.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.teBeschreibung.setPlainText(QCoreApplication.translate("karteDialog", u"$original$", None))
        self.labelVoraussetzungen.setText(QCoreApplication.translate("karteDialog", u"<html><head/><body><p>Voraussetzungen</p><p>(nur Charakterexport)</p></body></html>", None))
        self.leTitel.setText(QCoreApplication.translate("karteDialog", u"$original$", None))
        self.labelNewEditDelete.setText(QCoreApplication.translate("karteDialog", u"Aktion", None))
        self.labelFusszeile.setText(QCoreApplication.translate("karteDialog", u"Fu\u00dfzeile", None))
        self.labelInfo.setText(QCoreApplication.translate("karteDialog", u"Neue Karte erstellen", None))
        self.radioEdit.setText(QCoreApplication.translate("karteDialog", u"Generierte Karte bearbeiten", None))
        self.radioDelete.setText(QCoreApplication.translate("karteDialog", u"Generierte Karte l\u00f6schen", None))
        self.labelTitel.setText(QCoreApplication.translate("karteDialog", u"Titel", None))
    # retranslateUi

