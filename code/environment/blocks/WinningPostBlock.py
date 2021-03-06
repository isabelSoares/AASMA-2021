from ursina import color
from environment.blocks.Block import Block

class WinningPostBlock(Block):
    def __init__(self, position = (0,0,0), agent_name = "", color = color):
        super().__init__(
            position = position,
            color = color,
        )
        self.agent_name = agent_name
    
    def getAgentName(self):
        return self.agent_name