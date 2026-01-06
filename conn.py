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
    ssid = "RPSWireless"
    password = "38934"

    drivetrain = None

    def __init__(self, drivetrain):
        self.drivetrain = drivetrain

    def connect(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(self.ssid, self.password)
        while not wlan.isconnected():
            time.sleep(0.1)
        return wlan.ifconfig()[0]

    def stripCommands(self, cmd):


    def start(self):

        ip = self.connect()
        print(f"IP: {ip}")

        addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(1)

        print(f"Connect at {addr}")

        while True:
            cl, addr = s.accept()

            try:
                cmd = cl.recv(1024)

                cmd = cmd.split('\n')[0]

                method, path, _ = cmd.split()

                path = path.lstrip('/')

                if path == "FORWARD":
                    self.drivetrain.forward()
                elif path == "LEFT":
                    self.drivetrain.turnLeft()
                elif path == "RIGHT":
                    self.drivetrain.forward()
                elif path == "BACKWARD":
                    self.drivetrain.backward()
                elif path == "STOP":
                    self.drivetrain.stop()
                cl.send(b"OK")

            except OSError:
                pass
            
            finally:
                cl.close()

