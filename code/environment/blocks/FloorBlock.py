import random
from ursina import color, load_texture
from environment.blocks.Block import Block

grass_texture = load_texture('textures/grass_block.png')

class FloorBlock(Block):
    def __init__(self, position = (0,0,0)):
        super().__init__(
            position = position,
            color = color.color(0,0,random.uniform(0.9,1)),
            model = 'textures/block',
            texture = grass_texture,
            scale = 0.5
        )