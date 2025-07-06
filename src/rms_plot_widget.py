# rms_plot_widget.py
import pyqtgraph as pg
from PyQt5 import QtWidgets
import math

class RMSPlotWidget(QtWidgets.QWidget):
    def __init__(self, window_size=500):
        super().__init__()

        self.window_size = window_size
        self.magBuffer = [0.0] * window_size
        self.rmsData = [0.0] * 1000  # Plot history

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.plotWidget = pg.GraphicsLayoutWidget()
        self.plot = self.plotWidget.addPlot(title="RMS Magnitude")
        self.plot.setLabel('left', 'RMS')
        self.plot.setLabel('bottom', 'Time')
        self.plot.setXRange(0, 1000, padding=0)
        self.plot.getViewBox().setLimits(xMin=0, xMax=1000, maxXRange=500)

        self.rmsCurve = self.plot.plot(self.rmsData, pen='m')
        layout.addWidget(self.plotWidget)

    def update(self, mag):
        # Update buffer
        self.magBuffer = self.magBuffer[1:] + [mag]

        # Compute RMS
        rms = math.sqrt(sum(x**2 for x in self.magBuffer) / self.window_size)

        # Append to plot history
        self.rmsData = self.rmsData[1:] + [rms]

        # Update plot
        self.rmsCurve.setData(list(range(len(self.rmsData))), self.rmsData)
