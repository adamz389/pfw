# ViperIDE - MicroPython Web IDE
# Read more: https://github.com/vshymanskyy/ViperIDE

# Connect your device and start creating! 🤖👨‍💻🕹️

# You can also open a virtual device and explore some examples:
# https://viper-ide.org?vm=1


import network
import socket
import time


class Connection:
    ssid = "RPSWireless"
    password = "test"

    def connect(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(self.ssid, self.password)
        while not wlan.isconnected():
            time.sleep(0.1)
        return wlan.ifconfig()[0]

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
                data = cl.recv(1024)
                print(data)
                cl.send(b"OK")
            except OSError:
                pass
            cl.close()

