from ursina import *
from export import export_module
from scipy import spatial

import sys
import copy
import math
import random

from agent.layers.Layer import Layer
from agent.layers.Layer import LayerMemory

# Import Message Type
from agent.layers.Message import Message
from agent.layers.Message import MessageType
from agent.layers.Message import MessageDirection

# ============= ACTIONS VARIABLES =============
MOVE_ONLY = 'MOVE_ONLY'
MOVE_UP = 'MOVE_UP'
MOVE_DOWN = 'MOVE_DOWN'
ROTATE_LEFT = 'ROTATE_LEFT'
ROTATE_RIGHT = 'ROTATE_RIGHT'
CREATE_ONLY_BLOCK = 'CREATE_ONLY_BLOCK'
CREATE_UP_BLOCK = 'CREATE_UP_BLOCK'
CREATE_DOWN_BLOCK = 'CREATE_DOWN_BLOCK'
BREAK_ONLY_BLOCK = 'BREAK_ONLY_BLOCK'
BREAK_UP_BLOCK = 'BREAK_UP_BLOCK'
BREAK_DOWN_BLOCK = 'BREAK_DOWN_BLOCK'

# ============= DESIRES VARIABLES =============
REACH_GOAL = 'REACH_GOAL'
OPEN_DOOR = 'OPEN_DOOR'
OPEN_DOOR_BACK = 'OPEN_DOOR_BACK'
PLACE_BLOCK = 'PLACE_BLOCK'
BREAK_BLOCK = 'BREAK_BLOCK'
REACH_POSITION = 'REACH_POSITION'
EXPLORE_UNKNOWN = 'EXPLORE_UNKNOWN'
ROAM_AROUND = 'ROAM_AROUND'
STAY_STILL = 'STAY_STILL'

# ============= PRE-DEFINED CONSTANTS =============
RECONSIDER_CHANCE = 0.05
PATH_CHECK_DEPT = -1
BELIEF_STUCK_THRESHOLD = 20
COSSINE_DOOR_AGENT = 0.5

# ============= VALID MOVEMENT POSITIONS AND DIRECTIONS =============
MOVE_POSITIONS = (
    (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1),
    (1, -1, 0), (-1, -1, 0), (0, -1, 1), (0, -1, -1),
    (1, 1, 0), (-1, 1, 0), (0, 1, 1), (0, 1, -1),
    (1, 2, 0), (-1, 2, 0), (0, 2, 1), (0, 2, -1),
    (1, -2, 0), (-1, -2, 0), (0, -2, 1), (0, -2, -1),
)

BREAK_BLOCK_POSITIONS = (
    (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1),
    (1, -1, 0), (-1, -1, 0), (0, -1, 1), (0, -1, -1),
    (1, 1, 0), (-1, 1, 0), (0, 1, 1), (0, 1, -1),
)

DIRECTIONS = ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1))

class Belief():
    def __init__(self, block, agent, entity):
        self.block = block
        self.agent = agent
        self.entity = entity

class Intention():
    def __init__(self, desire, position):
        self.desire = desire
        self.position = position

class DeliberativeMemory(LayerMemory):
    def __init__(self):
        super()

        # Beliefs
        self.belief_name = ""
        self.belief_color = None
        self.belief_last_position = None
        self.belief_current_position = None
        self.belief_forward = None
        self.belief_number_blocks = 0
        self.beliefs = {}
        self.goal_beliefs = set()
        self.beliefs_agents_saw = []
        # For it to roam around
        self.belief_stuck = False
        self.belief_stuck_threshold = BELIEF_STUCK_THRESHOLD
        # Cooperation beliefs
        self.belief_door_to_open = None
        self.belief_block_to_place = None
        self.belief_block_to_break = None

        # To pass to Communication Layer
        self.door_to_pass = None
        self.wall_to_pass = None
        self.block_to_break = None
        self.already_asked_for_help = False
        self.infos_to_transmit = []

        self.desires = []
        self.intention = None
        self.plan = []

        self.chosen_action = None

    def beliefs_memory_update(self, percepts):
        name = percepts['name']
        self.belief_name = name
        color = percepts['color']
        self.belief_color = color
        current_position = percepts['current position']
        self.belief_last_position = self.belief_current_position
        self.belief_current_position = current_position
        forward = percepts['forward']
        self.belief_forward = forward
        number_of_blocks = percepts['number of blocks']
        self.belief_number_blocks = number_of_blocks
        self.beliefs_agents_saw = []

        # Update stuck belief
        if self.belief_last_position == self.belief_current_position: self.belief_stuck_threshold = self.belief_stuck_threshold - 1
        else: self.belief_stuck_threshold = BELIEF_STUCK_THRESHOLD
        self.belief_stuck = self.belief_stuck_threshold < 0

        # Update goal block belief
        distance = percepts['goal distance']
        lower_bound, upper_bound = math.floor(distance), math.ceil(distance)
        if (len(self.goal_beliefs) == 0):
            for x in range(-upper_bound, upper_bound + 1):
                for y in range(-upper_bound, upper_bound + 1):
                    for z in range(-upper_bound, upper_bound + 1):

                        check_position = sum_positions(current_position, (x, y, z))
                        check_position = convert_vec3_to_key(check_position)

                        distance = ursinamath.distance(current_position, check_position)
                        if (lower_bound <= distance and distance <= upper_bound): self.goal_beliefs.add(check_position)
        elif (len(self.goal_beliefs) > 1):
            to_remove = set()
            for check_position in self.goal_beliefs:
                distance_to_position = ursinamath.distance(current_position, check_position)
                if not(lower_bound <= distance_to_position and distance_to_position <= upper_bound): to_remove.add(check_position)

            self.goal_beliefs = self.goal_beliefs - to_remove

        # Update 3 x 3 around
        percepts_around = percepts['around']
        for key_position in percepts_around:
            check_position = sum_positions(current_position, key_position)

            # Update belief
            percept = percepts_around[key_position]
            block = percept['block']
            agent = percept['agent']
            entity = percept['entity']
            belief_to_update = Belief(block, agent, entity)

            # If agent was seen clear agent from any other belief
            if agent != None:
                self.beliefs_agents_saw.append(agent.name)
                for belief_position in self.beliefs:
                    belief = self.beliefs[belief_position]
                    if belief.agent and belief.agent.name == agent.name:
                        belief.agent = None

            # Check if agent disappeared from view
            if check_position in self.beliefs:
                previous_belief = self.beliefs[check_position]
                if previous_belief.agent != None and (agent == None or agent.name != previous_belief.agent.name):
                    agent_forward = convert_vec3_to_key(previous_belief.agent.Forward())
                    new_position_agent = sum_positions(check_position, agent_forward)
                    if new_position_agent in self.beliefs:
                        belief_stored = self.beliefs[new_position_agent]
                        belief_stored.agent = previous_belief.agent
                        self.beliefs[new_position_agent] = belief_stored
                    else:
                        new_belief_to_store = Belief(None, previous_belief.agent, None)
                        self.beliefs[new_position_agent] = new_belief_to_store

            self.beliefs[check_position] = belief_to_update

            # If it is its own goal save it as so
            if type(block).__name__ == "WinningPostBlock" and block.getAgentName() == self.belief_name.replace("Agent ", ""):
                self.goal_beliefs = set([check_position])

            # Create Messages to be transmitted 
            if entity != None: self.infos_to_transmit.append({'type': "entity", 'position': check_position, 'belief': entity})
            if agent != None and agent.name == self.belief_name: self.infos_to_transmit.append({'type': "agent", 'position': check_position, 'belief': agent})
            if type(block).__name__ == "AgentBlock": self.infos_to_transmit.append({ 'type': "block", 'position': check_position, 'belief': block })
            if type(block).__name__ == "WinningPostBlock": self.infos_to_transmit.append({ 'type': "goal", 'position': check_position, 'belief': block })

    def has_belief(self, position):
        return position in self.beliefs

    def desires_update(self):
        self.desires = [REACH_GOAL]

        # Wants door open?
        if self.belief_door_to_open != None: self.desires.append(OPEN_DOOR)
        # Wants place block?
        if self.belief_block_to_place != None: self.desires.append(PLACE_BLOCK)
        # Wants break block?
        if self.belief_block_to_break != None: self.desires.append(BREAK_BLOCK)
        # Wants to Roam Around
        if self.belief_stuck: self.desires.append(ROAM_AROUND)
    
    def intention_update(self):
        focused_desire = self.desires[-1]
        
        if focused_desire == REACH_GOAL:
            goal_possibility = random.sample(self.goal_beliefs, 1)[0]
            objective_position = sum_positions(goal_possibility, (0, 1, 0))

            self.intention = Intention(focused_desire, objective_position)

        elif focused_desire == OPEN_DOOR:
            pressure_plate_position = self.pressure_plate_to_open(focused_desire)
            self.intention = Intention(focused_desire, pressure_plate_position)

        elif focused_desire == PLACE_BLOCK:
            self.intention = Intention(focused_desire, self.belief_block_to_place)

        elif focused_desire == BREAK_BLOCK:
            self.intention = Intention(focused_desire, self.belief_block_to_break)

        elif focused_desire == ROAM_AROUND:
            self.intention = Intention(focused_desire, None)

    def check_for_helps(self, path_positions):

        found_door = False
        for path_position in path_positions:
            # If not in belief no help
            if path_position not in self.beliefs: continue
            belief = self.beliefs[path_position]

            # Check whether needs to go through door
            if type(belief.entity).__name__ == "Door" and not belief.entity.state:
                found_door = True
                self.door_to_pass = path_position

        found_wall_to_climb = False
        if len(path_positions) >= 2:
            for i in range(1, len(path_positions)):
                from_position = path_positions[i - 1]
                to_position = path_positions[i]

                height_diff = to_position[1] - from_position[1]
                if height_diff == 2:
                    found_wall_to_climb = True
                    self.wall_to_pass = from_position
                elif height_diff == -2:
                    found_wall_to_climb = True
                    self.wall_to_pass = to_position
        
        found_block_to_break = False
        for path_position in path_positions:
            # If not in belief no help
            support_position = sub_positions(path_position, (0, 1, 0))
            if support_position not in self.beliefs: continue
            belief = self.beliefs[support_position]

            # Check whether needs to go through door
            if type(belief.block).__name__ == "AgentBlock" and belief.block.color != self.belief_color:
                found_block_to_break = True
                self.belief_block_to_break = support_position

        if not found_door and not found_wall_to_climb: self.already_asked_for_help = False
        if not found_door: self.door_to_pass = None
        if not found_wall_to_climb: self.wall_to_pass = None
        if not found_block_to_break: self.belief_block_to_break = None

    def print(self):
        export_module.print_and_write_to_txt('   - Beliefs: ' + str(len(self.beliefs)))
        export_module.print_and_write_to_txt('   - Beliefs for Goal: ' + str(len(self.goal_beliefs)))
        export_module.print_and_write_to_txt('   - Belief Stuck: ' + str(self.belief_stuck) + ' : ' + str(self.belief_stuck_threshold))
        export_module.print_and_write_to_txt('   - Desires: ' + str(self.desires))
        if self.intention == None: export_module.print_and_write_to_txt('   - Intention: None')
        else: export_module.print_and_write_to_txt('   - Intention: ' + self.intention.desire + " @ " + 
            str(None if self.intention.position == None else convert_vec3_to_key(self.intention.position)))
        export_module.print_and_write_to_txt('   - Plan: ' + str(self.plan))

    # ======================= UTILITY FUNCTIONS =======================

    def create_messages(self):

        message = {
            'infos': [],
            'action': None,
        }

        # If we have a help process going can't ask for more help
        if not self.already_asked_for_help: 
            # Send help with door
            if self.door_to_pass != None:
                self.already_asked_for_help = True
                message['action'] = {'agent': self.belief_name, 'action': OPEN_DOOR, 'position': self.door_to_pass}
            # Send help with wall
            elif self.wall_to_pass != None:
                self.already_asked_for_help = True
                message['action'] = {'agent': self.belief_name, 'action': PLACE_BLOCK, 'position': self.wall_to_pass}
            # Send help with break block
            elif self.block_to_break != None:
                self.already_asked_for_help = True
                message['action'] = {'agent': self.belief_name, 'action': BREAK_BLOCK, 'position': self.block_to_break}

        # Treat Info messages
        for info in self.infos_to_transmit:
            content = { 'type': info['type'], 'belief': info['belief'] }
            message_info = {'agent': self.belief_name, 'type': type(info['belief']).__name__, 'position': info['position'], 'content': content}
            message['infos'].append(message_info)

        # Reset Infos to send
        self.infos_to_transmit = []

        return message

    def beliefs_from_message(self, message):

        if message['action'] != None:
            action_message = message['action']
            # Open door
            if action_message['action'] == OPEN_DOOR: self.belief_door_to_open = action_message['position']
            # Place Block
            if action_message['action'] == PLACE_BLOCK: self.belief_block_to_place = action_message['position']
            # Break Block
            if action_message['action'] == BREAK_BLOCK: self.belief_block_to_break = action_message['position']

        # Deal with info messages
        for info in message['infos']:

            position = info['position']
            info_content_type = info['content']['type']

            if info_content_type == "entity":
                # If in beliefs simply write belief
                if position in self.beliefs:
                    saved_belief = self.beliefs[position]
                    saved_belief.entity = info['content']['belief']
                    self.beliefs[position] = saved_belief
                # If not in beliefs simply write belief
                else: belief = Belief(None, None, info['content']['belief'])
            
            elif info_content_type == "block":
                # If in beliefs simply write belief
                if position in self.beliefs:
                    saved_belief = self.beliefs[position]
                    saved_belief.block = info['content']['belief']
                    self.beliefs[position] = saved_belief
                # If not in beliefs simply write belief
                else: belief = Belief(info['content']['belief'], None, None)

            elif info_content_type == "goal":
                block = info['content']['belief']
                if type(block).__name__ == "WinningPostBlock" and block.getAgentName() == self.belief_name.replace("Agent ", ""):
                    self.goal_beliefs = set([position])

            elif info_content_type == "agent":
                agent = info['content']['belief']
                if agent.name not in self.beliefs_agents_saw:
                    for belief_position in self.beliefs:
                        belief = self.beliefs[belief_position]
                        if belief.agent and belief.agent.name == agent.name:
                            belief.agent = None

                    # If in beliefs simply write belief
                    if position in self.beliefs:
                        saved_belief = self.beliefs[position]
                        saved_belief.agent = agent
                        self.beliefs[position] = saved_belief
                    # If not in beliefs simply write belief
                    else: belief = Belief(None, info['content']['belief'], None)

    def pressure_plate_to_open(self, focused_desire):
        if focused_desire == OPEN_DOOR: door_to_open = self.belief_door_to_open
        else: return None

        valid_positions = list()
        for belief_position in self.beliefs:
            belief = self.beliefs[belief_position]
            if (belief.entity != None and type(belief.entity).__name__ == "PressurePlate" and
                belief.entity.block_affected_pos == door_to_open): valid_positions.append(belief_position)

        if len(valid_positions) > 0: return random.choice(valid_positions)
        return None

    # ======================= CHECK FUNCTIONS =======================

    def check_valid_movement(self, from_position, to_position):
        support_position = sum_positions(to_position, (0, -1, 0))
        jump_head_position = sum_positions(from_position, (0, 2, 0))
        head_to_position = sum_positions(to_position, (0, 1, 0))
        fall_head_position = sum_positions(to_position, (0, 2, 0))

        # Support must be known and give support
        if (support_position not in self.beliefs or
            not self.gives_support_from_belief(support_position)): return False

        # To position must be known and free
        if (to_position not in self.beliefs or
            not self.movable_position_from_belief(to_position)): return False

        # Head to position must be know and free
        if (head_to_position not in self.beliefs or
            not self.movable_position_from_belief(head_to_position)): return False

        height_difference = to_position[1] - from_position[1]
        if height_difference == 1:
            # Jump head block must be know and free
            if (jump_head_position not in self.beliefs or
                not self.movable_position_from_belief(jump_head_position)): return False
        elif height_difference == -1:
            # Fall head block must be know and free
            if (fall_head_position not in self.beliefs or
                not self.movable_position_from_belief(fall_head_position)): return False
        elif height_difference != 0: return False

        return True

    def check_valid_explore_movement(self, from_position, to_position):
        support_position = sum_positions(to_position, (0, -1, 0))
        under_support_position = sum_positions(to_position, (0, -2, 0))
        head_to_position = sum_positions(to_position, (0, 1, 0))
        from_under_support_position = sum_positions(from_position, (0, -2, 0))
        
        # Support must be free if known
        support_is_agent_block_not_is = False
        if support_position in self.beliefs:
            support_is_agent_block_not_is = self.has_block_of_other_agent(support_position)
        if (support_position in self.beliefs and
            not self.gives_support_from_belief(support_position)): return False

        # To position must be free if known
        if (to_position in self.beliefs and
            not self.explorable_position_from_belief(to_position)): return False

        # Head to position must be free if known
        if (head_to_position in self.beliefs and
            not self.explorable_position_from_belief(head_to_position)): return False

        height_difference = to_position[1] - from_position[1]
        if  (height_difference == 1 or height_difference == -1) and not support_is_agent_block_not_is: return False
        elif height_difference == 2 and not self.is_wall_from_belief(under_support_position): return False
        elif height_difference == -2 and not self.is_wall_from_belief(from_under_support_position): return False

        return True

    def check_block_break(self):
        for belief_position in self.beliefs:
            if self.has_block_of_other_agent(belief_position):
                self.belief_block_to_break = belief_position
                break
    
    def movable_position_from_belief(self, position):
        belief = self.beliefs[position]
        if belief.block != None or belief.agent != None: return False

        # Entities need to be taken care of with care
        if belief.entity != None:
            if type(belief.entity).__name__ == "Door" and not belief.entity.state:
                return False

        return True

    def explorable_position_from_belief(self, position):
        belief = self.beliefs[position]
        if belief.block != None or belief.agent != None: return False

        # Entities need to be taken care of with care
        if belief.entity != None:
            if type(belief.entity).__name__ == "Door":
                return True

        return True

    def gives_support_from_belief(self, position):
        belief = self.beliefs[position]
        if belief.block == None: return False

        # Check if Agent Block placed has its name
        if type(belief.block).__name__ == "AgentBlock" and belief.block.color != self.belief_color:
            return False

        return True

    def is_wall_from_belief(self, position):
        belief = self.beliefs[position]
        if belief.block != None or type(belief.block).__name__ == "WallBlock": return True
        return False

    def is_free_to_place_from_belief(self, position):
        belief = self.beliefs[position]
        if belief.block != None or belief.agent != None or belief.entity != None: return False
        return True

    def has_block_of_other_agent(self, position):
        belief = self.beliefs[position]
        if type(belief.block).__name__ == "AgentBlock" and belief.block.color != self.belief_color: return True
        return False
    
    def has_block_of_agent(self, position):
        belief = self.beliefs[position]
        if type(belief.block).__name__ == "AgentBlock" and belief.block.color == self.belief_color: return True
        return False

class DeliberativeLayer(Layer):
    def __init__(self):
        super().__init__(DeliberativeMemory())

    def process_flow(self, message, world):

        message_type = message.get_type_message()
        if message_type == MessageType.PERCEPTIONS:
            self.memory.beliefs_memory_update(message.get_content())
            return Message("Deliberative", MessageDirection.UP, MessageType.COMMUNICATION_PERCEPTS, self.memory.belief_name)

        elif message_type == MessageType.DONE_COMMUNICATION_PERCEPTS:
            com_message = message.get_content()
            if com_message != None: self.memory.beliefs_from_message(com_message)
            return Message("Deliberative", MessageDirection.DOWN, MessageType.DONE_BELIEF_UPDATE, None)
        
        elif message_type == MessageType.BUILD_PATH:
            self.make_deliberation()
            self.memory.print()

            if self.empty_plan(): action = None
            else: action = self.memory.plan.pop(0)
            
            self.memory.chosen_action = action
            com_message = self.memory.create_messages()
            return Message("Deliberative", MessageDirection.UP, MessageType.COMMUNICATION_MESSAGES, com_message)

        elif message_type == MessageType.DONE_COMMUNICATION_MESSAGES:
            return Message("Deliberative", MessageDirection.DOWN, MessageType.ACTION, self.memory.chosen_action)

    def make_deliberation(self):

        if (self.succededIntention() or self.impossibleIntention() or self.empty_plan()):
            # Recalculate Plan
            export_module.print_and_write_to_txt('   - Plan Recalculated')
            self.memory.desires_update()
            self.memory.intention_update()
            self.build_plan()

        else:

            if not self.plan_is_sound():
                export_module.print_and_write_to_txt('   - Plan Not Sound')
                self.build_plan()
                # Should not happen
                if self.empty_plan(): return

            if self.reconsider():
                export_module.print_and_write_to_txt('   - Reconsidered')
                self.memory.desires_update()
                self.memory.intention_update()

    def empty_plan(self):
        return len(self.memory.plan) == 0

    def succededIntention(self):
        intention = self.memory.intention
        if intention == None: return True
        current_position = self.memory.belief_current_position
        
        if (intention.desire == REACH_GOAL or intention.desire == EXPLORE_UNKNOWN or 
            intention.desire == REACH_POSITION or intention.desire == ROAM_AROUND):
                return current_position == intention.position

        elif intention.desire == OPEN_DOOR and intention.position == current_position:
            self.memory.belief_door_to_open = None
            return True

        elif intention.desire == PLACE_BLOCK and intention.position in self.memory.beliefs and self.memory.has_block_of_other_agent(intention.position):
            self.memory.belief_block_to_place = None
            return True

        elif intention.desire == BREAK_BLOCK and intention.position in self.memory.beliefs and not self.memory.has_block_of_other_agent(intention.position):
            self.memory.belief_block_to_break = None
            return True

        elif intention.desire == STAY_STILL:
            return True

        return False

    def impossibleIntention(self):
        intention = self.memory.intention
        if intention == None: return True

        if intention.desire == REACH_GOAL or intention.desire == REACH_POSITION:
            return not self.memory.check_valid_movement(intention.position, intention.position)
        elif intention.desire == EXPLORE_UNKNOWN and intention.position != None:
            return not self.memory.check_valid_explore_movement(intention.position, intention.position)
        elif intention.desire == PLACE_BLOCK:
            if self.memory.belief_number_blocks == 0: return False
            if intention.position in self.memory.beliefs and not self.memory.is_free_to_place_from_belief(intention.position): return False
            return True
        elif intention.desire == STAY_STILL:
            return False

        return False

    def reconsider(self):
        # Simply reconsiders based on percentage
        return random.random() < RECONSIDER_CHANCE

    def build_plan(self):
        # Get current position
        current_position = self.memory.belief_current_position
        intention = self.memory.intention
        
        if (intention.desire == REACH_GOAL or intention.desire == EXPLORE_UNKNOWN or intention.desire == OPEN_DOOR):
            plan = self.build_path_plan(current_position, intention.position)
            self.memory.plan = plan

        if intention.desire == PLACE_BLOCK:
            self.memory.plan = self.build_path_plan_block(current_position, intention.position, intention.desire)
        
        if intention.desire == BREAK_BLOCK:
            self.memory.plan = self.build_path_plan_break_block(current_position, intention.position, intention.desire)
        
        elif intention.desire == STAY_STILL:
            plan = []
            self.memory.plan = plan

        elif intention.desire == ROAM_AROUND:
            plan = self.build_longest_path_plan(current_position)
            self.memory.plan = plan

    def plan_is_sound(self):
        plan = self.memory.plan
        # Control how far along the plan is checked
        if PATH_CHECK_DEPT == -1: elements_to_check = len(plan)
        else: elements_to_check = PATH_CHECK_DEPT

        temp = min(len(plan), elements_to_check)
        path_positions = self.build_path_positions_from_actions(plan[:temp])

        for i in range(1, len(path_positions)):
            from_position = path_positions[i - 1]
            to_position = path_positions[i]

            if not self.memory.check_valid_movement(from_position, to_position):
                return False

        # Check if spot allows for placing of block
        forward = self.memory.belief_forward
        current_position = self.memory.belief_current_position
        forward_position = sum_positions(current_position, forward)

        last_action = plan[:temp - 1]
        last_position = path_positions[-1]
        if last_action == CREATE_ONLY_BLOCK and not self.is_free_to_place_from_belief(forward_position): return False
        elif last_action == CREATE_UP_BLOCK and not self.is_free_to_place_from_belief(sum_positions(forward_position, (0, 1, 0))): return False
        elif last_action == CREATE_DOWN_BLOCK and not self.is_free_to_place_from_belief(sum_positions(forward_position, (0, -1, 0))): return False

        return True

    # ======== START BUILD PATH ======== 

    def build_path_plan(self, initial_position, final_position):
        # Check if already accomplished
        if initial_position == final_position: return []
        unknown_path_positions = None

        path_positions = self.build_path_positions(initial_position, final_position)
        if path_positions != None:
            intention = self.memory.intention
            intention.position = convert_vec3_to_key(path_positions[-1])
            self.memory.intention = intention
            path_actions = self.build_path_actions(path_positions)

            return path_actions

        # Doesn't know how to get to goal or goal not specified
        path_positions_return = self.build_path_positions_unknown(initial_position, final_position)
        if path_positions_return != None:
            path_positions = path_positions_return[0]
            unknown_path_positions = path_positions_return[1]
            self.memory.intention.desire = EXPLORE_UNKNOWN
            path_actions = self.build_path_actions(path_positions)

            self.memory.check_for_helps(unknown_path_positions)
            # Need to go away for them to place block
            if self.memory.wall_to_pass: return self.build_longest_path_plan(initial_position)

            return path_actions

        # Try to break own block
        self.memory.check_block_break()

        # Doesn't have anything to explore or do
        intention = Intention(STAY_STILL, None)
        self.memory.intention = intention
        return []

    def build_longest_path_plan(self, initial_position):
        intention = self.memory.intention

        path_positions_return = self.build_path_positions_unknown(initial_position, None)
        if path_positions_return != None:
            self.memory.check_for_helps(path_positions_return[1])
            intention.desire = EXPLORE_UNKNOWN
            path_positions = path_positions_return[0]

        if path_positions_return == None or len(path_positions) <= 1:
            path_positions = self.build_path_positions_longest(initial_position)

        if path_positions == None: return []

        path_actions = self.build_path_actions(path_positions)
        return path_actions

    def build_path_positions(self, initial_position, final_position):
        if final_position == None: return None

        class Explorer():
            def __init__(self, current_position):
                self.current_position = current_position
                self.history_positions = list([current_position])

        # Create Initial Explorer
        current_position = initial_position
        current_explorers = set([Explorer(current_position)])
        # Marks visited positions
        visited_positions = set([current_position])

        found_final = None
        while found_final == None:
            new_explorers = set()

            for explorer in current_explorers:
                for move_position in MOVE_POSITIONS:
                    new_current_position = sum_positions(explorer.current_position, move_position)

                    # Create Explorer
                    new_explorer = copy.deepcopy(explorer)
                    new_explorer.current_position = new_current_position
                    new_explorer.history_positions.append(new_current_position)

                    # Don't go to already visited cells
                    if new_current_position in visited_positions: continue
                    visited_positions.add(new_current_position)

                    # Check if valid movement according to beliefs
                    if not self.memory.check_valid_movement(explorer.current_position, new_current_position):
                        continue

                    if new_current_position == final_position: found_final = new_explorer
                    new_explorers.add(new_explorer)

            current_explorers = new_explorers
            
            # Didn't find objective
            if (len(current_explorers) == 0): return None

        return found_final.history_positions

    def build_path_positions_unknown(self, initial_position, final_position):
        class Explorer():
            def __init__(self, current_position):
                self.current_position = current_position
                self.history_positions = list([current_position])
                self.valid_path = True
                self.non_found_history_positions = list([current_position])

        # Create Initial Explorer
        current_position = initial_position
        current_explorers = set([Explorer(current_position)])

        # Marks visited positions
        visited_positions = set([current_position])
        # If path can't be formulated from beliefs then chose one not known place to explore
        unknown_possibilities = set()

        while len(current_explorers) > 0:
            new_explorers = set()

            for explorer in current_explorers:
                for move_position in MOVE_POSITIONS:
                    new_current_position = sum_positions(explorer.current_position, move_position)

                    # Don't go to already visited cells
                    if new_current_position in visited_positions: continue
                    visited_positions.add(new_current_position)

                    # Create Explorer
                    new_explorer = copy.deepcopy(explorer)

                    # If block completely unknown
                    if not self.memory.has_belief(new_current_position) or new_current_position == final_position:
                        unknown_possibilities.add(new_explorer)
                        continue

                    # Check if valid movement according to beliefs
                    if not self.memory.check_valid_movement(explorer.current_position, new_current_position):
                        new_explorer.valid_path = False
                        if not self.memory.check_valid_explore_movement(explorer.current_position, new_current_position):
                            continue

                    # Update Explorer
                    new_explorer.current_position = new_current_position
                    if (new_explorer.valid_path): new_explorer.history_positions.append(new_current_position)
                    new_explorer.non_found_history_positions.append(new_current_position)

                    new_explorers.add(new_explorer)

            current_explorers = new_explorers

        # If nothing to discover
        if len(unknown_possibilities) == 0: return None

        # Choose closest non known position to explore, in tie chose the one closest to final position (if exists)
        chosen_explorer = None
        chosen_steps, chosen_distance = None, None 
        for possibility in unknown_possibilities:
            steps_till_position = len(possibility.non_found_history_positions)
            if final_position == None: distance_till_final = None
            else: distance_till_final = ursinamath.distance(possibility.current_position, final_position)

            if (chosen_explorer == None or steps_till_position < chosen_steps or 
                (steps_till_position == chosen_steps and distance_till_final != None and distance_till_final < chosen_distance)):
                    chosen_explorer = possibility
                    chosen_steps = steps_till_position
                    chosen_distance = distance_till_final

        return chosen_explorer.history_positions, chosen_explorer.non_found_history_positions

    def build_path_plan_block(self, initial_position, block_position, action_type):

        path_positions = self.build_path_positions(initial_position, block_position)
        if path_positions != None:
            # Has intention of being in position before it got to where it wants to place block
            self.memory.intention.position = convert_vec3_to_key(path_positions[-1])
            # Remove last action which led agent to be in same block where it wants to place it
            path_actions = self.build_path_actions(path_positions)
            path_actions = self.remove_action_to_go_back_n_positions(path_actions, 1)
            # Append right action according to position
            position_to_be = convert_vec3_to_key(path_positions[-2])
            action_to_append = self.compute_appropriate_action_block(position_to_be, block_position, action_type)
            if action_to_append != None: path_actions.append(action_to_append)

            return path_actions

        # Doesn't know how to get to block
        path_positions_return = self.build_path_positions_unknown(initial_position, block_position)
        if path_positions_return != None:
            path_positions = path_positions_return[0]
            unknown_path_positions = path_positions_return[1]
            self.memory.intention.desire = EXPLORE_UNKNOWN
            self.memory.intention.position = convert_vec3_to_key(path_positions[-1])
            path_actions = self.build_path_actions(path_positions)
            return path_actions

        # Doesn't have anything to explore or do
        self.memory.intention.desire = STAY_STILL
        self.memory.intention.position = convert_vec3_to_key(self.memory.belief_current_position)
        return []

    def build_path_plan_break_block(self, initial_position, block_position, action_type):

        for variation in BREAK_BLOCK_POSITIONS:
            check_position = sum_positions(block_position, variation)

            path_positions = self.build_path_positions(initial_position, check_position)
            if path_positions != None:
                # Create actions which lead to the block and go back one
                path_positions.append(block_position)
                
                path_actions = self.build_path_actions(path_positions)
                path_actions = self.remove_action_to_go_back_n_positions(path_actions, 1)
                # Append right action according to position
                position_to_be = convert_vec3_to_key(path_positions[-2])
                action_to_append = self.compute_appropriate_action_block(position_to_be, block_position, action_type)
                if action_to_append != None: path_actions.append(action_to_append)

                return path_actions

        # Doesn't know how to get to block
        path_positions_return = self.build_path_positions_unknown(initial_position, block_position)
        if path_positions_return != None:
            path_positions = path_positions_return[0]
            unknown_path_positions = path_positions_return[1]
            self.memory.intention.desire = EXPLORE_UNKNOWN
            self.memory.intention.position = convert_vec3_to_key(path_positions[-1])
            path_actions = self.build_path_actions(path_positions)
            return path_actions

        # Doesn't have anything to explore or do
        self.memory.intention.desire = STAY_STILL
        self.memory.intention.position = convert_vec3_to_key(self.memory.belief_current_position)
        return []

    def build_path_positions_longest(self, initial_position):
        class Explorer():
            def __init__(self, current_position):
                self.current_position = current_position
                self.history_positions = list([current_position])

        # Create Initial Explorer
        current_position = initial_position
        current_explorers = set([Explorer(current_position)])
        # Marks visited positions
        visited_positions = set([current_position])
        # Explorers possible for choosing
        final_explorers = list()

        while len(current_explorers) > 0:
            new_explorers = set()
            final_explorers.clear()

            for explorer in current_explorers:
                for move_position in MOVE_POSITIONS:
                    new_current_position = sum_positions(explorer.current_position, move_position)

                    # Create Explorer
                    new_explorer = copy.deepcopy(explorer)
                    new_explorer.current_position = new_current_position
                    new_explorer.history_positions.append(new_current_position)

                    # Don't go to already visited cells
                    if new_current_position in visited_positions: continue
                    visited_positions.add(new_current_position)

                    # Check if valid movement according to beliefs
                    if not self.memory.check_valid_movement(explorer.current_position, new_current_position):
                        final_explorers.append(explorer)
                        continue

                    new_explorers.add(new_explorer)

            current_explorers = new_explorers

        if len(final_explorers) == 0: return None
        return random.sample(final_explorers, 1)[0].history_positions

    def build_path_actions(self, path_positions):
        # Create Path of Actions
        paths_actions = list()
        current_rotation = self.memory.belief_forward
        for index_position in range(1, len(path_positions)):
            from_position = path_positions[index_position - 1]    
            to_position = path_positions[index_position]
            variation = sub_positions(to_position, from_position)

            plane_vector = (variation[0], 0, variation[2])
            if current_rotation != plane_vector:
                right = forward_after_right(current_rotation)
                left = forward_after_left(current_rotation)
                back = forward_after_back(current_rotation)

                # Test Turn Right
                if right == plane_vector:
                    current_rotation = right
                    paths_actions.append(ROTATE_RIGHT)
                elif left == plane_vector:
                    current_rotation = left
                    paths_actions.append(ROTATE_LEFT)
                elif back == plane_vector:
                    current_rotation = back
                    paths_actions.extend([ROTATE_RIGHT, ROTATE_RIGHT])
                else:
                    print("ERROR PARSING ROTATIONS!")
                    sys.exit(1)

            if variation[1] < 0: paths_actions.append(MOVE_DOWN)
            elif variation[1] > 0: paths_actions.append(MOVE_UP)
            else: paths_actions.append(MOVE_ONLY)

        return paths_actions

    def remove_action_to_go_back_n_positions(self, path_actions, n):
        while n != 0 and len(path_actions) > 0:
            last_action = path_actions.pop(-1)
            if last_action != ROTATE_LEFT and last_action != ROTATE_RIGHT:
                n = n - 1
            
        return path_actions

    def build_path_positions_from_actions(self, path_actions):
        current_position = self.memory.belief_current_position
        current_forward = self.memory.belief_forward

        path_positions = list([current_position])
        for action in path_actions:

            next_position = None
            if action == MOVE_ONLY: next_position = sum_positions(current_position, current_forward)
            elif action == MOVE_UP: next_position = sum_positions(current_position, sum_positions(current_forward, (0, 1, 0)))
            elif action == MOVE_DOWN: next_position = sum_positions(current_position, sum_positions(current_forward, (0, -1, 0)))
            elif action == ROTATE_LEFT: current_forward = forward_after_left(current_forward)
            elif action == ROTATE_RIGHT: current_forward = forward_after_right(current_forward)

            if next_position != None and current_position != next_position: path_positions.append(next_position)

        return path_positions

    def compute_appropriate_action_block(self, position_to_be, block_position, action_type):
        difference_position = sub_positions(block_position, position_to_be)

        if difference_position[1] > 0:
            if action_type == PLACE_BLOCK: return CREATE_UP_BLOCK
            if action_type == BREAK_BLOCK: return BREAK_UP_BLOCK
        elif difference_position[1] < 0:
            if action_type == PLACE_BLOCK: return CREATE_DOWN_BLOCK
            if action_type == BREAK_BLOCK: return BREAK_DOWN_BLOCK
        else:
            if action_type == PLACE_BLOCK: return CREATE_ONLY_BLOCK
            if action_type == BREAK_BLOCK: return BREAK_ONLY_BLOCK

    # ======== END BUILD PATH ======== 

# ================================== UTIL FUNCTION ==================================

def convert_vec3_to_key(vec):
        x = round(vec[0])
        y = round(vec[1])
        z = round(vec[2])

        return (x, y, z)
        
def sum_positions(position_1, position_2):
    new_position = tuple()
    for (elem_1, elem_2) in zip(position_1, position_2):
        new_position = new_position + (elem_1 + elem_2,)

    return new_position
def sub_positions(position_1, position_2):
    new_position = tuple()
    for (elem_1, elem_2) in zip(position_1, position_2):
        new_position = new_position + (elem_1 - elem_2,)

    return new_position

def degree_between_positions(position_1, position_2):
    return 1 - spatial.distance.cosine(list(position_1), list(position_2))


def forward_after_right(forward_direction):
    if forward_direction == (1, 0, 0): return (0, 0, -1)
    elif forward_direction == (0, 0, -1): return (-1, 0, 0)
    elif forward_direction == (-1, 0, 0): return (0, 0, 1)
    elif forward_direction == (0, 0, 1): return (1, 0, 0)
def forward_after_left(forward_direction):
    if forward_direction == (1, 0, 0): return (0, 0, 1)
    elif forward_direction == (0, 0, 1): return (-1, 0, 0)
    elif forward_direction == (-1, 0, 0): return (0, 0, -1)
    elif forward_direction == (0, 0, -1): return (1, 0, 0)
def forward_after_back(forward_direction):
    if forward_direction == (1, 0, 0): return (-1, 0, 0)
    elif forward_direction == (0, 0, 1): return (0, 0, -1)
    elif forward_direction == (-1, 0, 0): return (1, 0, 0)
    elif forward_direction == (0, 0, -1): return (0, 0, 1)