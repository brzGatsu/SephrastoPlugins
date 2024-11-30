# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'KartenExportDialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QTreeWidget, QTreeWidgetItem,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(465, 581)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.labelOpen = QLabel(Dialog)
        self.labelOpen.setObjectName(u"labelOpen")

        self.gridLayout.addWidget(self.labelOpen, 6, 0, 1, 1)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setMaximumSize(QSize(16777215, 16777215))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setCenterButtons(True)

        self.gridLayout.addWidget(self.buttonBox, 14, 0, 1, 2)

        self.labelEinzeln = QLabel(Dialog)
        self.labelEinzeln.setObjectName(u"labelEinzeln")

        self.gridLayout.addWidget(self.labelEinzeln, 11, 0, 1, 1)

        self.treeCategories = QTreeWidget(Dialog)
        self.treeCategories.setObjectName(u"treeCategories")

        self.gridLayout.addWidget(self.treeCategories, 4, 0, 1, 2)

        self.checkEinzeln = QCheckBox(Dialog)
        self.checkEinzeln.setObjectName(u"checkEinzeln")
        self.checkEinzeln.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.gridLayout.addWidget(self.checkEinzeln, 11, 1, 1, 1)

        self.leNameFormat = QLineEdit(Dialog)
        self.leNameFormat.setObjectName(u"leNameFormat")

        self.gridLayout.addWidget(self.leNameFormat, 12, 1, 1, 1)

        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")
        font = QFont()
        font.setBold(True)
        self.label_4.setFont(font)

        self.gridLayout.addWidget(self.label_4, 0, 0, 1, 2)

        self.checkHintergrund = QCheckBox(Dialog)
        self.checkHintergrund.setObjectName(u"checkHintergrund")
        self.checkHintergrund.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.checkHintergrund.setChecked(True)

        self.gridLayout.addWidget(self.checkHintergrund, 7, 1, 1, 1)

        self.checkOpen = QCheckBox(Dialog)
        self.checkOpen.setObjectName(u"checkOpen")
        self.checkOpen.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.checkOpen.setChecked(True)

        self.gridLayout.addWidget(self.checkOpen, 6, 1, 1, 1)

        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 7, 0, 1, 1)

        self.labelNameFormat = QLabel(Dialog)
        self.labelNameFormat.setObjectName(u"labelNameFormat")

        self.gridLayout.addWidget(self.labelNameFormat, 12, 0, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.comboFormat = QComboBox(Dialog)
        self.comboFormat.addItem("")
        self.comboFormat.addItem("")
        self.comboFormat.setObjectName(u"comboFormat")
        self.comboFormat.setMinimumSize(QSize(80, 0))
        self.comboFormat.setMaximumSize(QSize(80, 16777215))

        self.horizontalLayout_3.addWidget(self.comboFormat)


        self.gridLayout.addLayout(self.horizontalLayout_3, 10, 1, 1, 1)

        self.labelBilder = QLabel(Dialog)
        self.labelBilder.setObjectName(u"labelBilder")

        self.gridLayout.addWidget(self.labelBilder, 10, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.buttonExpandToggle = QPushButton(Dialog)
        self.buttonExpandToggle.setObjectName(u"buttonExpandToggle")
        font1 = QFont()
        font1.setHintingPreference(QFont.PreferNoHinting)
        self.buttonExpandToggle.setFont(font1)

        self.horizontalLayout.addWidget(self.buttonExpandToggle)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.gridLayout.addLayout(self.horizontalLayout, 3, 0, 1, 2)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Sephrasto - Man\u00f6verkarten Export", None))
        self.labelOpen.setText(QCoreApplication.translate("Dialog", u"PDF nach dem Erstellen \u00f6ffnen", None))
        self.labelEinzeln.setText(QCoreApplication.translate("Dialog", u"Jede Karte als einzelne Datei ausgeben", None))
        ___qtreewidgetitem = self.treeCategories.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("Dialog", u"Kategorien", None));
        self.checkEinzeln.setText("")
        self.leNameFormat.setText(QCoreApplication.translate("Dialog", u"{deckname}_{titel}", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Man\u00f6verkarten Export", None))
        self.label_4.setProperty(u"class", QCoreApplication.translate("Dialog", u"h2", None))
#if QT_CONFIG(tooltip)
        self.checkHintergrund.setToolTip(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Wenn du die Karten ohne Hintergrundbild ausdruckst, sparst du Tinte.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkHintergrund.setText("")
        self.checkOpen.setText("")
        self.label.setText(QCoreApplication.translate("Dialog", u"Hintergrundbild", None))
        self.labelNameFormat.setText(QCoreApplication.translate("Dialog", u"Dateinamen-Format", None))
        self.comboFormat.setItemText(0, QCoreApplication.translate("Dialog", u"PDF", None))
        self.comboFormat.setItemText(1, QCoreApplication.translate("Dialog", u"JPG", None))

        self.labelBilder.setText(QCoreApplication.translate("Dialog", u"Format", None))
        self.buttonExpandToggle.setText(QCoreApplication.translate("Dialog", u"Expand Toggle", None))
        self.buttonExpandToggle.setProperty(u"class", QCoreApplication.translate("Dialog", u"icon", None))
    # retranslateUi

