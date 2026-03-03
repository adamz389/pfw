# ViperIDE - MicroPython Web IDE
# Read more: https://github.com/vshymanskyy/ViperIDE

# Connect your device and start creating! 🤖👨‍💻🕹️

# You can also open a virtual device and explore some examples:
# https://viper-ide.org?vm=1

from machine import PWM, Pin
import time
import math


class PID:

    def __init__(self, kP, kI, kD):
        self.kP = kP
        self.kI = kI
        self.kD = kD
        self.integral = 0
        self.last_error = 0
        self.last_time = time.ticks_ms()

    def compute(self, target, current):
        # KP
        error = target - current

        # KI
        now = time.ticks_ms()
        dt = (time.ticks_diff(now, self.last_time)) / 1000
        self.last_time = now
        self.integral += error * dt

        # KD
        derivative = (error - self.last_error) / dt if dt > 0 else 0
        self.last_error = error

        output = self.kP * error + self.kI * self.integral + self.kD * derivative

        return max(0, min(65535, int(output)))


class MotorEX:

    def __init__(self, m1, c1, pid, ppr=700):
        self.curr_rpm = 0
        self.targ_rpm = 0
        self.pulse_count = 0
        self.last_duty = 0

        self.motorA1 = PWM(Pin(m1))
        self.encoder = Pin(c1, Pin.IN)

        self.motorA1.freq(1000)

        self.encoder.irq(trigger=Pin.IRQ_RISING, handler=self.on_pulse)
        self.ppr = ppr
        self.pid = pid

    def on_pulse(self, pin):
        self.pulse_count += 1

    # replace dt how long motor has been counting pulses
    def getRPM(self, dt=0.05):
        revolutions = self.pulse_count / self.ppr
        rpm = revolutions * (60 / dt)
        self.pulse_count = 0
        self.curr_rpm = rpm
        return rpm

    def setRPM(self, targetRPM):
        # back and forwards
        self.targ_rpm = targetRPM

    def getVelocity(self):
        return self.rpmToRADS(self.getRPM())

    def setVelocity(self, velocity):
        self.targ_rpm = self.radsToRPM(velocity)

    def radsToRPM(self, omega):
        return omega * 30 / math.pi

    def rpmToRADS(self, rpm):
        return rpm * math.pi / 30

    def getLastDuty(self):
        return self.last_duty

    def update(self, dt=0.05):
        rpm = self.getRPM(dt)
        duty = self.pid.compute(self.targ_rpm, rpm)
        self.motorA1.duty_u16(duty)
        self.last_duty = duty


# must tune values
pid = PID(1, 0.2, 0.5)
motor = MotorEX(15, 13, pid)
motor.setVelocity(150)  # 150 rad/s

last_time = time.ticks_ms()

while True:
    # compute dt internally in motor.getRPM(dt) ??
    now = time.ticks_ms()
    dt = time.ticks_diff(now, last_time) / 1000  # seconds
    last_time = now
    motor.update(dt)







