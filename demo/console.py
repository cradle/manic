import ogre.renderer.OGRE as ogre
import ogre.io.OIS as OIS
import array
import code
import sys

class Console(ogre.FrameListener, ogre.LogListener):
    CONSOLE_LINE_LENGTH = 85
    CONSOLE_LINE_COUNT = 15
    
    def __init__(self, root, consoleLocals = {}):
        ogre.FrameListener.__init__(self)
        ogre.LogListener.__init__(self)
        self.currentInputHistory = 0
        self.currentOutputHistory = 0
        self.inputHistory = []
        self.outputHistory = []
        self.prompt = array.array('b')
        self.visible = False
        self.updateOverlay = False
        self.interpreter = code.InteractiveConsole(consoleLocals)
        self.moreInput = False

        if not root.getSceneManagerIterator().hasMoreElements():
             raise("No scene manager found")

        self.root = root
        scene = root.getSceneManagerIterator().getNext()
        root.addFrameListener(self)

        self.height = 0.0

        overlay = ogre.OverlayManager.getSingleton().getByName("Application/ConsoleOverlay")
        self.textbox = ogre.OverlayManager.getSingleton().getOverlayElement("Application/ConsoleText")
        self.textpanel = ogre.OverlayManager.getSingleton().getOverlayElement("Application/ConsolePanel")

        overlay.show()
        ogre.LogManager.getSingleton().getDefaultLog().addListener(self)

        self.textbox.setCaption("PythonOgre Console\nGlenn Murray 2008")

    def keyPressed(self, evt):
        if not self.visible:
            if evt.key == OIS.KC_GRAVE:
                self.setVisible(True)
            return

        if evt.key == OIS.KC_ESCAPE:
            self.setVisible(False)  
        elif evt.key == OIS.KC_RETURN:
            if  len(self.prompt) > 0 or self.moreInput:
                self.outputHistory += [self.promptCursor() + self.prompt.tostring()]
                _stderr = sys.stderr
                _stdout = sys.stdout
                sys.stderr = self
                sys.stdout = self
                self.moreInput = self.interpreter.push(self.prompt.tostring())
                sys.stderr = _stderr
                sys.stdout = _stdout
                self.inputHistory += [self.prompt]
                self.prompt = self.prompt[0:0]
                self.currentInputHistory = len(self.inputHistory)
        elif evt.key == OIS.KC_BACK and len(self.prompt) > 0:
            self.prompt.pop()
        #elif evt.key == OIS.KC_PGUP:
        #    if self.currentLine != 0:
        #        self.currentLine -= 1
        #elif evt.key == OIS.KC_PGDOWN:
        #    if self.current_line < len(self.inputHistory):
        #        self.currentLine += 1
        elif evt.key == OIS.KC_UP:
            if self.currentInputHistory > 0:
                self.currentInputHistory -= 1 
                self.prompt = self.inputHistory[self.currentInputHistory][:]
        elif evt.key == OIS.KC_DOWN:
            if self.currentInputHistory+1 < len(self.inputHistory):
                self.currentInputHistory += 1 
                self.prompt = self.inputHistory[self.currentInputHistory][:]
        elif evt.text != 0:
            self.prompt.append(evt.text)
            self.currentInputHistory = len(self.inputHistory)
                
        self.updateOverlay = True


    def frameStarted(self, evt):
        if self.visible and self.height < 1.0:
            self.height += evt.timeSinceLastFrame * 2
            self.textpanel.show()
            if self.height >= 1.0:
                self.height = 1.0
        elif not self.visible and self.height > 0.0:
            self.height -= evt.timeSinceLastFrame * 2
            if self.height < 0.0:
                self.height = 0.0
                self.textpanel.hide()

        self.textpanel.setPosition(0,(self.height-1.0)*0.5)

        if self.updateOverlay:
            lines = []
            lines += [""] * (Console.CONSOLE_LINE_COUNT - len(self.outputHistory))
            lines += self.outputHistory[-1*Console.CONSOLE_LINE_COUNT:]
            text = "\n".join(lines)
            text += "\n" + self.promptCursor() + self.prompt.tostring() + "_"
            self.textbox.setCaption(text)
            self.updateOverlay = False
      
        return True

    def promptCursor(self):
        return '... ' if self.moreInput else '>>> '

    def write(self, text):
        for line in text.split("\n"):
            if len(line) > 0:
                self.outputHistory += [line]

        #TODO linewrap CONSOLE_LINE_LENGTH (eg dir(''))
                
        self.updateOverlay = True

    def frameEnded(self, evt):
        return True

    # variable assignation?
    def setVisible(self, visible):
        self.visible = visible
