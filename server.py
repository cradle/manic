import engine
import networkserver
import os
import time

class Server(engine.Engine):
    def __init__(self):
        engine.Engine.__init__(self)
        self.network = networkserver.NetworkServer()
        self.timeBetweenNetworkUpdates = 0.1
        self.timeUntilNextNetworkUpdate = 0.0

    def frameEnded(self, frameTime):
        self.timeUntilNextNetworkUpdate -= frameTime
        if self.timeUntilNextNetworkUpdate <= 0.0:
            self.network.update()
            while self.timeUntilNextNetworkUpdate <= 0.0:
                self.timeUntilNextNetworkUpdate += self.timeBetweenNetworkUpdates

            for client in self.network.clients:
                client.send(["ping", time.time()])
                while client.hasMoreMessages():
                    print client.pop()

if __name__ == "__main__":
    engine = Server()
    engine.go()
    os._exit(0)
