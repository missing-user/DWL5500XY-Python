#!/usr/bin/env python

import serial

class Sensor(object):
    # Constant values
    DEVICE = 0x01
    COMPUTER = 0x06
    SENSOR_CONNECTED_STATUS = 0x55
    EXPECTED_BYTES = 12
# Modes
    SINGLE_MODE = 0x01
    DUAL_MODE = 0x02
    VIBRO_MODE = 0x03
    CALIBRATION_MODE = 0x0B
    ALT_SINGLE_MODE = 0x05
    ALT_DUAL_MODE = 0x06
    LOCATION_MODE = 0x07
# Device mode and stand
    SINGLE_STANDMODE = 0x11
    DUAL_STANDMODE = 0x22
    SINGLEMODE_DUALSTAND = 0x12
    DUALMODE_SINGLESTAND = 0x21
    VIBRO_SINGLE_STANDMODE = 0x13
    VIBRO_DUAL_STANDMORE = 0x23

    SET_ALT_ZERO = 0x6C
    RESET_ALT_ZERO = 0x46

    degree_symbol = str(u"\u00b0")

    def __init__(self, print_response=False):
        # """
        # Constructor. Initializes the serial connection to 'None'
        # """
        self.print_response = print_response
        self.conn = None
        self.country_code = 0x00
        self.city_code = 0x01
        self.single_val = 0.0
        self.alt_single_val = 0.0
        self.dual_xval = 0.0
        self.dual_yval = 0.0
        self.alt_dual_xval = 0.0
        self.alt_dual_yval = 0.0
        self.vibration = 0.0
        self.last_response = [0x00] * self.EXPECTED_BYTES
        self.mode = self.DUAL_MODE

    def open_connection(self, usb_dir):
        ser = serial.Serial(
            # Windows: give COMport number minus one, numbering starts at zero.
            port=usb_dir,
            # Linux: Directory of device like: /dev/ttyUSB0
            baudrate=115200,  # baudrate
            bytesize=serial.EIGHTBITS,  # number of databits
            parity=serial.PARITY_NONE,  # enable parity checking
            stopbits=serial.STOPBITS_ONE,  # number of stopbits
            timeout=10,  # set a timeout value (example only because reset
                                        # takes longer)
            xonxoff=0,  # disable software flow control

            rtscts=0,  # disable RTS/CTS flow control
        )
        self.conn = ser
        self.buf = bytes()
        # self.conn.reset_input_buffer()
        self.conn.reset_output_buffer()

    def initialize_sensor(self):
        # Sensor reset:
        command = [0x00] * self.EXPECTED_BYTES
        command[0] = 0x06
        command[1] = 0x24
        command[2] = 0x00

        # convert list of numbers to bytearray
        command = bytearray(command)
        # send command to the device
        self.conn.write(command)

    def set_location_code(self, country_code, city_code=0x01):
        self.country_code = country_code
        self.city_code = city_code

    def set_mode(self, mode):
        # Sets the mode of the device byt creating a buffer array and sending it to the device.
        self.mode = mode
        if self.mode == self.CALIBRATION_MODE:  # if the mode is calibration the fourth byte has to be 0x0A
            outbuffer = [self.COMPUTER, self.DEVICE, mode, 0x0A,
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        elif self.mode == self.LOCATION_MODE:
            outbuffer = [self.COMPUTER, self.DEVICE, mode, self.country_code, self.city_code,
                         0x00, 0x00, 0x5A, 0x00, 0x00, 0x00, 0x00]
        else:
            outbuffer = [self.COMPUTER, self.DEVICE, mode, 0xAA,
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        outbuffer = bytearray(outbuffer)
        self.conn.write(outbuffer)
        return self.read_response() # Wait until mode has been successfully set and the sensor has responded again

    def read_response(self):
        # Method reads the response of the device and returns either, None and a diagnostic message or a string with the reponse values.
        data = self.conn.readline(self.EXPECTED_BYTES)
        self.buf += data
        # if data is shorter than expected, wait for more data
        if len(self.buf) < self.EXPECTED_BYTES:
            print("Waiting for more data")
            return None
        else:
            # if data is longer than expected, discard the extra data
            # get first 12 bytes, if the message is longer, then remove message from buffer
            message = self.buf[:self.EXPECTED_BYTES]
            self.buf = self.buf[self.EXPECTED_BYTES:]
            return self.parse_response(message)

    def parse_response(self, response)-> (float | dict[str, float]):

        if len(response) == self.EXPECTED_BYTES:
            # Single mode and stand confirmed
            if response[1] == self.SINGLE_STANDMODE and (self.mode == self.SINGLE_MODE or self.mode == self.ALT_SINGLE_MODE):
                self.single_val = (((int)(response[5]) << 24)) + (
                    ((int)(response[4]) << 16)) + ((int)(response[3] << 8) + response[2])
                self.single_val = ((float)(
                    self.single_val - 18000000)) / 100000

                if self.mode == self.ALT_SINGLE_MODE:
                    if self.print_response:
                        print("{:.3f}".format(self.single_val +
                                              ((-1)*self.alt_single_val)) + self.degree_symbol)
                    return self.single_val - self.alt_single_val
                else:
                    if self.print_response:
                        print("{:.3f}".format(self.single_val) +
                              self.degree_symbol)
                    return self.single_val

            elif (response[1] == self.DUAL_STANDMODE or response[1] == self.DUALMODE_SINGLESTAND) and (self.mode == self.DUAL_MODE or self.mode == self.ALT_DUAL_MODE):
                self.dual_xval = (
                    ((int)(response[7]) << 16)) + ((int)(response[6] << 8) + response[5])
                self.dual_xval = ((float)(self.dual_xval - 3000000)) / 100000

                self.dual_yval = (
                    ((int)(response[4]) << 16)) + ((int)(response[3] << 8) + response[2])
                self.dual_yval = ((float)(self.dual_yval - 3000000)) / 100000
                if self.mode == self.ALT_DUAL_MODE:
                    if self.print_response:
                        print("X" + "{:.4f}".format(self.dual_xval + ((-1) * self.alt_dual_xval)) + self.degree_symbol +
                              " Y" + "{:.4f}".format(self.dual_yval + ((-1) * self.alt_dual_yval)) + self.degree_symbol)
                    return {"x": (self.dual_xval - self.alt_dual_xval), "y": (self.dual_yval - self.alt_dual_yval)}
                else:
                    if self.print_response:
                        print("X" + "{:.4f}".format(self.dual_xval) + self.degree_symbol +
                              " Y" + "{:.4f}".format(self.dual_yval) + self.degree_symbol)
                    return {"x": (self.dual_xval), "y": (self.dual_yval)}

            # Vibration stand and mode
            elif (response[1] == self.VIBRO_SINGLE_STANDMODE or response[1] == self.VIBRO_DUAL_STANDMORE) and self.mode == self.VIBRO_MODE:
                self.vibration = (((float)((((int)(response[5] << 24)) + ((int)(response[4] << 16)) +
                                            ((int)(response[3] << 8)) + response[2])-250000))/100000)

                if self.print_response:
                    print("{:.5f}".format(self.vibration) + "g")
                return self.vibration

            elif response[1] == self.SINGLEMODE_DUALSTAND and self.mode == self.SINGLE_MODE:
                print("Inclination sensor error: In single mode, but in dual stand")
                return None

            elif response[1] == self.DUALMODE_SINGLESTAND and self.mode == self.DUAL_MODE:
                print("Inclination sensor error: In dual mode, but in single stand")
                return None
            else:
                print("Unknown response: ", hex(
                    response[1]), list(response))
                return None
        else:
            print("Size of response was wrong ", len(response))
            return None

    def set_alternate_zero_singleaxis(self):
        self.mode = self.ALT_SINGLE_MODE
        self.alt_dual_xval = self.dual_xval
        self.alt_dual_yval = self.dual_yval
#        outbuffer = [self.COMPUTER, self.DEVICE, self.ALT_SINGLE_MODE,
#                     self.SET_ALT_ZERO, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
#        outbuffer = bytearray(outbuffer)
#        self.conn.write(outbuffer)
#        print("Alternate zero for single axis mode is set")

    def reset_alternate_zero_singleaxis(self):
        self.mode = self.SINGLE_MODE

#        outbuffer = [self.COMPUTER, self.DEVICE, self.ALT_SINGLE_MODE,
#                     self.RESET_ALT_ZERO, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
#        outbuffer = bytearray(outbuffer)
#        self.conn.write(outbuffer)
#        print("Alternate zero for single axis mode is reset")

    def set_alternate_zero_dualaxis(self):
        self.mode = self.ALT_DUAL_MODE
        self.alt_dual_xval = self.dual_xval
        self.alt_dual_yval = self.dual_yval

#        outbuffer = [self.COMPUTER, self.ADDRESS, 0x0A,
#                     self.SET_ALT_ZERO, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
#        outbuffer = bytearray(outbuffer)
#        self.conn.write(outbuffer)
#        print("Alternate zero for dual axis mode is set")

    def reset_alternate_zero_dualaxis(self):
        self.mode = self.DUAL_MODE
        self.alt_dual_xval = self.dual_xval = 0
        self.alt_dual_yval = self.dual_yval = 0

#        outbuffer = [self.COMPUTER, self.ADDRESS, 0x0A,
#                     self.RESET_ALT_ZERO, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
#        outbuffer = bytearray(outbuffer)
#        self.conn.write(outbuffer)
#        print("Alternate zero for dual axis mode is reset")





# This is meant to be a script for calibrating the Digi-Pas, DWL-5500 XY
# Please note the following:
# Use the manual(DWL-5x000-instruction-manual.pdf) to see the correct positioning
# Calibration setup:
# 1. Use a Granite table of grade AA(Levelled to =< 1.0 arcsec
# 2. Have the sensor powered, with enough time to warm up and stabilise before executing
# 3. Hold the device firmly and do not move it during calibration steps.
# The calibration is done in 4 steps as the sensor has to be moved to 4 different position
# in between steps the you will be asked to into enter to confirm the sensor is in position.
# This has not been tested only compiled as the sensor was calibrated when purchased.


    def calibration(self):

        self.set_mode(self.CALIBRATION_MODE)
        self.read_response()

        # Calibration mode activated
        if self.last_response[5] == 0x01 and (self.last_response[1] & 0x0F) == 0xB:
            # STEP 1
            print("Please position the sensor for step 1")
            input("Press enter when the sensor is positioned correctly")
            outbuffer = [self.COMPUTER, self.DEVICE, self.CALIBRATION_MODE,
                         self.CALIBRATION_MODE, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            outbuffer = bytearray(outbuffer)
            self.conn.write(outbuffer)

            while(True):  # The sensor will now broadcast and increment byte 4 to 0x1E
                self.read_response()
                if (self.last_response[3] == 0x1E):
                    break

            if (self.last_response[2] == 0x17 and self.last_response[5] == 0x02):
                print(
                    "Calibration step 1 is complete, please move the sensor into position for step 2")
            else:
                print(
                    "Calibration step1 was unsuccesful, sensor must have powered off and then on again before trying again")
                return

            input("Press enter when the sensor is positioned correctly")
            # STEP 2
            outbuffer = [self.COMPUTER, self.DEVICE, self.CALIBRATION_MODE,
                         self.CALIBRATION_MODE, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            outbuffer = bytearray(outbuffer)
            self.conn.write(outbuffer)

            while(True):  # The sensor will now broadcast and increment byte 4 to 0x1E
                self.read_response()
                if (self.last_response[3] == 0x1E):
                    break

            if(self.last_response[2] == 0x17 and self.last_response[5] == 0x03):
                print(
                    "Calibration step 2 is complete, please move the sensor into position for step 3")
            else:
                print(
                    "Calibration step2 was unsuccesful, sensor must have powered off and then on again before trying again")
                return
            # STEP 3
            outbuffer = [self.COMPUTER, self.DEVICE, self.CALIBRATION_MODE,
                         self.CALIBRATION_MODE, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            outbuffer = bytearray(outbuffer)
            self.conn.write(outbuffer)

            while(True):  # The sensor will now broadcast and increment byte 4 to 0x1E
                self.read_response()
                if (self.last_response[3] == 0x1E):
                    break

            if (self.last_response[2] == 0x17 and self.last_response[5] == 0x04):
                print(
                    "Calibration step 3 is complete, please move the sensor into position for step 4")
            else:
                print(
                    "Calibration step3 was unsuccesful, sensor must have powered off and then on again before trying again")
                return
            # STEP 4
            outbuffer = [self.COMPUTER, self.DEVICE, self.CALIBRATION_MODE,
                         self.CALIBRATION_MODE, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            outbuffer = bytearray(outbuffer)
            self.conn.write(outbuffer)

            while(True):  # The sensor will now broadcast and increment byte 4 to 0x1E
                self.read_response()
                if (self.last_response[3] == 0x1E):
                    break

            if (self.last_response[2] == 0x17 and self.last_response[5] == 0x05):
                print(
                    "Calibration step 4 is complete, the sensor will now enter dual axis mode and broadcast dual axis values.")
            else:
                print(
                    "Calibration step 4 was unsuccesful, sensor must have powered off and then on again before trying again")
                return
        else:
            print("Failed to enter calibration mode")
            return
