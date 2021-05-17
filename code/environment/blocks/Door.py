from ursina import Vec3, color, load_texture
from environment.blocks.StatefulBlock import StatefulBlock

wood_door_texture = load_texture('textures/woodDoor.jpg')

class Door(StatefulBlock): 
    def __init__(self, position = (0,0,0), state = False, permission = 'ALL'):
        super().__init__(
            position = position,
            color = color.rgba(247, 202, 24, 255),
            texture = wood_door_texture, 
            model = 'cube',
            state = state,
            scale = Vec3(1, 2, 1),
            origin = Vec3(0,-0.25,0),
        )
        self.permission = permission

    def update(self):
        if self.state == self.last_state: return False
        else:
            self.last_state = self.state
            if self.state: self.color = color.rgba(255,255,255,255)
            else: self.color = color.rgba(247, 202, 24, 255)
            return True
    
    def isOpen(self):
        return self.state
    
    def hasPermission(self, agent_name):
        if self.permission == 'ALL':
            return True
        return self.permission == agent_name