import os
import numpy as np

list_of_maps = ['map1', 'map2', 'map3', 'map4', 'map5', 'map6', 'map7']
agent_type = 'reactive'

for map in list_of_maps:
    for i in range(10):
        os.system('python .\maze.py ' + agent_type + ' ' + map)