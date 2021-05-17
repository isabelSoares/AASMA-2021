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

class ReactiveMemory(LayerMemory):
    def __init__(self):
        super()

class ReactiveLayer(Layer):
    def __init__(self):
        super().__init__(ReactiveMemory())

    def process_flow(self, message):

        message_type = message.get_type_message()
        if message_type == MessageType.PERCEPTIONS:
            return Message("Reactive", MessageDirection.UP, MessageType.PERCEPTIONS, message.content)
        elif message_type == MessageType.DONE_BELIEF_UPDATE:
            return Message("Reactive", MessageDirection.UP, MessageType.BUILD_PATH, None)
        elif message_type == MessageType.ACTION:
            action = message.content;
            return Message("Reactive", MessageDirection.DOWN, MessageType.ACTION, action)
