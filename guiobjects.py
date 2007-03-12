import objects
import Ogre as ogre
import ode
import OIS
import CEGUI
import OgreAL
import math, random

class StaticObject(objects.StaticObject):    
    def __init__(self, gameworld, name, size = (1.0, 1.0, 1.0), scale = (0.1, 0.1, 0.1), mesh = 'crate.mesh', geomFunc = ode.GeomBox):
        super(StaticObject, self).__init__(gameworld, name, size, geomFunc)   

        self._entity = gameworld.sceneManager.createEntity('e' + name, mesh)
        self._node = gameworld.sceneManager.rootSceneNode.createChildSceneNode('n' + name)
        self._node.attachObject(self._entity)
        
        if hasattr(size, "__getitem__"):
            self._node.setScale(scale[0]*size[0],scale[1]*size[1],scale[2]*size[2])
        else:
            self._node.setScale(scale[0]*size,scale[1]*size,scale[2]*size)

        self._updateDisplay()

    def __del__(self):
        self._gameworld.sceneManager.rootSceneNode.removeAndDestroyChild('n' + self._name)
        objects.StaticObject.__del__(self)
        
    def setPosition(self, position):
        super(StaticObject, self).setPosition(position)
        self._updateDisplay()

    def setRotation(self, quaternion):
        super(StaticObject, self).setRotation(quaternion)
        self._updateDisplay()

    def _updateDisplay(self):
        self._node.setPosition(self._geometry.getPosition())
        self._node.setOrientation(self._geometry.getQuaternion()[0],\
                                 self._geometry.getQuaternion()[1],\
                                 self._geometry.getQuaternion()[2],\
                                 self._geometry.getQuaternion()[3])


class DynamicObject(objects.DynamicObject, StaticObject):    
    def __init__(self, gameworld, name, size = (1.0,1.0,1.0), \
                 scale = (0.1, 0.1, 0.1), mesh = 'crate.mesh', geomFunc = ode.GeomBox, weight = 50):
        StaticObject.__init__(self, gameworld, name, size, scale, mesh, geomFunc)
        objects.DynamicObject.__init__(self, gameworld, name, size, geomFunc, weight)

        self.keys = {
            'up':OIS.KC_I,
            'down':OIS.KC_K,
            'downdown':OIS.KC_Z,
            'left':OIS.KC_L,
            'right':OIS.KC_J,
            'rotate-left':OIS.KC_O,
            'rotate-right':OIS.KC_U,
            'reload':OIS.KC_UNASSIGNED,
            'weapon1':OIS.KC_UNASSIGNED,
            'weapon2':OIS.KC_UNASSIGNED,
            'weapon3':OIS.KC_UNASSIGNED,
            'weapon4':OIS.KC_UNASSIGNED,
            'weapon5':OIS.KC_UNASSIGNED,
            'shoot':None}

    def frameEnded(self, frameTime):
        objects.DynamicObject.frameEnded(self, frameTime)
        self._updateDisplay()

    def input(self, keyboard, mouse):
        presses = [self.getDirection()]
        
        if CEGUI.WindowManager.getSingleton().getWindow("TextWindow/Editbox1").hasInputFocus():
            return presses

        if keyboard.isKeyDown(self.keys['left']):
            #self._moveLeft()
            presses.append("l")
        if keyboard.isKeyDown(self.keys['right']):
            #self._moveRight()
            presses.append("r")
        if keyboard.isKeyDown(self.keys['rotate-left']):
            #self._rotateLeft()
            presses.append("rl")
        if keyboard.isKeyDown(self.keys['rotate-right']):
            #self._rotateRight()
            presses.append("rr")
        if keyboard.isKeyDown(self.keys['up']):
            #self._jump()
            presses.append("u")
        if keyboard.isKeyDown(self.keys['down']):
            #self._crouch()
            presses.append("d")
        if keyboard.isKeyDown(self.keys['reload']):
            #self._reload()
            presses.append("a")
        if keyboard.isKeyDown(self.keys['downdown']):
            #self._prone()
            presses.append("p")
        if keyboard.isKeyDown(self.keys['weapon1']):
            presses.append("1")
        if keyboard.isKeyDown(self.keys['weapon2']):
            presses.append("2")
        if keyboard.isKeyDown(self.keys['weapon3']):
            presses.append("3")
        if keyboard.isKeyDown(self.keys['weapon4']):
            presses.append("4")
        if keyboard.isKeyDown(self.keys['weapon5']):
            presses.append("5")
        if self.keys['shoot'] != None and mouse.getMouseState().buttonDown(self.keys['shoot']):
            #self._shoot()
            presses.append("s")

        return presses
    
    def disable(self):
        objects.DynamicObject.disable(self)
        self._entity.setVisible(False)

    def enable(self):
        objects.DynamicObject.enable(self)
        self._entity.setVisible(True)

    def __del__(self):
        StaticObject.__del__(self)
        objects.DynamicObject.__del__(self)

class SphereObject(objects.SphereObject, DynamicObject):
    def __init__(self, gameworld, name, size = 0.5, scale = (0.01, 0.01, 0.01), \
                 mesh = 'sphere.mesh', geomFunc = ode.GeomSphere, weight = 10):
        objects.SphereObject.__init__(self, gameworld, name, size, geomFunc, weight)
        DynamicObject.__init__(self, gameworld, name, size, scale, mesh, geomFunc, weight)
            
        self.keys['up'] = OIS.KC_NUMPAD8
        self.keys['down'] = OIS.KC_NUMPAD5
        self.keys['left'] = OIS.KC_NUMPAD4
        self.keys['right'] = OIS.KC_NUMPAD6
        self.keys['rotate-left'] = OIS.KC_NUMPAD7
        self.keys['rotate-right'] = OIS.KC_NUMPAD9

    def __del__(self):
        DynamicObject.__del__(self)
        objects.SphereObject.__del__(self)

class BulletObject(objects.BulletObject, SphereObject):
    def __init__(self, gameworld, name, direction = None, velocity = None, damage = 1):
        objects.BulletObject.__init__(self, gameworld, name, direction, velocity, damage)

        self.keys = {
            'up':OIS.KC_I,
            'down':OIS.KC_K,
            'downdown':OIS.KC_Z,
            'left':OIS.KC_L,
            'right':OIS.KC_J,
            'rotate-left':OIS.KC_O,
            'rotate-right':OIS.KC_U,
            'reload':OIS.KC_UNASSIGNED,
            'weapon1':OIS.KC_UNASSIGNED,
            'weapon2':OIS.KC_UNASSIGNED,
            'weapon3':OIS.KC_UNASSIGNED,
            'weapon4':OIS.KC_UNASSIGNED,
            'weapon5':OIS.KC_UNASSIGNED,
            'shoot':None}
        
        self.name = name
        self._entity = gameworld.sceneManager.createBillboardSet("bb" + name)
        self._entity.setDefaultDimensions(0.1,0.1)

        #self.billboard = ogre.Billboard()
        self._entity.createBillboard(0,0,0)
                
        self._node = gameworld.sceneManager.rootSceneNode.createChildSceneNode('n' + name)
        self._node.attachObject(self._entity)

        self._updateDisplay()

        self.gameworld = gameworld
        
    def __del__(self):
        self.gameworld.sceneManager.destroyBillboardSet("bb" + self.name)
        SphereObject.__del__(self)
        objects.BulletObject.__del__(self)

class Person(objects.Person, SphereObject):
    def __init__(self, gameworld, name, camera = None):
        super(Person, self).__init__(gameworld, name, camera)

        # The scale to scale the model by
        scale = 0.01
        offset = (0.0, -self.feetSize, 0.0)
        self._nodeOffset = offset
        
        # Entity
        self._entity = gameworld.sceneManager.createEntity('e' + name, 'ninja.mesh')
        self._entity.setMaterialName(random.choice(["white-ninja",
                                                    "grey-ninja",
                                                    "green-ninja",
                                                    "red-ninja",
                                                    "blue-ninja",
                                                    "yellow-ninja"]))
        # Scene -> Node
        self._node = gameworld.sceneManager.rootSceneNode.createChildSceneNode('n' + name)
        self._node.setScale(scale,scale,scale)
        # Node -> Entity
        self._node.attachObject(self._entity)
        
        self.soundManager = gameworld.soundManager

        self.sounds = {}
        self.sounds['SMPistol'] = self.soundManager.createSound("SMPistol-" + name, "smg.wav", False)
        self.sounds['SMG'] = self.soundManager.createSound("SMG-" + name, "bolter.wav", False)
        self.sounds['Test'] = self.soundManager.createSound("Test-" + name, "pbeampistol.wav", False)
        self.sounds['Assault'] = self.soundManager.createSound("Assault-" + name, "assault.wav", False)
        self.sounds['Shotgun'] = self.soundManager.createSound("Shotgun-" + name, "shotgun.wav", False)
        self.sounds['Sniper'] = self.soundManager.createSound("Sniper-" + name, "sniper.wav", False)
        
        self.noAmmoSound = self.soundManager.createSound("empty-" + name, "verschluss.wav", False)

        for sound in [self.sounds[name] for name in self.sounds]:
            self._node.attachObject(sound)

        self.setDirection((1.0,0.0,0.0))
        self._camera = camera

        self.keys = {
            'up':OIS.KC_UNASSIGNED,
            'down':OIS.KC_UNASSIGNED,
            'downdown':OIS.KC_UNASSIGNED,
            'left':OIS.KC_UNASSIGNED,
            'right':OIS.KC_UNASSIGNED,
            'rotate-left':OIS.KC_UNASSIGNED,
            'rotate-right':OIS.KC_UNASSIGNED,
            'reload':OIS.KC_UNASSIGNED,
            'weapon1':OIS.KC_UNASSIGNED,
            'weapon2':OIS.KC_UNASSIGNED,
            'weapon3':OIS.KC_UNASSIGNED,
            'weapon4':OIS.KC_UNASSIGNED,
            'weapon5':OIS.KC_UNASSIGNED,
            'shoot':None}
        
        ogre.Animation.setDefaultInterpolationMode(ogre.Animation.IM_SPLINE)
        self.animations = {}
        self.animations['dead'] = self._entity.getAnimationState('Death1')
        self.animations['dead'].setLoop(False)
        self.animations['run'] = self._entity.getAnimationState('Stealth')
        self.animations['idle'] = self._entity.getAnimationState('Idle1')
        self.animations['crouch'] = self._entity.getAnimationState('Crouch')
        self.animations['crouch'].setLoop(False)
        self.animations['crouch'].setLength(self.animations['crouch'].getLength()/2.0)
        self.animations['jump'] = self._entity.getAnimationState('JumpNoHeight')
        self.animations['jump'].setLoop(False)

    def __del__(self):
        objects.Person.__del__(self)
        for sound in [self.sounds[name] for name in self.sounds]:
            self.audioManager.destroySound(sound)

    def _shootSound(self):
        if self.sounds[self.gunName].isPlaying():
            self.sounds[self.gunName].stop()

        self.sounds[self.gunName].play()

    def getDirection(self):
        if self._camera:
            direction = self._camera.getDirection()
            direction.z = 0.0
            direction.normalise()
            direction = (direction[0], direction[1], 0)
        else:
            direction = (1.0,0.0,0)

        if direction == (0.0,0.0,0.0):
            direction = (1.0,0.0,0)
            
        return direction

    def setDirection(self, direction):
        super(Person, self).setDirection(direction)
        if not self.isDead():
            left = ogre.Quaternion(ogre.Degree(90), ogre.Vector3.UNIT_Y)
            right = ogre.Quaternion(ogre.Degree(-90), ogre.Vector3.UNIT_Y)
            
            if direction[0] < 0.0:
                self._node.setOrientation(left)
            elif direction[0] >= 0.0:
                self._node.setOrientation(right)

    def setEvents(self, events):
        if 'shoot' in events:
            self._shootSound()

    def frameEnded(self, time):     
        if self._camera:
            camPosZ = (self._camera.getPosition()[2] + self.guns[self.gunName]['zoom'])/2
            self._camera.setPosition((self._body.getPosition()[0],self._body.getPosition()[1],camPosZ))
            self.soundManager.getListener().setPosition((self._body.getPosition()[0],self._body.getPosition()[1],camPosZ))
            
        if not self.isDead() and math.fabs(self._body.getLinearVel()[0]) > 0.1:
            if self.getDirection()[0] <= 0.0: # facing left
                self.animations['run'].addTime(time * self._body.getLinearVel()[0] * -0.3)
            else: # "right"
                self.animations['run'].addTime(time * self._body.getLinearVel()[0] * 0.3)
            self.animations['dead'].Enabled = False
            self.animations['jump'].Enabled = False
            self.animations['run'].Enabled = True
            self.animations['idle'].Enabled = False
            self.animations['crouch'].Enabled = False
            self.animations['crouch'].setTimePosition(0)
            self.animations['jump'].setTimePosition(0)
            self.animations['dead'].setTimePosition(0)
        elif self.isDead():
            self.animations['dead'].addTime(time)
            self.animations['jump'].Enabled = False
            self.animations['dead'].Enabled = True
            self.animations['run'].Enabled = False
            self.animations['idle'].Enabled = False
            self.animations['crouch'].Enabled = False
            self.animations['crouch'].setTimePosition(0)
            self.animations['jump'].setTimePosition(0)
        elif self.isCrouching:
            self.animations['crouch'].addTime(time)
            self.animations['jump'].Enabled = False
            self.animations['dead'].Enabled = False
            self.animations['run'].Enabled = False
            self.animations['idle'].Enabled = False
            self.animations['crouch'].Enabled = True
            self.animations['jump'].setTimePosition(0)
            self.animations['dead'].setTimePosition(0)
        elif self.isJumping:
            self.animations['jump'].addTime(time)
            self.animations['jump'].Enabled = True
            self.animations['dead'].Enabled = False
            self.animations['run'].Enabled = False
            self.animations['idle'].Enabled = False
            self.animations['crouch'].Enabled = True
            self.animations['crouch'].setTimePosition(0)
            self.animations['dead'].setTimePosition(0)
        else:
            self.animations['idle'].addTime(time)
            self.animations['jump'].Enabled = False
            self.animations['dead'].Enabled = False
            self.animations['run'].Enabled = False
            self.animations['idle'].Enabled = True
            self.animations['crouch'].Enabled = False
            self.animations['crouch'].setTimePosition(0)
            self.animations['jump'].setTimePosition(0)
            self.animations['dead'].setTimePosition(0)
            

        super(Person, self).frameEnded(time)
        self._updateDisplay()

    def _updateDisplay(self):
        # Todo: Exchange for attaching body to node and using transforms
        p = self._geometry.getPosition()
        o = self._nodeOffset
        self._node.setPosition(p[0]+o[0], p[1]+o[1], p[2]+o[2])

class Player(Person):
    def __init__(self, gameworld, name, camera):
        super(Player, self).__init__(gameworld, name, camera)
        
        self.keys['up'] = OIS.KC_W
        self.keys['down'] = OIS.KC_S
        # For air movement (will influence ground movement *slightly*)
        self.keys['left'] = OIS.KC_A
        self.keys['right'] = OIS.KC_D
        # For ground movement
        self.keys['rotate-left'] = OIS.KC_A
        self.keys['rotate-right'] = OIS.KC_D
        self.keys['shoot'] = OIS.MB_Left
        self.keys['reload'] = OIS.KC_R
        self.keys['weapon1'] = OIS.KC_1
        self.keys['weapon2'] = OIS.KC_2
        self.keys['weapon3'] = OIS.KC_3
        self.keys['weapon4'] = OIS.KC_4
        self.keys['weapon5'] = OIS.KC_5

    #def setPosition(self, position):
    #    Person.setPosition(self, [(x+y)/2 for x,y in zip(position, self._body.getPosition())])

    def setAttributes(self, attributes):
        Person.setAttributes(self, attributes)
        if self.isDisabled():
            self.enable()
