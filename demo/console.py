import ogre.renderer.OGRE as ogre
import ogre.io.OIS as OIS
import array
import code
import sys

## PythonOgre Console
# Usage:
#   console = console.Console(self.root, locals())
#   console.show()
#   # Then inject the keys pressed in your keyboard handler
#   console.keyPressed(evt)
#
## TODO
# - Key repeating
# - PGUP PGDOWN history viewing
# - Linewrap if prompt too long
# - Write history to file
# - Read history from file

class Console(ogre.FrameListener):
    CONSOLE_LINE_LENGTH = 85
    CONSOLE_LINE_COUNT = 15
    
    def __init__(self, root, consoleLocals = {}):
        ogre.FrameListener.__init__(self)
        
        self.currentInputHistory = 0
        self.inputHistory = []
        self.outputHistory = []
        self.prompt = array.array('b')
        self.updateOverlay = True
        self.multiLineInput = False

        consoleLocals['console'] = self
        self.interpreter = code.InteractiveConsole(consoleLocals)

        root.addFrameListener(self)
        
        self.height = 0.0
        self.hide()

        self.overlay = ogre.OverlayManager.getSingleton().getByName("Application/ConsoleOverlay")
        self.overlay.show()
        self.textbox = ogre.OverlayManager.getSingleton().getOverlayElement("Application/ConsoleText")
        self.textoverlay = ogre.OverlayManager.getSingleton().getOverlayElement("Application/ConsoleTextOverlay")
        self.textpanel = ogre.OverlayManager.getSingleton().getOverlayElement("Application/ConsolePanel")

        self.keyBinds = {
            OIS.KC_RETURN: self._runPromptText,
            OIS.KC_BACK: self._backspaceCharPrompt,
            OIS.KC_DELETE: self._deleteCharPrompt,
            OIS.KC_UP: self._prevPromptText,
            OIS.KC_DOWN: self._nextPromptText,
            OIS.KC_ESCAPE: self.hide,
            OIS.KC_LEFT: self._moveCursorLeft,
            OIS.KC_RIGHT: self._moveCursorRight,
            OIS.KC_HOME: self._moveCursorHome,
            OIS.KC_END: self._moveCursorEnd
            }

    def _moveCursorEnd(self):
        self.cursorPosition = len(self.prompt)
        
    def _moveCursorHome(self):
        self.cursorPosition = 0

    def _moveCursorLeft(self):
        if self.cursorPosition > 0:
            self.cursorPosition -= 1

    def _moveCursorRight(self):
        if self.cursorPosition < len(self.prompt):
            self.cursorPosition += 1

    def _deleteCharPrompt(self):
        if len(self.prompt) > 0 and self.cursorPosition < len(self.prompt):
            self.prompt.pop(self.cursorPosition)

    def _backspaceCharPrompt(self):
        if len(self.prompt) > 0 and self.cursorPosition > 0:
            self.prompt.pop(self.cursorPosition-1)
            self.cursorPosition -= 1

    def setPrompt(self, byteArray):
        self._prompt = byteArray
        self.cursorPosition = len(self._prompt)

    def getPrompt(self):
        return self._prompt

    prompt = property(getPrompt, setPrompt)

    def _enableSysRedirect(self):
        self._stderr, self._stdout = sys.stderr, sys.stdout
        sys.stderr, sys.stdout = self, self

    def _disableSysRedirect(self):
        sys.stderr, sys.stdout = self._stderr, self._stdout

    def _runPromptText(self):
        if  len(self.prompt) > 0 or self.multiLineInput:
            self.outputHistory += [self.promptCursor + self.prompt.tostring()]
            self._enableSysRedirect()
            self.multiLineInput = self.interpreter.push(self.prompt.tostring())
            self._disableSysRedirect()
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
                self.prompt.insert(self.cursorPosition, evt.text)
                self.cursorPosition += 1
                self.currentInputHistory = len(self.inputHistory)
               
        self.updateOverlay = True

    def _updateConsoleText(self):
        lines = [""] * (Console.CONSOLE_LINE_COUNT - len(self.outputHistory))
        lines += self.outputHistory[-1*Console.CONSOLE_LINE_COUNT:]
        text = "\n".join(lines)
        text += u"\n%s%s" % (self.promptCursor,
                               self.prompt.tostring())
        self.textbox.setCaption(text)

        text = "\n".join([""] * (Console.CONSOLE_LINE_COUNT))
        text += u"\n%s%s_" % (self.promptCursor,
                               " " * self.cursorPosition)
        
        self.textoverlay.setCaption(text)

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
            while len(line) > 0:
                self.outputHistory += [line[:Console.CONSOLE_LINE_LENGTH]]
                line = line[Console.CONSOLE_LINE_LENGTH:]
                
        self.updateOverlay = True
