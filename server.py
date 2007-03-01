from engine import Engine
import networkserver
import os
import time

class Server(Engine):
    def __init__(self):
        Engine.__init__(self)
        self.network = networkserver.NetworkServer()
        self.timeBetweenNetworkUpdates = 0.1
        self.timeUntilNextNetworkUpdate = 0.0

    def frameEnded(self, frameTime):
        Engine.frameEnded(self, frameTime)
        
        self.timeUntilNextNetworkUpdate -= frameTime
        if self.timeUntilNextNetworkUpdate <= 0.0:
            self.network.update()
            while self.timeUntilNextNetworkUpdate <= 0.0:
                self.timeUntilNextNetworkUpdate += self.timeBetweenNetworkUpdates

            for client in self.network.clients:
                for object in self.objects:
                    client.send([object._name,object.getAttributes()])
                    
                while client.hasMoreMessages():
                    # Client input (keyboard/mouse)
                    print client.pop()

if __name__ == "__main__":
    engine = Server()
    engine.go()
    os._exit(0)
