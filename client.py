import ode, math, os, time
import Ogre as ogre
import CEGUI as CEGUI
import OgreAL
import OgreOde
import OIS
from engine import Engine
from guiobjects import *
import objects
import networkclient
import gamenet
from encode import timer

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
        self.debugNetworkTime = 0
        self.debugChatTime = 0

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
        config.load('resources.cfg' ) 
        seci = config.getSectionIterator()
        while seci.hasMoreElements():
            SectionName = seci.peekNextKey()
            Section = seci.getNext()
            for item in Section:
                ogre.ResourceGroupManager.getSingleton().\
                    addResourceLocation(item.value, item.key, SectionName)
                
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
        return False

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
        self.chatAlpha = 0.3
        self.chatPosition = CEGUI.UDim(0.8, 0)

    def frameEnded(self, time, keyboard):
        chat = CEGUI.WindowManager.getSingleton().getWindow("TextWindow")
        # TODO: Moderate speed of effects with time
        chat.setAlpha((chat.getAlpha()*3 + self.chatAlpha)/4)
        chat.setYPosition((chat.getYPosition()*CEGUI.UDim(3, 0) + self.chatPosition)*CEGUI.UDim(0.25, 0))
        
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
        return True # Keep running

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

        if arg.key == OIS.KC_RETURN and editBox.hasInputFocus():
            self.game.sendText()
            editBox.deactivate() # Remove focus from editbox
            chat.disable()
            self.chatAlpha = 0.3
            
        if arg.key == OIS.KC_T and \
           (chat.isDisabled() or (not chat.isDisabled() and not editBox.hasInputFocus())):
            chat.enable()
            self.chatAlpha = 0.9
            self.chatPosition = CEGUI.UDim(0.8, 0)
            if editBox.getText().c_str().startswith("team:"):
                editBox.setText(editBox.getText().c_str()[5:])
                editBox.setCaratIndex(editBox.getCaratIndex() - 5)
            editBox.activate()
            
        if arg.key == OIS.KC_Y and \
           (chat.isDisabled() or (not chat.isDisabled() and not editBox.hasInputFocus())):
            chat.enable()
            self.chatAlpha = 0.9
            self.chatPosition = CEGUI.UDim(0.8, 0)
            if not editBox.getText().c_str().startswith("team:"):
                editBox.setText("team:" + editBox.getText().c_str())
                editBox.setCaratIndex(editBox.getCaratIndex() + 5)
            editBox.activate()
                    
        if arg.key == OIS.KC_ESCAPE and editBox.hasInputFocus():
            editBox.deactivate()
            chat.disable()
            self.chatAlpha = 0.3
                
        if arg.key == OIS.KC_F12:
            if self.chatPosition == CEGUI.UDim(0.8, 0):
                self.chatPosition = CEGUI.UDim(1.0, 0)
                editBox.deactivate()
            else:
                self.chatPosition = CEGUI.UDim(0.8, 0)
                
            chat.disable()
            self.chatAlpha = 0.3

class GameMouseListener(OIS.MouseListener):
    def __init__(self, game):
        self.game = game
        OIS.MouseListener.__init__( self)

    def mouseMoved( self, arg ):
        self.game.camera.yaw(ogre.Radian(- arg.get_state().X.rel * 0.06))
        self.game.camera.pitch(ogre.Radian(- arg.get_state().Y.rel * 0.11))
        d = self.game.camera.getDirection()
        # TODO: Swing camera on circular path away from directly in front of character?
        maxMouseLook = 0.39
        angle = 0
        
        if d.x != 0.0:
            angle = math.atan2(d.y,d.x)
            
        maxY = math.sin(angle)*maxMouseLook
        maxX = math.cos(angle)*maxMouseLook
        
        if math.fabs(d.x) >= math.fabs(maxX):
            d.x = maxX
        if math.fabs(d.y) >= math.fabs(maxY):
            d.y = maxY
            
        self.game.camera.setDirection(d)
        CEGUI.System.getSingleton().injectMousePosition( \
            ((d.x + maxMouseLook)/(maxMouseLook*2))*arg.get_state().width, \
            ((1.0 - ((d.y + maxMouseLook))/(maxMouseLook*2)))*arg.get_state().height )
        
        
    def mousePressed(  self, arg, id ):
        pass
        #CEGUI.System.getSingleton().injectMouseButtonDown(convertOISMouseButtonToCegui(id))

    def mouseReleased( self, arg, id ):
        pass
        #CEGUI.System.getSingleton().injectMouseButtonUp(convertOISMouseButtonToCegui(id))

class FrameListener(ogre.FrameListener, ogre.WindowEventListener):
    """A default frame listener, which takes care of basic mouse and keyboard
    input."""
    def __init__(self, game, renderWindow, camera):
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
        self.MenuMode = False   # lets understand a simple menu function

        self._setupInput()

        self.keylistener = GameKeyListener(self.game)
        self.BufferedKeyboard.setEventCallback(self.keylistener)

        self.mouselistener = GameMouseListener(self.game)
        self.Mouse.setEventCallback(self.mouselistener)
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
        keepGoing = keepGoing and self.game.frameEnded(frameTime, self.Keyboard, self.Mouse)
        self.lastUpdate = curTime
        return keepGoing
            

class Client(Application, Engine):
    def __init__(self, autoConnect = False):
        Application.__init__(self)
        Engine.__init__(self)
        ip, port = "cradle.dyndns.org", "10001"

        if not autoConnect:
            address = raw_input("server ('cradle.dyndns.org:10001') :> ")
            
            if address != "":
                split = address.split(":")
                ip = split[0]
                if len(split) == 2:
                    port = split[1]

        self.chat = gamenet.NetCode("cradle", "cradle.dyndns.org", "AV", "enter", "-".join([ip, port]))
        self.chat.registerMessageListener(self.messageListener)
        self.timeBetweenChatUpdates = 0.5
        self.timeUntilNextChatUpdate = 0.0            
            
        self.network = networkclient.NetworkClient(ip, int(port))
        self.timeBetweenNetworkUpdates = 0.02
        self.timeUntilNextNetworkUpdate = 0.0
        self.serverRoundTripTime = 0.0
        self.lastServerUpdate = time.time()
        self.player = None
    
    def sendText(self):
        e = CEGUI.WindowManager.getSingleton().getWindow("TextWindow/Editbox1")
        self.chat.sendMessage(e.getText().c_str())
        e.setText("")

    def messageListener(self, name, message):
        if message.startswith("/me") and len(message[3:].strip()) > 0 :
            self.appendText("*" + name + " " + message[3:].strip())
        else:
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

    def createBulletObject(self, name, direction, velocity, damage):
        return BulletObject(self, name, direction, velocity, damage)

    def createGrenadeObject(self, name, direction , velocity, damage):
        return GrenadeObject(self, name, direction, velocity, damage)

    def createPerson(self, name):
        return Person(self, name)
    
    def createStaticTriangleMesh(self, ent, space):
        vertdata=[]
        facedata=[]
        node = ent.parentNode
        for i in range(ent.mesh.numSubMeshes):
            #if not ent.mesh.getSubMesh(i).useSharedVertices:
            for v in ( ent.mesh.getSubMesh(i).getVertices(node.position, node.orientation, node.scale)):
                vertdata.append(v)             
            for f in (ent.mesh.getSubMesh(i).indices):
                facedata.append(f)

        data = ode.TriMeshData()
        data.build(vertdata, facedata)
        geom = ode.GeomTriMesh(data, space)
        del vertdata
        del facedata
        return geom
    
    def _createScene(self):
        Engine._createWorld(self)
        self.sceneManager.setAmbientLight((0.75, 0.75, 0.75, 0.0))

##        entity = self.sceneManager.createEntity('bgE', 'game.mesh')
##        entity.setNormaliseNormals(True)
##        # Scene -> Node
##        node = self.sceneManager.rootSceneNode.createChildSceneNode('bgN')
##        node.setScale(scale*self._size[0],scale*self._size[1],scale*self._size[2])
##        # Node -> Entity
##        node.attachObject(entity)
##        node.setPosition(0,0,0)
##        node.setDirection(0,0,-1)
##        node.setScale(0.5,0.5,0.5)
##        node.setVisible(True)
##        tempWorld = OgreOde.World(self.sceneManager)
##        self.createStaticTriangleMesh(entity, self.space)
##        geom = self.createStaticTriangleMesh(entity, self.space) 
##        print type(geom)

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
        CEGUI.MouseCursor.getSingleton().setVisible(False)
        font = CEGUI.FontManager.getSingleton().createFont("tuffy.font")
        background = winMgr.createWindow("TaharezLook/StaticImage", "background_wnd")
        background.setProperty("FrameEnabled", "false")
        background.setProperty("BackgroundEnabled", "false")
        ## install this as the root GUI sheet
        self.GUIsystem.setGUISheet(background)
        sheet = winMgr.createWindow("DefaultWindow", "root_wnd")
        ## attach this to the 'real' root
        background.addChildWindow(sheet)
        
        self.soundManager  = OgreAL.SoundManager()
        self.soundManager.getListener().setDirection((0,25,75))
            
        ##
        ## Build a window with some text and formatting options via radio buttons etc
        ##
        textwnd = winMgr.createWindow("TaharezLook/FrameWindow", "TextWindow")
        sheet.addChildWindow(textwnd)
        textwnd.setPosition(CEGUI.UVector2(CEGUI.UDim(0.2, 0), CEGUI.UDim(0.8, 0)))
        textwnd.setSize(CEGUI.UVector2(cegui_reldim(0.55), cegui_reldim( 0.2)))
        textwnd.setCloseButtonEnabled(False)
        textwnd.setText("Chat:'t', Team chat:'y', Send:'Enter', Cancel:'ESC', Hide:'F12')")
        textwnd.setEnabled(False)
        textwnd.setAlpha(0.3)
        
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

        debug = winMgr.createWindow("TaharezLook/StaticText", "DebugWindow")
        debug.setPosition(CEGUI.UVector2(CEGUI.UDim(0.8,0), CEGUI.UDim(0.01,0)))
        debug.setSize(CEGUI.UVector2(CEGUI.UDim(0.18,0), CEGUI.UDim(0.25,0)))
        debug.setProperty("HorzFormatting","WordWrapLefteAligned")
        debug.setProperty("VertFormatting", "TopAligned")
        self._debugWindow = debug
        sheet.addChildWindow(debug)

        vitals = winMgr.createWindow("TaharezLook/StaticText", "VitalsWindow")
        vitals.setPosition(CEGUI.UVector2(CEGUI.UDim(0.8,0), CEGUI.UDim(0.8,0)))
        vitals.setSize(CEGUI.UVector2(CEGUI.UDim(0.2,0), CEGUI.UDim(0.2,0)))
        vitals.setProperty("HorzFormatting","WordWrapLefteAligned")
        vitals.setProperty("VertFormatting", "TopAligned")
        self._vitalsWindow = vitals
        sheet.addChildWindow(vitals)

        myMaterial = ogre.MaterialManager.getSingleton().create("bullets","debugger")
        myMaterial.setLightingEnabled(False)
        myMaterial.setDepthWriteEnabled(False)
        myMaterial.setSceneBlending(ogre.SBT_TRANSPARENT_ALPHA)
        myMaterial.getTechnique(0).getPass(0).setVertexColourTracking(ogre.TVC_DIFFUSE)

        myMaterial = ogre.MaterialManager.getSingleton().create("grenade","debugger")
        

    def displayDebug(self):
        self._debugWindow.setText( ("FrameTime:    %0.4f\n" +
                                     "1StepTime:   %0.4f\n" +
                                     "NumSteps:    %4i\n" +
                                     "StepTime:    %0.4f\n" +
                                     "NetworkTime: %0.4f\n" +
                                     "ChatTime:    %0.4f\n" +
                                     "SNDPacketLen:%5i\n" +
                                     "RCVPacketLen:%5i\n") % \
                                  (self.debugFrameTime,
                                   (self.debugStepTime / self.debugNumSteps) if self.debugNumSteps else 0,
                                   self.debugNumSteps,
                                   self.debugStepTime,
                                   self.debugNetworkTime,
                                   self.debugChatTime,
                                   self.network.debugSendPacketLength,
                                   self.network.debugReceivePacketLength,
                                   )
                                  )

    def displayVitals(self):
        if self.player:
            self._vitalsWindow.setText(self.player.vitals())

    def displayScores(self):
        text = ""
        players = [object for object in self.objects if object.type == objects.PERSON]
        for player in players:
            text += " %s, %2i, %.2f\n" % \
                    (player._name, player.score, player.ping)

        self._scoreWindow.setSize(CEGUI.UVector2(CEGUI.UDim(0.15,0), CEGUI.UDim(0.01 + 0.05*len(players),0)))
        self._scoreWindow.setText(text)


    def _createFrameListener(self):
        ## note we pass ourselves as the demo to the framelistener
        self.frameListener = FrameListener(self, self.renderWindow, self.camera)
        self.keylistener = GameKeyListener(self)
        self.root.addFrameListener(self.frameListener)

    def updateChat(self, frameTime):
        self.timeUntilNextChatUpdate -= frameTime
        if self.timeUntilNextChatUpdate <= 0.0:
            self.chat.update()
            self.timeUntilNextChatUpdate = self.timeBetweenChatUpdates
    
    def frameEnded(self, frameTime, keyboard,  mouse):
        t = timer()

            
        Engine.frameEnded(self, frameTime)
        self.displayDebug()

        t.start()
        self.updateChat(frameTime)
        t.stop()
        t.debugChatTime = t.time()
        
        self.keyboard = keyboard
        self.mouse = mouse
        self.timeUntilNextNetworkUpdate -= frameTime
        t.start()

        if self.timeUntilNextNetworkUpdate <= 0.0:
            self.network.update(frameTime)
            self.displayScores()
            self.displayVitals()
            
            self.timeUntilNextNetworkUpdate = self.timeBetweenNetworkUpdates

            for message in self.network._messages:
                    
                if message[1] > self.lastServerUpdate:
                    self.timeUntilNextEngineUpdate = message[Engine.NET_TIME_UNTIL_UPDATE]
                    #print message[Engine.NET_TIME_UNTIL_UPDATE]
                    self.lastServerUpdate = message[Engine.NET_TIME]

                    for object in self.objects:
                        object.existsOnServer = False

                    for serverObject in message[Engine.NET_OBJECTS]:
                        hasObject = False
                        for object in self.objects:
                            if serverObject[Engine.NET_OBJECTS_NAME] == object._name:
                                hasObject = True
                                object.existsOnServer = True
                                object.setAttributes(serverObject[Engine.NET_OBJECTS_ATTRIBUTES])
                                object.setEvents(serverObject[Engine.NET_OBJECTS_EVENTS])
                        if not hasObject:
                            newObject = None
                            if serverObject[2] == True:
                                newObject = Player(self, serverObject[Engine.NET_OBJECTS_NAME], self.camera)
                                self.chat.setNickName(serverObject[Engine.NET_OBJECTS_NAME])
                                newObject.enable()
                                self.player = newObject
                            else:
                                if serverObject[Engine.NET_OBJECTS_TYPE] == objects.PERSON:
                                    newObject = Person(self, serverObject[Engine.NET_OBJECTS_NAME])
                                elif serverObject[Engine.NET_OBJECTS_TYPE] == objects.BULLET:
                                    newObject = BulletObject(self, serverObject[Engine.NET_OBJECTS_NAME])
                                elif serverObject[Engine.NET_OBJECTS_TYPE] == objects.GRENADE:
                                    newObject = GrenadeObject(self, serverObject[Engine.NET_OBJECTS_NAME])
                                else:
                                    print "Unknown object to create", serverObject[Engine.NET_OBJECTS_TYPE], objects.PERSON

                            if newObject:
                                newObject.existsOnServer = True        
                                newObject.setAttributes(serverObject[Engine.NET_OBJECTS_ATTRIBUTES])
                                newObject.setEvents(serverObject[Engine.NET_OBJECTS_EVENTS])
                                self.objects += [newObject]

                    for object in self.objects:
                        if not object.existsOnServer:
                            self.objects.remove(object)
                            object.close()
                            del object
                        
            self.network._messages = []
            
        if self.player != None:
            self.network.send(self.player.input(self.keyboard,  self.mouse))

        t.stop()
        self.debugNetworkTime = t.time()
        return True # Keep running
    
if __name__ == "__main__":
    world = Client()
    world.go()
    os._exit(0)
