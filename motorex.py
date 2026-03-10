# # # ViperIDE - MicroPython Web IDE
# # # Read more: https://github.com/vshymanskyy/ViperIDE

# # # Connect your device and start creating! 🤖👨‍💻🕹️

# # # You can also open a virtual device and explore some examples:
# # # https://viper-ide.org?vm=1


# ViperIDE - MicroPython Web IDE
# Read more: https://github.com/vshymanskyy/ViperIDE

# Connect your device and start creating! 🤖👨‍💻🕹️

# You can also open a virtual device and explore some examples:
# https://viper-ide.org?vm=1

from machine import PWM, Pin
import time
import math
import gc
import network
import socket

MAX_DUTY = 65535

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
        print("Connect at http://192.168.4.1/")

    def addMapping(self, cmd, function):
        self.command_map[cmd] = function

    def runMapping(self, cmd):
        if cmd in self.command_map:
            self.command_map[cmd]()
        else:
            print(f"Command {cmd} has no function")

    def update(self, dt):
        # Non-blocking check for new client
        try:
            self.s.settimeout(0)  # Non-blocking
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

class Utils:

    @staticmethod
    def Clamp(num, minimum, maximum):
        return min(maximum, max(minimum, num))

class Motor:

    def __init__(self, m1, m2):
        motorA1 = PWM(Pin(m1))
        motorA2 = PWM(Pin(m2))

        motorA1.freq(1000)
        motorA2.freq(1000)

        self.motorA2 = motorA2
        self.motorA1 = motorA1


    def setPower(self, power):
        power = Utils.Clamp(power, -1, 1)

        if power > 0:
            self.motorA1.duty_u16(int(power * MAX_DUTY))
            self.motorA2.duty_u16(0)
        elif power < 0:
            self.motorA2.duty_u16(int(-power * MAX_DUTY))
            self.motorA1.duty_u16(0)
        else:
            self.stop()

    def stop(self):
        self.motorA1.duty_u16(0)
        self.motorA2.duty_u16(0)

    def setMaxDuty(self, duty):
        MAX_DUTY = duty

    def forward(self, power=1):
        self.setPower(abs(power))

    def reverse(self, power=1):
        self.setPower(-abs(power))

class PID:

    def __init__(self, kP, kI, kD):
        self.kP = kP
        self.kI = kI
        self.kD = kD
        self.integral = 0
        self.last_error = 0
        self.last_time = time.ticks_ms()

    def compute(self, target, current, dt=None):
        # KP
        error = target - current

        # KI
        now = time.ticks_ms()
        actual_dt = (time.ticks_diff(now, self.last_time)) / 1000
        self.last_time = now
        if dt is None:
            dt = actual_dt
        self.integral += error * dt

        # KD
        derivative = (error - self.last_error) / dt if dt > 0 else 0
        self.last_error = error

        output = self.kP * error + self.kI * self.integral + self.kD * derivative

        return int(Utils.Clamp(output, -MAX_DUTY, MAX_DUTY))
        
class MotorEX:

    def __init__(self, m1, m2, c1, pid, ppr=41, measure_interval=1.0):
        self.curr_rpm = 0
        self.targ_rpm = 0
        self.pulse_count = 0
        self.last_duty = 0

        self.motorA1 = PWM(Pin(m1))
        self.motorA2 = PWM(Pin(m2))
        self.encoder = Pin(c1, Pin.IN, Pin.PULL_UP)

        self.motorA1.freq(1000)
        self.motorA2.freq(1000)

        self.encoder.irq(trigger=Pin.IRQ_RISING, handler=self.on_pulse)

        self.pid = pid
        self.ppr = ppr

        # measurement timing
        self.measure_interval = measure_interval
        self.measure_timer = 0

    def setPower(self, power):
        power = Utils.Clamp(power, -1, 1)

        if power > 0:
            self.motorA1.duty_u16(int(power * MAX_DUTY))
            self.motorA2.duty_u16(0)
        elif power < 0:
            self.motorA2.duty_u16(int(-power * MAX_DUTY))
            self.motorA1.duty_u16(0)
        else:
            self.stop()

    def on_pulse(self, pin):
        self.pulse_count += 1

    def computeRPM(self, dt):
        revolutions = self.pulse_count / self.ppr
        rpm = revolutions * (60 / dt)

        self.curr_rpm = rpm
        self.pulse_count = 0

    def setRPM(self, targetRPM):
        self.targ_rpm = targetRPM

    def getRPM(self):
        return self.curr_rpm

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

        # accumulate time for RPM measurement
        self.measure_timer += dt

        if self.measure_timer >= self.measure_interval:
            self.computeRPM(self.measure_timer)
            self.measure_timer = 0

        # run PID using latest rpm
        duty = self.pid.compute(self.targ_rpm, self.curr_rpm, dt)

        if duty >= 0:
            self.motorA1.duty_u16(duty)
            self.motorA2.duty_u16(0)
        else:
            self.motorA1.duty_u16(0)
            self.motorA2.duty_u16(-duty)

        self.last_duty = duty

# must tune values
pid = PID(1, 0.2, 5)
motor = MotorEX(3, 2, 13, pid, 51) 


robot = Robot()
robot.register(motor)

while True:
    motor.setPower(1)
    robot.periodic()
    print(f"RPM: {motor.getRPM()}")

R = .0127 # wheel radius
g = 9.81 # g constant
# y = 0.5715
y = 0.4445 # height of target
theta = 60 # launch angle

# def calculatePower(x):
#         pow = -(2.94189e-9 * (x*x*x*x)) + (0.00000229358 * (x*x*x)) - (0.000625231 * (x*x)) + (0.0732917 * x) - 2.80291
#         print(f"runs at {pow} power")
#         return pow

# def calculateOmega(x):
#     denominator = x * math.sqrt(3) - y
#     if denominator <= 0:
#         print("Invalid input: square root would be negative or division by zero")
#         return None
#     omega = (1/R) * math.sqrt((2*g*(x*x)) / denominator)
#     print(f"rad/s of {omega}")
#     return omega

# rad = calculateOmega(0.6096)
# pow = calculatePower(rad)

#add tiny 1ms delay in robot periodoc
