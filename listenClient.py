from client import Client
from server import Server
import guiobjects, time

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
        print "Self", self.player._name, "connected"
        self._stepNumber = 0
        self._startTime = time.time()

        bot = guiobjects.Person(self, "b1")
        bot.setPosition(self.spawnLocation())
        self.objects += [bot]
        
    def frameEnded(self, frameTime, keyboard, mouse):            
        Server.frameEnded(self, frameTime)
        self.updateChat(frameTime)
        self.displayScores()
        self.displayVitals()
        self.displayDebug()
        self.player.inputPresses(self.player.input(keyboard, mouse))
        return True # Keep going
        
    def networkUpdate(self):
        for o in self.objects:
            o.setEvents(o.getEvents())
        Server.networkUpdate(self)
        
    def sleep(self):
        # We don't want to sleep on the listen client
        pass

if __name__ == "__main__":
    engine = ListenClient()
    import cProfile
    cProfile.run('engine.go()', 'profile.txt')
    import os
    os._exit(0)
