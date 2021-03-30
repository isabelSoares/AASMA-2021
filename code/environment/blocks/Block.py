from ursina import Entity, color, scene

class Block(Entity):
	def __init__(self, position = (0,0,0), texture = 'white_cube', color = color.rgba(198,193,168)):
		super().__init__(
			parent = scene,
			position = position,
			model = 'cube',
			texture = texture,
			color = color
        )