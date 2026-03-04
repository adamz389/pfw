class Connection:
    def __init__(self):
        gc.collect()
        self.ap = network.WLAN(network.AP_IF)
        self.command_map = {}
        self.s = None

    def create(self):
        self.ap.active(True)
        self.ap.config(essid="pico123", password="12345678")
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

    def update(self):
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
            pass  # No client connected
