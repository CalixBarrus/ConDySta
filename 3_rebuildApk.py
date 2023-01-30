
import os
import pexpect
import sys


# for line in open("/home/xueling/apkAnalysis/invokeDetection/apkName_1007").readlines():
#     line = line.strip() + ".apk"
#     apkNameList.append(line)
# print len(apkNameList)

def rebuild():
    i = 1
    for apkName in os.listdir(decodeOutputFilePath):
        print(i)
        if os.path.isfile(os.path.join(decodeOutputFilePath, apkName)):
            continue

        if apkName in os.listdir(rebuiltApksPath):
            print("Exists!!!!")

        else:
            # rebuild the first file name, and place the output as the second file name
            cmd = "apktool b {}{} -o {}{}".format(decodeOutputFilePath, apkName, rebuiltApksPath, apkName)
            print(cmd)
            os.system(cmd)
        i += 1

if __name__ == '__main__':
    # rebuildApkPath = "/home/xueling/apkAnalysis/invokeDetection/rebuildApk/branch/"
    # decodeFilePath = "/home/xueling/apkAnalysis/invokeDetection/decodeFile/branch/"
    decodeOutputFilePath = "decoded-apks/"
    rebuiltApksPath = "rebuilt-apks/"
    apkNameList = []

    rebuild()