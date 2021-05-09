import random
from ursina import *
from export import export_module

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
        self.agent_to_go_up = None
    
    def decision(self, world, agents_decisions):
        export_module.print_and_write_to_txt("THIS AGENT HAS NO IMPLEMENTATION, PLEASE CREATE YOUR OWN!")
        return self.position
    
    # ============================ Actuators and Observations Methods ============================

    def stay(self):
        export_module.print_and_write_to_txt('   - stayed')
        return self.position

    def move_only(self, world):
        export_module.print_and_write_to_txt('   - moved forward')
        final_position = self.position + self.Forward()
        world.update_agent(self.position, final_position)
        self.animate_position(final_position, curve=curve.linear, duration=self.animation_duration)
        return final_position
    
    def move_up(self, world):
        export_module.print_and_write_to_txt('   - jumped forward')
        final_position = self.position + self.Forward() + Vec3(0, 1, 0)
        world.update_agent(self.position, final_position)
        self.position = self.position + self.Forward() + Vec3(0, 1, 0)
        return final_position
    
    def move_down(self, world):
        export_module.print_and_write_to_txt('   - came down forward')
        final_position = self.position + self.Forward() - Vec3(0, 1, 0)
        world.update_agent(self.position, final_position)
        self.position = self.position + self.Forward() - Vec3(0, 1, 0)
        return final_position
    
    def rotate_right(self):
        export_module.print_and_write_to_txt('   - rotated to the right')
        self.animate_rotation(self.rotation + Vec3(0, 90, 0), curve=curve.linear, duration=self.animation_duration)
        return self.position
    
    def rotate_left(self):
        export_module.print_and_write_to_txt('   - rotated to the left')
        self.animate_rotation(self.rotation - Vec3(0, 90, 0), curve=curve.linear, duration=self.animation_duration)
        return self.position
    
    def rotate_randomly(self):
        export_module.print_and_write_to_txt('   - random choice of rotation')
        return random.choice([self.rotate_right, self.rotate_left])()

    def create_only(self, world):
        export_module.print_and_write_to_txt('   - block created (ahead) at (x,y,z) = ' + str(tuple(self.position + self.Forward())))
        world.create_agent_block(self.position + self.Forward(), self.name, self.block_color)
        self.number_of_blocks -= 1
        return self.position

    def create_up(self, world):
        export_module.print_and_write_to_txt('   - block created (top)) at (x,y,z) = ' + str(tuple(self.position + self.Forward() + Vec3(0,1,0))))
        world.create_agent_block(self.position + self.Forward() + Vec3(0,1,0), self.name, self.block_color)
        self.number_of_blocks -= 1
        return self.position
    
    def create_down(self, world):
        export_module.print_and_write_to_txt('   - block created (bottom) at (x,y,z) = ' + str(tuple(self.position + self.Forward() - Vec3(0,1,0))))
        world.create_agent_block(self.position + self.Forward() - Vec3(0,1,0), self.name, self.block_color)
        self.number_of_blocks -= 1
        return self.position

    def break_only(self, world):
        export_module.print_and_write_to_txt('   - block broken (ahead) at (x,y,z) = ' + str(tuple(self.position + self.Forward())))
        world.break_agent_block(self.position + self.Forward(), self.name)
        self.number_of_blocks += 1
        return self.position

    def break_up(self, world):
        export_module.print_and_write_to_txt('   - block broken (top) at (x,y,z) = ' + str(tuple(self.position + self.Forward() + Vec3(0,1,0))))
        world.break_agent_block(self.position + self.Forward() + Vec3(0,1,0), self.name)
        self.number_of_blocks += 1
        return self.position

    def break_down(self, world):
        export_module.print_and_write_to_txt('   - block broken (bottom) at (x,y,z) = ' + str(tuple(self.position + self.Forward() - Vec3(0,1,0))))
        world.break_agent_block(self.position + self.Forward() - Vec3(0,1,0), self.name)
        self.number_of_blocks += 1
        return self.position
    
    def create_block(self, world):
        export_module.print_and_write_to_txt('   - block created (ahead) at (x,y,z) = ' + str(tuple(self.position + self.Forward())))
        #export_module.print_and_write_to_txt('   - ' + self.agent_to_go_up.name + ' new position = ' + str(tuple(self.position + self.Forward() + Vec3(0, 1, 0))))
        world.create_agent_block(self.position + self.Forward(), self.name, self.block_color)
        self.number_of_blocks -= 1
        #self.agent_to_go_up.position += Vec3(0, 1, 0)
        return self.position
    
    def break_block(self, world):
        export_module.print_and_write_to_txt('   - block broken (ahead) at (x,y,z) = ' + str(tuple(self.position + self.Forward())))
        world.break_agent_block(self.position + self.Forward(), self.name)
        self.number_of_blocks += 1
        return self.position

    def agentAhead(self, world):
        next_position = Vec3(self.position + self.Forward())
        return world.get_agent(next_position) != None
    
    def getAgentAhead(self, world):
        next_position = Vec3(self.position + self.Forward())
        return world.get_agent(next_position)

    # ================== Auxiliary Methods ==================

    def Forward(self):
        return round(Vec3(self.forward))
    
    def Backward(self):
        return round(Vec3(self.back))
    
    def Right(self):
        return round(Vec3(self.right))
    
    def Left(self):
        return round(Vec3(self.left))
    
    def Up(self):
        return round(Vec3(self.up))
    
    def Down(self):
        return round(Vec3(self.down))

    def set_animation_duration(self, tick_time):
        self.animation_duration = animation_duration_tick_proportion * tick_time
    
    def typeOfBlock(self, block):
        return type(block).__name__
    
    def isNone(self, o):
        return o == None
    
    def isWall(self, block):
        return self.typeOfBlock(block) == 'WallBlock'
    
    def isAgentBlock(self, block):
        return self.typeOfBlock(block) == 'AgentBlock'
    
    def typeOfEntity(self, entity):
        return type(entity).__name__
    
    def isDoor(self, entity):
        return self.typeOfEntity(entity) == 'Door'
    
    def isPressurePlate(self, entity):
        return self.typeOfEntity(entity) == 'PressurePlate'
    
    # ================== Get Entities ==================

    def getEntityOfCurrentPosition(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position)

    def getEntityAhead(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward())
    
    def getEntityRight(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Right())
    
    def getEntityLeft(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Left())
    
    def getEntityBehind(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Backward())
    
    def getEntityUp(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Up())

    def getEntityDown(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Down())
    
    def getEntityUp_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Up() + self.Up())
    
    def getEntityDown_Down(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Down() + self.Down())
    
    def getEntityAhead_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward() + self.Up())
    
    def getEntityAhead_Up_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward() + self.Up() + self.Up())
    
    def getEntityAhead_Down(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward() + self.Down())
    
    def getEntityAhead_Down_Down(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward() + self.Down() + self.Down())
    
    def getEntityAhead_Ahead(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward() + self.Forward())
    
    def getEntityAhead_Right(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward() + self.Right())
    
    def getEntityAhead_Left(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward() + self.Left())
    
    def getEntityAhead_Right_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward() + self.Right() + self.Up())
    
    def getEntityAhead_Right_Up_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward() + self.Right() + self.Up() + self.Up())
    
    def getEntityAhead_Left_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward() + self.Left() + self.Up())
    
    def getEntityAhead_Left_Up_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward() + self.Left() + self.Up() + self.Up())
    
    def getEntityAhead_Ahead_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward() + self.Forward() + self.Up())
    
    def getEntityAhead_Ahead_Up_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward() + self.Forward() + self.Up() + self.Up())
    
    def getEntityAhead_Ahead_Down(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward() + self.Forward() + self.Down())
    
    def getEntityAhead_Ahead_Down_Down(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Forward() + self.Forward() + self.Down() + self.Down())
    
    def getEntityBehind_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Backward() + self.Up())
    
    def getEntityBehind_Up_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Backward() + self.Up() + self.Up())
    
    def getEntityBehind_Down(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Backward() + self.Down())
    
    def getEntityBehind_Down_Down(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Backward() + self.Down() + self.Down())
    
    def getEntityRight_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Right() + self.Up())
    
    def getEntityRight_Up_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Right() + self.Up() + self.Up())
    
    def getEntityLeft_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Left() + self.Up())
    
    def getEntityLeft_Up_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_entity(position + self.Left() + self.Up() + self.Up())
    
    # ================== Get Blocks ==================

    def getBlockOfCurrentPosition(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position)

    def getBlockAhead(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward())
    
    def getBlockRight(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Right())
    
    def getBlockLeft(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Left())
    
    def getBlockBehind(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Backward())
    
    def getBlockUp(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Up())

    def getBlockDown(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Down())
    
    def getBlockUp_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Up() + self.Up())
    
    def getBlockDown_Down(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Down() + self.Down())
    
    def getBlockAhead_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward() + self.Up())
    
    def getBlockAhead_Up_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward() + self.Up() + self.Up())
    
    def getBlockAhead_Down(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward() + self.Down())
    
    def getBlockAhead_Down_Down(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward() + self.Down() + self.Down())
    
    def getBlockAhead_Ahead(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward() + self.Forward())
    
    def getBlockAhead_Right(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward() + self.Right())
    
    def getBlockAhead_Left(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward() + self.Left())
    
    def getBlockAhead_Right_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward() + self.Right() + self.Up())
    
    def getBlockAhead_Right_Up_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward() + self.Right() + self.Up() + self.Up())
    
    def getBlockAhead_Left_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward() + self.Left() + self.Up())
    
    def getBlockAhead_Left_Up_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward() + self.Left() + self.Up() + self.Up())
    
    def getBlockAhead_Ahead_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward() + self.Forward() + self.Up())
    
    def getBlockAhead_Ahead_Up_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward() + self.Forward() + self.Up() + self.Up())
    
    def getBlockAhead_Ahead_Down(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward() + self.Forward() + self.Down())
    
    def getBlockAhead_Ahead_Down_Down(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Forward() + self.Forward() + self.Down() + self.Down())
    
    def getBlockBehind_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Backward() + self.Up())
    
    def getBlockBehind_Up_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Backward() + self.Up() + self.Up())
    
    def getBlockBehind_Down(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Backward() + self.Down())
    
    def getBlockBehind_Down_Down(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Backward() + self.Down() + self.Down())
    
    def getBlockRight_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Right() + self.Up())
    
    def getBlockRight_Up_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Right() + self.Up() + self.Up())
    
    def getBlockLeft_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Left() + self.Up())
    
    def getBlockLeft_Up_Up(self, world, position=None):
        if position == None: position = self.position
        return world.get_static_block(position + self.Left() + self.Up() + self.Up())
    

    def set_animation_duration(self, tick_time):
        self.animation_duration = animation_duration_tick_proportion * tick_time