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
R_DOOR = 1
R_PRESSURE_PLATE = 1
R_WALL = 1
R_CREATE_BLOCK = 1

EPS = 1
LR = 0.9
GAMMA = 0.6
LR_DOOR = 0.4
GAMMA_DOOR = 0.9
LR_WALL = 0.4
GAMMA_WALL = 0.9


var_names = ['STAY', 'MOVE', 'ROTATE_LEFT', 'ROTATE_RIGHT', 'CREATE_BLOCK', 'BREAK_BLOCK']

class RLearningAgent(Agent):
    def __init__(self, name = 'Unknown', position = (0, 1, 0), color = color.rgba(0,0,0), block_color = None, number_of_blocks = 0, q_function = {}):
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

        self.r_distance = True
        self.r_door = 0
        self.r_pressure_plate = 0
        self.r_wall = 0
        self.r_create_block = 0
        self.create_block_y = None
        
        self.obstacle_completed = 0
        self.forbidden_positions = []
        self.unbreakable_blocks = []

        self.count = 0
        self.count_positions = []

    def decision(self, world, agents_decisions):
        self.count += 1

        last_position = self.position
        current_position = self.position

        print(str(self.name) + ' - ' + str(last_position) + '; forbidden_positions = ' + str(self.forbidden_positions))
        print('          - lr = ' + str(self.lr))
        print('          - eps = ' + str(self.eps))
        print()

        print("EPS = ", self.eps)
        print("LR = ", self.lr)
        print("GAMMA = ", self.gamma)
        print("create_block_y = ", self.create_block_y)
        print()

        self.check_messages(world)
        self.check_if_message(world)

        if self.id_being_helped == None and self.id_solving_message == None and self.isDoor(self.getEntityAhead(world)) and self.hasPermission(self.getEntityAhead(world)) and (last_position + self.Forward() not in self.forbidden_positions):
            self.send_message(world, last_position + self.Forward(), 'pressure_plate', 'pressure_plate')
            return last_position
        elif self.id_being_helped == None and self.id_solving_message == None and self.isWall(self.getBlockAhead(world)) and self.hasPermission(self.getBlockAhead(world)) and self.isWall(self.getBlockAhead_Up(world)) and self.isNone(self.getBlockAhead_Up_Up(world)):
            self.send_message(world, last_position + self.Forward(), 'create_block', 'create_block')
            return last_position

        if self.isDoor(self.getEntityOfCurrentPosition(world)):
            self.forbidden_positions.append(last_position)
            next_position = self.take_action(MOVE, world, 0)
            if self.r_door > 0:
                self.solve_message(world)
            return next_position

        if (last_position + self.Backward() - Vec3(0, 2, 0)) not in self.unbreakable_blocks and self.isNone(self.getBlockBehind(world)) and self.isNone(self.getBlockBehind_Down(world)) and self.isAgentBlock(self.getBlockBehind_Down_Down(world)):
            world.send_info_message(self.name, last_position + self.Backward() - Vec3(0, 2, 0), 'unbreakable_block', 'unbreakable_block')
            self.unbreakable_blocks.append(last_position + self.Backward() - Vec3(0, 2, 0))
            if self.r_wall > 0:
                self.solve_message(world)

        possible_actions_list, height = self.possible_actions(world, agents_decisions)

        distance_to_goal = world.distance_provider(self.name, self)

        export_module.print_and_write_to_txt(self.name + ':')
        export_module.print_and_write_to_txt('   - distance to goal: ' + str(distance_to_goal))
        export_module.print_and_write_to_txt('   - possible actions: ' + str(possible_actions_list))

        orientation = self.getOrientation()
        
        current_position = (current_position[0], current_position[1], current_position[2], orientation)

        if current_position not in self.Q:
            self.Q[current_position] = np.zeros(6)

        a = self.egreedy(self.Q[current_position], possible_actions_list, self.eps)

        #to test
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

        reward = self.get_reward(world, last_position, next_position, distance_to_goal)

        q_next_position = (next_position[0], next_position[1], next_position[2], orientation)
        if q_next_position in self.Q:
            self.Q[current_position][a] += self.lr * (reward + self.gamma * np.max(self.Q[q_next_position]) - self.Q[current_position][a])
        else:
            self.Q[current_position][a] += self.lr * (reward - self.Q[current_position][a])
        
        #self.writeQfunction()

        self.updateEPS()
        #self.updateLR()
        
        self.printRewards()

        if n != None:
            return n
        else:
            return next_position
    
    def egreedy(self, q, possible_actions, eps=0.1):
        s = np.array(list(map(q.__getitem__, possible_actions)))
        number_of_actions = len(s)
        return possible_actions[np.random.choice([np.random.randint(number_of_actions), np.random.choice(np.where(np.isclose(s, s.max()))[0])], p=[eps, 1-eps])]
    
    def get_reward(self, world, last_position, next_position, distance_to_goal):
        r = 0
        if self.isPressurePlate(self.getEntityOfCurrentPosition(world, last_position)):
            r += self.r_pressure_plate
        elif self.isDoor(self.getEntityOfCurrentPosition(world, next_position)) and self.hasPermission(self.getEntityOfCurrentPosition(world, next_position)):
            r += self.r_door
        elif self.isDoor(self.getEntityAhead(world, last_position)) and self.hasPermission(self.getEntityAhead(world, last_position)):
            r += self.r_door * 0.2
        elif (self.isDoor(self.getEntityBehind(world, last_position)) and self.hasPermission(self.getEntityBehind(world, last_position))) or \
             (self.isDoor(self.getEntityRight(world, last_position)) and self.hasPermission(self.getEntityRight(world, last_position))) or \
             (self.isDoor(self.getEntityLeft(world, last_position)) and self.hasPermission(self.getEntityLeft(world, last_position))):
            r += self.r_door * 0.1
        elif (self.isWall(self.getBlockAhead(world, last_position)) \
                and self.hasPermission(self.getBlockAhead(world, last_position)) \
                and self.isWall(self.getBlockAhead_Up(world, last_position)) \
                and self.isNone(self.getBlockAhead_Up_Up(world, last_position))) or \
             (self.isWall(self.getBlockBehind(world, last_position)) \
                and self.hasPermission(self.getBlockBehind(world, last_position)) \
                and self.isWall(self.getBlockBehind_Up(world, last_position)) \
                and self.isNone(self.getBlockBehind_Up_Up(world, last_position))) or \
             (self.isWall(self.getBlockRight(world, last_position)) \
                and self.hasPermission(self.getBlockRight(world, last_position)) \
                and self.isWall(self.getBlockRight_Up(world, last_position)) \
                and self.isNone(self.getBlockRight_Up_Up(world, last_position))) or \
             (self.isWall(self.getBlockLeft(world, last_position)) \
                and self.hasPermission(self.getBlockLeft(world, last_position)) \
                and self.isWall(self.getBlockLeft_Up(world, last_position)) \
                and self.isNone(self.getBlockLeft_Up_Up(world, last_position))):
            r += self.r_wall
        elif (self.isWall(self.getBlockAhead_Ahead(world, last_position)) \
                and self.hasPermission(self.getBlockAhead_Ahead(world, last_position)) \
                and self.isWall(self.getBlockAhead_Ahead_Up(world, last_position)) \
                and self.isNone(self.getBlockAhead_Ahead_Up_Up(world, last_position))) \
                or \
                (self.isWall(self.getBlockAhead_Right(world, last_position)) \
                and self.hasPermission(self.getBlockAhead_Right(world, last_position)) \
                and self.isWall(self.getBlockAhead_Right_Up(world, last_position)) \
                and self.isNone(self.getBlockAhead_Right_Up_Up(world, last_position))) \
                or \
                (self.isWall(self.getBlockAhead_Left(world, last_position)) \
                and self.hasPermission(self.getBlockAhead_Left(world, last_position)) \
                and self.isWall(self.getBlockAhead_Left_Up(world, last_position)) \
                and self.isNone(self.getBlockAhead_Left_Up_Up(world, last_position))):
            r += self.r_create_block
        if self.r_distance:
            r += 1/distance_to_goal
        return r
    
    def updateEPS(self):
        if self.eps > 0.8:
            self.eps *= 0.9999
        elif self.eps <= 0.8 and self.eps > 0.3:
            self.eps *= 0.9
        elif self.eps <= 0.3 and self.eps > 0.2:
            self.eps *= 0.9999
        else:
            self.eps = 0.2
    
    def updateLR(self):
        if self.lr > 0.97:
            self.lr *= 0.9999
        elif self.lr <= 0.97 and self.lr > 0.7:
            self.lr *= 0.9
        elif self.lr <= 0.7 and self.lr > 0.5:
            self.lr *= 0.9999
        else:
            self.lr = 0.4
    
    def send_message(self, world, position, needed_action, text):
        m = world.send_message(self.name, position, needed_action, text)
        self.id_being_helped = m.getId()
        self.clear_rewards()
        if needed_action == 'pressure_plate':
            self.r_door = R_DOOR
            self.r_distance = False
            self.lr = LR_DOOR
            self.gamma = GAMMA_DOOR
        elif needed_action == 'create_block':
            self.r_wall = R_WALL
            self.r_distance = False
            self.lr = LR_WALL
            self.gamma = GAMMA_WALL
        else:
            self.r_distance = True

    
    def check_messages(self, world):
        info = world.get_info_message()
        if info != None and info.getNeededAction() == 'unbreakable_block':
            self.unbreakable_blocks.append(info.getPosition())
        if self.id_being_helped != None or self.id_solving_message != None: return
        m = world.going_to_solve_older_message(self.name)
        if m == None: return
        self.id_solving_message = m.getId()
        a = m.getNeededAction()
        self.clear_rewards()

        if a == 'pressure_plate':
            self.r_pressure_plate = R_PRESSURE_PLATE
            self.r_distance = False
            self.lr = LR_DOOR
            self.gamma = GAMMA_DOOR
        elif a == 'create_block':
            self.create_block_y = m.getPosition()[1]
            self.r_create_block = R_CREATE_BLOCK
            self.r_distance = False
            self.lr = LR_WALL
            self.gamma = GAMMA_WALL
        else:
            self.r_distance = True
    
    def check_if_message(self, world):
        if self.id_solving_message == None:
            return
        if self.id_solving_message != None and not world.is_message_being_solved(self.id_solving_message):
            self.id_solving_message = None
            self.clear_rewards()
    
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
        self.create_block_y = None
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
        
        if self.agentAhead(world) or (next_position in agents_decisions):
            return (possible_actions_list, height)
        
        #to test
        door_open = False
        for i in world.agents_map:
            if self.isPressurePlate(world.get_entity(world.agents_map[i].position)):
                door_open = True

        if next_position not in self.forbidden_positions \
            and self.getBlockAhead_Down(world) != None \
            and self.getBlockAhead(world) == None \
            and self.getBlockAhead_Up(world) == None \
            and next_position not in agents_decisions \
            and (not self.isDoor(self.getEntityAhead(world)) or (self.isDoor(self.getEntityAhead(world)) and self.hasPermission(self.getEntityAhead(world)))):
            if self.isAgentBlock(self.getBlockAhead_Down(world)) and self.getBlockAhead_Down(world).color == self.color:
                possible_actions_list.append(MOVE)
            elif not self.isAgentBlock(self.getBlockAhead_Down(world)):
                possible_actions_list.append(MOVE)

        elif (self.r_create_block <= 0 or (next_position + Vec3(0, 1, 0))[1] == self.create_block_y) \
            and next_position + Vec3(0, 1, 0) not in self.forbidden_positions \
            and self.getBlockAhead(world) != None \
            and self.getBlockAhead_Up(world) == None \
            and self.getBlockAhead_Up(world) == None \
            and next_position + Vec3(0, 1, 0) not in agents_decisions \
            and (not self.isDoor(self.getEntityAhead_Up(world)) or (self.isDoor(self.getEntityAhead_Up(world)) and self.hasPermission(self.getEntityAhead_Up(world)))):
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
            and (not self.isDoor(self.getEntityAhead_Down(world)) or (self.isDoor(self.getEntityAhead_Down(world)) and self.hasPermission(self.getEntityAhead_Down(world)))):
            if self.isAgentBlock(self.getBlockAhead_Down_Down(world)) and self.getBlockAhead_Down_Down(world).color == self.color:
                possible_actions_list.append(MOVE)
            elif not self.isAgentBlock(self.getBlockAhead_Down_Down(world)):
                possible_actions_list.append(MOVE)

            # down
            height -= 1
        
        if self.isWall(self.getBlockAhead_Ahead(world)) and self.number_of_blocks > 0 and self.getBlockAhead(world) == None and self.getBlockAhead_Down(world) != None and self.r_create_block > 0:
            possible_actions_list.append(CREATE_BLOCK)

        if self.getBlockAhead(world) != None and self.isAgentBlock(self.getBlockAhead(world)) and (self.getBlockAhead(world).position not in self.unbreakable_blocks) and self.getBlockAhead(world).agent_name == self.name and self.isNone(self.getEntityAhead_Up(world)):
            possible_actions_list.append(BREAK_BLOCK)
      
        return (possible_actions_list, height)

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
    
    def getOrientation(self):
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
        return orientation
    
    def writeQfunction(self):
        if self.count%1000 == 0:
            with open('Q-Function ' + self.name + '.pkl', 'wb') as f:
                pickle.dump(self.Q, f)
    