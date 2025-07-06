import pyqtgraph as pg
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
import numpy as np

class RMSTrendWindow(QDialog):
    def __init__(self, rms_values, rms_timestamps, mag_values, mag_timestamps, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RMS & Acceleration Magnitude Trend Viewer")
        self.resize(1000, 750)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Plot 1: Raw RMS values
        self.plot_widget_mag = pg.PlotWidget()
        self.plot_widget_mag.setLabel('left', 'RMS Magnitude')
        self.plot_widget_mag.setLabel('bottom', 'Time (minutes)')
        layout.addWidget(QLabel("RMS Magnitude (Raw Values)"))
        layout.addWidget(self.plot_widget_mag)

        # Plot 2: RMS Trend
        self.plot_widget_trend = pg.PlotWidget()
        self.plot_widget_trend.setLabel('left', 'RMS Trend')
        self.plot_widget_trend.setLabel('bottom', 'Time (minutes)')
        self.plot_widget_trend.setXLink(self.plot_widget_mag)
        self.plot_widget_trend.setYLink(self.plot_widget_mag)
        layout.addWidget(QLabel("RMS Trend Line"))
        layout.addWidget(self.plot_widget_trend)

        # Plot 3: Acceleration Magnitude
        self.plot_widget_acc_mag = pg.PlotWidget()
        self.plot_widget_acc_mag.setLabel('left', 'Acceleration Magnitude (g)')
        self.plot_widget_acc_mag.setLabel('bottom', 'Time (minutes)')
        self.plot_widget_acc_mag.setXLink(self.plot_widget_mag)  # ✅ Sync X-axis with other plots
        layout.addWidget(QLabel("Acceleration Magnitude (Whole Magnitude)"))
        layout.addWidget(self.plot_widget_acc_mag)

        # Vertical lines
        self.vline_mag = None
        self.vline_trend = None
        self.vline_acc_mag = None

        # Store data
        self.rms_values = rms_values
        self.rms_timestamps = rms_timestamps
        self.mag_values = mag_values
        self.mag_timestamps = mag_timestamps
        self.minutes = []
        self.mag_minutes = []

        # Connect clicks
        self.plot_widget_mag.scene().sigMouseClicked.connect(self.handle_mag_click)
        self.plot_widget_trend.scene().sigMouseClicked.connect(self.handle_trend_click)
        self.plot_widget_acc_mag.scene().sigMouseClicked.connect(self.handle_acc_mag_click)

        # Plot data
        self.plot_rms_data()
        self.plot_acc_mag_data()

    def plot_rms_data(self):
        if not self.rms_values or not self.rms_timestamps:
            return

        t0 = self.rms_timestamps[0]
        self.minutes = [(ts - t0).total_seconds() / 60.0 for ts in self.rms_timestamps]

        self.plot_widget_mag.clear()
        self.plot_widget_trend.clear()

        # Raw RMS
        self.plot_widget_mag.plot(
            self.minutes,
            self.rms_values,
            pen=pg.mkPen('b', width=1)
        )

        # RMS Trend (Moving average)
        if len(self.rms_values) >= 5:
            window = 20
            weights = np.ones(window) / window
            smoothed = np.convolve(self.rms_values, weights, mode='valid')
            smoothed_x = self.minutes[window - 1:]

            self.plot_widget_trend.plot(
                smoothed_x,
                smoothed,
                pen=pg.mkPen('g', width=1)
            )

    def plot_acc_mag_data(self):
        if not self.mag_values or not self.mag_timestamps:
            return

        t0 = self.mag_timestamps[0]
        self.mag_minutes = [(ts - t0).total_seconds() / 60.0 for ts in self.mag_timestamps]

        self.plot_widget_acc_mag.clear()

        self.plot_widget_acc_mag.plot(
            self.mag_minutes,
            self.mag_values,
            pen=pg.mkPen('y', width=1)
        )

    def draw_vertical_lines(self, x_val):
        if self.vline_mag:
            self.plot_widget_mag.removeItem(self.vline_mag)
        if self.vline_trend:
            self.plot_widget_trend.removeItem(self.vline_trend)
        if self.vline_acc_mag:
            self.plot_widget_acc_mag.removeItem(self.vline_acc_mag)

        self.vline_mag = pg.InfiniteLine(pos=x_val, angle=90, pen=pg.mkPen('r', width=1))
        self.vline_trend = pg.InfiniteLine(pos=x_val, angle=90, pen=pg.mkPen('r', width=1))
        self.vline_acc_mag = pg.InfiniteLine(pos=x_val, angle=90, pen=pg.mkPen('r', width=1))

        self.plot_widget_mag.addItem(self.vline_mag)
        self.plot_widget_trend.addItem(self.vline_trend)
        self.plot_widget_acc_mag.addItem(self.vline_acc_mag)

    def handle_mag_click(self, event):
        pos = event.scenePos()
        vb = self.plot_widget_mag.getViewBox()
        if vb.sceneBoundingRect().contains(pos):
            mouse_point = vb.mapSceneToView(pos)
            self.draw_vertical_lines(mouse_point.x())

    def handle_trend_click(self, event):
        pos = event.scenePos()
        vb = self.plot_widget_trend.getViewBox()
        if vb.sceneBoundingRect().contains(pos):
            mouse_point = vb.mapSceneToView(pos)
            self.draw_vertical_lines(mouse_point.x())

    def handle_acc_mag_click(self, event):
        pos = event.scenePos()
        vb = self.plot_widget_acc_mag.getViewBox()
        if vb.sceneBoundingRect().contains(pos):
            mouse_point = vb.mapSceneToView(pos)
            self.draw_vertical_lines(mouse_point.x())
