import objects
import Ogre as ogre
import ode
import OIS
import CEGUI
import OgreAL
import math, random

def add(a,b):
    return a+b

#http://tomayko.com/weblog/2004/09/13/cleanest-python-find-in-list-function
def find(f, seq):
  """Return first item in sequence where f(item) == True."""
  for item in seq:
    if f(item): 
      return item

class StaticObject(objects.StaticObject):    
    def __init__(self, gameworld, name, size = (1.0, 1.0, 1.0), scale = (0.5,0.5,0.5), mesh = 'crate.mesh', geomFunc = ode.GeomBox):
        super(StaticObject, self).__init__(gameworld, name, size, geomFunc)   

        self._entity = gameworld.sceneManager.createEntity('e' + name, mesh)
        self._entity.setCastShadows(True)
        self._entity.setNormaliseNormals(True)
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
            'weapon6':OIS.KC_UNASSIGNED,
            'weapon7':OIS.KC_UNASSIGNED,
            'weapon8':OIS.KC_UNASSIGNED,
            'weapon9':OIS.KC_UNASSIGNED,
            'shoot':None,
            'secondaryFire':None,
            'previous':None,
            'next':None}

    def frameEnded(self, frameTime):
        objects.DynamicObject.frameEnded(self, frameTime)
        self._updateDisplay()

    def input(self, keyboard, mouse):
        presses = [self.getDirection(),0]
        
        if CEGUI.WindowManager.getSingleton().getWindow("TextWindow/Editbox1").hasInputFocus():
            return presses

        if keyboard.isKeyDown(self.keys['left']):
            presses[1] |= objects.LEFT
        if keyboard.isKeyDown(self.keys['right']):
            presses[1] |= objects.RIGHT
        if keyboard.isKeyDown(self.keys['rotate-left']):
            presses[1] |= objects.ROTATE_LEFT
        if keyboard.isKeyDown(self.keys['rotate-right']):
            presses[1] |= objects.ROTATE_RIGHT
        if keyboard.isKeyDown(self.keys['up']):
            presses[1] |= objects.UP
        if keyboard.isKeyDown(self.keys['down']):
            presses[1] |= objects.DOWN
        if keyboard.isKeyDown(self.keys['reload']):
            presses[1] |= objects.RELOAD
        if keyboard.isKeyDown(self.keys['downdown']):
            presses[1] |= objects.DOWNDOWN
        if keyboard.isKeyDown(self.keys['weapon1']):
            presses[1] |= objects.WEAPON1
        if keyboard.isKeyDown(self.keys['weapon2']):
            presses[1] |= objects.WEAPON2
        if keyboard.isKeyDown(self.keys['weapon3']):
            presses[1] |= objects.WEAPON3
        if keyboard.isKeyDown(self.keys['weapon4']):
            presses[1] |= objects.WEAPON4
        if keyboard.isKeyDown(self.keys['weapon5']):
            presses[1] |= objects.WEAPON5
        if keyboard.isKeyDown(self.keys['weapon6']):
            presses[1] |= objects.WEAPON6
        if keyboard.isKeyDown(self.keys['weapon7']):
            presses[1] |= objects.WEAPON7
        if keyboard.isKeyDown(self.keys['weapon8']):
            presses[1] |= objects.WEAPON8
        if keyboard.isKeyDown(self.keys['weapon9']):
            presses[1] |= objects.WEAPON9
        if self.keys['shoot'] != None and mouse.getMouseState().buttonDown(self.keys['shoot']):
            presses[1] |= objects.SHOOT
##        if self.keys['previous'] != None and mouse.getMouseState().buttonDown(self.keys['previous']):
##            presses.append("mu")
##        if self.keys['next'] != None and mouse.getMouseState().buttonDown(self.keys['next']):
##            presses.append("md")
##        if self.keys['secondaryFire'] != None and mouse.getMouseState().buttonDown(self.keys['secondaryFire']):
##            presses.append("s2")

        return presses
    
    def disable(self):
        objects.DynamicObject.disable(self)
        self._entity.setVisible(False)

    def enable(self):
        objects.DynamicObject.enable(self)
        self._entity.setVisible(True)
        
    def setPosition(self, position):
        objects.DynamicObject.setPosition(self, position)

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
        self.reset()

    def reset(self):        
        self.trail = self._gameworld.sceneManager.createRibbonTrail("bb" + self._name)
        self.trailNode = self._gameworld.sceneManager.rootSceneNode.createChildSceneNode('t' + self._name)
        self.trailNode.attachObject(self.trail)

        self.trail.setMaxChainElements(4)
        self.trail.setMaterialName('bullets')
        self.trail.setTrailLength(2.0)
                
        self._node = self._gameworld.sceneManager.rootSceneNode.createChildSceneNode('n' + self._name)
        self.trail.setColourChange(0, 0, 0, 0, 20)
        self.trail.setInitialWidth(0, 0.05)
        self.hasTrail = False

    def setPosition(self, position):
        SphereObject.setPosition(self, position)
        self.createTrail()

    def setAttributes(self, attributes):
        objects.BulletObject.setAttributes(self, attributes)
        self.createTrail()

    def createTrail(self):
        if not self.hasTrail:            
            self.hasTrail = True
            self._updateDisplay()
            self.trail.addNode(self._node)
            self._updateDisplay()

    def close(self):
        SphereObject.close(self)
        objects.BulletObject.close(self)

    def frameEnded(self, time):
        objects.BulletObject.frameEnded(self, time)
        SphereObject.frameEnded(self, time)
        
    def __del__(self):
        self._gameworld.sceneManager.destroyRibbonTrail("bb" + self._name)
        self._gameworld.sceneManager.rootSceneNode.removeAndDestroyChild('t' + self._name)
        SphereObject.__del__(self)
        objects.BulletObject.__del__(self)

    def hitObject(self, other, position):
        objects.BulletObject.hitObject(self, other, position)
        self._gameworld.sfx.play("BulletHit.wav",# % random.randint(10,10),
                                 self._body.getPosition(),
                                 maxDistance = 500,
                                 rolloffFactor = 1.5,
                                 refDistance = 5)

class ShrapnelObject(objects.ShrapnelObject, BulletObject):
    def __init__(self, gameworld, name, direction = None, velocity = None, damage = 1):
        objects.ShrapnelObject.__init__(self, gameworld, name, direction, velocity, damage)
        BulletObject.reset(self)

    def hitObject(self, other, position):
        objects.ShrapnelObject.hitObject(self, other, position)
        if other.type != objects.STATIC or self.ricochetTime <= 0:
            BulletObject.hitObject(self, other, position)
        
    def frameEnded(self, time):
        objects.ShrapnelObject.frameEnded(self, time)
        BulletObject.frameEnded(self, time)

class GrenadeObject(objects.GrenadeObject, BulletObject):
    def __init__(self, gameworld, name, direction = None, velocity = None, damage = 1):
        objects.GrenadeObject.__init__(self, gameworld, name, direction, velocity, damage)
        BulletObject.reset(self)

        self.trail.setMaxChainElements(8)
        self.trail.setTrailLength(4.0)
                
        self._node = self._gameworld.sceneManager.rootSceneNode.createChildSceneNode('g' + name)
        self.trail.setInitialColour(0, 1, 1, 0, 1)
        self.trail.setColourChange(0, 0,0,0,10)
        self.trail.setInitialWidth(0, 0.15)
        self.trail.setWidthChange(0, 0.5)

        self.light = gameworld.sceneManager.createLight("light" + name)
        self.light.setAttenuation(range = 200, constant = 0.0, linear = 0.0, quadratic = 0.01)
        self.light.setDiffuseColour ((1.0,1.0,0.5))
        self.light.setSpecularColour((0.1,0.1,0.01))
        self.light.setType(ogre.Light.LT_POINT)
        self.light.setCastShadows(True)
        self._node.attachObject(self.light)

    def frameEnded(self, time):
        objects.GrenadeObject.frameEnded(self, time)
        BulletObject.frameEnded(self, time)

    def close(self):
        self._geometry.object = None
        self.light.setVisible(False)
        BulletObject.close(self)
        objects.GrenadeObject.close(self)

    def setAttributes(self, attributes):
        objects.GrenadeObject.setAttributes(self, attributes)
        self.createTrail()
        
    def __del__(self):
        self._node.detachAllObjects()
        BulletObject.__del__(self)
        objects.GrenadeObject.__del__(self)

    def explode(self):
        objects.GrenadeObject.explode(self)
        self._gameworld.sfx.play("GrenadeLauncherExplode.wav", self._body.getPosition())

    def hitObject(self, other, position):
        objects.GrenadeObject.hitObject(self, other, position)
        if self.timeUntilArmed > 0:
            self._gameworld.sfx.play("GrenadeLauncherBounce.wav", self._body.getPosition())

class Person(objects.Person, SphereObject):
    def __init__(self, gameworld, name, camera = None):
        super(Person, self).__init__(gameworld, name, camera)

        # The scale to scale the model by
        scale = 0.01
        self.scale = scale
        offset = (0.0, -self.feetSize, 0.0)
        self._nodeOffset = offset
        
        # Entity
        self._entity = gameworld.sceneManager.createEntity('e' + name, 'ninja.mesh')
        self._entity.setMaterialName("white-ninja")
        self._entity.setNormaliseNormals(True)
        colours = [[1,0,0,1],
                   [0,1,0,1],
                   [0,0,1,1],
                   [1,1,0,1],
                   [1,0,1,1],
                   [0,1,1,1],
                   [1,1,1,1]]
        self.playerColour = random.choice(colours)
        self.swordColour = random.choice(colours)

        # Scene -> Node
        self._node = gameworld.sceneManager.rootSceneNode.createChildSceneNode('n' + name)
        self._node.setScale(scale,scale,scale)
        
        body = self._entity.getSubEntity(0).getMaterial().clone("bodyskin-" + name)
        self._entity.getSubEntity(0).setMaterialName("bodyskin-" + name)
        body.setDiffuse(self.playerColour)
        
        sword = self._entity.getSubEntity(1).getMaterial().clone("swordskin-" + name)
        self._entity.getSubEntity(1).setMaterialName("swordskin-" + name)
        sword.setDiffuse(self.swordColour)


        
##        self._entity.getSubEntity(0).getMaterial().setAmbient((1.0,0.0,0.0,0.5))
##        self._entity.getSubEntity(0).getMaterial().setSpecular((1.0,1.0,1.0,0.5))
        # Node -> Entity
        self._node.attachObject(self._entity)

        self.light = gameworld.sceneManager.createLight("light" + name)
        self.light.setType(ogre.Light.LT_POINT)
##        self.light.setSpecularColour(0.0001,0.0001,0.0001)
        self.light.setDiffuseColour(1.0, 1.0, 1.0)
        self.light.setAttenuation(range = 1000, constant = 0.0, linear = 0.0, quadratic = 0.025)
        self.light.setCastShadows(True)     
        #self._node.attachObject(self.light)

        
        self.gameworld = gameworld
        
        self.soundManager = gameworld.soundManager

        self.sounds = {}
        for gun in self.guns.keys():
            self.sounds[gun] = {}
            self.sounds[gun]['sound'] = gun + ".wav"
            self.sounds[gun]['maxDistance'] = 150
            self.sounds[gun]['rolloffFactor'] = 0.0025
            self.sounds[gun]['refDistance'] = 2

        self.sounds['Sniper']['refDistance'] = 150
        self.sounds['Sniper']['maxDistance'] = 200
        
##        self.reloadSound = self.soundManager.createSound("reload-" + name, "reload.wav", False)
##        self.noAmmoSound = self.soundManager.createSound("noammo-" + name, "noammo.wav", False)

##        for sound in [self.sounds[name] for name in self.sounds]:
##            self._node.attachObject(sound)
##
##        self._node.attachObject(self.reloadSound)
##        self._node.attachObject(self.noAmmoSound)

        self.setDirection((1.0,0.0,0.0))
        self._camera = camera
        self.zoomMode = False

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
            'weapon6':OIS.KC_UNASSIGNED,
            'weapon7':OIS.KC_UNASSIGNED,
            'weapon8':OIS.KC_UNASSIGNED,
            'weapon9':OIS.KC_UNASSIGNED,
            'shoot':None,
            'secondaryFire':None,
            'previous':None,
            'next':None}
        
        ogre.Animation.setDefaultInterpolationMode(ogre.Animation.IM_SPLINE)
        self.animations = {}
        self.animations['dead'] = self._entity.getAnimationState('Death1')
        self.animations['dead'].setLoop(False)
        self.animations['run'] = self._entity.getAnimationState('Stealth')
        self.animations['run'].setWeight(2)
        self.animations['idle'] = self._entity.getAnimationState('Idle1')
        self.animations['idle'].setWeight(0.25)
        self.animations['crouch'] = self._entity.getAnimationState('Crouch')
        self.animations['crouch'].setLoop(False)
        self.animations['crouch'].setWeight(2)
        self.animations['crouch'].setLength(self.animations['crouch'].getLength()/2.0)
        self.animations['jump'] = self._entity.getAnimationState('JumpNoHeight')
        self.animations['jump'].setLoop(False)
        self.animations['jump'].setWeight(8)

        self.events = []
        self.soundEvents = []
        self.muzzleFlash = False
        self.light.setVisible(False)
        self.muzzleFlashColour = (1.0,1.0,1.0)

    def __del__(self):
        SphereObject.__del__(self)
        objects.Person.__del__(self)

    def _hitSound(self):
        self._gameworld.sfx.play(
            "BulletHitPlayer%i.wav" % random.randint(1,4),
            self._node.getPosition(),
            maxDistance = 500,
            rolloffFactor = 1.0,
            refDistance = 5)

    def _shoot(self):
        #TODO: Make server side
        objects.Person._shoot(self)

    def _shootSound(self):
        self._gameworld.sfx.play(
            self.sounds[self.gunName]['sound'],
            self.getShootingPoint(),
            maxDistance = self.sounds[self.gunName]['maxDistance'],
            rolloffFactor = self.sounds[self.gunName]['rolloffFactor'],
            refDistance = self.sounds[self.gunName]['refDistance'])

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
        self.events = events
        for sound in ['shoot', 'hit']:
            if sound in events:
                numSounds = events.count(sound)
                t = (1.0/15.0) / (numSounds+1) # self.timeBetweenNetworkUpdates
                self.soundEvents += [{'sound':sound, 'time':t*i} for i in range(numSounds)]

    def getShootingPoint(self):
        return (self._body.getPosition()[0] + self.getShootOffset()[0] + self._pointingDirection[0],
                self._body.getPosition()[1] + self.getShootOffset()[1] + self._pointingDirection[1],
                0)

    def frameEnded(self, time):
        for sound in self.soundEvents:
            sound['time'] -= time
            if sound['time'] <= 0:
                if 'shoot' == sound['sound']:
                    self._shootSound()
                    self.light.setPosition(self.getShootingPoint())
                    self.light.setDiffuseColour(self.muzzleFlashColour)
                    self.muzzleFlash = True
                    self.light.setVisible(True)
                if 'hit' == sound['sound']:
                    self._hitSound()
                self.soundEvents.remove(sound)

        if self.muzzleFlash:
            colour = self.light.getDiffuseColour()
            if colour[0] <= 0:
                self.muzzleFlash = False
                self.light.setVisible(False)
            else:
                self.light.setDiffuseColour(colour[0]-time*20, colour[1]-time*20, colour[2]-time*20)
            
        if self.isDead():
            self.animations['dead'].addTime(time)
            self.animations['jump'].Enabled = False
            self.animations['dead'].Enabled = True
            self.animations['run'].Enabled = False
            self.animations['idle'].Enabled = False
            self.animations['crouch'].Enabled = False
            self.animations['crouch'].setTimePosition(0)
            self.animations['jump'].setTimePosition(0)
        else:
            self.animations['dead'].Enabled = False
            self.animations['dead'].setTimePosition(0)
            
            if abs(self._body.getLinearVel()[0]) > 0.1:
                modifier = 0.3
                if not self.isOnGround:
                    modifier = 0.15
                
                if self.getDirection()[0] <= 0.0: # facing left
                    self.animations['run'].addTime(time * self._body.getLinearVel()[0] * -modifier)
                else: # "right"
                    self.animations['run'].addTime(time * self._body.getLinearVel()[0] * modifier)
                self.animations['run'].Enabled = True
                self.animations['idle'].setWeight(0.1)
            else:
                self.animations['idle'].addTime(time)
                self.animations['idle'].Enabled = True
                self.animations['idle'].setWeight(2)
                
            if self.isCrouching and self.isOnGround:
                self.animations['crouch'].addTime(time)
                self.animations['crouch'].Enabled = True
            else:
                self.animations['crouch'].setTimePosition(0)
                self.animations['crouch'].Enabled = False

            if self.isJumping:
                self.animations['jump'].addTime(time*2)
                self.animations['jump'].Enabled = True
            else:
                self.animations['jump'].setTimePosition(0)
                self.animations['jump'].Enabled = False
            

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
        
        self._node.attachObject(self.soundManager.getListener())

        self.cursor = CEGUI.MouseCursor.getSingleton()
        
        self.keys['up'] = OIS.KC_W
        self.keys['down'] = OIS.KC_S
        # For air movement (will influence ground movement *slightly*)
        self.keys['left'] = OIS.KC_A
        self.keys['right'] = OIS.KC_D
        # For ground movement
        self.keys['rotate-left'] = OIS.KC_A
        self.keys['rotate-right'] = OIS.KC_D
        self.keys['shoot'] = OIS.MB_Left
        self.keys['previous'] = OIS.MB_Button3
        self.keys['next'] = OIS.MB_Button4
        self.keys['reload'] = OIS.KC_R
        self.keys['weapon1'] = OIS.KC_1
        self.keys['weapon2'] = OIS.KC_2
        self.keys['weapon3'] = OIS.KC_3
        self.keys['weapon4'] = OIS.KC_4
        self.keys['weapon5'] = OIS.KC_5
        self.keys['weapon6'] = OIS.KC_6
        self.keys['weapon7'] = OIS.KC_7
        self.keys['weapon8'] = OIS.KC_8
        self.keys['weapon9'] = OIS.KC_9
        self.keys['secondaryFire'] = OIS.MB_Right
        
        self.cursorNode = gameworld.sceneManager.getRootSceneNode().createChildSceneNode('t' + name)
        self.cursorLines = ogre.ManualObject( "__CURSOR__" + name)
        self.cursorLines.begin("cursor", ogre.RenderOperation.OT_LINE_LIST)
        self.cursorColour = (0.3,0.8,1.0,1.0)
        for i in range(12):
            self.cursorLines.position( (0,0,0) )
            self.cursorLines.colour(self.cursorColour)
        self.cursorLines.end()
        self.cursorNode.attachObject(self.cursorLines)

        self.addLists = add
        
    def setPosition(self, position):
        Person.setPosition(self, position)

    def setAttributes(self, attributes):
        Person.setAttributes(self, attributes)
        if self.isDisabled():
            self.enable()

    def secondaryFire(self):
        self.zoomMode = True

    def frameEnded(self, frameTime):        
        mouse = CEGUI.MouseCursor.getSingleton().getPosition()
        rend = CEGUI.System.getSingleton().getRenderer()
        
        if self.zoomMode:
            camPosX = CEGUI.MouseCursor.getSingleton().getPosition().d_x
            camPosY = CEGUI.MouseCursor.getSingleton().getPosition().d_y
            camPosZ = 20
        else:
            camPosX = self._body.getPosition()[0]
            camPosY = self._body.getPosition()[1]
            camPosZ = (self._camera.getPosition()[2] + self.guns[self.gunName]['zoom'])/2
            
        self._camera.setPosition((camPosX,camPosY,camPosZ))
        #self.soundManager.getListener().setPosition(self._body.getPosition())
        #self.soundManager.getListener().setDirection(self.getDirection())
        #self.soundManager.getListener().setPosition((camPosX,camPosY,camPosZ))

        
        mx = mouse.d_x / rend.getWidth()
        my = mouse.d_y / rend.getHeight()
        camray = self._camera.getCameraToViewportRay( mx, my )
    
        campt = camray.getPoint(camray.intersects(ogre.Plane(ogre.Vector3(0,0,1), 0)).second)
        campt = self.addLists(campt, (0,0,2)) # Zoom Offset
        campt = self.addLists(campt, self.getShootOffset())

        selfPos = self._geometry.getPosition()
        xd = campt[0] - selfPos[0]
        yd = campt[1] - selfPos[1]
        distance = math.sqrt(xd*xd + yd*yd)

        radius = (1-self.getAccuracy())*distance/2
        r = 0.3/(40/camPosZ)
        
        self.cursorLines.beginUpdate(0)
        # Static Crosshair
        self.cursorLines.position( self.addLists(campt, (-r,0,0) ))
        self.cursorLines.position( self.addLists(campt, (r,0,0) ))
        self.cursorLines.position( self.addLists(campt, (0,r,0) ))
        self.cursorLines.position( self.addLists(campt, (0,-r,0) ))
        # Accuracy Crosshair
        s = 0.1
        self.cursorLines.position( self.addLists(campt, (radius,radius,0) ))
        self.cursorLines.position( self.addLists(campt, (radius-s,radius-s,0) ))
        self.cursorLines.position( self.addLists(campt, (radius,-radius,0) ))
        self.cursorLines.position( self.addLists(campt, (radius-s,-radius+s,0) ))
        self.cursorLines.position( self.addLists(campt, (-radius,-radius,0) ))
        self.cursorLines.position( self.addLists(campt, (-radius+s,-radius+s,0) ))
        self.cursorLines.position( self.addLists(campt, (-radius,radius,0) ))
        self.cursorLines.position( self.addLists(campt, (-radius+s,radius-s,0) ))
        self.cursorLines.end()

        Person.frameEnded(self, frameTime)

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

class SFX(object):
    def __init__(self, soundManager):
        self.soundNum = 0
        self.soundManager = soundManager
        self.sounds = {}
        self.maxSounds = soundManager.maxSources()
        print "Maximum Sound Sources:", self.maxSounds

    def play(self, soundFile, position, refDistance = 2.0, rolloffFactor = 0.1, maxDistance = 200.0):
        # You can't change the rolloff (etc) of a sound after playing it once
        if soundFile in self.sounds:
            s = self.sounds[soundFile]
            s.stop()
            s.setPosition(position)
            s.play()
        else:
            if len(self.sounds) >= self.maxSounds: 
                sound = find(lambda s: s[1].isStopped(), self.sounds.items())
                if sound:
                    self.soundManager.destroySound(self.sounds.pop(sound[0]))
                
            if len(self.sounds) < self.maxSounds:
                s = self.soundManager.createSound("sfx%i" % self.soundNum, soundFile, False)
                self.soundNum += 1
                s.setPosition(position)
                s.setMaxDistance(maxDistance)
                s.setRolloffFactor(rolloffFactor)
                s.setReferenceDistance(refDistance)
                s.play()
                self.sounds[soundFile] = s
    
