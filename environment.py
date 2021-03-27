from ursina import *

class Block(Button):
	def __init__(self, position = (0,0,0), texture = 'white_cube', color = color.rgba(198,193,168)):
		super().__init__(
			parent = scene,
			position = position,
			model = 'cube',
			origin_y = 0.5,
			texture = texture,
			color = color
        )

for x in range(20):
	for y in range(20):
		Block(position = (x-10,0,y-10))

Block(position = (5,2,5), color = color.rgba(34,47,98))
Block(position = (5,3,5), color = color.rgba(34,47,98))
Block(position = (5,4,5), color = color.rgba(34,47,98))
