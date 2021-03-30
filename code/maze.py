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

def update():
    sleep(0.15)

    if held_keys['q']:
        print(map_info['agents']['RED'].position)
        print("teste")

    # Just checking agent functions
    elif held_keys['d']: # rotate right
        map_info['agents']['RED'].rotate_right()
    elif held_keys['a']: # rotate left
        map_info['agents']['RED'].rotate_left()
    elif held_keys['s']: # rotate randomly
        map_info['agents']['RED'].rotate_randomly()
    elif held_keys['w']: # move forward
        map_info['agents']['RED'].move(world)
    
    # Just checking world functions
    elif held_keys['o']:
        block = map_info["world"].get_static_block(Vec3(3,0,0))
        if block != None: block.color = color.rgba(38,213,147)
    elif held_keys['p']:
        positions = [Vec3(3,0,0), Vec3(3,1,-1)]
        if map_info["world"].get_static_block(positions[0]) != None: map_info["world"].update_static_block(positions[0], positions[1])
        else: map_info["world"].update_static_block(positions[1], positions[0])


app.run()
