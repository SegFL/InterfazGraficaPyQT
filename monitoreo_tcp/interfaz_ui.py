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
from PySide6.QtWidgets import (QApplication, QComboBox, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QMenuBar, QPushButton,
    QSizePolicy, QSpinBox, QStatusBar, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(565, 600)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setMaximumSize(QSize(16777215, 546))
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
        sizePolicy.setHeightForWidth(self.layout_plots.sizePolicy().hasHeightForWidth())
        self.layout_plots.setSizePolicy(sizePolicy)
        self.btn_pause = QPushButton(self.tab_plots)
        self.btn_pause.setObjectName(u"btn_pause")
        self.btn_pause.setGeometry(QRect(680, 0, 41, 26))
        self.lineEdit_muestras = QLineEdit(self.tab_plots)
        self.lineEdit_muestras.setObjectName(u"lineEdit_muestras")
        self.lineEdit_muestras.setGeometry(QRect(550, 0, 113, 26))
        self.tabWidget.addTab(self.tab_plots, "")
        self.curve_editor = QWidget()
        self.curve_editor.setObjectName(u"curve_editor")
        sizePolicy.setHeightForWidth(self.curve_editor.sizePolicy().hasHeightForWidth())
        self.curve_editor.setSizePolicy(sizePolicy)
        self.tableCurva = QTableWidget(self.curve_editor)
        self.tableCurva.setObjectName(u"tableCurva")
        self.tableCurva.setGeometry(QRect(50, 10, 591, 241))
        self.spinBoxCurveID = QSpinBox(self.curve_editor)
        self.spinBoxCurveID.setObjectName(u"spinBoxCurveID")
        self.spinBoxCurveID.setGeometry(QRect(680, 20, 77, 26))
        self.btnAgregarFila = QPushButton(self.curve_editor)
        self.btnAgregarFila.setObjectName(u"btnAgregarFila")
        self.btnAgregarFila.setGeometry(QRect(680, 60, 81, 26))
        self.btnEliminarFila = QPushButton(self.curve_editor)
        self.btnEliminarFila.setObjectName(u"btnEliminarFila")
        self.btnEliminarFila.setGeometry(QRect(690, 100, 81, 26))
        self.btnEnviarCurva = QPushButton(self.curve_editor)
        self.btnEnviarCurva.setObjectName(u"btnEnviarCurva")
        self.btnEnviarCurva.setGeometry(QRect(700, 140, 81, 26))
        self.plot_curva_container = QWidget(self.curve_editor)
        self.plot_curva_container.setObjectName(u"plot_curva_container")
        self.plot_curva_container.setGeometry(QRect(20, 270, 741, 181))
        sizePolicy.setHeightForWidth(self.plot_curva_container.sizePolicy().hasHeightForWidth())
        self.plot_curva_container.setSizePolicy(sizePolicy)
        self.tabWidget.addTab(self.curve_editor, "")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 565, 33))
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
        self.btnAgregarFila.setText(QCoreApplication.translate("MainWindow", u"Agregar fila", None))
        self.btnEliminarFila.setText(QCoreApplication.translate("MainWindow", u"Eliminar fila", None))
        self.btnEnviarCurva.setText(QCoreApplication.translate("MainWindow", u"Enviar", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.curve_editor), QCoreApplication.translate("MainWindow", u"Curvas", None))
    # retranslateUi

