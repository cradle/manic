from objects import *
import Ogre as ogre
import ode
import OIS

class StaticObject(StaticObject):    
    def __init__(self, gameworld, name, size = (1.0, 1.0, 1.0), scale = (0.1, 0.1, 0.1), mesh = 'crate.mesh', geomFunc = ode.GeomBox):
        StaticObject.__init__(self, gameworld, name, size, geomFunc)   

        self._entity = gameworld.sceneManager.createEntity('entity_' + name, mesh)
        self._node = gameworld.sceneManager.rootSceneNode.createChildSceneNode('node_' + name)
        self._node.attachObject(self._entity)
        
        if hasattr(size, "__getitem__"):
            self._node.setScale(scale[0]*size[0],scale[1]*size[1],scale[2]*size[2])
        else:
            self._node.setScale(scale[0]*size,scale[1]*size,scale[2]*size)

        self._updateDisplay()

    def __del__(self):
        super(StaticObject, self).__del__()
        self._gameworld.sceneManager.rootSceneNode.removeAndDestroyChild(self._name)

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


class DynamicObject(DynamicObject):
    
    def __init__(self, gameworld, name, size = (1.0,1.0,1.0), \
                 scale = (0.1, 0.1, 0.1), mesh = 'crate.mesh', geomFunc = ode.GeomBox, weight = 50):
        DynamicObject.__init__(self, gameworld, name, size, geomFunc, weight)

        self.keys = {
            'up':OIS.KC_I,
            'down':OIS.KC_K,
            'downdown':OIS.KC_Z,
            'left':OIS.KC_L,
            'right':OIS.KC_J,
            'rotate-left':OIS.KC_O,
            'rotate-right':OIS.KC_U,
            'shoot':None}

    def preStep(self, keyboard, mouse):
        super(DynamicObject, self).preStep()        
        if CEGUI.WindowManager.getSingleton().getWindow("TextWindow/Editbox1").hasInputFocus():
            return
        
        if keyboard.isKeyDown(self.keys['left']):
            self._moveLeft()
        if keyboard.isKeyDown(self.keys['right']):
            self._moveRight()
        if keyboard.isKeyDown(self.keys['rotate-left']):
            self._rotateLeft()
        if keyboard.isKeyDown(self.keys['rotate-right']):
            self._rotateRight()
        if keyboard.isKeyDown(self.keys['up']):
            self._jump()
        if keyboard.isKeyDown(self.keys['down']):
            self._crouch()
        if keyboard.isKeyDown(self.keys['downdown']):
            self._prone()
        if self.keys['shoot'] != None and mouse.getMouseState().buttonDown(self.keys['shoot']):
            self._shoot()
        
    def postStep(self):
        super(DynamicObject, self).postStep()
        self._updateDisplay()

class SphereObject(SphereObject):
    def __init__(self, gameworld, name, size = 0.5, scale = (0.01, 0.01, 0.01), \
                 mesh = 'sphere.mesh', geomFunc = ode.GeomSphere, weight = 10):
        
        SphereObject.__init__(self, gameworld, name, size, geomFunc, weight)
            
        self.keys['up'] = OIS.KC_NUMPAD8
        self.keys['down'] = OIS.KC_NUMPAD5
        self.keys['left'] = OIS.KC_NUMPAD4
        self.keys['right'] = OIS.KC_NUMPAD6
        self.keys['rotate-left'] = OIS.KC_NUMPAD7
        self.keys['rotate-right'] = OIS.KC_NUMPAD9

class BulletObject(BulletObject):
    def __init__(self, gameworld, name, position, direction):
        BulletObject.__init__(self, gameworld, name, size, scale, geomFunc = ode.GeomBox, weight = 0.01)
        
        scale = (0.01, 0.01, 0.01)
            
        self.keys['up'] = OIS.KC_UNASSIGNED
        self.keys['down'] = OIS.KC_UNASSIGNED
        self.keys['left'] = OIS.KC_UNASSIGNED
        self.keys['right'] = OIS.KC_UNASSIGNED
        self.keys['rotate-left'] = OIS.KC_UNASSIGNED
        self.keys['rotate-right'] = OIS.KC_UNASSIGNED

class Person(Person):
    def __init__(self, gameworld, name, camera = None):
        Person.__init__(self, gameworld, name, camera)
        # The scale to scale the model by
        scale = 0.01
        offset = (0.0, -1.0, 0.0)
        self._nodeOffset = offset
        
        # Entity
        self._entity = gameworld.sceneManager.createEntity('entity_' + name, 'ninja.mesh')
        # Scene -> Node
        self._node = gameworld.sceneManager.rootSceneNode.createChildSceneNode('node_' + name)
        self._node.setScale(scale*self._size[0],scale*self._size[1],scale*self._size[2])
        # Node -> Entity
        self._node.attachObject(self._entity)

        self._node.setDirection(1.0,0.0,0.0)
        self.facing = "right"
        self._camera = camera
        self._pointingDirection = (1,0,0)        

        self.keys = {
            'up':OIS.KC_UNASSIGNED,
            'down':OIS.KC_UNASSIGNED,
            'downdown':OIS.KC_UNASSIGNED,
            'left':OIS.KC_UNASSIGNED,
            'right':OIS.KC_UNASSIGNED,
            'rotate-left':OIS.KC_UNASSIGNED,
            'rotate-right':OIS.KC_UNASSIGNED,
            'shoot':None}
        
        ogre.Animation.setDefaultInterpolationMode(ogre.Animation.IM_SPLINE)
        self.animation = self._entity.getAnimationState('Walk')
        self.animation.Enabled = True


    def frameEnded(self, time):
        super(Person, self).frameEnded(time)
        left = ogre.Quaternion(ogre.Degree(90), ogre.Vector3.UNIT_Y)
        right = ogre.Quaternion(ogre.Degree(-90), ogre.Vector3.UNIT_Y)
        
        if self._camera:
            self._pointingDirection = self._camera.getDirection()
        
        if self._pointingDirection[0] <= 0.0 and \
           self._node.getOrientation().equals(right, ogre.Radian(ogre.Degree(5))): 
            self._node.setOrientation(left)
            self.facing = "left"
        elif self._pointingDirection[0] > 0.0 and \
           self._node.getOrientation().equals(left, ogre.Radian(ogre.Degree(5))): 
            self._node.setOrientation(right)
            self.facing = "right"
            
        if math.fabs(self._body.getLinearVel()[0]) > 0.1:
            if self.facing == "left":
                self.animation.addTime(time * self._body.getLinearVel()[0] * -0.3)
            else: # "right"
                self.animation.addTime(time * self._body.getLinearVel()[0] * 0.3)

    def _updateDisplay(self):
        p = self._geometry.getPosition()
        o = self._nodeOffset
        self._node.setPosition(p[0]+o[0], p[1]+o[1], p[2]+o[2])
        print self._name, self._geometry.getPosition()

class Player(Person):
    def __init__(self, gameworld, name, camera):
        Person.__init__(self, gameworld, name, camera)
        
        self.keys['up'] = OIS.KC_W
        self.keys['down'] = OIS.KC_S
        # For air movement (will influence ground movement *slightly*)
        self.keys['left'] = OIS.KC_A
        self.keys['right'] = OIS.KC_D
        # For ground movement
        self.keys['rotate-left'] = OIS.KC_A
        self.keys['rotate-right'] = OIS.KC_D
        self.keys['shoot'] = OIS.MB_Left
