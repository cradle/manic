# -*- coding: cp1252 -*-
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.spread import jelly
from twisted.spread import banana
import time

class ping(object):
    def __init__(self, number, time):
        self.number = number
        self.time = time

class NetworkClient(DatagramProtocol):
    def __init__(self, serverIP = "127.0.0.1", port = 9999):
        self._messages = []
        self.reactor = reactor
        self.serverIP = serverIP
        self.port = port
        self.reactor.listenUDP(0, self)
        self._pingSendTime = time.time()
        self.roundTripTime = 0.0
        self.serverOffset = 0.0
        self.lastPingNumber = 0
        self.pings = []
        self.pingNumber = 0
        self.timeBetweenPings = 0.5
        self.timeUntilNextPing = 0.0

    def ping(self):
        self.pingNumber += 1
        self.send(["ping", self.pingNumber])
        self.pings.append(ping(self.pingNumber, time.time()))
        
    def startProtocol(self):
        self.transport.connect(self.serverIP, self.port)

    def datagramReceived(self, data, (host, port)):
        message = jelly.unjelly(banana.decode(data))
        if type(message[0]) == str and message[0] == "pong":
            for ping in self.pings:
                if ping.number == message[1]:
                    self.roundTripTime = time.time() - ping.time;
                    self.serverOffset = time.time() - (message[2] + self.roundTripTime/2)
                    self.pings = [p for p in self.pings if p.number <= ping.number]
        else:
            self._messages.insert(0,message)
        
    # Possibly invoked if there is no server listening on the
    # address to which we are sending.
    def connectionRefused(self):
        pass
        #print "Noone listening"

    def send(self, obj):
        self.transport.write(banana.encode(jelly.jelly(obj)))

    def update(self, elapsedTime):
        self.timeUntilNextPing -= elapsedTime
        if self.timeUntilNextPing <= 0.0:
            self.ping()
            while self.timeUntilNextPing <= 0.0:
                self.timeUntilNextPing += self.timeBetweenPings
                
        self.reactor.doIteration(0)

if __name__ == "__main__":
    # 0 means any port, we don’t care in this case
    client = NetworkClient()
    reactor.listenUDP(0, client)
    t = ""
    while t != "exit":
        reactor.doIteration(0)
        t = raw_input(":")
        if t != "":
            client.send(eval(t))
    
