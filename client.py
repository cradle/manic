# -*- coding: cp1252 -*-
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.spread import jelly
from twisted.spread import banana
import time

class NetworkClient(DatagramProtocol):
    def startProtocol(self):
        self.transport.connect("127.0.0.1", 9999)
        print "we can only send to %s now" % str(("127.0.0.1", 9999))
                
    def datagramReceived(self, data, (host, port)):
        print "%r" % (jelly.unjelly(banana.decode(data)))
        
    # Possibly invoked if there is no server listening on the
    # address to which we are sending.
    def connectionRefused(self):
        print "Noone listening"

    def send(self, obj):
        self.transport.write(banana.encode(jelly.jelly(obj)))
        
        
# 0 means any port, we don’t care in this case
client = NetworkClient()
reactor.listenUDP(0, client)
t = ""
while t != "exit":
    reactor.doIteration(0)
    t = raw_input(":")
    if t != "":
        client.send(eval(t))
    
