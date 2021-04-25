class Message():
    def __init__(self, id, agent, position, needed_action, text):
        self.id = id
        self.agent = agent
        self.position = position
        self.needed_action = needed_action
        self.text = text
    
    def getId(self):
        return self.id
    
    def getAgent(self):
        return self.agent
    
    def getPosition(self):
        return self.position
    
    def getNeededAction(self):
        return self.needed_action
    
    def getText(self):
        return self.text