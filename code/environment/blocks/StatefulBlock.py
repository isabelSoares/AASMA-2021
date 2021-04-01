# Block with state

from ursina import color, Vec3
from environment.blocks.Block import Block

class StatefulBlock(Block):
    def __init__(self, state, position = (0,0,0), model = 'cube', texture = 'white_cube', color = color.rgba(198,193,168), scale = 1, origin = Vec3(0,0,0)):
        super().__init__(
            position = position,
            model = model,
            texture = texture,
            color = color,
            scale = scale,
			origin = origin
        )
        self.state = state
        self.last_state = state

    def update(self):
        pass

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state
        