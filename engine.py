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
        self.limboObjects = []
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
                if object.isDead():
                    if object.type != "Person":
                        self.objects.remove(object)
                        del object

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
        if len([o for o in (self.objects + self.statics) if o._name == name]) == 0:
            print "DEBUG: No object of name", name
            return None
        else:
            return [o for o in (self.objects + self.statics) if o._name == name][0]


    def collision_callback(self, args, geom1, geom2):
        o1 = self.findObjectByName(geom1.objectName)
        o2 = self.findObjectByName(geom2.objectName)\

        if o1 == None or o2 == None:
            print type(geom1), type(geom2)
            return

        if (o1.type == "Bullet" and o2.type == "Bullet") or (o1 == o2):
            contacts = []
        else:
            contacts = ode.collide(geom1, geom2)

        for contact in contacts:
            contact.setMode(ode.ContactBounce + ode.ContactApprox1_1)
            contact.setBounce(0.01)
            contact.setBounceVel(0.0)
            contact.setMu(1.7)
        
            for a,b,geom in [[o1,o2,geom2],[o2,o1,geom1]]:
                if a.type == "Bullet":
                    a.setDead()
                    if b.type == "Person":
                        print "Hit",b._name, "on the", geom.location
                        if not b.isDead():
                            b.doDamage(a.damage)
                            if b.isDead():
                                b.setSpawnPosition(self.spawnLocation())
                                if a == b:
                                    self.messageListener(">",a.ownerName + " committed suicide")
                                    self.addScore(a.ownerName, -1)
                                else:
                                    self.messageListener(">",a.ownerName + " killed " + b.ownerName)
                                    self.addScore(a.ownerName, 1)
                    
            # Assume that if collision normal is facing up we are 'on ground'
            normal = contact.getContactGeomParams()[1]
            if normal[1] < 0.0: # normal.y points "up"
                o2.isOnGround = True
            if normal[1] > 0.0: # normal.y points "up"
                o1.isOnGround = True
                    
            joint = ode.ContactJoint(self.world, self.contactgroup, contact)
            joint.attach(geom1.getBody(), geom2.getBody())
