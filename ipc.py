import socket, threading, os, uuid, time
from models import *

class ProcessNode:
    """
    Creates a process node on the service, which receives and sends data or instructions (commands)
    Communication between nodes may be done by direct contact (using process's id number) or by events system for
    multiple communication.
    """
    def __init__(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = SocketWrapper(sock)
        self.id = os.getpid()
        self.handlers = {}
        self.admin_events = []
        # list of authorized emits (open events). prevents false requests of unauthorized emits
        self.emissions = []

        print (self.id)
        try:
            sock.connect(('127.0.0.1', port))
            pack = struct.pack("!I", self.id)
            sock.sendall(pack)
            print("connected")
        except:
            raise Exception ('Connection failed')

    def listen(self, handler):
        """
        Starts listening thread
        :param handler: callable; handler function
        """
        threading.Thread(target=self.__listen, args=(handler,)).start()

    def __listen(self, handler):
        """
        Listens for income data through the service and handles it accordingly
        :param handler: callable; handler function
        """
        while True:
            response = self.socket.receive()
            action = struct.unpack("!B", response[:1])[0]
            response = response[1:]
            if action == CONTACT_PROCESS:
                handler(response)
            elif action == EMIT:
                self.__handle_emission(response)
            # notification of a multi emission event.
            # Adds the event to the emissions list enabling the user to emit the event at any time
            elif action == OPEN_EVENT:
                event_id = response.decode()
                self.emissions.append(event_id)

    def __handle_emission(self, response):
        """
        Handles income event emission
        :param response: bytes
        :return:
        """
        event_id_len = struct.unpack("!I", response[:4])[0]
        event_id = response[4:event_id_len + 4].decode()
        data = response[event_id_len + 4:]
        if event_id in self.handlers:
            self.handlers[event_id](data)

    def contact(self, process_id, data):
        """
        Contacts a process directly
        :param process_id: int; target process's id
        :param data: bytes; data to be send
        """
        if self.id != process_id:
            header = struct.pack("! B I", CONTACT_PROCESS, process_id)
            pack = bytearray(header + data)
            self.socket.send(pack)

    def subscribe(self, event_id:str, handler):
        """
        Subscribes to an event in the service
        :param event_id: str; event's id
        :param handler: callable; callback function to handle income data
        """
        if event_id in self.admin_events:
            raise Exception("Can't subscribe to admin event")
        self.handlers[event_id] = handler
        header = struct.pack("!B", SUBSCRIBE)
        pack = bytearray(header + event_id.encode())
        self.socket.send(pack)

    def unsubscribe(self, event_id):
        """
        Unsubscribes from an event
        :param event_id: str; event's id
        """
        if event_id in self.admin_events:
            raise Exception("Can't unsubscribe from own event. Use dissolve event instead")
        del self.handlers[event_id]
        if event_id in self.emissions:
            self.emissions.remove(event_id)
        header = struct.pack("!B", UNSUBSCRIBE)
        pack = bytearray(header + event_id.encode())
        self.socket.send(pack)

    def create_event(self, event_id, event_type, handler=None):
        """
        Creates an event on the service
        :param event_id: str; event's id
        :param event_type: event type (int);
                          * SINGLE_EMISSION - only the event's creator can emit the event
                          * MULTI_EMISSION- all event's subscribers can emit the event
        :param handler: callable; callback function to handle income data
        :return:
        """
        event_id = event_id if event_id else str(uuid.uuid4()).replace('-', '')
        header = struct.pack("! B B", CREATE_EVENT, event_type)
        pack = bytearray(header + event_id.encode())
        self.socket.send(pack)
        if event_type == MULTI_EMISSION and handler:
            self.handlers[event_id] = handler
        elif event_type == SINGLE_EMISSION:
            self.admin_events.append(event_id)

        return event_id

    def dissolve_event(self, event_id):
        """
        Dissolves and event from the service
        :param event_id: str; event's id
        """
        if event_id in self.admin_events:
            header = struct.pack("! B I", DISSOLVE_EVENT, len(event_id))
            pack = bytearray(header + event_id.encode())
            self.socket.send(pack)
            self.admin_events.remove(event_id)
            self.emissions.remove(event_id)

    def emit(self, event_id, data):
        """
        Emits an event and sends the data
        :param event_id: str; event's id
        :param data: bytes
        """
        if event_id not in self.emissions and event_id not in self.admin_events:
            raise Exception("Process is not authorized to emit the event")
        header = struct.pack("!B I", EMIT, len(event_id))
        pack = bytearray(header + event_id.encode() + data)
        self.socket.send(pack)

    def get_subscriptions(self):
        """
        Returns all subscribed events
        :return: list
        """
        return self.handlers.keys()

def p(data):
    print(data)

if __name__ == "__main__":
    c = ProcessNode(42356)
    c.listen(p)
    #c.contact(11168, b'hello')
    c.create_event("newEvent", MULTI_EMISSION, p)
    #c.subscribe("12", p)
    time.sleep(10)
    c.emit("newEvent", b'hello')
    time.sleep(25)
    c.emit("newEvent", b'hello')