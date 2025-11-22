import serial
import time

class ArduinoServo:
    def __init__(self, puerto="/dev/ttyUSB0", baud=9600):
        self.serial = serial.Serial(puerto, baud, timeout=1)
        time.sleep(2)

    def mover(self, categoria: str):
        if not getattr(self.serial, "is_open", True):
            return
        self.serial.write(b"A" if categoria == "A" else b"B")

    def close(self):
        if self.serial:
            try:
                if getattr(self.serial, "is_open", False):
                    self.serial.close()
            finally:
                self.serial = None
