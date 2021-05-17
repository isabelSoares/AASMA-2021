import glob
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

list_of_maps = ['map1', 'map2', 'map3', 'map4', 'map5', 'map6', 'map7']
agent_types = ['random', 'reactive', 'deliberative', 'rlearning']

#to run every agent and every map
#for agent_type in agent_types:
#    for map in list_of_maps:
#        for i in range(10):
#            os.system('python .\maze.py ' + agent_type + ' ' + map)

#for map in list_of_maps:
#    for i in range(10):
#        os.system('python .\maze.py ' + 'random' + ' ' + map)

number_of_tests = 10

x = np.arange(len(agent_types))
width = 0.3

for map_name in list_of_maps:
    metrics = {}
    for agent_type in agent_types:
        list_of_metric_files = glob.glob('./exports/' + agent_type + '/' + map_name + '/*.csv')
        if not list_of_metric_files:
            for column in df.columns:
                if column not in metrics:
                    metrics[column] = [0] * len(agent_types)
                metrics[column][agent_types.index(agent_type)] = 0
            continue
        latest_metric_file = max(list_of_metric_files, key=os.path.getctime)
        #best_x_files = sorted(list_of_metric_files, key=os.path.getctime, reverse=True)[:number_of_tests]
        df = pd.read_csv(latest_metric_file)
        last_row = df.iloc[-1]

        i = 0
        for column in df.columns:
            if column not in metrics:
                metrics[column] = [0] * len(agent_types)
            #metric_files = []
            #for f in best_x_files:
                #last_row = df.iloc[-1]
                #metric_files.append(last_row[i])
            #metric_files = sorted(metric_files)
            #metric_files = metric_files[2:number_of_tests-2]
            #metrics[column][agent_types.index(agent_type)] = sum(metric_files)/len(metric_files)
            metrics[column][agent_types.index(agent_type)] = last_row[i]

            i += 1
    
    fig = None
    ax = None
    for metric in metrics:
        _dir = './graphs/' + map_name + '/'
        if not os.path.exists(_dir):
            os.makedirs(_dir)

        if metric == 'Timestep':
            fig, ax = plt.subplots()

            ax.bar(x - width, metrics[metric], width, label='Timestep')

            ax.set_ylabel(metric)
            ax.set_title(metric)
            ax.set_xticks(x)
            ax.set_xticklabels(agent_types)

            plt.savefig(_dir + metric)
            plt.close("all")
        
        elif 'BLUE' in metric:
            fig, ax = plt.subplots()
            ax.bar(x - width/2, metrics[metric], width, label='BLUE')
        
        elif 'ORANGE' in metric:
            ax.bar(x + width/2, metrics[metric], width, label='ORANGE')

            metric = metric.replace(' - ORANGE', '')
            ax.set_ylabel(metric)
            ax.set_title(metric)
            ax.set_xticks(x)
            ax.set_xticklabels(agent_types)
            ax.legend()

            fig.tight_layout()

            plt.savefig(_dir + metric)
            plt.close("all")


# if needed

Timestep = []
Steps_BLUE = []
Steps_ORANGE = []
Pressure_Plates_Activated_BLUE = []
Pressure_Plates_Activated_ORANGE = []
Blocks_Placed_BLUE = []
Blocks_Placed_ORANGE = []
Blocks_Removed_BLUE = []
Blocks_Removed_ORANGE = []
Messages_Sent_BLUE = []
Messages_Sent_ORANGE = []