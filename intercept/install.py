# install apk (10 app each batch) and start the app on device


import os
import webbrowser
import time
import subprocess
from typing import List

from util.input import ApkModel
from util.subprocess import run_command

from subprocess import CalledProcessError

import util.logger
logger = util.logger.get_logger(__name__)

# def check_adb_connection() -> bool: # Should this throw an exception?
#     cmd = ["adb", "devices"]

#     result = run_command(cmd)

#     if result.splitlines()[1].strip() == "":

#         logger.error(result)
#         return False
#         # raise AssertionError("Adb can't find device")

#     return True


def uninstall_apk(package_name):
    cmd="adb uninstall {}".format(package_name)
    logger.debug(cmd)
    cmd_result = getCmdExecuteResult(cmd)


def getCmdExecuteResult(cmd):
    tmp = os.popen(cmd).readlines()
    return tmp


def get_package_name(apk_path):
    cmd = ["aapt", "dump", "badging", apk_path]
    logger.debug(" ".join(cmd))
    result = run_command(cmd)

    # Example output:
    """
package: name='de.ecspride' versionCode='1' versionName='1.0' platformBuildVersionName='6.0-2438415' compileSdkVersion='23' compileSdkVersionCodename='6.0-2438415'
sdkVersion:'8'
targetSdkVersion:'17'
uses-permission: name='android.permission.READ_PHONE_STATE'
uses-permission: name='android.permission.SEND_SMS'
application-label:'StaticInitialization1'
application-icon-160:'res/drawable-mdpi-v4/ic_launcher.png'
application-icon-240:'res/drawable-hdpi-v4/ic_launcher.png'
application-icon-320:'res/drawable-xhdpi-v4/ic_launcher.png'
application-icon-480:'res/drawable-xxhdpi-v4/ic_launcher.png'
application: label='StaticInitialization1' icon='res/drawable-mdpi-v4/ic_launcher.png'
application-debuggable
launchable-activity: name='de.ecspride.MainActivity'  label='StaticInitialization1' icon=''
feature-group: label=''
  uses-feature: name='android.hardware.faketouch'
  uses-implied-feature: name='android.hardware.faketouch' reason='default feature for all apps'
  uses-feature: name='android.hardware.telephony'
  uses-implied-feature: name='android.hardware.telephony' reason='requested a telephony permission'
main
supports-screens: 'small' 'normal' 'large' 'xlarge'
supports-any-density: 'true'
locales: '--_--'
densities: '160' '240' '320' '480'
    """

    result = result.split('\n')[0].split(" ")[1]

    # str= getCmdExecuteResult(cmd)[0].split(" ")[1]
    return result[6:-1]


def getApkMainIntent(packageName):
    # TODO: refactor function
    """
    :param packageName: packageName resulting from getPackageName call.
    :return: String that can be used as an Intent to launch the main activity of
    the apk.
    """

    cmd='adb shell dumpsys package {}'.format(packageName)
    logger.debug(cmd)
    exeResult= getCmdExecuteResult(cmd)

    # Example Output:
    """
Activity Resolver Table:
  Non-Data Actions:
      android.intent.action.MAIN:
        40355f5 de.ecspride/.MainActivity filter 5381d72
          Action: "android.intent.action.MAIN"
          Category: "android.intent.category.LAUNCHER"
          AutoVerify=false

Key Set Manager:
  [de.ecspride]
      Signing KeySets: 4380

Packages:
  Package [de.ecspride] (a1a6f8a):
    userId=13009
    pkg=Package{9f9b9fb de.ecspride}
    codePath=/data/app/de.ecspride-1
    resourcePath=/data/app/de.ecspride-1
    legacyNativeLibraryDir=/data/app/de.ecspride-1/lib
    primaryCpuAbi=null
    secondaryCpuAbi=null
    versionCode=1 minSdk=8 targetSdk=17
    versionName=1.0
    splits=[base]
    apkSigningVersion=2
    applicationInfo=ApplicationInfo{920da18 de.ecspride}
    flags=[ DEBUGGABLE HAS_CODE ALLOW_CLEAR_USER_DATA ALLOW_BACKUP ]
    dataDir=/data/user/0/de.ecspride
    supportsScreens=[small, medium, large, xlarge, resizeable, anyDensity]
    timeStamp=2023-09-21 16:02:40
    firstInstallTime=2023-09-21 16:02:41
    lastUpdateTime=2023-09-21 16:02:41
    signatures=PackageSignatures{c005c71 [69b8f03]}
    installPermissionsFixed=true installStatus=1
    pkgFlags=[ DEBUGGABLE HAS_CODE ALLOW_CLEAR_USER_DATA ALLOW_BACKUP ]
    requested permissions:
      android.permission.READ_PHONE_STATE
      android.permission.SEND_SMS
    install permissions:
      android.permission.READ_PHONE_STATE: granted=true
      android.permission.SEND_SMS: granted=true
    User 0: ceDataInode=432967 installed=true hidden=false suspended=false stopped=true notLaunched=true enabled=0
      runtime permissions:


Dexopt state:
  [de.ecspride]
    Instruction Set: arm
      path: /data/app/de.ecspride-1/base.apk
      status: /data/app/de.ecspride-1/oat/arm/base.odex [compilation_filter=interpret-only, status=kOatUpToDate]


Compiler stats:
  [de.ecspride]
     base.apk - 578
    """


    #print exeResult
    for index, val in enumerate(exeResult):
        #print index ,val
        if val.strip("\r\n").strip()=='Action: "android.intent.action.MAIN"':
            # Grab the previous line. In the above example, it's "40355f5 de.ecspride/.MainActivity filter 5381d72"
            
            return exeResult[index-1].strip().split(" ")[1]

    raise AssertionError("Unable to find main intent!")


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


def install_apk(apk_path: str):

    # -r, replace the app if already installed
    # -t, allows test packages

    try:
        cmd = ["adb", "install", apk_path]
        cmd = ["adb", "install", "-r", apk_path]
        logger.debug(" ".join(cmd))
        run_command(cmd)
    except CalledProcessError as e:
        logger.error("Install failed with stderr report: " + e.stderr)
        logger.error("Attempting to uninstall and reinstall")

        # Uninstall the apk
        uninstall_apk(get_package_name(apk_path))

        # Try again
        cmd = ["adb", "install", apk_path]
        logger.debug(" ".join(cmd))
        run_command(cmd)

def check_device_is_ready() -> bool:
    cmd = 'adb devices'
    result = run_command(cmd.split())

    devices_found = result.splitlines()[1].__contains__("device")

    if not devices_found:
        logger.error("No devices found. adb devices output: \n" + result)

    return devices_found

def list_installed_apps():
    "adb shell cmd package list packages -3"
    pass

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

    # apk_path = "/Users/calix/Documents/programming/TaintASet/com.ladywoodi.herbarium.apk"
    # # installApk(apk_path)

    # package_name = "com.ladywoodi.herbarium"
    # uninstall_apk(package_name)

    # check_adb_connection()
    pass
