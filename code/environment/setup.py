from ursina import window, camera
from ursina import Vec3, Entity

def setup_window(fps_counter = False):
    window.fps_counter.enabled = fps_counter

def setup_camera(orthographic = True, position = Vec3(0,0,0), look_at = Vec3(0,0,0), fov = 20):
    camera.orthographic = orthographic
    camera.position = position
    camera.look_at(Entity(position=look_at))
    camera.fov = fov