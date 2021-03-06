from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.spread import banana
import time
import zlib

class Ping(object):
    _numberOfPings = 0

    def __init__(self):
        self._number = Ping._numberOfPings
        Ping._numberOfPings += 1
        self._time = time.time()
        self._roundTripTime = None

    def received(self):
        self._roundTripTime = time.time() - self._time

    def __eq__(self, other):
        return self._number == other._number

    def __repr__(self):
        if self._roundTripTime:
            return "%s (%.3f)" % (self._number, self._roundTripTime)
        else:
            return "%s" % self._number

class Client():
    def __init__(self, address, transport):
        self.address = address
        self.messages = []
        self.transport = transport
        self.lastMessageTime = time.time()
        self.timeout = 10.0
        self.pings = []
        self.player = None
        self.packetNumber = 0

    def __str__(self):
        return "%s:%i" % self.address

    def debug(self):
        output = ""
        output += "%s:%i " % self.address
        for message in self.messages:
            output += "    %s\n" % message
        output += "ping(%s) " % self.ping
        output += "#(%s)" % self.packetNumber
        return output

    def __eq__(self, other):
        return self.address == other.address

    def timedOut(self):
        return (time.time() - self.lastMessageTime) > self.timeout

    def push(self, data):
        if type(data) == list and len(data) > 0 and data[0] == "p":
            self.send(["p", data[1], time.time()])
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
        toSend = zlib.compress(banana.encode(data),4)
        self.transport.write(toSend, self.address)
        NetworkServer.debugSendPacketLength = len(toSend)

    def ping(self):
        p = Ping()
        self.send(["p", p.number])
        self.pings.append(p)
    
class NetworkServer(DatagramProtocol):
    debugSendPacketLength = 0
    
    def __init__(self, connectedCallback, port = 10001, debug = False):
        self.clients = []
        self.debug = debug
        self.reactor = reactor
        self.reactor.startRunning()
        self.reactor.listenUDP(port, self)
        self.connectedCallback = connectedCallback
        self.debugSendPacketLength = 0
        self.debugReceivePacketLength = 0
        if self.debug: print "Started"
        
    def datagramReceived(self, data, address):
        if self.debug: print "RCV",
        self.debugReceivePacketLength = len(data)
        # Allocate the received datagram to the correct client
        client = Client(address, self.transport)
        if client not in self.clients:
            if self.debug: print "!New!",
            self.clients.append(client)
            self.connectedCallback(client)
        else:
            client = self.clients[self.clients.index(client)]

        if self.debug: print client.debug()
        client.push(banana.decode(zlib.decompress(data)))

    def update(self, time = 0):
        self.debugSendPacketLength = NetworkServer.debugSendPacketLength
        self.reactor.runUntilCurrent()
        self.reactor.doIteration(0)

if __name__ == "__main__":
    def testCallback(client):
        print client
    
    server = NetworkServer(testCallback, debug = True)
    while(reactor.running):
        server.update(0.1)
        time.sleep(0.1)
