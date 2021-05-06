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

# =================== REWARD ==================
R_DOOR = 20
R_PRESSURE_PLATE = 20
R_WALL = 20
R_CREATE_BLOCK = 20

EPS = 1
LR = 0.2
GAMMA = 0.4


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
        self.id_being_helped = None
        self.id_solving_message = None

        self.Q = q_function
        self.eps = EPS
        self.lr = LR
        self.gamma = GAMMA

        self.rewards = rewards
        self.r_distance = True
        self.r_door = 0
        self.r_pressure_plate = 0
        self.r_wall = 0
        self.r_create_block = 0
        if self.rewards == 'door':
            self.r_door = R_DOOR
        elif self.rewards == 'pressure_plate':
            self.r_pressure_plate = R_PRESSURE_PLATE
        elif self.rewards == 'wall':
            self.r_wall = R_WALL
        elif self.rewards == 'create_block':
            self.r_create_block = R_CREATE_BLOCK
        
        self.obstacle_completed = 0
        self.forbidden_positions = []
        #self.forbidden_positions = [Vec3(-2, 1, 1)]

        self.count = 0
        self.count_positions = []

        self.printQFunction()

    def decision(self, world, agents_decisions):
        self.count += 1

        last_position = self.position
        current_position = self.position

        print(str(self.name) + ' - ' + str(last_position) + '; door = ' + str(type(world.get_entity(last_position)).__name__ == 'Door') + '; forbidden_positions = ' + str(self.forbidden_positions))
        print('          - lr = ' + str(self.lr))
        print('          - eps = ' + str(self.eps))

        self.check_messages(world)
        self.check_if_message(world)

        if self.id_being_helped == None and self.id_solving_message == None and (type(world.get_entity(last_position + self.Forward())).__name__ == 'Door') and (last_position + self.Forward() not in self.forbidden_positions):
            self.send_message(world, last_position + self.Forward(), 'pressure_plate', 'pressure_plate')
            return last_position
        elif self.id_being_helped == None and self.id_solving_message == None and (type(world.get_static_block(last_position + self.Forward())).__name__ == 'WallBlock') and (type(world.get_static_block(last_position + self.Forward() + Vec3(0, 1, 0))).__name__ == 'WallBlock') and (world.get_static_block(last_position + self.Forward() + Vec3(0, 2, 0)) == None):
            self.send_message(world, last_position + self.Forward(), 'create_block', 'create_block')
            return last_position

        if type(world.get_entity(last_position)).__name__ == 'Door':
            self.forbidden_positions.append(last_position)
            next_position = self.take_action(MOVE, world, 0)
            if self.r_door > 0:
                self.solve_message(world)
            print('          - next_position = ' + str(next_position))
            return next_position

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
        
        #####################
        #print(self.count)
        if self.count%3000 == 0:
            print()
            print()
            print()
            print(self.name)
            self.printQFunction()
            print(self.forbidden_positions)
            print(self.obstacle_completed)
            if self.name == 'Agent ORANGE':
                exit()
        #####################

        a = self.egreedy(self.Q[current_position], possible_actions_list, self.eps)
        #to delete
        door_open = False
        for i in world.agents_map:
            if type(world.get_entity(world.agents_map[i].position)).__name__ == 'PressurePlate':
                door_open = True
        
        n = None
        if a == MOVE and type(world.get_entity(last_position + self.Forward())).__name__ == 'Door' and not door_open:
            n = self.take_action(STAY, world, 0)
            next_position = last_position + self.Forward()
        else:
            next_position = self.take_action(a, world, height)

        next_distance_to_goal = world.distance_provider(self.name, Entity(next_position))
        reward = self.get_reward(world, last_position, next_position, distance_to_goal)

        q_next_position = (next_position[0], next_position[1], next_position[2], orientation)
        if q_next_position in self.Q:
            self.Q[current_position][a] += self.lr * (reward + self.gamma * np.max(self.Q[q_next_position]) - self.Q[current_position][a])
        else:
            self.Q[current_position][a] += self.lr * (reward - self.Q[current_position][a])
        
        #if self.count%1000 == 0:
        #    with open('Q-Function ' + self.name + '.pkl', 'wb') as f:
        #        pickle.dump(self.Q, f)
        
        if self.eps > 0.3:
            self.eps *= 0.999
        elif self.eps <= 0.3 and self.eps > 0.1:
            self.eps *= 0.99
        else:
            self.eps = 0.1
        
        #if self.lr > 0.2:
        #    self.lr *= 0.999
        #else:
        #    self.lr = 0.2
        
        self.printRewards()

        if n != None:
            return n
        else:
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
            r += self.r_pressure_plate
        if type(world.get_entity(last_position + self.Forward())).__name__ == 'PressurePlate':
            r += self.r_pressure_plate * 0.2
        elif type(world.get_entity(last_position)).__name__ == 'Door':
            r += self.r_door
        elif type(world.get_entity(last_position + self.Forward())).__name__ == 'Door':
            r += self.r_door * 0.2
        elif type(world.get_entity(last_position + self.Backward())).__name__ == 'Door' or \
             type(world.get_entity(last_position + self.Right())).__name__ == 'Door' or \
             type(world.get_entity(last_position + self.Left())).__name__ == 'Door':
            r += self.r_door * 0.1
        elif (type(world.get_entity(last_position + self.Forward())).__name__ == 'WallBlock' \
                and type(world.get_entity(last_position + self.Forward() + Vec3(0, 1, 0))).__name__ == 'WallBlock' \
                and world.get_entity(last_position + self.Forward() + Vec3(0, 2, 0)) == None) or \
            (type(world.get_entity(last_position + self.Backward())).__name__ == 'WallBlock' \
                and type(world.get_entity(last_position + self.Backward() + Vec3(0, 1, 0))).__name__ == 'WallBlock' \
                and world.get_entity(last_position + self.Backward() + Vec3(0, 2, 0)) == None) or \
            (type(world.get_entity(last_position + self.Right())).__name__ == 'WallBlock' \
                and type(world.get_entity(last_position + self.Right() + Vec3(0, 1, 0))).__name__ == 'WallBlock' \
                and world.get_entity(last_position + self.Right() + Vec3(0, 2, 0)) == None) or \
            (type(world.get_entity(last_position + self.Left())).__name__ == 'WallBlock' \
                and type(world.get_entity(last_position + self.Left() + Vec3(0, 1, 0))).__name__ == 'WallBlock' \
                and world.get_entity(last_position + self.Left() + Vec3(0, 2, 0)) == None):
            r += self.r_wall
        elif ((type(world.get_entity(last_position + self.Forward() + self.Forward())).__name__ == 'WallBlock' \
                and type(world.get_entity(last_position + self.Forward() + self.Forward() + Vec3(0, 1, 0))).__name__ == 'WallBlock' \
                and world.get_entity(last_position + self.Forward() + self.Forward() + Vec3(0, 2, 0)) == None) \
                or \
                (type(world.get_entity(last_position + self.Forward() + self.Right())).__name__ == 'WallBlock' \
                and type(world.get_entity(last_position + self.Forward() + self.Right() + Vec3(0, 1, 0))).__name__ == 'WallBlock' \
                and world.get_entity(last_position + self.Forward() + self.Right() + Vec3(0, 2, 0)) == None) \
                or \
                (type(world.get_entity(last_position + self.Forward() + self.Left())).__name__ == 'WallBlock' \
                and type(world.get_entity(last_position + self.Forward() + self.Left() + Vec3(0, 1, 0))).__name__ == 'WallBlock' \
                and world.get_entity(last_position + self.Forward() + self.Left() + Vec3(0, 2, 0)) == None)):
            r += self.r_create_block
        if self.r_distance:
            r += 1/distance_to_goal
        return r
    
    def send_message(self, world, position, needed_action, text):
        print()
        print()
        print(self.name)
        print("send")
        print()
        print()
        m = world.send_message(self.name, position, needed_action, text)
        self.id_being_helped = m.getId()
        self.clear_rewards()
        if needed_action == 'pressure_plate':
            self.r_door = R_DOOR
            self.r_distance = False
        elif needed_action == 'create_block':
            self.r_wall = R_WALL
            self.r_distance = False
        else:
            self.r_distance = True

    
    def check_messages(self, world):
        print("check")
        if self.id_being_helped != None or self.id_solving_message != None: return
        m = world.going_to_solve_older_message(self.name)
        if m == None: return
        self.id_solving_message = m.getId()
        a = m.getNeededAction()
        self.clear_rewards()
        print(m)
        print(m.getId())
        print(a)
        if a == 'pressure_plate':
            print('pressure_plate')
            self.r_pressure_plate = R_PRESSURE_PLATE
            self.r_distance = False
        elif a == 'create_block':
            print('crea_teblock')
            self.r_create_block = R_CREATE_BLOCK
            self.r_distance = False
        else:
            self.r_distance = True
        print(self.r_pressure_plate)
        print(self.name)
    
    def check_if_message(self, world):
        if self.id_solving_message == None:
            return
        print(1)
        print(self.id_solving_message)
        print(world.is_message_being_solved(self.id_solving_message))
        if self.id_solving_message != None and not world.is_message_being_solved(self.id_solving_message):
            print(2)
            self.id_solving_message = None
            self.clear_rewards()
        print(3)
    
    def solve_message(self, world):
        world.solve_message(self.id_being_helped)
        self.id_being_helped = None
        self.clear_rewards()
    
    def clear_rewards(self):
        self.r_distance = True
        self.r_door = 0
        self.r_pressure_plate = 0
        self.r_wall = 0
        self.r_create_block = 0
        self.eps = EPS
        self.lr = LR
        self.gamma = GAMMA
        self.Q = {}

    def init_rewards(self, reward_name):
        self.r_distance = False
        if reward_name == 'door':
            self.r_door = R_DOOR
        elif reward_name == 'pressure_plate':
            self.r_pressure_plate = R_PRESSURE_PLATE
        elif reward_name == 'wall':
            self.r_wall = R_WALL
        elif reward_name == 'create_block':
            self.r_create_block = R_CREATE_BLOCK
        self.eps = EPS
        self.lr = LR
        self.gamma = GAMMA
        self.Q = {}
    
    def reset_rewards(self):
        self.r_distance = True
        self.eps = EPS
        self.lr = LR
        self.gamma = GAMMA
        self.Q = {}

    def print_export(self, world, possible_actions_list):
        export_module.print_and_write_to_txt(self.name + ':')
        export_module.print_and_write_to_txt('   - distance to goal: ' + str(world.distance_provider(self.name, self)))
        export_module.print_and_write_to_txt('   - possible actions: ' + str(possible_actions_list))

    def possible_actions(self, world, agents_decisions):
        height = 0
        possible_actions_list = []
        next_position = self.position + self.Forward()

        if self.position not in self.forbidden_positions:
            possible_actions_list.append(STAY)
            possible_actions_list.append(ROTATE_LEFT)
            possible_actions_list.append(ROTATE_RIGHT)

        minus_2_block = world.get_static_block(next_position - Vec3(0, 2, 0))
        minus_1_block = world.get_static_block(next_position - Vec3(0, 1, 0))
        _0_block = world.get_static_block(next_position)
        _1_block = world.get_static_block(next_position + Vec3(0, 1, 0))
        _2_block = world.get_static_block(next_position + Vec3(0, 2, 0))
        
        if self.agentAhead(world) or (next_position in agents_decisions):
            #if self.number_of_blocks > 0 and self.r_create_block > 0:
            #    possible_actions_list.append(CREATE_BLOCK)
            #    self.agent_to_go_up = self.getAgentAhead(world)
            return (possible_actions_list, height)
        
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
            and ((type(world.get_entity(next_position)).__name__ != 'Door') or (type(world.get_entity(next_position)).__name__ == 'Door')):# and door_open)):#world.get_entity(next_position).isOpen())):
            if type(minus_1_block).__name__ == 'AgentBlock' and minus_1_block.color == self.color:
                possible_actions_list.append(MOVE)
            elif type(minus_1_block).__name__ != 'AgentBlock':
                possible_actions_list.append(MOVE)

        elif next_position + Vec3(0, 1, 0) not in self.forbidden_positions \
            and _0_block != None \
            and _1_block == None \
            and _2_block == None \
            and next_position + Vec3(0, 1, 0) not in agents_decisions \
            and ((type(world.get_entity(next_position + Vec3(0, 1, 0))).__name__ != 'Door') or (type(world.get_entity(next_position + Vec3(0, 1, 0))).__name__ == 'Door')):# and door_open)):# and world.get_entity(next_position + Vec3(0, 1, 0)).isOpen())):
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
            and ((type(world.get_entity(next_position - Vec3(0, 1, 0))).__name__ != 'Door') or (type(world.get_entity(next_position - Vec3(0, 1, 0))).__name__ == 'Door')):# and door_open)):# and world.get_entity(next_position - Vec3(0, 1, 0)).isOpen())):
            if type(minus_2_block).__name__ == 'AgentBlock' and minus_2_block == self.color:
                possible_actions_list.append(MOVE)
            elif type(minus_2_block).__name__ != 'AgentBlock':
                possible_actions_list.append(MOVE)

            # down
            height -= 1
        
        if self.number_of_blocks > 0 and _0_block == None and minus_1_block != None and self.r_create_block > 0:
            possible_actions_list.append(CREATE_BLOCK)

        if _0_block != None and type(_0_block).__name__ == 'AgentBlock' and _0_block.agent_name == self.name and world.get_entity(next_position + Vec3(0,1,0)) == None:
            possible_actions_list.append(BREAK_BLOCK)
      
        return (possible_actions_list, height)
    
    def change_rewards(self, rewards):
        self.eps = EPS
        self.lr = LR
        self.gamma = GAMMA
        self.Q = {}

        self.obstacle_completed += 1
        print()
        print()
        print('--- change rewards ---')
        print(self.name + '(' + str(self.position) + ') - obstacle - ' + str(self.obstacle_completed))
        print('----------------------')
        print()
        print()
        if self.obstacle_completed == 2:
            self.reset_rewards()
            #self.obstacle_completed = 0
            #self.r_door = 0
            #self.r_pressure_plate = 0
            # to change
            #if self.name == 'Agent BLUE':
            #    self.r_wall = R_WALL
            #    self.r_create_block = 0
            #else:
            #    self.r_wall = 0
            #    self.r_create_block = R_CREATE_BLOCK
            return
        if rewards == 'no_change':
            return
        self.rewards = rewards
        self.r_wall = 0
        if rewards == 'door_pressure_plate':
            if self.r_door == R_DOOR:
                self.r_door = 0
                self.r_pressure_plate = R_PRESSURE_PLATE
            elif self.r_pressure_plate == R_PRESSURE_PLATE:
                self.r_door = R_DOOR
                self.r_pressure_plate = 0

    def printQFunction(self):
        for key in self.Q:
            print()
            print(str(key[0]) + ', ' + str(key[2]) + ', ' + str(key[3]) + ':' )
            #print(str(key) + ':' )
            c = 0
            for i in range(len(self.Q[key])):
                if self.Q[key][i] > 0:
                    c += 1
                    print('    - ' + var_names[i] + ' = ' + str(self.Q[key][i]))
            if c == 0:
                print('    - no reward received yet')
    
    def printRewards(self):
        print('door - ', self.r_door)
        print('pressure plate - ', self.r_pressure_plate)
        print('wall - ', self.r_wall)
        print('create block - ', self.r_create_block)
    