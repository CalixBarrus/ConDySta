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


def uninstall_apk(package_name):
    cmd="adb uninstall {}".format(package_name)
    logger.debug(cmd)
    cmd_result = execute_cmd_for_result(cmd)


def execute_cmd_for_result(cmd: str) -> str:
    result = run_command(cmd.split(), redirect_stderr_to_stdout=True)
    return result


def get_package_name(apk_path, output_apk_model: ApkModel=None):
    # apk_model is optional parameter to save off additional information from the dump badging operation.

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

    package_name_field = result.split('\n')[0].split(" ")[1]
    # name='de.ecspride'
    package_name = package_name_field[6:-1]

    if output_apk_model is not None:
      output_apk_model.apk_package_name = package_name

      for line in result.splitlines():
          if line.strip().startswith("application-label:'"):
              # Name of the app in the phone
              # application-label:'StaticInitialization1'     
              application_label = line[19:-1]
              output_apk_model.apk_application_label = application_label
              break

    package_name_field = result.split('\n')[0].split(" ")[1]
    # name='de.ecspride'
    package_name = package_name_field[6:-1]

    return package_name







def getApkMainIntent(packageName):
    # TODO: refactor function
    """
    :param packageName: packageName resulting from getPackageName call.
    :return: String that can be used as an Intent to launch the main activity of
    the apk.
    """

    cmd='adb shell dumpsys package {}'.format(packageName)
    logger.debug(cmd)
    exeResult= execute_cmd_for_result(cmd)

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
    logger.debug(execute_cmd_for_result(cmd))


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

    # TODO: If multiple devices, make sure ANDROID_SERIAL env variable is set or something

    return devices_found

def list_installed_3rd_party_apps() -> List[str]:
    # Return package names of installed 3rd party apps 

    cmd = "adb shell cmd package list packages -3"
    result = execute_cmd_for_result(cmd)

    """Expected output like:
package:io.appium.settings
package:io.appium.uiautomator2.server
package:edu.utsa.sefm.heapsnapshot
package:io.appium.uiautomator2.server.test
package:com.lexa.fakegps
    """

    package_names = [line.strip().split(":")[1] for line in result.splitlines()]

    return package_names

def clean_apps_off_phone():
    package_names_to_keep = [
        "package:com.lexa.fakegps",
        "package:io.appium.uiautomator2.server.test",
        "package:io.appium.uiautomator2.server",
        "package:io.appium.settings",
        ]

    package_names = list_installed_3rd_party_apps()

    for package_name in  package_names:
      if package_name not in package_names_to_keep:
        uninstall_apk(package_name)


if __name__ == '__main__':

    pass
