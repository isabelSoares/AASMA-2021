from ursina import Entity, Panel

class InfoPanel(Panel):
    def __init__(self):
        super().__init__(
            scale = (.4, .4),
            origin = (0, 0),
            position = (-.69, .29),
        )

        self.item_parent = Entity(parent=self)
        self.input_speed = Entity(parent=self)
        self.input_player = Entity(parent=self)

    def get_time_tick(self):
        return self.input_speed.children[0].value

class MessagePanel(Panel):
    def __init__(self):
        super().__init__(
            scale = (.4, .4),
            origin = (0, 0),
            position = (.69, .29),
        )

        self.input_message_type = Entity(parent=self)
        self.messages = Entity(parent=self)