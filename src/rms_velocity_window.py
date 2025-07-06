import sys
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

class RMSVelocityWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Real-Time RMS Velocity Plot (ISO 10816)")
        self.resize(800, 400)

        layout = QtWidgets.QVBoxLayout(self)
        self.plot_widget = pg.PlotWidget(title="RMS Velocity (mm/s) - ISO 10816 Zones")
        layout.addWidget(self.plot_widget)

        self.plot = self.plot_widget.plot(pen=pg.mkPen('b', width=2))
        self.rms_data = []

        self.setup_threshold_zones()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(500)  # Update every 500ms

    def setup_threshold_zones(self):
        # ISO 10816 RMS Velocity Zones in mm/s
        zone_a = pg.LinearRegionItem(values=(0, 0.71), brush=(0, 255, 0, 50))  # Good
        zone_b = pg.LinearRegionItem(values=(0.71, 1.8), brush=(255, 255, 0, 50))  # Satisfactory
        zone_c = pg.LinearRegionItem(values=(1.8, 4.5), brush=(255, 165, 0, 50))  # Unsatisfactory
        zone_d = pg.LinearRegionItem(values=(4.5, 10), brush=(255, 0, 0, 50))  # Unacceptable

        for zone in [zone_a, zone_b, zone_c, zone_d]:
            zone.setMovable(False)
            self.plot_widget.addItem(zone)

        self.plot_widget.setYRange(0, 6)

    def simulate_acceleration_data(self, num_points=500, fs=1000):
        """Simulate random acceleration data with vibration"""
        t = np.arange(num_points) / fs
        freq = 50  # Simulated vibration frequency in Hz
        accel = 0.5 * np.sin(2 * np.pi * freq * t) + 0.05 * np.random.randn(num_points)
        return accel, fs

    def compute_rms_velocity(self, accel_data, fs):
        dt = 1.0 / fs
        velocity_data = np.cumsum(accel_data) * dt
        velocity_data -= np.mean(velocity_data)  # Remove drift
        rms_velocity = np.sqrt(np.mean(velocity_data ** 2)) * 1000  # mm/s
        return rms_velocity

    def update_plot(self):
        accel_data, fs = self.simulate_acceleration_data()
        rms_velocity = self.compute_rms_velocity(accel_data, fs)
        
        self.rms_data.append(rms_velocity)
        if len(self.rms_data) > 100:
            self.rms_data = self.rms_data[-100:]

        self.plot.setData(self.rms_data)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = RMSVelocityWindow()
    window.show()
    sys.exit(app.exec_())
