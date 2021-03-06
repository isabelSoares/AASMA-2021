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


def setup_panel_control(panel, min, start_value, max, step, agents):

    # ======== Information Display ========
    lines_of_informations = [
        "Time: 0",
        "Steps (individualy): 0",
        "Pressure Plate Activations (individualy): 0",
        "Blocks Placed by Agents (individualy): 0",
        "Blocks Removed by Agents (individualy): 0",
        "Messages Sent by Agents (individualy): 0",
    ]

    spacing = .08
    for index in range(len(lines_of_informations)):
        information = lines_of_informations[index]
        item = Text(text=information, parent=panel.item_parent, scale_override=1.75, origin=(-.5, 0), position=(-.45, .4 - + index * spacing))

    # ======== Input Display ========
    slider = Slider(min, max, default=start_value, step=step, parent=panel.input_speed, scale=1.5, position=(-.25 * 1.5, - .125))

    # ======== Input Player Display ========
    text = Text(text="All Players Selected", parent=panel.input_player, scale_override=1.5, origin=(-.5, 0), position=(0, -.2), x=-.25)

    drop_down_button = DropdownMenu('Metrics refers to...', parent=panel.input_player, position=(0, -.225), buttons=(DropdownMenuButton('All Players'),))
    agents_list = list(agents)
    for agent_index, agent_name in enumerate(agents_list):
        drop_down_button.buttons += (DropdownMenuButton(agent_name, world_parent=drop_down_button, position=(0, - (agent_index + 2) *.99)),)
        drop_down_button.buttons[agent_index + 1].scale = drop_down_button.buttons[0].scale

    for button in drop_down_button.buttons:
        def on_click(button=button): text.text = button.text + " Selected"
        button.on_click = on_click

    drop_down_button.scale = 2 * drop_down_button.scale
    drop_down_button.x = drop_down_button.x - drop_down_button.scale[0] / 2

def setup_panel_messages(panel):

    # ======== Input Message Type ========
    text = Text(text="Need Help Selected", parent=panel.input_message_type, scale_override=1.5, origin=(-.5, 0), position=(0, .4), x=-.25)
    drop_down_button = DropdownMenu('Messages of type...', parent=panel.input_message_type, position=(0, .375), buttons=(
        DropdownMenuButton('Need Help'),
        DropdownMenuButton('Being Helped'),
        DropdownMenuButton('Info')))

    for button in drop_down_button.buttons:
        def on_click(button=button): text.text = button.text + " Selected"
        button.on_click = on_click

    drop_down_button.scale = 2 * drop_down_button.scale
    drop_down_button.x = drop_down_button.x - drop_down_button.scale[0] / 2

