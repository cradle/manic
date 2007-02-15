import Ogre as ogre
import OgreOde
import OIS

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

class AssaultVectorFrameListener ( FrameListener ):
    def __init__( self, demo, renderWindow, camera ):
        FrameListener.__init__(self, renderWindow, camera)
        self._demo = demo

    def frameEnded(self, evt):
        self._demo.frameEnded(evt.timeSinceLastFrame, self.Keyboard, self.Mouse)
        return FrameListener.frameEnded(self, evt)
    
class AssaultVector(Application, OgreOde.CollisionListener, OgreOde.StepListener):
    def _createScene(self):
        sceneManager = self.sceneManager
        
        ## Add some default lighting to the scene
        sceneManager.setAmbientLight( (0.25, 0.25, 0.25) )
        
        ## Give us some sky
        sceneManager.setSkyBox(True,"kk3d/DesertVII",5000,True)

        ## Position and orient the camera
        self.camera.setPosition(13,4.5,0)
        self.camera.lookAt(0,0.5,0)
        self.camera.setNearClipDistance(0.5)

        ## Create the ODE world
        self._world = OgreOde.World(sceneManager)

        self._world.setGravity( (0,-9.80665,0) )
        self._world.setCFM(0.0000010 )  # 10e-5)
        self._world.setERP(0.8)
        self._world.setAutoSleep(True)
        self._world.setAutoSleepAverageSamplesCount(10)

        entity = sceneManager.createEntity('robot', 'robot.mesh')
        sub = entity.getSubEntity(0)
        sub.materialName = 'Examples/CelShading'
        sub.setCustomParameter(CUSTOM_SHININESS, (20.0, 0.0, 0.0, 0.0))
        sub.setCustomParameter(CUSTOM_DIFFUSE, (1.0, 1.0, 0.7, 1.0))
        sub.setCustomParameter(CUSTOM_SPECULAR, (1.0, 1.0, 1.0, 1.0))
        robotNode = sceneManager.rootSceneNode.createChildSceneNode('robotNode')
        robotNode.attachObject(entity)
        robotBody = OgreOde.Body(self._world)
        robotNode.attachObject(robotBody)

        ## Create a box to jump over, the visual version
        entity = sceneManager.createEntity("Jump", "crate.mesh")
        entity.setNormaliseNormals(True)
        entity.setCastShadows(True)

        node = sceneManager.getRootSceneNode().createChildSceneNode(entity.getName())
        node.attachObject(entity)
        node.setPosition(ogre.Vector3(0,0.3,-5))
        node.setOrientation(ogre.Quaternion(ogre.Radian(0.4),ogre.Vector3(1,0,0)))
        node.setScale(0.3,0.1,0.4)

        ## Create the physical version (just static geometry, it can't move so
        ## it doesn't need a body) and keep track of it
        ei = OgreOde.EntityInformer(entity,ogre.Matrix4.getScale(node.getScale()))
        geom = ei.createSingleStaticBox(self._world, self._world.getDefaultSpace())
        entity.setUserObject(geom)

        self._stepper = OgreOde.ForwardFixedInterpolatedStepHandler(
            self._world,
            OgreOde.StepHandler.QuickStep, 
	    0.01, # Step rate
            1.0 / 60.0, # Frame rate
            1.0 / 4.0, # Max Frame rate
            1.7 # Time Scale
        )

        self._stepper.setAutomatic(OgreOde.StepHandler.AutoMode_PostFrame, self.root)

        OgreOde.CollisionListener.__init__(self)
        self._world.setCollisionListener(self)
        OgreOde.StepListener.__init__(self)
        
    def frameEnded(self, time,  input,  mouse):
        ## Tell the self.vehicle what digital inputs are being pressed left, right, power and brake
        ## There are equivalent methods for analogue controls, current you can't change gear so
        ## you can't reverse!


        ## Update the self.vehicle, you need to do this every time step
        pass


    ##------------------------------------------------------------------------------------------------
    ## Override the collision callback to set our own parameters
    def collision(self,  contact):
        
        contact.setCoulombFriction( 9999999999 ) ### OgreOde.Utility.Infinity)

        contact.setBouncyness(0.1)

        return True

    ## we need to register the framelistener
    def _createFrameListener(self):
        ## note we pass ourselves as the demo to the framelistener
        self.frameListener = AssaultVectorFrameListener(self, self.renderWindow, self.camera)
        self.root.addFrameListener(self.frameListener)

            
if __name__ == '__main__':
    av = AssaultVector()
    av.go()

