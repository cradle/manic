from engine import Engine
import networkserver
import os
import time
from objects import Person, StaticObject, DynamicObject, SphereObject

class Server(Engine):
    def __init__(self):
        Engine.__init__(self)
        self.network = networkserver.NetworkServer(self.clientConnected)
        self.timeBetweenNetworkUpdates = 1.0/15.0
        self.timeUntilNextNetworkUpdate = 0.0
        self.clientNumber = 0
        print "Server started"

    def clientConnected(self, client):
        self.clientNumber += 1
        client.player = self.createPerson("p%i" % self.clientNumber)
        client.player.setPosition(self.spawnLocation())
        self.objects += [client.player]
        self._stats[client.player._name] = {}
        self._stats[client.player._name]["ping"] = 0
        self._stats[client.player._name]["score"] = 0
        print "Client", client.player._name, " connected"

    def _createWorld(self):
        Engine._createWorld(self)
        bot = Person(self, "b1")
        bot.setPosition(self.spawnLocation())
        self.objects += [bot]

    def networkUpdate(self):
        self.network.update()

        for client in self.network.clients:
            self._stats[client.player._name]["ping"] = client.ping
        
        for client in self.network.clients:                
            client.send(["stats", self._stats])

        while self.timeUntilNextNetworkUpdate <= 0.0:
            self.timeUntilNextNetworkUpdate += self.timeBetweenNetworkUpdates

        for client in self.network.clients:
            if client.timedOut():
                print "Client", client.player._name, "timed out, disconnecting"
                del self._stats[client.player._name]
                client.player.close()
                self.objects.remove(client.player)
                self.network.clients.remove(client)

        for client in self.network.clients:                
            client.send([[[o._name,
                           o.getAttributes(),
                           o._name == client.player._name,
                           o.type,
                           o.getEvents()] for o in self.objects],
                        time.time()])
            #parameter above is whether or not the player is the current player
            client.player.setEvents(client.player.getEvents())
            
                
            while client.hasMoreMessages():
                client.player.inputPresses(client.pop())

        for o in self.objects:
            o.clearEvents()

    def frameEnded(self, frameTime):
        self.timeUntilNextNetworkUpdate -= frameTime
        if self.timeUntilNextNetworkUpdate <= 0.0:
            self.networkUpdate()
        
        Engine.frameEnded(self, frameTime)

        self.sleep()
        return True

    def sleep(self):
        time.sleep(min(self.timeUntilNextNetworkUpdate,
                       self.timeUntilNextEngineUpdate))


if __name__ == "__main__":
    engine = Server()
    engine.go()
    os._exit(0)
