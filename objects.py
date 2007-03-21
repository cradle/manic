import ode, random, math, time
import engine

#TYPES
STATIC = 0
DYNAMIC = 1
SPHERE = 2
PERSON = 3
BULLET = 4
GRENADE = 5
SHRAPNEL = 6

#Keys
LEFT = 1
RIGHT = 2
ROTATE_LEFT = 4
ROTATE_RIGHT = 8
UP = 16
DOWN = 32
SHOOT = 64
RELOAD = 128
DOWNDOWN = 256
WEAPON1 = 512
WEAPON2 = 1024
WEAPON3 = 2048
WEAPON4 = 8192
WEAPON5 = 16384
WEAPON6 = 32768
WEAPON7 = 65536
WEAPON8 = 131072
WEAPON9 = 262144

class Generator(object):
    _objectNum = 0

    def nextID():
        Generator._objectNum += 1
        return Generator._objectNum

    nextID = staticmethod(nextID)

class StaticObject(object):

    #COLLISION TYPES
    TERRAIN = 1
    PROJECTILE = 2
    PLAYER = 4
    
    def __init__(self, gameworld, name, size = (1.0, 1.0, 1.0), geomFunc = ode.GeomBox):
        self._size = size
        self._geometry = geomFunc(gameworld.space, self._size)
        self._geometry.location = "Torso"
        self._geometry.objectName = name
        self._geometry.object = self
        self._name = name
        self._nick = name
        self._world = gameworld.world
        self._space = gameworld.space
        self._gameworld = gameworld
        self.type = STATIC
        self._geometry.setCategoryBits(self.TERRAIN)
        self._geometry.setCollideBits(self.PROJECTILE | self.PLAYER)
        self._gameID = Generator.nextID()
        
    def shouldSendToClients(self):
        return True

    def getBody(self):
        return None

    def close(self):
        self._geometry.object = None

    def hitObject(self, other, position):
        pass

    def __del__(self):
        self._geometry.disable()
        self._world = None
        self._space = None
        self._gameworld = None

    def __str__(self):
        return "P=(%2.2f, %2.2f, %2.2f)" % self._geometry.getPosition()

    def setPosition(self, position):
        if position:
            self._geometry.setPosition(position)

    def setRotation(self, quaternion):
        self._geometry.setQuaternion(quaternion)

class DynamicObject(StaticObject):
    
    def __init__(self, gameworld, name, size = (1.0,1.0,1.0), geomFunc = ode.GeomBox, weight = 50):
        StaticObject.__init__(self, gameworld, name, size, geomFunc)
        
        self.maxMoveForce = 2000
        self.maxMoveVelocity = 10
        self.maxSpinForce = 700
        self.maxSpinVelocity = 15
        
        self._body = ode.Body(gameworld.world)
        mass = ode.Mass()
        
        if hasattr(size, "__getitem__"):
            mass.setBoxTotal(weight, size[0], size[1], size[2])
        else:
            mass.setBoxTotal(weight, size, size, size)
            
        self._body.setMass(mass)
        self._geometry.setBody(self._body)
        
        self._motor = ode.Plane2DJoint(gameworld.world)
        self._motor.attach(self._body, ode.environment)

        self.isOnGround = False
        self.isJumping = False
        self.type = DYNAMIC
        self._body.name = name

        self.presses = None
        self._pointingDirection = (1.0,0.0,0.0)
        self.setDead(False)

    def getBody(self):
        return self._body

    def setDead(self, dead = True):
        self.dead = dead

    def isDead(self):
        return self.dead

    def __del__(self):
        self._body.disable()
        StaticObject.__del__(self)
    
    def disable(self):
        self._body.disable()
        self._geometry.disable()
        self.enabled = False

    def enable(self):
        self._body.enable()
        self._geometry.enable()
        self.enabled = True

    def getEvents(self):
        return []

    def clearEvents(self):
        pass

    def setEvents(self, position):
        pass

    def getDirection(self):
        return self._pointingDirection

    def setDirection(self, direction):
        self._pointingDirection = direction

    def setPosition(self, position):
        StaticObject.setPosition(self, position)
        if position:
            self._body.setPosition(position)

    def to2d(self, vector):
        return ([0 if x == 0.0 else x for x in vector[0:-1]])

    def to3d(self, vector):
        return vector + [0]

    def getAttributes(self):
        return [self.to2d(self._body.getPosition()),
         self.to2d(self._body.getQuaternion()),
         self.to2d(self._body.getAngularVel()),
         self.to2d(self._body.getLinearVel()),
         self.to2d(self.getDirection())]

    def setAttributes(self, attributes):
        self.setPosition(self.to3d(attributes[0]))
        self.setQuaternion(self.to3d(attributes[1]))
        self.setAngularVel(self.to3d(attributes[2]))
        self.setLinearVel(self.to3d(attributes[3]))
        self.setDirection(self.to3d(attributes[4]))

    def setQuaternion(self, quaternion):
        self._body.setQuaternion(quaternion)

    def setAngularVel(self, vel):
        self._body.setAngularVel(vel)

    def setLinearVel(self, vel):
        self._body.setLinearVel(vel)

    def preCollide(self):
        self.isOnGround = False

    def _secondaryFire(self):
        pass

    def preStep(self):
        if self.presses:
            keys = self.presses[1]
            if keys & LEFT:
                self._moveLeft()
            if keys & RIGHT:
                self._moveRight()
            if keys & ROTATE_LEFT:
                self._rotateLeft()
            if keys & ROTATE_RIGHT:
                self._rotateRight()
            if keys & DOWN:
                self._crouch()
            else:
                self._unCrouch()
            if keys & UP:
                self._jump()
            else:
                self._unJump()
            if keys & SHOOT:
                self._shoot()
            else:
                self._unShoot()
            #if 's2' in self.presses:
            #    self._secondaryFire()
            if keys & RELOAD:
                self._reload()

        # Apply wind friction
        self._body.addForce([-0.05*abs(x)*x for x in self._body.getLinearVel()])

        #if self.isOnGround:
        #    # Apply rolling friction
        #    self._body.addTorque([x*-0.5 for x in self._body.getAngularVel()])
        
    def postStep(self):
        #self._alignToZAxis()
        self._motor.setXParam(ode.ParamFMax, 0)
        self._motor.setYParam(ode.ParamFMax, 0)
        self._motor.setAngleParam(ode.ParamFMax, 0)

    def frameEnded(self, frameTime):
        pass

    def _alignToZAxis(self):
        self._alignBodyToZAxis(self._body)

    def _alignBodyToZAxis(self, body):
        pass# If we get alignment issues, uncomment this!
        #rot = body.getAngularVel()
        #old_quat = body.getQuaternion()
        #quat_len = math.sqrt( old_quat[0] * old_quat[0] + old_quat[3] * old_quat[3] )
        #body.setQuaternion((old_quat[0] / quat_len, 0, 0, old_quat[3] / quat_len))
        #body.setAngularVel((0,0,rot[2]))
        # http://opende.sourceforge.net/wiki/index.php/HOWTO_constrain_objects_to_2d

    def _shoot(self):
        pass
    def _unShoot(self):
        pass

    def _reload(self):
        pass
    
    def _moveLeft(self):
        if self._body.getLinearVel()[0] > -self.maxMoveVelocity:
            self._motor.setXParam(ode.ParamVel, -self.maxMoveVelocity)
            self._motor.setXParam(ode.ParamFMax, self.maxMoveForce)
        
    def _moveRight(self):
        if self._body.getLinearVel()[0] < self.maxMoveVelocity:
            self._motor.setXParam(ode.ParamVel,  self.maxMoveVelocity)
            self._motor.setXParam(ode.ParamFMax, self.maxMoveForce)

    def _rotateLeft(self):
        if self.isCrouching:
            self._motor.setAngleParam(ode.ParamVel,  self.maxSpinVelocity/2)
            self._motor.setAngleParam(ode.ParamFMax, self.maxSpinForce)
        else:
            self._motor.setAngleParam(ode.ParamVel,  self.maxSpinVelocity)
            self._motor.setAngleParam(ode.ParamFMax, self.maxSpinForce)

    def _rotateRight(self):
        if self.isCrouching:
            self._motor.setAngleParam(ode.ParamVel,  -self.maxSpinVelocity/2)
            self._motor.setAngleParam(ode.ParamFMax, self.maxSpinForce)
        else:
            self._motor.setAngleParam(ode.ParamVel,  -self.maxSpinVelocity)
            self._motor.setAngleParam(ode.ParamFMax, self.maxSpinForce)
        
    def _jump(self):
        if self.isOnGround:
            self.isJumping = True
            self._motor.setYParam(ode.ParamVel,  self.maxMoveVelocity)
            self._motor.setYParam(ode.ParamFMax, self.maxMoveForce)
            
    def _unJump(self):
        pass

    def _crouch(self):
        pass
    
    def _unCrouch(self):
        pass

    def _prone(self):
        pass

    def __str__(self):
        return StaticObject.__str__(self) + ", LV=(%2.2f, %2.2f, %2.2f), AV=(%2.2f, %2.2f, %2.2f)" % \
               (self._body.getLinearVel() + self._body.getAngularVel())

    def inputPresses(self, presses):
        self.setDirection(presses[0])
        self.presses = presses

class SphereObject(DynamicObject):
    def __init__(self, gameworld, name, size = 0.5, geomFunc = ode.GeomSphere, weight = 10):
        DynamicObject.__init__(self, gameworld, name, size, geomFunc, weight)

        if type(size) == float or type(size) == int:
            self._body.getMass().setSphereTotal(weight, size)
            
        self.type = SPHERE

class BulletObject(SphereObject):
    def __init__(self, gameworld, name, direction = None, velocity = [0.0,0.0], damage = 1.0, weight = 3.0):
        
        self.size = 0.025
        self.maxSpeed = velocity
        self.weight = weight
        self.damage = damage
        self._gameworld = gameworld
        
        SphereObject.__init__(self, gameworld, name, self.size, geomFunc = ode.GeomSphere, weight = self.weight)

        
        if type(self.size) == float or type(self.size) == int:
            self._body.getMass().setSphereTotal(self.weight, self.size)

        speedVariation = (1-(random.random()-0.5)/5)

        if direction:
            self._body.setLinearVel((direction[0] * speedVariation * self.maxSpeed[0],
                                     direction[1] * speedVariation * self.maxSpeed[1],
                                     0))
##            self._motor.setXParam(ode.ParamVel,  direction[0] * speedVariation * self.maxSpeed[0])
##            self._motor.setXParam(ode.ParamFMax, ode.Infinity)
##            self._motor.setYParam(ode.ParamVel,  direction[1] * speedVariation * self.maxSpeed[1])
##            self._motor.setYParam(ode.ParamFMax, ode.Infinity)
            
        self.setDead(False)
        self.type = BULLET
        self.hasSentToClients = False
        self.events = []
        
        self._geometry.setCategoryBits(self.PROJECTILE)
        self._geometry.setCollideBits(self.TERRAIN | self.PLAYER)

        self.hasStepped = False
        self.needToTellClient = True

    def __del__(self):
        SphereObject.__del__(self)

    def hitObject(self, other, position):
        self.setDead()

    def setOwnerName(self, name):
        self.ownerName = name

    def postStep(self):
        pass;
##        if not self.hasStepped:
##            # Optimisation, bullet objects should be very light weight
##            self.hasStepped = True
##            
##            SphereObject.postStep(self)
##            self._motor.setXParam(ode.ParamFMax, 0)
##            self._motor.setYParam(ode.ParamFMax, 0)

    def getAttributes(self):
        return [self.to2d(self._body.getPosition()),
                self.to2d(self._body.getLinearVel())]

    def setAttributes(self, attributes):
        self._body.setPosition(self.to3d(attributes[0]))
        self._body.setLinearVel(self.to3d(attributes[1]))

    def shouldSendToClients(self):
        return not self.hasSentToClients and self.needToTellClient

    def clearEvents(self):
        self.hasSentToClients = True  

class ShrapnelObject(BulletObject):
    def __init__(self, gameworld, name, direction = None, velocity = [0.0,0.0], damage = 2.0):
        BulletObject.__init__(self, gameworld, name, direction, velocity, damage, 1.0)
        self.ricochetTime = 0.15

    def hitObject(self, other, position):
        if other.type != STATIC or self.ricochetTime <= 0:
            BulletObject.hitObject(self, other, position)

    def frameEnded(self, time):
        self.ricochetTime -= time

class GrenadeObject(BulletObject):
    def __init__(self, gameworld, name, direction = None, velocity = [0.0,0.0], damage = 2.0):
        self.ownerName = ""
        BulletObject.__init__(self, gameworld, name, direction, velocity, damage)
        self.timeUntilArmed = 0.25
        self.timeUntilExploded = self.timeUntilArmed + 2.5
        self.lastFrameTime = 0.1
        self.type = GRENADE
        self.explodePos = None
        self.exploded = False
        self.seed = random.randint(0,10000)

    def hitObject(self, other, position):
        if self.timeUntilArmed <= 0:
            self.explodePos = position
            BulletObject.hitObject(self, other, position)
        else:
            self.events += ["ricochet"]
            print "Hit", other._name

    def getAttributes(self):
        return BulletObject.getAttributes(self) + [
            self.timeUntilArmed,
            self.timeUntilExploded,
            self.seed]

    def setAttributes(self, attributes):
        BulletObject.setAttributes(self, attributes)
        self.timeUntilArmed = attributes[2]
        self.timeUntilExploded = attributes[3]
        self.seed = attributes[4]
    
    def setDead(self, dead = True):
        BulletObject.setDead(self, dead)
        # TODO: Move to explode
        if dead == True and not self.exploded:
            self.events += ["explode"]

    def postStep(self):
        BulletObject.postStep(self)
        if self.isDead() and not self.exploded:
            self.explode()

    def explode(self):
        random.seed(self.seed)
        if not self.explodePos:
            self.explodePos = self._body.getPosition()
        for i in range(50):
            direction = [random.random()-0.5, random.random()-0.5, 0]
            length = math.sqrt(direction[0]*direction[0] + direction[1]*direction[1])
            direction[0] /= length
            direction[1] /= length
            velocity = random.randint(7,17)
            b = self._gameworld.addBullet(SHRAPNEL,
                  self._name + "s" + str(i), \
                  map((lambda a,b: a+b/5), self.explodePos, direction),
                  direction,
                  [velocity, velocity],
                  5, #Damage
                  self._geometry.object._name)
            b.needToTellClient = False
            b.ownerName = self.ownerName
            
        self.exploded = True

    def frameEnded(self, time):
        self.timeUntilArmed -= time
        self.timeUntilExploded -= time

        if self.timeUntilExploded <= 0:
            self.setDead()
        
        BulletObject.frameEnded(self, time)
        self.lastFrameTime = time

        
class Person(SphereObject):
    def __init__(self, gameworld, name, camera = None):
        self._gameworld = gameworld

        # The size of the movement ball
        self.feetSize = 0.5 # Sphere
        torsoSize = (1.0, 0.5, 1.0) # Box
        headSize = (1.0 ,0.4 ,1.0 )# Box
        weight = 70
        self.weight = weight
        self._name = name   
        self._gameID = Generator.nextID()
     
        self._size = self.feetSize
        
        self._geometry = ode.GeomSphere(gameworld.space, self.feetSize)
        self._body = ode.Body(gameworld.world)
        mass = ode.Mass()
        mass.setSphereTotal(weight,self.feetSize)
        self._body.setMass(mass)
        self._geometry.setBody(self._body)
        self._geometry.objectName = name
        self._geometry.object = self
        
        self._motor = ode.Plane2DJoint(gameworld.world)
        self._motor.attach(self._body, ode.environment)

        self._geometry.location = "Legs"

        # Torso
        self._torsoGeometry = ode.GeomBox(lengths=torsoSize)
        self._torsoGeometry.objectName = self._name
        ## Moving up only feetSize (not *2) so that it overlaps the feet
        self._torsoGeometry.setPosition((0,0.8,0))

        self._torsoTransform = ode.GeomTransform(gameworld.space)
        self._torsoTransform.setGeom(self._torsoGeometry)
        self._torsoTransform.location = "Torso"
        self._torsoTransform.objectName = self._name
        self._torsoTransform.object = self

        # Head
        self._headGeometry = ode.GeomBox(lengths=headSize)
        self._headGeometry.objectName = self._name
        self._headGeometry.setPosition((0,1.0,0))

        self._headTransform = ode.GeomTransform(gameworld.space)
        self._headTransform.setGeom(self._headGeometry)
        self._headTransform.location = "Head"
        self._headTransform.objectName = self._name
        self._headTransform.object = self

        self.torsoBody = ode.Body(gameworld.world)
        self.torsoBody.setGravityMode(False)
        self.torsoBody.setAngularVel((0,0,0))
        self.torsoBody.setLinearVel((0,0,0))
        mass = ode.Mass()
        mass.setSphereTotal(weight,self.feetSize)
        #self.torsoBody.setMass(mass)

        self.hinge = ode.HingeJoint(gameworld.world)
        self.hinge.attach(self._body, self.torsoBody)
        self.hinge.setAxis((0,0,1))
        
        self._torsoTransform.setBody(self.torsoBody)
        self._headTransform.setBody(self.torsoBody)
        
        self.type = PERSON
        self.ownerName = name
        self._bulletNum = 0
        self.timeNeededToPrepareJump = 0.125
        self.maxStopForce = 70000/self.feetSize
        self.maxSpinForce = 70000/self.feetSize
        self.maxSpinVelocity = 10/self.feetSize
        self.maxMoveForce = 800
        self.maxMoveVelocity = 3.5
        self.maxJumpForce = ode.Infinity
        self.maxJumpVelocity = 11
        self._world = gameworld
        self.maxHealth = 100
        self.spawnPosition = None
        self.respawnTime = 3.0
        self.setDead(False)
        self.timeUntilRespawn = 0.0
        self.events = []
        self.ping = 0.0

        self.gunIDs = {
             "Pistol":  1,
             "SMPistol":2,
             "SMG":     3,
             "Shotgun": 4,
             "Assault": 5,
             "Support": 6,
             "Sniper":  7,
             "GrenadeLauncher": 8,
            }

        self.gunNames = {}
        for name, id in self.gunIDs.items():
            self.gunNames[id] = name

        self.gunName = None
        self._instability = 0.0
        self.score = 0
        
        self._geometry.setCategoryBits(self.PLAYER)
        self._geometry.setCollideBits(self.PROJECTILE | self.TERRAIN)
        self._torsoTransform.setCategoryBits(self.PLAYER)
        self._torsoTransform.setCollideBits(self.PROJECTILE | self.TERRAIN)
        self._headTransform.setCategoryBits(self.PLAYER)
        self._headTransform.setCollideBits(self.PROJECTILE | self.TERRAIN)

        self.reset()
        
        self.setGun("Assault")

    def close(self):
        self._geometry.object = None
        self._torsoTransform.object = None
        self._headTransform.object = None

    def setPosition(self, position):
        SphereObject.setPosition(self, position)
        if position:
            self.torsoBody.setPosition(position)

    def __del__(self):
        self._torsoGeometry.disable()
        self._torsoTransform.disable()
        self._headGeometry.disable()
        self._headTransform.disable()
        SphereObject.__del__(self)
        del self._torsoGeometry
        del self._torsoTransform
        del self._headGeometry
        del self._headTransform
        
    def reset(self):
        self.timeLeftUntilMustShoot = None
        self.isCrouching = False
        self.canShoot = True
        self.isJumping = False
        self.isOnGround = False
        self.timeLeftUntilCanJump = self.timeNeededToPrepareJump
        self.wantsToJump = False
        self._pointingDirection = (1.0,0.0,0.0)
        self._body.setLinearVel((0,0,0))
        self._body.setAngularVel((0,0,0))
        self.torsoBody.setAngularVel((0,0,0))
        self.torsoBody.setLinearVel((0,0,0))
        self.presses = None
        self.health = self.maxHealth
        self.events = []
        self.soundEvents = []

        self.guns = {
            'Pistol':{
                'ammo':7,
                'reloadTime':0.8,
                'accuracy':0.98,
                'timeBetweenShots':0.0,
                'damage':15,
                'velocity':35.0,
                'type':'single',
                'ammoType':BULLET,
                'zoom':35,
                'recoil':0.1,
                'auto':False,
                },
            'SMPistol':{
                'ammo':30,
                'reloadTime':1.4,
                'accuracy':0.75,
                'timeBetweenShots':0.02,
                'damage':5,
                'velocity':25.0,
                'type':'single',
                'ammoType':BULLET,
                'zoom':30,
                'recoil':0.025,
                'auto':True,
                },
            'SMG':{
                'ammo':50,
                'reloadTime':2.5,
                'accuracy':0.85,
                'timeBetweenShots':0.07,
                'damage':5,
                'velocity':40.0,
                'type':'single',
                'ammoType':BULLET,
                'zoom':40,
                'recoil':0.025,
                'auto':True,
                },
            'Shotgun':{
                'ammo':5,
                'reloadTime':5.0,
                'accuracy':0.8,
                'timeBetweenShots':0.6,
                'damage':7,
                'velocity':25.0,
                'type':'scatter',
                'ammoType':BULLET,
                'bulletsPerShot':11,
                'zoom':35,
                'recoil':0.0,
                'auto':False,
                },
            'Assault':{
                'ammo':30,
                'reloadTime':2.2,
                'accuracy':0.88,
                'timeBetweenShots':0.1,
                'damage':11.0,
                'velocity':65.0,
                'type':'burst',
                'ammoType':BULLET,
                'bulletsPerBurst':3,
                'shotsLeftInBurst':3,
                'timeBetweenBurstShots':0.03,
                'timeBetweenBursts':0.5,
                'type2':'single',
                'zoom':45,
                'recoil':0.02,
                'auto':False,
                },
            'Support':{
                'ammo':100,
                'reloadTime':5.0,
                'accuracy':0.85,
                'timeBetweenShots':0.18,
                'damage':10,
                'velocity':50.0,
                'type':'single',
                'ammoType':BULLET,
                'bulletsPerShot':3,
                'zoom':60,
                'recoil':0.075,
                'auto':True,
                },
            'Sniper':{
                'ammo':5,
                'reloadTime':15.0,
                'accuracy':0.98,
                'timeBetweenShots':7.5,
                'damage':100,
                'velocity':120.0,
                'type':'single',
                'ammoType':BULLET,
                'zoom':80,
                'recoil':3.0,
                'auto':False,
                },
            'GrenadeLauncher':{
                'ammo':1,
                'reloadTime':3.0,
                'accuracy':1.0,
                'timeBetweenShots':5.0,
                'damage':1,
                'velocity':25.0,
                'type':'single',
                'ammoType':GRENADE,
                'zoom':50,
                'recoil':0.0,
                'auto':False,
                }
            }

        for gun in self.guns.values():
            gun['maxAmmo'] = gun['ammo']
            gun['timeLeftUntilNextShot'] = 0.0
            gun['maxAccuracy'] = gun['accuracy']
            gun['reloading'] = False
            if gun['type'] == 'burst':
                gun['shotsLeftInBurst'] = gun['bulletsPerBurst']

    def hitObject(self, other, position):
        if other.type == BULLET:
            self.events += ['hit']
        
    def doDamage(self, damage):        
        if not self.isDead():
            self.health -= damage
            if self.health <= 0:
                self.health = 0
                self.setDead()
                self.timeUntilRespawn = self.respawnTime
            
    def preStep(self):
        if not self.isDead():
            if self.presses:
                keys = self.presses[1]
                SphereObject.preStep(self)
                if keys & WEAPON1:
                    self.setGun("Pistol")
                if keys & WEAPON2:
                    self.setGun("SMPistol")
                if keys & WEAPON3:
                    self.setGun("SMG")
                if keys & WEAPON4:
                    self.setGun("Shotgun")
                if keys & WEAPON5:
                    self.setGun("Assault")
                if keys & WEAPON6:
                    self.setGun("GrenadeLauncher")
                if keys & WEAPON7:
                    self.setGun("Support")
                if keys & WEAPON8:
                    self.setGun("Sniper")
##                if keys & WEAPON9:
##                    self.setGun(self.primaryGunName)
##                if 'md' in self.presses:
##                    self.setGun(self.secondaryGunName)
                
            if self.timeLeftUntilMustShoot and self.timeLeftUntilMustShoot < 0:
                self._shoot()
        else:
            if self.timeUntilRespawn <= 0:
                self.setDead(False)
                self.enable()
                self.reset()
                self.setPosition(self.spawnPosition)

    def setGun(self, name):
        if not self.timeLeftUntilMustShoot:
            self.gun = self.guns[name]
            self.gunName = name

    def getAttributes(self):
        # Massive corners cut here for the sake of network traffic
        return SphereObject.getAttributes(self) + \
               [int(self.health),
                int(self.gunIDs[self.gunName]),
                int(self.gun['ammo']),
                self.gun['timeLeftUntilNextShot'] if self.gun['timeLeftUntilNextShot'] > 0 else 0,
                self.timeUntilRespawn if self.timeUntilRespawn > 0 else 0,
                ((1 if self.gun['reloading'] else 0) |
                (2 if self.isCrouching else 0) |
                (4 if self.isJumping else 0) |
                (8 if self.isDead() else 0) |
                (16 if self.canShoot else 0)),
                self.score,
                self.ping,
                self._instability
                ]

    def setAttributes(self, attributes):
        SphereObject.setAttributes(self,attributes)
        self.health = attributes[5]
        self.setGun(self.gunNames[attributes[6]])
        self.gun['ammo'] = attributes[7]
        self.gun['timeLeftUntilNextShot'] = attributes[8]
        self.timeUntilRespawn = attributes[9]
        state = attributes[10]
        self.gun['reloading'] = (state & 1 == 1)
        self.isCrouching = (state & 2 == 2)
        self.isJumping = (state & 4 == 4)
        self.setDead((state & 8 == 8))
        self.canShoot = (state & 16 == 16)
        self.score = attributes[11]
        self.ping = attributes[12]
        self._instability = attributes[13]

    def _calculateAccuracy(self):
        self.gun['accuracy'] -= self._instability
        self._instability /= 1.1

        recoveryWeight = 2.5
        if self.isCrouching and self.isOnGround:
            self.gun['accuracy']  = (self.gun['accuracy']*recoveryWeight + ((self.gun['maxAccuracy']+1.0)/2.0) )/(recoveryWeight+1)
        elif self.isOnGround:
            self.gun['accuracy']  = (self.gun['accuracy']*recoveryWeight + self.gun['maxAccuracy'])/(recoveryWeight+1)
        else:
            self.gun['accuracy']  = (self.gun['accuracy']*recoveryWeight + self.gun['maxAccuracy'] * 0.75)/(recoveryWeight + 1)
            

    def getAccuracy(self):
        if self.gun['type'] == "scatter":
            return self.gun['maxAccuracy']
        else:
            return self.gun['accuracy']

    def setAccuracy(self, accuracy):
        self.gun['accuracy'] = accuracy

    def getEvents(self):
        return self.events

    def clearEvents(self):
        self.events = []

    def setSpawnPosition(self, position):
        self.spawnPosition = position

    def vitals(self):
        text = " Health: %i/%i\n Weapon: %s" % \
               (self.health,
                self.maxHealth,
                self.gunName)

        if self.gun['reloading']:
            text += "\n Reloading: %3i%%" % (100 - self.gun['timeLeftUntilNextShot'] * 100 / self.gun['reloadTime'])
        else:
            text += "\n Ammo: %i/%i" % (self.gun['ammo'], self.gun['maxAmmo'])
            if self.gun['timeLeftUntilNextShot'] > 0:
                text += " (%3i%%)" % (100 - self.gun['timeLeftUntilNextShot'] * 100 / self.gun['timeBetweenShots'])
            if float(self.gun['ammo'])/self.gun['maxAmmo'] <= 0.2:
                text += "\n Press R to reload"

        return text

    def frameEnded(self, time):
        self.timeUntilRespawn -= time

        if self.timeLeftUntilMustShoot:
            self.timeLeftUntilMustShoot -= time
        
        # TODO: I hate flags!!! 
        if self.wantsToJump:
            self.timeLeftUntilCanJump -= time
        else:
            self.timeLeftUntilCanJump = self.timeNeededToPrepareJump

        if self.gun['timeLeftUntilNextShot'] > 0:
            self.gun['timeLeftUntilNextShot'] -= time
        elif self.gun['timeLeftUntilNextShot'] > -time:
            self.gun['timeLeftUntilNextShot'] = -time

        if self.gun['timeLeftUntilNextShot'] <= 0.0 and self.gun['reloading']:
            self.gun['reloading'] = False

    def _calculateScatter(self):
        a = None
        a = self.getAccuracy()
        return random.random()*(1-a)-0.5*(1-a)

    def _reload(self):
        if not self.gun['reloading'] and self.gun['ammo'] != self.gun['maxAmmo']:
            self.gun['ammo'] = self.gun['maxAmmo']
            self.gun['reloading'] = True
            self.gun['timeLeftUntilNextShot'] = self.gun['reloadTime']
            self.timeLeftUntilMustShoot = None
            if self.gun['type'] == "burst":
                self.gun['shotsLeftInBurst'] = self.gun['bulletsPerBurst']
            
    def _crouch(self):
        self.isCrouching = True
        
    def _unCrouch(self):
        self.isCrouching = False

    def getShootOffset(self):
        return [0,0.5,0]

    def _unShoot(self):
        self.canShoot = True

    def _shoot(self):
        while (self.timeLeftUntilMustShoot and self.timeLeftUntilMustShoot <= 0 and self.gun['ammo'] > 0) or\
           self.gun['timeLeftUntilNextShot'] < 0.0 and self.gun['ammo'] > 0 and self.canShoot:
            if not self.gun['auto']:
                self.canShoot = False
            numShots = 1
            if self.gun['type'] == "scatter":
                numShots = self.gun['bulletsPerShot']

            for i in range(numShots):
                direction = [self.getDirection()[0]+self._calculateScatter(),
                             self.getDirection()[1]+self._calculateScatter(),
                             0]
                length = math.sqrt(direction[0]*direction[0] + direction[1]*direction[1])
                direction[0] /= length
                direction[1] /= length
                position = [a+b for a,b in zip(self._body.getPosition(), self.getShootOffset())]
                position = [p + x for p, x in zip(position, direction)]
                position[2] = 0
                self._bulletNum += 1
                self._world.addBullet(self.gun['ammoType'],
                                      self._name + "b" + str(self._bulletNum), \
                                      position,
                                      direction,
                                      ## TODO: Add player velocity
                                      #[self._body.getLinearVel()[0] + (self._body.getLinearVel()[0]/(abs(self._body.getLinearVel()[0]))*self.gun['velocity']), \
                                      # self._body.getLinearVel()[1] + (self._body.getLinearVel()[1]/(abs(self._body.getLinearVel()[1]))*self.gun['velocity'])],
                                      [self.gun['velocity'], self.gun['velocity']],
                                      self.gun['damage'],
                                      self._geometry.object._name)
                
            self.gun['ammo'] -= 1
            self.events += ['shoot']
            if self.gun['ammo'] > 0:
                self.gun['timeLeftUntilNextShot'] += self.gun['timeBetweenShots']

            if self.gun['type'] == "burst":
                self.gun['shotsLeftInBurst'] -= 1
                if self.gun['shotsLeftInBurst'] <= 0:
                    self.gun['shotsLeftInBurst'] = self.gun['bulletsPerBurst']
                    self.timeLeftUntilMustShoot = None
                    self.gun['timeLeftUntilNextShot'] = self.gun['timeBetweenBursts']
                else:
                    self.timeLeftUntilMustShoot = self.gun['timeBetweenBurstShots']
                
            self._instability += self.gun['recoil']
        
    def _jump(self):
        if self.isOnGround and self.timeLeftUntilCanJump <= 0:
            self._motor.setYParam(ode.ParamVel,  self.maxJumpVelocity)
            self._motor.setYParam(ode.ParamFMax, self.maxJumpForce)
            self.wantsToJump = False
            self.isJumping = False
        elif self.isOnGround:
            self.wantsToJump = True
            self.isJumping = True
        else:
            self.wantsToJump = False
            
    def _unJump(self):
        self.isJumping = False
        self.timeLeftUntilCanJump = self.timeNeededToPrepareJump

    def _rotateLeft(self):
        if self.isOnGround:
            SphereObject._rotateLeft(self)

    def _rotateRight(self):
        if self.isOnGround:
            SphereObject._rotateRight(self)
        
            
    def postStep(self):
        SphereObject.postStep(self)
        if self.isOnGround:
            # People have a lot of friction against movement, if we aren't moving. Slam on the brakes
            self._motor.setAngleParam(ode.ParamFMax, self.maxStopForce)
            self._motor.setAngleParam(ode.ParamVel, 0)
        self._calculateAccuracy()
        v = self.torsoBody.getAngularVel()[2]
        self._body.addForce((-self.weight*v*abs(v)*0.25,0,0))
            
        self.torsoBody.setQuaternion((1,0,0,0))
        self.torsoBody.setAngularVel((0,0,0))
        
    def isEnabled(self):
        return self.enabled

    def isDisabled(self):
        return not self.enabled
