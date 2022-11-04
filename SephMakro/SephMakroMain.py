# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'SephMakroMain.ui'
##
## Created by: Qt User Interface Compiler version 6.3.1
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
    QPlainTextEdit, QPushButton, QSizePolicy, QSpacerItem,
    QSplitter, QToolButton, QVBoxLayout, QWidget)

class Ui_formMain(object):
    def setupUi(self, formMain):
        if not formMain.objectName():
            formMain.setObjectName(u"formMain")
        formMain.setWindowModality(Qt.ApplicationModal)
        formMain.resize(1016, 811)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(formMain.sizePolicy().hasHeightForWidth())
        formMain.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(formMain)
        self.gridLayout.setObjectName(u"gridLayout")
        self.splitter = QSplitter(formMain)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Vertical)
        self.horizontalLayoutWidget = QWidget(self.splitter)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.horizontalLayoutWidget)
        self.teOutput = QPlainTextEdit(self.splitter)
        self.teOutput.setObjectName(u"teOutput")
        self.teOutput.setReadOnly(True)
        self.splitter.addWidget(self.teOutput)

        self.gridLayout.addWidget(self.splitter, 1, 2, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.buttonRun = QToolButton(formMain)
        self.buttonRun.setObjectName(u"buttonRun")

        self.horizontalLayout_2.addWidget(self.buttonRun)

        self.buttonLoad = QToolButton(formMain)
        self.buttonLoad.setObjectName(u"buttonLoad")

        self.horizontalLayout_2.addWidget(self.buttonLoad)

        self.buttonSave = QToolButton(formMain)
        self.buttonSave.setObjectName(u"buttonSave")

        self.horizontalLayout_2.addWidget(self.buttonSave)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.buttonSaveOutput = QPushButton(formMain)
        self.buttonSaveOutput.setObjectName(u"buttonSaveOutput")
        self.buttonSaveOutput.setMaximumSize(QSize(120, 16777215))

        self.horizontalLayout_2.addWidget(self.buttonSaveOutput)


        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 2, 1, 1)

        self.makroListLayout = QGroupBox(formMain)
        self.makroListLayout.setObjectName(u"makroListLayout")
        self.verticalLayout = QVBoxLayout(self.makroListLayout)
        self.verticalLayout.setObjectName(u"verticalLayout")

        self.gridLayout.addWidget(self.makroListLayout, 0, 0, 2, 1)


        self.retranslateUi(formMain)

        QMetaObject.connectSlotsByName(formMain)
    # setupUi

    def retranslateUi(self, formMain):
        formMain.setWindowTitle(QCoreApplication.translate("formMain", u"SephMakro", None))
        self.buttonRun.setText(QCoreApplication.translate("formMain", u"...", None))
#if QT_CONFIG(shortcut)
        self.buttonRun.setShortcut(QCoreApplication.translate("formMain", u"F5", None))
#endif // QT_CONFIG(shortcut)
        self.buttonLoad.setText(QCoreApplication.translate("formMain", u"...", None))
#if QT_CONFIG(shortcut)
        self.buttonLoad.setShortcut(QCoreApplication.translate("formMain", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.buttonSave.setText(QCoreApplication.translate("formMain", u"...", None))
#if QT_CONFIG(shortcut)
        self.buttonSave.setShortcut(QCoreApplication.translate("formMain", u"Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
        self.buttonSaveOutput.setText(QCoreApplication.translate("formMain", u"Ausgabe speichern", None))
        self.makroListLayout.setTitle(QCoreApplication.translate("formMain", u"Makros", None))
    # retranslateUi

