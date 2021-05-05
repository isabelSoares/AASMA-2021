from ursina import *
from agent.agent import Agent
from export import export_module
import numpy as np
import pickle

# ============= ACTIONS VARIABLES =============
STAY = 0
MOVE = 1
ROTATE_LEFT = 2
ROTATE_RIGHT = 3
CREATE_BLOCK = 4
BREAK_BLOCK = 5

var_names = ['STAY', 'MOVE', 'ROTATE_LEFT', 'ROTATE_RIGHT', 'CREATE_BLOCK', 'BREAK_BLOCK']
#var_names = ['STAY', 'MOVE_ONLY', 'MOVE_UP', 'MOVE_DOWN', 'ROTATE_LEFT', 'ROTATE_RIGHT', 'MOVE_ONLY_TO_GOAL', 'MOVE_ONLY_TO_AGENT_BLOCK', 'MOVE_ONLY_TO_PressurePlate', 'MOVE_ONLY_TO_Door', 'MOVE_UP_TO_GOAL', 'MOVE_UP_TO_AGENT_BLOCK', 'MOVE_UP_TO_PressurePlate', 'MOVE_UP_TO_Door', 'MOVE_DOWN_TO_GOAL', 'MOVE_DOWN_TO_AGENT_BLOCK', 'MOVE_DOWN_TO_PressurePlate', 'MOVE_DOWN_TO_Door', 'CREATE_BLOCK', 'BREAK_BLOCK']

class RLearningAgent(Agent):
    def __init__(self, name = 'Unknown', position = (0, 1, 0), color = color.rgba(0,0,0), block_color = None, number_of_blocks = 0, q_function = {}, rewards = 'pressure_plate'):
        super().__init__(
            name = name,
            position = position,
            color = color,
            block_color = block_color,
            number_of_blocks = number_of_blocks
        )
        self.Q = q_function
        self.eps = 1
        self.lr = 0.3
        self.gamma = 0.6

        self.rewards = rewards
        self.r_door = 0
        self.r_pressure_plate = 0
        self.r_wall = 0
        if self.rewards == 'door':
            self.r_door = 20
        elif self.rewards == 'pressure_plate':
            self.r_pressure_plate = 20
        elif self.rewards == 'wall':
            self.r_wall = 20
        
        self.forbidden_positions = []

        self.count = 0
        self.count_positions = []

        self.printQFunction()

    def decision(self, world, agents_decisions):
        last_position = self.position
        current_position = self.position

        possible_actions_list, height = self.possible_actions(world, agents_decisions)
        distance_to_goal = world.distance_provider(self.name, self)

        export_module.print_and_write_to_txt(self.name + ':')
        export_module.print_and_write_to_txt('   - distance to goal: ' + str(distance_to_goal))
        export_module.print_and_write_to_txt('   - possible actions: ' + str(possible_actions_list))

        f = self.Forward()
        orientation = None
        if f == (1, 0, 0):
            orientation = 'NORTH'
        elif f == (-1, 0, 0):
            orientation = 'SOUTH'
        elif f == (0, 0, 1):
            orientation = 'WEST'
        elif f == (0, 0, -1):
            orientation = 'EAST'
        
        current_position = (current_position[0], current_position[1], current_position[2], orientation)

        if current_position not in self.Q:
            self.Q[current_position] = np.zeros(6)
        
        self.count += 1
        #self.count_positions.append(current_position)
        #if self.count%2000 == 0:
        #    self.printQFunction()
        #    exit()

        a = self.egreedy(self.Q[current_position], possible_actions_list, self.eps)
        next_position = self.take_action(a, world, height)

        next_distance_to_goal = world.distance_provider(self.name, Entity(next_position))
        reward = self.get_reward(world, last_position, next_position, next_distance_to_goal)

        q_next_position = (next_position[0], next_position[1], next_position[2], orientation)
        if q_next_position in self.Q:
            self.Q[current_position][a] += self.lr * (reward + self.gamma * np.max(self.Q[q_next_position]) - self.Q[current_position][a])
        else:
            self.Q[current_position][a] += self.lr * (reward - self.Q[current_position][a])
        
        if type(world.get_entity(last_position)).__name__ == 'Door' and next_distance_to_goal < distance_to_goal:
            self.forbidden_positions.append(last_position)
            return (next_position, "door_pressure_plate")
        
        #if self.count%1000 == 0:
        #    with open('Q-Function ' + self.name + '.pkl', 'wb') as f:
        #        pickle.dump(self.Q, f)
        
        if self.eps > 0.15:
            self.eps *= 0.999
        else:
            self.eps = 0.15
        print('door - ', self.r_door)
        print('prssure plate - ', self.r_pressure_plate)
        
        return next_position
    
    def egreedy(self, q, possible_actions, eps=0.1):
        s = np.array(list(map(q.__getitem__, possible_actions)))
        number_of_actions = len(s)
        return possible_actions[np.random.choice([np.random.randint(number_of_actions), np.random.choice(np.where(np.isclose(s, s.max()))[0])], p=[eps, 1-eps])]

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
    
    def get_reward(self, world, last_position, next_position, distance_to_goal):
        r = 0
        if type(world.get_entity(last_position)).__name__ == 'PressurePlate':
            r = self.r_pressure_plate
        if type(world.get_entity(last_position)).__name__ == 'PressurePlate' and type(world.get_entity(next_position)).__name__ == 'PressurePlate':
            r = self.r_pressure_plate * 2
        elif type(world.get_entity(last_position)).__name__ == 'Door':
            r = self.r_door
        elif type(world.get_entity(last_position + self.Forward())).__name__ == 'Door' or \
             type(world.get_entity(last_position + self.Backward())).__name__ == 'Door' or \
             type(world.get_entity(last_position + self.Right())).__name__ == 'Door' or \
             type(world.get_entity(last_position + self.Left())).__name__ == 'Door':
            r = self.r_door * 0.5
        return r + 1/distance_to_goal

    def init_rewards(self, rewards):
        self.r_door = rewards[0]
        self.r_pressure_plate = rewards[1]

    def print_export(self, world, possible_actions_list):
        export_module.print_and_write_to_txt(self.name + ':')
        export_module.print_and_write_to_txt('   - distance to goal: ' + str(world.distance_provider(self.name, self)))
        export_module.print_and_write_to_txt('   - possible actions: ' + str(possible_actions_list))

    def possible_actions(self, world, agents_decisions):
        height = 0
        possible_actions_list = []
        next_position = self.position + self.Forward()

        possible_actions_list.append(STAY)
        possible_actions_list.append(ROTATE_LEFT)
        possible_actions_list.append(ROTATE_RIGHT)

        minus_2_block = world.get_static_block(next_position - Vec3(0, 2, 0))
        minus_1_block = world.get_static_block(next_position - Vec3(0, 1, 0))
        _0_block = world.get_static_block(next_position)
        _1_block = world.get_static_block(next_position + Vec3(0, 1, 0))
        _2_block = world.get_static_block(next_position + Vec3(0, 2, 0))
        
        if self.agentAhead(world) or (next_position in agents_decisions):
            if self.number_of_blocks > 0:
                possible_actions_list.append(CREATE_BLOCK)
                self.agent_to_go_up = self.getAgentAhead(world)
            return (possible_actions_list, height)

        if type(world.get_entity(next_position)).__name__ == 'Door' and world.get_entity(next_position).isOpen():
            print()
            print()
            print(world.get_entity(next_position).isOpen())
            print()
            print()
            for a in world.agents_map:
                print(world.agents_map[a].position)
            #exit()
        
        #to delete
        door_open = False
        for i in world.agents_map:
            if type(world.get_entity(world.agents_map[i].position)).__name__ == 'PressurePlate':
                door_open = True

        if next_position not in self.forbidden_positions \
            and minus_1_block != None \
            and _0_block == None \
            and _1_block == None \
            and next_position not in agents_decisions \
            and ((type(world.get_entity(next_position)).__name__ != 'Door') or (type(world.get_entity(next_position)).__name__ == 'Door' and door_open)):#world.get_entity(next_position).isOpen())):
            if type(minus_1_block).__name__ == 'AgentBlock' and minus_1_block.color == self.color:
                possible_actions_list.append(MOVE)
            elif type(minus_1_block).__name__ != 'AgentBlock':
                possible_actions_list.append(MOVE)

        elif next_position + Vec3(0, 1, 0) not in self.forbidden_positions \
            and _0_block != None \
            and _1_block == None \
            and _2_block == None \
            and next_position + Vec3(0, 1, 0) not in agents_decisions \
            and ((type(world.get_entity(next_position + Vec3(0, 1, 0))).__name__ != 'Door') or (type(world.get_entity(next_position + Vec3(0, 1, 0))).__name__ == 'Door' and door_open)):# and world.get_entity(next_position + Vec3(0, 1, 0)).isOpen())):
            if type(_0_block).__name__ == 'AgentBlock' and _0_block.color == self.color:
                possible_actions_list.append(MOVE)
            elif type(_0_block).__name__ != 'AgentBlock':
                possible_actions_list.append(MOVE)
            
            # up
            height += 1
        elif next_position - Vec3(0, 1, 0) not in self.forbidden_positions \
            and minus_2_block != None \
            and minus_1_block == None \
            and _0_block == None \
            and _1_block == None \
            and next_position - Vec3(0, 1, 0) not in agents_decisions \
            and ((type(world.get_entity(next_position - Vec3(0, 1, 0))).__name__ != 'Door') or (type(world.get_entity(next_position - Vec3(0, 1, 0))).__name__ == 'Door' and door_open)):# and world.get_entity(next_position - Vec3(0, 1, 0)).isOpen())):
            if type(minus_2_block).__name__ == 'AgentBlock' and minus_2_block == self.color:
                possible_actions_list.append(MOVE)
            elif type(minus_2_block).__name__ != 'AgentBlock':
                possible_actions_list.append(MOVE)

            # down
            height -= 1

        if _0_block != None and type(_0_block).__name__ == 'AgentBlock' and _0_block.agent_name == self.name and world.get_entity(next_position + Vec3(0,1,0)) == None:
            possible_actions_list.append(BREAK_BLOCK)
      
        return (possible_actions_list, height)
    
    def change_rewards(self, rewards):
        if rewards == 'no_change':
            return
        self.rewards = rewards
        self.r_wall = 0
        if rewards == 'door_pressure_plate':
            if self.r_door == 20:
                self.r_door = 0
                self.r_pressure_plate = 20
            elif self.r_pressure_plate == 20:
                self.r_door = 20
                self.r_pressure_plate = 0
        elif rewards == 'wall':
            self.r_door = 0
            self.r_pressure_plate = 0
            self.r_wall = 20
        self.Q = {}

    
    def printQFunction(self):
        for key in self.Q:
            print()
            print(str(key) + ':' )
            for i in range(len(self.Q[key])):
                if self.Q[key][i] > 0:
                    print('    - ' + var_names[i] + ' = ' + str(self.Q[key][i]))
    