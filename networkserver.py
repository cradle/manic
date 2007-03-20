from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import cerealizer
import time
import zlib

class Client():
    def __init__(self, address, transport):
        self.address = address
        self.messages = []
        self.transport = transport
        self.lastMessageTime = time.time()
        self.timeout = 10.0
        self.ping = 0.0
        self.player = None
        self.packetNumber = 0

    def __eq__(self, other):
        return self.address == other.address

    def timedOut(self):
        return (time.time() - self.lastMessageTime) > self.timeout

    def push(self, data):
        if type(data) == list and len(data) > 0 and data[0] == "ping":
            self.send(["pong", data[1], time.time()])
            self.ping = data[2]
            if self.player:
                self.player.ping = data[2]
        else:
            self.messages.insert(0,data)
            
        self.lastMessageTime = time.time()

    def hasMoreMessages(self):
        return len(self.messages) != 0

    def pop(self):
        return self.messages.pop()

    def send(self, data):
        #toSend = zlib.compress(banana.encode(data),4)
        #toSend = banana.encode(data)
        toSend = zlib.compress(cerealizer.dumps(data), 4)
        self.transport.write(toSend, self.address)
        NetworkServer.debugSendPacketLength = len(toSend)
    
class NetworkServer(DatagramProtocol):
    debugSendPacketLength = 0
    
    def __init__(self, connectedCallback):
        self.clients = []
        self.reactor = reactor
        self.reactor.startRunning()
        self.reactor.listenUDP(10001, self)
        self.connectedCallback = connectedCallback
        self.debugSendPacketLength = 0
        self.debugReceivePacketLength = 0
        
    def datagramReceived(self, data, address):
        self.debugReceivePacketLength = len(data)
        # Allocate the received datagram to the correct client
        client = Client(address, self.transport)
        if client not in self.clients:
            self.clients.append(client)
            self.connectedCallback(client)
        else:
            client = self.clients[self.clients.index(client)]

        client.push(cerealizer.loads(zlib.decompress(data)))

    def update(self, time = 0):
        self.debugSendPacketLength = NetworkServer.debugSendPacketLength
        self.reactor.runUntilCurrent()
        self.reactor.doIteration(0)
