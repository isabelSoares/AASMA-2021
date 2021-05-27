# script does not work without changing maze and RLearning agent
# the script was being used to test different learning rates and discount factors

import subprocess

lr_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
gamma_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
for lr in lr_list:
    for gamma in gamma_list:
            result = subprocess.run('python .\maze.py rlearning map2 ' + str(lr) + ' ' + str(gamma), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
            print('------')
            print('LR = ' + str(lr) + '; GAMMA = ' + str(gamma) + ':')
            print(result.stdout[-5:])
            print('------')