# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'interfaz.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
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
from PySide6.QtWidgets import (QApplication, QComboBox, QLabel, QLineEdit,
    QMainWindow, QMenuBar, QPushButton, QSizePolicy,
    QStatusBar, QTabWidget, QTextEdit, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(0, 0, 791, 551))
        self.tab_terminal = QWidget()
        self.tab_terminal.setObjectName(u"tab_terminal")
        self.label = QLabel(self.tab_terminal)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 0, 49, 16))
        self.btnIniciar = QPushButton(self.tab_terminal)
        self.btnIniciar.setObjectName(u"btnIniciar")
        self.btnIniciar.setGeometry(QRect(370, 0, 81, 26))
        self.comboBox = QComboBox(self.tab_terminal)
        self.comboBox.setObjectName(u"comboBox")
        self.comboBox.setGeometry(QRect(100, 0, 82, 26))
        self.comboBox_2 = QComboBox(self.tab_terminal)
        self.comboBox_2.setObjectName(u"comboBox_2")
        self.comboBox_2.setGeometry(QRect(220, 0, 91, 26))
        self.textEdit = QTextEdit(self.tab_terminal)
        self.textEdit.setObjectName(u"textEdit")
        self.textEdit.setGeometry(QRect(20, 70, 671, 391))
        self.btn_refresh = QPushButton(self.tab_terminal)
        self.btn_refresh.setObjectName(u"btn_refresh")
        self.btn_refresh.setGeometry(QRect(190, 0, 21, 26))
        self.pushButton_2 = QPushButton(self.tab_terminal)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setGeometry(QRect(560, 470, 81, 26))
        self.input_send = QLineEdit(self.tab_terminal)
        self.input_send.setObjectName(u"input_send")
        self.input_send.setGeometry(QRect(20, 470, 531, 26))
        self.tabWidget.addTab(self.tab_terminal, "")
        self.tab_plots = QWidget()
        self.tab_plots.setObjectName(u"tab_plots")
        self.layout_plots = QWidget(self.tab_plots)
        self.layout_plots.setObjectName(u"layout_plots")
        self.layout_plots.setGeometry(QRect(20, 20, 751, 491))
        self.btn_pause = QPushButton(self.tab_plots)
        self.btn_pause.setObjectName(u"btn_pause")
        self.btn_pause.setGeometry(QRect(680, 0, 41, 26))
        self.tabWidget.addTab(self.tab_plots, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.btnIniciar.setText(QCoreApplication.translate("MainWindow", u"Iniciar", None))
        self.btn_refresh.setText(QCoreApplication.translate("MainWindow", u"PushButton", None))
        self.pushButton_2.setText(QCoreApplication.translate("MainWindow", u"Enviar", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_terminal), QCoreApplication.translate("MainWindow", u"Comunicacion", None))
        self.btn_pause.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_plots), QCoreApplication.translate("MainWindow", u"Graficos", None))
    # retranslateUi

