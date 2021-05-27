import subprocess

lr_list = [0.2, 0.4, 0.6, 0.9]
gamma_list = [0.2, 0.4, 0.6, 0.9]
for lr in lr_list:
    for gamma in gamma_list:
            result = subprocess.run('python .\maze.py rlearning map2 ' + str(lr) + ' ' + str(gamma), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
            print('------')
            print('LR = ' + str(lr) + '; GAMMA = ' + str(gamma) + ':')
            print(result.stdout[-5:])
            print('------')