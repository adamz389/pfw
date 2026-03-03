import gc
import network
import socket
import time
from machine import PWM, Pin


class Motor:

    def __init__(self, motorA1, motorA2):
        self.motorA1 = motorA1
        self.motorA2 = motorA2
        self.MAX_DUTY = 65535

    def setMaxDuty(self, duty):
        self.MAX_DUTY = duty

    def setPower(self, power):
        direction = "forward" if power > 0 else "backward" if power < 0 else "stop"
        power = int(max(0, min(1, abs(power))) * self.MAX_DUTY)
        if direction == "forward":
            self.motorA1.duty_u16(power)
            self.motorA2.duty_u16(0)
        elif direction == "backward":
            self.motorA1.duty_u16(0)
            self.motorA2.duty_u16(power)
        else:
            self.motorA1.duty_u16(0)
            self.motorA2.duty_u16(0)

    def forward(self, power=1):
        self.setPower(power)

    def backward(self, power=-1):
        self.setPower(power)

    def stop(self):
        self.setPower(0)


class Drivetrain:

    def __init__(self):
        self.leftMotor = None
        self.rightMotor = None
        self.status = "Idle"

    def addLeftMotor(self, posNumber, negNumber):
        motorA1 = PWM(Pin(posNumber))
        motorA2 = PWM(Pin(negNumber))
        motorA1.freq(1000)
        motorA2.freq(1000)
        self.leftMotor = Motor(motorA1, motorA2)

    def addRightMotor(self, posNumber, negNumber):
        motorA1 = PWM(Pin(posNumber))
        motorA2 = PWM(Pin(negNumber))
        motorA1.freq(1000)
        motorA2.freq(1000)
        self.rightMotor = Motor(motorA1, motorA2)

    def _ready_(self):
        if self.leftMotor is None:
            raise ValueError("Left motor not initialized.")
        if self.rightMotor is None:
            raise ValueError("Right motor not initialized.")

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
        self.leftMotor.forward()
        self.rightMotor.backward()
        self.status = "Moving"

    def turnLeft(self):
        self._ready_()
        self.leftMotor.backward()
        self.rightMotor.forward()
        self.status = "Moving"

    def stop(self):
        self._ready_()
        self.leftMotor.stop()
        self.rightMotor.stop()
        self.status = "Idle"


class Connection:

    def __init__(self):
        gc.collect()
        self.ap = network.WLAN(network.AP_IF)
        self.command_map = {}

    def create(self):
        self.ap.active(True)
        self.ap.config(essid="pico123", password="12345678")
        while not self.ap.active():
            time.sleep(0.1)
        time.sleep(1)

    def addMapping(self, cmd, function):
        self.command_map[cmd] = function

    def runMapping(self, cmd):
        if self.command_map.__contains__(cmd):
            self.command_map[cmd]()
        else:
            print(f"Command {cmd} is mapped to no function")

    def start(self):
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
                cmd_line = cmd.split("\n")[0]
                parts = cmd_line.split()
                if len(parts) < 2:
                    cl.close()
                    continue
                method, path = parts[0], parts[1]
                path = path.lstrip('/')

                html = """
                <html>
                  <head>
                    <style>
                      body { font-family: Arial, sans-serif; background-color: #f2f2f2; margin: 0; padding: 20px; }
                      h1 { color: #333; }
                      h2 { color: #555; }
                      .status-box { background-color: #fff; padding: 20px; border-radius: 12px; box-shadow: 0 0 10px rgba(0,0,0,0.2); max-width: 400px; }
                      .controller { position: fixed; bottom: 20px; right: 20px; width: 160px; height: 160px; display: grid; grid-template-columns: 50px 60px 50px; grid-template-rows: 50px 60px 50px; gap: 5px; background-color: rgba(255,255,255,0.9); border-radius: 12px; box-shadow: 0 0 8px rgba(0,0,0,0.2); padding: 5px; }
                      .controller button { font-size: 16px; cursor: pointer; border: none; border-radius: 6px; background-color: #4CAF50; color: white; transition: 0.2s; }
                      .controller button:hover { background-color: #45a049; }
                      .empty { background: none; }
                      .stop { background-color: #f44336; }
                      .stop:hover { background-color: #d32f2f; }
                    </style>
                  </head>
                  <body>
                    <div class="status-box">
                      <h1>robot drivetrain</h1>
                      <h2>Status: {status}</h2>
                      <p>IP: 192.168.4.1</p>
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
                """.format(status=self.drivetrain.status)

                if path == "":
                    cl.send(f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{html}".encode())
                    cl.close()
                    continue
                else:
                    self.runMapping(path)

                cl.send(b"OK")

            except OSError:
                pass
            finally:
                cl.close()
dt = Drivetrain()
connection = Connection()

# can map paths to functions instead of pre-set pairs
# remove drivetrain object from connection

connection.addMapping("FORWARD", dt.forward)
connection.addMapping("LEFT", dt.turnLeft)
connection.addMapping("RIGHT", dt.turnRight)
connection.addMapping("BACKWARD", dt.backward)
connection.addMapping("STOP", dt.stop)

connection.start()