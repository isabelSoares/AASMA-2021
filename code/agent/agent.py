from ursina import *
from time import sleep
import random

class Agent(Entity):
    def __init__(self, name = 'Unknown', model = 'cube', position = (0, 1, 0), color = color.rgba(0,0,0)):
        super().__init__(
            name = 'Agent ' + name,
            model = model,
            position = Vec3(position),
            color = color,
            scale = Vec3(1, 2, 1),
            origin = Vec3(0, -0.25, 0)
        )
    
    def move(self):
        if False: # TODO if there is a wall ahead
            print(self.name + ': FAILED to move forward - WALL')
            return
        elif False: # TODO if there is a closed door ahead
            print(self.name + ': FAILED to move forward - DOOR CLOSED')
            return
        print(self.name + ': moved forward')
        self.position += self.forward
    
    def jump(self):
        if False: # TODO if there is not a block ahead
            print(self.name + ': FAILED to jump forward - NO BLOCK')
            return
        elif False: # TODO if there is more than one block ahed
            print(self.name + ': FAILED to jump forward - VERY HIGH')
            return
        print(self.name + ': jumped forward')
        self.position += self.forward
        self.position += self.up
    
    def rotate_right(self):
        print(self.name + ': rotated to the right')
        self.rotation += Vec3(0, 90, 0)
    
    def rotate_left(self):
        print(self.name + ': rotated to the left')
        self.rotation -= Vec3(0, 90, 0)
    
    def rotate_randomly(self):
        random.choice([self.rotate_right, self.rotate_left])()
        print('   - random choice')