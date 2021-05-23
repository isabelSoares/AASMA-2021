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
            self.process_received_message(com_message, world)
            return Message("Reactive", MessageDirection.DOWN, MessageType.DONE_COMMUNICATION_MESSAGES, None)

    def process_received_message(self, message, world):
        self.process_action_message(message['action'], world)
        self.process_info_messages(message['infos'], world)

    def process_action_message(self, message, world):
        if message == None: return

        agent_name = message['agent']
        action = message['action']
        position = message['position']

        world.send_message(agent_name, position, action, None)

    def process_info_messages(self, messages, world):

        for message in messages:
            agent_name = message['agent']
            type_action = message['type']
            position = message['position']
            text = message['content']

            world.send_info_message(agent_name, position, type_action, text)

    def process_respond_message(self, agent_name, world):

        message = {
            'infos': [],
            'action': None
        }

        # Need Help Messages
        action_message = world.going_to_solve_older_message(agent_name)
        if action_message != None: message['action'] = {'agent': action_message.getAgent(), 'action': action_message.getNeededAction(), 'position': action_message.getPosition()}

        # Info Message
        infoUntreated = world.get_info_message()
        while infoUntreated != None:
            info = {'agent': infoUntreated.getAgent(), 'type': infoUntreated.getNeededAction(), 'position': infoUntreated.getPosition(), 'content': infoUntreated.getText()}
            message['infos'].append(info)
            # Get next
            infoUntreated = world.get_info_message()

        return message