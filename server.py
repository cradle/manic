from engine import Engine
import networkserver
import os
import time
from objects import Person, StaticObject, DynamicObject, SphereObject

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

    def _createWorld(self):
        Engine._createWorld(self)
        static = StaticObject(self, "bottom", size=(50,1,3))
        static.setPosition((0,0,0))
        self.statics += [static]
  
        static = StaticObject(self, "back", size=(51,51,3))
        static.setPosition((0,25,-5))
        self.statics += [static]
  
        static = StaticObject(self, "top", size=(50,1,3))
        static.setPosition((0,50,0))
        self.statics += [static]
            
        static = StaticObject(self, "%s" % 1, size=(10,1,3))
        static.setPosition((10,5,0))
        self.statics += [static]
        
        static = StaticObject(self, "%s" % 2, size=(10,1,3))
        static.setPosition((-10.5,10,0))
        self.statics += [static]
            
        static = StaticObject(self, "%sa" % 3, size=(10,1,3))
        static.setPosition((20,7.5,0))
        static.setRotation((-0.84851580858230591,0,0,0.52916997671127319))
        self.statics += [static]
            
        static = StaticObject(self, "%s" % 4, size=(10,1,3))
        static.setPosition((-15,15,0))
        self.statics += [static]
        
        static = StaticObject(self, "%sl" % 5, size=(1,50,3))
        static.setPosition((-25,25,0))
        self.statics += [static]

        static = StaticObject(self, "%sr" % 6, size=(1,50,3))
        static.setPosition((25,25,0))
        self.statics += [static]

        for i in range(3):
            for j in range(3):
                dynamic = SphereObject(self, "%i-%i-ball" % (i,j))
                dynamic.setPosition((0+i,30+j,0))
                self.objects += [dynamic]

    def frameEnded(self, frameTime):
        self.timeUntilNextNetworkUpdate -= frameTime
        if self.timeUntilNextNetworkUpdate <= 0.0:
            self.network.update()
            while self.timeUntilNextNetworkUpdate <= 0.0:
                self.timeUntilNextNetworkUpdate += self.timeBetweenNetworkUpdates

            for client in self.network.clients:
                if client.timedOut():
                    print "Client", client.player._name, "timed out, disconnecting"
                    self.objects.remove(client.player)
                    self.network.clients.remove(client)

            for client in self.network.clients:                
                client.send([[[o._name,
                               o.getAttributes(),
                               o._name == client.player._name,
                               o._body.objectType] for o in self.objects],
                            time.time()])
                #parameter above is whether or not the player is the current player
                    
                while client.hasMoreMessages():
                    client.player.inputPresses(client.pop())
                    
        time.sleep(min(self.timeUntilNextChatUpdate,
                       self.timeUntilNextNetworkUpdate,
                       self.timeUntilNextEngineUpdate))
        
        Engine.frameEnded(self, frameTime)

if __name__ == "__main__":
    engine = Server()
    engine.go()
    os._exit(0)
