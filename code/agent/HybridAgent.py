from ursina import *
from agent.agent import Agent
from export import export_module

import sys

# Importing Layers
from agent.layers.ReactiveLayer import ReactiveLayer
from agent.layers.DeliberativeLayer import DeliberativeLayer

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

class HybridAgent(Agent):
    def __init__(self, name = 'Unknown', position = (0, 1, 0), color = color.rgba(0,0,0), block_color = None, number_of_blocks = 0):
        super().__init__(
            name = name,
            position = position,
            color = color,
            block_color = block_color,
            number_of_blocks = number_of_blocks
        )

        self.layers = [
            ReactiveLayer(),
            DeliberativeLayer(),
        ]

    def decision(self, world, agents_decisions):
        last_position = self.position
        export_module.print_and_write_to_txt(self.name + ': @ ' + str(convert_vec3_to_key(self.position)))
        
        # Create Perceptions Message
        perceptions = self.get_perceptions(world)
        message = Message('outside', MessageDirection.UP, MessageType.PERCEPTIONS, perceptions)

        # Start flow between layers
        current_message = message
        to_index = 0
        while to_index != -1:
            targetLayer = self.layers[to_index]
            current_message = targetLayer.process_flow(current_message)

            if (current_message.get_direction() == MessageDirection.UP): to_index = to_index + 1
            elif (current_message.get_direction() == MessageDirection.DOWN): to_index = to_index - 1
            else: sys.exit("ERROR: Direction " + str(current_message.get_direction()) + " not specified")
                
        # Retrieve last message and execute it
        last_message = current_message
        next_position = self.execute(world, last_message.content)
        if next_position == None: next_position = last_position

        return next_position


    def get_perceptions(self, world):

        goal_distance = world.distance_provider(self.name, self)

        perceptions_around = {} 
        # Update 3 x 3 around
        for x in range(-1, 2):
            for y in range(-1, 4):
                for z in range(-1, 2):
                    store_position = convert_vec3_to_key((x, y, z))
                    check_position = (self.position[0] + x, self.position[1] + y, self.position[2] + z)
                    check_position = convert_vec3_to_key(check_position)

                    block = world.get_static_block(check_position)
                    agent = world.get_agent(check_position)
                    entity = world.get_entity(check_position)

                    perceptions_around[store_position] = {
                        'block': block,
                        'agent': agent,
                        'entity': entity,
                    }

        perceptions = {
            'name': self.name,
            'number of blocks': self.number_of_blocks,
            'current position': convert_vec3_to_key(self.position),
            'forward': convert_vec3_to_key(self.Forward()),
            'goal distance': goal_distance,
            'around': perceptions_around
        }

        return perceptions
    
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

        if action == None: return None

        function_to_call = action_to_functions[action]
        takes_world_argument = function_to_call[1]
        if takes_world_argument: next_position = action_to_functions[action][0](world)
        else: next_position = action_to_functions[action][0]()

        return next_position

def convert_vec3_to_key(vec):
    x = round(vec[0])
    y = round(vec[1])
    z = round(vec[2])

    return (x, y, z)