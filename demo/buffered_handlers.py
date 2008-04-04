import ogre.io.OIS as OIS
import ogre.gui.CEGUI as CEGUI

class KeyboardListener(OIS.KeyListener):
    def __init__(self, keyboard = 0):
        # You will also need to store references to instances of this class to prevent them being garbage collected
        OIS.KeyListener.__init__(self)

        if keyboard:
            keyboard.setEventCallback(self)

        self.keyListeners = []

    def addKeyListener(self, listener):
        self.keyListeners.append(listener)
    
    def keyPressed(self, evt):
        for listener in self.keyListeners:
            listener.keyPressed(evt)
        
        ceguiSystem = CEGUI.System.getSingleton()
        ceguiSystem.injectKeyDown(evt.key)
        ceguiSystem.injectChar(evt.text)
        return True
    
    def keyReleased(self, evt):
       CEGUI.System.getSingleton().injectKeyUp(evt.key)
       return True
