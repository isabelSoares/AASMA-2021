from ursina import Vec3, color, Text, Entity, camera, Panel, destroy
from environment.blocks.FloorBlock import FloorBlock
from environment.blocks.AgentBlock import AgentBlock
from environment.blocks.WinningPostBlock import WinningPostBlock
from environment.blocks.WallBlock import WallBlock
from environment.blocks.TriggersBlock import TriggersBlock
from environment.blocks.PressurePlate import PressurePlate
from environment.blocks.Door import Door

import math

class Metrics:
    def __init__(self):
        self.selected_agent = None

        self.time = 0
        self.steps = {}
        self.pressure_plates_activated = {}
        self.blocks_placed = {}
        self.blocks_removed = {}

    def initialize_for_agent(self, agent):
        self.steps[agent] = 0
        self.pressure_plates_activated[agent] = 0
        self.blocks_placed[agent] = 0
        self.blocks_removed[agent] = 0

    def export_content(self, panel):
        selection = panel.input_player.children[0].text.replace(" Selected", "")
        # No ternary operator :'(
        self.selected_agent = None if selection == "All Players" else selection

        steps, pressure_plates_activated, blocks_placed, blocks_removed = 0, 0, 0, 0
        if (self.selected_agent == None):
            for agent in self.steps: steps += self.steps[agent]
            for agent in self.pressure_plates_activated: pressure_plates_activated += self.pressure_plates_activated[agent]
            for agent in self.blocks_placed: blocks_placed += self.blocks_placed[agent]
            for agent in self.blocks_removed: blocks_removed += self.blocks_removed[agent]

        else:
            steps = self.steps[self.selected_agent]
            pressure_plates_activated = self.pressure_plates_activated[self.selected_agent]
            blocks_placed = self.blocks_placed[self.selected_agent]
            blocks_removed = self.blocks_removed[self.selected_agent]

        optional_tag = ""
        if self.selected_agent != None: optional_tag = " (individualy)"
        information_to_display = [
            "Time: " + str(self.time),
            "Steps" + optional_tag + ": " + str(steps),
            "Pressure Plate Activations" + optional_tag + ": " + str(pressure_plates_activated),
            "Blocks Placed by Agents" + optional_tag + ": " + str(blocks_placed),
            "Blocks Removed by Agents" + optional_tag + ": " + str(blocks_removed),
        ]

        for index in range(len(information_to_display)):
            information = information_to_display[index]
            if index < len(panel.item_parent.children): panel.item_parent.children[index].text = information

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

class World():
    def __init__(self, center = (0,0,0), size = (5, 5)):

        # Initializing variables defining world
        self.static_map = {}
        self.goal_map = {}
        self.dynamic_map = {}
        self.agents_map = {}
        self.entities_map = {}
        self.count = 0

        # Initializing metrics
        self.metrics = Metrics()
		
        # Create floor
        radius_x = math.ceil((size[0] - 1) / 2)
        radius_y = math.ceil((size[1] - 1) / 2)
        from_position = (center[0] - radius_x, center[1] - radius_y)
        to_position = (center[0] + radius_x, center[1] + radius_y)
        self.create_floor(from_position, to_position)

    def update(self):

        self.metrics.time = self.metrics.time + 1

        for pos in self.entities_map:
            entity = self.entities_map[pos]
            if entity.update() & isinstance(entity, TriggersBlock): 
                block_affected_pos = entity.get_block_affected_pos()
                block = self.get_entity(block_affected_pos)
                entity.affect_block(block)
        


    # ================== Attributes Management ==================

    def get_static_block(self, position):
        position = convert_vec3_to_key(position)
        if position in self.static_map: return self.static_map[position]
        else: return None

    def add_static_block(self, position, block):
        position = convert_vec3_to_key(position)
        self.static_map[position] = block
    
    def create_agent_block(self, position, agent_name, color):
        position = convert_vec3_to_key(position)
        self.static_map[position] = AgentBlock(position, agent_name, color)
        
    def delete_static_block(self, position):
        position = convert_vec3_to_key(position)
        if position not in self.static_map: return
        destroy(self.static_map[position])
        del self.static_map[position]
    
    def break_agent_block(self, position):
        self.delete_static_block(position)

    def update_static_block(self, current_position, updated_position):
        current_position = convert_vec3_to_key(current_position)
        updated_position = convert_vec3_to_key(updated_position)
        if current_position not in self.static_map: return

        block = self.get_static_block(current_position)
        self.add_static_block(updated_position, block)
        block.position = updated_position
        self.delete_static_block(current_position)

    def get_agent(self, position):
        position = convert_vec3_to_key(position)
        if position in self.agents_map: return self.agents_map[position]
        else: return None

    def add_agent(self, position, agent):
        position = convert_vec3_to_key(position)
        self.agents_map[position] = agent
        self.metrics.initialize_for_agent(agent.name.replace("Agent ", ""))
    
    def delete_agent(self, position):
        position = convert_vec3_to_key(position)
        if position not in self.agents_map: return
        del self.agents_map[position]

    def update_agent(self, current_position, updated_position):
        current_position = convert_vec3_to_key(current_position)
        updated_position = convert_vec3_to_key(updated_position)
        if current_position not in self.agents_map: return

        agent = self.get_agent(current_position)
        self.add_agent(updated_position, agent)
        self.delete_agent(current_position)
    
    def get_entity(self, position):
        position = convert_vec3_to_key(position)
        if position in self.entities_map: return self.entities_map[position]
        else: return None

    def add_entity(self, position, entity):
        position = convert_vec3_to_key(position)
        self.entities_map[position] = entity
        
    def delete_entity(self, position):
        position = convert_vec3_to_key(position)
        if position not in self.entities_map: return
        del self.entities_map[position]

    def update_entity(self, current_position, updated_position):
        current_position = convert_vec3_to_key(current_position)
        updated_position = convert_vec3_to_key(updated_position)
        if current_position not in self.entities_map: return

        entity = self.get_entity(current_position)
        self.add_entity(updated_position, entity)
        self.delete_entity(current_position)
    
    def export_metrics_content(self, panel):
        self.metrics.export_content(panel)

    # ================== Auxiliary Methods ==================

    def create_floor(self, from_position, to_position):
        for x in range(from_position[0], to_position[0] + 1, 1):
            for y in range(from_position[1], to_position[1] + 1, 1):
                block = create_block_from_code("Floor", (x, 0, y))
                self.static_map[(x, 0, y)] = block
        
        for y in range(from_position[1], to_position[1] + 1, 1):
            block = create_block_from_code("WinningPost", (to_position[0] + 1, 0, y))
            self.goal_map[(to_position[0] + 1, 0, y)] = block

def create_block_from_code(code, position, block_affected_pos = None):

    # Manual Switch (sadly)
    if code == "Floor": return FloorBlock(position = position)
    elif code == "WinningPost": return WinningPostBlock(position = position)
    elif code == "Wall": return WallBlock(position = position)
    elif code == "PressurePlate": return PressurePlate(position = position, block_affected_pos = block_affected_pos)
    elif code == "Door": return Door(position = position)
    
# ================== Auxiliary Methods ==================

def convert_vec3_to_key(vec):
    x = round(vec[0])
    y = round(vec[1])
    z = round(vec[2])

    return (x, y, z)