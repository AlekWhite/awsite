from model import Arduino
import threading
import serial
import time

class ArduinoInterface(threading.Thread):

    def __init__(self, app):
        super(ArduinoInterface, self).__init__()
        self.app = app
        self.arduino = None

    # connects to board
    def connect(self, port):
        try:
            ard = serial.Serial(port=port, baudrate=9600, timeout=.1)
            return ard
        except:
            print(f"No Arduino Connection - port: {port}")
            return None

    # set led colors
    def setColors(self, colorString):
        if self.arduino:
            try:
                self.arduino.write(colorString.encode())
            except:
                print("Could Not Send to Arduino")
                self.arduino = None
                with self.app.app_context():
                    Arduino.update_state("offline")

    # main loop
    def run(self):
        with self.app.app_context():
            port = Arduino.get_port()
            self.arduino = self.connect(port)

            # run once a min, at the start of the min
            while True:

                # look for status chnages while waiting for new data
                while int(time.time()) % 60 != 0:
                    time.sleep(0.8)

                    # update port and colors as needed
                    if Arduino.get_state() == "update":
                        port = Arduino.get_port()

                # when connected, read data 
                if self.arduino:
                    try:
                        line = str(self.arduino.readline())
                        if line != "b''":
                            Arduino.update_state("online")
                            print(line)

                    # detect when connection is lost
                    except Exception as e:
                        print(f"Read error: {e}")
                        Arduino.update_state("offline")
                        self.arduino = None
                        continue
                else:
                    Arduino.update_state("offline")
                    self.arduino = self.connect(port)
                time.sleep(1)