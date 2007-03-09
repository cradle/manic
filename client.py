import ode, math
import Ogre as ogre
import CEGUI as CEGUI
import OIS
import os, time
from engine import Engine
from guiobjects import *
import objects
import networkclient

def cegui_reldim ( x ) :
    return CEGUI.UDim((x),0)
    
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
        self.root = ogre.Root(os.path.join(os.getcwd(), 'plugins.cfg'))
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
    
class Client(Application, Engine):
    def __init__(self):
        Application.__init__(self)
        Engine.__init__(self)
        self.chat.registerMessageListener(self.messageListener)
        address = raw_input("server ('127.0.0.1:10001') :> ")
        if address != "":
            ip, port = address.split(":")
        else:
            ip, port = "127.0.0.1", 10001
            
        self.network = networkclient.NetworkClient(ip, int(port))
        self.timeBetweenNetworkUpdates = 0.01
        self.timeUntilNextNetworkUpdate = 0.0
        self.serverRoundTripTime = 0.0
        self.lastServerUpdate = time.time()
        self.player = None
    
    def sendText(self):
        e = CEGUI.WindowManager.getSingleton().getWindow("TextWindow/Editbox1")
        self.messageListener("Me", e.getText().c_str())
        self.chat.sendMessage(e.getText().c_str())
        e.setText("")

    def messageListener(self, name, message):
        self.appendText(name + ": " + message)

    def appendText(self, text):
        st = CEGUI.WindowManager.getSingleton().getWindow("TextWindow/Static")
        currentText = st.getText()
        currentText += "\n"
        currentText += text
        st.setText(currentText)
    
    def _createCamera(self):
        self.camera = self.sceneManager.createCamera("Player1Cam")
        self.camera.setPosition(0,25,75)
        self.camera.lookAt(0,25,0)
        self.camera.nearClipDistance = 5
    
    def _createViewports(self):
        self.viewPort = self.renderWindow.addViewport(self.camera,1)
        self.viewPort.setDimensions(0.0, 0.0, 1.0, 1.0)
        self.camera.aspectRatio = self.viewPort.actualWidth / self.viewPort.actualHeight
        self.viewPort.setOverlaysEnabled(True)             

    def createStaticObject(self, size):
        return StaticObject(self, "s%s" % len(self.statics), size=size)
    
    def _createScene(self):
        Engine._createWorld(self)
        self.sceneManager.setAmbientLight((0.75, 0.75, 0.75))

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

        scores = winMgr.createWindow("TaharezLook/StaticText", "ScoreWindow")
        scores.setPosition(CEGUI.UVector2(CEGUI.UDim(0,5), CEGUI.UDim(0,5)))
        scores.setSize(CEGUI.UVector2(CEGUI.UDim(0,100), CEGUI.UDim(0,1)))
        scores.setProperty("HorzFormatting","WordWrapLefteAligned")
        scores.setProperty("VertFormatting", "TopAligned")
        self._scoreWindow = scores
        sheet.addChildWindow(scores)

        vitals = winMgr.createWindow("TaharezLook/StaticText", "VitalsWindow")
        vitals.setPosition(CEGUI.UVector2(CEGUI.UDim(0.8,0), CEGUI.UDim(0.8,0)))
        vitals.setSize(CEGUI.UVector2(CEGUI.UDim(0.2,0), CEGUI.UDim(0.2,0)))
        vitals.setProperty("HorzFormatting","WordWrapLefteAligned")
        vitals.setProperty("VertFormatting", "TopAligned")
        self._vitalsWindow = vitals
        sheet.addChildWindow(vitals)

    def displayVitals(self):
        if self.player:
            self._vitalsWindow.setText(self.player.vitals())

    def displayScores(self):
        text = ""
        scores = [[self._stats[name]["score"],name] for name in self._stats.keys()]
        scores.sort(reverse=True)
        for player in [name for score, name in scores]:
            text += " %s, %i, %.2f\n" % \
                    (player, self._stats[player]["score"], self._stats[player]["ping"])

        self._scoreWindow.setSize(CEGUI.UVector2(CEGUI.UDim(0.15,0), CEGUI.UDim(0.01 + 0.05*len(self._stats),0)))
        self._scoreWindow.setText(text)


    def _createFrameListener(self):
        ## note we pass ourselves as the demo to the framelistener
        self.frameListener = FrameListener(self, self.renderWindow, self.camera, True)
        self.keylistener = GameKeyListener(self)
        self.root.addFrameListener(self.frameListener)
        
    def frameEnded(self, frameTime, keyboard,  mouse):
        self.keyboard = keyboard
        self.mouse = mouse
        self.timeUntilNextNetworkUpdate -= frameTime
        if self.timeUntilNextNetworkUpdate <= 0.0:
            self.network.update(frameTime)

            self._stats = self.network._stats
            self.displayScores()
            self.displayVitals()
            
            while self.timeUntilNextNetworkUpdate <= 0.0:
                self.timeUntilNextNetworkUpdate += self.timeBetweenNetworkUpdates

            for message in self.network._messages:
                if message[1] > self.lastServerUpdate:
                    self.timeUntilNextNetworkUpdate = self.stepSize
                    self.lastServerUpdate = message[1]

                    for object in self.objects:
                        object.existsOnServer = False
                        
                    for serverObject in message[0]:
                        hasObject = False
                        for object in self.objects:
                            if serverObject[0] == object._name:
                                hasObject = True
                                object.setAttributes(serverObject[1])
                                object.existsOnServer = True
                        if not hasObject:
                            newObject = None
                            if serverObject[2] == True:
                                newObject = Player(self, serverObject[0], self.camera)
                                newObject.enable()
                                self.player = newObject
                            else:
                                if serverObject[3] == "Person":
                                    newObject = Person(self, serverObject[0])
                                elif serverObject[3] == "Bullet":
                                    newObject = BulletObject(self, serverObject[0])
                                elif serverObject[3] == "Dynamic":
                                    newObject = DynamicObject(self, serverObject[0])
                                elif serverObject[3] == "Sphere":
                                    newObject = SphereObject(self, serverObject[0])

                            newObject.existsOnServer = True        
                            newObject.setAttributes(serverObject[1])
                            self.objects += [newObject]

                    for object in self.objects:
                        if not object.existsOnServer:
                            #self.messageListener("Server", object._name + " timed out")
                            self.objects.remove(object)
                            del object
                        
            self.network._messages = []
            
        if self.player != None:
            self.network.send(self.player.input(self.keyboard,  self.mouse));
            
        Engine.frameEnded(self, frameTime)

    def step(self, frameTime):
        pass# TODO: Client side prediction of physics
        #Engine.step(self, frameTime)
    
if __name__ == "__main__":
    world = Client()
    world.go()
    os._exit(0)
