import ode, math, random, time

class StaticObject(object):    
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
        self.type = "Static"

    def getBody(self):
        return None

    def close(self):
        self._geometry.object = None

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
        self.type = "Dynamic"
        self._body.name = name

        self.presses = {}
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

    def initialisePosition(self, position):
        StaticObject.setPosition(self, position)

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

    def preStep(self):
        if 'l' in self.presses:
            self._moveLeft()
        if 'r' in self.presses:
            self._moveRight()
        if 'rl' in self.presses:
            self._rotateLeft()
        if 'rr' in self.presses:
            self._rotateRight()
        if 'd' in self.presses:
            self._crouch()
        else:
            self._unCrouch()
        if 'u' in self.presses:
            self._jump()
        else:
            self._unJump()
        if 's' in self.presses:
            self._shoot()
        else:
            self._unShoot()
        if 'a' in self.presses:
            self._reload()

        # Apply wind friction
        self._body.addForce([-1*0.000001*math.fabs(x)*x for x in self._body.getLinearVel()])

        #if self.isOnGround:
        #    # Apply rolling friction
        #    self._body.addTorque([x*-0.5 for x in self._body.getAngularVel()])
        
    def postStep(self):
        self._alignToZAxis()
        self._motor.setXParam(ode.ParamFMax, 0)
        self._motor.setYParam(ode.ParamFMax, 0)
        self._motor.setAngleParam(ode.ParamFMax, 0)

    def frameEnded(self, frameTime):
        pass

    def _alignToZAxis(self):
        self._alignBodyToZAxis(self._body)

    def _alignBodyToZAxis(self, body):
        rot = body.getAngularVel()
        old_quat = body.getQuaternion()
        quat_len = math.sqrt( old_quat[0] * old_quat[0] + old_quat[3] * old_quat[3] )
        body.setQuaternion((old_quat[0] / quat_len, 0, 0, old_quat[3] / quat_len))
        body.setAngularVel((0,0,rot[2]))
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
        self._motor.setAngleParam(ode.ParamVel,  self.maxSpinVelocity)
        self._motor.setAngleParam(ode.ParamFMax, self.maxSpinForce)

    def _rotateRight(self):
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
            
        self.type = "Sphere"

class BulletObject(SphereObject):
    def __init__(self, gameworld, name, direction = None, velocity = 50.0, damage = 1.0):
        self.size = 0.025
        self.maxSpeed = velocity
        self.weight = 5.0
        self.damage = damage
        
        SphereObject.__init__(self, gameworld, name, self.size, geomFunc = ode.GeomSphere, weight = self.weight)

        if type(self.size) == float or type(self.size) == int:
            self._body.getMass().setSphereTotal(self.weight, self.size)

        if direction:
            self._motor.setXParam(ode.ParamVel,  self.maxSpeed * direction[0])
            self._motor.setXParam(ode.ParamFMax, ode.Infinity)
            self._motor.setYParam(ode.ParamVel,  self.maxSpeed * direction[1])
            self._motor.setYParam(ode.ParamFMax, ode.Infinity)
            
        self.setDead(False)
        self.type = "Bullet"
        self.damage = damage
        self.hasSentToClients = False

    def __del__(self):
        SphereObject.__del__(self)

    def setOwnerName(self, name):
        self.ownerName = name

    def postStep(self):
        SphereObject.postStep(self)
        self._motor.setXParam(ode.ParamFMax, 0)
        self._motor.setYParam(ode.ParamFMax, 0)
        
        if self.isDead():
            self.disable()

    def getAttributes(self):
        if self.hasSentToClients:
            return 0
        else:
            return [self.to2d(self._body.getPosition()),
                    self.to2d(self._body.getLinearVel())]

    def setAttributes(self, attributes):
        if type(attributes) != int:
            self._body.setPosition(self.to3d(attributes[0]))
            self._body.setLinearVel(self.to3d(attributes[1]))

    def clearEvents(self):
        self.hasSentToClients = True  
        

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
        
        self.type = "Person"
        self.ownerName = name
        self._bulletNum = 0
        self.timeNeededToPrepareJump = 0.25
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

        self.gunIDs = {
             "Pistol":  1,
             "SMPistol":2,
             "SMG":     3,
             "Shotgun": 4,
             "Assault": 5,
             "Support": 6,
             "Sniper":  7,
            }

        self.gunNames = {}
        for name, id in self.gunIDs.items():
            self.gunNames[id] = name

        self.reset()
        self._instability = 0.0

    def close(self):
        self._geometry.object = None
        self._torsoTransform.object = None
        self._headTransform.object = None

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
        self.shotsLeftInBurst = 0
        self.isCrouching = False
        self.canShoot = True
        self.isJumping = False
        self.isOnGround = False
        self.timeLeftUntilCanJump = self.timeNeededToPrepareJump
        self.wantsToJump = False
        self._pointingDirection = (1.0,0.0,0.0)
        self.presses = {}
        self.health = self.maxHealth

        self.guns = {
            'Pistol':{
                'maxAmmo':7,
                'ammo':7,
                'reloadTime':1.5,
                'timeLeftUntilNextShot':0.0,
                'reloading':False,
                'accuracy':0.95,
                'timeBetweenShots':0.0,
                'damage':10,
                'velocity':35.0,
                'type':'single',
                'zoom':35,
                'recoil':0.1,
                'auto':False,
                },
            'SMPistol':{
                'maxAmmo':30,
                'ammo':30,
                'reloadTime':3.0,
                'timeLeftUntilNextShot':0.0,
                'reloading':False,
                'accuracy':0.7,
                'timeBetweenShots':0.01,
                'damage':3.5,
                'velocity':25.0,
                'type':'single',
                'zoom':30,
                'recoil':0.06,
                'auto':True,
                },
            'SMG':{
                'maxAmmo':50,
                'ammo':50,
                'reloadTime':3.0,
                'timeLeftUntilNextShot':0.0,
                'reloading':False,
                'accuracy':0.8,
                'timeBetweenShots':0.1,
                'damage':5,
                'velocity':40.0,
                'type':'single',
                'zoom':40,
                'recoil':0.15,
                'auto':True,
                },
            'Shotgun':{
                'maxAmmo':5,
                'ammo':5,
                'reloadTime':3.0,
                'timeLeftUntilNextShot':0.0,
                'reloading':False,
                'accuracy':0.75,
                'timeBetweenShots':0.3,
                'damage':7,
                'velocity':25.0,
                'type':'scatter',
                'bulletsPerShot':11,
                'zoom':35,
                'recoil':0.0,
                'auto':False,
                },
            'Assault':{
                'maxAmmo':30,
                'ammo':30,
                'reloadTime':2.2,
                'timeLeftUntilNextShot':0.0,
                'reloading':False,
                'accuracy':0.85,
                'timeBetweenShots':0.1,
                'damage':8.0,
                'velocity':45.0,
                'type':'burst',
                'bulletsPerBurst':3,
                'timeBetweenBurstShots':0.035,
                'timeBetweenBursts':0.4,
                'type2':'single',
                'zoom':45,
                'recoil':0.08,
                'auto':False,
                },
            'Support':{
                'maxAmmo':100,
                'ammo':100,
                'reloadTime':5.0,
                'timeLeftUntilNextShot':0.0,
                'reloading':False,
                'accuracy':0.8,
                'timeBetweenShots':0.18,
                'damage':10,
                'velocity':50.0,
                'type':'single',
                'bulletsPerShot':3,
                'zoom':60,
                'recoil':0.075,
                'auto':True,
                },
            'Sniper':{
                'maxAmmo':5,
                'ammo':5,
                'reloadTime':10.0,
                'timeLeftUntilNextShot':0.0,
                'reloading':False,
                'accuracy':0.95,
                'timeBetweenShots':5.0,
                'damage':100,
                'velocity':70.0,
                'type':'single',
                'zoom':80,
                'recoil':1.0,
                'auto':False,
                }
            }

        self.gunName = ""
        self.primaryGunName = "SMG"
        self.secondayGunName = "Assault"
        self.setGun("SMG")
        
    def doDamage(self, damage):
        if not self.isDead():
            self.health -= damage
            if self.health <= 0:
                self.health = 0
                self.setDead()
                self.timeUntilRespawn = self.respawnTime
            
    def preStep(self):
        if not self.isDead():
            #self._body.addForce(self._torsoBody.getForce())
            
            SphereObject.preStep(self)
            if '1' in self.presses:
                self.setGun("Pistol")
            if '2' in self.presses:
                self.setGun("SMPistol")
            if '3' in self.presses:
                self.setGun("SMG")
            if '4' in self.presses:
                self.setGun("Shotgun")
            if '5' in self.presses:
                self.setGun("Assault")
            if '6' in self.presses:
                self.setGun("Support")
            if '7' in self.presses:
                self.setGun("Sniper")
            if 'mu' in self.presses:
                self.setGun(self.primaryGunName)
            if 'md' in self.presses:
                self.setGun(self.secondaryGunName)
        else:
            if self.timeUntilRespawn <= 0:
                self.setDead(False)
                self.enable()
                self.reset()
                self.setPosition(self.spawnPosition)

    def setGun(self, name):
        #Store Old Gun Stats
        if self.gunName != "":
            self.guns[self.gunName]['ammo'] = self.ammo
            self.guns[self.gunName]['reloading'] = self.reloading
            self.guns[self.gunName]['timeLeftUntilNextShot'] = self.timeLeftUntilNextShot
                
        #Load New Gun Stats
        if self.gunName != name:
            self.gunName = name
            self.maxAmmo = self.guns[self.gunName]['maxAmmo']
            self.ammo = self.guns[self.gunName]['ammo']
            self.reloading = self.guns[self.gunName]['reloading'] 
            self.reloadTime = self.guns[self.gunName]['reloadTime']
            self.timeLeftUntilNextShot = self.guns[self.gunName]['timeLeftUntilNextShot']
            self.timeBetweenShots = self.guns[self.gunName]['timeBetweenShots']
            self._accuracy = self.guns[self.gunName]['accuracy']
            self._maxAccuracy = self.guns[self.gunName]['accuracy']
            self.damage = self.guns[self.gunName]['damage']
            self.velocity = self.guns[self.gunName]['velocity']
            self.recoil = self.guns[self.gunName]['recoil']
            self.automatic = self.guns[self.gunName]['auto']
            if self.guns[self.gunName]['type'] == "burst":
                self.shotsLeftInBurst = self.guns[self.gunName]['bulletsPerBurst']

    def getAttributes(self):
        # Massive corners cut here for the sake of network traffic
        return SphereObject.getAttributes(self) + \
               [int(self.health),
                int(self.gunIDs[self.gunName]),
                int(self.ammo),
                self.timeLeftUntilNextShot if self.timeLeftUntilNextShot > 0 else 0,
                self.timeUntilRespawn if self.timeUntilRespawn > 0 else 0,
                (1 if self.reloading else 0 |
                2 if self.isCrouching else 0 |
                4 if self.isJumping else 0 |
                8 if self.isDead() else 0 |
                16 if self.canShoot else 0)
                ]

    def setAttributes(self, attributes):
        SphereObject.setAttributes(self,attributes)
        self.health = attributes[5]
        self.setGun(self.gunNames[attributes[6]])
        self.ammo = attributes[7]
        self.timeLeftUntilNextShot = attributes[8]
        self.timeUntilRespawn = attributes[9]
        state = attributes[10]
        self.reloading = (state & 1 == 1)
        self.isCrouching = (state & 2 == 2)
        self.isJumping = (state & 4 == 4)
        self.setDead((state & 8 == 8))
        self.canShoot = (state & 16 == 16)

    def _calculateAccuracy(self):
            
        self._accuracy -= self._instability
        self._instability /= 1.1

        recoveryWeight = 2.5

        if self.isCrouching and self.isOnGround:
            self._accuracy  = (self._accuracy*recoveryWeight + ((self._maxAccuracy+1.0)/2.0) )/(recoveryWeight+1)
        elif self.isOnGround:
            self._accuracy  = (self._accuracy*recoveryWeight + self._maxAccuracy)/(recoveryWeight+1)
        else:
            self._accuracy  = (self._accuracy*recoveryWeight + self._maxAccuracy * 0.75)/(recoveryWeight + 1)
            

    def getAccuracy(self):
        if self.guns[self.gunName]['type'] == "scatter":
            return self._maxAccuracy
        else:
            return self._accuracy

    def setAccuracy(self, accuracy):
        self._accuracy = accuracy

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

        if self.reloading:
            text += "\n Reloading: %3i%%" % (self.timeLeftUntilNextShot * 100 / self.reloadTime)
        else:
            text += "\n Ammo: %i/%i" % (self.ammo, self.maxAmmo)
            if self.timeLeftUntilNextShot > 0:
                text += " (%3i%%)" % (self.timeLeftUntilNextShot * 100 / self.timeBetweenShots)

        return text

    def frameEnded(self, time):
        self.timeUntilRespawn -= time

        if self.timeLeftUntilMustShoot:
            self.timeLeftUntilMustShoot -= time
            if self.timeLeftUntilMustShoot < 0:
                self._shoot()
        
        # TODO: I hate flags!!! 
        if self.wantsToJump:
            self.timeLeftUntilCanJump -= time
        else:
            self.timeLeftUntilCanJump = self.timeNeededToPrepareJump

        self.timeLeftUntilNextShot -= time

        if self.timeLeftUntilNextShot <= 0.0 and self.reloading:
            self.reloading = False

    def _calculateScatter(self):
        a = None
        a = self.getAccuracy()
        return random.random()*(1-a)-0.5*(1-a)

    def _reload(self):
        if not self.reloading and self.ammo != self.maxAmmo:
            self.ammo = self.maxAmmo
            self.timeLeftUntilNextShot = self.reloadTime
            self.reloading = True
            self.timeLeftUntilMustShoot = None
            if self.guns[self.gunName]['type'] == "burst":
                self.shotsLeftInBurst = self.guns[self.gunName]['bulletsPerBurst']
            
    def _crouch(self):
        self.isCrouching = True
        
    def _unCrouch(self):
        self.isCrouching = False

    def getShootOffset(self):
        return [0,0.5,0]

    def _unShoot(self):
        self.canShoot = True

    def _shoot(self):
        if (self.timeLeftUntilMustShoot and self.timeLeftUntilMustShoot <= 0 and self.ammo > 0) or\
           self.timeLeftUntilNextShot < 0.0 and self.ammo > 0 and self.canShoot:
            if not self.automatic:
                self.canShoot = False
            numShots = 1
            if self.guns[self.gunName]['type'] == "scatter":
                numShots = self.guns[self.gunName]['bulletsPerShot']

            for i in range(numShots):
                scatter = self._calculateScatter()
                self._bulletNum += 1
                self._world.addBullet(self._name + "b" + str(self._bulletNum), \
                                      [a+b for a,b in zip(self._body.getPosition(), self.getShootOffset())],
                                      [self.getDirection()[0] + self._calculateScatter(),
                                       self.getDirection()[1] + self._calculateScatter(),
                                       0],
                                      self.velocity,
                                      self.damage,
                                      self)
                
            self.ammo -= 1
            self.events += ['shoot']
            self.timeLeftUntilNextShot = self.timeBetweenShots

            if self.guns[self.gunName]['type'] == "burst":
                self.shotsLeftInBurst -= 1
                if self.shotsLeftInBurst <= 0:
                    self.shotsLeftInBurst = self.guns[self.gunName]['bulletsPerBurst']
                    self.timeLeftUntilMustShoot = None
                    self.timeLeftUntilNextShot = self.guns[self.gunName]['timeBetweenBursts']
                else:
                    self.timeLeftUntilMustShoot = self.guns[self.gunName]['timeBetweenBurstShots']
                
            self._instability += self.recoil
        
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
        # Temp variable to prevent clobbering
        SphereObject.postStep(self)
        if self.isOnGround:
            # People have a lot of friction against movement, if we aren't moving. Slam on the brakes
            self._motor.setAngleParam(ode.ParamFMax, self.maxStopForce)
            self._motor.setAngleParam(ode.ParamVel, 0)
        self._calculateAccuracy()
        v = self.torsoBody.getAngularVel()[2]
        self._body.addForce((-self.weight*v*math.fabs(v)*0.25,0,0))
            
        self.torsoBody.setQuaternion((1,0,0,0))
        self.torsoBody.setAngularVel((0,0,0))
        
    def isEnabled(self):
        return self.enabled

    def isDisabled(self):
        return not self.enabled
