import math, os, time
import ode
from engine import Engine
import objects
from objects import *
import networkclient
import gamenet
from encode import timer

class Bot(Engine):
    def __init__(self, autoConnect = False):
        Engine.__init__(self)

        self.debugNetworkTime = 0 
        self.debugChatTime = 0
        #ip, port = "cradle.dyndns.org", "10001"
        ip, port = "127.0.0.1", "10001"

        if not autoConnect:
            address = raw_input("server ('%s:%s') :> " % (ip, port))
            
            if address != "":
                split = address.split(":")
                ip = split[0]
                if len(split) == 2:
                    port = split[1]

        self.chat = gamenet.NetCode("cradle", "cradle.dyndns.org", "AV", "enter", "-".join([ip, port]))
        self.chat.registerMessageListener(self.messageListener)
        self.timeBetweenChatUpdates = 0.5
        self.timeUntilNextChatUpdate = 0.0            
            
        self.network = networkclient.NetworkClient(ip, int(port))
        self.timeBetweenNetworkUpdates = 0.02
        self.timeUntilNextNetworkUpdate = 0.0
        self.serverRoundTripTime = 0.0
        self.lastServerUpdate = time.time()
        self.player = None
    
    def sendText(self):
        self.chat.sendMessage('sending text')

    def messageListener(self, name, message):
        if message.startswith("/me") and len(message[3:].strip()) > 0 :
            self.appendText("*" + name + " " + message[3:].strip())
        else:
            self.appendText(name + ": " + message)            

    def appendText(self, text):
        print text,
    
    def displayDebug(self):
        print ("1/FPS:%0.2f, " +
             "1Step:%0.2f, " +
             "#Steps:%i, " +
             "ST:%0.2f, " +
             "Net:%0.2f, " +
             "Cht:%0.2f, " +
             "SND:%i, " +
             "RCV:%i") % \
              (self.debugFrameTime,
               (self.debugStepTime / self.debugNumSteps) if self.debugNumSteps else 0,
               self.debugNumSteps,
               self.debugStepTime,
               self.debugNetworkTime,
               self.debugChatTime,
               self.network.debugSendPacketLength,
               self.network.debugReceivePacketLength,
              ),

    def displayVitals(self):
        if self.player:
            print self.player.vitals(),

    def displayScores(self):
        text = ""
        players = [object for object in self.objects if object.type == objects.PERSON]
        for player in players:
            text += " %s, %2i, %4i; " % \
                    (player._name, player.score, player.ping)

        print text,


    def updateChat(self, frameTime):
        self.timeUntilNextChatUpdate -= frameTime
        if self.timeUntilNextChatUpdate <= 0.0:
            self.chat.update()
            self.timeUntilNextChatUpdate = self.timeBetweenChatUpdates

    def updateGUI(self, frameTime):
        self.displayDebug()
        #self.displayScores()
        #self.displayVitals()
        print '\r',
    
    def frameEnded(self, frameTime):
        t = timer()

        self.updateGUI(frameTime)
        
        Engine.frameEnded(self, frameTime)

        t.start()
        self.updateChat(frameTime)
        t.stop()
        t.debugChatTime = t.time()
        
        self.timeUntilNextNetworkUpdate -= frameTime
        t.start()

        if self.timeUntilNextNetworkUpdate <= 0.0:
            self.timeUntilNextNetworkUpdate = self.timeBetweenNetworkUpdates

            u = timer()
            u.start()
            self.network.update(frameTime)
            u.stop()

            for message in self.network._messages:
                if message[1] > self.lastServerUpdate:
                    self.timeUntilNextEngineUpdate = message[Engine.NET_TIME_UNTIL_UPDATE]
                    self.lastServerUpdate = message[Engine.NET_TIME]

                    for object in self.objects:
                        object.existsOnServer = False

                    for serverObject in message[Engine.NET_OBJECTS]:
                        hasObject = False
                        for object in self.objects:
                            if serverObject[Engine.NET_OBJECTS_NAME] == object._name:
                                hasObject = True
                                object.existsOnServer = True
                                object.setAttributes(serverObject[Engine.NET_OBJECTS_ATTRIBUTES])
                                object.setEvents(serverObject[Engine.NET_OBJECTS_EVENTS])
                        if not hasObject:
                            newObject = None
                            if serverObject[2] == True:
                                newObject = Person(self, serverObject[Engine.NET_OBJECTS_NAME])
                                self.chat.setNickName(serverObject[Engine.NET_OBJECTS_NAME])
                                newObject.enable()
                                self.player = newObject
                            else:
                                if serverObject[Engine.NET_OBJECTS_TYPE] == objects.PERSON:
                                    newObject = Person(self, serverObject[Engine.NET_OBJECTS_NAME])
                                elif serverObject[Engine.NET_OBJECTS_TYPE] == objects.BULLET:
                                    newObject = BulletObject(self, serverObject[Engine.NET_OBJECTS_NAME])
                                elif serverObject[Engine.NET_OBJECTS_TYPE] == objects.GRENADE:
                                    newObject = GrenadeObject(self, serverObject[Engine.NET_OBJECTS_NAME])
                                elif serverObject[Engine.NET_OBJECTS_TYPE] == objects.SHRAPNEL:
                                    newObject = ShrapnelObject(self, serverObject[Engine.NET_OBJECTS_NAME])
                                elif serverObject[Engine.NET_OBJECTS_TYPE] == objects.LASER:
                                    newObject = LaserObject(self, serverObject[Engine.NET_OBJECTS_NAME])
                                else:
                                    print "Unknown object to create", serverObject[Engine.NET_OBJECTS_TYPE], objects.PERSON

                            if newObject:
                                newObject.existsOnServer = True        
                                newObject.setAttributes(serverObject[Engine.NET_OBJECTS_ATTRIBUTES])
                                newObject.setEvents(serverObject[Engine.NET_OBJECTS_EVENTS])
                                self.objects += [newObject]

                    for object in self.objects:
                        if not object.existsOnServer and object.type == objects.PERSON:
                            self.objects.remove(object)
                            object.close()
                            del object
                        
            self.network.clearMessages()
            
        if self.player != None:
            self.network.send(self.player.input())

        t.stop()
        self.debugNetworkTime = t.time()
        return True # Keep running
    
if __name__ == "__main__":
    try:
        import psyco
        psyco.full()
        print "Psyco Enabled"
    except ImportError:
        print "No Psyco Support"
        
    world = Bot()
    import cProfile
    cProfile.run('world.go()', 'client-profile.txt')
    os._exit(0)
