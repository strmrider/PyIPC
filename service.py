import socket, threading
from models import *

class Service:
    """
    The service runs as a server on the local machine and transfers data between connected processes.
    """
    def __init__(self, port):
        """
        :param port: int; service's port number
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((LOCAL_ADDRESS, port))
        self.lock = threading.Lock()
        self.processes = {}
        self.events = {}

    def run(self):
        """
        Runs the service
        """
        self.socket.listen(5)
        while True:
            connection, address = self.socket.accept()
            threading.Thread(target=self._handle_client, args=(connection,)).start()

    def _handle_client(self, connection):
        """
        Registers new process
        :param connection: socket
        """
        process_id = connection.recv(4)
        process_id = struct.unpack("!I", process_id)[0]
        print (process_id , "registered")
        new_process = Process(process_id, connection)
        self.lock.acquire()
        self.processes[process_id] = new_process
        self.lock.release()

        self.handle_income_request(new_process)

    def handle_income_request(self, process):
        """
        Listens for income requests from registered process and handles it, whether it's data transfer or
        events managements instructions
        :param process: Process; registered process
        """
        while True:
            request = process.receive()
            action = struct.unpack("!B", request[:1])[0]
            request = request[1:]
            if action == CREATE_EVENT:
                self.handle_event_creation(process, request)
            elif action == DISSOLVE_EVENT:
                self.handle_dissolve(process, request)
            elif action == SUBSCRIBE or action == UNSUBSCRIBE:
                self.handle_subscription(process, action, request)
            elif action == EMIT:
                self.handle_emission(process, request)
            elif action == CONTACT_PROCESS:
                self.handle_process_contact(request)
            elif action == LISTEN_ON or action == LISTEN_OFF:
                process.listening = action

    def handle_event_creation(self, process, request):
        """
        Handles event creation request
        :param process: Process; event's creator
        :param request: bytes; the request
        """
        mode = struct.unpack("!B", request[:1])[0]
        event_id = request[1:].decode()
        creator = None if mode == MULTI_EMISSION else process.id
        self.lock.acquire()
        event = Event(event_id, mode, creator)
        if mode == MULTI_EMISSION:
            event.add_subscription(process.id)
        self.events[event_id] = event
        self.lock.release()

    def handle_subscription(self, process, action, request):
        """
        Handles new subscription request to an event
        :param process: Process; subscribed process
        :param action: int; subscribe or unsubscribe
        :param request: bytes; the request
        """
        event_id = request.decode()
        self.lock.acquire()
        if event_id in self.events:
            event = self.events[event_id]
            if action == SUBSCRIBE:
                event.add_subscription(process.id)
                if event.mode == MULTI_EMISSION:
                    header = struct.pack("!B", OPEN_EVENT)
                    process.send(bytearray(header + event_id.encode()))
            elif action == UNSUBSCRIBE:
                event.remove_subscription(process.id)
                if event.mode == MULTI_EMISSION and len(event.subscribers) == 0:
                    del self.events[event.id]
        self.lock.release()

    def handle_dissolve(self, process, request):
        """
        Handles event dissolvement request
        :param process: Process; event's creator
        :param request: bytes; the request
        :return:
        """
        event_id = request.decode()
        self.lock.acquire()
        event = self.events[event_id]
        self.lock.release()
        if event:
            if event.mode == SINGLE_EMISSION and event.creator == process.id:
                del self.events[event_id]

    def handle_emission(self, process, request):
        """
        Handles event emission. Only permitted processes can emit events
        :param process: Process; emitting process
        :param request: bytes
        """
        event_id_len = struct.unpack("!I", request[:4])[0]
        event_id = request[4:event_id_len+4].decode()
        if event_id in  self.events:
            event = self.events[event_id]
            if event.mode == MULTI_EMISSION or (event.mode == SINGLE_EMISSION and event.creator == process.id):
                data = request[event_id_len+4:]
                header = struct.pack("!B I", EMIT, len(event_id))
                pack = bytearray(header +  event_id.encode() + data)
                for subscriber in event.subscribers:
                    # avoids sending to yourself
                    if subscriber != process.id:
                        self.processes[subscriber].send(pack)

    def handle_process_contact(self,request):
        """
        handles direct contact request
        :param request: bytes
        """
        target_id = struct.unpack("!I", request[:4])[0]
        data = request[4:]
        if target_id in self.processes:
            target_process = self.processes[target_id]
            if target_process.listening == LISTEN_ON:
                pack = bytearray(struct.pack("!B", CONTACT_PROCESS) + data)
                target_process.send(pack)

if __name__ == "__main__":
    s = Service(42356)
    s.run()