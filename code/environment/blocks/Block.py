from ursina import Entity, color, scene, Vec3

class Block(Entity):
	def __init__(self, position = (0,0,0), model = 'cube', texture = 'white_cube', color = color.rgba(198,193,168), scale = 1, origin = Vec3(0,0,0)):
		super().__init__(
			parent = scene,
			position = position,
			model = model,
			texture = texture,
			color = color,
			scale = scale,
			origin = origin
        )