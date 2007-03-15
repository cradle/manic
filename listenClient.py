from client import Client
from server import Server
import guiobjects

class ListenClient(Client, Server):
    def __init__(self):
        Client.__init__(self, True)
        Server.__init__(self)

    def _createScene(self):
        Client._createScene(self)
        self.clientNumber += 1
        self.player = guiobjects.Player(self, "p%i" % self.clientNumber, self.camera)
        self.chat.setNickName(self.player._name)
        self.player.setPosition(self.spawnLocation())
        self.objects += [self.player]
        self._stats[self.player._name] = {}
        self._stats[self.player._name]["ping"] = 0
        self._stats[self.player._name]["score"] = 0
        print "Self", self.player._name, "connected"
        
    def frameEnded(self, frameTime, keyboard, mouse):            
        Server.frameEnded(self, frameTime)
        self.updateChat(frameTime)
        self.displayScores()
        self.displayVitals()
        self.player.inputPresses(self.player.input(keyboard, mouse))
        return True # Keep going
        
    def networkUpdate(self):
        self.player.setEvents(self.player.getEvents())
        Server.networkUpdate(self)
        
    def sleep(self):
        # We don't want to sleep on the listen client
        pass

if __name__ == "__main__":
    engine = ListenClient()
    engine.go()
    import os
    os._exit(0)
