import random
from ursina import *
from time import sleep

animation_duration_tick_proportion = .2
char_texture = load_texture('textures/Char.png')

# ============= ACTIONS VARIABLES =============
MOVE_ONLY = 'MOVE_ONLY'
MOVE_UP = 'MOVE_UP'
MOVE_DOWN = 'MOVE_DOWN'
ROTATE_LEFT = 'ROTATE_LEFT'
ROTATE_RIGHT = 'ROTATE_RIGHT'
MOVE_ONLY_TO_PRESSURE_PLATE = 'MOVE_ONLY_TO_PressurePlate'
MOVE_ONLY_TO_DOOR = 'MOVE_ONLY_TO_Door'
MOVE_UP_TO_PRESSURE_PLATE = 'MOVE_UP_TO_PressurePlate'
MOVE_UP_TO_DOOR = 'MOVE_UP_TO_Door'
MOVE_DOWN_TO_PRESSURE_PLATE = 'MOVE_DOWN_TO_PressurePlate'
MOVE_DOWN_TO_DOOR = 'MOVE_DOWN_TO_Door'

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

        self.animation_duration = animation_duration_tick_proportion
    
    def decision(self, world, agents_decisions):
        last_position = self.position

        possible_actions_list = self.possible_actions(world, agents_decisions)
        print(self.name + ':')
        print('   - possible actions: ' + str(possible_actions_list))
        a = random.choice(possible_actions_list)
        if a == MOVE_ONLY or a == MOVE_ONLY_TO_PRESSURE_PLATE:
            next_position = self.move_only(world)
        elif a == MOVE_UP or a == MOVE_UP_TO_PRESSURE_PLATE:
            next_position = self.move_up(world)
        elif a == MOVE_DOWN or a == MOVE_DOWN_TO_PRESSURE_PLATE:
            next_position = self.move_down(world)
        elif a == ROTATE_LEFT:
            next_position = self.rotate_left()
        elif a == ROTATE_RIGHT:
            next_position = self.rotate_right()
        elif a == MOVE_ONLY_TO_DOOR:
            next_position = self.position;
            print('   - \"There\'s a door here!\"')
        elif a == MOVE_UP_TO_DOOR:
            next_position = self.position;
            print('   - \"There\'s a door here!\"')
        elif a == MOVE_DOWN_TO_DOOR:
            next_position = self.position;
            print('   - \"There\'s a door here!\"')

        #agent in the pressure plate
        entity = world.get_entity(next_position)
        last_entity = world.get_entity(last_position)
        if (entity != None) & (last_position != next_position) & (type(entity).__name__ == "PressurePlate"):
            entity.state = True
        elif (last_entity != None) & (last_position != next_position) & (type(last_entity).__name__ == "PressurePlate"):
            last_entity.state = False
        
        return next_position

    def Forward(self):
        return round(Vec3(self.forward))
    
    def move_only(self, world):
        print('   - moved forward')
        final_position = self.position + self.Forward()
        world.update_agent(self.position, final_position)
        self.animate_position(final_position, curve=curve.linear, duration=self.animation_duration)
        return final_position
    
    def move_up(self, world):
        print('   - jumped forward')
        final_position = self.position + self.Forward() + Vec3(0, 1, 0)
        world.update_agent(self.position, final_position)
        self.position = self.position + self.Forward() + Vec3(0, 1, 0)
        return final_position
    
    def move_down(self, world):
        print('   - came down forward')
        final_position = self.position + self.Forward() - Vec3(0, 1, 0)
        world.update_agent(self.position, final_position)
        self.position = self.position + self.Forward() - Vec3(0, 1, 0)
        return final_position
    
    def rotate_right(self):
        print('   - rotated to the right')
        self.animate_rotation(self.rotation + Vec3(0, 90, 0), curve=curve.linear, duration=self.animation_duration)
        return self.position
    
    def rotate_left(self):
        print('   - rotated to the left')
        self.animate_rotation(self.rotation - Vec3(0, 90, 0), curve=curve.linear, duration=self.animation_duration)
        return self.position
    
    def rotate_randomly(self):
        print('   - random choice')
        return random.choice([self.rotate_right, self.rotate_left])()
    
    def possible_actions(self, world, agents_decisions):
        possible_actions_list = []
        next_position = self.position + self.Forward()
        if self.agentAhead(world) or (next_position in agents_decisions):
            return [ROTATE_LEFT, ROTATE_RIGHT]
        if world.get_static_block(next_position - Vec3(0, 1, 0)) != None \
            and world.get_static_block(next_position) == None \
            and world.get_static_block(next_position + Vec3(0, 1, 0)) == None \
            and (next_position not in agents_decisions):
            if world.get_entity(next_position) != None:
                possible_actions_list.append('MOVE_ONLY_TO_' + type(world.get_entity(next_position)).__name__)
            else:
                possible_actions_list.append(MOVE_ONLY)
        if world.get_static_block(next_position) != None \
            and world.get_static_block(next_position + Vec3(0, 1, 0)) == None \
            and world.get_static_block(next_position + Vec3(0, 2, 0)) == None \
            and (next_position + Vec3(0, 1, 0) not in agents_decisions):
            if world.get_entity(next_position + Vec3(0, 1, 0)) != None:
                possible_actions_list.append('MOVE_UP_TO_' + type(world.get_entity(next_position)).__name__)
            else:
                possible_actions_list.append(MOVE_UP)
        if world.get_static_block(next_position - Vec3(0, 2, 0)) != None \
            and world.get_static_block(next_position - Vec3(0, 1, 0)) == None \
            and world.get_static_block(next_position) == None \
            and world.get_static_block(next_position + Vec3(0, 1, 0)) == None \
            and (next_position - Vec3(0, 1, 0) not in agents_decisions):
            if world.get_entity(next_position - Vec3(0, 1, 0)) != None:
                possible_actions_list.append('MOVE_DOWN_TO_' + type(world.get_entity(next_position)).__name__)
            else:
                possible_actions_list.append(MOVE_DOWN)
        possible_actions_list.append(ROTATE_LEFT)
        possible_actions_list.append(ROTATE_RIGHT)
      
        return possible_actions_list
    
    def agentAhead(self, world):
        next_position = Vec3(self.position + self.Forward())
        return world.get_agent(next_position) != None

    # ================== Auxiliary Methods ==================

    def set_animation_duration(self, tick_time):
        self.animation_duration = animation_duration_tick_proportion * tick_time