from ursina import *
from time import sleep
import random
from math import isclose

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
    
    def move(self, world):
        if not self.canMove(world):
            return
        print(self.name + ': moved forward')
        world.update_agent(self.position, self.position + self.forward)
        self.position += self.forward
    
    def jump(self, world):
        print(self.name + ': jumped forward')
        world.update_agent(self.position, self.position + self.forward + Vec3(0, 1, 0))
        print(self.position)
        self.position += self.forward + Vec3(0, 1, 0)
        print(self.position)
    
    def rotate_right(self):
        print(self.name + ': rotated to the right')
        self.rotation += Vec3(0, 90, 0)
    
    def rotate_left(self):
        print(self.name + ': rotated to the left')
        self.rotation -= Vec3(0, 90, 0)
    
    def rotate_randomly(self):
        random.choice([self.rotate_right, self.rotate_left])()
        print('   - random choice')

    def canMove(self, world):
        blocksAhead = self.blocksAhead(world)
        if blocksAhead == -1:
            print(self.name + ': FAILED to move forward - NO BLOCKS AHEAD')
            return False
        elif blocksAhead == 1:
            self.jump(world)
            return False
        elif blocksAhead > 1:
            print(self.name + ': FAILED to to jump forward - ' + str(blocksAhead) + ' VERY HIGH')
            return False
        
        entity_type = self.entityAhead(world)
        if entity_type == 'Door':
            print(self.name + ': FAILED to move forward - DOOR AHEAD')
            return False
        
        return True

    def blocksAhead(self, world):
        next_position = round(Vec3(self.position + self.forward - Vec3(0, 1, 0)))
        count = -1
        while next_position in world.static_map:
            count += 1
            next_position += Vec3(0, 1, 0)
        return count
    
    def entityAhead(self, world):
        next_position = round(Vec3(self.position + self.forward))
        if next_position in world.entities_map:
            return type(world.entities_map[next_position].__name__)
        else:
            return None
    
    def agentAhead(self, world):
        next_position = Vec3(self.position + self.forward)
        return next_position in world.agents_map