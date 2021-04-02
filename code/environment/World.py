from ursina import Vec3, color
from environment.blocks.FloorBlock import FloorBlock
from environment.blocks.WallBlock import WallBlock
from environment.blocks.TriggersBlock import TriggersBlock
from environment.blocks.PressurePlate import PressurePlate
from environment.blocks.Door import Door

import math

class World():
    def __init__(self, center = (0,0,0), size = (5, 5)):

        # Initializing variables
        self.static_map = {}
        self.agents_map = {}
        self.entities_map = {}
        self.count = 0
		
        # Create floor
        radius_x = math.ceil((size[0] - 1) / 2)
        radius_y = math.ceil((size[1] - 1) / 2)
        from_position = (center[0] - radius_x, center[1] - radius_y)
        to_position = (center[0] + radius_x, center[1] + radius_y)
        self.create_floor(from_position, to_position)

    def update(self):
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
        
    def delete_static_block(self, position):
        position = convert_vec3_to_key(position)
        if position not in self.static_map: return
        del self.static_map[position]

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

    # ================== Auxiliary Methods ==================

    def create_floor(self, from_position, to_position):
        for x in range(from_position[0], to_position[0] + 1, 1):
            for y in range(from_position[1], to_position[1] + 1, 1):
                block = create_block_from_code("Floor", (x, 0, y))
                self.static_map[(x, 0, y)] = block

def create_block_from_code(code, position, block_affected_pos = None):

    # Manual Switch (sadly)
    if code == "Floor": return FloorBlock(position = position)
    elif code == "Wall": return WallBlock(position = position)
    elif code == "PressurePlate": return PressurePlate(position = position, block_affected_pos = block_affected_pos)
    elif code == "Door": return Door(position = position)
    
# ================== Auxiliary Methods ==================

def convert_vec3_to_key(vec):
    x = round(vec[0])
    y = round(vec[1])
    z = round(vec[2])

    return (x, y, z)