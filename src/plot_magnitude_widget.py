# plot_magnitude_widget.py
import pyqtgraph as pg
from PyQt5 import QtWidgets

class MagnitudePlotWidget(QtWidgets.QWidget):
    def __init__(self, buffer_size=500):
        super().__init__()

        self.buffer_size = buffer_size
        self.magData = [0] * buffer_size

        # Layout
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # Plot
        self.plotWidget = pg.GraphicsLayoutWidget()
        self.plot = self.plotWidget.addPlot(title="Acceleration Magnitude (g)")
        self.plot.setLabel('left', 'Magnitude')
        self.plot.setLabel('bottom', 'Sample')
        self.plot.setXRange(0, buffer_size, padding=0)
        self.plot.getViewBox().setLimits(xMin=0, xMax=buffer_size, maxXRange=buffer_size)
        layout.addWidget(self.plotWidget)

        self.magCurve = self.plot.plot(self.magData, pen='y', name='|a|')

    def update_data(self, ax, ay, az):
        mag = (ax**2 + ay**2 + az**2) ** 0.5
        self.magData = self.magData[1:] + [mag]
        xVals = list(range(len(self.magData)))
        self.magCurve.setData(xVals, self.magData)

    def show(self):
        super().show()
        self.setWindowTitle("Real-Time Acceleration Magnitude")
        self.resize(1000, 300)
