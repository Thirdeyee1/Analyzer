# plot_xyz_widget.py
import pyqtgraph as pg
from PyQt5 import QtWidgets

class XYZPlotWidget(QtWidgets.QWidget):
    def __init__(self, buffer_size=500):
        super().__init__()

        self.buffer_size = buffer_size
        self.xData = [0] * buffer_size
        self.yData = [0] * buffer_size
        self.zData = [0] * buffer_size

        # Main horizontal layout
        mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(mainLayout)

        # Plot widget
        self.plotWidget = pg.GraphicsLayoutWidget()
        self.plot = self.plotWidget.addPlot(title="Acceleration (g)")
        self.plot.addLegend()
        self.plot.setXRange(0, buffer_size, padding=0)

        # ✅ Properly restrict zoom-out/pan limits on x-axis
        self.plot.getViewBox().setLimits(xMin=0, xMax=buffer_size, maxXRange=buffer_size)

        mainLayout.addWidget(self.plotWidget, stretch=4)

        # Right-side checkbox layout
        rightPanel = QtWidgets.QVBoxLayout()
        self.xCheck = QtWidgets.QCheckBox("X")
        self.yCheck = QtWidgets.QCheckBox("Y")
        self.zCheck = QtWidgets.QCheckBox("Z")

        for cb in [self.xCheck, self.yCheck, self.zCheck]:
            cb.setChecked(True)
            rightPanel.addWidget(cb)

        rightPanel.addStretch()
        mainLayout.addLayout(rightPanel, stretch=1)

        # Plot curves
        self.xCurve = self.plot.plot(self.xData, pen='r', name='X')
        self.yCurve = self.plot.plot(self.yData, pen='g', name='Y')
        self.zCurve = self.plot.plot(self.zData, pen='b', name='Z')

    def update_data(self, ax, ay, az):
        self.xData = self.xData[1:] + [ax]
        self.yData = self.yData[1:] + [ay]
        self.zData = self.zData[1:] + [az]

        xVals = list(range(len(self.xData)))

        if self.xCheck.isChecked():
            self.xCurve.setData(xVals, self.xData)
        else:
            self.xCurve.setData([], [])

        if self.yCheck.isChecked():
            self.yCurve.setData(xVals, self.yData)
        else:
            self.yCurve.setData([], [])

        if self.zCheck.isChecked():
            self.zCurve.setData(xVals, self.zData)
        else:
            self.zCurve.setData([], [])

    def show(self):
        super().show()
        self.setWindowTitle("Real-Time XYZ Acceleration")
        self.resize(1000, 600)
