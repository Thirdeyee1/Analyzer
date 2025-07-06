import serial
import sys
import math
from datetime import datetime
from PyQt5 import QtWidgets, QtCore
from combined_plot_widget import CombinedPlotWidget

PORT = 'COM5'
BAUD = 1000000

ser = serial.Serial(PORT, BAUD, timeout=1)

app = QtWidgets.QApplication(sys.argv)

mag_buffer = []

# ✅ No need to pass rms_values or rms_timestamps
combined_widget = CombinedPlotWidget(buffer_size=500)
combined_widget.show()

def update():
    if combined_widget.is_paused:
        return

    while ser.in_waiting:
        try:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) != 4:
                continue

            ax, ay, az = map(float, parts[:3])
            combined_widget.update_data(ax, ay, az)

            mag = math.sqrt(ax**2 + ay**2 + az**2)
            mag_buffer.append(mag)
            if len(mag_buffer) > 1000:
                mag_buffer.pop(0)

            if len(mag_buffer) >= 10:
                rms = math.sqrt(sum(m**2 for m in mag_buffer) / len(mag_buffer))

                # ✅ Store directly in the widget's internal lists
                combined_widget.rms_values.append(rms)
                combined_widget.rms_timestamps.append(datetime.now())
                combined_widget.update_rms_progress()

        except Exception as e:
            print("Error:", e)


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(10)

if __name__ == '__main__':
    sys.exit(app.exec_())
