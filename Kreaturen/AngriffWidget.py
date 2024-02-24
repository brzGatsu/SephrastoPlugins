# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'AngriffWidget.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QSizePolicy, QSpinBox, QVBoxLayout,
    QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(876, 101)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.wAngriff = QWidget(Form)
        self.wAngriff.setObjectName(u"wAngriff")
        self.gridLayout_11 = QGridLayout(self.wAngriff)
        self.gridLayout_11.setObjectName(u"gridLayout_11")
        self.sbLZ = QSpinBox(self.wAngriff)
        self.sbLZ.setObjectName(u"sbLZ")
        self.sbLZ.setMinimumSize(QSize(50, 0))

        self.gridLayout_11.addWidget(self.sbLZ, 2, 7, 1, 1)

        self.label_21 = QLabel(self.wAngriff)
        self.label_21.setObjectName(u"label_21")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_21.sizePolicy().hasHeightForWidth())
        self.label_21.setSizePolicy(sizePolicy)

        self.gridLayout_11.addWidget(self.label_21, 1, 4, 1, 1)

        self.sbRW = QSpinBox(self.wAngriff)
        self.sbRW.setObjectName(u"sbRW")
        self.sbRW.setMinimumSize(QSize(50, 0))

        self.gridLayout_11.addWidget(self.sbRW, 2, 4, 1, 1)

        self.sbVT = QSpinBox(self.wAngriff)
        self.sbVT.setObjectName(u"sbVT")
        self.sbVT.setMinimumSize(QSize(50, 0))

        self.gridLayout_11.addWidget(self.sbVT, 2, 6, 1, 1)

        self.label_22 = QLabel(self.wAngriff)
        self.label_22.setObjectName(u"label_22")
        sizePolicy.setHeightForWidth(self.label_22.sizePolicy().hasHeightForWidth())
        self.label_22.setSizePolicy(sizePolicy)

        self.gridLayout_11.addWidget(self.label_22, 1, 5, 1, 1)

        self.leTP = QLineEdit(self.wAngriff)
        self.leTP.setObjectName(u"leTP")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.leTP.sizePolicy().hasHeightForWidth())
        self.leTP.setSizePolicy(sizePolicy1)

        self.gridLayout_11.addWidget(self.leTP, 2, 3, 1, 1)

        self.label_4 = QLabel(self.wAngriff)
        self.label_4.setObjectName(u"label_4")
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy2)

        self.gridLayout_11.addWidget(self.label_4, 1, 0, 1, 1)

        self.sbAT = QSpinBox(self.wAngriff)
        self.sbAT.setObjectName(u"sbAT")
        self.sbAT.setMinimumSize(QSize(50, 0))

        self.gridLayout_11.addWidget(self.sbAT, 2, 5, 1, 1)

        self.leName = QLineEdit(self.wAngriff)
        self.leName.setObjectName(u"leName")
        sizePolicy1.setHeightForWidth(self.leName.sizePolicy().hasHeightForWidth())
        self.leName.setSizePolicy(sizePolicy1)

        self.gridLayout_11.addWidget(self.leName, 2, 0, 1, 3)

        self.label_20 = QLabel(self.wAngriff)
        self.label_20.setObjectName(u"label_20")
        sizePolicy.setHeightForWidth(self.label_20.sizePolicy().hasHeightForWidth())
        self.label_20.setSizePolicy(sizePolicy)

        self.gridLayout_11.addWidget(self.label_20, 1, 3, 1, 1)

        self.sbHT = QSpinBox(self.wAngriff)
        self.sbHT.setObjectName(u"sbHT")
        self.sbHT.setMinimumSize(QSize(50, 0))

        self.gridLayout_11.addWidget(self.sbHT, 2, 8, 1, 1)

        self.label_28 = QLabel(self.wAngriff)
        self.label_28.setObjectName(u"label_28")
        sizePolicy.setHeightForWidth(self.label_28.sizePolicy().hasHeightForWidth())
        self.label_28.setSizePolicy(sizePolicy)

        self.gridLayout_11.addWidget(self.label_28, 1, 6, 1, 1)

        self.label_30 = QLabel(self.wAngriff)
        self.label_30.setObjectName(u"label_30")
        sizePolicy.setHeightForWidth(self.label_30.sizePolicy().hasHeightForWidth())
        self.label_30.setSizePolicy(sizePolicy)

        self.gridLayout_11.addWidget(self.label_30, 1, 8, 1, 1)

        self.label_29 = QLabel(self.wAngriff)
        self.label_29.setObjectName(u"label_29")
        sizePolicy.setHeightForWidth(self.label_29.sizePolicy().hasHeightForWidth())
        self.label_29.setSizePolicy(sizePolicy)

        self.gridLayout_11.addWidget(self.label_29, 1, 7, 1, 1)

        self.widget_3 = QWidget(self.wAngriff)
        self.widget_3.setObjectName(u"widget_3")
        sizePolicy.setHeightForWidth(self.widget_3.sizePolicy().hasHeightForWidth())
        self.widget_3.setSizePolicy(sizePolicy)
        self.horizontalLayout_2 = QHBoxLayout(self.widget_3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_31 = QLabel(self.widget_3)
        self.label_31.setObjectName(u"label_31")
        sizePolicy2.setHeightForWidth(self.label_31.sizePolicy().hasHeightForWidth())
        self.label_31.setSizePolicy(sizePolicy2)
        self.label_31.setMinimumSize(QSize(90, 0))

        self.horizontalLayout_2.addWidget(self.label_31)

        self.leEigenschaften = QLineEdit(self.widget_3)
        self.leEigenschaften.setObjectName(u"leEigenschaften")
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(2)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.leEigenschaften.sizePolicy().hasHeightForWidth())
        self.leEigenschaften.setSizePolicy(sizePolicy3)

        self.horizontalLayout_2.addWidget(self.leEigenschaften)


        self.gridLayout_11.addWidget(self.widget_3, 3, 0, 1, 9)


        self.verticalLayout.addWidget(self.wAngriff)

        QWidget.setTabOrder(self.leName, self.leTP)
        QWidget.setTabOrder(self.leTP, self.sbRW)
        QWidget.setTabOrder(self.sbRW, self.sbAT)
        QWidget.setTabOrder(self.sbAT, self.sbVT)
        QWidget.setTabOrder(self.sbVT, self.sbLZ)
        QWidget.setTabOrder(self.sbLZ, self.sbHT)
        QWidget.setTabOrder(self.sbHT, self.leEigenschaften)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_21.setText(QCoreApplication.translate("Form", u"RW", None))
        self.label_22.setText(QCoreApplication.translate("Form", u"AT", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"Name", None))
        self.label_20.setText(QCoreApplication.translate("Form", u"TP", None))
        self.label_28.setText(QCoreApplication.translate("Form", u"VT", None))
        self.label_30.setText(QCoreApplication.translate("Form", u"H\u00e4rte", None))
        self.label_29.setText(QCoreApplication.translate("Form", u"LZ", None))
        self.label_31.setText(QCoreApplication.translate("Form", u"Eigenschafgen: ", None))
    # retranslateUi

