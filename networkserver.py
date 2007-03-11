from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.spread import jelly
from twisted.spread import banana
import time

class Client():
    def __init__(self, address, transport):
        self.address = address
        self.messages = []
        self.transport = transport
        self.lastMessageTime = time.time()
        self.timeout = 10.0
        self.ping = 0.0
        self.packetNumber = 0

    def __eq__(self, other):
        return self.address == other.address

    def timedOut(self):
        return (time.time() - self.lastMessageTime) > self.timeout

    def push(self, data):
        if type(data) == list and len(data) > 0 and data[0] == "ping":
            self.send(["pong", data[1], time.time()])
            self.ping = data[2]
        else:
            self.messages.insert(0,data)
            
        self.lastMessageTime = time.time()

    def hasMoreMessages(self):
        return len(self.messages) != 0

    def pop(self):
        return self.messages.pop()

    def send(self, data):
        self.transport.write(banana.encode(jelly.jelly(data)), self.address)
    
class NetworkServer(DatagramProtocol):
    def __init__(self, connectedCallback):
        self.clients = []
        self.reactor = reactor
        self.reactor.listenUDP(10001, self)
        self.connectedCallback = connectedCallback
        
    def datagramReceived(self, data, address):
        # Allocate the received datagram to the correct client
        client = Client(address, self.transport)
        if client not in self.clients:
            self.clients.append(client)
            self.connectedCallback(client)
        else:
            client = self.clients[self.clients.index(client)]

        client.push(jelly.unjelly(banana.decode(data)))

    def update(self):
        self.reactor.doIteration(0)
