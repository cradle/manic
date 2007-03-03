from engine import Engine
import networkserver
import os
import time
from objects import Person

class Server(Engine):
    def __init__(self):
        Engine.__init__(self)
        self.network = networkserver.NetworkServer(self.clientConnected)
        self.timeBetweenNetworkUpdates = 0.01
        self.timeUntilNextNetworkUpdate = 0.0
        self.clientNumber = 0

    def clientConnected(self, client):
        self.clientNumber += 1
        client.player = Person(self, "p%i" % self.clientNumber)
        client.player.setPosition((0.0,20.0,0.0))
        self.objects += [client.player]

    def frameEnded(self, frameTime):
        Engine.frameEnded(self, frameTime)
        
        self.timeUntilNextNetworkUpdate -= frameTime
        if self.timeUntilNextNetworkUpdate <= 0.0:
            self.network.update()
            while self.timeUntilNextNetworkUpdate <= 0.0:
                self.timeUntilNextNetworkUpdate += self.timeBetweenNetworkUpdates

            for client in self.network.clients:
                client.send([[[o._name,o.getAttributes()] for o in self.objects],
                            time.time()])
                    
                while client.hasMoreMessages():
                    client.player.inputPresses(client.pop())
                    
        time.sleep(min(self.timeUntilNextChatUpdate,
                       self.timeUntilNextNetworkUpdate,
                       self.timeUntilNextEngineUpdate))

if __name__ == "__main__":
    engine = Server()
    engine.go()
    os._exit(0)
