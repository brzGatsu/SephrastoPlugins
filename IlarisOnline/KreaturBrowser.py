# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'KreaturBrowser.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QGridLayout, QHeaderView,
    QLabel, QLineEdit, QSizePolicy, QTreeWidget,
    QTreeWidgetItem, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(465, 581)
        self.gridLayout = QGridLayout(Dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.widget = QWidget(Dialog)
        self.widget.setObjectName(u"widget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.gridLayout_2 = QGridLayout(self.widget)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.cbNSC = QCheckBox(self.widget)
        self.cbNSC.setObjectName(u"cbNSC")

        self.gridLayout_2.addWidget(self.cbNSC, 2, 0, 1, 1)

        self.cbTyp = QComboBox(self.widget)
        self.cbTyp.setObjectName(u"cbTyp")

        self.gridLayout_2.addWidget(self.cbTyp, 2, 1, 1, 1)

        self.leSuche = QLineEdit(self.widget)
        self.leSuche.setObjectName(u"leSuche")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.leSuche.sizePolicy().hasHeightForWidth())
        self.leSuche.setSizePolicy(sizePolicy1)

        self.gridLayout_2.addWidget(self.leSuche, 0, 0, 1, 2)


        self.gridLayout.addWidget(self.widget, 1, 0, 1, 2)

        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")
        font = QFont()
        font.setBold(True)
        self.label_4.setFont(font)

        self.gridLayout.addWidget(self.label_4, 0, 0, 1, 2)

        self.treeKreaturen = QTreeWidget(Dialog)
        self.treeKreaturen.setObjectName(u"treeKreaturen")

        self.gridLayout.addWidget(self.treeKreaturen, 3, 0, 1, 2)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setMaximumSize(QSize(16777215, 16777215))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)

        self.gridLayout.addWidget(self.buttonBox, 8, 0, 1, 2)


        self.retranslateUi(Dialog)
        self.buttonBox.rejected.connect(Dialog.reject)
        self.buttonBox.accepted.connect(Dialog.accept)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Sephrasto - Kreaturen Import", None))
        self.cbNSC.setText(QCoreApplication.translate("Dialog", u"NSCs anzeigen", None))
        self.leSuche.setPlaceholderText(QCoreApplication.translate("Dialog", u"Name und Beschreibung durchsuchen", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Kreaturen von Ilaris-Online.de", None))
        self.label_4.setProperty(u"class", QCoreApplication.translate("Dialog", u"h2", None))
        ___qtreewidgetitem = self.treeKreaturen.headerItem()
        ___qtreewidgetitem.setText(3, QCoreApplication.translate("Dialog", u"Von", None));
        ___qtreewidgetitem.setText(2, QCoreApplication.translate("Dialog", u"Beschreibung", None));
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("Dialog", u"Typ", None));
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("Dialog", u"Name", None));
    # retranslateUi

