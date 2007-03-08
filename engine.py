import ode
from objects import *
import gamenet
import time

class Engine():    
    def __init__(self):
        self.chat = gamenet.NetCode("cradle", "cradle.dyndns.org", "AssaultVector", "enter")
        self.chat.registerMessageListener(self.messageListener)
        self.stepSize = 1.0/85.0
        self.timeBetweenChatUpdates = 0.5
        self.timeUntilNextChatUpdate = 0.0
        self.timeUntilNextEngineUpdate = 0.0

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
        #self.world.setERP(0.2)
        #self.world.setCFM(0.001)
        #self.world.setContactMaxCorrectingVel(1000)
        self.space = ode.Space(type=1)
        self.contactgroup = ode.JointGroup()
        self.objects = []
        self.statics = []
            
    def messageListener(self, source, message):
        print "%s: %s" % (source, message)

    def addBullet(self, name, position, direction):
        b = BulletObject(self, name, direction)
        b.setPosition([p + x for p, x in zip(position, direction)])
        self.objects.append(b)
        
    def frameEnded(self, frameTime):
        self.timeUntilNextChatUpdate -= frameTime
        if self.timeUntilNextChatUpdate <= 0.0:
            self.chat.update()
            while self.timeUntilNextChatUpdate <= 0.0:
                self.timeUntilNextChatUpdate += self.timeBetweenChatUpdates

        self.timeUntilNextEngineUpdate -= frameTime
        while self.timeUntilNextEngineUpdate <= 0.0:    
            self.step()        
            self.timeUntilNextEngineUpdate += self.stepSize

        for object in self.objects:
            object.frameEnded(self.stepSize)
            
        for object in self.objects:
            if object.isDead():
                self.objects.remove(object)

    def step(self):
        self.space.collide(0, self.collision_callback)
        
        for object in self.objects:
            object.preStep()
            
        self.world.quickStep(self.stepSize)
        
        for object in self.objects:
            object.postStep()

        self.contactgroup.empty()

    def collision_callback(self, args, geom1, geom2):
        body1 = geom1.getBody()
        body2 = geom2.getBody()

        if body1 and body1.objectType == "Bullet" and body2 and body2.objectType == "Bullet":
            contacts = []
        else:
            contacts = ode.collide(geom1, geom2)

        for contact in contacts:
            contact.setMode(ode.ContactBounce + ode.ContactApprox1_1)
            contact.setBounce(0.01)
            contact.setBounceVel(0.0)
            contact.setMu(1.7)

            if body1:
                if body1.objectType == "Bullet" and not body2:
                    body1.isDead = True
                    
                # Assume that if collision normal is facing up we are 'on ground'
                normal = contact.getContactGeomParams()[1]
                if normal[1] > 0.05: # normal.y points "up"
                    geom1.isOnGround = True
                    
            if body2:
                if body2.objectType == "Bullet" and not body1:
                    body2.isDead = True
                    
                # Assume that if collision normal is facing up we are 'on ground'
                normal = contact.getContactGeomParams()[1]
                if normal[1] < 0.05: # normal.y points "up"
                    geom2.isOnGround = True
                    
            joint = ode.ContactJoint(self.world, self.contactgroup, contact)
            joint.attach(body1, body2)
