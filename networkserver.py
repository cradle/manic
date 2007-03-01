from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.spread import jelly
from twisted.spread import banana

class Client():
    def __init__(self, address, transport):
        self.address = address
        self.messages = []
        self.transport = transport

    def __eq__(self, other):
        return self.address == other.address

    def push(self, data):
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
            client.send(["position", (0.0,0.0,0.0)])
        else:
            client = self.clients[self.clients.index(client)]

        client.push(jelly.unjelly(banana.decode(data)))
        

    def update(self):
        self.reactor.doIteration(0)
