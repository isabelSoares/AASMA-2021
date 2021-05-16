from ursina import *
from export import export_module

import math

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
BELIEF_STUCK_THRESHOLD = 25
COSSINE_DOOR_AGENT = 0.5

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
        self.beliefs = {}
        self.goal_beliefs = set()
        # For it to roam around
        self.belief_stuck = False
        self.belief_stuck_threshold = BELIEF_STUCK_THRESHOLD

        self.desires = []
        self.intention = None
        self.plan = []

    def beliefs_memory_update(self, percepts):
        current_position = percepts['current position']

        # Update stuck belief
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
            if type(block).__name__ == "WinningPostBlock" and block.getAgentName() == self.name.replace("Agent ", ""):
                self.goal_beliefs = set([check_position])

    def beliefs_print(self):
        export_module.print_and_write_to_txt('   - Beliefs: ' + str(len(self.beliefs)))
        export_module.print_and_write_to_txt('   - Beliefs for Goal: ' + str(len(self.goal_beliefs)))
        export_module.print_and_write_to_txt('   - Belief Stuck: ' + str(self.belief_stuck) + ' : ' + str(self.belief_stuck_threshold))                    
    

class DeliberativeLayer(Layer):
    def __init__(self):
        super().__init__(DeliberativeMemory())

    def process_flow(self, message):

        if message.get_type_message() == MessageType.PERCEPTIONS:
            self.memory.beliefs_memory_update(message.get_content())
            self.memory.beliefs_print()
            return Message("Deliberative", MessageDirection.DOWN, MessageType.DONE_BELIEF_UPDATE, None)

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