from ursina import color
from environment.blocks.Block import Block

class WallBlock(Block):
    def __init__(self, position = (0,0,0), permission = 'ALL'):
        super().__init__(
            position = position,
            color = color.rgba(205, 177, 177, 255),
            texture = 'brick'
        )
        self.permission = permission

    def hasPermission(self, agent_name):
        if self.permission == 'ALL':
            return True
        return self.permission == agent_name