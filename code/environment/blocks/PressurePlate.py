from ursina import Vec3, color, load_texture
from environment.blocks.TriggersBlock import TriggersBlock

wooden_floor_texture = load_texture('textures/woodenFloor.jpg')

class PressurePlate(TriggersBlock): 
    def __init__(self, block_affected_pos, position = (0,0,0), state = False):
        super().__init__(
            position = position,
            color = color.rgba(247, 202, 24, 255),
            texture = wooden_floor_texture, 
            model = 'cube',
            state = state,
            scale = Vec3(0.85, 0.10, 0.85),
            origin = Vec3(0,4.5,0),
            block_affected_pos = block_affected_pos
        )

    def update(self):
        if self.state == self.last_state: return False
        else:
            self.last_state = self.state
            if self.state: self.color = color.rgba(255,255,255,255)
            else: self.color = color.rgba(247, 202, 24, 255)
            return True

    def affect_block(self, block):
        block.set_state(self.state)
        block.update()

        