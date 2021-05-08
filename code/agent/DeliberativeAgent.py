from ursina import *
from agent.agent import Agent
from export import export_module

import sys
import math
import random
import copy

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
EXPLORE_UNKNOWN = 'EXPLORE_UNKNOWN'

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
        self.plan = []

    def decision(self, world, agents_decisions):
        self.print_agent_state()
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
        elif (len(self.goal_beliefs) > 1):
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

                    # If it is its own goal save it as so
                    if type(block).__name__ == "WinningPostBlock" and block.getAgentName() == self.name.replace("Agent ", ""):
                        self.goal_beliefs = set([check_position])

    def desires_update(self):
        self.desires = [REACH_GOAL]

    def intention_update(self):
        focused_desire = self.desires[-1]
        
        if focused_desire == REACH_GOAL:
            goal_possibility = random.sample(self.goal_beliefs, 1)[0]
            objective_position = list(goal_possibility)
            objective_position[1] = objective_position[1] + 1
            objective_position = tuple(objective_position)

            self.intention = Intention(focused_desire, objective_position)

    def build_plan(self):
        
        if self.intention.desire == REACH_GOAL:
            current_position = convert_vec3_to_key(self.position)
            self.plan = self.build_path_plan(current_position, self.intention.position)

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

    # ======== START BUILD PATH ======== 

    def build_path_plan(self, initial_position, final_position):
        # Check if already accomplished
        if initial_position == final_position: return []

        path_positions = self.build_path_positions(initial_position, final_position)
        path_actions = self.build_path_actions(path_positions)

        return path_actions

    def build_path_positions(self, initial_position, final_position):
        move_positions = (
            (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1),
            (1, -1, 0), (-1, -1, 0), (0, -1, 1), (0, -1, -1),
            (1, 1, 0), (-1, 1, 0), (0, 1, 1), (0, 1, -1),
        )

        class Explorer():
            def __init__(self, current_position):
                self.current_position = current_position
                self.history_positions = list([current_position])

        # Create Initial Explorer
        current_position = initial_position
        current_explorers = set([Explorer(current_position)])

        # Marks visited positions
        visited_positions = set([current_position])
        # If path can't be formulated from beliefs then chose one not known place to explore
        non_found_possibilities = list()

        done = False
        found_final = None
        while not done:
            new_explorers = set()

            for explorer in current_explorers:
                current_distance = ursinamath.distance(explorer.current_position, final_position)
                for move_position in move_positions:
                    new_current_position_x = explorer.current_position[0] + move_position[0]
                    new_current_position_y = explorer.current_position[1] + move_position[1]
                    new_current_position_z = explorer.current_position[2] + move_position[2]
                    new_current_position = (new_current_position_x, new_current_position_y, new_current_position_z)

                    # Create Explorer
                    new_explorer = copy.deepcopy(explorer)
                    new_explorer.current_position = new_current_position
                    new_explorer.history_positions.append(new_current_position)

                    # Don't go to already visited cells
                    if new_current_position in visited_positions: continue
                    visited_positions.add(new_current_position)

                    # Check if valid movement according to beliefs
                    if not self.check_valid_movement(explorer.current_position, new_current_position):
                        if self.check_valid_explore_movement(explorer.current_position, new_current_position):
                            non_found_possibilities.append(explorer)
                        continue

                    if new_current_position == final_position: found_final = new_explorer
                    new_explorers.add(new_explorer)

            current_explorers = new_explorers
            if (len(current_explorers) == 0 or found_final != None): done = True

        chosen_explorer = found_final
        if not found_final:
            # Explorer unknown
            self.intention.desire = EXPLORE_UNKNOWN
            
            # Choose closest non known position to explore, in tie chose the one close to final position
            chosen_steps, chosen_distance = None, None 
            for possibility in non_found_possibilities:
                steps_till_position = len(possibility.history_positions)
                distance_till_final = ursinamath.distance(possibility.current_position, final_position)

                if (chosen_explorer == None or steps_till_position < chosen_steps or 
                    (steps_till_position == chosen_steps and distance_till_final < chosen_distance)):
                        chosen_explorer = possibility
                        chosen_steps = steps_till_position
                        chosen_distance = distance_till_final

        return chosen_explorer.history_positions

    def build_path_actions(self, path_positions):
        def plane_transformation_right(plane):
            if plane == (1, 0, 0): return (0, 0, -1)
            elif plane == (0, 0, -1): return (-1, 0, 0)
            elif plane == (-1, 0, 0): return (0, 0, 1)
            elif plane == (0, 0, 1): return (1, 0, 0)
        def plane_transformation_left(plane):
            if plane == (1, 0, 0): return (0, 0, 1)
            elif plane == (0, 0, 1): return (-1, 0, 0)
            elif plane == (-1, 0, 0): return (0, 0, -1)
            elif plane == (0, 0, -1): return (1, 0, 0)
        def plane_transformation_back(plane):
            if plane == (1, 0, 0): return (-1, 0, 0)
            elif plane == (0, 0, 1): return (0, 0, -1)
            elif plane == (-1, 0, 0): return (1, 0, 0)
            elif plane == (0, 0, -1): return (0, 0, 1)

        # Create Path of Actions
        paths_actions = list()
        current_rotation = convert_vec3_to_key(self.Forward())
        for index_position in range(1, len(path_positions)):
            from_position = path_positions[index_position - 1]    
            to_position = path_positions[index_position]

            variation_x = to_position[0] - from_position[0]
            variation_y = to_position[1] - from_position[1]
            variation_z = to_position[2] - from_position[2]

            plane_vector = (variation_x, 0, variation_z)
            if current_rotation != plane_vector:
                right = plane_transformation_right(current_rotation)
                left = plane_transformation_left(current_rotation)
                back = plane_transformation_back(current_rotation)

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

            if variation_y < 0: paths_actions.append(MOVE_DOWN)
            elif variation_y > 0: paths_actions.append(MOVE_UP)
            else: paths_actions.append(MOVE_ONLY)

        return paths_actions

    # ======== END BUILD PATH ======== 

    def check_valid_movement(self, from_position, to_position):
        support_position = list(to_position)
        support_position[1] = support_position[1] - 1
        support_position = tuple(support_position)

        jump_head_position = list(from_position)
        jump_head_position[1] = jump_head_position[1] + 2
        jump_head_position = tuple(jump_head_position)

        head_to_position = list(to_position)
        head_to_position[1] = head_to_position[1] + 1
        head_to_position = tuple(head_to_position)

        fall_head_position = list(to_position)
        fall_head_position[1] = fall_head_position[1] + 2
        fall_head_position = tuple(fall_head_position)

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
        if height_difference > 0:
            # Jump head block must be know and free
            if (jump_head_position not in self.beliefs or
                not self.movable_position_from_belief(jump_head_position)): return False
        elif height_difference < 0:
            # Fall head block must be know and free
            if (fall_head_position not in self.beliefs or
                not self.movable_position_from_belief(fall_head_position)): return False

        return True

    def check_valid_explore_movement(self, from_position, to_position):
        support_position = list(to_position)
        support_position[1] = support_position[1] - 1
        support_position = tuple(support_position)

        head_to_position = list(to_position)
        head_to_position[1] = head_to_position[1] + 1
        head_to_position = tuple(head_to_position)

        # Support must be free if known
        if (support_position in self.beliefs and
            not self.gives_support_from_belief(support_position)): return False

        # To position must be free if known
        if (to_position in self.beliefs and
            not self.movable_position_from_belief(to_position)): return False

        # Head to position must befree if known
        if (head_to_position in self.beliefs and
            not self.movable_position_from_belief(head_to_position)): return False

        height_difference = to_position[1] - from_position[1]
        if height_difference != 0:
            return False

        return True

    def movable_position_from_belief(self, position):
        belief = self.beliefs[position]
        if belief.block != None or belief.agent != None: return False
        # TODO: Deal with entities

        return True

    def gives_support_from_belief(self, position):
        belief = self.beliefs[position]
        if belief.block == None: return False
        return True

    def print_beliefs(self):
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

        print("Goal Possibilities: " + str(len(self.goal_beliefs)))

    def print_agent_state(self):
        export_module.print_and_write_to_txt(self.name + ': @ ' + str(convert_vec3_to_key(self.position)))
        export_module.print_and_write_to_txt('   - Beliefs: ' + str(len(self.beliefs)))
        export_module.print_and_write_to_txt('   - Beliefs for Goal: ' + str(len(self.goal_beliefs)))
        export_module.print_and_write_to_txt('   - Desires: ' + str(self.desires))
        if self.intention == None: export_module.print_and_write_to_txt('   - Intention: None')
        else: export_module.print_and_write_to_txt('   - Intention: ' + self.intention.desire + " @ " + str(convert_vec3_to_key(self.intention.position)))
        export_module.print_and_write_to_txt('   - Plan: ' + str(self.plan))

def convert_vec3_to_key(vec):
    x = round(vec[0])
    y = round(vec[1])
    z = round(vec[2])

    return (x, y, z)