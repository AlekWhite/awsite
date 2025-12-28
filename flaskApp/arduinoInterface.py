from model import Arduino, RGBLightValue, CurrentTemperature, TemperatureData
import threading
import datetime
import serial
import time
import re

class ArduinoInterface(threading.Thread):

    def __init__(self, app):
        super(ArduinoInterface, self).__init__()
        self.app = app
        self.arduino = None
        with self.app.app_context():
            TemperatureData.cleanup_excess_entries()
            CurrentTemperature.cleanup_old_readings()

    # connects to board
    def connect(self, port):
        try:
            ard = serial.Serial(port=port, baudrate=9600, timeout=.1)
            print("Arduino Connected!")
            with self.app.app_context():
                Arduino.update_state("update")
            return ard
        except Exception as e:
            print(f"No Arduino Connection - port: {port} {e}")
            return None

    # set led colors
    def setColors(self, colorString):
        if self.arduino:
            try:
                self.arduino.write(colorString.encode())
                time.sleep(1)
                Arduino.update_state("online")
            except Exception as e:
                print(f"serial write failed: {e}")
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

                # look for status changes while waiting for new data
                while int(time.time()) % 60 != 0:
                    time.sleep(0.8)

                    # update colors as needed
                    if Arduino.get_state() == "update":
                        port = Arduino.get_port()
                        c1 = RGBLightValue.get_by_name("zone1").rgb_tuple
                        c2 = RGBLightValue.get_by_name("zone2").rgb_tuple
                        c1_out = "".join(str(c).zfill(3) + " " for c in c1) + "0"
                        c2_out = "".join(str(c).zfill(3) + " " for c in c2) + "1"
                        print(f"updating colors to be: z1:{c1_out} z2:{c2_out}")
                        self.setColors(c1_out)
                        self.setColors(c2_out)

                # when connected, read data 
                if self.arduino:
                    try:
                        # parse new temperature data, add to db
                        line = str(self.arduino.readline())
                        if line != "b''" and line.startswith("b'# TEMP DATA #") and (len(line) > 60):
                            Arduino.update_state("online")
                            new_temp = re.findall(r"[0-9.-]+", line)[0]
                            CurrentTemperature.add_temp(new_temp)
                            print(f"new-temp-data: {new_temp}, {line}")
                            
                    # detect when connection is lost
                    except Exception as e:
                        print(f"Read error: {e}")
                        Arduino.update_state("offline")
                        self.arduino = None
                        continue

                    # get avg temp for this hour, at the end of the hour
                    if datetime.datetime.now().minute == 59:
                        total = 0
                        db_data = CurrentTemperature.get_last_hour()
                        for t in db_data:
                            total += t.current_temp
                        if len(db_data) > 0:
                            out = float(int((total / len(db_data))*10))/10
                            print(f"new-avg-temp: {out}")
                            TemperatureData.add_temp(out)
                        
                else:
                    Arduino.update_state("offline")
                    self.arduino = self.connect(port)
                    time.sleep(1)