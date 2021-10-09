import struct

REGISTER = 0
LISTEN_ON = 1
LISTEN_OFF = 2
CREATE_EVENT = 3
DISSOLVE_EVENT = 4
SUBSCRIBE = 5
UNSUBSCRIBE = 6
EMIT = 7
# new multi event
OPEN_EVENT = 77
CONTACT_PROCESS = 8

# only the creator can emit the event
SINGLE_EMISSION = 0
# all subscribers can emit events
MULTI_EMISSION = 1

LOCAL_ADDRESS = '127.0.0.1'

class SocketWrapper:
    """
    Wrappers socket object for extended receive and send methods
    """
    def __init__(self, sock):
        self.socket = sock

    def send(self, data):
        size = struct.pack('!I', len(data))
        self.socket.sendall(size)
        self.socket.sendall(data)

    def _receive(self, data_size):
        data = b''
        while len(data) < data_size:
            buffer = self.socket.recv(data_size - len(data))
            if buffer:
                data += buffer
            else:
                raise Exception("Connection lost")
        return data

    def receive(self):
        size = struct.unpack("!I", self.socket.recv(4))[0]
        return self._receive(size)

class Process:
    """
    Process container. Registered process
    """
    def __init__(self, process_id, sock):
        self.id = process_id
        self.socket = SocketWrapper(sock)
        self.subscriptions = []
        self.listening = LISTEN_ON

    def set_listening(self, status):
        self.listening = status

    def receive(self):
        return self.socket.receive()

    def send(self, data):
        self.socket.send(data)


class Event:
    """
    Events are used to connect processes by a specific defined call
    Stores event's data (id, mode) and subscribers
    """
    def __init__(self, event_id, mode, creator=None):
        """
        Initializes an event
        :param event_id: str; event's id
        :param mode: event;s mode: Multi emission or single
        :param creator: str; Creator;s process's id
        """
        self.id = event_id
        self.mode = mode
        self.creator = creator
        self.subscribers = []

    def remove_subscription(self, process_id):
        """
        Removes a process subscriber
        :param process_id: str; subscribed process
        """
        self.subscribers.remove(process_id)

    def add_subscription(self, process_id):
        """
        Subscribes a process
        :param process_id: str; subscribed process
        """
        self.subscribers.append(process_id)