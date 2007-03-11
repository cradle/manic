import ode, math, random, time

class StaticObject(object):    
    def __init__(self, gameworld, name, size = (1.0, 1.0, 1.0), geomFunc = ode.GeomBox):
        self._size = size
        self._geometry = geomFunc(gameworld.space, self._size)
        self._name = name
        self._nick = name
        self._world = gameworld.world
        self._space = gameworld.space
        self._gameworld = gameworld

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

        self._geometry.isOnGround = False
        self.isJumping = False
        self._body.objectType = "Dynamic"
        self._body.name = name

        self.presses = {}
        self._pointingDirection = (1.0,0.0,0.0)

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
        
    def isDead(self):
        return False

    def getDirection(self):
        return self._pointingDirection

    def setDirection(self, direction):
        self._pointingDirection = direction

    def getAttributes(self):
        return [self._body.getPosition(),
         self._body.getQuaternion(),
         self._body.getAngularVel(),
         self._body.getLinearVel(),
         self.getDirection()]

    def setAttributes(self, attributes):
        self._body.setPosition(attributes[0])
        self._body.setQuaternion(attributes[1])
        self._body.setAngularVel(attributes[2])
        self._body.setLinearVel(attributes[3])
        self.setDirection(attributes[4])

    def preStep(self):
        if 'left' in self.presses:
            self._moveLeft()
        if 'right' in self.presses:
            self._moveRight()
        if 'rotate-left' in self.presses:
            self._rotateLeft()
        if 'rotate-right' in self.presses:
            self._rotateRight()
        if 'down' in self.presses:
            self._crouch()
        else:
            self._unCrouch()
        if 'up' in self.presses:
            self._jump()
        else:
            self._unJump()
        if 'shoot' in self.presses:
            self._shoot()
        if 'reload' in self.presses:
            self._reload()

        # Apply wind friction
        self._body.addForce([-1*0.000001*math.fabs(x)*x for x in self._body.getLinearVel()])

        #if self._geometry.isOnGround:
        #    # Apply rolling friction
        #    self._body.addTorque([x*-0.5 for x in self._body.getAngularVel()])
        
    def postStep(self):
        self._alignToZAxis()
        self._motor.setXParam(ode.ParamFMax, 0)
        self._motor.setYParam(ode.ParamFMax, 0)
        self._motor.setAngleParam(ode.ParamFMax, 0)
        self._geometry.isOnGround = False

    def frameEnded(self, frameTime):
        pass

    def _alignToZAxis(self):
        rot = self._body.getAngularVel()
        old_quat = self._body.getQuaternion()
        quat_len = math.sqrt( old_quat[0] * old_quat[0] + old_quat[3] * old_quat[3] )
        self._body.setQuaternion((old_quat[0] / quat_len, 0, 0, old_quat[3] / quat_len))
        self._body.setAngularVel((0,0,rot[2]))
        # http://opende.sourceforge.net/wiki/index.php/HOWTO_constrain_objects_to_2d

    def _shoot(self):
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
        if self._geometry.isOnGround:
            self.isJumping = True
            self._motor.setYParam(ode.ParamVel,  self.maxMoveVelocity)
            self._motor.setYParam(ode.ParamFMax, self.maxMoveForce)
            
    def _unJump(self):
        self.isJumping = False

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
        self.setDirection(presses.pop(0))
        self.presses = presses

class SphereObject(DynamicObject):
    def __init__(self, gameworld, name, size = 0.5, geomFunc = ode.GeomSphere, weight = 10):
        DynamicObject.__init__(self, gameworld, name, size, geomFunc, weight)

        if type(size) == float or type(size) == int:
            self._body.getMass().setSphereTotal(weight, size)
            
        self._body.objectType = "Sphere"

class BulletObject(SphereObject):
    def __init__(self, gameworld, name, direction = None, velocity = 50.0, damage = 1.0):
        #TODO: When doing graphical, use billboard?
        self.size = (0.05, 0.05, 0.05)
        self.maxSpeed = velocity
        self.weight = 5.0
        self.damage = damage
        
        SphereObject.__init__(self, gameworld, name, self.size, geomFunc = ode.GeomBox, weight = self.weight)

        if type(self.size) == float or type(self.size) == int:
            self._body.getMass().setSphereTotal(self.weight, self.size)

        if direction:
            self._motor.setXParam(ode.ParamVel,  self.maxSpeed * direction[0])
            self._motor.setXParam(ode.ParamFMax, ode.Infinity)
            self._motor.setYParam(ode.ParamVel,  self.maxSpeed * direction[1])
            self._motor.setYParam(ode.ParamFMax, ode.Infinity)
            
        self._body._isDead = False
        self._body.objectType = "Bullet"
        self._body.damage = damage

    def setOwnerName(self, name):
        self._body.ownerName = name

    def isDead(self):
        return self._body._isDead

    def postStep(self):
        SphereObject.postStep(self)
        self._motor.setXParam(ode.ParamFMax, 0)
        self._motor.setYParam(ode.ParamFMax, 0)
        
        if self.isDead():
            self.disable()

    def getAttributes(self):
        return [self._body.getPosition(),
         self._body.getLinearVel()]

    def setAttributes(self, attributes):
        self._body.setPosition(attributes[0])
        self._body.setLinearVel(attributes[1])

class Person(SphereObject):
    def __init__(self, gameworld, name, camera = None):
        self._gameworld = gameworld

        # The size of the bounding box
        size = (1.0, 1.0, 1.0)
        weight = 70
        self._name = name        
        self._size = size
        self._geometry = ode.GeomSphere(gameworld.space, min(self._size))
        self._body = ode.Body(gameworld.world)
        mass = ode.Mass()
        mass.setBoxTotal(weight, size[0], size[1], size[2])
        self._body.setMass(mass)
        self._geometry.setBody(self._body)
        self._motor = ode.Plane2DJoint(gameworld.world)
        self._motor.attach(self._body, ode.environment)
        self._body.objectType = "Person"
        self._body.ownerName = name
        self._bulletNum = 0
        self.timeNeededToPrepareJump = 0.0
        self.maxStopForce = 28000
        self.maxSpinForce = 28000
        self.maxSpinVelocity = 10
        self.maxMoveForce = 1500
        self.maxMoveVelocity = 4
        self.maxJumpForce = ode.Infinity
        self.maxJumpVelocity = 11
        self._world = gameworld
        self.maxHealth = 100
        self.spawnPosition = None
        self.respawnTime = 3.0
        self._body._isDead = False
        self.timeUntilRespawn = 0.0
        self.isShooting = False
        self.reset()
        
    def reset(self):
        self.isCrouching = False
        self.isJumping = False
        self._geometry.isOnGround = False
        self.timeLeftUntilCanJump = self.timeNeededToPrepareJump
        self.wantsToJump = False
        self._pointingDirection = (1.0,0.0,0.0)
        self.presses = {}
        self.health = self.maxHealth

        self.guns = {
            'SMPistol':{
                'maxAmmo':30,
                'ammo':30,
                'reloadTime':3.0,
                'timeLeftUntilNextShot':0.0,
                'reloading':False,
                'accuracy':0.6,
                'timeBetweenShots':0.01,
                'damage':3.5,
                'velocity':25.0,
                'type':'single'
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
                'type':'single'
                },
            'Shotgun':{
                'maxAmmo':2,
                'ammo':2,
                'reloadTime':3.0,
                'timeLeftUntilNextShot':0.0,
                'reloading':False,
                'accuracy':0.75,
                'timeBetweenShots':0.3,
                'damage':11.12,
                'velocity':25.0,
                'type':'scatter',
                'bulletsPerShot':9
                },
            'Assault':{
                'maxAmmo':30,
                'ammo':30,
                'reloadTime':5.0,
                'timeLeftUntilNextShot':0.0,
                'reloading':False,
                'accuracy':0.95,
                'timeBetweenShots':0.2,
                'damage':15,
                'velocity':50.0,
                'type':'burst',
                'bulletsPerShot':3
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
                'type':'single'
                }
            }

        self.gunName = ""
        self.setGun("SMG")
        
    def doDamage(self, damage):
        if not self.isDead():
            self.health -= damage
            if self.health <= 0:
                self.health = 0
                self._body._isDead = True
                self.timeUntilRespawn = self.respawnTime
            
    def preStep(self):
        if not self.isDead():
            SphereObject.preStep(self)
            if 'weapon1' in self.presses:
                self.setGun("SMPistol")
            if 'weapon2' in self.presses:
                self.setGun("SMG")
            if 'weapon3' in self.presses:
                self.setGun("Shotgun")
            if 'weapon4' in self.presses:
                self.setGun("Assault")
            if 'weapon5' in self.presses:
                self.setGun("Sniper")
        else:
            if self.timeUntilRespawn <= 0:
                self._body._isDead = False
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
            self.maxAmmo = self.guns[name]['maxAmmo']
            self.ammo = self.guns[name]['ammo']
            self.reloading = self.guns[self.gunName]['reloading'] 
            self.reloadTime = self.guns[self.gunName]['reloadTime']
            self.timeLeftUntilNextShot = self.guns[self.gunName]['timeLeftUntilNextShot']
            self.timeBetweenShots = self.guns[self.gunName]['timeBetweenShots']
            self.accuracy = self.guns[self.gunName]['accuracy']
            self.damage = self.guns[self.gunName]['damage']
            self.velocity = self.guns[self.gunName]['velocity']

    def getAttributes(self):
        return SphereObject.getAttributes(self) + \
               [self.health,
                self.gunName,
                self.ammo,
                self.reloading,
                self.timeLeftUntilNextShot,
                self.isCrouching,
                self.isJumping,
                self.isDead(),
                self.timeUntilRespawn]

    def setAttributes(self, attributes):
        SphereObject.setAttributes(self,attributes)
        self.health = attributes[5]
        self.setGun(attributes[6])
        self.ammo = attributes[7]
        self.reloading = attributes[8]
        self.timeLeftUntilNextShot = attributes[9]
        self.isCrouching = attributes[10]
        self.isJumping = attributes[11]
        self._body._isDead = attributes[12]
        self.timeUntilRespawn = attributes[13]

    def getEvents(self):
        events = SphereObject.getEvents(self)
        if self.isShooting:
            events += ['shoot']
        return events

    def clearEvents(self):
        SphereObject.clearEvents(self)
        self.isShooting = False

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

    def isDead(self):
        return self._body._isDead

    def frameEnded(self, time):
        self.timeUntilRespawn -= time
        
        # TODO: I hate flags!!! 
        if self.wantsToJump:
            self.timeLeftUntilCanJump -= time
        else:
            self.timeLeftUntilCanJump = self.timeNeededToPrepareJump

        self.timeLeftUntilNextShot -= time

        if self.timeLeftUntilNextShot <= 0.0 and self.reloading:
            self.reloading = False

    def _calculateScatter(self):
        a = self.accuracy
        if self.isCrouching and self._geometry.isOnGround:
            a = (a + 1.0)/2.0
        return random.random()*(1-a)-0.5*(1-a)

    def _reload(self):
        if not self.reloading and self.ammo != self.maxAmmo:
            self.ammo = self.maxAmmo
            self.timeLeftUntilNextShot = self.reloadTime
            self.reloading = True
            
    def _crouch(self):
        self.isCrouching = True
        
    def _unCrouch(self):
        self.isCrouching = False

    def _shoot(self):
        if self.timeLeftUntilNextShot < 0.0 and self.ammo > 0:
            self.isShooting = True
            numShots = 1
            if self.guns[self.gunName]['type'] == "scatter":
                numShots = self.guns[self.gunName]['bulletsPerShot']

            for i in range(numShots):
                scatter = self._calculateScatter()
                self._bulletNum += 1
                self._world.addBullet(self._name + "b" + str(self._bulletNum), \
                                      self._body.getPosition(),
                                      [self.getDirection()[0] + self._calculateScatter(),
                                       self.getDirection()[1] + self._calculateScatter(),
                                       0],
                                      self.velocity,
                                      self.damage,
                                      self)
                
            self.ammo -= 1
            self.timeLeftUntilNextShot = self.timeBetweenShots
        
    def _jump(self):
        if self._geometry.isOnGround and self.timeLeftUntilCanJump <= 0:
            self._motor.setYParam(ode.ParamVel,  self.maxJumpVelocity)
            self._motor.setYParam(ode.ParamFMax, self.maxJumpForce)
            self.wantsToJump = False
        elif self._geometry.isOnGround:
            self.wantsToJump = True
            self.isJumping = True
        else:
            self.wantsToJump = False

    def _rotateLeft(self):
        if self._geometry.isOnGround:
            SphereObject._rotateLeft(self)

    def _rotateRight(self):
        if self._geometry.isOnGround:
            SphereObject._rotateRight(self)

    # TODO: Should be pre-step? Post-collision?
    def postStep(self):
        isOnGround = self._geometry.isOnGround
        SphereObject.postStep(self)
        if isOnGround:
            # People have a lot of friction against movement, if we aren't moving. Slam on the brakes
            self._motor.setAngleParam(ode.ParamFMax, self.maxStopForce)
            self._motor.setAngleParam(ode.ParamVel, 0)
            
    def isEnabled(self):
        return self.enabled

    def isDisabled(self):
        return not self.enabled
