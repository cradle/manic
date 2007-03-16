import ode
from objects import *
import time, random

class Engine:    
    def __init__(self):
        self.stepSize = 1.0/85.0
        self.timeUntilNextEngineUpdate = 0.0
        self._stats = {}
        random.seed(time.time())

    def go(self):
        self._createWorld()
        self._startTime = time.time()
        self._stepNumber = 0
        lastFrame = time.time()
        timeSinceLastFrame = 0.0
        while self.frameEnded(timeSinceLastFrame):
            timeSinceLastFrame = time.time() - lastFrame
            lastFrame += timeSinceLastFrame
    
    def _createWorld(self):
        self.world = ode.World()
        self.world.setGravity((0,-9.81,0))
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

    def createBulletObject(self, name, direction, velocity, damage):
        return BulletObject(self, name, direction, velocity, damage)

    def createPerson(self, name):
        return Person(self, name)
    
    def messageListener(self, source, message):
        print "%s: %s" % (source, message)

    def addBullet(self, name, position, direction, velocity, damage, owner):
        if len([True for object in self.objects if object._name == name]) == 0:
            b = self.createBulletObject(name, direction, velocity, damage)
            b.initialisePosition([p + x for p, x in zip(position, direction)])
            b.setOwnerName(owner._name)
            self.objects.append(b)
        
    def frameEnded(self, frameTime):
        self.timeUntilNextEngineUpdate -= frameTime  
        self.step(frameTime)        

        for object in self.objects:
            object.frameEnded(frameTime)

        return True # Keep going

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
            
            for object in self.objects:
                object.preCollide() 
                
            self.space.collide(0, self.collision_callback)
            
            for object in self.objects:
                object.preStep()
                
            self.world.quickStep(self.stepSize)
            if self._stepNumber != None:
                self._stepNumber += 1
                #print "Steps per second =", self._stepNumber / (time.time() - self._startTime), 1.0/self.stepSize
            
            for object in self.objects:
                object.postStep()
                if object.isDead():
                    if object.type != "Person":
                        self.objects.remove(object)
                        object.close()
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

    def collision_callback(self, args, geom1, geom2):
        o1 = geom1.object
        o2 = geom2.object

        if o1 == None or o2 == None:
            print "BUG! Probably not deleting some object properly"
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
