import ode
from objects import *
import gamenet
import time, random

class Engine():    
    def __init__(self):
        self.chat = gamenet.NetCode("cradle", "cradle.dyndns.org", "AssaultVector", "enter")
        self.chat.registerMessageListener(self.messageListener)
        self.stepSize = 1.0/85.0
        self.timeBetweenChatUpdates = 0.5
        self.timeUntilNextChatUpdate = 0.0
        self.timeUntilNextEngineUpdate = 0.0
        self._stats = {}
        random.seed(time.time())

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

        f = open('dm_arena.lvl', 'r')
        for line in f:
            line = line.strip()
            if not line.startswith('#') and len(line) != 0:
                size, loc, rot = [[float(y) for y in x.strip('()').split(',')] for x in line.split(":")]
                static = self.createStaticObject(size)
                static.setPosition(loc)
                static.setRotation(rot)
                self.statics += [static]

    def createStaticObject(self, size):
        return StaticObject(self, "s%s" % len(self.statics), size=size)
    
    def messageListener(self, source, message):
        print "%s: %s" % (source, message)

    def addBullet(self, name, position, direction, velocity, damage, owner):
        b = BulletObject(self, name, direction, velocity, damage)
        b.setPosition([p + x for p, x in zip(position, direction)])
        b.setOwnerName(owner._name)
        self.objects.append(b)
        
    def frameEnded(self, frameTime):
        self.timeUntilNextChatUpdate -= frameTime
        if self.timeUntilNextChatUpdate <= 0.0:
            self.chat.update()
            while self.timeUntilNextChatUpdate <= 0.0:
                self.timeUntilNextChatUpdate += self.timeBetweenChatUpdates

        self.timeUntilNextEngineUpdate -= frameTime  
        self.step(frameTime)        

        for object in self.objects:
            object.frameEnded(frameTime)
            
        for object in self.objects:
            if object.isDead():
                if type(object) != Person:
                    self.objects.remove(object)
                    del object
                else:
                    object.reset()
                    object.setPosition(self.spawnLocation())

    def spawnLocation(self):
        return random.choice([
            (0.0,20.0,0.0),
            (30.0,55.0,0.0),
            (-19.0,45.0,0.0),
            (-23.0,22.0,0.0),
            (0.0,20.0,0.0),
            (0.0,20.0,0.0)
            ])

    def step(self, frameTime):
        while self.timeUntilNextEngineUpdate <= 0.0:  
            self.space.collide(0, self.collision_callback)
            
            for object in self.objects:
                object.preStep()
                
            self.world.quickStep(self.stepSize)
            
            for object in self.objects:
                object.postStep()

            self.contactgroup.empty()
            self.timeUntilNextEngineUpdate += self.stepSize

    def addScore(self, name, amount):
        # TODO: Add to Player object
        if not self._stats.has_key(name):
            self._stats[name] = {}
        if not self._stats[name].has_key("score"):
            self._stats[name]["score"] = 0

        self._stats[name]["score"] += amount

    def findObjectByName(self, name):
        return [o for o in self.objects if o._name == name][0]

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
                if body1.objectType == "Bullet":
                    body1.isDead = True
                    if body2 and body2.objectType == "Person":
                        recepient = self.findObjectByName(body2.ownerName)
                        recepient.doDamage(body1.damage)
                        if recepient.isDead():
                            if body1.ownerName == body2.ownerName:
                                self.messageListener(">",body1.ownerName + " committed suicide")
                                self.addScore(body1.ownerName, -1)
                            else:
                                self.messageListener(">",body1.ownerName + " killed " + body2.ownerName)
                                self.addScore(body1.ownerName, 1)
                    
                # Assume that if collision normal is facing up we are 'on ground'
                normal = contact.getContactGeomParams()[1]
                if normal[1] > 0.05: # normal.y points "up"
                    geom1.isOnGround = True
                    
            if body2:
                if body2.objectType == "Bullet":
                    body2.isDead = True
                    if body1 and body1.objectType == "Person":
                        recepient = self.findObjectByName(body1.ownerName)
                        recepient.doDamage(body2.damage)
                        if recepient.isDead():
                            if body1.ownerName == body1.ownerName:
                                self.messageListener(">",body2.ownerName + " committed suicide")
                                self.addScore(body2.ownerName, -1)
                            else:
                                self.messageListener(">",body2.ownerName + " killed " + body1.ownerName)
                                self.addScore(body2.ownerName, 1)
                    
                # Assume that if collision normal is facing up we are 'on ground'
                normal = contact.getContactGeomParams()[1]
                if normal[1] < 0.05: # normal.y points "up"
                    geom2.isOnGround = True
                    
            joint = ode.ContactJoint(self.world, self.contactgroup, contact)
            joint.attach(body1, body2)
