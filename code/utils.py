import json
import sys

from ursina import color
from environment.World import World, create_block_from_code
from agent.agent import Agent

# ============= DEFAULT WORLD VARIABLES =============
DEFAULT_CENTER = (0,0,0)
DEFAULT_FLOOR_SIZE = (10, 10)
# ============= DEFAULT AGENTS VARIABLES =============
DEFAULT_COLOR = [255, 255, 255]

def load_map_from_json_file(json_file):

    with open(json_file) as f: data = json.load(f)
    return_object = {}

    load_world(data, return_object)
    load_agents(data, return_object)
    load_map(data, return_object)

    return return_object

def load_world(json_object, return_object):

    center = DEFAULT_CENTER
    if ("world" in json_object) & ("center" in json_object["world"]): center = tuple(json_object["world"]["center"])
    else: print("DEBUG-LOAD: center not loaded from map")
    return_object["center"] = center

    floor_size = DEFAULT_FLOOR_SIZE
    if ("world" in json_object) & ("floor-size" in json_object["world"]): floor_size = tuple(json_object["world"]["floor-size"])
    else: print("DEBUG-LOAD: floor-size not loaded from map")
    return_object["floor-size"] = floor_size

    world = World(center, floor_size)
    return_object["world"] = world
    print("DEBUG-LOAD: World loaded")

def load_agents(json_object, return_object):

    if "agents" not in json_object: return

    return_object["agents"] = {}
    for agent in json_object["agents"]:
        load_single_agent(agent, return_object)

    print("DEBUG-LOAD: {} agent(s) loaded".format(len(return_object["agents"])))

def load_single_agent(json_agent, return_object):

    if "name" not in json_agent: sys.exit("Every agent should have at least a name and position")
    name = json_agent["name"]

    if "position" not in json_agent: sys.exit("Every agent should have at least a name and position")
    position = tuple(json_agent["position"])

    agent_color = DEFAULT_COLOR
    if ("color" in json_agent): agent_color = color.rgba(json_agent["color"][0], json_agent["color"][1], json_agent["color"][2])

    new_agent = Agent(name = name, position = position, color = agent_color)
    return_object["agents"][name] = new_agent
    return_object["world"].add_agent(position, new_agent)

def load_map(json_object, return_object):

    if "map" not in json_object: return

    # Dealing with static blocks
    if "static" in json_object["map"]:
        for block in json_object["map"]["static"]:

            if "code" not in block: sys.exit("Every map block should have at least a code and position")
            code = block["code"]
            if "position" not in block: sys.exit("Every map block should have at least a code and position")
            position = tuple(block["position"])

            print("Oi")

            block_object = create_block_from_code(code, position)
            return_object["world"].add_static_block(position, block_object)

    # TODO: Dealing with non static blocks
