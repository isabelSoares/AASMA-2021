from ursina import window, camera, Vec3, Entity, Text, Slider
from ursina.prefabs.dropdown_menu import DropdownMenu, DropdownMenuButton

def setup_window(fps_counter = False, borderless = True):
    window.fps_counter.enabled = fps_counter
    window.borderless = borderless

def setup_camera(orthographic = True, position = Vec3(0,0,0), look_at = Vec3(0,0,0), fov = 20):
    camera.orthographic = orthographic
    camera.position = position
    camera.look_at(Entity(position=look_at))
    camera.fov = fov


def setup_panel(panel, min, start_value, max, step, agents):

    # ======== Information Display ========
    lines_of_informations = [
        "Time: 0",
        "Steps (individualy): 0",
        "Pressure Plate Activations (individualy): 0",
        "Blocks Placed by Agents (individualy): 0",
        "Blocks Removed by Agents (individualy): 0"
    ]

    spacing = .08
    for index in range(len(lines_of_informations)):
        information = lines_of_informations[index]
        item = Text(text=information, parent=panel.item_parent, scale_override=1.75, origin=(-.5, 0), position=(-.45, .4 - + index * spacing))

    # ======== Input Display ========
    slider = Slider(min, max, default=start_value, step=step, parent=panel.input_speed, scale=1.5, position=(-.25 * 1.5, - .075))

    # ======== Input Player Display ========
    text = Text(text="All Players Selected", parent=panel.input_player, scale_override=1.5, origin=(-.5, 0), position=(0, -.15), x=-.25)
    # TODO: Dynamically add possible player (not sure how to add buttons)
    drop_down_button = DropdownMenu('Metrics refers to...', parent=panel.input_player, position=(0, -.175), buttons=(
        DropdownMenuButton('All Players'),
        DropdownMenuButton('BLUE'),
        DropdownMenuButton('GREEN'),
    ))

    for button in drop_down_button.buttons:
        def on_click(button=button): text.text = button.text + " Selected"
        
        button.on_click = on_click

    drop_down_button.scale = 2 * drop_down_button.scale
    drop_down_button.x = drop_down_button.x - drop_down_button.scale[0] / 2