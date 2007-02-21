import ode, math
import Ogre as ogre
import CEGUI as CEGUI
import OIS
import gamenet
import time

def aMethod(a,b):
    print a,"=>",b
    
def cegui_reldim ( x ) :
    return CEGUI.UDim((x),0)

def getPluginPath():
    """Return the absolute path to a valid plugins.cfg file.""" 
    import sys
    import os
    import os.path
    
    paths = [os.path.join(os.getcwd(), 'plugins.cfg'),
             '/etc/OGRE/plugins.cfg',
             os.path.join(os.path.dirname(os.path.abspath(".")),
                              'plugins.cfg')]
    for path in paths:
        if os.path.exists(path):
            return path

    sys.stderr.write("\n"
        "** Warning: Unable to locate a suitable plugins.cfg file.\n"
        "** Warning: Please check your ogre installation and copy a\n"
        "** Warning: working plugins.cfg file to the current directory.\n\n")
    raise ogre.Exception(0, "can't locate the 'plugins.cfg' file", "")
    
class Application(object):
    debugText = ""
    
    def __init__(self):
        self.frameListener = None
        self.root = None
        self.camera = None
        self.renderWindow = None
        self.sceneManager = None
        self.world = None

    def go(self):
        "Starts the rendering loop."
        if not self._setUp():
            return
        if self._isPsycoEnabled():
            self._activatePsyco()
        self.root.startRendering()

    def _setUp(self):
        """This sets up the ogre application, and returns false if the user
        hits "cancel" in the dialog box."""
        self.root = ogre.Root(getPluginPath())
        self.root.setFrameSmoothingPeriod(5.0)

        self._setUpResources()
        
        if not self._configure():
            return False
        
        self._chooseSceneManager()
        self._createWorld()
        self._createCamera()
        self._createViewports()

        ogre.TextureManager.getSingleton().setDefaultNumMipmaps (5)

        self._createResourceListener()
        self._loadResources()

        self._createScene()
        self._createFrameListener()
        return True

    def _setUpResources(self):
        """This sets up Ogre's resources, which are required to be in
        resources.cfg."""
        config = ogre.ConfigFile()
        config.load('resources.cfg' ) #, '', False )
        seci = config.getSectionIterator()
        while (seci.hasMoreElements()):
            secName = seci.peekNextKey()
            settings = seci.getNext()
            ## Note that getMultiMapSettings is a Python-Ogre extension to return a multimap in a list of tuples
            settingslist = config.getMultiMapSettings ( settings )
            for typeName, archName in settingslist:
                ogre.ResourceGroupManager.getSingleton().addResourceLocation(archName, typeName, secName)
                    
    def _createResourceListener(self):
        """This method is here if you want to add a resource listener to check
        the status of resources loading."""
        pass
        
    def _createWorld ( self ):
        """ this should be overridden when supporting the OgreRefApp framework.  Also note you 
        will have to override __createCamera"""
        pass

    def _loadResources(self):
        ogre.ResourceGroupManager.getSingleton().initialiseAllResourceGroups()

    def _configure(self):
        carryOn = self.root.showConfigDialog()
            
        if carryOn:
            self.renderWindow = self.root.initialise(True, "Assault Vector")

        return carryOn

    def _chooseSceneManager(self):
        self.sceneManager = self.root.createSceneManager(ogre.ST_GENERIC,"ExampleSMInstance")

    def _isPsycoEnabled(self):
        return True

    def _activatePsyco(self):        
       try:
           import psyco
           psyco.full()
       except ImportError:
           pass
        
def convertOISMouseButtonToCegui( buttonID):
    if buttonID ==0:
        return CEGUI.LeftButton
    elif buttonID ==1:
        return CEGUI.RightButton
    elif buttonID ==2:
        return CEGUI.MiddleButton
    elif buttonID ==3:
        return CEGUI.X1Button
    else:
        return CEGUI.LeftButton
    
class GameKeyListener(OIS.KeyListener):
    def __init__(self, game):
        OIS.KeyListener.__init__(self)
        self.game = game
        self.keyToRepeat = {}
        self.timeUntilRepeat = 0.4
        self.timeBetweenRepeats = 0.03

    def frameEnded(self, time, keyboard):
        if len(self.keyToRepeat) != 0:
            key = self.keyToRepeat['key']
            self.keyToRepeat['time'] += time
            if self.keyToRepeat['mode'] == 'waiting' and \
               self.keyToRepeat['time'] > self.timeUntilRepeat:
                self.keyToRepeat['mode'] = 'repeating'
                self.keyToRepeat['time'] -= self.timeUntilRepeat
            elif self.keyToRepeat['mode'] == 'repeating':
                while self.keyToRepeat['time'] > self.timeBetweenRepeats:
                    self.keyToRepeat['time'] -= self.timeBetweenRepeats
                    CEGUI.System.getSingleton().injectKeyDown( key )
                    CEGUI.System.getSingleton().injectChar( self.keyToRepeat['text'] )

    def keyPressed(self, arg):
        self.keyToRepeat = {'mode':'waiting', 'time':0.0, 'text':arg.text, 'key':arg.key}
        CEGUI.System.getSingleton().injectKeyDown( arg.key )
        CEGUI.System.getSingleton().injectChar( arg.text )
    
    def keyReleased(self, arg):
        if len(self.keyToRepeat) != 0 and arg.key == self.keyToRepeat['key']:
            self.keyToRepeat = {}
            
        CEGUI.System.getSingleton().injectKeyUp( arg.key )

        static = CEGUI.WindowManager.getSingleton().getWindow("TextWindow/Static")
        chat = CEGUI.WindowManager.getSingleton().getWindow("TextWindow")
        editBox = CEGUI.WindowManager.getSingleton().getWindow("TextWindow/Editbox1")

        # TODO: Put more thought into HCI
        if arg.key == OIS.KC_RETURN and editBox.hasInputFocus():
            self.game.sendText()
            static.activate() # Remove focus from editbox
            chat.setEnabled(False)
            
        if arg.key == OIS.KC_T and \
           (chat.isDisabled() or (not chat.isDisabled() and not editBox.hasInputFocus())):
            chat.setEnabled(True)
            editBox.activate()
                    
        if arg.key == OIS.KC_ESCAPE and editBox.hasInputFocus():
            static.activate() # Remove focus from editbox
            chat.setEnabled(False)
                
        if arg.key == OIS.KC_F12:
            chat.setVisible(not chat.isVisible())
            chat.setEnabled(chat.isVisible())

class GameMouseListener(OIS.MouseListener):
    def __init__(self, game):
        self.game = game
        OIS.MouseListener.__init__( self)

    def mouseMoved( self, arg ):
        self.game.camera.yaw(ogre.Radian(- arg.get_state().X.rel * 0.06))
        self.game.camera.pitch(ogre.Radian(- arg.get_state().Y.rel * 0.11))
        d = self.game.camera.getDirection()
        # TODO: Make circular?
        # TODO: Swing camera on circular path away from directly in front of character?
        if d.x >= 0.35:
            d.x = 0.35
        if d.x <= -0.35:
            d.x = -0.35
        if d.y >= 0.39:
            d.y = 0.39
        if d.y <= -0.39:
            d.y = -0.39
        self.game.camera.setDirection(d)
        CEGUI.System.getSingleton().injectMousePosition( \
            ((d.x + 0.35)/(0.35*2))*arg.get_state().width, \
            ((1.0 - ((d.y + 0.39))/(0.39*2)))*arg.get_state().height )
        
        
    def mousePressed(  self, arg, id ):
        pass
        #CEGUI.System.getSingleton().injectMouseButtonDown(convertOISMouseButtonToCegui(id))

    def mouseReleased( self, arg, id ):
        pass
        #CEGUI.System.getSingleton().injectMouseButtonUp(convertOISMouseButtonToCegui(id))

class FrameListener(ogre.FrameListener, ogre.WindowEventListener):
    """A default frame listener, which takes care of basic mouse and keyboard
    input."""
    def __init__(self, game, renderWindow, camera, bufferedKeys = False, bufferedMouse = True, bufferedJoy = False):
        ogre.FrameListener.__init__(self)
        ogre.WindowEventListener.__init__(self)
        self.game = game
        self.camera = camera
        self.renderWindow = renderWindow
        self.statisticsOn = True
        self.numScreenShots = 0
        self.timeUntilNextToggle = 0
        self.sceneDetailIndex = 0
        self.moveScale = 0.0
        self.rotationScale = 0.0
        self.translateVector = ogre.Vector3(0.0,0.0,0.0)
        self.filtering = ogre.TFO_BILINEAR
        self.moveSpeed = 100.0
        self.rotationSpeed = 8.0
        self.displayCameraDetails = False
        self.bufferedKeys = bufferedKeys
        self.bufferedMouse = bufferedMouse
        self.bufferedJoy = bufferedJoy
        self.MenuMode = False   # lets understand a simple menu function

        self._setupInput()

        self.keylistener = GameKeyListener(self.game)
        self.Keyboard.setEventCallback(self.keylistener)

        self.mouselistener = GameMouseListener(self.game)
        self.Mouse.setEventCallback(self.mouselistener)
        
    def __del__ (self ):
      ogre.WindowEventUtilities.removeWindowEventListener(self.renderWindow, self)
      self.windowClosed(self.renderWindow)
      
    def _setupInput(self):
         windowHnd = self.renderWindow.getCustomAttributeInt("WINDOW")
         self.InputManager = \
             OIS.createPythonInputSystem([("WINDOW",str(windowHnd))])
         
         #Create all devices (We only catch joystick exceptions here, as, most people have Key/Mouse)
         self.Keyboard = self.InputManager.createInputObjectKeyboard( OIS.OISKeyboard, self.bufferedKeys )
         self.Mouse = self.InputManager.createInputObjectMouse( OIS.OISMouse, self.bufferedMouse )
         try :
            self.Joy = self.InputManager.createInputObjectJoyStick( OIS.OISJoyStick, bufferedJoy )
         except:
            self.Joy = False
         
         #Set initial mouse clipping size
         self.windowResized(self.renderWindow)
         
         #Register as a Window listener
         ogre.WindowEventUtilities.addWindowEventListener(self.renderWindow, self);
         
    def setMenuMode(self, mode):
        self.MenuMode = mode
        
    def _UpdateSimulation( self, frameEvent ):
        # create a real version of this to update the simulation
        pass 
           
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
        self.Keyboard.capture()    
        self.Mouse.capture()
        if( self.Joy ):
            self.Joy.capture()

        return True

    def frameEnded(self, frameEvent):
        self.keylistener.frameEnded(frameEvent.timeSinceLastFrame, self.Keyboard)
        self.game.frameEnded(frameEvent.timeSinceLastFrame, self.Keyboard, self.Mouse)
        return True
    
class GameWorld(Application):
    def __init__(self):
        Application.__init__(self)
        self.net = gamenet.NetCode("cradle", "cradle.dyndns.org", "AssaultVector", "enter")
        self.net.registerMessageListener(self.messageListener)
        self.timeBetweenNetworkUpdates = 0.1
        self.stepSize = 1.0/60.0
        self.timeUntilNextNetworkUpdate = 0.0
        self.timeUntilNextEngineUpdate = 0.0
    
    def sendText(self):
        e = CEGUI.WindowManager.getSingleton().getWindow("TextWindow/Editbox1")
        self.messageListener("Me", e.getText().c_str())
        self.net.sendMessage(e.getText().c_str())
        e.setText("")

    def appendText(self, text):
        st = CEGUI.WindowManager.getSingleton().getWindow("TextWindow/Static")
        currentText = st.getText()
        currentText += "\n"
        currentText += text
        st.setText(currentText)
    
    def _createCamera(self):
        self.camera = self.sceneManager.createCamera("Player1Cam")
        self.camera.setPosition(0,0,20)
        self.camera.lookAt(0,0.5,0)
        self.camera.nearClipDistance = 5
    
    def _createViewports(self):
        self.viewPort = self.renderWindow.addViewport(self.camera,1)
        self.viewPort.setDimensions(0.0, 0.0, 1.0, 1.0)
        self.camera.aspectRatio = self.viewPort.actualWidth / self.viewPort.actualHeight
        self.viewPort.setOverlaysEnabled(True)             
    
    def _createScene(self):
        self.sceneManager.setAmbientLight((0.75, 0.75, 0.75))
        self.world = ode.World()
        self.world.setGravity((0,-9.81,0))
        #self.world.setERP(0.2)
        #self.world.setCFM(0.0000001)
        self.space = ode.Space()
        self.contactgroup = ode.JointGroup()
        self.objects = []
  
        static = StaticObject(self, "bottom", size=(50,1,3))
        static.setPosition((0,0,0))
            
        static = StaticObject(self, "%s" % 1, size=(10,1,3))
        static.setPosition((10,5,0))
        
        static = StaticObject(self, "%s" % 2, size=(10,1,3))
        static.setPosition((-10.5,10,0))
            
        static = StaticObject(self, "%sa" % 3, size=(10,1,3))
        static.setPosition((20,7.5,0))
        static.setRotation((-0.84851580858230591,0,0,0.52916997671127319))
            
        static = StaticObject(self, "%s" % 4, size=(10,1,3))
        static.setPosition((-15,15,0))
        
        static = StaticObject(self, "%sl" % 5, size=(1,50,3))
        static.setPosition((-25,25,0))

        static = StaticObject(self, "%sr" % 6, size=(1,50,3))
        static.setPosition((25,25,0))
            
        self.player = Person(self, "p1")
        self.player.setPosition((-5.0,3.0,0.0))
        
        self.objects += [self.player]

        ## setup GUI system
        self.GUIRenderer = CEGUI.OgreCEGUIRenderer(self.renderWindow, 
            ogre.RENDER_QUEUE_OVERLAY, False, 3000, self.sceneManager) 

        self.GUIsystem = CEGUI.System(self.GUIRenderer)
        
        logger = CEGUI.Logger.getSingleton()
        logger.setLoggingLevel( CEGUI.Informative )

        winMgr = CEGUI.WindowManager.getSingleton()
        ## load scheme and set up defaults
        CEGUI.SchemeManager.getSingleton().loadScheme("TaharezLook.scheme") 
        self.GUIsystem.setDefaultMouseCursor("TaharezLook",  "MouseArrow") 
        CEGUI.FontManager.getSingleton().createFont("Commonwealth-10.font")
        background = winMgr.createWindow("TaharezLook/StaticImage", "background_wnd")
        background.setProperty("FrameEnabled", "false")
        background.setProperty("BackgroundEnabled", "false")
        ## install this as the root GUI sheet
        self.GUIsystem.setGUISheet(background)
        sheet = winMgr.createWindow("DefaultWindow", "root_wnd")
        ## attach this to the 'real' root
        background.addChildWindow(sheet)
            
        ##
        ## Build a window with some text and formatting options via radio buttons etc
        ##
        textwnd = winMgr.createWindow("TaharezLook/FrameWindow", "TextWindow")
        sheet.addChildWindow(textwnd)
        textwnd.setPosition(CEGUI.UVector2(cegui_reldim(0.2), cegui_reldim( 0.8)))
        #textwnd.setMaxSize(CEGUI.UVector2(cegui_reldim(0.4), cegui_reldim( 0.2)))
        #textwnd.setMinSize(CEGUI.UVector2(cegui_reldim(0.1), cegui_reldim( 0.1)))
        textwnd.setSize(CEGUI.UVector2(cegui_reldim(0.55), cegui_reldim( 0.2)))
        textwnd.setCloseButtonEnabled(False)
        textwnd.setText("Chat (press 't' to activate, 'Enter' to send, 'ESC' to cancel)")
        textwnd.setEnabled(False)
        
        st = winMgr.createWindow("TaharezLook/StaticText", "TextWindow/Static")
        st.setProperty("HorzFormatting","WordWrapLeftAligned")
        st.setProperty("VertFormatting", "BottomAligned")
        textwnd.addChildWindow(st)
        st.setPosition(CEGUI.UVector2(CEGUI.UDim(0.0,5.0), CEGUI.UDim(0.0,5.0)))
        st.setSize(CEGUI.UVector2(CEGUI.UDim(1.0,-10.0), CEGUI.UDim(1.0,-30.0)))
        
        ## Edit box for text entry
        eb = winMgr.createWindow("TaharezLook/Editbox", "TextWindow/Editbox1")
        textwnd.addChildWindow(eb)
        eb.setPosition(CEGUI.UVector2(cegui_reldim(0.0), CEGUI.UDim(1.0,-30.0)))
        eb.setMaxSize(CEGUI.UVector2(cegui_reldim(1.0), CEGUI.UDim(0.0,30.0)))
        eb.setSize(CEGUI.UVector2(cegui_reldim(1.0), CEGUI.UDim(0.0,30.0)))
        ## subscribe a handler to listen for when the text changes

        winMgr.getWindow("TextWindow/Editbox1").setText("")
        #eb.subscribeEvent(CEGUI.Window.EventKeyDown, self.blah,"")
            
    def messageListener(self, source, message):
        self.appendText("%s: %s" % (source, message))

    def _createFrameListener(self):
        ## note we pass ourselves as the demo to the framelistener
        self.frameListener = FrameListener(self, self.renderWindow, self.camera, True)
        self.keylistener = GameKeyListener(self)
        self.root.addFrameListener(self.frameListener)
        
    def frameEnded(self, frameTime, keyboard,  mouse):
        self.timeUntilNextNetworkUpdate -= frameTime
        if self.timeUntilNextNetworkUpdate <= 0.0:
            self.net.update()
            while self.timeUntilNextNetworkUpdate <= 0.0:
                self.timeUntilNextNetworkUpdate += self.timeBetweenNetworkUpdates

        self.timeUntilNextEngineUpdate -= frameTime
        while self.timeUntilNextEngineUpdate <= 0.0:
            self.step(keyboard)
            for object in self.objects:
                object.frameEnded(self.stepSize)
            self.timeUntilNextEngineUpdate += self.stepSize
                
        pos = self.player._geometry.getPosition()
        self.camera.setPosition(pos[0], pos[1], pos[2] + 20)

    def step(self, keyboard):
        if self.stepSize == 0.0:
            return 
    
        self.space.collide(0, self.collision_callback)
        
        for object in self.objects:
            object.preStep(keyboard)
            
        self.world.step(self.stepSize)
        
        for object in self.objects:
            object.postStep()
            
        self.contactgroup.empty()

    def collision_callback(self, args, geom1, geom2):
        contacts = ode.collide(geom1, geom2)

        for contact in contacts: #ode.ContactSoftERP + ode.ContactSoftCFM + 
            contact.setMode(ode.ContactBounce + ode.ContactApprox1_1)
            contact.setBounce(0.01)
            contact.setBounceVel(0.0)
            contact.setMu(1.7)

            body = geom1.getBody()
            if body:
                # Assume that if collision normal is facing up we are 'on ground'
                normal = contact.getContactGeomParams()[1]
                if normal[1] > 0.05: # normal.y points "up"
                    geom1.isOnGround = True
                            
            joint = ode.ContactJoint(self.world, self.contactgroup, contact)
            joint.attach(body, geom2.getBody())

class StaticObject():    
    def __init__(self, gameworld, name, size = (1.0, 1.0, 1.0), scale = (0.1, 0.1, 0.1), mesh = 'crate.mesh', geomFunc = ode.GeomBox):
        self._size = size
        self._geometry = geomFunc(gameworld.space, self._size)
        self._entity = gameworld.sceneManager.createEntity('entity_' + name, mesh)
        self._node = gameworld.sceneManager.rootSceneNode.createChildSceneNode('node_' + name)
        self._node.attachObject(self._entity)
        
        if hasattr(size, "__getitem__"):
            self._node.setScale(scale[0]*size[0],scale[1]*size[1],scale[2]*size[2])
        else:
            self._node.setScale(scale[0]*size,scale[1]*size,scale[2]*size)
            
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
    
    def __init__(self, gameworld, name, size = (1.0,1.0,1.0), \
                 scale = (0.1, 0.1, 0.1), mesh = 'crate.mesh', geomFunc = ode.GeomBox, weight = 50):
        StaticObject.__init__(self, gameworld, name, size, scale, mesh, geomFunc)

        self.keys = {
            'up':OIS.KC_I,
            'down':OIS.KC_K,
            'downdown':OIS.KC_Z,
            'left':OIS.KC_L,
            'right':OIS.KC_J,
            'rotate-left':OIS.KC_O,
            'rotate-right':OIS.KC_U}
        
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

    def preStep(self, input):
        # TODO: Move! for lack of a better home...
        # Apply wind friction
        self._body.addForce([-0.01*x*math.fabs(x)for x in self._body.getLinearVel()])

        if self._geometry.isOnGround:
            # Apply rolling friction
            self._body.addTorque([x*-2.0 for x in self._body.getAngularVel()])
        
        if CEGUI.WindowManager.getSingleton().getWindow("TextWindow/Editbox1").hasInputFocus():
            return
        
        if input.isKeyDown(self.keys['left']):
            self._moveLeft()
        elif input.isKeyDown(self.keys['right']):
            self._moveRight()
        if input.isKeyDown(self.keys['rotate-left']):
            self._rotateLeft()
        elif input.isKeyDown(self.keys['rotate-right']):
            self._rotateRight()
        if input.isKeyDown(self.keys['up']):
            self._jump()
        elif input.isKeyDown(self.keys['down']):
            self._crouch()
        elif input.isKeyDown(self.keys['downdown']):
            self._prone()

    def postStep(self):
        self._alignToZAxis()
        self._motor.setXParam(ode.ParamFMax, 0)
        self._motor.setYParam(ode.ParamFMax, 0)
        self._motor.setAngleParam(ode.ParamFMax, 0)
        self._geometry.isOnGround = False
        self._updateDisplay()

    def _alignToZAxis(self):
        rot = self._body.getAngularVel()
        old_quat = self._body.getQuaternion()
        quat_len = math.sqrt( old_quat[0] * old_quat[0] + old_quat[3] * old_quat[3] )
        self._body.setQuaternion((old_quat[0] / quat_len, 0, 0, old_quat[3] / quat_len))
        self._body.setAngularVel((0,0,rot[2]))
        # http://opende.sourceforge.net/wiki/index.php/HOWTO_constrain_objects_to_2d
        
    def _moveLeft(self):
        self._motor.setXParam(ode.ParamVel, -self.maxMoveVelocity)
        self._motor.setXParam(ode.ParamFMax, self.maxMoveForce)
        
    def _moveRight(self):
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
    
class SphereObject(DynamicObject):
    def __init__(self, gameworld, name, size = 0.5, scale = (0.01, 0.01, 0.01), \
                 mesh = 'sphere.mesh', geomFunc = ode.GeomSphere, weight = 10):
        
        DynamicObject.__init__(self, gameworld, name, size, scale, mesh, geomFunc, weight)

        if type(size) == float or type(size) == int:
            self._body.getMass().setSphereTotal(weight, size)
            
        self.keys['up'] = OIS.KC_NUMPAD8
        self.keys['down'] = OIS.KC_NUMPAD5
        self.keys['left'] = OIS.KC_NUMPAD4
        self.keys['right'] = OIS.KC_NUMPAD6
        self.keys['rotate-left'] = OIS.KC_NUMPAD7
        self.keys['rotate-right'] = OIS.KC_NUMPAD9

class Person(SphereObject):
    def __init__(self, gameworld, name, size = (0.2, 1.0, 0.5), \
                 scale = (0.01, 0.01, 0.01), offset = (0.0, -1.0, 0.0), \
                 mesh = 'ninja.mesh', geomFunc = ode.GeomSphere, weight = 70):
        self._nodeOffset = offset
        SphereObject.__init__(self, gameworld, name, 1.0, scale, mesh, geomFunc, weight)
        self._node.setDirection(1.0,0.0,0.0)
        self.facing = "right"
        self._camera = gameworld.camera

        self.timeNeededToPrepareJump = 0.1
        self.timeLeftUntilCanJump = self.timeNeededToPrepareJump
        self.wantsToJump = False
        
        self.keys['up'] = OIS.KC_W
        self.keys['down'] = OIS.KC_S
        # For air movement (will influence ground *slightly*)
        self.keys['left'] = OIS.KC_A
        self.keys['right'] = OIS.KC_D
        # For ground movement
        self.keys['rotate-left'] = OIS.KC_A
        self.keys['rotate-right'] = OIS.KC_D
        
        self.maxStopForce = 28000
        self.maxSpinForce = 28000
        self.maxSpinVelocity = 10
        self.maxMoveForce = 20
        self.maxMoveVelocity = 1
        self.maxJumpForce = ode.Infinity
        self.maxJumpVelocity = 10

        ogre.Animation.setDefaultInterpolationMode(ogre.Animation.IM_SPLINE)
        self.animation = self._entity.getAnimationState('Walk')
        self.animation.Enabled = True

    def frameEnded(self, time):
        left = ogre.Quaternion(ogre.Degree(90), ogre.Vector3.UNIT_Y)
        right = ogre.Quaternion(ogre.Degree(-90), ogre.Vector3.UNIT_Y)
        if self._camera.getDirection()[0] <= 0.0 and \
           self._node.getOrientation().equals(right, ogre.Radian(ogre.Degree(5))): 
            self._node.setOrientation(left)
            self.facing = "left"
        elif self._camera.getDirection()[0] > 0.0 and \
           self._node.getOrientation().equals(left, ogre.Radian(ogre.Degree(5))): 
            self._node.setOrientation(right)
            self.facing = "right"
            
        if math.fabs(self._body.getLinearVel()[0]) > 0.1:
            if self.facing == "left":
                self.animation.addTime(time * self._body.getLinearVel()[0] * -0.3)
            else: # "right"
                self.animation.addTime(time * self._body.getLinearVel()[0] * 0.3)

        # TODO: I hate flags!!! 
        if self.wantsToJump:
            self.timeLeftUntilCanJump -= time
        else:
            self.timeLeftUntilCanJump = self.timeNeededToPrepareJump

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

    def _updateDisplay(self):
        p = self._geometry.getPosition()
        o = self._nodeOffset
        self._node.setPosition(p[0]+o[0], p[1]+o[1], p[2]+o[2])


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

if __name__ == '__main____main__':
    world = GameWorld()
    world.go()


    
if __name__ == "__main__":
    world = GameWorld()
    world.go()
