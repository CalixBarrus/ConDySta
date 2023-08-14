# install apk (10 app each batch) and start the app on device


import os
import webbrowser
import time
import subprocess
from typing import List

from intercept import intercept_config

from util import logger
from util.subprocess import run_command

logger = logger.get_logger('intercept', 'install')


def uninstall_apk(package_name):
    cmd="adb uninstall {}".format(package_name)
    logger.debug(cmd)
    cmd_result = getCmdExecuteResult(cmd)


def getCmdExecuteResult(cmd):
    tmp = os.popen(cmd).readlines()
    return tmp


def getPackageName(apk_name, signed_apk_path):
    install_name = os.path.join(signed_apk_path, apk_name)
    cmd = 'aapt dump badging "{}" '.format(install_name)
    logger.debug(cmd)
    str= getCmdExecuteResult(cmd)[0].split(" ")[1]
    return str[6:-1]


def getApkMainIntent(packageName):
    """
    :param packageName: packageName resulting from getPackageName call.
    :return: String that can be used as an Intent to launch the main activity of
    the apk.
    """
    cmd='adb shell dumpsys package {}'.format(packageName)
    logger.debug(cmd)
    exeResult= getCmdExecuteResult(cmd)
    #print exeResult
    for index, val in enumerate(exeResult):
        #print index ,val
        if val.strip("\r\n").strip()=='Action: "android.intent.action.MAIN"':
            return exeResult[index-1].strip().split(" ")[1]


def startApk(packageName):
    try:
        packagename_mainActivity = getApkMainIntent(packageName)
        logger.debug(packagename_mainActivity)
    except:
        logger.debug("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        packagename_mainActivity = packageName + "/"

    logger.debug(packagename_mainActivity)
    cmd = "adb shell am start {}".format(packagename_mainActivity)
    logger.debug(cmd)
    logger.debug(getCmdExecuteResult(cmd))


def installApk(apkName, signed_apk_path):
    apkName = os.path.join(signed_apk_path, apkName)
    # -r, replace the app if already installed
    # -t, allows test packages

    cmd='adb  install "{}"'.format(apkName)
    logger.debug(cmd)
    return os.system(cmd)

def check_device_is_ready():
    cmd = 'adb devices'
    result = run_command(cmd.split())
    return result.splitlines()[1].__contains__("device")


# def batch(apkNameList,index):
#     packageNameList=[]
#     count_installed = 0
#     print("the {}dth batch:".format(index))
#     for i in range(0,len(apkNameList)):
#         print(apkNameList[i][:-4])
#
#     apkName_installed=[]
#     for apkName in apkNameList:                      # install 10apk
#         # print "%s installing"%apkName
#         if ((installApk(apkName)) == 0):
#             count_installed += 1
#             print("apk_installed: %d" % count_installed)
#             print(apkName[:-4])
#             apkName_installed.append(apkName)
#     print(" the appInstalled in this bath:")
#     print(apkName_installed)
#     for apkName in apkName_installed:
#         packageName = getPackageName(apkName, signedApkPath)
#         packageNameList.append(packageName)
#         # packageNameListALL.append(packageName)
#
#     # print "start Apk..........................."
#     # # start APK
#     # for packageName in packageNameList:
#     #     startApk(packageName)
#     # time.sleep(30)
#     print("login to the app....................")
#     # time.sleep(180)
#     console=input("delete all apk in this batch,enter y")
#     if console =='y':
#         for packageName in packageNameList:
#             uninstall_apk(packageName)


# def installAndStart():
#     apkNameList=[]       # complete list
#     apkNameList10N=[]        # 10 apks
#     apkNameList_lastbatch = []
#     count = 0
#     # # get from folder
#     # for i in os.listdir(apk_signedPath):
#     #     if os.path.isfile(os.path.join(apk_signedPath, i)):
#     #         if i[-4:] == '.apk':
#     #             apkName = i
#     #             apkNameList.append(apkName)
#     # print len(apkNameList)
#     #
#     # index=1
#     # for apkName in apkNameList:
#     #     apkNameList10N.append(apkName)
#     #     count+=1
#     #     if count%10 == 0:
#     #         # print apkNameList10N
#     #         batch(apkNameList10N, index)            #rank every 10 apks
#     #         index += 1
#     #         apkNameList10N = []
#     #
#     #     if (len(apkNameList) - count) < (len(apkNameList)%10):
#     #         apkNameList_lastbatch.append(apkName)
#     #
#     #     if len(apkNameList_lastbatch) > 0 and count == len(apkNameList):
#     #         batch(apkNameList_lastbatch, index)
#     #
#     # print apkNameList10N
#
#
#     # get from temp
#     temp = open("/home/xueling/apkAnalysis/invokeDetection/temp").readlines()
#     print(len(temp))
#     list2 = []
#     for line in temp:
#         line = line.strip() + ".apk"
#         list2.append(line.strip())
#     batch(list2, 0)

if __name__ == '__main__':
    configuration = intercept_config.get_default_intercept_config()

    # apk_signedPath = "/home/xueling/apkAnalysis/invokeDetection/apk_signed/test/"
    # signedApkPath = "signed-apks/"
    # signedApkPath = "rebuilt-apks/"
    configuration.signed_apks_path = "input-apks/"
    apkName = "FieldSensitivity1.apk"

    
    # signedApkPath = "../test-apks/"
    # apkName = "art.coloringpages.paint.number.zodiac.free.apk"

    adbOnPath = True
    if not adbOnPath:
        platformPath = "/home/xueling/Android/Sdk/platform-tools"
    packageNameListALL = []
    apkNameList = []

    # moveToWork()
    # openWeb()

    # installAndStart()

    apkPackageName = getPackageName(apkName, configuration.signed_apks_path)
    uninstall_apk(apkPackageName)

    # installApk(apkName, configuration.signed_apks_path)

    # startApk(apkPackageName)

    # apkPackageName = getPackageName(apkName, signedApkPath)
    # startApk(apkPackageName)


    # moveToDone()
