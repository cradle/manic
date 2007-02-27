import ode
from objects import *
import gamenet
import time

class Engine():    
    def __init__(self):
        self.chat = gamenet.NetCode("cradle", "cradle.dyndns.org", "AssaultVector", "enter")
        self.chat.registerMessageListener(self.messageListener)
        self.stepSize = 1.0/100.0
        self.timeBetweenChatUpdates = 0.5
        self.timeUntilNextNetworkUpdate = 0.0
        self.timeUntilNextEngineUpdate = 0.0
        self.players = []

    def go(self):
        self._createWorld()
        lastFrame = time.time()
        while True:
            timeSinceLastFrame = time.time() - lastFrame
            lastFrame += timeSinceLastFrame
            self.frameEnded(timeSinceLastFrame)

            #for object in self.objects:
            #    print object
    
    def _createWorld(self):
        self.world = ode.World()
        self.world.setGravity((0,-9.81,0))
        self.space = ode.Space(type=1)
        self.contactgroup = ode.JointGroup()
        self.objects = []
        self.statics = []
  
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
            
        self.player = Person(self, "p1")
        self.player.setPosition((-5.0,3.0,0.0))
        
        self.objects += [self.player]
            
        player2 = Person(self, "p2")
        player2.setPosition((5.0,3.0,0.0))
        
        self.objects += [player2]
            
    def messageListener(self, source, message):
        print "%s: %s" % (source, message)
        
    def frameEnded(self, frameTime):
        self.timeUntilNextChatUpdate -= frameTime
        if self.timeUntilNextChatUpdate <= 0.0:
            self.chat.update()
            while self.timeUntilNextChatUpdate <= 0.0:
                self.timeUntilNextChatUpdate += self.timeBetweenChatUpdates

        self.timeUntilNextEngineUpdate -= frameTime
        while self.timeUntilNextEngineUpdate <= 0.0:
            self.step()
            for object in self.objects:
                object.frameEnded(self.stepSize)
            for player in self.players:
                player.updateWorld(objects)
            self.timeUntilNextEngineUpdate += self.stepSize

    def step(self):
        if self.stepSize == 0.0:
            return 
    
        self.space.collide(0, self.collision_callback)
        
        for object in self.objects:
            object.preStep()
            
        self.world.quickStep(self.stepSize)
        
        for object in self.objects:
            object.postStep()
            
        self.contactgroup.empty()

    def collision_callback(self, args, geom1, geom2):
        if geom1.getBody() and geom1.getBody().objectType == "Bullet" \
           and geom2.getBody() and geom2.getBody().objectType == "Bullet":
            contacts = []
        else:
            contacts = ode.collide(geom1, geom2)

        for contact in contacts: #ode.ContactSoftERP + ode.ContactSoftCFM + 
            contact.setMode(ode.ContactBounce + ode.ContactApprox1_1)
            contact.setBounce(0.01)
            contact.setBounceVel(0.0)
            contact.setMu(1.7)

            body = geom1.getBody()
            if body:
                if body.objectType == "Bullet" and geom2.getBody() == None:
                    body.isDead = True
                    
                # Assume that if collision normal is facing up we are 'on ground'
                normal = contact.getContactGeomParams()[1]
                if normal[1] > 0.05: # normal.y points "up"
                    geom1.isOnGround = True
           
            joint = ode.ContactJoint(self.world, self.contactgroup, contact)
            joint.attach(body, geom2.getBody())
