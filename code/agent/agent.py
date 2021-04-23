import random
from ursina import *

animation_duration_tick_proportion = .2
char_texture = load_texture('textures/Char.png')

class Agent(Entity):
    def __init__(self, name = 'Unknown', model = 'textures/agent', position = (0, 1, 0), texture = char_texture, color = color.rgba(0,0,0), block_color = None, number_of_blocks = 0):
        super().__init__(
            name = 'Agent ' + name,
            model = model,
            texture = texture,
            position = Vec3(position),
            color = color,
            origin = Vec3(0, 1, 0)
        )

        self.animation_duration = animation_duration_tick_proportion
        self.block_color = block_color
        self.number_of_blocks = number_of_blocks
    
    def decision(self, world, agents_decisions):
        print("THIS AGENT HAS NO IMPLEMENTATION, PLEASE CREATE YOUR OWN!")
        return self.position
    
    # ============================ Actuators and Observations Methods ============================

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
        print('   - random choice of rotation')
        return random.choice([self.rotate_right, self.rotate_left])()

    def create_only(self, world):
        print('   - block created (ahead) at (x,y,z) = ' + str(tuple(self.position + self.Forward())))
        world.create_agent_block(self.position + self.Forward(), self.name, self.block_color)
        self.number_of_blocks -= 1
        return self.position

    def create_up(self, world):
        print('   - block created (top)) at (x,y,z) = ' + str(tuple(self.position + self.Forward() + Vec3(0,1,0))))
        world.create_agent_block(self.position + self.Forward() + Vec3(0,1,0), self.name, self.block_color)
        self.number_of_blocks -= 1
        return self.position
    
    def create_down(self, world):
        print('   - block created (bottom) at (x,y,z) = ' + str(tuple(self.position + self.Forward() - Vec3(0,1,0))))
        world.create_agent_block(self.position + self.Forward() - Vec3(0,1,0), self.name, self.block_color)
        self.number_of_blocks -= 1
        return self.position

    def break_only(self, world):
        print('   - block broken (ahead) at (x,y,z) = ' + str(tuple(self.position + self.Forward())))
        world.break_agent_block(self.position + self.Forward(), self.name)
        self.number_of_blocks += 1
        return self.position

    def break_up(self, world):
        print('   - block broken (top) at (x,y,z) = ' + str(tuple(self.position + self.Forward() + Vec3(0,1,0))))
        world.break_agent_block(self.position + self.Forward() + Vec3(0,1,0), self.name)
        self.number_of_blocks += 1
        return self.position

    def break_down(self, world):
        print('   - block broken (bottom) at (x,y,z) = ' + str(tuple(self.position + self.Forward() - Vec3(0,1,0))))
        world.break_agent_block(self.position + self.Forward() - Vec3(0,1,0), self.name)
        self.number_of_blocks += 1
        return self.position

    def agentAhead(self, world):
        next_position = Vec3(self.position + self.Forward())
        return world.get_agent(next_position) != None

    # ================== Auxiliary Methods ==================

    def Forward(self):
        return round(Vec3(self.forward))

    def set_animation_duration(self, tick_time):
        self.animation_duration = animation_duration_tick_proportion * tick_time