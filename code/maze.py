from ursina import *
from time import sleep
app = Ursina()
# Import environment
from environment.setup import setup_window, setup_camera
from environment.World import World
# Import agent
from agent.agent import *


# Call construction of World
center, size = (0, 0, 0), (10, 5)
world = World(center, size)

# Setup window and camera
setup_window()
setup_camera(position = Vec3(50,50,50), look_at = center)

# Create agents
AGENT_GREEN = Agent(name = 'GREEN', model = 'cube', position = (0,1,0), color = GREEN_COLOR)
AGENT_RED = Agent(name = 'RED', model = 'cube', position = (2,1,0), color = RED_COLOR)

def update():
    sleep(0.1)
    if held_keys['q']:
        print("teste")
    elif held_keys['d']: # rotate right
        AGENT_RED.rotate_right()
    elif held_keys['a']: # rotate left
        AGENT_RED.rotate_left()
    elif held_keys['s']: # rotate randomly
        AGENT_RED.rotate_randomly()
    elif held_keys['w']: # move forward
        AGENT_RED.move()

app.run()
