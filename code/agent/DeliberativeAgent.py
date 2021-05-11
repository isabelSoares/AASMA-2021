from ursina import *
from agent.agent import Agent
from export import export_module
from scipy import spatial

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

# ============= VALID MOVEMENT POSITIONS AND DIRECTIONS =============
MOVE_POSITIONS = (
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
        # For it to roam around
        self.belief_stuck = False
        self.belief_stuck_threshold = BELIEF_STUCK_THRESHOLD

        self.desires = []
        self.intention = None
        self.plan = []

    def decision(self, world, agents_decisions):
        self.print_agent_state()
        last_position = self.position
        next_position = last_position

        self.beliefs_update(world)

        if (self.succededIntention() or self.impossibleIntention() or self.empty_plan()):
            # Recalculate Plan
            export_module.print_and_write_to_txt('   - Plan Recalculated')
            self.desires_update()
            self.intention_update()
            self.build_plan()

        else:

            if not self.plan_is_sound():
                export_module.print_and_write_to_txt('   - Plan Not Sound')
                self.build_plan()
                # Should not happen
                if len(self.plan) == 0: return next_position
            
            # Go with plan
            action = self.plan.pop(0)
            next_position = self.execute(world, action)

            if self.reconsider():
                export_module.print_and_write_to_txt('   - Reconsidered')
                self.desires_update()
                self.intention_update()  
        
        self.belief_update_after_decision(last_position, next_position)

        return next_position

    def beliefs_update(self, world):
        current_position = self.position

        # Update stuck belief
        self.belief_stuck = self.belief_stuck_threshold < 0

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
            for y in range(-1, 4):
                for z in range(-1, 2):
                    check_position = sum_positions(self.position, (x, y, z))
                    check_position = convert_vec3_to_key(check_position)

                    # Update belief
                    block = world.get_static_block(check_position)
                    agent = world.get_agent(check_position)
                    entity = world.get_entity(check_position)
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

    def belief_update_after_decision(self, last_position, next_position):
        # If agent doesn't have decrement counter
        if last_position == next_position: self.belief_stuck_threshold -= 1
        else: self.belief_stuck_threshold = BELIEF_STUCK_THRESHOLD

    def desires_update(self):
        self.desires = [REACH_GOAL]

        # Wants to place block?
        if self.desires_place_block() != None: self.desires.append(PLACE_BLOCK)
        # Wants door open?
        if self.desires_door_open() != None: self.desires.append(OPEN_DOOR)
        # Wants to open door back to agent
        if self.desires_door_open_back() != None: self.desires.append(OPEN_DOOR_BACK)
        # Wants to Roam Around
        if self.belief_stuck: self.desires.append(ROAM_AROUND)

    def intention_update(self):
        focused_desire = self.desires[-1]
        
        if focused_desire == REACH_GOAL:
            goal_possibility = random.sample(self.goal_beliefs, 1)[0]
            objective_position = sum_positions(goal_possibility, (0, 1, 0))

            self.intention = Intention(focused_desire, objective_position)

        elif focused_desire == OPEN_DOOR or focused_desire == OPEN_DOOR_BACK:
            pressure_plate_position = self.pressure_plate_to_open(focused_desire)
            self.intention = Intention(focused_desire, pressure_plate_position)

        elif focused_desire == PLACE_BLOCK:
            block_position = self.desires_place_block()
            self.intention = Intention(focused_desire, block_position)

        elif focused_desire == ROAM_AROUND:
            self.intention = Intention(focused_desire, None)

    def build_plan(self):
        # Get current position
        current_position = convert_vec3_to_key(self.position)
        
        if (self.intention.desire == REACH_GOAL or self.intention.desire == EXPLORE_UNKNOWN or 
            self.intention.desire == OPEN_DOOR or self.intention.desire == OPEN_DOOR_BACK):
                self.plan = self.build_path_plan(current_position, self.intention.position)

        if self.intention.desire == PLACE_BLOCK:
            self.plan = self.build_path_plan_block(current_position, self.intention.position)
        
        elif self.intention.desire == STAY_STILL:
            self.plan = []

        elif self.intention.desire == ROAM_AROUND:
            self.plan = self.build_longest_path_plan(current_position)

    def empty_plan(self):
        return len(self.plan) == 0

    def succededIntention(self):
        if self.intention == None: return True
        current_position = convert_vec3_to_key(self.position)
        
        if (self.intention.desire == REACH_GOAL or self.intention.desire == EXPLORE_UNKNOWN or 
            self.intention.desire == REACH_POSITION or self.intention.desire == ROAM_AROUND):
                return current_position == self.intention.position

        elif self.intention.desire == OPEN_DOOR and self.intention.position == current_position:
            return_value = self.desires_door_open()
            if return_value != None:
                agent_position = return_value[1]
                self.beliefs[agent_position].agent = None
            return True

        elif self.intention.desire == STAY_STILL:
            return True

    def impossibleIntention(self):
        if self.intention == None: return True

        if self.intention.desire == REACH_GOAL or self.intention.desire == REACH_POSITION:
            return not self.check_valid_movement(self.intention.position, self.intention.position)
        elif self.intention.desire == EXPLORE_UNKNOWN and self.intention.position != None:
            return not self.check_valid_explore_movement(self.intention.position, self.intention.position)
        elif self.intention.desire == STAY_STILL:
            return False

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
        # Simply reconsiders based on percentage
        # TODO: Improve reconsider logic
        return random.random() < RECONSIDER_CHANCE

    def plan_is_sound(self):
        # Control how far along the plan is checked
        if PATH_CHECK_DEPT == -1: elements_to_check = len(self.plan)
        else: elements_to_check = PATH_CHECK_DEPT

        temp = min(len(self.plan), elements_to_check)
        path_positions = self.build_path_positions_from_actions(self.plan[:temp])

        for i in range(1, len(path_positions)):
            from_position = path_positions[i - 1]
            to_position = path_positions[i]

            if not self.check_valid_movement(from_position, to_position):
                return False

        # Check if spot allows for placing of block
        forward = convert_vec3_to_key(self.Forward())
        current_position = convert_vec3_to_key(self.position)
        forward_position = sum_positions(current_position, forward)

        last_action = self.plan[:temp - 1]
        last_position = path_positions[-1]
        if last_action == CREATE_ONLY_BLOCK and not self.is_free_to_place_from_belief(forward_position): return False
        elif last_action == CREATE_UP_BLOCK and not self.is_free_to_place_from_belief(sum_positions(forward_position, (0, 1, 0))): return False
        elif last_action == CREATE_DOWN_BLOCK and not self.is_free_to_place_from_belief(sum_positions(forward_position, (0, -1, 0))): return False

        return True

    # ======================= UTILITY FUNCTIONS =======================

    def desires_door_open(self):
        agents_beliefs = list()
        door_beliefs = list()
        for belief_position in self.beliefs:
            belief = self.beliefs[belief_position]
            if belief.agent != None and belief.agent.name != self.name: agents_beliefs.append(belief_position)
            if belief.entity != None and type(belief.entity).__name__ == "Door": door_beliefs.append(belief_position)

        # If agent (not self) next to door assume wants it open
        for door_belief in door_beliefs:
            for agent_belief in agents_beliefs:
                distance = ursinamath.distance(door_belief, agent_belief)
                if distance == 1: return (door_belief, agent_belief)

        return None

    def desires_door_open_back(self):
        agents_beliefs = list()
        door_beliefs = list()
        for belief_position in self.beliefs:
            belief = self.beliefs[belief_position]
            if belief.agent != None and belief.agent.name != self.name: agents_beliefs.append(belief_position)
            if belief.entity != None and type(belief.entity).__name__ == "Door": door_beliefs.append(belief_position)

        # If other agent further away than a door then wants it open (Heuristic)
        current_position = convert_vec3_to_key(self.position)
        for door_belief in door_beliefs:
            distance_to_door = ursinamath.distance(door_belief, current_position)
            sub_door = sub_positions(current_position, door_belief)
            for agent_belief in agents_beliefs:
                distance_to_agent = ursinamath.distance(agent_belief, current_position)
                sub_agent = sub_positions(current_position, agent_belief)
                cossine_metric = degree_between_positions(sub_door, sub_agent)

                if distance_to_door < distance_to_agent and cossine_metric >= COSSINE_DOOR_AGENT:
                    return (door_belief, agent_belief)

    def desires_place_block(self):
        if self.number_of_blocks == 0: return None

        valid_place_block_positions = list()
        for belief_position in self.beliefs:
            for direction in DIRECTIONS:
                if self.helpfull_place_block(belief_position, direction):
                    valid_place_block_positions.append(belief_position)

        if len(valid_place_block_positions) == 0: return None
        else: return random.sample(valid_place_block_positions, 1)[0]

    def helpfull_place_block(self, position_block, direction):
        ahead_position = sum_positions(position_block, direction)

        support_position = sum_positions(position_block, (0, -1, 0))
        ahead_feet_position = sum_positions(ahead_position, (0, 0, 0))
        ahead_head_position = sum_positions(ahead_position, (0, 1, 0))
        ahead_above_head_position = sum_positions(ahead_position, (0, 2, 0))

        # Position block must be known and be free
        if (position_block not in self.beliefs or
            not self.is_free_to_place_from_belief(position_block)): return False
        # Support must be known and give support
        if (support_position not in self.beliefs or
            not self.gives_support_from_belief(support_position)): return False
        # Ahead feet position must be known and be a wall
        if (ahead_feet_position not in self.beliefs or
            not self.is_wall_from_belief(ahead_feet_position)): return False
        # Ahead head position must be known and be a wall
        if (ahead_head_position not in self.beliefs or
            not self.is_wall_from_belief(ahead_head_position)): return False
        # Ahead head position must be known and not be a wall
        if (ahead_above_head_position not in self.beliefs or
            self.is_wall_from_belief(ahead_above_head_position)): return False

        return True

    def pressure_plate_to_open(self, focused_desire):
        if focused_desire == OPEN_DOOR: door_to_open, _ = self.desires_door_open()
        elif focused_desire == OPEN_DOOR_BACK: door_to_open, _ = self.desires_door_open_back()
        else: return None

        valid_positions = list()
        for belief_position in self.beliefs:
            belief = self.beliefs[belief_position]
            if (belief.entity != None and type(belief.entity).__name__ == "PressurePlate" and
                belief.entity.block_affected_pos == door_to_open): valid_positions.append(belief_position)

        if len(valid_positions) > 0: return random.choice(valid_positions)
        return None

    # ======== START BUILD PATH ======== 

    def build_path_plan(self, initial_position, final_position):
        # Check if already accomplished
        if initial_position == final_position: return []

        path_positions = self.build_path_positions(initial_position, final_position)
        # Doesn't know how to get to goal or goal not specified
        if path_positions == None:
            path_positions = self.build_path_positions_unknown(initial_position, final_position)
            self.intention.desire = EXPLORE_UNKNOWN
        # Doesn't have anything to explore or do        
        if path_positions == None:
            self.intention.desire = STAY_STILL
            self.intention.position = convert_vec3_to_key(self.position)
            return []
        
        self.intention.position = convert_vec3_to_key(path_positions[-1])
        path_actions = self.build_path_actions(path_positions)
        return path_actions

    def build_longest_path_plan(self, initial_position):
        path_positions = self.build_path_positions_unknown(initial_position, None)
        if path_positions != None: self.intention.desire = EXPLORE_UNKNOWN
        if path_positions == None or len(path_positions) <= 1: path_positions = self.build_path_positions_longest(initial_position)
        if path_positions == None: return []

        path_actions = self.build_path_actions(path_positions)
        return path_actions

    def build_path_plan_block(self, initial_position, block_position):

        path_positions = self.build_path_positions(initial_position, block_position)
        # Doesn't know how to get to block
        if path_positions == None:
            path_positions = self.build_path_positions_unknown(initial_position, block_position)
            if path_positions != None:
                self.intention.desire = EXPLORE_UNKNOWN
                self.intention.position = convert_vec3_to_key(path_positions[-1])
                path_actions = self.build_path_actions(path_positions)
                return path_actions
        # Doesn't have anything to explore or do        
        if path_positions == None:
            self.intention.desire = STAY_STILL
            self.intention.position = convert_vec3_to_key(self.position)
            return []
        
        # Has intention of being in position before it got to where it wants to place block
        self.intention.position = convert_vec3_to_key(path_positions[-1])

        path_actions = self.build_path_actions(path_positions)
        # Remove last action which led agent to be in same block where it wants to place it
        path_actions = self.remove_action_to_go_back_n_positions(path_actions, 1)

        # Append right action according to position
        position_to_be = convert_vec3_to_key(path_positions[-2])
        action_to_append = self.compute_appropriate_action_block(position_to_be, block_position)
        if action_to_append != None: path_actions.append(action_to_append)

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
                    if not self.check_valid_movement(explorer.current_position, new_current_position):
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
                    if new_current_position not in self.beliefs:
                        unknown_possibilities.add(new_explorer)
                        continue

                    # Check if valid movement according to beliefs
                    if not self.check_valid_movement(explorer.current_position, new_current_position):
                        new_explorer.valid_path = False
                        if not self.check_valid_explore_movement(explorer.current_position, new_current_position):
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

        return chosen_explorer.history_positions

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
                    if not self.check_valid_movement(explorer.current_position, new_current_position):
                        final_explorers.append(explorer)
                        continue

                    new_explorers.add(new_explorer)

            current_explorers = new_explorers

        if len(final_explorers) == 0: return None
        return random.sample(final_explorers, 1)[0].history_positions

    def build_path_actions(self, path_positions):
        # Create Path of Actions
        paths_actions = list()
        current_rotation = convert_vec3_to_key(self.Forward())
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
        current_position = convert_vec3_to_key(self.position)
        current_forward = convert_vec3_to_key(self.Forward())

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

    def compute_appropriate_action_block(self, position_to_be, block_position):
        difference_position = sub_positions(block_position, position_to_be)

        if difference_position[1] > 0: return CREATE_UP_BLOCK
        elif difference_position[1] < 0: return CREATE_DOWN_BLOCK
        else: return CREATE_ONLY_BLOCK

    # ======== END BUILD PATH ======== 

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
        support_position = sum_positions(to_position, (0, -1, 0))
        head_to_position = sum_positions(to_position, (0, 1, 0))
        
        # Support must be free if known
        if (support_position in self.beliefs and
            not self.gives_support_from_belief(support_position)): return False

        # To position must be free if known
        if (to_position in self.beliefs and
            not self.explorable_position_from_belief(to_position)): return False

        # Head to position must be free if known
        if (head_to_position in self.beliefs and
            not self.explorable_position_from_belief(head_to_position)): return False

        height_difference = to_position[1] - from_position[1]
        if height_difference != 0:
            return False

        return True

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
        if type(belief.block).__name__ == "AgentBlock" and belief.block.color != self.color:
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

    def print_beliefs(self, position_belief):
        belief = self.beliefs[position_belief]

        info_line = "("
        if (belief.agent == None): info_line += "None" + ", "
        else: info_line += belief.agent.name + ", "
        if (belief.entity == None): info_line += "None" + ", "
        else: info_line += type(belief.entity).__name__ + ", "
        if (belief.block == None): info_line += "None" + ")"
        else: info_line += type(belief.block).__name__ + ")"

        print(info_line + " @ " + str(position_belief))

    def print_agent_state(self):
        export_module.print_and_write_to_txt(self.name + ': @ ' + str(convert_vec3_to_key(self.position)))
        export_module.print_and_write_to_txt('   - Beliefs: ' + str(len(self.beliefs)))
        export_module.print_and_write_to_txt('   - Beliefs for Goal: ' + str(len(self.goal_beliefs)))
        export_module.print_and_write_to_txt('   - Belief Stuck: ' + str(self.belief_stuck) + ' : ' + str(self.belief_stuck_threshold))
        export_module.print_and_write_to_txt('   - Desires: ' + str(self.desires))
        if self.intention == None: export_module.print_and_write_to_txt('   - Intention: None')
        else: export_module.print_and_write_to_txt('   - Intention: ' + self.intention.desire + " @ " + 
            str(None if self.intention.position == None else convert_vec3_to_key(self.intention.position)))
        export_module.print_and_write_to_txt('   - Plan: ' + str(self.plan))

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

def convert_vec3_to_key(vec):
    x = round(vec[0])
    y = round(vec[1])
    z = round(vec[2])

    return (x, y, z)

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