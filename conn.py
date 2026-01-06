# ViperIDE - MicroPython Web IDE
# Read more: https://github.com/vshymanskyy/ViperIDE

# Connect your device and start creating! 🤖👨‍💻🕹️

# You can also open a virtual device and explore some examples:
# https://viper-ide.org?vm=1


import network
import socket
import time
from machine import PWM, Pin


class Motor:
    motorA1 = None
    motorA2 = None

    max = 60000

    def __init__(self, motorA1, motorA2):
        self.motorA2 = motorA2
        self.motorA1 = motorA1

    def forward(self):
        self.motorA1.duty_u16(max)
        self.motorA2.duty_u16(0)

    def backward(self):
        self.motorA1.duty_u16(0)
        self.motorA2.duty_u16(max)

    def stop(self):
        self.motorA1.duty_u16(0)
        self.motorA2.duty_u16(0)


class Drivetrain:
    leftMotor = None
    rightMotor = None

    def _init__(self, leftMotor, rightMotor):
        self.leftMotor = leftMotor
        self.rightMotor = rightMotor

    def addLeftMotor(self, posNumber, negNumber):
        motorA1 = PWM(Pin(posNumber))
        motorA2 = PWM(Pin(negNumber))

        motorA1.freq(1000)
        motorA2.freq(1000)

        motor = Motor(motorA1, motorA2)
        self.leftMotor = motor

    def addRightMotor(self, posNumber, negNumber):
        motorA1 = PWM(Pin(posNumber))
        motorA2 = PWM(Pin(negNumber))

        motorA1.freq(1000)
        motorA2.freq(1000)

        motor = Motor(motorA1, motorA2)
        self.rightMotor = motor

    def forward(self):
        self.leftMotor.forward()
        self.rightMotor.forward()

    def backward(self):
        self.leftMotor.backward()
        self.rightMotor.backward()

    def turnRight(self):
        self.rightMotor.forward()
        self.leftMotor.backward()

    def turnLeft(self):
        self.rightMotor.backward()
        self.leftMotor.forward()

    def stop(self):
        self.rightMotor.stop()
        self.leftMotor.stop()


class Connection:
    gc.collect()
    ap = network.WLAN(network.AP_IF)

    drivetrain = None

    def __init__(self, drivetrain):
        self.drivetrain = drivetrain

    def connect(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(self.ssid, self.password)
        while not wlan.isconnected():
            print("incorrect ssid or password")
            time.sleep(0.1)

        return wlan.ifconfig()[0]

    def create(self):
        ap.active(True)
        ap.config(essid="pico123", password="12345678")
        while not ap.active():
            time.sleep(0.1)
        time.sleep(1)

    def start(self):

        # ip = self.connect()
        # print(f"IP: {ip}")

        self.create()

        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(1)

        print("Connect at http://192.168.4.1/")

        while True:
            cl, addr = s.accept()

            try:
                cmd = cl.recv(1024).decode()

                print(cmd)

                cmd = cmd.split('\n')[0]

                method, path, _ = cmd.split()

                path = path.lstrip('/')

                print(path)

                if path == "FORWARD":
                    self.drivetrain.forward()
                elif path == "LEFT":
                    self.drivetrain.turnLeft()
                elif path == "RIGHT":
                    self.drivetrain.turnRight()
                elif path == "BACKWARD":
                    self.drivetrain.backward()
                elif path == "STOP":
                    self.drivetrain.stop()
                cl.send(b"OK")

            except OSError:
                pass

            finally:
                cl.close()


# dt = Drivetrain()
# dt.addLeftMotor(2, 3)
# dt.addRightMotor(15, 14)
#
# conn = Connection(dt)
# conn.start()

