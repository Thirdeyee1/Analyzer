import pyqtgraph as pg
import csv
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QPushButton, QFileDialog, QMessageBox
from datetime import datetime
from collections import deque
from rms_plot_widget import RMSPlotWidget
from rms_trend_window import RMSTrendWindow


class CombinedPlotWidget(QtWidgets.QWidget):
    def __init__(self, buffer_size=500, rms_values=None, rms_timestamps=None):
        super().__init__()

        self.buffer_size = buffer_size
        self.rms_values = rms_values or []
        self.rms_timestamps = rms_timestamps or []
        self.is_paused = False

        self.peak_magnitude = 0.0
        self.peak_timestamp = None
        self.peak_axis = ""

        self.threshold_factor = 2.0
        self.warning_active = False
        self.warning_start_time = None
        self.warning_last_time = None
        self.warning_count = 0

        self.xData = deque([0] * buffer_size, maxlen=buffer_size)
        self.yData = deque([0] * buffer_size, maxlen=buffer_size)
        self.zData = deque([0] * buffer_size, maxlen=buffer_size)
        self.magData = deque([0] * buffer_size, maxlen=buffer_size)

        self.mag_values_full = []
        self.mag_timestamps_full = []

        outerLayout = QtWidgets.QHBoxLayout()
        self.setLayout(outerLayout)

        plotStack = QtWidgets.QVBoxLayout()

        # X/Y/Z Plot
        self.xyzPlotWidget = pg.GraphicsLayoutWidget()
        self.xyzPlot = self.xyzPlotWidget.addPlot(title="Acceleration (g)")
        self.xyzPlot.setXRange(0, buffer_size, padding=0)
        self.xyzPlot.getViewBox().setLimits(xMin=0, xMax=buffer_size, maxXRange=buffer_size)
        self.xCurve = self.xyzPlot.plot(pen='r', name='X')
        self.yCurve = self.xyzPlot.plot(pen='g', name='Y')
        self.zCurve = self.xyzPlot.plot(pen='b', name='Z')
        plotStack.addWidget(self.xyzPlotWidget, stretch=1)

        # Magnitude Plot
        self.magPlotWidget = pg.GraphicsLayoutWidget()
        self.magPlot = self.magPlotWidget.addPlot(title="Acceleration Magnitude (g)")
        self.magPlot.setLabel('left', 'Magnitude')
        self.magPlot.setLabel('bottom', 'Sample')
        self.magPlot.setXRange(0, buffer_size, padding=0)
        self.magPlot.getViewBox().setLimits(xMin=0, xMax=buffer_size, maxXRange=buffer_size)
        self.magCurve = self.magPlot.plot(pen='y', name='|a|')
        plotStack.addWidget(self.magPlotWidget, stretch=1)

        # RMS Plot (Separate QWidget)
        self.rmsWidget = RMSPlotWidget(window_size=1000)
        plotStack.addWidget(self.rmsWidget, stretch=1)

        outerLayout.addLayout(plotStack, stretch=5)

        controlPanel = QtWidgets.QVBoxLayout()
        self.xCheck = QtWidgets.QCheckBox("X 🟥")
        self.yCheck = QtWidgets.QCheckBox("Y 🟩")
        self.zCheck = QtWidgets.QCheckBox("Z 🟦")
        for cb in [self.xCheck, self.yCheck, self.zCheck]:
            cb.setChecked(True)
            controlPanel.addWidget(cb)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setCheckable(True)
        self.pause_btn.toggled.connect(self.toggle_pause)
        controlPanel.addWidget(self.pause_btn)

        self.threshold_btn = QPushButton("Set Threshold")
        self.threshold_btn.clicked.connect(self.set_threshold)
        controlPanel.addWidget(self.threshold_btn)

        self.export_button = QPushButton("Export RMS")
        self.export_button.clicked.connect(self.export_rms_data)
        controlPanel.addWidget(self.export_button)

        self.trend_button = QPushButton("Show RMS Trend")
        self.trend_button.clicked.connect(self.show_rms_trend)
        controlPanel.addWidget(self.trend_button)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximum(18000)
        controlPanel.addWidget(self.progress_bar)

        self.peak_label = QtWidgets.QLabel("📈 Peak Acceleration:\n0.000 g\n@ --")
        controlPanel.addWidget(self.peak_label)

        self.threshold_summary_label = QtWidgets.QLabel("⚠️ No active threshold warnings.")
        controlPanel.addWidget(self.threshold_summary_label)

        controlPanel.addStretch()
        outerLayout.addLayout(controlPanel, stretch=1)

        self.plot_timer = QtCore.QTimer()
        self.plot_timer.timeout.connect(self.redraw_plots)
        self.plot_timer.start(100)

    def update_data(self, ax, ay, az):
        if self.is_paused:
            return

        self.xData.append(ax)
        self.yData.append(ay)
        self.zData.append(az)
        mag = (ax ** 2 + ay ** 2 + az ** 2) ** 0.5
        self.magData.append(mag)

        self.mag_values_full.append(mag)
        self.mag_timestamps_full.append(datetime.now())

        self.rmsWidget.update(mag)
        self.check_peak(ax, ay, az, mag)
        self.check_rms_threshold()
        self.update_rms_progress()

    def redraw_plots(self):
        xVals = list(range(len(self.xData)))
        self.xCurve.setData(xVals, list(self.xData) if self.xCheck.isChecked() else [])
        self.yCurve.setData(xVals, list(self.yData) if self.yCheck.isChecked() else [])
        self.zCurve.setData(xVals, list(self.zData) if self.zCheck.isChecked() else [])
        self.magCurve.setData(xVals, list(self.magData))

    def check_peak(self, ax, ay, az, mag):
        max_axis_val = max(abs(ax), abs(ay), abs(az))
        if mag > self.peak_magnitude:
            self.peak_axis = "X" if abs(ax) == max_axis_val else "Y" if abs(ay) == max_axis_val else "Z"
            self.peak_magnitude = mag
            self.peak_timestamp = datetime.now()
            formatted_time = self.peak_timestamp.strftime('%d-%b-%y %H:%M:%S.%f')[:-3]
            self.peak_label.setText(f"📈 Peak Acceleration: {self.peak_magnitude:.3f} g\n@ {formatted_time}")

    def check_rms_threshold(self):
        if len(self.rms_values) < 1:
            return

        now = datetime.now()
        latest_rms = self.rms_values[-1]

        if latest_rms > self.threshold_factor:
            if not self.warning_active:
                self.warning_active = True
                self.warning_start_time = now
                self.warning_last_time = now
                self.warning_count = 1
            else:
                time_since_last = (now - self.warning_last_time).total_seconds()
                if time_since_last >= 300:
                    self.warning_start_time = now
                    self.warning_last_time = now
                    self.warning_count = 1
                else:
                    self.warning_count += 1
                    self.warning_last_time = now
        else:
            if self.warning_active:
                time_since_last = (now - self.warning_last_time).total_seconds()
                if time_since_last >= 300:
                    self.warning_active = False
                    self.warning_start_time = None
                    self.warning_last_time = None
                    self.warning_count = 0

        self.update_threshold_summary()

    def update_threshold_summary(self):
        if self.warning_active:
            start_str = self.warning_start_time.strftime('%d-%b-%y %H:%M:%S')
            last_str = self.warning_last_time.strftime('%d-%b-%y %H:%M:%S')
            summary = (
                f"⚠️ Threshold Exceeded:\n"
                f"First: {start_str}\n"
                f"Last: {last_str}\n"
                f"Total: {self.warning_count} times"
            )
        else:
            summary = "⚠️ No active threshold warnings."
        self.threshold_summary_label.setText(summary)

    def toggle_pause(self, checked):
        self.is_paused = checked
        self.pause_btn.setText("Resume" if checked else "Pause")

    def set_threshold(self):
        new_threshold, ok = QtWidgets.QInputDialog.getDouble(
            self, "Set RMS Threshold", "Enter new RMS threshold value:",
            self.threshold_factor, 0.0001, 10000.0, decimals=4
        )
        if ok:
            self.threshold_factor = new_threshold

    def export_rms_data(self):
        if not self.rms_values or not self.rms_timestamps:
            QMessageBox.warning(self, "Export Error", "No RMS data to export.")
            return

        path = "C:/Users/Thirdy/Desktop/RMS trend data"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{path}/RMS_Export_{timestamp}.csv"

        try:
            with open(filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Timestamp', 'RMS Value'])
                for ts, rms in zip(self.rms_timestamps, self.rms_values):
                    writer.writerow([ts.strftime('%Y-%m-%d %H:%M:%S.%f'), rms])
            print(f"✅ RMS data exported to: {filename}")
        except Exception as e:
            print(f"❌ Error saving RMS data: {e}")

    def update_rms_progress(self):
        self.progress_bar.setValue(min(len(self.rms_values), self.progress_bar.maximum()))

    def show_rms_trend(self):
        if len(self.rms_values) < 1 or len(self.mag_values_full) < 1:
            QMessageBox.warning(self, "Data Missing", "Collect more data first.")
            return

        self.trend_window = RMSTrendWindow(
            self.rms_values,
            self.rms_timestamps,
            self.mag_values_full,
            self.mag_timestamps_full
        )
        self.trend_window.exec_()
