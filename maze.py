from ursina import *
app = Ursina()
import environment
import agent

window.fps_counter.enabled = False

camera.orthographic = True
camera.position = Vec3(50,50,50)
camera.look_at(Entity(position=(0,0,0)))
camera.fov = 20

def update():
    if held_keys['q']:
        print("teste")

app.run()
