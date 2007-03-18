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
        presses = [self.getDirection()]
        
        if CEGUI.WindowManager.getSingleton().getWindow("TextWindow/Editbox1").hasInputFocus():
            return presses

        if keyboard.isKeyDown(self.keys['left']):
            presses.append("l")
        if keyboard.isKeyDown(self.keys['right']):
            presses.append("r")
        if keyboard.isKeyDown(self.keys['rotate-left']):
            presses.append("rl")
        if keyboard.isKeyDown(self.keys['rotate-right']):
            presses.append("rr")
        if keyboard.isKeyDown(self.keys['up']):
            presses.append("u")
        if keyboard.isKeyDown(self.keys['down']):
            presses.append("d")
        if keyboard.isKeyDown(self.keys['reload']):
            presses.append("a")
        if keyboard.isKeyDown(self.keys['downdown']):
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
        if keyboard.isKeyDown(self.keys['weapon6']):
            presses.append("6")
        if keyboard.isKeyDown(self.keys['weapon7']):
            presses.append("7")
        if keyboard.isKeyDown(self.keys['weapon8']):
            presses.append("8")
        if keyboard.isKeyDown(self.keys['weapon9']):
            presses.append("9")
        if self.keys['shoot'] != None and mouse.getMouseState().buttonDown(self.keys['shoot']):
            presses.append("s")
        if self.keys['previous'] != None and mouse.getMouseState().buttonDown(self.keys['previous']):
            presses.append("mu")
        if self.keys['next'] != None and mouse.getMouseState().buttonDown(self.keys['next']):
            presses.append("md")
        if self.keys['secondaryFire'] != None and mouse.getMouseState().buttonDown(self.keys['secondaryFire']):
            presses.append("s2")
        if self.keys['next'] != None and mouse.getMouseState().buttonDown(self.keys['next']):
            presses.append("md")

        self.presses = presses
        return presses
    
    def disable(self):
        objects.DynamicObject.disable(self)
        self._entity.setVisible(False)

    def enable(self):
        objects.DynamicObject.enable(self)
        self._entity.setVisible(True)
        
    def setPosition(self, position):
        #curPos = self._body.getPosition()
        #curVel = self._body.getLinearVel()
        #if position and \
        #   (math.fabs(position[0] - curPos[0]) > math.fabs(curVel[0]) or \
        #    math.fabs(position[1] - curPos[1]) > math.fabs(curVel[1])):
            #position = [(x+y)/2 for x,y in zip(position, curPos)]
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
            'shoot':None,
            'secondaryFire':None,
            'previous':None,
            'next':None}
        
        self.name = name
        self._entity = gameworld.sceneManager.createBillboardSet("bb" + name)
        self._entity.setDefaultDimensions(0.05,0.05)

        self._entity.createBillboard(0,0,0)
        
        self.trailNode = gameworld.sceneManager.getRootSceneNode().createChildSceneNode('t' + name)
        self.trail = ogre.ManualObject( "__TRAIL__" + name)
        self.trailNode.attachObject(self.trail)
                
        self._node = gameworld.sceneManager.rootSceneNode.createChildSceneNode('n' + name)
        self._node.attachObject(self._entity)

        self._updateDisplay()

        self.gameworld = gameworld

    def frameEnded(self, time):
        objects.BulletObject.frameEnded(self, time)
        SphereObject.frameEnded(self, time)
        
        self.trail.clear()
        self.trailNode.detachAllObjects()
        self.trail.begin("bullets", ogre.RenderOperation.OT_LINE_LIST)
        self.trail.position( self._body.getPosition() )
        self.trail.colour(1.0,1.0,1.0,0.5)
        self.trail.position(\
            [a-(b*2*time) for a,b in zip(self._body.getPosition(), self._body.getLinearVel())])
        self.trail.colour(1.0,1.0,1.0,0.0)
        self.trail.end()
        self.trailNode.attachObject(self.trail)
        
    def __del__(self):
        self.gameworld.sceneManager.destroyBillboardSet("bb" + self.name)
        self.trailNode.detachAllObjects()
        self.trail.clear()
        self.gameworld.sceneManager.rootSceneNode.removeAndDestroyChild('t' + self.name)
        SphereObject.__del__(self)
        objects.BulletObject.__del__(self)

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
        self.gameworld = gameworld
        
        self.soundManager = gameworld.soundManager

        self.sounds = {}
        for gun in self.guns.keys():
            self.sounds[gun] = self.soundManager.createSound(gun + "-" + name, gun + ".wav", False)
        
        self.reloadSound = self.soundManager.createSound("reload-" + name, "reload.wav", False)
        self.noAmmoSound = self.soundManager.createSound("noammo-" + name, "noammo.wav", False)

        for sound in [self.sounds[name] for name in self.sounds]:
            self._node.attachObject(sound)

        self._node.attachObject(self.reloadSound)
        self._node.attachObject(self.noAmmoSound)

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
        self.animations['jump'].setWeight(4)

        self.events = []

    def __del__(self):
        SphereObject.__del__(self)
        objects.Person.__del__(self)
        for sound in [self.sounds[name] for name in self.sounds]:
            self.soundManager.destroySound(sound)

    def _shoot(self):
        #TODO: Make server side
        if self.ammo == 0:
            self.noAmmoSound.play()
        objects.Person._shoot(self)

    def _shootSound(self):
        self.noAmmoSound.stop()
        if self.sounds[self.gunName].isPlaying():
            self.sounds[self.gunName].stop()

        self.sounds[self.gunName].play()

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
        if 'shoot' in self.events:
            #TODO: Space out sounds between updates
            self.events.remove('shoot')
            self._shootSound()

    def frameEnded(self, time):
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
            
            if math.fabs(self._body.getLinearVel()[0]) > 0.1:
                modifier = 0.3
                if not self.isOnGround:
                    modifier = 0.15
                
                if self.getDirection()[0] <= 0.0: # facing left
                    self.animations['run'].addTime(time * self._body.getLinearVel()[0] * -modifier)
                else: # "right"
                    self.animations['run'].addTime(time * self._body.getLinearVel()[0] * modifier)
                self.animations['run'].Enabled = True
                self.animations['idle'].setWeight(0.5)
            else:
                self.animations['idle'].addTime(time)
                self.animations['idle'].Enabled = True
                self.animations['idle'].setWeight(2)
                
            if self.isCrouching and self.isOnGround:
                self.animations['crouch'].addTime(time)
                self.animations['crouch'].Enabled = True
                self.animations['jump'].setTimePosition(0)
            else:
                self.animations['crouch'].setTimePosition(0)
                self.animations['crouch'].Enabled = False

            if self.isJumping:
                self.animations['jump'].addTime(time)
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
        self.cursorNode.attachObject(self.cursorLines)
        
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
        self.soundManager.getListener().setPosition((camPosX,camPosY,camPosZ))

        
        mx = mouse.d_x / rend.getWidth()
        my = mouse.d_y / rend.getHeight()
        camray = self._camera.getCameraToViewportRay( mx, my )
    
        campt = camray.getPoint(camray.intersects(ogre.Plane(ogre.Vector3(0,0,1), 0)).second)
        campt = self.addLists(campt, (0,0,2)) # Zoom Offset
        campt = self.addLists(campt, self.getShootOffset())
        self.cursorLines.clear()
        self.cursorLines.begin("Red", ogre.RenderOperation.OT_LINE_LIST)

        selfPos = self._geometry.getPosition()
        xd = campt[0] - selfPos[0]
        yd = campt[1] - selfPos[1]
        distance = math.sqrt(xd*xd + yd*yd)

        radius = (1-self.getAccuracy())*distance/2
        r = 0.3/(40/camPosZ)
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

    def addLists(self, a, b):
        return [a+b for a,b in zip(a,b)]

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
