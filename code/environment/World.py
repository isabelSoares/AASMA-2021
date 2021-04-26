from ursina import Vec3, color, Text, Entity, camera, destroy, ursinamath
from environment.blocks.FloorBlock import FloorBlock
from environment.blocks.AgentBlock import AgentBlock
from environment.blocks.WinningPostBlock import WinningPostBlock
from environment.blocks.WallBlock import WallBlock
from environment.blocks.TriggersBlock import TriggersBlock
from environment.blocks.PressurePlate import PressurePlate
from environment.blocks.Door import Door
from environment.messages.Message import Message

import math

class Metrics:
    def __init__(self):
        self.selected_agent = None

        self.time = 0
        self.steps = {}
        self.pressure_plates_activated = {}
        self.blocks_placed = {}
        self.blocks_removed = {}
        self.messages_sent = {}

    def initialize_for_agent(self, agent):
        self.steps[agent] = 0
        self.pressure_plates_activated[agent] = 0
        self.blocks_placed[agent] = 0
        self.blocks_removed[agent] = 0
        self.messages_sent[agent] = 0

    def export_content(self, panel):
        selection = panel.input_player.children[0].text.replace(" Selected", "")
        # No ternary operator :'(
        self.selected_agent = None if selection == "All Players" else selection

        steps, pressure_plates_activated, blocks_placed, blocks_removed, messages_sent = 0, 0, 0, 0, 0
        if (self.selected_agent == None):
            for agent in self.steps: steps += self.steps[agent]
            for agent in self.pressure_plates_activated: pressure_plates_activated += self.pressure_plates_activated[agent]
            for agent in self.blocks_placed: blocks_placed += self.blocks_placed[agent]
            for agent in self.blocks_removed: blocks_removed += self.blocks_removed[agent]
            for agent in self.messages_sent: messages_sent += self.messages_sent[agent]

        else:
            steps = self.steps[self.selected_agent]
            pressure_plates_activated = self.pressure_plates_activated[self.selected_agent]
            blocks_placed = self.blocks_placed[self.selected_agent]
            blocks_removed = self.blocks_removed[self.selected_agent]
            messages_sent = self.messages_sent[self.selected_agent]

        optional_tag = ""
        if self.selected_agent != None: optional_tag = " (individualy)"
        information_to_display = [
            "Time: " + str(self.time),
            "Steps" + optional_tag + ": " + str(steps),
            "Pressure Plate Activations" + optional_tag + ": " + str(pressure_plates_activated),
            "Blocks Placed by Agents" + optional_tag + ": " + str(blocks_placed),
            "Blocks Removed by Agents" + optional_tag + ": " + str(blocks_removed),
            "Messages Sent by Agents" + optional_tag + ": " + str(messages_sent),
        ]

        for index in range(len(information_to_display)):
            information = information_to_display[index]
            if index < len(panel.item_parent.children): panel.item_parent.children[index].text = information

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

        # Initializing messages
        self.messages_id_count = 1
        self.need_help_messages = []
        self.being_helped_messages = []
        self.info_messages = []
		
        # Create floor
        radius_x = math.ceil((size[0] - 1) / 2)
        radius_y = math.ceil((size[1] - 1) / 2)
        from_position = (center[0] - radius_x, center[1] - radius_y)
        to_position = (center[0] + radius_x, center[1] + radius_y)
        self.create_floor(from_position, to_position)
    
    def distance_provider(self, agent_name, agent):
        goal_block = self.get_goal_block(agent_name)
        return ursinamath.distance(goal_block, agent)

    def update(self):

        self.metrics.time = self.metrics.time + 1

        for pos in self.entities_map:
            entity = self.entities_map[pos]
            if entity.update() & isinstance(entity, TriggersBlock): 
                block_affected_pos = entity.get_block_affected_pos()
                block = self.get_entity(block_affected_pos)
                entity.affect_block(block)
        


    # ================== Attributes Management ==================

    def get_goal_block(self, agent_name):
        if agent_name in self.goal_map: return self.goal_map[agent_name]
        else: return None

    def add_goal_block(self, agent_name, block):
        self.goal_map["Agent " + agent_name] = block

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
        # Update metric
        tmp_agent_name = agent_name.replace("Agent ", "")
        self.metrics.blocks_placed[tmp_agent_name] += + 1
        
    def delete_static_block(self, position):
        position = convert_vec3_to_key(position)
        if position not in self.static_map: return
        destroy(self.static_map[position])
        del self.static_map[position]
    
    def break_agent_block(self, position, agent_name):
        self.delete_static_block(position)
        # Update metric
        tmp_agent_name = agent_name.replace("Agent ", "")
        self.metrics.blocks_removed[tmp_agent_name] += + 1

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

    def first_add_agent(self, position, agent):
        position = convert_vec3_to_key(position)
        self.agents_map[position] = agent
        self.metrics.initialize_for_agent(agent.name.replace("Agent ", ""))

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
        if current_position not in self.agents_map or current_position == updated_position: return

        agent = self.get_agent(current_position)
        self.add_agent(updated_position, agent)
        self.delete_agent(current_position)

        # Agent in the pressure plate?
        pressurePlateStepedOn = False
        entity = self.get_entity(updated_position)
        last_entity = self.get_entity(current_position)
        if (entity != None) & (type(entity).__name__ == "PressurePlate"):
            entity.state = True
            pressurePlateStepedOn = True
        elif (last_entity != None) & (type(last_entity).__name__ == "PressurePlate"):
            last_entity.state = False

        # Update metrics
        agent_name = agent.name.replace("Agent ", "")
        self.metrics.steps[agent_name] += + 1
        if pressurePlateStepedOn: self.metrics.pressure_plates_activated[agent_name] += + 1
    
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
        
        #for y in range(from_position[1], to_position[1] + 1, 1):
        #    block = create_block_from_code("WinningPost", (to_position[0] + 1, 0, y))
        #    self.goal_map[(to_position[0] + 1, 0, y)] = block
    
    # ==================== Message flow ====================

    def send_message(self, agent, position, needed_action, text):
        self.need_help_messages.append(Message(self.messages_id_count, agent, position, needed_action, text))
        self.messages_id_count += 1
        # Update metric
        tmp_agent_name = agent.replace("Agent ", "")
        self.metrics.messages_sent[tmp_agent_name] += + 1
    
    def going_to_solve_older_message(self):
        message = self.need_help_messages.pop()
        self.being_helped_messages[message.getId()] = message
        # Update metric
        tmp_agent_name = agent.replace("Agent ", "")
        self.metrics.messages_sent[tmp_agent_name] += + 1

        return message
    
    def solve_message(self, id):
        if id not in self.being_helped_messages: return
        destroy(self.being_helped_messages[id])
        del self.being_helped_messages[id]

    def export_messages_content(self, panel):
        number_of_messages = 5
        selection = panel.input_message_type.children[0].text.replace(" Selected", "")
        destroy(panel.messages)
        panel.messages = Entity(parent=panel)
        
        messages = []
        if selection == "Need Help":
            if len(self.need_help_messages) < number_of_messages: number_of_messages = len(self.need_help_messages)
            messages = self.need_help_messages[::-1]
            messages = messages[:number_of_messages]
        elif selection == "Being Helped":
            if len(self.being_helped_messages) < number_of_messages: number_of_messages = len(self.being_helped_messages)
            messages = self.being_helped_messages[::-1]
            messages = messages[:number_of_messages]
        elif selection == "Info":
            if len(self.info_messages) < number_of_messages: number_of_messages = len(self.info_messages)
            messages = self.info_messages[::-1]
            messages = messages[:number_of_messages]

        spacing = .06
        for message_index, message in enumerate(messages):
            text_to_add = message.agent + " @ " + str(message.position) + ": " + message.needed_action
            item = Text(text=text_to_add, parent=panel.messages, scale_override=1.5, origin=(-.5, 0), position=(-.45, .125 - message_index * spacing))


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