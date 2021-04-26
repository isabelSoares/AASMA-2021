import sys
from time import sleep

# Ursina import
from ursina import *
app = Ursina()
# Import util : load_json
from utils import load_map_from_json_file
# Import environment
from environment.setup import setup_window, setup_camera, setup_panel_control, setup_panel_messages
from environment.World import World
from environment.Panels import InfoPanel, MessagePanel
# Import agent
from agent.agent import *

# Check if file was given in arguments and load it
if len(sys.argv) <= 2: sys.exit("Please provide a type of agent and file to read the map from as an argument. Example: python ./maze.py random ./maps/map1.json")
type_of_agent = sys.argv[1]
map_info = load_map_from_json_file(type_of_agent, sys.argv[2])

# Setup window, camera and window panel
setup_window(borderless = False)
setup_camera(position = Vec3(-50,50,-50), look_at = map_info["center"])

world = map_info['world']
agents = map_info['agents'].values()

info_panel = InfoPanel()
message_panel = MessagePanel()
min_tick_time, tick_time, max_tick_time, step = 0.25, 1.0, 1.0, 0.05
setup_panel_control(info_panel, min_tick_time, tick_time, max_tick_time, step, map_info['agents'].keys())
setup_panel_messages(message_panel)

t = 0
def update():
    global t, tick_time
    t += time.dt
    if t > tick_time:
        t = 0
        print()
        print('------------ ' + str(world.metrics.time) + ' ------------')
        for agent in agents:

            agents_decisions = []
            agents_decisions.append(agent.decision(world, agents_decisions))
        
        world.update()
        world.export_metrics_content(info_panel)
        world.export_messages_content(message_panel)
        tick_time = info_panel.get_time_tick()

def input(key):

    if key == 'q':
        print(map_info['agents']['BLUE'].position)
        print("teste")

    # Just checking agent functions
    elif key == 'd': # rotate right
        map_info['agents']['BLUE'].rotate_right(world)
    elif key == 'a': # rotate left
        map_info['agents']['BLUE'].rotate_left(world)
    elif key == 's': # rotate randomly
        map_info['agents']['BLUE'].rotate_randomly(world)
    elif key == 'w': # move forward
        map_info['agents']['BLUE'].move(world)

    # Just checking world functions
    elif key == 'o':
        block = map_info["world"].get_static_block(Vec3(3,0,0))
        if block != None: block.color = color.rgba(38,213,147)
    elif key == 'p':
        positions = [Vec3(3,0,0), Vec3(3,1,-1)]
        if map_info["world"].get_static_block(positions[0]) != None: map_info["world"].update_static_block(positions[0], positions[1])
        else: map_info["world"].update_static_block(positions[1], positions[0])

    elif key == 'space':
        info_panel.enabled = not info_panel.enabled
        message_panel.enabled = not message_panel.enabled

app.run()
