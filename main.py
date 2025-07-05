
import socket
import sys
import cbor2
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QSizePolicy, QSpacerItem, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

import numpy as np
from collections import deque
import pyqtgraph as pg

from ppg.dataTools import movingAverage
from ppg.ppgPy import ppgPy

# Constants
IP = '0.0.0.0'
PORT = 5004
WINDOWSIZE = 3
MAXDATASIZE = 500

class PPGMonitoring(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initSocket()
        self.rawData = np.zeros(MAXDATASIZE)
        self.timeData = deque(maxlen=MAXDATASIZE)
        self.irData1 = deque(maxlen=MAXDATASIZE)
        self.irData2 = deque(maxlen=MAXDATASIZE)
        #self.redData = deque(maxlen=MAXDATASIZE)
        self.measures = {}
        self.isRunning =  False

    def initUI(self):
        self.setWindowTitle("PPG Monitoring")
        self.setGeometry(100, 100, 720, 1280)

        self.setStyleSheet("""
            QWidget {
                background-color: #FAFAFA;
                color: #FFFFFF;
            }
            QLabel {
                color: #0784B5;
                background-color: #D2D3DB;
                padding: 10px;
                border: 2px solid #0784B5;
                border-radius: 10px;
            }
            QPushButton {
                color: #FFFFFF;
                background-color: #0784B5;
                padding: 10px;
                border: 2px solid #0784B5;
                border-radius: 10px;
            }
            QMainWindow {
                background-color: #FAFAFA;
            }
            PlotWidget {
                background-color: #D2D3DB;
            }
        """)

        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)

        layout = QVBoxLayout()
        centralWidget.setLayout(layout)

        pg.setConfigOptions(useOpenGL=True, antialias=False)
        
        self.rawPlot = pg.PlotWidget(title="PPG Signal")
        layout.addWidget(self.rawPlot)
        
        self.rawCurve = self.rawPlot.plot(pen=(7,132,181))
        self.rawPlot.addLegend()
        self.rawPlot.setYRange(0, 3.3)
        self.rawPlot.setXRange(0, MAXDATASIZE)
        self.rawPlot.setBackground((210, 211, 219))
        self.rawPlot.enableAutoRange('xy', False)
        self.rawPlot.setMinimumHeight(250)
        self.rawPlot.setMaximumHeight(250)
        self.rawPlot.plotItem.hideButtons()
        self.rawPlot.plotItem.setMenuEnabled(False)
        self.rawPlot.getPlotItem().hideAxis('bottom')
        self.rawPlot.getPlotItem().hideAxis('left')
        self.rawPlot.getViewBox().setMouseEnabled(x=False, y=False)

        self.line = pg.InfiniteLine(pos=1024, angle=0, pen=(7,132,181))
        self.rawPlot.addItem(self.line)

        self.rawPlot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.rawPlot, stretch=1)

        labelsLayout = QVBoxLayout()

        self.bpmLabel = QLabel('Heart Rate : n/a')
        self.rpmLabel = QLabel('Breathing Rate : n/a')

        self.customizeLabel(self.bpmLabel)
        self.customizeLabel(self.rpmLabel)

        labelsLayout.addWidget(self.bpmLabel, stretch=1)
        labelsLayout.addWidget(self.rpmLabel, stretch=1)
        labelsLayout.addWidget(self.spo2Label, stretch=1)
        layout.addLayout(labelsLayout, stretch=1)
        self.bpmLabel.setMinimumHeight(50)
        self.bpmLabel.setMaximumHeight(50)
        self.rpmLabel.setMinimumHeight(50)
        self.rpmLabel.setMaximumHeight(50)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addSpacerItem(spacer)

        self.toggleButton = QPushButton("Start Measuring")
        self.toggleButton.clicked.connect(self.toggleUpdate)
        self.customizeButton(self.toggleButton)
        layout.addWidget(self.toggleButton, stretch=1)
        self.toggleButton.setMinimumHeight(50)
        self.toggleButton.setMaximumHeight(50)

        self.timerGraph = QTimer(self)
        self.timerGraph.timeout.connect(self.update)

        self.timerMeasures = QTimer(self)
        self.timerMeasures.timeout.connect(self.updateMeasures)
    
    def customizeButton(self, button):
        font = QFont("Arial", 16, QFont.Bold)
        button.setFont(font)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def customizeLabel(self, label):
        font = QFont("Arial", 12, QFont.Bold)
        label.setFont(font)
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def initSocket(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((IP, PORT))
        except OSError:
            pass

    def update(self):
        rawCapture = []
        for _ in range(WINDOWSIZE):
            try:
                data = self.sock.recv(1024)
            except OSError:
                pass
            decodedData = cbor2.loads(data)
            self.timeData.append(decodedData[0])
            self.irData1.append(decodedData[1])
            self.irData2.append(decodedData[2])
            rawCapture.append(decodedData[1])
            if len(rawCapture) == WINDOWSIZE:
                rawCapture = movingAverage(rawCapture, 60, windowSize=1).tolist()

        self.rawData = np.concatenate([self.rawData, rawCapture])

        if len(self.rawData) > MAXDATASIZE:
            self.rawData = self.rawData[WINDOWSIZE:]

        self.rawCurve.setData(self.rawData)

    def updateMeasures(self):
        if len(self.timeData) == 500:
            try:
                self.measures = ppgPy(self.irData1, self.irData2, self.timeData)
                if self.measures:
                    self.bpmLabel.setText("Heart Rate : " + str(self.measures['bpm']) + " BPM")
                    self.rpmLabel.setText("Breathing Rate : " + str(self.measures['breathingrate']) + " RPM")
            except:
                pass
    
    def toggleUpdate(self):
        if self.isRunning:
            self.timerGraph.stop()
            self.timerMeasures.stop()
            self.sock.close()
            self.resetGraphAndLabels()
            self.toggleButton.setText("Start Measuring")
        else:
            self.initSocket()
            self.timerGraph.start(0)
            self.timerMeasures.start(10)
            self.toggleButton.setText("Stop Measuring")
        self.isRunning = not self.isRunning
    
    def resetGraphAndLabels(self):
        self.rawData = np.zeros(MAXDATASIZE)
        self.rawCurve.setData(self.rawData)
        
        self.bpmLabel.setText("BPM: n/a")
        self.rpmLabel.setText("RPM: n/a")

    def closeEvent(self, event):
        self.sock.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ppgMonitoring = PPGMonitoring()
    ppgMonitoring.show()
    sys.exit(app.exec_())