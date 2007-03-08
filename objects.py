import ode, math

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
        self._body.objectType = "Dynamic"
        self._body.name = name
        
        self._moveLeftPressed = False
        self._moveRightPressed = False
        self._rotateLeftPressed = False
        self._rotateRightPressed = False
        self._crouchPressed = False
        self._jumpPressed = False
        self._shootPressed = False
        self._pointingDirection = (1.0,0.0,0.0)


    def __del__(self):
        self._body.disable()
        StaticObject.__del__(self)
        
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
            
        if self._moveLeftPressed:
            self._moveLeft()
        if self._moveRightPressed:
            self._moveRight()
        if self._rotateLeftPressed:
            self._rotateLeft()
        if self._rotateRightPressed:
            self._rotateRight()
        if self._crouchPressed:
            self._crouch()
        if self._jumpPressed:
            self._jump()
        if self._shootPressed:
            self._shoot()

        # Apply wind friction
        self._body.addForce([-1*0.001*x for x in self._body.getLinearVel()])

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
            self._motor.setYParam(ode.ParamVel,  self.maxMoveVelocity)
            self._motor.setYParam(ode.ParamFMax, self.maxMoveForce)

    def _crouch(self):
        pass

    def _prone(self):
        pass

    def __str__(self):
        return StaticObject.__str__(self) + ", LV=(%2.2f, %2.2f, %2.2f), AV=(%2.2f, %2.2f, %2.2f)" % \
               (self._body.getLinearVel() + self._body.getAngularVel())

    def inputPresses(self, presses):
        self.setDirection(presses.pop(0))
        
        if 'left' in presses:
            self._moveLeftPressed = True
        else:
            self._moveLeftPressed = False
        if 'right' in presses:
            self._moveRightPressed = True
        else:
            self._moveRightPressed = False
        if 'rotate-left' in presses:
            self._rotateLeftPressed = True
        else:
            self._rotateLeftPressed = False
        if 'rotate-right' in presses:
            self._rotateRightPressed = True
        else:
            self._rotateRightPressed = False
        if 'down' in presses:
            self._crouchPressed = True
        else:
            self._crouchPressed = False
        if 'up' in presses:
            self._jumpPressed = True
        else:
            self._jumpPressed = False
        if 'shoot' in presses:
            self._shootPressed = True
        else:
            self._shootPressed = False

class SphereObject(DynamicObject):
    def __init__(self, gameworld, name, size = 0.5, geomFunc = ode.GeomSphere, weight = 10):
        DynamicObject.__init__(self, gameworld, name, size, geomFunc, weight)

        if type(size) == float or type(size) == int:
            self._body.getMass().setSphereTotal(weight, size)
            
        self._body.objectType = "Sphere"

class BulletObject(SphereObject):
    def __init__(self, gameworld, name, direction = None):
        #TODO: When doing graphical, use billboard?
        self.size = (0.05, 0.05, 0.05)
        self.maxSpeed = 50.0
        self.weight = 0.01
        
        SphereObject.__init__(self, gameworld, name, self.size, geomFunc = ode.GeomBox, weight = self.weight)

        if type(self.size) == float or type(self.size) == int:
            self._body.getMass().setSphereTotal(self.weight, self.size)

        if direction:
            self._motor.setXParam(ode.ParamVel,  self.maxSpeed * direction[0])
            self._motor.setXParam(ode.ParamFMax, 100)#ode.Infinity)
            self._motor.setYParam(ode.ParamVel,  self.maxSpeed * direction[1])
            self._motor.setYParam(ode.ParamFMax, 100)#ode.Infinity)
            
        self._body.isDead = False
        self._body.objectType = "Bullet"

    def setOwnerName(self, name):
        self._body.ownerName = name

    def isDead(self):
        return self._body.isDead

    def postStep(self):
        SphereObject.postStep(self)
        self._motor.setXParam(ode.ParamFMax, 0)
        self._motor.setYParam(ode.ParamFMax, 0)

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
        self._geometry.isOnGround = False

        self.timeNeededToPrepareJump = 0.1
        self.timeLeftUntilCanJump = self.timeNeededToPrepareJump
        self.wantsToJump = False
        self._body.objectType = "Person"
        self._body.name = name
        self._body._isDead = False

        self.timeBetweenShots = 0.1
        self.timeLeftUntilNextShot = self.timeBetweenShots
        
        self.maxStopForce = 28000
        self.maxSpinForce = 28000
        self.maxSpinVelocity = 10
        self.maxMoveForce = 1500
        self.maxMoveVelocity = 4
        self.maxJumpForce = ode.Infinity
        self.maxJumpVelocity = 11

        self._bulletNum = 0
        
        self._world = gameworld
        
        self._moveLeftPressed = False
        self._moveRightPressed = False
        self._rotateLeftPressed = False
        self._rotateRightPressed = False
        self._crouchPressed = False
        self._jumpPressed = False
        self._shootPressed = False
        self._pointingDirection = (1.0,0.0,0.0)

    def isDead(self):
        return False

    def frameEnded(self, time):
        # TODO: I hate flags!!! 
        if self.wantsToJump:
            self.timeLeftUntilCanJump -= time
        else:
            self.timeLeftUntilCanJump = self.timeNeededToPrepareJump

        self.timeLeftUntilNextShot -= time

    def _shoot(self):
        if self.timeLeftUntilNextShot < 0.0:                
            self._bulletNum += 1
            self._world.addBullet(self._name + "b" + str(self._bulletNum), \
                                  self._body.getPosition(),
                                  self.getDirection(),
                                  self)
            self.timeLeftUntilNextShot = self.timeBetweenShots
        
    def _jump(self):
        if self._geometry.isOnGround and self.timeLeftUntilCanJump <= 0:
            self._motor.setYParam(ode.ParamVel,  self.maxJumpVelocity)
            self._motor.setYParam(ode.ParamFMax, self.maxJumpForce)
            self.wantsToJump = False
        elif self._geometry.isOnGround:
            self.wantsToJump = True
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
