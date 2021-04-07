from ursina import color
from environment.blocks.Block import Block

class AgentBlock(Block):
    def __init__(self, position = (0,0,0), agent_name = None, color = color):
        super().__init__(
            position = position,
            color = color
        )
        self.agent_name = agent_name