from ursina import *
from agent.agent import Agent
from export import export_module

import sys
import math
import random

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
PLACE_BLOCK = 'PLACE_BLOCK'
BREAK_BLOCK = 'BREAK_BLOCK'
REACH_POSITION = 'REACH_POSITION'

class Belief():
    def __init__(self, block, agent, entity):
        self.block = block
        self.agent = agent
        self.entity = entity

class Intention():
    def __init__(self, desire, position):
        self.desire = desire
        self.position = position

class DeliberativeAgent(Agent):
    def __init__(self, name = 'Unknown', position = (0, 1, 0), color = color.rgba(0,0,0), block_color = None, number_of_blocks = 0):
        super().__init__(
            name = name,
            position = position,
            color = color,
            block_color = block_color,
            number_of_blocks = number_of_blocks
        )

        # Beliefs
        self.beliefs = {}
        self.goal_beliefs = set()

        self.desires = []
        self.intention = None
        self.plan = [ROTATE_RIGHT, MOVE_ONLY, MOVE_ONLY, MOVE_ONLY]

    def decision(self, world, agents_decisions):
        last_position = self.position
        next_position = last_position

        self.beliefs_update(world)

        if (self.empty_plan() or self.succededIntention() or self.impossibleIntention()):
            # Recalculate Plan
            self.desires_update()
            self.intention_update()
            self.build_plan()

        else:
            # Go with plan
            action = self.plan.pop(0)
            next_position = self.execute(world, action)

            if self.reconsider():
                self.desires_update()
                self.intention_update()

            if not self.plan_is_sound():
                self.build_plan()
                
        
        return next_position

    def beliefs_update(self, world):
        current_position = self.position

        # Update goal block belief
        distance = world.distance_provider(self.name, self)
        lower_bound, upper_bound = math.floor(distance), math.ceil(distance)
        if (len(self.goal_beliefs) == 0):
            for x in range(-upper_bound, upper_bound + 1):
                for y in range(-upper_bound, upper_bound + 1):
                    for z in range(-upper_bound, upper_bound + 1):

                        check_position = (self.position[0] + x, self.position[1] + y, self.position[2] + z)
                        check_position = convert_vec3_to_key(check_position)

                        distance = ursinamath.distance(self.position, check_position)
                        if (lower_bound <= distance and distance <= upper_bound): self.goal_beliefs.add(check_position)
        else:
            to_remove = set()
            for check_position in self.goal_beliefs:
                distance_to_position = ursinamath.distance(self.position, check_position)
                if not(lower_bound <= distance_to_position and distance_to_position <= upper_bound): to_remove.add(check_position)

            self.goal_beliefs = self.goal_beliefs - to_remove


        # Update 3 x 3 around
        for x in range(-1, 2):
            for y in range(-1, 3):
                for z in range(-1, 2):
                    check_position = (self.position[0] + x, self.position[1] + y, self.position[2] + z)
                    check_position = convert_vec3_to_key(check_position)

                    # Update belief
                    block = world.get_static_block(check_position)
                    agent = world.get_agent(check_position)
                    entity = world.get_entity(check_position)
                    belief_to_update = Belief(block, agent, entity)

                    self.beliefs[check_position] = belief_to_update

        self.print_beliefs()

    def desires_update(self):
        self.desires = [REACH_GOAL]

    def intention_update(self):
        focused_desire = self.desires[-1]
        
        if focused_desire == REACH_GOAL:
            self.intention = Intention(focused_desire, random.sample(self.goal_beliefs, 1))

    def build_plan(self):
        
        if self.intention.desire == REACH_GOAL:
            self.plan = self.build_path_plan(self.position, self.intention.position)

    def empty_plan(self):
        return len(self.plan) == 0

    def succededIntention(self):
        return False

    def impossibleIntention(self):
        return False

    def execute(self, world, action):
        action_to_functions = dict(
            MOVE_ONLY = (self.move_only, True),
            MOVE_UP = (self.move_up, True),
            MOVE_DOWN = (self.move_down, True),
            ROTATE_LEFT = (self.rotate_left, False),
            ROTATE_RIGHT = (self.rotate_right, False),
            CREATE_ONLY_BLOCK = (self.create_block, True),
            CREATE_UP_BLOCK = (self.create_up, True),
            CREATE_DOWN_BLOCK = (self.create_down, True),
            BREAK_ONLY_BLOCK = (self.break_block, True),
            BREAK_UP_BLOCK = (self.break_up, True),
            BREAK_DOWN_BLOCK = (self.break_down, True)
        )

        function_to_call = action_to_functions[action]
        takes_world_argument = function_to_call[1]
        if takes_world_argument: next_position = action_to_functions[action][0](world)
        else: next_position = action_to_functions[action][0]()

        return next_position

    def reconsider(self):
        return False

    def plan_is_sound(self):
        return True

    # ======================= UTILITY FUNCTIONS =======================
    def build_path_plan(self, initial_position, final_position):
        return []

    def print_beliefs(self):
        '''
        print("Beliefs:")

        for position_belief in self.beliefs:
            belief = self.beliefs[position_belief]

            info_line = "("
            if (belief.agent == None): info_line += "None" + ", "
            else: info_line += belief.agent.name + ", "
            if (belief.entity == None): info_line += "None" + ", "
            else: info_line += type(belief.entity).__name__ + ", "
            if (belief.block == None): info_line += "None" + ")"
            else: info_line += type(belief.block).__name__ + ")"

            print(info_line + " @ " + str(position_belief))
        '''

        print("Goal Possibilities: " + str(len(self.goal_beliefs)))


def convert_vec3_to_key(vec):
    x = round(vec[0])
    y = round(vec[1])
    z = round(vec[2])

    return (x, y, z)