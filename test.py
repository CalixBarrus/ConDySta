import re
import os
#
# # out_1 = '/Users/xueling/Desktop/hybrid/comparision_result_batch2/'
#
# app = 'com.mxtech.videoplayer.ad'
# leakResult = []
# lines = open(out_1).readlines()
# lines.reverse()
#
# source_count_UI = 0
# source_count_PII = 0
#
# ##get the result block
# for line in lines:
#     line = line.strip()
#     if "Begin: " in line or "End: " in line:
#         print line
#     if "[main] INFO soot.jimple.infoflow.android.SetupApplication" in line:
#         leakResult.append(line)
#     else:
#         break
#
# leakResult.reverse()
#
# for line in leakResult:
#     print line

# for line in leakResult:
#     stmt_1 = line.split("on line")[0]
#     # print stmt_1
#
#     if "The sink" in line:
#         sink = re.search(r'<.*?>', stmt_1).group(0)
#         print 'sink: ' + sink
#
#     else:
#         match = re.search(r'<.*?>', stmt_1)
#         if match:
#             source = match.group(0)
#             # print source
#             if 'android.widget' in source:
#                 source_count_UI += 1
#                 print 'IU source ' + str(source_count_UI) + ': ' + source
#             else:
#                 source_count_PII += 1
#                 print 'PII source ' + str(source_count_PII) + ': ' + source


# ### the average imtermedia source
# import os
# path_1 = '/Users/xueling/Desktop/research/hybrid_paper2/PII_sourceSig/'
# apps = os.listdir(path_1)
# sum = 0
# for app in apps:
#     if ".DS_Store" == app:
#         continue
#     # print(app)
#     lines = open(path_1+app).readlines()
#     # print(len(lines))
#     sum += len(app)
# average = sum / len(apps)
# print(average)
#
# path_2 = '/Users/xueling/Desktop/research/hybrid_paper2/PII_sourceSig_batch2/'
# apps = os.listdir(path_2)
# sum = 0
# for app in apps:
#     if ".DS_Store" == app:
#         continue
#     # print(app)
#     lines = open(path_2+app).readlines()
#     # print(len(lines))
#     sum += len(app)
# average = sum / len(apps)
# print(average)


# ## average length of callStack, need to get avergae from the 2 files
#
# import os
# paths = ['/Users/xueling/Desktop/research/hybrid_paper2/input_log_path/','/Users/xueling/Desktop/research/hybrid_paper2/log_batch2/']
#
# sum_mean = 0
# for path in paths:
#     apps = os.listdir(path)
#     for app in apps:
#         print(app)
#         if ".DS_Store" == app:
#             continue
#         # for each app's input_log_path
#         callStacks_count = 0
#         callStacks_len = 0
#         lines = open(path+app).readlines()
#         callStack = list()
#         flag = 0
#         for line in lines:
#             line = line.strip()
#             if "W System.err: java.lang.Exception:" in line:
#                 # print(line)
#                 flag = 1
#                 callStack.append(line)
#
#             if flag == 1 and "W System.err:" in line and "W System.err: java.lang.Exception:" not in line:
#                 # print(line)
#                 callStack.append(line)
#
#             if flag == 1 and "W System.err: java.lang.Exception:" in line:
#                 callStacks_len += len(callStack)
#                 callStacks_count += 1
#                 callStack = []
#                 callStack.append(line)
#             else:
#                 continue
#         if callStacks_count > 0:
#             mean = callStacks_len/callStacks_count
#             print(mean)
#             sum_mean += mean
#             # print sum_mean
#     average = sum_mean / len(apps)
#     print("average for " + path + ": " + str(average))
#     sum_mean = 0


# #get result block from eclipse for several apps
#
# out = '/Users/xueling/Desktop/research/hybrid_paper2/supplementExpr/sourceToOurSource/eclipseOut'
# lines = open(out).readlines()
# # lines.reverse()
#
# leakResult = list()
# for line in lines:
#     line = line.strip()
#     if line.startswith("Begin: "):
#         print line
#     if "[main] INFO soot.jimple.infoflow.android.SetupApplication - Found" in line:
#         # leakResult.append(line)
#         print line
#
#     if line.startswith("End: "):
#         # for item in leakResult:
#         #     print item.strip()
#         # leakResult = []
#         print line
#     else:
#         continue
#Build tree
# import buildTrees
# leakStackTraces = buildTrees.buildTrees('com.disney.WMWLite')

path = "/Users/xueling/Desktop/research/hybrid_paper2/"
apps = open(path+"temp.txt").readlines()

for app in apps:
    # try:
    #     # cmd = "cp " + path + 'apk_1' + app + ".apk" + path + "comparasion_apk"
    #     os.system("cp " + path + 'apk_1/' + app.strip() + ".apk " + path + "comparasion_apk/")
    #
    # except:
    os.system("cp " + path + 'apk_org_batch2/' + app.strip() + ".apk " + path + "comparasion_apk/")

