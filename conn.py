from machine import PWM, Pin
import time
import math
import gc
import network
import socket


class Connection:

    def __init__(self, essid, password):
        gc.collect()
        self.ap = network.WLAN(network.AP_IF)
        self.command_map = {}
        self.s = None
        self.essid = essid
        self.password = password

    def create(self):
        self.ap.active(True)
        self.ap.config(self.essid, self.password)
        while not self.ap.active():
            time.sleep(0.1)
        time.sleep(1)
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        self.s = socket.socket()
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(addr)
        self.s.listen(1)
        self.s.settimeout(0)
        print("Connect at http://192.168.4.1/")

    def addMapping(self, cmd, function):
        self.command_map[cmd] = function

    def runMapping(self, cmd):
        if cmd in self.command_map:
            self.command_map[cmd]()
        else:
            print(f"Command {cmd} has no function")

    def update(self, dt):
        try:
            cl, addr = self.s.accept()
            try:
                cmd = cl.recv(1024).decode()
                path = cmd.split("\n")[0].split()[1].lstrip('/')
                if path:
                    self.runMapping(path)
                cl.send(b"OK")
            except OSError:
                pass
            finally:
                cl.close()
        except OSError:
            pass


class Robot:

    def __init__(self):
        self.periodics = []
        self.loop = Loop()
        self.runtime = Runtime()
        self.runtime.start()
        self.running = True

    def register(self, device):
        if hasattr(device, "update"):
            self.periodics.append(device.update)

    def periodic(self):
        dt = self.get_dt()
        for func in self.periodics:
            func(dt)
        time.sleep(0.001)

    def get_runtime(self):
        return self.runtime.elapsed()

    def get_dt(self):
        return self.loop.dt()

    def is_running(self):
        return self.running

    def stop(self):
        self.running = False


class Runtime:

    def __init__(self):
        self.last_time = None

    def start(self):
        self.last_time = time.ticks_ms()

    def reset(self):
        self.last_time = time.ticks_ms()

    def elapsed(self):
        if self.last_time is None:
            return 0
        now = time.ticks_ms()
        return time.ticks_diff(now, self.last_time)


class Loop:

    def __init__(self):
        self.last_time = time.ticks_ms()

    def dt(self):
        now = time.ticks_ms()
        dt = time.ticks_diff(now, self.last_time) / 1000
        self.last_time = now
        return max(dt, 0.001)


class Vector2:

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def normalize(self):
        mag = self.magnitude()
        if mag == 0:
            return
        self.x /= mag
        self.y /= mag

    def magnitude(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)


class PID:

    def __init__(self, kP, kI, kD):
        self.kP = kP
        self.kI = kI
        self.kD = kD
        self.integral = 0
        self.last_error = 0

    def compute(self, target, current, dt):
        error = target - current
        self.integral += error * dt
        derivative = (error - self.last_error) / dt if dt > 0 else 0
        self.last_error = error
        output = self.kP * error + self.kI * self.integral + self.kD * derivative
        return max(0, min(65535, int(output)))


class MotorEX:

    def __init__(self, m1, m2, c1, pid, ppr=700):
        self.curr_rpm = 0
        self.targ_rpm = 0
        self.pulse_count = 0
        self.last_duty = 0

        self.motorA1 = PWM(Pin(m1))
        self.motorA2 = PWM(Pin(m2))
        self.encoder = Pin(c1, Pin.IN)


        self.motorA1.freq(1000)
        self.motorA2.freq(1000)

        self.encoder.irq(trigger=Pin.IRQ_RISING, handler=self.on_pulse)
        self.ppr = ppr
        self.pid = pid

    def on_pulse(self, pin):
        self.pulse_count += 1

    def getRPM(self, dt):
        revolutions = self.pulse_count / self.ppr
        rpm = revolutions * (60 / dt)
        self.pulse_count = 0
        self.curr_rpm = rpm
        return rpm

    def setRPM(self, targetRPM):
        self.targ_rpm = targetRPM

    def getVelocity(self):
        return self.rpmToRADS(self.curr_rpm)

    def setVelocity(self, velocity):
        self.targ_rpm = self.radsToRPM(velocity)

    def radsToRPM(self, omega):
        return omega * 30 / math.pi

    def rpmToRADS(self, rpm):
        return rpm * math.pi / 30

    def getLastDuty(self):
        return self.last_duty

    def update(self, dt):
        rpm = self.getRPM(dt)
        duty = self.pid.compute(self.targ_rpm, rpm, dt)
        if self.targ_rpm >= 0:
            self.motorA1.duty_u16(duty)
            self.motorA2.duty_u16(0)
        else:
            self.motorA1.duty_u16(0)
            self.motorA2.duty_u16(duty)
        self.last_duty = duty


pid = PID(1, 0.2, 0.5) # tune pid values
motor = MotorEX(15, 14, 13, pid)
motor.setVelocity(150) # rad/s

robot = Robot()
robot.register(motor)

# increase robot periodic sleep time more than 1ms for cpu

while robot.is_running():
    robot.periodic()