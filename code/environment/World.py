import math
import environment.blocks.Block as GeneralBlock

class World():
    def __init__(self, center = (0,0,0), size = (5, 5)):
		
        # Create floor
        radius_x = math.ceil((size[0] - 1) / 2)
        radius_y = math.ceil((size[1] - 1) / 2)
        from_position = (center[0] - radius_x, center[1] - radius_y)
        to_position = (center[0] + radius_x, center[1] + radius_y)
        create_floor(from_position, to_position)

def create_floor(from_position, to_position):
    for x in range(from_position[0], to_position[0] + 1, 1):
        for y in range(from_position[1], to_position[1] + 1, 1):
            GeneralBlock.Block(position = (x, 0, y))