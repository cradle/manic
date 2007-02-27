from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.spread import jelly
from twisted.spread import banana

class Server(DatagramProtocol):
    def __init__(self):
        self.clients = []
        
    def datagramReceived(self, data, client):
        if not self.clients.count(client):
            self.clients.append(client)
            self.send("Success", client)
            
        print "received %r from %s" % (data, client)

    def send(self, obj, client):
        self.transport.write(banana.encode(jelly.jelly(obj)), client)
        

reactor.listenUDP(9999, Server())
reactor.run()
