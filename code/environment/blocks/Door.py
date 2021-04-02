from ursina import Vec3, color
from environment.blocks.StatefulBlock import StatefulBlock


class Door(StatefulBlock): 
    def __init__(self, position = (0,0,0), state = False):
        super().__init__(
            position = position,
            color = color.rgba(247, 202, 24, 255),
            model = 'cube',
            state = state,
            texture = 'white_cube',
            scale = Vec3(1, 2, 1),
            origin = Vec3(0,-0.25,0)
        )

    def update(self):
        if self.state == self.last_state: return False
        else:
            self.last_state = self.state
            if self.state: self.color = color.rgba(255,255,255,255)
            else: self.color = color.rgba(247, 202, 24, 255)
            return True