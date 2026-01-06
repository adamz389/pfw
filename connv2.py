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

    max = 65535

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
    status = "Idle"

    def __init__(self, leftMotor, rightMotor):
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

    def _ready_(self):
        if not self.leftMotor and self.rightMotor:
            raise ValueError("Left motor not initialized.")
        elif self.leftMotor and not self.rightMotor:
            raise ValueError("Right motor not initialized.")
        elif not self.leftMotor and not self.rightMotor:
            raise ValueError("No motors are initialized.")

    def forward(self):
        self._ready_()
        self.leftMotor.forward()
        self.rightMotor.forward()
        self.status = "Moving"

    def backward(self):
        self._ready_()
        self.leftMotor.backward()
        self.rightMotor.backward()
        self.status = "Moving"

    def turnRight(self):
        self._ready_()
        self.rightMotor.forward()
        self.leftMotor.backward()
        self.status = "Moving"

    def turnLeft(self):
        self._ready_()
        self.rightMotor.backward()
        self.leftMotor.forward()
        self.status = "Moving"

    def stop(self):
        self._ready_()
        self.rightMotor.stop()
        self.leftMotor.stop()
        self.status = "Idle"


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

                html = """
                <html>
                  <head>
                    <style>
                      body {
                        font-family: Arial, sans-serif;
                        background-color: #f2f2f2;
                        margin: 0;
                        padding: 20px;
                      }

                      h1 {
                        color: #333;
                      }

                      h2 {
                        color: #555;
                      }

                      .status-box {
                        background-color: #fff;
                        padding: 20px;
                        border-radius: 12px;
                        box-shadow: 0 0 10px rgba(0,0,0,0.2);
                        max-width: 400px;
                      }

                      .controller {
                        position: fixed;
                        bottom: 20px;
                        right: 20px;
                        width: 160px;
                        height: 160px;
                        display: grid;
                        grid-template-columns: 50px 60px 50px;
                        grid-template-rows: 50px 60px 50px;
                        gap: 5px;
                        background-color: rgba(255,255,255,0.9);
                        border-radius: 12px;
                        box-shadow: 0 0 8px rgba(0,0,0,0.2);
                        padding: 5px;
                      }

                      .controller button {
                        font-size: 16px;
                        cursor: pointer;
                        border: none;
                        border-radius: 6px;
                        background-color: #4CAF50;
                        color: white;
                        transition: 0.2s;
                      }

                      .controller button:hover {
                        background-color: #45a049;
                      }

                      .empty { background: none; }
                      .stop { background-color: #f44336; }
                      .stop:hover { background-color: #d32f2f; }
                    </style>
                  </head>
                  <body>
                    <div class="status-box">
                      <h1>robot drivetrain</h1>
                      <h2>Status: {status}</h2>
                      <p>IP: {ip}</p>
                    </div>

                    <div class="controller">
                      <div class="empty"></div>
                      <button onclick="fetch('http://192.168.4.1/FORWARD')">▲</button>
                      <div class="empty"></div>

                      <button onclick="fetch('http://192.168.4.1/LEFT')">◀</button>
                      <button class="stop" onclick="fetch('http://192.168.4.1/STOP')">■</button>
                      <button onclick="fetch('http://192.168.4.1/RIGHT')">▶</button>

                      <div class="empty"></div>
                      <button onclick="fetch('http://192.168.4.1/BACKWARD')">▼</button>
                      <div class="empty"></div>
                    </div>
                  </body>
                </html>
                """.format(
                    status=self.drivetrain.status,
                    ip="192.168.4.1"
                )

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
                elif path == "":
                    cl.send(f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{html}".encode())
                    cl.close()
                    continue

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

