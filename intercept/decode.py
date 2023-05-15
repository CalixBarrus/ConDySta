# decode
import copy
import os
# import commands
import subprocess

import intercept.intercept_config
from intercept import intercept_main, intercept_config

apkNameList = []

def decode(config: intercept_config.InterceptConfig):
    print("Decoding input APKs...")

    input_apks_path = config.input_apks_path
    decoded_apks_path = config.decoded_apks_path
    output_files = os.listdir(decoded_apks_path)

    recursive = config.is_recursive_on_input_apks_path

    for item in os.listdir(input_apks_path):
        if os.path.isfile(os.path.join(input_apks_path, item)) and item.endswith(".apk"):
            apk = item
            if apk in output_files:
                print(f"APK {item} already decompiled. Skipping.")
                continue

            else:
                # decompile to decoded_apks_path
                # Pull off the ".apk" of the name of the output file
                cmd = "apktool d '{}' -o '{}'".format(
                    os.path.join(input_apks_path, apk),
                    os.path.join(decoded_apks_path, apk[:-4]))
                print(cmd)
                os.system(cmd)

        if recursive and os.path.isdir(os.path.join(input_apks_path, item)):
            # Recursively check subdirectories for APKs.
            config_copy = copy.deepcopy(config)
            config_copy.input_apks_path = \
                os.path.join(config_copy.input_apks_path, item)
            decode(config_copy)



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
