
from machine import PWM, Pin

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
