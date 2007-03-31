class MenuItem(object):
    _itemNumber = 0
    def nextItemNumber():
        MenuItem._itemNumber += 1
        return MenuItem._itemNumber

    nextItemNumber = staticmethod(nextItemNumber)
    
    def __init__(self, text, sceneManager):
        self.selected = False
        self.itemNumber = MenuItem.nextItemNumber()
        self.text = text
        self.width = len(self.text)
        self.height = 1.5
        self.node = sceneManager.rootSceneNode.createChildSceneNode('option-' + str(self.itemNumber))
        self.entity = sceneManager.createEntity("option-e-" + str(self.itemNumber),"option.mesh")
        self.node.attachObject(self.entity)
        self.position = (0, 10-self.itemNumber*self.height, -5)
        self.node.setPosition(self.position)

    def update(self, x, y, frameTime):
        if x > self.position[0] - self.width/2 and x < self.position[0] + self.width/2 and\
           y > self.position[1] - self.height/2 and y < self.position[1] + self.width/2:
            self.node.setPosition((self.position[0], self.position[1], 5))
        else:
            self.node.setPosition((self.position[0], self.position[1], -5))
    
class Menu(object):
    def __init__(self, sceneManager):
        self.items = []
        for option in ["Start", "Quit", "Options", "1", "2", "3","4"]:
            self.items.append(MenuItem(option, sceneManager))

    def update(self, x,y, frameTime):
        for item in self.items:
            item.update(x,y,frameTime)
        
