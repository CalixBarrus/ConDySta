'''
This script takes a single flowdroid log file that has been run on many apks and
created different files for each apk, with each file containing the corresponding
flowdroid log statements.
'''

import os
# import commands
import subprocess

lines = open('/Users/xueling/Desktop/hybrid/out.txt').readlines()
print(len(lines))
results = []
flag = 0

for i in range(0, len(lines)):
    if lines[i]:
        line = lines[i].strip()
        if "App under test:" in line and flag == 0:
            flag += 1
            temp = []
            temp.append(line)

        elif "App under test:" in line and flag != 0:
            results.append(temp)
            temp = []
            temp.append(line)
            flag += 1

        elif i == (len(lines) - 1):
            results.append(temp)

        else:
            print(line)
            temp.append(line)

print(len(results))

for result in results:
    app = result[0].split(': ')[1]
    fw = open('/Users/xueling/Desktop/hybrid/FlowDroidLog/' + app, 'a+')
    for line in result:
        fw.writelines(line + '\n')
