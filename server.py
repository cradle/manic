from engine import Engine
import networkserver
import os
import time, encode
import gamenet
from objects import Person, StaticObject, DynamicObject, SphereObject

class Server(Engine):
    def __init__(self):
        Engine.__init__(self)
        port = 10001
        self.network = networkserver.NetworkServer(self.clientConnected, port)
        self.timeBetweenNetworkUpdates = 1.0/15.0
        self.timeUntilNextNetworkUpdate = 0.0
        self.clientNumber = 0
	self.debugNetworkTime = 0.0
	ip = "cradle.dyndns.org"
	self.serverChat = gamenet.NetCode("cradle", "cradle.dyndns.org", "AV-admin", "enter", "-".join([ip, str(port)]))
	self.serverChat.registerMessageListener(self.messageListener)
	self.serverChat.setNickName("admin")
	self.timeBetweenChatUpdates = 0.5
	self.timeUntilNextChatUpdate = 0.0
        print "Server started"

    def messageListener(self, name, message):
    	print name, ":", message

    def clientConnected(self, client):
        self.clientNumber += 1
        client.player = self.createPerson("p%i" % self.clientNumber)
        client.player.setPosition(self.spawnLocation())
        self.objects += [client.player]
        self.serverChat.sendMessage(client.player._name+ " connected")

    def _createWorld(self):
        Engine._createWorld(self)
        bot = Person(self, "b1")
        bot.setPosition(self.spawnLocation())
        self.objects += [bot]

    def networkUpdate(self):
        self.network.update()
        while self.timeUntilNextNetworkUpdate <= 0.0:
            self.timeUntilNextNetworkUpdate += self.timeBetweenNetworkUpdates

        for client in self.network.clients:
            if client.timedOut():
                self.serverChat.sendMessage(client.player._name + " timed out, disconnecting")
                client.player.close()
                self.objects.remove(client.player)
                self.network.clients.remove(client)

        timer = encode.timer()
        timer.start()

        for client in self.network.clients:                
            client.send([[[o._name,
                           o.getAttributes(),
                           1 if o._name == client.player._name else 0,
                           o.type,
                           o.getEvents()] for o in self.objects if o.shouldSendToClients()],
                        time.time(), self.timeUntilNextEngineUpdate])
            #parameter above is whether or not the player is the current player
                            
            while client.hasMoreMessages():
                client.player.inputPresses(client.pop())

        timer.stop()
        self.debugNetworkTime = timer.time()

        for o in self.objects:
            o.clearEvents()

    def frameEnded(self, frameTime):
        self.timeUntilNextNetworkUpdate -= frameTime
        if self.timeUntilNextNetworkUpdate <= 0.0:
            self.networkUpdate()
        
        Engine.frameEnded(self, frameTime)

        self.sleep()
        return self.network.reactor.running

    def sleep(self):
        time.sleep(min(self.timeUntilNextNetworkUpdate,
                       self.timeUntilNextEngineUpdate))


if __name__ == "__main__":
    engine = Server()
    import cProfile
    cProfile.run('engine.go()', 'server-profile.txt')
    os._exit(0)
