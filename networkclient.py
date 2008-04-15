# -*- coding: cp1252 -*-
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.spread import banana
from collections import deque
from encode import timer
import zlib
import time

class ping(object):
    def __init__(self, number, time):
        self.number = number
        self.time = time

class NetworkClient(DatagramProtocol):
    def __init__(self, host = "127.0.0.1", port = 10001):
        self._messages = deque()
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
        self.debugSendPacketLength = 0
        self.debugReceivePacketLength = 0

    def gotIP(self, ip):
        print "Got IP", ip
        self.serverIP = ip
        self.reactor.listenUDP(0, self)

    def ping(self):
        if self.serverIP != None:
            self.pingNumber += 1
            self.send(["p", self.pingNumber, int(self.roundTripTime*100)])
            self.pings.append(ping(self.pingNumber, time.time()))
        
    def startProtocol(self):
        self.transport.connect(self.serverIP, self.port)
        
    def datagramReceived(self, data, (host, port)):
        t = timer()
        self.debugReceivePacketLength = len(data)
        t.start()
        message = banana.decode(zlib.decompress(data))
        #message = banana.decode(data)
        #message = cerealizer.loads(zlib.decompress(data))
        t.stop()
        if type(message[0]) == str and message[0] == "p":
            for ping in self.pings:
                if ping.number == message[1]:
                    self.roundTripTime = time.time() - ping.time;
                    self.serverOffset = time.time() - (message[2] + self.roundTripTime/2)
                    self.pings = [p for p in self.pings if p.number <= ping.number]
        else:
            self._messages.append(message)

    # Possibly invoked if there is no server listening on the
    # address to which we are sending.
    def connectionRefused(self):
        print "No Server"

    def send(self, obj):
        data = zlib.compress(banana.encode(obj),1)
        self.transport.write(data)
        self.debugSendPacketLength = len(data)

    def update(self, elapsedTime):
        if self.serverIP != None:
            self.timeUntilNextPing -= elapsedTime
            if self.timeUntilNextPing <= 0.0:
                self.ping()
                self.timeUntilNextPing = self.timeBetweenPings
                
        self.reactor.runUntilCurrent()
        self.reactor.doIteration(0)

    def clearMessages(self):
        self._messages.clear()

if __name__ == "__main__":
    client = NetworkClient()
    while(True):
        client.update(5)
        time.sleep(5)
    
