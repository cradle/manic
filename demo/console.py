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
        self.hide()
        self.updateOverlay = False
        consoleLocals['console'] = self
        self.interpreter = code.InteractiveConsole(consoleLocals)
        self.multiLineInput = False
        self.hideSpeed = 2
        self.showSpeed = 2

        if not root.getSceneManagerIterator().hasMoreElements():
             raise("No scene manager found")

        self.root = root
        scene = root.getSceneManagerIterator().getNext()
        root.addFrameListener(self)

        self.height = 0.0

        self.overlay = ogre.OverlayManager.getSingleton().getByName("Application/ConsoleOverlay")
        self.overlay.show()
        self.textbox = ogre.OverlayManager.getSingleton().getOverlayElement("Application/ConsoleText")
        self.textpanel = ogre.OverlayManager.getSingleton().getOverlayElement("Application/ConsolePanel")
        ogre.LogManager.getSingleton().getDefaultLog().addListener(self)

        self.textbox.setCaption("PythonOgre Console\nGlenn Murray 2008")

        self.keyBinds = {
            OIS.KC_RETURN: self._runPromptText,
            OIS.KC_BACK: self._delCharPrompt,
            OIS.KC_UP: self._prevPromptText,
            OIS.KC_DOWN: self._nextPromptText,
            OIS.KC_ESCAPE: self.hide
            }

    def _delCharPrompt(self):
        if len(self.prompt) > 0:
            self.prompt.pop()

    def _runPromptText(self):
        if  len(self.prompt) > 0 or self.multiLineInput:
            self.outputHistory += [self.promptCursor + self.prompt.tostring()]
            _stderr, _stdout = sys.stderr, sys.stdout
            sys.stderr, sys.stdout = self, self
            self.multiLineInput = self.interpreter.push(self.prompt.tostring())
            sys.stderr, sys.stdout = _stderr, _stdout
            self.inputHistory += [self.prompt]
            self.prompt = self.prompt[0:0]
            self.currentInputHistory = len(self.inputHistory)

    def _prevPromptText(self):
        if self.currentInputHistory > 0:
            self.currentInputHistory -= 1 
            self.prompt = self.inputHistory[self.currentInputHistory][:]

    def _nextPromptText(self):
        if self.currentInputHistory+1 < len(self.inputHistory):
            self.currentInputHistory += 1 
            self.prompt = self.inputHistory[self.currentInputHistory][:]

    def _getVisible(self):
        return self._visible

    visible = property(_getVisible)

    def hide(self):
        self._visible = False

    def show(self):
        self._visible = True

    def keyPressed(self, evt):
        if not self.visible:
            if evt.key == OIS.KC_GRAVE:
                self.show()
            return

        try:
            self.keyBinds[evt.key]()
        except KeyError:
            if evt.text != 0:
                self.prompt.append(evt.text)
                self.currentInputHistory = len(self.inputHistory)
               
        self.updateOverlay = True

    def _appear(self, amt):
        self.height += amt
        self.overlay.show()
        if self.height >= 1.0:
            self.height = 1.0

    def _dissapear(self, amt):
        self.height -= amt
        if self.height < 0.0:
            self.height = 0.0
            self.overlay.hide()

    def _updateConsoleText(self):
        lines = []
        lines += [""] * (Console.CONSOLE_LINE_COUNT - len(self.outputHistory))
        lines += self.outputHistory[-1*Console.CONSOLE_LINE_COUNT:]
        text = "\n".join(lines)
        text += "\n" + self.promptCursor + self.prompt.tostring() + "_"
        self.textbox.setCaption(text)

    def _updateConsolePosition(self, time):
        if self.visible and self.height < 1.0:
            self._appear((1.005-self.height)/0.15*time)
        elif not self.visible and self.height > 0.0:
            self._dissapear(3.5*time)

        self.textpanel.setPosition(0,(self.height-1.0)*0.5)

    def frameStarted(self, evt):
        self._updateConsolePosition(evt.timeSinceLastFrame)

        if self.updateOverlay:
            self._updateConsoleText()
            self.updateOverlay = False
      
        return True

    def _getPromptCursor(self):
        return '... ' if self.multiLineInput else '>>> '

    promptCursor = property(_getPromptCursor)

    def write(self, text):
        for line in text.split("\n"):
            if len(line) > 0:
                self.outputHistory += [line]

        #TODO linewrap CONSOLE_LINE_LENGTH (eg dir(''))
                
        self.updateOverlay = True
