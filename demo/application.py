import ogre.renderer.OGRE as ogre
import ogre.io.OIS as OIS
import ogre.gui.CEGUI as CEGUI
import os
import buffered_handlers
import console
 
class ExitListener(ogre.FrameListener):
    def __init__(self, keyboard):
        ogre.FrameListener.__init__(self)
        self.keyboard = keyboard
 
    def frameStarted(self, evt):
        self.keyboard.capture()
        return not self.keyboard.isKeyDown(OIS.KC_ESCAPE)
 
class Application(object):
    def __init__(self):
        self.systemDirectory = os.path.join(os.getcwd(),"system")
        
        self.pluginFile = os.path.join(self.systemDirectory, "plugins.cfg")
        self.configFile = os.path.join(self.systemDirectory, "graphics.cfg")
        self.resourcesFile = os.path.join(self.systemDirectory, "resources.cfg")

        self.logFile = os.path.join(self.systemDirectory, "ogre.log")
 
    def go(self):
        self.createRoot()
        self.defineResources()
        self.setupRenderSystem()
        self.createRenderWindow()
        self.initializeResourceGroups()
        self.setupScene()
        self.setupInputSystem()
        self.setupCEGUI()
        self.createFrameListener()
        self.createInputListener()
        self.setupConsole()
        self.startRenderLoop()
        self.cleanUp()
 
    def createRoot(self):
        self.root = ogre.Root(self.pluginFile,
                              self.configFile,
                              self.logFile)
        
    def defineResources(self):
        cf = ogre.ConfigFile()
        cf.load(self.resourcesFile)

        seci = cf.getSectionIterator()
        while seci.hasMoreElements():
            secName = seci.peekNextKey()
            settings = seci.getNext()
            for item in settings:
                typeName = item.key
                archName = item.value
                ogre.ResourceGroupManager.getSingleton().addResourceLocation(archName, typeName, secName)

 
    def setupRenderSystem(self):
        # http://wiki.python-ogre.org/index.php/Basic_Tutorial_6
        
        if not self.root.restoreConfig():
            renderers = self.root.getAvailableRenderers()
            if len(renderers) == 0:
                raise Exception("No Available Renderers")

            renderer = renderers[0]
            self.root.setRenderSystem(renderer)
            self.root.saveConfig()

 
    def createRenderWindow(self):
        self.root.initialise(True, "Assault Vector")
 
    def initializeResourceGroups(self):
        ogre.TextureManager.getSingleton().setDefaultNumMipmaps(5)
        ogre.ResourceGroupManager.getSingleton().initialiseAllResourceGroups()
 
    def setupScene(self):
        sceneManager = self.root.createSceneManager(ogre.ST_GENERIC, "Default SceneManager")
        camera = sceneManager.createCamera("Camera")
        viewPort = self.root.getAutoCreatedWindow().addViewport(camera)
 
    def setupInputSystem(self):
        windowHandle = 0
        renderWindow = self.root.getAutoCreatedWindow()
        windowHandle = renderWindow.getCustomAttributeInt("WINDOW")
        paramList = [("WINDOW", str(windowHandle))]
        self.inputManager = OIS.createPythonInputSystem(paramList)

        try:
            self.keyboard = self.inputManager.createInputObjectKeyboard(OIS.OISKeyboard, True)
            # self.mouse = self.inputManager.createInputObjectMouse(OIS.OISMouse, False)
            # self.joystick = self.inputManager.createInputObjectJoyStick(OIS.OISJoyStick, False)
        except Exception, e:
            raise e
 
    def setupCEGUI(self):
        sceneManager = self.root.getSceneManager("Default SceneManager")
        renderWindow = self.root.getAutoCreatedWindow()

        # CEGUI setup
        self.renderer = CEGUI.OgreCEGUIRenderer(renderWindow, ogre.RENDER_QUEUE_OVERLAY, False, 3000, sceneManager)
        self.system = CEGUI.System(self.renderer)
 
    def createFrameListener(self):
        self.exitListener = ExitListener(self.keyboard)
        self.root.addFrameListener(self.exitListener)
 
    def createInputListener(self):
        self.keyboardListener = buffered_handlers.KeyboardListener(self.keyboard)

    def setupConsole(self):
        self.console = console.Console(self.root, self.keyboard)
        self.console.setVisible(True)
        self.keyboardListener.addKeyListener(self.console)
 
    def startRenderLoop(self):
        self.root.startRendering()
 
    def cleanUp(self):
        ## OIS
        self.inputManager.destroyInputObjectKeyboard(self.keyboard)
        # self.inputManager.destroyInputObjectMouse(self.mouse)
        # self.inputManager.destroyInputObjectJoyStick(self.joystick)
        OIS.InputManager.destroyInputSystem(self.inputManager)
        self.inputManager = None

        ## CEGUI
        del self.renderer
        del self.system

        ## Ogre
        del self.exitListener
        del self.root
 
 
if __name__ == '__main__':
    try:
        ta = Application()
        ta.go()
    except ogre.OgreException, e:
        print e
