import sys
from time import sleep

# Ursina import
from ursina import *
app = Ursina()
# Import util : load_json
from utils import load_map_from_json_file
# Import environment
from environment.setup import setup_window, setup_camera
from environment.World import World
# Import agent
from agent.agent import *

# Check if file was given in arguments and load it
if len(sys.argv) <= 1: sys.exit("Please provide a file to read the map from as an argument.")
map_info = load_map_from_json_file(sys.argv[1])

# Setup window and camera
setup_window()
setup_camera(position = Vec3(50,50,50), look_at = map_info["center"])

world = map_info['world']
agents = map_info['agents'].values()

t = 0
def update():
    global t
    t += time.dt
    if t > 1:
        t = 0
        for agent in agents:
            agent.decision(world)
        world.update()

def input(key):

    if key == 'q':
        print(map_info['agents']['RED'].position)
        print("teste")

    # Just checking agent functions
    elif key == 'd': # rotate right
        map_info['agents']['RED'].rotate_right()
    elif key == 'a': # rotate left
        map_info['agents']['RED'].rotate_left()
    elif key == 's': # rotate randomly
        map_info['agents']['RED'].rotate_randomly()
    elif key == 'w': # move forward
        map_info['agents']['RED'].move(world)

    # Just checking world functions
    elif key == 'o':
        block = map_info["world"].get_static_block(Vec3(3,0,0))
        if block != None: block.color = color.rgba(38,213,147)
    elif key == 'p':
        positions = [Vec3(3,0,0), Vec3(3,1,-1)]
        if map_info["world"].get_static_block(positions[0]) != None: map_info["world"].update_static_block(positions[0], positions[1])
        else: map_info["world"].update_static_block(positions[1], positions[0])


app.run()
