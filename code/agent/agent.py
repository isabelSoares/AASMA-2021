from ursina import *

green_color = color.rgba(21,127,21)
red_color = color.rgba(141,25,25)

class Agent(Entity):
    def __init__(self, model = 'cube', position = (0, 1, 0), color = color.rgba(0,0,0)):
        super().__init__(
            model = model,
            position = Vec3(position),
            color = color
        )

agent_green = Agent(model = 'cube', position = (0,1,0), color = green_color)
agent_red = Agent(model = 'cube', position = (2,1,0), color = red_color)
