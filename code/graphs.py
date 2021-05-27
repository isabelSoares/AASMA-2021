import glob
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

list_of_maps = ['map1', 'map2', 'map3', 'map4', 'map5', 'map6', 'map7']
agent_types = ['reactive', 'deliberative', 'hybrid', 'rlearning']

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
        #latest_metric_file = max(list_of_metric_files, key=os.path.getctime)
        best_x_files = sorted(list_of_metric_files, key=os.path.getctime, reverse=True)[:number_of_tests]
        last_rows = []
        number_of_true_tests = 0
        for b_x_f in best_x_files:
            df = pd.read_csv(b_x_f)
            if (df.iloc[-1][0] == 400 and agent_type == 'deliberative')\
                or (df.iloc[-1][0] == 500 and agent_type == 'hybrid')\
                or df.iloc[-1][0] == 20000:
                continue
            number_of_true_tests += 1
            last_rows.append(df.iloc[-1])
        
        true_discount = 4 - (number_of_tests - number_of_true_tests)

        if true_discount < 0:
            true_discount = 0

        last_rows.sort(key=lambda x: x[0])
        last_rows = last_rows[true_discount%2 : number_of_tests - (true_discount - true_discount%2)]

        last_row = last_rows[0]
        for l_r in range(number_of_true_tests - true_discount):
            if l_r == 0:
                continue
            last_row += last_rows[l_r]
        last_row /= number_of_tests

        i = 0
        for column in df.columns:
            if column not in metrics:
                metrics[column] = [0] * len(agent_types)
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

            rect = ax.bar(x - width, metrics[metric], width, label='Timestep')

            ax.set_ylabel(metric)
            ax.set_title(metric)
            ax.set_xticks(x)
            ax.set_xticklabels(agent_types)

            ax.bar_label(rect, padding=3)

            plt.savefig(_dir + metric)
            plt.close("all")
        
        elif 'BLUE' in metric:
            fig, ax = plt.subplots()
            rect = ax.bar(x - width/2, metrics[metric], width, label='BLUE')
            ax.bar_label(rect, padding=3)
        
        elif 'ORANGE' in metric:
            rect = ax.bar(x + width/2, metrics[metric], width, label='ORANGE')

            metric = metric.replace(' - ORANGE', '')
            ax.set_ylabel(metric)
            ax.set_title(metric)
            ax.set_xticks(x)
            ax.set_xticklabels(agent_types)
            ax.legend()

            ax.bar_label(rect, padding=3)

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