import math, os, time
import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as CEGUI
import ogre.sound.OgreAL as OgreAL
import ode
import ogre.io.OIS as OIS
from engine import Engine
from guiobjects import *
import objects
import networkclient
import gamenet
from encode import timer
    
class Application(object):
    debugText = ""
    
    def __init__(self):
        self.frameListener = None
        self.root = None
        self.camera = None
        self.renderWindow = None
        self.sceneManager = None
        self.world = None
        self.debug = True
        self.debugNetworkTime = 0
        self.debugChatTime = 0

    def go(self):
        "Starts the rendering loop."
        if not self._setUp():
            return
        self.root.startRendering()

    def _setUp(self):
        """This sets up the ogre application, and returns false if the user
        hits "cancel" in the dialog box."""
        self.root = ogre.Root(os.path.join(os.getcwd(), 'plugins.cfg'))
        self.root.setFrameSmoothingPeriod(5.0)

        config = ogre.ConfigFile()
        config.load('resources.cfg' ) 
        seci = config.getSectionIterator()
        while seci.hasMoreElements():
            SectionName = seci.peekNextKey()
            Section = seci.getNext()
            for item in Section:
                ogre.ResourceGroupManager.getSingleton().\
                    addResourceLocation(item.value, item.key, SectionName)
        
        if not self.root.showConfigDialog():
            return False

        self.renderWindow = self.root.initialise(True, "Assault Vector")
        
        self.sceneManager = self.root.createSceneManager(ogre.ST_GENERIC,"ExampleSMInstance")
        
        self._createWorld()
        self._createCamera()
        self._createViewports()

        ogre.TextureManager.getSingleton().setDefaultNumMipmaps(5)

        ogre.ResourceGroupManager.getSingleton().initialiseAllResourceGroups()

        self._createScene()
        self._createFrameListener()
        
        return True
        
    
class GameKeyListener(OIS.KeyListener):
    def __init__(self, game):
        OIS.KeyListener.__init__(self)
        self.game = game

    def frameEnded(self, time, keyboard):
        return True # Keep running

    def keyPressed(self, arg):
        pass
    
    def keyReleased(self, arg):
        pass

class GameJoystickListener(OIS.JoyStickListener):
    def __init__(self, game):
        self.game = game
        OIS.JoyStickListener.__init__( self)
        
    def povMoved( self, event, pov ):
        pass
        
    def axisMoved( self, event, axis ):
        pass
        
    def sliderMoved( self, event, sliderID ):
        pass
        
    def buttonPressed( self, event, button ):
        print button
        pass
        
    def buttonReleased( self, event, button ):
        pass

class GameMouseListener(OIS.MouseListener):
    def __init__(self, game):
        self.game = game
        OIS.MouseListener.__init__( self)

    def mouseMoved( self, arg ):
        pass
    
    def mousePressed(  self, arg, id ):
        pass

    def mouseReleased( self, arg, id ):
        pass

class FrameListener(ogre.FrameListener, ogre.WindowEventListener):
    def __init__(self, game, renderWindow, camera):
        ogre.FrameListener.__init__(self)
        ogre.WindowEventListener.__init__(self)
        self.game = game
        self.camera = camera
        self.renderWindow = renderWindow

        self._setupInput()

        self.keylistener = GameKeyListener(self.game)
        self.BufferedKeyboard.setEventCallback(self.keylistener)

        self.mouselistener = GameMouseListener(self.game)
        self.Mouse.setEventCallback(self.mouselistener)
        
        if self.Joy:
            self.joysticklistener = GameJoystickListener(self.game)
            self.Joy.setEventCallback(self.joysticklistener)
        
        self.lastUpdate = time.time()
        
    def __del__ (self ):
        ogre.WindowEventUtilities.removeWindowEventListener(self.renderWindow, self)
        self.windowClosed(self.renderWindow)
      
    def _setupInput(self):
        windowHnd = self.renderWindow.getCustomAttributeInt("WINDOW")
        self.InputManager = \
            OIS.createPythonInputSystem([("WINDOW",str(windowHnd))])

        #Create all devices (We only catch joystick exceptions here, as, most people have Key/Mouse)
        self.Keyboard = self.InputManager.createInputObjectKeyboard( OIS.OISKeyboard, False )
        self.BufferedKeyboard = self.InputManager.createInputObjectKeyboard( OIS.OISKeyboard, True )
        self.Mouse = self.InputManager.createInputObjectMouse( OIS.OISMouse, True )
        try :
            self.Joy = self.InputManager.createInputObjectJoyStick( OIS.OISJoyStick, True )
        except:
            self.Joy = False

        #Set initial mouse clipping size
        self.windowResized(self.renderWindow)

        #Register as a Window listener
        ogre.WindowEventUtilities.addWindowEventListener(self.renderWindow, self);
           
    def windowResized (self, rw):
        [width, height, depth, left, top] = rw.getMetrics()  # Note the wrapped function as default needs unsigned int's
        ms = self.Mouse.getMouseState()
        ms.width = width
        ms.height = height
         
    def windowClosed(self, rw):
        #Only close for window that created OIS (mWindow)
        if( rw == self.renderWindow ):
            if( self.InputManager ):
                self.InputManager.destroyInputObjectMouse( self.Mouse )
                self.InputManager.destroyInputObjectKeyboard( self.Keyboard )
                if self.Joy:
                    self.InputManager.destroyInputObjectJoyStick( self.Joy )
                OIS.InputManager.destroyInputSystem(self.InputManager)
                self.InputManager=None
            
    def frameStarted(self, frameEvent):
        if(self.renderWindow.isClosed()):
            return False
        
        ##Need to capture/update each device - this will also trigger any listeners
        self.BufferedKeyboard.capture()
        self.Keyboard.capture()
        self.Mouse.capture()
        if( self.Joy ):
            self.Joy.capture()
        return True

    def frameEnded(self, frameEvent):
        keepGoing = True
        curTime = time.time()
        frameTime = (curTime - self.lastUpdate)
        keepGoing = keepGoing and self.keylistener.frameEnded(frameTime, self.BufferedKeyboard)
        keepGoing = keepGoing and self.game.frameEnded(frameTime, self.Keyboard, self.Mouse, self.Joy)
        self.lastUpdate = curTime
        return keepGoing

class Game(Application, Engine):
    def __init__(self):
        Application.__init__(self)
    
    def _createCamera(self):
        self.camera = self.sceneManager.createCamera("Player1Cam")
##        self.camera.setProjectionType(ogre.PT_ORTHOGRAPHIC)
        self.camera.setPosition(0,0,20)
        self.camera.lookAt(0,0,0)
        self.camera.nearClipDistance = 5
    
    def _createViewports(self):
        self.viewPort = self.renderWindow.addViewport(self.camera,1)
        self.viewPort.setDimensions(0.0, 0.0, 1.0, 1.0)
        self.viewPort.setBackgroundColour((0.0, 0.0, 0.0, 1.0))
        self.camera.aspectRatio = self.viewPort.actualWidth / self.viewPort.actualHeight
        self.viewPort.setOverlaysEnabled(True)    

    def createLogo(self):
        logoa = self.sceneManager.rootSceneNode.createChildSceneNode('logo-a')
        elogoa = self.sceneManager.createEntity("m-logo-a","logo-a.mesh")
        logoa.attachObject(elogoa)
        
        logov = self.sceneManager.rootSceneNode.createChildSceneNode('logo-v')
        elogov = self.sceneManager.createEntity("m-logo-v","logo-v.mesh")
        logoa.attachObject(elogov)

        logoPos = (0, 0, 0)
        logoa.setPosition(logoPos)
        logov.setPosition(logoPos)
        
        self.logoa = logoa
        self.logov = logov

    def updateLogo(self, frameTime):
        rotateSpeed = 0.3
        self.logoa.yaw(rotateSpeed*frameTime)
        self.logov.yaw(rotateSpeed*frameTime)
    
    def _createScene(self):
        Engine._createWorld(self)
        self.sceneManager.setAmbientLight((1.0, 1.0, 1.0, 1.0))
        self.createLogo()    

    def _createFrameListener(self):
        ## note we pass ourselves as the demo to the framelistener
        self.frameListener = FrameListener(self, self.renderWindow, self.camera)
        self.keylistener = GameKeyListener(self)
        self.root.addFrameListener(self.frameListener)

    def updateGUI(self, frameTime):
        self.updateLogo(frameTime)
    
    def frameEnded(self, frameTime, keyboard,  mouse, joystick):
        self.updateGUI(frameTime)
        return True # Keep running
    
if __name__ == "__main__":
    try:
        import psyco
        psyco.full()
        print "Psyco Enabled"
    except ImportError:
        print "No Psyco Support"
        
    game = Game()
    import cProfile
    cProfile.run('game.go()', 'game-profile.txt')
    os._exit(0)
