"""
PFW - MicroPython Robotics Framework
====================================

ViperIDE - MicroPython Web IDE
https://github.com/vshymanskyy/ViperIDE

This module provides classes and utilities for:
- Robot control loops
- Motor control with PWM
- PID controllers
- Physics calculations
- MicroPython network connections for remote commands
"""

from machine import PWM, Pin
import time
import math
import gc
import network
import socket

MAX_DUTY = 65535

class Drivetrain:
    
    def __init__(self, motor1, motor2):
        self.motor1 = motor1
        self.motor2 = motor2

    def resetMotors(self):
        self.motor1.setPower(0)
        self.motor2.setPower(0)

    def right(self):
        self.resetMotors()
        self.motor1.setPower(1)
        self.motor2.setPower(-1)

    def left(self):
        self.resetMotors()
        self.motor1.setPower(-1)
        self.motor2.setPower(1)
        
    def forward(self):
        self.resetMotors()
        self.motor1.setPower(1)
        self.motor2.setPower(1)

    def backward(self):
        self.resetMotors()
        self.motor1.setPower(-1)
        self.motor2.setPower(-1)

    def stop(self):
        self.resetMotors()

class Connection:
    """
    Handles a WiFi access point connection for remote command execution.

    Attributes:
        ap (network.WLAN): The access point interface.
        command_map (dict): Maps commands to functions.
        s (socket.socket): TCP server socket.
        essid (str): WiFi network name.
        password (str): WiFi password.
    """

    def __init__(self, essid, password):
        """
        Initialize the connection.

        Args:
            essid (str): SSID for the WiFi AP.
            password (str): Password for the WiFi AP.
        """
        gc.collect()
        self.ap = network.WLAN(network.AP_IF)
        self.command_map = {}
        self.s = None
        self.essid = essid
        self.password = password

    def create(self):
        self.ap.active(True)
        self.ap.config(essid=self.essid, password=self.password)

        while not self.ap.active():
            time.sleep(0.1)

        time.sleep(1)

        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        self.s = socket.socket()
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(addr)
        self.s.listen(1)

        print("Connect at http://192.168.4.1/")

    def initDrive(self, drivetrain):
        self.addMapping("RIGHT", drivetrain.right)
        self.addMapping("LEFT", drivetrain.left)
        self.addMapping("FORWARD", drivetrain.forward)
        self.addMapping("BACKWARD", drivetrain.backward)
        self.addMapping("STOP", drivetrain.stop)

    def addMapping(self, cmd, function):
        """
        Map a command string to a function.

        Args:
            cmd (str): Command string.
            function (callable): Function to run when command is received.
        """
        self.command_map[cmd] = function

    def runMapping(self, cmd):
        """
        Execute a mapped command if it exists.

        Args:
            cmd (str): Command string.
        """
        if cmd in self.command_map:
            self.command_map[cmd]()
        else:
            print(f"Command {cmd} has no function")

    def update(self, dt):
        """
        Non-blocking check for incoming connections and run commands.

        Args:
            dt (float): Time step (not used here, required for compatibility).
        """
        try:
            self.s.settimeout(0.01)
            cl, addr = self.s.accept()
            try:
                cmd = cl.recv(1024).decode()

                if not cmd:
                    return
                
                line = cmd.split("\r\n")[0]
                parts = line.split()
                
                if len(parts) >= 2:
                    path = parts[1].lstrip('/')
                else:
                    path = ""
                
                if path:
                    self.runMapping(path)
                
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK"
                cl.send(response.encode())
            except OSError:
                pass
            finally:
                cl.close()
        except OSError:
            pass


class Physics:
    """
    Basic physics calculations for projectile motion.

    Attributes:
        g (float): Gravity constant (9.81 m/s^2).
        y (float): Target height.
        R (float): Radius of the launcher or wheel.
        theta (float): Launch angle in degrees.
    """

    g = 9.81
    y = 0.5

    def __init__(self, R=0.0127, theta=30):
        """
        Initialize the physics calculator.

        Args:
            R (float): Radius of the wheel/launcher in meters.
            theta (float): Launch angle in degrees.
        """
        self.R = R
        self.theta = theta

    def calculateOmega(self, x):
        """
        Calculate the required angular velocity to reach a distance x.

        Args:
            x (float): Horizontal distance to target.

        Returns:
            float: Angular velocity in rad/s, or None if invalid.
        """
        denominator = (x * math.tan(math.radians(self.theta)) - self.y) * (2 * (math.cos(math.radians(self.theta)) ** 2))
        if denominator <= 0:
            print("Invalid input: square root would be negative or division by zero")
            return None

        omega = 2 * (1 / self.R) * math.sqrt((self.g * (x * x)) / denominator)
        print(f"rad/s of {omega}")
        return omega


class Robot:
    """
    Main robot class handling periodic updates and runtime.

    Attributes:
        periodics (list): List of periodic update functions.
        loop (Loop): Loop timer.
        runtime (Runtime): Runtime tracker.
        running (bool): Flag indicating if the robot loop is active.
    """

    def __init__(self):
        self.periodics = []
        self.loop = Loop()
        self.runtime = Runtime()
        self.runtime.start()
        self.running = True

    def register(self, device):
        """
        Register a device with an 'update' method to run each cycle.

        Args:
            device: Object with an 'update(dt)' method.
        """
        if hasattr(device, "update"):
            self.periodics.append(device.update)

    def periodic(self):
        """
        Call all registered periodic functions with the current dt.
        """
        dt = self.get_dt()
        for func in self.periodics:
            func(dt)

    def get_runtime(self):
        """
        Get elapsed runtime in milliseconds.

        Returns:
            int: Runtime in milliseconds.
        """
        return self.runtime.elapsed()

    def get_dt(self):
        """
        Get delta time since last loop in seconds.

        Returns:
            float: Delta time in seconds.
        """
        return self.loop.dt()

    def is_running(self):
        """
        Check if robot loop is still running.

        Returns:
            bool
        """
        return self.running

    def stop(self):
        """
        Stop the robot loop.
        """
        self.running = False


class Runtime:
    """
    Tracks elapsed time for robot runtime.
    """

    def __init__(self):
        self.last_time = None

    def start(self):
        """Start the timer."""
        self.last_time = time.ticks_ms()

    def reset(self):
        """Reset the timer."""
        self.last_time = time.ticks_ms()

    def elapsed(self):
        """
        Return elapsed time since start in milliseconds.

        Returns:
            int: Elapsed time in ms.
        """
        if self.last_time is None:
            return 0
        now = time.ticks_ms()
        return time.ticks_diff(now, self.last_time)


class Loop:
    """
    Loop timer to calculate dt between cycles.
    """

    def __init__(self):
        self.last_time = time.ticks_ms()

    def dt(self):
        """
        Return delta time in seconds since last call.

        Returns:
            float: Delta time in seconds.
        """
        now = time.ticks_ms()
        dt = time.ticks_diff(now, self.last_time) / 1000
        self.last_time = now
        return max(dt, 0.001)


class Utils:
    """Utility static methods."""

    @staticmethod
    def Clamp(num, minimum, maximum):
        """
        Clamp a number between minimum and maximum.

        Args:
            num (float): Input number.
            minimum (float): Minimum allowed value.
            maximum (float): Maximum allowed value.

        Returns:
            float: Clamped value.
        """
        return min(maximum, max(minimum, num))


class Motor:
    """
    Basic 2-pin PWM motor control.
    """

    def __init__(self, m1, m2):
        """
        Initialize the motor.

        Args:
            m1 (int): Pin number for first motor wire.
            m2 (int): Pin number for second motor wire.
        """
        motorA1 = PWM(Pin(m1))
        motorA2 = PWM(Pin(m2))
        motorA1.freq(1000)
        motorA2.freq(1000)
        self.motorA1 = motorA1
        self.motorA2 = motorA2

    def setPower(self, power):
        """Set motor power between -1 and 1."""
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
        """Stop the motor."""
        self.motorA1.duty_u16(0)
        self.motorA2.duty_u16(0)

    def setMaxDuty(self, duty):
        """Set maximum PWM duty (currently global MAX_DUTY)."""
        global MAX_DUTY
        MAX_DUTY = duty

    def forward(self, power=1):
        """Run motor forward."""
        self.setPower(abs(power))

    def reverse(self, power=1):
        """Run motor backward."""
        self.setPower(-abs(power))


class PID:
    """
    Simple PID controller.
    """

    def __init__(self, kP, kI, kD):
        """
        Initialize PID controller.

        Args:
            kP (float): Proportional gain.
            kI (float): Integral gain.
            kD (float): Derivative gain.
        """
        self.kP = kP
        self.kI = kI
        self.kD = kD
        self.integral = 0
        self.last_error = 0
        self.last_time = time.ticks_ms()

    def compute(self, target, current, dt=None):
        """
        Compute PID output.

        Args:
            target (float): Desired value.
            current (float): Current value.
            dt (float, optional): Time delta in seconds.

        Returns:
            int: Duty cycle, clamped to [-MAX_DUTY, MAX_DUTY].
        """
        error = target - current
        now = time.ticks_ms()
        actual_dt = time.ticks_diff(now, self.last_time) / 1000
        self.last_time = now
        if dt is None:
            dt = actual_dt

        self.integral += error * dt
        self.integral = Utils.Clamp(self.integral, -5000, 5000)

        derivative = (error - self.last_error) / dt if dt > 0 else 0
        self.last_error = error

        output = self.kP * error + self.kI * self.integral + self.kD * derivative
        duty = int(Utils.Clamp(output, -MAX_DUTY, MAX_DUTY))
        return duty


class MotorEX:
    """
    Advanced motor with encoder and PID control.
    """

    def __init__(self, m1, m2, c1, pid=None, ppr=38, measure_interval=0.05):
        if pid is None:
            pid = PID(80, 1, 5)

        self.pid = pid
        """
        Initialize motor with encoder.

        Args:
            m1 (int): Motor pin 1.
            m2 (int): Motor pin 2.
            c1 (int): Encoder pin.
            pid (PID): PID controller instance.
            ppr (int): Pulses per revolution.
            measure_interval (float): Interval in seconds to measure RPM.
        """
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
        self.ppr = ppr
        self.logs_enabled = False
        self.measure_interval = measure_interval
        self.measure_timer = 0

    def setPower(self, power):
        """Set motor power manually (-1 to 1)."""
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
        """Increment pulse counter for RPM calculation."""
        self.pulse_count += 1

    def computeRPM(self, dt):
        """Compute RPM from pulses over dt seconds."""
        revolutions = self.pulse_count / self.ppr
        rpm = revolutions * (60 / dt)
        self.curr_rpm = rpm
        self.pulse_count = 0

    def setRPM(self, targetRPM):
        """Set target RPM for PID."""
        self.targ_rpm = targetRPM

    def getRPM(self):
        """Get current RPM."""
        return self.curr_rpm

    def enablePIDLogs(self):
        """Enable PID debug printing."""
        self.logs_enabled = True

    def getVelocity(self):
        """Get angular velocity in rad/s."""
        return self.rpmToRADS(self.curr_rpm)

    def setVelocity(self, velocity):
        """Set target velocity in rad/s."""
        self.targ_rpm = self.radsToRPM(velocity)

    def radsToRPM(self, omega):
        """Convert rad/s to RPM."""
        return omega * 30 / math.pi

    def rpmToRADS(self, rpm):
        """Convert RPM to rad/s."""
        return rpm * math.pi / 30

    def getLastDuty(self):
        """Return last applied PWM duty."""
        return self.last_duty

    def update(self, dt):
        """
        Update motor state:
        - Measure RPM
        - Compute PID duty
        - Apply PWM
        - Optionally print logs
        """
        self.measure_timer += dt
        if self.measure_timer >= self.measure_interval:
            self.computeRPM(self.measure_timer)
            self.measure_timer = 0

        duty = self.pid.compute(self.targ_rpm, self.curr_rpm, dt)

        if duty >= 0:
            self.motorA1.duty_u16(duty)
            self.motorA2.duty_u16(0)
        else:
            self.motorA1.duty_u16(0)
            self.motorA2.duty_u16(-duty)

        self.last_duty = duty

        if self.logs_enabled:
            print("RPM:", self.getRPM(), "Duty:", self.getLastDuty())
