import ode, math

class GameWorld():
    def __init__(self):
        self.world = ode.World()
        self.world.setGravity((0,-9.81,0))
        self.space = ode.Space()
        self.contactgroup = ode.JointGroup()
        self.objects = []

    def go(self, steps = 1, stepSize = 0.01):
        for i in range(steps):
            self.space.collide('', self.collision_callback)
            self.world.step(stepSize)
            for object in self.objects:
                object.postStep()
                
            self.contactgroup.empty()

    def collision_callback(self, args, geom1, geom2):
        contacts = ode.collide(geom1, geom2)

        for c in contacts:
            c.setBounce(0.4)
            c.setBounceVel(15.0)
            c.setMu(100.0)
            j = ode.ContactJoint(self.world, self.contactgroup, c)
            j.attach(geom1.getBody(), geom2.getBody())

class StaticObject():
    def __init__(self, gameworld, size = (1.0, 1.0, 1.0)):
        self.geometry = ode.GeomBox(gameworld.space, size)

    def __str__(self):
        return "P=(%2.2f, %2.2f, %2.2f)" % self.geometry.getPosition()

    def postStep(self):
        pass # Todo, store in seperate list to dynamics


class DynamicObject(StaticObject):
    def __init__(self, gameworld, size = (1.0,1.0,1.0), weight = 50):
        StaticObject.__init__(self, gameworld, size)
        
        self.body = ode.Body(gameworld.world)
        mass = ode.Mass()
        mass.setBoxTotal(weight, size[0], size[1], size[2])
        self.body.setMass(mass)
        self.geometry.setBody(self.body)
        
        self.motor = ode.Plane2DJoint(gameworld.world)
        self.motor.attach(self.body, ode.environment)

    def postStep(self):
        self.alignToZAxis()
        self.motor.setXParam(ode.ParamVel, 0)
        self.motor.setYParam(ode.ParamVel, 0)

    def alignToZAxis(self):
        rot = self.body.getAngularVel()
        old_quat = self.body.getQuaternion()
        quat_len = math.sqrt( old_quat[0] * old_quat[0] + old_quat[3] * old_quat[3] )
        self.body.setQuaternion((old_quat[0] / quat_len, 0, 0, old_quat[3] / quat_len))
        self.body.setAngularVel((0,0,rot[2]))
        # http://opende.sourceforge.net/wiki/index.php/HOWTO_constrain_objects_to_2d
        
    def moveLeft(self):
        self.motor.setXParam(ode.ParamVel, -10)
        self.motor.setXParam(ode.ParamFMax, 50000)

    def __str__(self):
        return StaticObject.__str__(self) + ", LV=(%2.2f, %2.2f, %2.2f), AV=(%2.2f, %2.2f, %2.2f)" % \
               (self.body.getLinearVel() + self.body.getAngularVel())
        
def assert_equal(expected, actual):
    assert round(expected,1) == round(actual,1), "Expected %0.1f, got %0.1f" % (expected, actual)
        
class TestGame():    
    def __init__(self):
        pass

    def go(self):
        tests = [method for method in dir(self) if method.startswith('test_')]
        for test in tests:
            self.setup()
            eval(("self.%s()" % test))
            print ".",

        print
        print len(tests), 'tests run and passed'
        
    def setup(self):
        global world, static, dynamic
        world = GameWorld()
        static = StaticObject(world)
        dynamic = DynamicObject(world)
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

            if on_way_up and dynamic.body.getLinearVel()[1] < 0.0:
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
        world.go(169)
        assert_equal( 1.0, dynamic.body.getPosition()[1] )
        assert_equal( 0.0, dynamic.body.getLinearVel()[1] )

    def test_dynamic_rebounding_off_static(self):
        assert_equal( 15.0, round(self.get_maximum_rebound_height(100),0))
        assert_equal( 8.0, round(self.get_maximum_rebound_height(50),0))
        assert_equal( 4.0, round(self.get_maximum_rebound_height(20),0))
        assert_equal( 1.0, round(self.get_maximum_rebound_height(10),0))

    def test_does_not_move_on_z_axis(self):
        for i in range(200):
            world.go()
            assert_equal( 0.0, dynamic.body.getPosition()[0] )
            assert_equal( 0.0, dynamic.body.getPosition()[2] )

    def test_move_left(self):
        static = StaticObject(world, size=(100.0, 100.0, 0.0))
        dynamic.body.setPosition((0.0, 1.0, 0.0))
        dynamic.moveLeft()
    
t = TestGame()
t.go()
