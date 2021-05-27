from ursina import *
from agent.agent import Agent
from export import export_module
import numpy as np
import random

# ============= ACTIONS VARIABLES =============
STAY = 0
MOVE = 1
ROTATE_LEFT = 2
ROTATE_RIGHT = 3
CREATE_BLOCK = 4
BREAK_BLOCK = 5

var_names = ['STAY', 'MOVE', 'ROTATE_LEFT', 'ROTATE_RIGHT', 'CREATE_BLOCK', 'BREAK_BLOCK']

class ReactiveAgent(Agent):
    def __init__(self, name = 'Unknown', position = (0, 1, 0), color = color.rgba(0,0,0), block_color = None, number_of_blocks = 0):
        super().__init__(
            name = name,
            position = position,
            color = color,
            block_color = block_color,
            number_of_blocks = number_of_blocks
        )
        self.count = 0
        self.forbidden_positions = []
        self.state = 'random'
        self.next_action = []

        self.create_block_position = None

        self.id_being_helped = None
        self.id_solving_message = None

        self.count_after_help = 0

    def decision(self, world, agents_decisions):
        self.count += 1
        height = 0
        current_position = self.position
        position_ahead = self.position + self.Forward()
        action = STAY
        while self.next_action:
            action = self.next_action.pop()    
            return self.take_action(action, world, height)

        self.check_if_message(world)
        self.check_messages(world)

        #to delete
        door_open = False
        for i in world.agents_map:
            if type(world.get_entity(world.agents_map[i].position)).__name__ == 'PressurePlate':
                door_open = True

        self.count_after_help += 1
        if self.isDoor(self.getEntityAhead(world)) and self.hasPermission(self.getEntityAhead(world)) and self.getEntityAhead(world).position not in self.forbidden_positions and (self.state == 'random' or self.state == 'door'):
            if self.state == 'random':
                self.send_message(world, position_ahead, 'pressure_plate', 'pressure_plate')
                self.count_after_help = 0
                self.state = 'door'
                action = STAY
            elif self.state == 'door' and not door_open:
                action = STAY
            elif self.state == 'door' and door_open:
                action = MOVE
                self.next_action.append(MOVE)
                self.solve_message(world)
                self.forbidden_positions.append(position_ahead)
        elif self.state == 'pressure_plate' and self.isPressurePlate(self.getEntityOfCurrentPosition(world)):
            action = STAY
        elif self.isWall(self.getBlockAhead(world)) and self.isWall(self.getBlockAhead_Up(world)) and self.isNone(self.getBlockAhead_Up_Up(world)) and self.hasPermission(self.getBlockAhead(world)) and self.state == 'random':
            self.send_message(world, current_position, 'create_block', 'create_block')
            self.count_after_help = 0
            self.state = 'wall'
        elif self.state == 'wall' and self.isAgentBlock(self.getBlockAhead(world)) and self.getBlockAhead(world).color == self.color:
            action = MOVE
            height = 1
            self.solve_message(world)
        elif self.state == 'create_block' and self.number_of_blocks > 0 and position_ahead == self.create_block_position and self.isNone(self.getBlockAhead(world)):
            action = CREATE_BLOCK
            self.number_of_blocks -= 1
        elif self.state == 'random' and self.isAgentBlock(self.getBlockAhead(world)) and self.getBlockAhead(world).color == self.color:
            action = MOVE
            height = 1
        elif self.state == 'random' and self.isOwnGoalBlock(self.getBlockOfCurrentPosition_Down(world)):
            action = STAY
        elif (self.state == 'door' or self.state == 'wall') and self.count_after_help == 500:
            self.solve_message(world)
        else:
            possible_actions_list, height = self.possible_actions(world, agents_decisions)
            action = random.choice(possible_actions_list)

        return self.take_action(action, world, height)
    
    def send_message(self, world, position, needed_action, text):
        m = world.send_message(self.name, position, needed_action, text)
        self.id_being_helped = m.getId()
    
    def check_messages(self, world):
        if self.id_being_helped != None or self.id_solving_message != None: return
        m = world.going_to_solve_older_message(self.name)
        if m == None: return
        self.id_solving_message = m.getId()
        self.state = m.getNeededAction()
        if self.state == 'create_block':
            self.create_block_position = m.getPosition()
    
    def check_if_message(self, world):
        if self.id_solving_message == None:
            return
        if self.id_solving_message != None and not world.is_message_being_solved(self.id_solving_message):
            self.id_solving_message = None
            self.state = 'random'
    
    def solve_message(self, world):
        world.solve_message(self.id_being_helped)
        self.id_being_helped = None
        self.state = 'random'

    def possible_actions(self, world, agents_decisions):
        height = 0
        possible_actions_list = []
        next_position = self.position + self.Forward()

        possible_actions_list.append(STAY)
        if self.position not in self.forbidden_positions:
            possible_actions_list.append(ROTATE_LEFT)
            possible_actions_list.append(ROTATE_RIGHT)
        
        if self.agentAhead(world) or (next_position in agents_decisions):
            return (possible_actions_list, height)
        
        #to delete
        door_open = False
        for i in world.agents_map:
            if self.isPressurePlate(world.get_entity(world.agents_map[i].position)):
                door_open = True

        if next_position not in self.forbidden_positions \
            and self.getBlockAhead_Down(world) != None \
            and self.getBlockAhead(world) == None \
            and self.getBlockAhead_Up(world) == None \
            and next_position not in agents_decisions \
            and (not self.isDoor(self.getEntityAhead(world)) or (self.isDoor(self.getEntityAhead(world)) and self.hasPermission(self.getEntityAhead(world)) and door_open)):
            if self.isAgentBlock(self.getBlockAhead_Down(world)) and self.getBlockAhead_Down(world).color == self.color:
                possible_actions_list.append(MOVE)
            elif not self.isAgentBlock(self.getBlockAhead_Down(world)):
                possible_actions_list.append(MOVE)

        elif next_position + Vec3(0, 1, 0) not in self.forbidden_positions \
            and self.getBlockAhead(world) != None \
            and self.getBlockAhead_Up(world) == None \
            and self.getBlockAhead_Up(world) == None \
            and next_position + Vec3(0, 1, 0) not in agents_decisions \
            and (not self.isDoor(self.getEntityAhead_Up(world)) or (self.isDoor(self.getEntityAhead_Up(world)) and self.hasPermission(self.getEntityAhead_Up(world)) and door_open)):
            if self.isAgentBlock(self.getBlockAhead(world)) and self.getBlockAhead(world).color == self.color:
                possible_actions_list.append(MOVE)
            elif not self.isAgentBlock(self.getBlockAhead(world)):
                possible_actions_list.append(MOVE)
            
            # up
            height += 1
        
        elif next_position - Vec3(0, 1, 0) not in self.forbidden_positions \
            and self.getBlockAhead_Down_Down(world) != None \
            and self.getBlockAhead_Down(world) == None \
            and self.getBlockAhead(world) == None \
            and self.getBlockAhead_Up(world) == None \
            and next_position - Vec3(0, 1, 0) not in agents_decisions \
            and (not self.isDoor(self.getEntityAhead_Down(world)) or (self.isDoor(self.getEntityAhead_Down(world)) and self.hasPermission(self.getEntityAhead_Down(world)) and door_open)):
            if self.isAgentBlock(self.getBlockAhead_Down_Down(world)) and self.getBlockAhead_Down_Down(world).color == self.color:
                possible_actions_list.append(MOVE)
            elif not self.isAgentBlock(self.getBlockAhead_Down_Down(world)):
                possible_actions_list.append(MOVE)

            # down
            height -= 1
      
        return (possible_actions_list, height)

    
    def take_action(self, a, world, height):
        if a == STAY:
            next_position = self.stay()
        elif a == MOVE and height == 0:
            next_position = self.move_only(world)
        elif a == MOVE and height == 1:
            next_position = self.move_up(world)
        elif a == MOVE and height == -1:
            next_position = self.move_down(world)
        elif a == ROTATE_LEFT:
            next_position = self.rotate_left()
        elif a == ROTATE_RIGHT:
            next_position = self.rotate_right()
        elif a == CREATE_BLOCK:
            next_position = self.create_block(world)
        elif a == BREAK_BLOCK:
            next_position = self.break_block(world)
        return next_position
    
    def print_export(self, world, possible_actions_list):
        export_module.print_and_write_to_txt(self.name + ':')
        export_module.print_and_write_to_txt('   - distance to goal: ' + str(world.distance_provider(self.name, self)))
        export_module.print_and_write_to_txt('   - possible actions: ' + str(possible_actions_list))