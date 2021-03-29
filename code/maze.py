from ursina import *
app = Ursina()
# Import environment
from environment.setup import setup_window, setup_camera
from environment.World import World
# Import agent
from agent import agent


# Call construction of World
center, size = (0, 0, 0), (10, 5)
world = World(center, size)

# Setup window and camera
setup_window()
setup_camera(position = Vec3(50,50,50), look_at = center)

def update():
    if held_keys['q']:
        print("teste")

app.run()
