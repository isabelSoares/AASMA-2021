# block that affects other block 

from ursina import color, Vec3
from environment.blocks.StatefulBlock import StatefulBlock

class TriggersBlock(StatefulBlock):
    def __init__(self, state, block_affected_pos, position = (0,0,0), model = 'cube', texture = 'white_cube', color = color.rgba(198,193,168), scale = 1, origin = Vec3(0,0,0)):
        super().__init__(
            position = position,
            model = model,
            texture = texture,
            color = color,
            scale = scale,
            state = state,
			origin = origin
        )
        self.block_affected_pos = block_affected_pos 

    def update(self):
        pass

    def affect_block(self, block):
        pass

    def get_block_affected_pos(self):
        return self.block_affected_pos

    def set_block_affected_pos(self, block_affected_pos):
        self.block_affected_pos = block_affected_pos