import ode, math
import Ogre as ogre
import OIS

ogre.OgreVersion = ogre.GetOgreVersion()
if (ogre.OgreVersion[0]+ ogre.OgreVersion[1]) == "12":
    from Ogre.sf import *
else: 
    from Ogre.sf_OIS import *

class GameFrameListener ( FrameListener ):
    def __init__( self, game, renderWindow, camera ):
        FrameListener.__init__(self, renderWindow, camera)
        self.game = game

    def frameEnded(self, evt):
        self.game.frameEnded(evt.timeSinceLastFrame, self.Keyboard, self.Mouse)
        return FrameListener.frameEnded(self, evt)
    
class GameWorld(Application):        
    def _createScene(self):
        self.sceneManager.setAmbientLight((0.25, 0.25, 0.25))
        self.camera.setPosition(0,0,20)
        self.camera.lookAt(0,0.5,0)
        self.camera.setNearClipDistance(0.5)
        self.world = ode.World()
        self.world.setGravity((0,-9.81,0))
        self.space = ode.Space()
        self.contactgroup = ode.JointGroup()
        self.objects = []
  
        static = StaticObject(self, "bottom", size=(50,1,1))
        static.setPosition((0,0,0))
            
        static = StaticObject(self, "%s" % 1, size=(10,1,1))
        static.setPosition((10,5,0))
        
        static = StaticObject(self, "%s" % 2, size=(10,1,1))
        static.setPosition((-10.5,10,0))
            
        static = StaticObject(self, "%sa" % 3, size=(10,1,1))
        static.setPosition((20,7.5,0))
        static.setRotation((-0.84851580858230591,0,0,0.52916997671127319))
            
        static = StaticObject(self, "%s" % 4, size=(10,1,1))
        static.setPosition((-15,15,0))
        
        static = StaticObject(self, "%sl" % 5, size=(1,50,1))
        static.setPosition((-25,25,0))

        static = StaticObject(self, "%sr" % 6, size=(1,50,1))
        static.setPosition((25,25,0))
            
        dynamic = DynamicObject(self, "d")
        dynamic.setPosition((0.0,3.0,0.0))
        
        self.objects += [dynamic]
        self.player = dynamic
        
    def _createFrameListener(self):
        ## note we pass ourselves as the demo to the framelistener
        self.frameListener = GameFrameListener(self, self.renderWindow, self.camera)
        self.root.addFrameListener(self.frameListener)
        
    def frameEnded(self, time, keyboard,  mouse):
        self.step(keyboard, 1, time)
        pos = self.player._geometry.getPosition()
        self.camera.setPosition(pos[0], pos[1], pos[2] + 20)

        return not keyboard.isKeyDown(OIS.KC_ESCAPE)

    def step(self, keyboard, steps = 1, stepSize = 0.01):
        if stepSize == 0.0:
            return 
    
        for i in range(steps):
            self.space.collide(0, self.collision_callback)
            
            for object in self.objects:
                object.preStep(keyboard)
                
            self.world.step(stepSize)
            
            for object in self.objects:
                object.postStep()
                
            self.contactgroup.empty()

    def collision_callback(self, args, geom1, geom2):
        contacts = ode.collide(geom1, geom2)

        for contact in contacts:
            contact.setMode(ode.ContactSoftERP + ode.ContactSoftCFM + ode.ContactBounce)
            contact.setBounce(0.20)
            contact.setBounceVel(10.0)
            contact.setMu(9200.0)
            contact.setSoftERP(0.3)
            contact.setSoftCFM(0.0000125)
                            
            joint = ode.ContactJoint(self.world, self.contactgroup, contact)
            joint.attach(geom1.getBody(), geom2.getBody())

class StaticObject():
    def __init__(self, gameworld, name, size = (1.0, 1.0, 1.0)):
        self._size = size
        self._geometry = ode.GeomBox(gameworld.space, self._size)
        entity = gameworld.sceneManager.createEntity('static' + name, 'crate.mesh')
        self._node = gameworld.sceneManager.rootSceneNode.createChildSceneNode('staticNode' + name)
        self._node.attachObject(entity)
        self._node.setScale(0.1*size[0],0.1*size[1],0.1*size[2])
        self._updateDisplay()

    def __str__(self):
        return "P=(%2.2f, %2.2f, %2.2f)" % self._geometry.getPosition()

    def setPosition(self, position):
        self._geometry.setPosition(position)
        self._updateDisplay()

    def setRotation(self, quaternion):
        self._geometry.setQuaternion(quaternion)
        self._updateDisplay()

    def _updateDisplay(self):
        self._node.setPosition(self._geometry.getPosition())
        self._node.setOrientation(self._geometry.getQuaternion()[0],\
                                 self._geometry.getQuaternion()[1],\
                                 self._geometry.getQuaternion()[2],\
                                 self._geometry.getQuaternion()[3])


class DynamicObject(StaticObject):
    maxMoveForce = 600
    maxMoveVelocity = 10
    maxSpinForce = 700
    maxSpinVelocity = 15
    
    def __init__(self, gameworld, name, size = (1.0,1.0,1.0), weight = 50):
        StaticObject.__init__(self, gameworld, name, size)
        
        self._body = ode.Body(gameworld.world)
        mass = ode.Mass()
        mass.setBoxTotal(weight, size[0], size[1], size[2])
        self._body.setMass(mass)
        self._geometry.setBody(self._body)
        
        self._motor = ode.Plane2DJoint(gameworld.world)
        self._motor.attach(self._body, ode.environment)

    def preStep(self, input):
        if input.isKeyDown(OIS.KC_J):
            self._moveLeft()
        if input.isKeyDown(OIS.KC_L):
            self._moveRight()
        if input.isKeyDown(OIS.KC_U):
            self._rotateLeft()
        if input.isKeyDown(OIS.KC_O):
            self._rotateRight()
        if input.isKeyDown(OIS.KC_I):
            self._jump()

    def postStep(self):
        self._alignToZAxis()
        self._motor.setXParam(ode.ParamFMax, 0)
        self._motor.setYParam(ode.ParamFMax, 0)
        self._motor.setAngleParam(ode.ParamFMax, 0)
        self._updateDisplay()

    def _alignToZAxis(self):
        rot = self._body.getAngularVel()
        old_quat = self._body.getQuaternion()
        quat_len = math.sqrt( old_quat[0] * old_quat[0] + old_quat[3] * old_quat[3] )
        self._body.setQuaternion((old_quat[0] / quat_len, 0, 0, old_quat[3] / quat_len))
        self._body.setAngularVel((0,0,rot[2]))
        # http://opende.sourceforge.net/wiki/index.php/HOWTO_constrain_objects_to_2d
        
    def _moveLeft(self):
        self._motor.setXParam(ode.ParamVel, -DynamicObject.maxMoveVelocity)
        self._motor.setXParam(ode.ParamFMax, DynamicObject.maxMoveForce)
        
    def _moveRight(self):
        self._motor.setXParam(ode.ParamVel,  DynamicObject.maxMoveVelocity)
        self._motor.setXParam(ode.ParamFMax, DynamicObject.maxMoveForce)

    def _rotateLeft(self):
        self._motor.setAngleParam(ode.ParamVel,  DynamicObject.maxSpinVelocity)
        self._motor.setAngleParam(ode.ParamFMax, DynamicObject.maxSpinForce)

    def _rotateRight(self):
        self._motor.setAngleParam(ode.ParamVel,  -DynamicObject.maxSpinVelocity)
        self._motor.setAngleParam(ode.ParamFMax, DynamicObject.maxSpinForce)
        
    def _jump(self):
        self._motor.setYParam(ode.ParamVel,  DynamicObject.maxMoveVelocity)
        self._motor.setYParam(ode.ParamFMax, DynamicObject.maxMoveForce)

    def __str__(self):
        return StaticObject.__str__(self) + ", LV=(%2.2f, %2.2f, %2.2f), AV=(%2.2f, %2.2f, %2.2f)" % \
               (self._body.getLinearVel() + self._body.getAngularVel())
    

def assert_equal(expected, actual):
    assert round(expected,1) == round(actual,1), "Expected %0.1f, got %0.1f" % (expected, actual)
        
class TestGame():    
    def __init__(self):
        pass

    def go(self):
        tests = [method for method in dir(self) if method.startswith('test_')]
        for test in tests:
            print "Running", test
            self.setup()
            eval(("self.%s()" % test))
            print ".",

        print
        print len(tests), 'tests run and passed'
        
    def setup(self):
        global world, static, dynamic
        world = GameWorld()
        static = StaticObject(world, "s")
        dynamic = DynamicObject(world, "d")
        dynamic.geometry.setPosition((0.0,10.0,0.0))
        world.objects += [static]
        world.objects += [dynamic]

    def get_maximum_rebound_height(self, initial_height):
        dynamic.geometry.setPosition((0.0,initial_height,0.0))
        on_way_down_second_time = False
        on_way_up = False
        while not on_way_down_second_time:
            if dynamic.body.getLinearVel()[1] > 0.0:
                on_way_up = True

            if on_way_up and dynamic.body.getLinearVel()[1] <= 0.0:
                on_way_down_second_time = True

            world.go()
            
        return dynamic.body.getPosition()[1]

    def test_one_second_static_object_doesnt_move(self):
        world.go(169)
        assert_equal( 0.0, static.geometry.getPosition()[1] )
            
    def test_one_second_fall_dynamic_object_falls_with_gravity(self):
        world.go(100)
        assert_equal( 5.0, dynamic.body.getPosition()[1] )
        assert_equal( -9.8, dynamic.body.getLinearVel()[1] )

    def test_dynamic_hitting_static(self):
        world.go(200)
        assert_equal( 0.0, dynamic.body.getLinearVel()[1] )
        assert_equal( 1.0, dynamic.body.getPosition()[1] )

    def test_dynamic_rebounding_off_static_100(self):
        assert_equal( 4.0, round(self.get_maximum_rebound_height(100),0))

    def test_dynamic_rebounding_off_static_50(self):
        assert_equal( 3.0, round(self.get_maximum_rebound_height(50),0))

    def test_dynamic_rebounding_off_static_20(self):
        assert_equal( 2.0, round(self.get_maximum_rebound_height(20),0))

    def test_dynamic_rebounding_off_static_10(self):
        assert_equal( 1.0, round(self.get_maximum_rebound_height(10),0))

    def test_does_not_move_on_z_axis(self):
        static = StaticObject(world, size=(1000.0, 1.0, 1.0))
        for i in range(200):
            dynamic.moveRight()
            world.go()
            assert_equal( 0.0, dynamic.body.getPosition()[2] )

    def test_move_left(self):
        static = StaticObject(world, size=(100.0, 100.0, 0.0))
        #dynamic.body.setPosition((0.0, 1.0, 0.0))
        for i in range(100):
            dynamic.moveLeft()
            world.go()
            
        assert_equal( -10.0, round(dynamic.body.getPosition()[0],0))

    def test_move_right(self):
        static = StaticObject(world, size=(1000.0, 1.0, 1.0))
        #dynamic.body.setPosition((0.0, 1.0, 0.0))
        for i in range(100):
            dynamic.moveRight()
            world.go()
            
        assert_equal( 10.0, round(dynamic.body.getPosition()[0],0))

    def test_slide_after_move(self):
        static = StaticObject(world, size=(1000.0, 1.0, 1.0))
        #dynamic.body.setPosition((0.0, 1.0, 0.0))
        i = 0
        for i in range(100):
            dynamic.moveRight()
            world.go()
            
        while (round(dynamic.body.getLinearVel()[1],2), \
               round(dynamic.body.getLinearVel()[2],2), \
               round(dynamic.body.getLinearVel()[0],2)) != (0,0,0):
            world.go()
        
        assert_equal( 0.0, round(dynamic.body.getPosition()[2],4))
        assert_equal( 1.0, round(dynamic.body.getPosition()[1],0))
        assert_equal( 15.0, round(dynamic.body.getPosition()[0],0))

if __name__ == '__test__':
    t = TestGame()
    t.go()

if __name__ == '__main__':
    world = GameWorld()
    world.go()
