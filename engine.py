import ode
from objects import *
import time
import encode

class Engine:
    NET_OBJECTS = 0
    NET_OBJECTS_NAME = 0
    NET_OBJECTS_ATTRIBUTES = 1
    NET_OBJECTS_IS_CURRENT_PLAYER = 2
    NET_OBJECTS_TYPE = 3
    NET_OBJECTS_EVENTS = 4
    NET_TIME = 1
    NET_TIME_UNTIL_UPDATE = 2
    
    def __init__(self):
        self.stepSize = 1.0/150.0
        self.timeUntilNextEngineUpdate = 0.0
        random.seed(time.time())
        self.debugStepTime = 1.0
        self.debugFrameTime = 1.0
        self.debugNumSteps = 0

    def go(self):
        self._createWorld()
        self._startTime = time.time()
        lastFrame = time.time()
        timeSinceLastFrame = 0.0
        while self.frameEnded(timeSinceLastFrame):
            timeSinceLastFrame = time.time() - lastFrame
            lastFrame += timeSinceLastFrame
    
    def _createWorld(self):
        self.world = ode.World()
        #self.world.setQuickStepNumIterations(10)
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

    def createGrenadeObject(self, name, direction, velocity, damage):
        return GrenadeObject(self, name, direction, velocity, damage)

    def createPerson(self, name):
        return Person(self, name)
    
    def messageListener(self, source, message):
        print "%s: %s" % (source, message)

    def addBullet(self, t, name, position, direction, velocity, damage, owner):
        if len([True for object in self.objects if object._name == name]) == 0:
            b = None
            if t == BULLET:
                b = self.createBulletObject(name, direction, velocity, damage)
            if t == GRENADE:
                b = self.createGrenadeObject(name, direction, velocity, damage)
            b.setPosition(position)
            b.setOwnerName(owner)
            self.objects += [b]
        
    def frameEnded(self, frameTime):
        timer = encode.timer()
        timer.start()
        self.timeUntilNextEngineUpdate -= frameTime
        self.step()     
        self.debugFrameTime = self.timeUntilNextEngineUpdate

        for object in self.objects:
            object.frameEnded(frameTime)
        timer.stop()
        self.debugStepTime = timer.time()

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

    def step(self):
        self.debugNumSteps = 0
        while self.timeUntilNextEngineUpdate <= 0.0:
            self.debugNumSteps += 1
            for o in self.objects:
                o.preCollide()
            self.space.collide(0, self.collision_callback)            
            for o in self.objects:
                o.preStep()
            self.world.quickStep(self.stepSize)
            
            for o in self.objects[:]:
                o.postStep()

            self.contactgroup.empty()
            self.timeUntilNextEngineUpdate += self.stepSize

    def addScore(self, name, amount):
        # TODO: Add to Player object
        for object in self.objects:
            if object._name == name:
                object.score += amount

    def collision_callback(self, args, geom1, geom2):
        o1 = geom1.object
        o2 = geom2.object

        if o1 == None or o2 == None:
            print "BUG! Probably not deleting some object properly", type(o1), type(o2)
            return

        if o1 == o2:
            contacts = []
        else:
            contacts = ode.collide(geom1, geom2)

        for contact in contacts[0:1]:
            contact.setMode(ode.ContactBounce + ode.ContactApprox1_1)
            contact.setBounce(0.01)
            contact.setBounceVel(0.0)
            contact.setMu(1.7)
        
            for a,b,geom in [[o1,o2,geom2],[o2,o1,geom1]]:  
                a.hitObject(b, contact.getContactGeomParams()[0])
                if a.type == GRENADE or a.type == BULLET:
                    contact.setBounce(1.0)
                    contact.setMu(0.0)
                    if a.isDead() and b.type == PERSON:
                        print "Hit",b._name, "on the", geom.location
                        if not b.isDead():
                            b.doDamage(a.damage)
                            if b.isDead():
                                b.setSpawnPosition(self.spawnLocation())
                                if a.ownerName == b._name:
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
