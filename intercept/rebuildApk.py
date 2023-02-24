
import os
import pexpect
import sys


# for line in open("/home/xueling/apkAnalysis/invokeDetection/apkName_1007").readlines():
#     line = line.strip() + ".apk"
#     apkNameList.append(line)
# print len(apkNameList)
from intercept import intercept_config


def rebuild(config):
    i = 1
    for apkName in os.listdir(decoded_apks_path):
        print(i)
        apk_name_with_suffix = apkName + ".apk"

        if apk_name_with_suffix in os.listdir(rebuiltApksPath):
            print("Exists!!!!")
            # don't rebuild an apk that has already been rebuilt
            continue

        else:
            # rebuild the first file name, and place the output as the second file name
            cmd = "apktool b {}{} -o {}{}".format(decoded_apks_path, apkName, rebuiltApksPath, apk_name_with_suffix)
            print(cmd)
            os.system(cmd)
        i += 1

if __name__ == '__main__':
    config = intercept_config.get_default_intercept_config()
    # rebuildApkPath = "/home/xueling/apkAnalysis/invokeDetection/rebuildApk/branch/"
    # decodeFilePath = "/home/xueling/apkAnalysis/invokeDetection/decodeFile/branch/"
    decoded_apks_path = "decoded-apks/"
    rebuiltApksPath = "rebuilt-apks/"

    rebuild(config)