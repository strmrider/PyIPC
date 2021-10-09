import socket, threading, struct

class SignalService:
    def __init__(self, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('127.0.0.1', port))
        self.addresses = []

    def start(self):
        while True:
            signal, addr = self.socket.recvfrom(1)
            self.addresses.append(addr)
            for address in self.addresses:
                if address != addr:
                    self.socket.sendto(signal, address)

class Signal:
    def __init__(self, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address =('127.0.0.1', port)

    def listen(self, handler):
        self.socket.sendto(b'0', self.address)
        threading.Thread(target=self.__listen, args=(handler,)).start()

    def __listen(self, handler):
        while True:
            signal = self.socket.recvfrom(1024)
            signal = struct.pack("!?", signal[0])[0]
            handler(signal)

    def signal(self, signal:bool):
        signal = struct.pack("!?", signal)
        self.socket.sendto(signal, self.address)

def print_signal(d):
    print (d)

def run_server():
    s = SignalService(12000)
    s.start()

def run_client():
    c = Signal(12000)
    c.listen(print_signal)

if __name__ == "__main__":
    #run_server()
    run_client()
