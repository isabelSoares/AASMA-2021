import sys
from time import sleep

# Check if file was given in arguments
if len(sys.argv) <= 2: sys.exit("Please provide a type of agent and file to read the map from as an argument. Example: python ./maze.py random ./maps/map1.json")
type_of_agent = sys.argv[1]
map_name = sys.argv[2]
# Create export Module
from export import create_export_module
export_module = create_export_module(type_of_agent, map_name)

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

# Load map
map_info = load_map_from_json_file(type_of_agent, './maps/'+map_name+'.json' )

# Setup window, camera and window panel
setup_window(borderless = False)
setup_camera(position = Vec3(-50,50,-50), look_at = map_info["center"])

world = map_info['world']
agents = map_info['agents'].values()

info_panel = InfoPanel()
message_panel = MessagePanel()
min_tick_time, tick_time, max_tick_time, step = 0.005, 0.5, 1.0, 0.005
setup_panel_control(info_panel, min_tick_time, tick_time, max_tick_time, step, map_info['agents'].keys())
setup_panel_messages(message_panel)

max_time = 20000
t = 0
def update():
    global t, tick_time
    t += time.dt
    if t > tick_time:
        t = 0
        export_module.print_and_write_to_txt('')
        export_module.print_and_write_to_txt('------------ ' + str(world.metrics.time) + ' ------------')
        tick_time = info_panel.get_time_tick()
        agents_in_goal = 0
        agents_decisions = []
        for agent in agents:
            agent.set_animation_duration(.8 * tick_time)
            a = agent.decision(world, agents_decisions)
            agents_decisions.append(a)

            if agent.position - Vec3(0, 1, 0) == world.get_agent_goal_position(agent.name):
                agents_in_goal += 1

        if agents_in_goal == len(agents):
            print()
            print()
            print('   ==========================')
            print(' //                          \\\\')
            print(' |  The Agents won the game!  |')
            print(' \\\\                          //')
            print('   ==========================')
            print()
            print()
            print(world.metrics.time)
            exit()
        
        world.update()
        world.export_metrics_content(info_panel)
        world.export_messages_content(message_panel)

        export_module.save_current_state()

        if world.metrics.time == max_time:
            print()
            print()
            print('   ==========================')
            print(' //                          \\\\')
            print(' |     Solution not found!    |')
            print(' \\\\                          //')
            print('   ==========================')
            print()
            print()
            exit()

app.run()