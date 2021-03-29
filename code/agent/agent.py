from ursina import *
from time import sleep
import random

GREEN_COLOR = color.rgba(21,127,21)
RED_COLOR = color.rgba(141,25,25)
NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3
DIRECTIONS = [Vec3(1,0,0), Vec3(0,0,-1), Vec3(-1,0,0), Vec3(0,0,1)]

class Agent(Entity):
    def __init__(self, name = 'Unknown', model = 'cube', position = (0, 1, 0), color = color.rgba(0,0,0), direction = NORTH):
        super().__init__(
            name = 'Agent ' + name,
            model = model,
            position = Vec3(position),
            color = color
        )
        self.direction = direction
    
    def move(self):
        if False: # TODO if there is a wall ahead
            print(self.name + ': FAILED to move forward - WALL')
            return
        elif False: # TODO if there is a closed door ahead
            print(self.name + ': FAILED to move forward - DOOR CLOSED')
            return
        print(self.name + ': moved forward')
        self.position += DIRECTIONS[self.direction]
    
    def jump(self):
        if False: # TODO if there is not a block ahead
            print(self.name + ': FAILED to jump forward - NO BLOCK')
            return
        elif False: # TODO if there is more than one block ahed
            print(self.name + ': FAILED to jump forward - VERY HIGH')
            return
        print(self.name + ': jumped forward')
        self.position += DIRECTIONS[self.direction]
        self.position += Vec3(0,1,0)
    
    def rotate_right(self):
        print(self.name + ': rotated to the right')
        self.rotation += Vec3(0, 90, 0)
        self.direction += 1
        if self.direction == 4:
            self.direction = 0
    
    def rotate_left(self):
        print(self.name + ': rotated to the left')
        self.rotation -= Vec3(0, 90, 0)
        self.direction -= 1
        if self.direction == -1:
            self.direction = 3
    
    def rotate_randomly(self):
        random.choice([self.rotate_right, self.rotate_left])()
        print('   - random choice')