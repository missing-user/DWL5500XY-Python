[![Upload Python Package](https://github.com/missing-user/py-DWL5500XY/actions/workflows/python-publish.yml/badge.svg)](https://github.com/missing-user/py-DWL5500XY/actions/workflows/python-publish.yml)
# Description
Python library and a small recording script for the [Digipass DWL5500XY inclinometer](https://www.digipas.com/product/precision-measurement/2-axis-inclination-sensor-module/dwl-5500xy.php), which fixes a few minor in [Stormholt's implementation](https://github.com/Stormholt/DWL5500XY-Python). 
For further details regarding the sensor, please read the [instruction manual](https://www.digipas.com/documents/DWL-5x000%20Instruction%20Manual-rev.2.4.12.pdf). 

The DWL5500-XY is an inclinometer (sensor that measures the angle against gravity) with an accuracy and precision of 0.001 deg. It internally uses a high precision accelerometer and therefore uses strong filtering to get rid of the noise. Measurements therefore need some time to settle (up to 5 minutes after sharp movements. Settling time is lower for small movements).

# Installation
> [!IMPORTANT]
> Both the libraries `serial` and `pyserial` can be imported as `import serial`. This module expects a `pyserial` installation, and will not work with the incorrect library!
```sh
git clone https://github.com/missing-user/py-DWL5500XY.git
pip install py-DWL5500XY
```
# Quickstart
1. Place the sensor according to one of the graphics below. Dual axis angle measurement is only available when oriented as in Figure 32 ![Graphic about mounting styles from the instruction manual](docs/angle_measurement_modes.png)
2. Let the sensor warm up and settle in for 15 minutes after connecting it to power to get the full measurement accuracy.
3. Run `python inclinometer_gui.py` from your terminal to open the recording tool.
4. It will ask you for the serial port your device is connected to. Type it into the terminal and press enter.
# Usage
1. Open the serial connection. On Windows you can find the port by opening `Windows Key > Device Manager > COM Devices` and identifying the COM port that appears when plugging in the USB to serial converter of your sensor. On Linux, you can list connected serial devices using `ls /sys/class/tty/ttyUSB*`. Replace the port name in the code by the one you identified. ![windows screenshot](docs/Windows10USB.png)
  ```python
  import os
  import DWL5500XY
  sc = DWL5500XY.Sensor(True) # The argument controls Logging level
  if os.name == 'nt':
    sc.open_connection("COM5") # Windows style serial port
  else:
    sc.open_connection('/dev/ttyUSB0') # Linux style serial port
  ```
2. Initialize the sensor and set the location you are operating in (county codes can be found starting on page 60 of the instruction manual). The location dependent gravitational acceleration constant `g` is internally used for filtering. 
  ```python
  sc.initialize_sensor()
  sc.set_location_code(0x17, 0x0E) # Germany, Munich
  sc.set_mode(sc.LOCATION_MODE) # Call after setting the location code
  ```
3. Switch the sensor into the correct measurement mode. It supports dual axis angle measurement (in degrees) (default), single axis angle measurement (in degrees), vibration measurement (in multiples of g).
  ```python
  sc.set_mode(sc.DUAL_MODE)
  # sc.set_mode(sc.SINGLE_MODE)
  # sc.set_mode(sc.VIBRO_MODE)
  ```
4. Periodically read data from the sensor.
  ```python
  sc.read_response() # Blocking function, sensor returns measurements at a rate of 10Hz 
  ```
# Re-Calibration
Connect to the sensor as usual, then call `sc.calibration()` and follow the instructions from the terminal.
> [!CAUTION]
> ***Calling the calibration function will overwrite the factory settings!***
>
> If you have purchased a new DWL5500XY sensor, i suggest to **NOT PERFORM A NEW CALIBRATION**! The sensor should be calibrated at the factory, and will most probably be better than what you can achieve, unless you really know what you're doing. You have been warned.
