import Ogre as ogre
import ode

# Custom parameter bindings
#TODO: Refactor
CUSTOM_SHININESS = 1
CUSTOM_DIFFUSE = 2
CUSTOM_SPECULAR = 3

ogre.OgreVersion = ogre.GetOgreVersion()
if (ogre.OgreVersion[0]+ ogre.OgreVersion[1]) == "12":
    from Ogre.sf import *
else: 
    from Ogre.sf_OIS import *

# Collision callback
def collision_callback(args, geom1, geom2):
    """Callback function for the collide() method.

    This function checks if the given geoms do collide and
    creates contact joints if they do.
    """

    # Check if the objects do collide
    contacts = ode.collide(geom1, geom2)

    # Create contact joints
    world,contactgroup = args
    for c in contacts:
        c.setBounce(0.1)
        c.setBounceVel(10.0)
        c.setMu(100.0)
        j = ode.ContactJoint(world, contactgroup, c)
        j.attach(geom1.getBody(), geom2.getBody())

class AssaultVectorFrameListener ( FrameListener ):
    def __init__( self, demo, renderWindow, camera ):
        FrameListener.__init__(self, renderWindow, camera)
        self._demo = demo

    def frameEnded(self, evt):
        self._demo.frameEnded(evt.timeSinceLastFrame, self.Keyboard, self.Mouse)
        return FrameListener.frameEnded(self, evt)
    
class AssaultVector(Application):
    def _createScene(self):
        sceneManager = self.sceneManager
      
        ## Add some default lighting to the scene
        sceneManager.setAmbientLight( (0.25, 0.25, 0.25) )

        ## Position and orient the camera
        self.camera.setPosition(0,0,100)
        self.camera.lookAt(0,0,0)
        self.camera.setNearClipDistance(0.5)

        ## Create the ODE world
        self._world = ode.World()

        self._world.setGravity( (0,-9.80665,0) )
        self._world.setCFM(0.0000010 )  # 10e-5)
        self._world.setERP(0.8)

        space = ode.Space()

        floorShape = (1000.0,1.0,3.0)
        floor = ode.GeomBox(space, floorShape)
        floor.setPosition((-50,-1,0))

        floorEntity = sceneManager.createEntity("Floor", "crate.mesh")
        floorNode = sceneManager.rootSceneNode.createChildSceneNode('floorNode',ogre.Vector3.ZERO)
        floorNode.attachObject(floorEntity)
        floorNode.setScale(floorShape)
        floorNode.setPosition((-50,-1,0))


        ## Load up our UI and display it
        pOver = ogre.OverlayManager.getSingleton().getByName("OgreOdeDemos/Overlay")    
        pOver.show()

        entity = sceneManager.createEntity('robot', 'robot.mesh')
        sub = entity.getSubEntity(0)
        robotNode = sceneManager.rootSceneNode.createChildSceneNode('robotNode')
        robotNode.attachObject(entity)
        robotBody = ode.Body(self._world)
        robotBody.setPosition((0,10,0))
        M = ode.Mass()
        M.setBox(2000, 1,1,1)
        robotBody.setMass(M)
        robotGeometry = ode.GeomBox(space, (1,1,1))
        robotGeometry.setBody(robotBody)
        robotNode.setPosition(robotBody.getPosition())
        robotNode.setScale((0.05,0.05,0.05))
        self.robotNode = robotNode
        self.robotBody = robotBody
        self.world = self._world
        self.space = space
        self.contactgroup = ode.JointGroup()
  
    def frameEnded(self, time,  input,  mouse):
        ## Tell the self.vehicle what digital inputs are being pressed left, right, power and brake
        ## There are equivalent methods for analogue controls, current you can't change gear so
        ## you can't reverse!
        self.robotNode.setPosition(self.robotBody.getPosition())

        
        # Detect collisions and create contact joints
        self.space.collide((self.world,self.contactgroup), collision_callback)

        # Simulation step
        if time != 0.0:
            self.world.step(time)

        if input.isKeyDown(OIS.KC_H):
            self.robotBody.addForce((-50000,0,0))

        print "t=%2.4f v=(%2.2f,%2.2f)" % (time, self.robotBody.getLinearVel()[0], self.robotBody.getLinearVel()[1])

        # Remove all contact joints
        self.contactgroup.empty()

        self.robotBody.setLinearVel((self.robotBody.getLinearVel()[0],self.robotBody.getLinearVel()[1],0))
        self.robotBody.setAngularVel((0,0,self.robotBody.getAngularVel()[2]))



    ## we need to register the framelistener
    def _createFrameListener(self):
        ## note we pass ourselves as the demo to the framelistener
        self.frameListener = AssaultVectorFrameListener(self, self.renderWindow, self.camera)
        self.root.addFrameListener(self.frameListener)

      
if __name__ == '__main__':
    av = AssaultVector()
    av.go()
