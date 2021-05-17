
class MessageDirection(Enum):
    UP = "UP"
    DOWN = "DOWN"

class MessageType(Enum):
    PERCEPTIONS = "PERCEPTIONS"
    ACTION = "ACTION"
    DONE_BELIEF_UPDATE = "DONE_BELIEF_UPDATE"

class Message():
    def __init__(self, layer_from, direction, type_message, content):
        self.layer_From = layer_from
        self.direction = direction
        self.type_message = type_message
        self.content = content

    def get_layer_from(self): return self.layer_from
    def get_direction(self): return self.direction
    def get_type_message(self): return self.type_message
    def get_content(self): return self.content