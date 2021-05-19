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

class CommunicationMemory(LayerMemory):
    def __init__(self):
        super()

class CommunicationLayer(Layer):
    def __init__(self):
        super().__init__(CommunicationMemory())

    def process_flow(self, message, world):

        message_type = message.get_type_message()
        if message_type == MessageType.COMMUNICATION_PERCEPTS:
            com_message = self.process_respond_message(message.get_content(), world)
            return Message("Reactive", MessageDirection.DOWN, MessageType.DONE_COMMUNICATION_PERCEPTS, com_message)
        elif message_type == MessageType.COMMUNICATION_MESSAGES:
            com_message = message.get_content()
            if com_message != None: self.process_received_message(com_message, world)
            return Message("Reactive", MessageDirection.DOWN, MessageType.DONE_COMMUNICATION_MESSAGES, None)

    def process_received_message(self, message, world):
        agent_name = message['agent']
        action = message['action']
        position = message['position']

        world.send_message(agent_name, position, action, None)

    def process_respond_message(self, agent_name, world):
        com_message = world.going_to_solve_older_message(agent_name)
        if com_message == None: return None
        else: return {'agent': com_message.getAgent(), 'action': com_message.getNeededAction(), 'position': com_message.getPosition()}