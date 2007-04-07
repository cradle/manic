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

        if arg.key == OIS.KC_F1:
            print "Technique:", self.game.sceneManager.getShadowTechnique()
            if self.game.sceneManager.getShadowTechnique() == ogre.SHADOWTYPE_STENCIL_ADDITIVE:
                self.game.sceneManager.setShadowTechnique(ogre.SHADOWTYPE_NONE)
            else:
                self.game.sceneManager.setShadowTechnique(ogre.SHADOWTYPE_STENCIL_ADDITIVE)

        if arg.key == OIS.KC_F2:
            self.game.sceneManager.setShowDebugShadows(not self.game.sceneManager.getShowDebugShadows())

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
        self.game.camera.yaw(- arg.get_state().X.rel * 0.0012)
        self.game.camera.pitch(- arg.get_state().Y.rel * 0.0022)
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
        self.viewPort.setBackgroundColour((0.0, 0.0, 0.0, 1.0))
        self.camera.aspectRatio = self.viewPort.actualWidth / self.viewPort.actualHeight
        self.viewPort.setOverlaysEnabled(True)             

    def createStaticObject(self, size):
        return StaticObject(self, "s%s" % len(self.statics), size=size)

    def createBulletObject(self, name, direction, velocity, damage):
        return BulletObject(self, name, direction, velocity, damage)

    def createShrapnelObject(self, name, direction, velocity, damage):
        return ShrapnelObject(self, name, direction, velocity, damage)

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

    def createLogo(self):
        logoa = self.sceneManager.rootSceneNode.createChildSceneNode('logo-a')
        elogoa = self.sceneManager.createEntity("m-logo-a","logo-a.mesh")
        logoa.attachObject(elogoa)
        
        logov = self.sceneManager.rootSceneNode.createChildSceneNode('logo-v')
        elogov = self.sceneManager.createEntity("m-logo-v","logo-v.mesh")
        logoa.attachObject(elogov)

        logoPos = (0, 25, -35)
        logoa.setPosition(logoPos)
        logov.setPosition(logoPos)
        
        logoScale = (5,5,5)
        logoa.setScale(logoScale)
        elogoa.setNormaliseNormals(True)
        logov.setScale(logoScale)
        elogov.setNormaliseNormals(True)
        self.logoa = logoa
        self.logov = logov

    def createMenu(self):
        from menu import Menu
        self.menu = Menu(self.sceneManager)

    def updateMenu(self, frameTime):
        x = CEGUI.MouseCursor.getSingleton().getPosition().d_x
        y = CEGUI.MouseCursor.getSingleton().getPosition().d_y
        self.menu.update(x, y, frameTime)

    def updateLogo(self, frameTime):
        rotateSpeed = 0.1
        self.logoa.yaw(rotateSpeed*frameTime)
        self.logov.yaw(rotateSpeed*frameTime)
    
    def _createScene(self):
        Engine._createWorld(self)
        self.sceneManager.setAmbientLight((1.0, 1.0, 1.0, 1.0))
##        self.sceneManager.setShadowTechnique(ogre.SHADOWTYPE_NONE)
##        self.sceneManager.setShadowColour((0.5, 0.5, 0.5))
##        self.sceneManager.setShadowTextureSize(1024)
##        self.sceneManager.setShadowTextureCount(2)

##        light = self.sceneManager.createLight("sunlight")
##        light.setType(ogre.Light.LT_DIRECTIONAL)   # or .type
##        light.setDirection((0.4,-0.4,-1))
##        light.setDiffuseColour(0.85,0.85,0.85)
        #light.setCastShadows(True)
        
        entity = self.sceneManager.createEntity('bgE', 'Scene.mesh')
        #entity.setCastShadows(False)
##        entity.setNormaliseNormals(True)
        node = self.sceneManager.rootSceneNode.createChildSceneNode('bgN')
        node.attachObject(entity)
        node.setVisible(True)
##        node.setDirection(0,0,-1)
##        node.setScale(0.05,0.05,0.05)
##        tempWorld = OgreOde.World(self.sceneManager)
##        self.createStaticTriangleMesh(entity, self.space)
##        geom = self.createStaticTriangleMesh(entity, self.space) 
##        print type(geom)

        self.createLogo()
##        self.createMenu()

        # Setup Audio 
        self.soundManager  = OgreAL.SoundManager()
        self.soundManager.getListener().setDirection((0,25,75))
        self.sfx = SFX(self.soundManager)
        
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

        CEGUI.ImagesetManager.getSingleton().createImageset("menu.imageset")
        
        winMgr.loadWindowLayout("menu.layout")
        
        winMgr.loadWindowLayout("hud.layout")

        sheet = winMgr.getWindow("Background")
        #self.GUIsystem.setGUISheet(winMgr.getWindow("Menu"))
        self.GUIsystem.setGUISheet(sheet)
        
        font = CEGUI.FontManager.getSingleton().createFont("tuffy.font")
            
        textwnd = winMgr.getWindow("TextWindow")
        self._scoreWindow = winMgr.getWindow("ScoreWindow")
        self._debugWindow = winMgr.getWindow("DebugWindow")
        self._vitalsWindow = winMgr.getWindow("VitalsWindow")

        # Materials
        myMaterial = ogre.MaterialManager.getSingleton().create("bullets","a")
        myMaterial.setLightingEnabled(False)
        myMaterial.setDepthWriteEnabled(False)
        myMaterial.setSceneBlending(ogre.SBT_TRANSPARENT_ALPHA)
##        myMaterial.getTechnique(0).getPass(0).setVertexColourTracking(ogre.TVC_DIFFUSE)

        myMaterial = ogre.MaterialManager.getSingleton().create("cursor","b")
        myMaterial.setLightingEnabled(False)
        myMaterial.setDepthWriteEnabled(False)
        myMaterial.setSceneBlending(ogre.SBT_TRANSPARENT_ALPHA)
        myMaterial.getTechnique(0).getPass(0).setVertexColourTracking(ogre.TVC_AMBIENT | ogre.TVC_DIFFUSE)

        myMaterial = ogre.MaterialManager.getSingleton().create("grenade","c")
        

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
            text += " %s, %2i, %4i\n" % \
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

    def updateGUI(self, frameTime):
        self.updateLogo(frameTime)
##        self.updateMenu(frameTime)
        self.displayDebug()
        self.displayScores()
        self.displayVitals()
    
    def frameEnded(self, frameTime, keyboard,  mouse):
        t = timer()

        self.updateGUI(frameTime)
        
        Engine.frameEnded(self, frameTime)

        t.start()
        self.updateChat(frameTime)
        t.stop()
        t.debugChatTime = t.time()
        
        self.keyboard = keyboard
        self.mouse = mouse
        self.timeUntilNextNetworkUpdate -= frameTime
        t.start()

        if self.timeUntilNextNetworkUpdate <= 0.0:
            self.timeUntilNextNetworkUpdate = self.timeBetweenNetworkUpdates

            u = timer()
            u.start()
            self.network.update(frameTime)
            u.stop()

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
                                elif serverObject[Engine.NET_OBJECTS_TYPE] == objects.SHRAPNEL:
                                    newObject = ShrapnelObject(self, serverObject[Engine.NET_OBJECTS_NAME])
                                else:
                                    print "Unknown object to create", serverObject[Engine.NET_OBJECTS_TYPE], objects.PERSON

                            if newObject:
                                newObject.existsOnServer = True        
                                newObject.setAttributes(serverObject[Engine.NET_OBJECTS_ATTRIBUTES])
                                newObject.setEvents(serverObject[Engine.NET_OBJECTS_EVENTS])
                                self.objects += [newObject]

                    for object in self.objects:
                        if not object.existsOnServer and object.type == objects.PERSON:
                            self.objects.remove(object)
                            object.close()
                            del object
                        
            self.network.clearMessages()
            
        if self.player != None:
            self.network.send(self.player.input(self.keyboard,  self.mouse))

        t.stop()
        self.debugNetworkTime = t.time()
        return True # Keep running
    
if __name__ == "__main__":
    world = Client()
    import cProfile
    cProfile.run('world.go()', 'client-profile.txt')
    os._exit(0)
