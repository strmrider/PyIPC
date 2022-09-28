# PyIPC
Light Python Inter process communication system (IPC)

* Event driven communication
* Light asynchronous notifications ([Signals](https://en.wikipedia.org/wiki/Signal_(IPC)))
* [Shared memory](https://en.wikipedia.org/wiki/Shared_memory) mechanism
## Examples
### Event driven communication
#### Service
Run the server
```Python
port = 54121
server = Servive(port)
# runs the server and connect registered processes
server.run()
```
#### Process Node
Preliminary data
```Python
# data handler (prints income data)
def data_handler(data):
    print (data)

port = 54121
data = b'sample message'
```
Connect current process to the service
```Python
node = ProcessNode(port)
# listens to income data
node.listen()
```
Contact peer process directly
```Python
target_process_id = 11168
node.contact(target_process_id, data)
```
Handle events
```Python
# create a new event
node.create_event("new event", MULTI_EMISSION, data_handler)
# emit the event with a data
node.emit("new event", data)
# subscribe to events
node.subscribe([TARGET EVENT ID], data_handler)
```
##### API
* **`listen(handler)`**
    
    Listens for income data through the service and handles it accordingly. Receives handler function.

* **`contact(process_id, data)`**
    
    Contacts a process directly. Receives target process's id and data to be send.
    
* **`subscribe(event_id, handler)`**
    
    Subscribes to an event in the service. Receives event's id and a function that handles income data.
    
* **`unsubscribe(event_id)`**

    Unsubscribes from an event
    
* **`create_event(event_id, event_type, handler=None)`**

    Creates an event on the service. Reveives event's id, type (SINGLE_EMISSION - only the event's creator can emit the event
    MULTI_EMISSION - all event's subscribers can emit the event) and a specfic handler function (optional).

* **`dissolve_event(event_id)`**

    Dissolves and event from the service.

* **`emit(event_id, data)`**

    Emits an event and sends the data. Reveives the emitted event's id and data in bytes.

* **`get_subscriptions()`**

    Returns a list of all the subscribed events.
    
### Signals system
Run the service
```Python
from signal import SignalService
port = 54121
server = SignalService()
server.start()
```
Signal target processes
```Python
from signal import Signal

# signals handler
def signal_handler():
    print ('New signal has been received')
    
proc_signal = Signal(port)
# listens to signals
proc_signal.listen(signal_handler)

# signal other process
target_process_id = 12000
proc_signal.signal(target_process_id)
```
