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

    def __eq__(self, other):
        return self.address == other.address

    def push(self, data):
        if type(data) == list and len(data) > 0:
            if data[0] == "ping":
                self.send(["pong", data[1], time.time()])
            
        self.messages.insert(0,data)

    def hasMoreMessages(self):
        return len(self.messages) != 0

    def pop(self):
        return self.messages.pop()

    def send(self, data):
        self.transport.write(banana.encode(jelly.jelly(data)), self.address)
    
class NetworkServer(DatagramProtocol):
    def __init__(self):
        self.clients = []
        self.reactor = reactor
        self.reactor.listenUDP(9999, self)
        
    def datagramReceived(self, data, address):
        # Allocate the received datagram to the correct client
        client = Client(address, self.transport)
        if not self.clients.count(client):
            self.clients.append(client)
        else:
            client = self.clients[self.clients.index(client)]

        client.push(jelly.unjelly(banana.decode(data)))
        

    def update(self):
        self.reactor.doIteration(0)
