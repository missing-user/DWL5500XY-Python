import os
import csv
import datetime
import DWL5500XY
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons
import matplotlib
import time
import sys

matplotlib.use("tkAgg")

# set the port name
portname = input("Enter the serial port name that the sensor is connected to (e.g. COM5):")
sc = DWL5500XY.TiltSensor(True)
sc.open_connection(portname)

sc.initialize_sensor()
sc.set_location_code(0x17, 0x0E)
sc.set_mode(sc.LOCATION_MODE)
sc.set_mode(sc.DUAL_MODE)
sc.reset_alternate_zero_dualaxis()

if sc.conn == None:
    print("Could not connect to sensor. Ensure the Serial port is correct.")
    exit(2)

plot_window = 600
# create buffer for plotting two values
x_var = np.zeros([plot_window])
y_var = np.zeros([plot_window])
g_var = np.zeros([plot_window])

plt.ion()
fig, ax = plt.subplots()
xline, = ax.step(list(range(plot_window)), x_var)
yline, = ax.step(list(range(plot_window)), y_var)


# y axis label in degrees
ax.set_ylabel('Angle [$^\circ$]')
ax.set_xlabel('Sample Number [$0.1 s$]')
ax.set_title("XY Inclination")

def reset_zero(event):
    print("Setting alternate zero for DUAL_MODE\n")
    sc.set_alternate_zero_dualaxis()

axnext = plt.axes([0.85, 0.9, 0.1, 0.05])
bnext = Button(axnext, 'Set Zero')
bnext.on_clicked(reset_zero)

def toggle_mode(e):
    if e == "Inclination":
        sc.set_mode(sc.DUAL_MODE)
        ax.legend(["x [$^\circ$]", "y [$^\circ$]"])
    else:
        sc.set_mode(sc.VIBRO)
        ax.legend(["vibration [$g$]"])

axtoggle = plt.axes([0.7, 0.9, 0.1, 0.08])
btggl = RadioButtons(axtoggle, ['Inclination', 'Vibration'])
btggl.on_clicked(toggle_mode)
toggle_mode("Inclination")

ax.grid(True, which='major', axis='y')
ax.grid(True, which='minor', axis='y', alpha=0.2)

fps = 0
fps_text = axnext.text(0, 1.1, "FPS:"+str(fps), fontsize=12)

def update_plot(x, y):
    xline.set_ydata(x[-plot_window:])
    yline.set_ydata(y[-plot_window:])

    minimum_limit = 0.001  # the resolution of the sensor

    value_max = max(np.amax(x[-plot_window:]),
                    np.amax(y[-plot_window:]))
    value_min = min(np.amin(x[-plot_window:]),
                    np.amin(y[-plot_window:]))

    ax.set_ylim([value_min-minimum_limit, value_max+minimum_limit])

    fig.canvas.draw()
    fig.canvas.flush_events()

now = datetime.datetime.now()
# Format the date and time as a string
timestamp = now.strftime("%Y%m%d_%H%M%S")

vibration_filename = "vibration_" + timestamp + ".csv"
inclination_filename = "inclination_" + timestamp + ".csv"
print("Saving data to " + vibration_filename + " and " + inclination_filename)

try:
    csv_writer = csv.DictWriter(open(inclination_filename, 'w'), fieldnames=[
                                "x", "y", "time"], lineterminator="\n")
    csv_writer.writeheader()
    csv_writerv = csv.DictWriter(open(vibration_filename, 'w'), fieldnames=[
                                "vibration[g]", "time"], lineterminator="\n")
    csv_writerv.writeheader()
except:
    sys.exit("Could not open the given file.")


fps_timer = time.perf_counter()
while True:
    try:
        fps = 1/(time.perf_counter() - fps_timer)
        fps_timer = time.perf_counter()
        fps_text.set_text("FPS: %.1f" % fps)

        angles = sc.read_response()
        if type(angles) == dict and btggl.value_selected == "Inclination":
            x_var = np.append(x_var, angles["x"])
            y_var = np.append(y_var, angles["y"])
            update_plot(x_var, y_var)
            angles["time"] = time.time()
            csv_writer.writerow(angles)
        elif type(angles) == float and btggl.value_selected == "Vibration":
            g_var = np.append(g_var, angles)
            update_plot(g_var, g_var)
            csv_writerv.writerow({"vibration[g]":angles, "time":time.time()})
        else:
            print("Invalid response from sensor")
            fig.canvas.draw()
            fig.canvas.flush_events()

    except KeyboardInterrupt:
        plt.savefig(inclination_filename.replace(".csv", ".png"))
        matplotlib.use("pgf")
        matplotlib.rcParams.update({
            "pgf.texsystem": "pdflatex",
            'font.family': 'serif',
            'text.usetex': True,
            'pgf.rcfonts': False,
        })
        plt.savefig(inclination_filename.replace(".csv", "")+".pgf")
        plt.close("all")
        exit(0)
