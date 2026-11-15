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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMainWindow, QMenuBar, QPushButton, QSizePolicy,
    QSpacerItem, QSpinBox, QStatusBar, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QToolButton,
    QVBoxLayout, QWidget)

from pyqtgraph import PlotWidget
from series_selector import SeriesSelector

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(650, 626)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setMaximumSize(QSize(16777215, 16777215))
        self.horizontalLayout_2 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.frame_2 = QFrame(self.centralwidget)
        self.frame_2.setObjectName(u"frame_2")
        sizePolicy.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_7 = QVBoxLayout(self.frame_2)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.tabWidget = QTabWidget(self.frame_2)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab_terminal = QWidget()
        self.tab_terminal.setObjectName(u"tab_terminal")
        self.frame_7 = QFrame(self.tab_terminal)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setGeometry(QRect(0, 0, 801, 491))
        sizePolicy.setHeightForWidth(self.frame_7.sizePolicy().hasHeightForWidth())
        self.frame_7.setSizePolicy(sizePolicy)
        self.frame_7.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_7.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame_7)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.frame_6 = QFrame(self.frame_7)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_6.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.frame_6)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label = QLabel(self.frame_6)
        self.label.setObjectName(u"label")

        self.horizontalLayout_7.addWidget(self.label)

        self.comboBox = QComboBox(self.frame_6)
        self.comboBox.setObjectName(u"comboBox")

        self.horizontalLayout_7.addWidget(self.comboBox)

        self.btn_refresh = QPushButton(self.frame_6)
        self.btn_refresh.setObjectName(u"btn_refresh")

        self.horizontalLayout_7.addWidget(self.btn_refresh)

        self.comboBox_2 = QComboBox(self.frame_6)
        self.comboBox_2.setObjectName(u"comboBox_2")

        self.horizontalLayout_7.addWidget(self.comboBox_2)

        self.btnIniciar = QPushButton(self.frame_6)
        self.btnIniciar.setObjectName(u"btnIniciar")

        self.horizontalLayout_7.addWidget(self.btnIniciar)


        self.verticalLayout_3.addWidget(self.frame_6)

        self.textEdit = QTextEdit(self.frame_7)
        self.textEdit.setObjectName(u"textEdit")

        self.verticalLayout_3.addWidget(self.textEdit)

        self.frame_8 = QFrame(self.frame_7)
        self.frame_8.setObjectName(u"frame_8")
        self.frame_8.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_8.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_8 = QHBoxLayout(self.frame_8)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.input_send = QLineEdit(self.frame_8)
        self.input_send.setObjectName(u"input_send")

        self.horizontalLayout_8.addWidget(self.input_send)

        self.pushButton_2 = QPushButton(self.frame_8)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.horizontalLayout_8.addWidget(self.pushButton_2)


        self.verticalLayout_3.addWidget(self.frame_8)

        self.tabWidget.addTab(self.tab_terminal, "")
        self.tab_plots = QWidget()
        self.tab_plots.setObjectName(u"tab_plots")
        self.horizontalLayout_5 = QHBoxLayout(self.tab_plots)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.frame_3 = QFrame(self.tab_plots)
        self.frame_3.setObjectName(u"frame_3")
        sizePolicy.setHeightForWidth(self.frame_3.sizePolicy().hasHeightForWidth())
        self.frame_3.setSizePolicy(sizePolicy)
        self.frame_3.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.frame_3)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.frame_4 = QFrame(self.frame_3)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_4.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.frame_4)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.btnToggleFiles = QToolButton(self.frame_4)
        self.btnToggleFiles.setObjectName(u"btnToggleFiles")
        self.btnToggleFiles.setCheckable(True)
        self.btnToggleFiles.setArrowType(Qt.ArrowType.RightArrow)

        self.horizontalLayout_3.addWidget(self.btnToggleFiles)

        self.btnToggleMath = QToolButton(self.frame_4)
        self.btnToggleMath.setObjectName(u"btnToggleMath")
        self.btnToggleMath.setCheckable(True)
        self.btnToggleMath.setArrowType(Qt.ArrowType.RightArrow)

        self.horizontalLayout_3.addWidget(self.btnToggleMath)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.btnSeleccionarCarpeta = QPushButton(self.frame_4)
        self.btnSeleccionarCarpeta.setObjectName(u"btnSeleccionarCarpeta")

        self.horizontalLayout_3.addWidget(self.btnSeleccionarCarpeta)

        self.btn_grabar = QPushButton(self.frame_4)
        self.btn_grabar.setObjectName(u"btn_grabar")
        self.btn_grabar.setCheckable(True)

        self.horizontalLayout_3.addWidget(self.btn_grabar)

        self.lineEdit_muestras = QLineEdit(self.frame_4)
        self.lineEdit_muestras.setObjectName(u"lineEdit_muestras")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lineEdit_muestras.sizePolicy().hasHeightForWidth())
        self.lineEdit_muestras.setSizePolicy(sizePolicy1)

        self.horizontalLayout_3.addWidget(self.lineEdit_muestras)

        self.btnStop = QPushButton(self.frame_4)
        self.btnStop.setObjectName(u"btnStop")

        self.horizontalLayout_3.addWidget(self.btnStop)


        self.verticalLayout_5.addWidget(self.frame_4)

        self.framePanelArchivos = QFrame(self.frame_3)
        self.framePanelArchivos.setObjectName(u"framePanelArchivos")
        self.framePanelArchivos.setFrameShape(QFrame.Shape.StyledPanel)
        self.framePanelArchivos.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.framePanelArchivos)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.btnCargarArchivo = QPushButton(self.framePanelArchivos)
        self.btnCargarArchivo.setObjectName(u"btnCargarArchivo")

        self.horizontalLayout_6.addWidget(self.btnCargarArchivo)

        self.btnRefrescarArchivos = QPushButton(self.framePanelArchivos)
        self.btnRefrescarArchivos.setObjectName(u"btnRefrescarArchivos")

        self.horizontalLayout_6.addWidget(self.btnRefrescarArchivos)


        self.verticalLayout_5.addWidget(self.framePanelArchivos)

        self.frame_5 = QFrame(self.frame_3)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_5.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.layout_plots = PlotWidget(self.frame_5)
        self.layout_plots.setObjectName(u"layout_plots")
        sizePolicy.setHeightForWidth(self.layout_plots.sizePolicy().hasHeightForWidth())
        self.layout_plots.setSizePolicy(sizePolicy)
        self.verticalLayout_4 = QVBoxLayout(self.layout_plots)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")

        self.horizontalLayout_4.addWidget(self.layout_plots)

        self.framePanelMath = QFrame(self.frame_5)
        self.framePanelMath.setObjectName(u"framePanelMath")
        self.framePanelMath.setFrameShape(QFrame.Shape.StyledPanel)
        self.framePanelMath.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout = QGridLayout(self.framePanelMath)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_2 = QLabel(self.framePanelMath)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.btnMathRestar = QPushButton(self.framePanelMath)
        self.btnMathRestar.setObjectName(u"btnMathRestar")

        self.gridLayout.addWidget(self.btnMathRestar, 0, 1, 1, 1)

        self.btnMathDividir = QPushButton(self.framePanelMath)
        self.btnMathDividir.setObjectName(u"btnMathDividir")

        self.gridLayout.addWidget(self.btnMathDividir, 0, 2, 1, 1)

        self.btnMathMultiplicar = QPushButton(self.framePanelMath)
        self.btnMathMultiplicar.setObjectName(u"btnMathMultiplicar")

        self.gridLayout.addWidget(self.btnMathMultiplicar, 0, 3, 1, 1)

        self.btnMathSumar = QPushButton(self.framePanelMath)
        self.btnMathSumar.setObjectName(u"btnMathSumar")

        self.gridLayout.addWidget(self.btnMathSumar, 0, 0, 1, 1)

        self.lineEditNombreSerie = QLineEdit(self.framePanelMath)
        self.lineEditNombreSerie.setObjectName(u"lineEditNombreSerie")
        self.lineEditNombreSerie.setEnabled(False)
        self.lineEditNombreSerie.setClearButtonEnabled(True)

        self.gridLayout.addWidget(self.lineEditNombreSerie, 1, 1, 1, 1)

        self.btnMathMostrar = QPushButton(self.framePanelMath)
        self.btnMathMostrar.setObjectName(u"btnMathMostrar")
        self.btnMathMostrar.setEnabled(False)

        self.gridLayout.addWidget(self.btnMathMostrar, 2, 0, 1, 1)

        self.btnMathGuardarCSV = QPushButton(self.framePanelMath)
        self.btnMathGuardarCSV.setObjectName(u"btnMathGuardarCSV")
        self.btnMathGuardarCSV.setEnabled(False)

        self.gridLayout.addWidget(self.btnMathGuardarCSV, 2, 1, 1, 1)

        self.btnMathSwap = QPushButton(self.framePanelMath)
        self.btnMathSwap.setObjectName(u"btnMathSwap")
        self.btnMathSwap.setEnabled(False)

        self.gridLayout.addWidget(self.btnMathSwap, 2, 2, 1, 1)

        self.lblMathOperandos = QLabel(self.framePanelMath)
        self.lblMathOperandos.setObjectName(u"lblMathOperandos")
        self.lblMathOperandos.setWordWrap(True)

        self.gridLayout.addWidget(self.lblMathOperandos, 3, 1, 1, 1)


        self.horizontalLayout_4.addWidget(self.framePanelMath)

        self.containerSelector = SeriesSelector(self.frame_5)
        self.containerSelector.setObjectName(u"containerSelector")

        self.horizontalLayout_4.addWidget(self.containerSelector)


        self.verticalLayout_5.addWidget(self.frame_5)


        self.horizontalLayout_5.addWidget(self.frame_3)

        self.tabWidget.addTab(self.tab_plots, "")
        self.curve_editor = QWidget()
        self.curve_editor.setObjectName(u"curve_editor")
        sizePolicy.setHeightForWidth(self.curve_editor.sizePolicy().hasHeightForWidth())
        self.curve_editor.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self.curve_editor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.plot_curva_container = QFrame(self.curve_editor)
        self.plot_curva_container.setObjectName(u"plot_curva_container")
        sizePolicy.setHeightForWidth(self.plot_curva_container.sizePolicy().hasHeightForWidth())
        self.plot_curva_container.setSizePolicy(sizePolicy)
        self.plot_curva_container.setFrameShape(QFrame.Shape.StyledPanel)
        self.plot_curva_container.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.plot_curva_container)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.frame = QFrame(self.plot_curva_container)
        self.frame.setObjectName(u"frame")
        sizePolicy1.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy1)
        self.frame.setMinimumSize(QSize(380, 0))
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tableCurva = QTableWidget(self.frame)
        self.tableCurva.setObjectName(u"tableCurva")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.tableCurva.sizePolicy().hasHeightForWidth())
        self.tableCurva.setSizePolicy(sizePolicy2)
        self.tableCurva.setMinimumSize(QSize(256, 0))
        self.tableCurva.setRowCount(0)
        self.tableCurva.setColumnCount(0)

        self.verticalLayout_2.addWidget(self.tableCurva)

        self.spinBoxCurveID = QSpinBox(self.frame)
        self.spinBoxCurveID.setObjectName(u"spinBoxCurveID")

        self.verticalLayout_2.addWidget(self.spinBoxCurveID)

        self.btnAgregarFila = QPushButton(self.frame)
        self.btnAgregarFila.setObjectName(u"btnAgregarFila")

        self.verticalLayout_2.addWidget(self.btnAgregarFila)

        self.btnEliminarFila = QPushButton(self.frame)
        self.btnEliminarFila.setObjectName(u"btnEliminarFila")

        self.verticalLayout_2.addWidget(self.btnEliminarFila)

        self.btnEnviarCurva = QPushButton(self.frame)
        self.btnEnviarCurva.setObjectName(u"btnEnviarCurva")

        self.verticalLayout_2.addWidget(self.btnEnviarCurva)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)


        self.horizontalLayout.addWidget(self.frame)

        self.curve_plot = PlotWidget(self.plot_curva_container)
        self.curve_plot.setObjectName(u"curve_plot")
        sizePolicy.setHeightForWidth(self.curve_plot.sizePolicy().hasHeightForWidth())
        self.curve_plot.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.curve_plot)


        self.verticalLayout.addWidget(self.plot_curva_container)

        self.tabWidget.addTab(self.curve_editor, "")

        self.verticalLayout_7.addWidget(self.tabWidget)


        self.horizontalLayout_2.addWidget(self.frame_2)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 650, 33))
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
        self.btn_refresh.setText(QCoreApplication.translate("MainWindow", u"Refresh", None))
        self.btnIniciar.setText(QCoreApplication.translate("MainWindow", u"Iniciar", None))
        self.pushButton_2.setText(QCoreApplication.translate("MainWindow", u"Enviar", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_terminal), QCoreApplication.translate("MainWindow", u"Comunicacion", None))
        self.btnToggleFiles.setText(QCoreApplication.translate("MainWindow", u"...", None))
        self.btnToggleMath.setText(QCoreApplication.translate("MainWindow", u"Matematica", None))
        self.btnSeleccionarCarpeta.setText(QCoreApplication.translate("MainWindow", u"Seleccionar carpeta de destino", None))
        self.btn_grabar.setText(QCoreApplication.translate("MainWindow", u"Iniciar grabacion", None))
        self.btnStop.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
        self.btnCargarArchivo.setText(QCoreApplication.translate("MainWindow", u"Cargar CSV", None))
        self.btnRefrescarArchivos.setText(QCoreApplication.translate("MainWindow", u"Refrescar", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Nombre", None))
        self.btnMathRestar.setText(QCoreApplication.translate("MainWindow", u"Restar", None))
        self.btnMathDividir.setText(QCoreApplication.translate("MainWindow", u"Dividir", None))
        self.btnMathMultiplicar.setText(QCoreApplication.translate("MainWindow", u"Multiplicar", None))
        self.btnMathSumar.setText(QCoreApplication.translate("MainWindow", u"Sumar", None))
        self.lineEditNombreSerie.setPlaceholderText(QCoreApplication.translate("MainWindow", u"ej: V(S1000)+V(S1001)", None))
#if QT_CONFIG(tooltip)
        self.btnMathMostrar.setToolTip(QCoreApplication.translate("MainWindow", u"Agregar la serie calculada a \"Series visibles\" y al gr\u00e1fico", None))
#endif // QT_CONFIG(tooltip)
        self.btnMathMostrar.setText(QCoreApplication.translate("MainWindow", u"Guardar", None))
        self.btnMathGuardarCSV.setText(QCoreApplication.translate("MainWindow", u"Guardar CSV", None))
#if QT_CONFIG(tooltip)
        self.btnMathSwap.setToolTip(QCoreApplication.translate("MainWindow", u"Invertir el orden de los operandos (importa en resta y divisi\u00f3n)", None))
#endif // QT_CONFIG(tooltip)
        self.btnMathSwap.setText(QCoreApplication.translate("MainWindow", u"A \u21c4 B", None))
        self.lblMathOperandos.setText(QCoreApplication.translate("MainWindow", u"Operandos: (seleccion\u00e1 hasta 2 series)", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_plots), QCoreApplication.translate("MainWindow", u"Graficos", None))
        self.spinBoxCurveID.setSpecialValueText(QCoreApplication.translate("MainWindow", u"ID (1-99)", None))
        self.btnAgregarFila.setText(QCoreApplication.translate("MainWindow", u"Agregar fila", None))
        self.btnEliminarFila.setText(QCoreApplication.translate("MainWindow", u"Eliminar fila", None))
        self.btnEnviarCurva.setText(QCoreApplication.translate("MainWindow", u"Enviar", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.curve_editor), QCoreApplication.translate("MainWindow", u"Curvas", None))
    # retranslateUi

