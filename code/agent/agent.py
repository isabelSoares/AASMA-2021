import random
from ursina import *
from time import sleep

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
        next_position = random.choice([self.move, self.rotate_right, self.rotate_left])(world)

        #agent in the pressure plate
        entity = world.get_entity(next_position)
        last_entity = world.get_entity(last_position)
        if (entity != None) & (last_position != next_position) & (type(entity).__name__ == "PressurePlate"):
            entity.state = True
        elif (last_entity != None) & (last_position != next_position) & (type(last_entity).__name__ == "PressurePlate"):
            last_entity.state = False
    
    def Forward(self):
        return round(Vec3(self.forward))
    
    def move(self, world):
        if not self.canMove(world):
            return self.position
        print(self.name + ': moved forward')
        final_position = self.position + self.Forward()

        world.update_agent(self.position, final_position)
        self.animate_position(final_position, curve=curve.linear, duration=.2)
        return final_position
    
    def jump(self, world):
        print(self.name + ': jumped forward')
        final_position = self.position + self.Forward() + Vec3(0, 1, 0)

        world.update_agent(self.position, final_position)
        self.animate_position(self.position + self.Forward(), curve=curve.linear, duration=.2)
        self.animate_position(self.position + Vec3(0, 1, 0), curve=curve.linear, duration=.08)
    
    def rotate_right(self, world):
        print(self.name + ': rotated to the right')
        self.animate_rotation(self.rotation + Vec3(0, 90, 0), curve=curve.linear, duration=.2)
        return self.position
    
    def rotate_left(self, world):
        print(self.name + ': rotated to the left')
        self.animate_rotation(self.rotation - Vec3(0, 90, 0), curve=curve.linear, duration=.2)
        return self.position
    
    def rotate_randomly(self):
        print('   - random choice')
        return random.choice([self.rotate_right, self.rotate_left])()

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
        while world.get_static_block(next_position) != None:
            count += 1
            next_position += Vec3(0, 1, 0)
        return count
    
    def entityAhead(self, world):
        next_position = Vec3(self.position + self.Forward())
        if world.get_entity(next_position) != None:
            return type(world.get_entity(next_position)).__name__
        else:
            return None
    
    def agentAhead(self, world):
        next_position = Vec3(self.position + self.Forward())
        return world.get_agent(next_position) != None