import sys
import signal
from flask_server import app
from fishOfTheWeek import FishOfTheWeek
from arduinoInterface import ArduinoInterface

def signal_handler(sig, frame):
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    data_b = ArduinoInterface(app)
    fish_bowl = FishOfTheWeek(app)
    data_b.start()
    fish_bowl.start()
    app.run(host="0.0.0.0", port="5100", debug=False)