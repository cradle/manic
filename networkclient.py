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
    def __init__(self, host = "127.0.0.1", port = 10001):
        self._messages = []
        self.reactor = reactor
        self.serverIP = None
        self.port = port
        self.reactor.startRunning()
        self.reactor.resolve(host).addCallback(self.gotIP)
        self._pingSendTime = time.time()
        self.roundTripTime = 0.0
        self.serverOffset = 0.0
        self.lastPingNumber = 0
        self.pings = []
        self.pingNumber = 0
        self.timeBetweenPings = 0.5
        self.timeUntilNextPing = 0.0
        self._stats = {}

    def gotIP(self, ip):
        print "Got IP", ip
        self.serverIP = ip
        self.reactor.listenUDP(0, self)

    def ping(self):
        if self.serverIP != None:
            self.pingNumber += 1
            self.send(["ping", self.pingNumber, self.roundTripTime])
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
        elif type(message[0]) == str and message[0] == "stats":
            self._stats = message[1]
        else:
            #self._messages.insert(0,message)
            self._messages += [message]
        
    # Possibly invoked if there is no server listening on the
    # address to which we are sending.
    def connectionRefused(self):
        print "No Server"

    def send(self, obj):
        self.transport.write(banana.encode(jelly.jelly(obj)))

    def update(self, elapsedTime):
        if self.serverIP != None:
            self.timeUntilNextPing -= elapsedTime
            if self.timeUntilNextPing <= 0.0:
                self.ping()
                while self.timeUntilNextPing <= 0.0:
                    self.timeUntilNextPing += self.timeBetweenPings
                
        self.reactor.runUntilCurrent()
        self.reactor.doIteration(0)

if __name__ == "__main__":
    # 0 means any port, we don’t care in this case
    client = NetworkClient("cradle.dyndns.org")
    while(True):
        client.update(0.1)
    
