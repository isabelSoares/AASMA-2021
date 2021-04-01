import random
from ursina import *
from time import sleep
from math import isclose
from environment.blocks.PressurePlate import PressurePlate

char_texture = load_texture('textures/Char.png')

class Agent(Entity):
    def __init__(self, name = 'Unknown', model = 'textures/agent', position = (0, 1, 0), texture = char_texture, color = color.rgba(0,0,0)):
        super().__init__(
            name = 'Agent ' + name,
            model = model,
            texture = texture,
            position = Vec3(position),
            color = color,
            origin = Vec3(0, 1, 0)
        )
    
    def decision(self, world):
        last_position = self.position
        random.choice([self.move, self.rotate_right, self.rotate_left])(world)

        #agent in the pressure plate
        entity = world.get_entity(self.position)
        last_entity = world.get_entity(last_position)
        if (entity != None) & (last_position != self.position) & (isinstance(entity, PressurePlate)):
            entity.state = True
        elif (last_entity != None) & (last_position != self.position) & (isinstance(last_entity, PressurePlate)):
            entity.state = False
    
    def Forward(self):
        return round(Vec3(self.forward))
    
    def move(self, world):
        if not self.canMove(world):
            return
        print(self.name + ': moved forward')
        world.update_agent(self.position, self.position + self.Forward())
        self.animate_position(self.position+self.Forward(), curve=curve.linear, duration=.2)
    
    def jump(self, world):
        print(self.name + ': jumped forward')
        world.update_agent(self.position, self.position + self.Forward() + Vec3(0, 1, 0))
        self.animate_position(self.position + self.Forward(), curve=curve.linear, duration=.2)
        self.animate_position(self.position + Vec3(0, 1, 0), curve=curve.linear, duration=.08)
    
    def rotate_right(self, world):
        print(self.name + ': rotated to the right')
        self.animate_rotation(self.rotation + Vec3(0, 90, 0), curve=curve.linear, duration=.2)
    
    def rotate_left(self, world):
        print(self.name + ': rotated to the left')
        self.animate_rotation(self.rotation - Vec3(0, 90, 0), curve=curve.linear, duration=.2)
    
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
        print(self.Forward())
        next_position = self.position + self.Forward() - Vec3(0, 1, 0)
        count = -1
        while next_position in world.static_map:
            count += 1
            next_position += Vec3(0, 1, 0)
        return count
    
    def entityAhead(self, world):
        next_position = Vec3(self.position + self.Forward())
        if next_position in world.entities_map:
            return type(world.entities_map[next_position].__name__)
        else:
            return None
    
    def agentAhead(self, world):
        next_position = Vec3(self.position + self.Forward())
        return next_position in world.agents_map