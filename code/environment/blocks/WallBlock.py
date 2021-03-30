from ursina import color
from environment.blocks.Block import Block

class WallBlock(Block):
    def __init__(self, position = (0,0,0)):
        super().__init__(
            position = position,
            color = color.rgba(205, 177, 177, 255)
        )