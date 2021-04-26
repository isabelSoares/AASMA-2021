from ursina import *
from agent.agent import Agent

# ============= ACTIONS VARIABLES =============
MOVE_ONLY = 'MOVE_ONLY'
MOVE_UP = 'MOVE_UP'
MOVE_DOWN = 'MOVE_DOWN'
ROTATE_LEFT = 'ROTATE_LEFT'
ROTATE_RIGHT = 'ROTATE_RIGHT'
MOVE_ONLY_TO_GOAL = 'MOVE_ONLY_TO_GOAL'
MOVE_ONLY_TO_AGENT_BLOCK = 'MOVE_ONLY_TO_AGENT_BLOCK'
MOVE_ONLY_TO_PRESSURE_PLATE = 'MOVE_ONLY_TO_PressurePlate'
MOVE_ONLY_TO_DOOR = 'MOVE_ONLY_TO_Door'
MOVE_UP_TO_GOAL = 'MOVE_UP_TO_GOAL'
MOVE_UP_TO_AGENT_BLOCK = 'MOVE_UP_TO_AGENT_BLOCK'
MOVE_UP_TO_PRESSURE_PLATE = 'MOVE_UP_TO_PressurePlate'
MOVE_UP_TO_DOOR = 'MOVE_UP_TO_Door'
MOVE_DOWN_TO_GOAL = 'MOVE_DOWN_TO_GOAL'
MOVE_DOWN_TO_AGENT_BLOCK = 'MOVE_DOWN_TO_AGENT_BLOCK'
MOVE_DOWN_TO_PRESSURE_PLATE = 'MOVE_DOWN_TO_PressurePlate'
MOVE_DOWN_TO_DOOR = 'MOVE_DOWN_TO_Door'
CREATE_ONLY_BLOCK = 'CREATE_ONLY_BLOCK'
CREATE_UP_BLOCK = 'CREATE_UP_BLOCK'
CREATE_DOWN_BLOCK = 'CREATE_DOWN_BLOCK'
BREAK_ONLY_BLOCK = 'BREAK_ONLY_BLOCK'
BREAK_UP_BLOCK = 'BREAK_UP_BLOCK'
BREAK_DOWN_BLOCK = 'BREAK_DOWN_BLOCK'

class RandomAgent(Agent):
    def __init__(self, name = 'Unknown', position = (0, 1, 0), color = color.rgba(0,0,0), block_color = None, number_of_blocks = 0):
        super().__init__(
            name = name,
            position = position,
            color = color,
            block_color = block_color,
            number_of_blocks = number_of_blocks
        )

    def decision(self, world, agents_decisions):
        last_position = self.position

        possible_actions_list = self.possible_actions(world, agents_decisions)
        print(self.name + ':')
        print('   - distance to goal: ' + str(world.distance_provider(self.name, self)))
        print('   - possible actions: ' + str(possible_actions_list))
        a = random.choice(possible_actions_list)
        if a == MOVE_ONLY or a == MOVE_ONLY_TO_PRESSURE_PLATE or a == MOVE_ONLY_TO_GOAL or a == MOVE_ONLY_TO_AGENT_BLOCK:
            next_position = self.move_only(world)
        elif a == MOVE_UP or a == MOVE_UP_TO_PRESSURE_PLATE or a == MOVE_UP_TO_GOAL or a == MOVE_UP_TO_AGENT_BLOCK:
            next_position = self.move_up(world)
        elif a == MOVE_DOWN or a == MOVE_DOWN_TO_PRESSURE_PLATE or a == MOVE_DOWN_TO_GOAL or a == MOVE_DOWN_TO_AGENT_BLOCK:
            next_position = self.move_down(world)
        elif a == ROTATE_LEFT:
            next_position = self.rotate_left()
        elif a == ROTATE_RIGHT:
            next_position = self.rotate_right()
        elif a == MOVE_ONLY_TO_DOOR:
            world.send_message(self.name, last_position, "OPEN DOOR", "find pressure plate")
            next_position = self.position
            print('   - \"There\'s a door here!\"')
        elif a == MOVE_UP_TO_DOOR:
            next_position = self.position
            print('   - \"There\'s a door here!\"')
        elif a == MOVE_DOWN_TO_DOOR:
            next_position = self.position
            print('   - \"There\'s a door here!\"')
        elif a == CREATE_ONLY_BLOCK:
            next_position = self.create_only(world)
        elif a == CREATE_UP_BLOCK:
            next_position = self.create_up(world)
        elif a == CREATE_DOWN_BLOCK:
            next_position = self.create_down(world)
        elif a == BREAK_ONLY_BLOCK:
            next_position = self.break_only(world)
        elif a == BREAK_UP_BLOCK:
            next_position = self.break_up(world)
        elif a == BREAK_DOWN_BLOCK:
            next_position = self.break_down(world)
        
        return next_position

    def possible_actions(self, world, agents_decisions):
        possible_actions_list = []
        next_position = self.position + self.Forward()
        if self.agentAhead(world) or (next_position in agents_decisions):
            return [ROTATE_LEFT, ROTATE_RIGHT]

        minus_2_block = world.get_static_block(next_position - Vec3(0, 2, 0))
        minus_1_block = world.get_static_block(next_position - Vec3(0, 1, 0))
        _0_block = world.get_static_block(next_position)
        _1_block = world.get_static_block(next_position + Vec3(0, 1, 0))
        _2_block = world.get_static_block(next_position + Vec3(0, 2, 0))

        if minus_1_block != None \
            and _0_block == None \
            and _1_block == None \
            and (next_position not in agents_decisions):
            if world.get_entity(next_position) != None:
                possible_actions_list.append('MOVE_ONLY_TO_' + type(world.get_entity(next_position)).__name__)
            elif type(minus_1_block).__name__ == 'WinningPostBlock':
                possible_actions_list.append(MOVE_ONLY_TO_GOAL)
            elif type(minus_1_block).__name__ == 'AgentBlock':
                if minus_1_block.color == self.color: possible_actions_list.append(MOVE_ONLY_TO_AGENT_BLOCK)
            else:
                possible_actions_list.append(MOVE_ONLY)
        if _0_block != None \
            and _1_block == None \
            and _2_block == None \
            and (next_position + Vec3(0, 1, 0) not in agents_decisions):
            if world.get_entity(next_position + Vec3(0, 1, 0)) != None:
                possible_actions_list.append('MOVE_UP_TO_' + type(world.get_entity(next_position + Vec3(0, 1, 0))).__name__)
            elif type(_0_block).__name__ == 'WinningPostBlock':
                possible_actions_list.append(MOVE_UP_TO_GOAL)
            elif type(_0_block).__name__ == 'AgentBlock':
                if _0_block.color == self.color: possible_actions_list.append(MOVE_UP_TO_AGENT_BLOCK)
            else:
                possible_actions_list.append(MOVE_UP)
        if minus_2_block != None \
            and minus_1_block == None \
            and _0_block == None \
            and _1_block == None \
            and (next_position - Vec3(0, 1, 0) not in agents_decisions):
            if world.get_entity(next_position - Vec3(0, 1, 0)) != None:
                possible_actions_list.append('MOVE_DOWN_TO_' + type(world.get_entity(next_position - Vec3(0, 1, 0))).__name__)
            elif type(minus_2_block).__name__ == 'WinningPostBlock':
                possible_actions_list.append(MOVE_DOWN_TO_GOAL)
            elif type(minus_2_block).__name__ == 'AgentBlock':
                if minus_2_block.color == self.color: possible_actions_list.append(MOVE_DOWN_TO_AGENT_BLOCK)
            else:
                possible_actions_list.append(MOVE_DOWN)

        if self.number_of_blocks > 0 and minus_1_block == None and _0_block == None:
            possible_actions_list.append(CREATE_DOWN_BLOCK)
        if self.number_of_blocks > 0 and _0_block == None and minus_1_block != None:
            possible_actions_list.append(CREATE_ONLY_BLOCK)
        if self.number_of_blocks > 0 and _1_block == None and _0_block != None:
            possible_actions_list.append(CREATE_UP_BLOCK)

        if minus_1_block != None and type(minus_1_block).__name__ == 'AgentBlock' and minus_1_block.agent_name == self.name and world.get_entity(next_position) == None:
            possible_actions_list.append(BREAK_DOWN_BLOCK)
        if _0_block != None and type(_0_block).__name__ == 'AgentBlock' and _0_block.agent_name == self.name and world.get_entity(next_position + Vec3(0,1,0)) == None:
            possible_actions_list.append(BREAK_ONLY_BLOCK)
        if _1_block != None and type(_1_block).__name__ == 'AgentBlock' and _1_block.agent_name == self.name and world.get_entity(next_position + Vec3(0,2,0)) == None:
            possible_actions_list.append(BREAK_UP_BLOCK)

        possible_actions_list.append(ROTATE_LEFT)
        possible_actions_list.append(ROTATE_RIGHT)
      
        return possible_actions_list
    