# executtion time for execute FlowDroid

import re
import os
# import commands
# import subprocess
import time


# ### get execution time for ConDySTA
# def getExeTime(app):
#     # print app
#     sumTime = 0
#     lines = open(result1_path + app).readlines()
#     for line in lines:
#         match = re.search(r'took .* seconds', line)
#         if match:
#             # print match.group(0)
#             seconds_1 = re.search(r'(?<=took ).*(?= seconds)', match.group(0)).group(0)
#             sumTime += float(seconds_1)
#             # print seconds_1
#     try:
#         lines = open(result2_path + app).readlines()
#         for line in lines:
#             match = re.search(r'took .* seconds', line)
#             if match:
#                 # print match.group(0)
#                 seconds_2 = re.search(r'(?<=took ).*(?= seconds)', match.group(0)).group(0)
#                 # print seconds_2
#                 sumTime += float(seconds_1)
#     except:
#         print "Eroor"
#
#     return sumTime
#
# result1_path = "/Users/xueling/Desktop/research/hybrid_paper2/result_1/"
# result2_path = "/Users/xueling/Desktop/research/hybrid_paper2/result_2/"
#
# # result1_path = "/Users/xueling/Desktop/research/hybrid_paper2/result_1_batch2/"
# # result2_path = "/Users/xueling/Desktop/research/hybrid_paper2/result_2_batch2_path/"
#
# apps = open('/Users/xueling/Desktop/research/hybrid_paper2/temp/temp.txt').readlines()
#
# # apps = ["com.kakao.story"]
#
# lists = os.listdir(result1_path)
# for app in apps:
#     app = app.strip()
#     # print app
#
#     if app in lists:
#         exeTime = getExeTime(app)
#         print app +  ";;" + str(exeTime)


# get execution time for pure FlowDroid

def getExeTime(app):

    # ###read from giant file
    # logPath_1 = "/Users/xueling/Desktop/research/hybrid_paper2/comparision_result/"
    # logPath_2 = "/Users/xueling/Desktop/research/hybrid_paper2/comparision_result_batch2/"
    #
    #
    # cmd_1 = "grep \"App under test: " + app + "\" " + logPath_1 + " -r"
    # cmd_2 = "grep \"App under test: " + app + "\" " + logPath_2 + " -r"
    #
    #
    # # print cmd_1
    # ret = commands.getoutput(cmd_1)
    #
    # if not ret:
    #     ret = commands.getoutput(cmd_2)
    #
    # ret = ret.replace("//", "/")
    # # print ret
    #
    # path = ret.split(":App under test:")[0]
    # # print "path: " + path

    path = "/Users/xueling/Desktop/research/hybrid_paper2/comparision_result/temp.txt"
    lines = open(path).readlines()


    sumTime = 0

    flag = 0
    segment = list()

    for line in lines:
        line = line.strip()

        if "End: " in line and app in line:
            break

        # if "App under test: " in line and app in line:
        elif "Begin: " in line and app in line:
            flag = 1
            segment.append(line)
        elif flag == 1:
            segment.append(line)
        # elif "App under test: " in line and app not in line and flag ==1:
        # elif "Begin: " in line and app not in line and flag == 1:
        else:
            continue

    for line in segment:
        match = re.search(r'took .* seconds', line)
        if match:
            # print match.group(0)
            seconds_1 = re.search(r'(?<=took ).*(?= seconds)', match.group(0)).group(0)
            # print float(seconds_1)
            sumTime += float(seconds_1)
    return sumTime


    # #read from individual file
    # sumTime = 0
    # for line in open("/Users/xueling/Desktop/research/hybrid_paper2/comparision_result_batch2/" + app).readlines():
    #     match = re.search(r'took .* seconds', line)
    #     if match:
    #         # print match.group(0)
    #         seconds_1 = re.search(r'(?<=took ).*(?= seconds)', match.group(0)).group(0)
    #         # print float(seconds_1)
    #         sumTime += float(seconds_1)
    # return sumTime
# #
#
#

##from giant files
path = '/Users/xueling/Desktop/research/hybrid_paper2/comparision_result/'
files = ["out_part1", "out_part2", "out_part3", "out_part4"]
files = ["temp.txt"]

apps = []
for file in files:
    print(file)
    lines = open(path + file).readlines()
    for line in lines:
        # print line.strip()
        if "Begin: " in line and ".apk" in line:
            app = re.search(r'(?<=Begin: ).*(?=.apk)', line.strip()).group(0)
            # print app
            apps.append(app)




##from single files:
# apps = os.listdir("/Users/xueling/Desktop/research/hybrid_paper2/comparision_result_batch2/")
for app in apps:
    app = app.strip()
    # print (app)
    exeTime = getExeTime(app)
    print (app + ": " + str(exeTime))

# cmd = 'java -jar /Users/xueling/Desktop/research/SACMAT_2020/soot-infoflow-cmd-jar-with-dependencies.jar  -a /Users/xueling/Desktop/research/hybrid_paper2/apk_org_batch2/com.creativemobile.DragRacing.apk -p /Users/xueling/Desktop/research/hybrid_paper2/platforms/ -s /Users/xueling/Desktop/research/hybrid_paper2/SourceAndSinks_comparision.txt'
# os.system(cmd)