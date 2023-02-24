# decode

import os
# import commands
import subprocess

import intercept.intercept_config
from intercept import intercept_main, intercept_config

apkNameList = []


#decode 1007 apks
def decode(config: intercept_config.InterceptConfig):

    input_apks_path = config.input_apks_path
    decoded_apks_path = config.decoded_apks_path

    # get apkNamelist_1007
    # for line in open("/home/xueling/apkAnalysis/invokeDetection/apkName_1007").readlines():

    apks = subprocess.getoutput('ls ' + input_apks_path).split('\n')
    print(apks)
    i = 1
    output_files = os.listdir(decoded_apks_path)
    for apk in apks:
        # decompile to smaliPath
        print(i)
        if apk in output_files:
            print(apk)
            print("exists!!!")
            i += 1
            continue

        else:
            # Pull off the ".apk" of the name of the output file
            cmd = "apktool d -r {}{} -o {}{}".format(input_apks_path, apk, decoded_apks_path, apk[:-4])
            print(cmd)
            os.system(cmd)
            i += 1



# move to library name
# def move():
#     apkNameList = set()
#     lines = open("/home/xueling/apkAnalysis/invokeDetection/decodeFile/nameList/branch").readlines()
#     print "len(lines): %d" %len(lines)
#     for line in lines:
#         line = line.strip() + ".apk"
#         apkNameList.add(line)
#     print "len(apkNameList): %d" % len(apkNameList)
#
#     files = os.listdir(decodeFilePath)
#     for line in apkNameList:
#         if line in files:
#             print "%s exists!!!" %line
#
#         else:
#             cmd = "mv %s%s %s" %(smaliPath, line, decodeFilePath)
#
#
#             print cmd
#             ret = os.system(cmd)
#             print ret
#             if ret == 256:
#                 fw = open("/home/xueling/apkAnalysis/invokeDetection/decodeFile/nameList/temp", "a")
#                 fw.write(line + "\n")
#                 fw.close()

if __name__ == '__main__':
    config = intercept_config.get_default_intercept_config()

    decode(config)


# move()
