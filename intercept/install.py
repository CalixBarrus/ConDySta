# install apk (10 app each batch) and start the app on device


import os
import webbrowser
import time

def uninstallApk(packageName):
    cmd="adb uninstall %s"%packageName
    print(cmd)
    print(getCmdExecuteResult(cmd))
#

def getCmdExecuteResult(cmd):
    tmp = os.popen(cmd).readlines()
    return tmp


def getPackageName(installName, signed_apk_path):
    installName = signed_apk_path + installName
    cmd = 'aapt dump badging "{}" '.format(installName)
    print(cmd)
    str= getCmdExecuteResult(cmd)[0].split(" ")[1]
    return str[6:-1]

def getApkMainIntent(packageName):
    """
    :param packageName: packageName resulting from getPackageName call.
    :return: String that can be used as an Intent to launch the main activity of
    the apk.
    """
    cmd='adb shell dumpsys package {}'.format(packageName)
    print(cmd)
    exeResult= getCmdExecuteResult(cmd)
    #print exeResult
    for index, val in enumerate(exeResult):
        #print index ,val
        if val.strip("\r\n").strip()=='Action: "android.intent.action.MAIN"':
            return exeResult[index-1].strip().split(" ")[1]

def startApk(packageName):
    try:
        packagename_mainActivity = getApkMainIntent(packageName)
        print(packagename_mainActivity)
    except:
        print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        packagename_mainActivity = packageName + "/"

    print(packagename_mainActivity)
    cmd = "adb shell am start {}".format(packagename_mainActivity)
    print(cmd)
    print(getCmdExecuteResult(cmd))


def installApk(apkName):
    apkName = signedApkPath + apkName
    # -r, replace the app if already installed
    # -t, allows test packages
    cmd='adb  install "{}"'.format(apkName)
    # If adb is not on the path, change to the AndroidPlatform Directory
    if not adbOnPath:
        os.chdir(platformPath)
    print(cmd)
    return os.system(cmd)

def batch(apkNameList,index):
    packageNameList=[]
    count_installed = 0
    print("the {}dth batch:".format(index))
    for i in range(0,len(apkNameList)):
        print(apkNameList[i][:-4])

    apkName_installed=[]
    for apkName in apkNameList:                      # install 10apk
        # print "%s installing"%apkName
        if ((installApk(apkName)) == 0):
            count_installed += 1
            print("apk_installed: %d" % count_installed)
            print(apkName[:-4])
            apkName_installed.append(apkName)
    print(" the appInstalled in this bath:")
    print(apkName_installed)
    for apkName in apkName_installed:
        packageName = getPackageName(apkName, signedApkPath)
        packageNameList.append(packageName)
        # packageNameListALL.append(packageName)

    # print "start Apk..........................."
    # # start APK
    # for packageName in packageNameList:
    #     startApk(packageName)
    # time.sleep(30)
    print("login to the app....................")
    # time.sleep(180)
    console=input("delete all apk in this batch,enter y")
    if console =='y':
        for packageName in packageNameList:
            uninstallApk(packageName)


def installAndStart():
    apkNameList=[]       # complete list
    apkNameList10N=[]        # 10 apks
    apkNameList_lastbatch = []
    count = 0
    # # get from folder
    # for i in os.listdir(apk_signedPath):
    #     if os.path.isfile(os.path.join(apk_signedPath, i)):
    #         if i[-4:] == '.apk':
    #             apkName = i
    #             apkNameList.append(apkName)
    # print len(apkNameList)
    #
    # index=1
    # for apkName in apkNameList:
    #     apkNameList10N.append(apkName)
    #     count+=1
    #     if count%10 == 0:
    #         # print apkNameList10N
    #         batch(apkNameList10N, index)            #rank every 10 apks
    #         index += 1
    #         apkNameList10N = []
    #
    #     if (len(apkNameList) - count) < (len(apkNameList)%10):
    #         apkNameList_lastbatch.append(apkName)
    #
    #     if len(apkNameList_lastbatch) > 0 and count == len(apkNameList):
    #         batch(apkNameList_lastbatch, index)
    #
    # print apkNameList10N


    # get from temp
    temp = open("/home/xueling/apkAnalysis/invokeDetection/temp").readlines()
    print(len(temp))
    list2 = []
    for line in temp:
        line = line.strip() + ".apk"
        list2.append(line.strip())
    batch(list2, 0)


def  moveToWork():
    files = os.listdir("/home/xueling/apkAnalysis/invokeDetection/apk_signed/branch/")
    apklist = list()
    for file in files:
        if os.path.isfile(os.path.join("/home/xueling/apkAnalysis/invokeDetection/apk_signed/branch/", file)):
            apklist.append(file)
    print(len(apklist))
    for i in range(0,10):
        cmd = "mv /home/xueling/apkAnalysis/invokeDetection/apk_signed/tune/%s %s" % (apklist[i], apk_signedPath)
        print(cmd)
        os.system(cmd)


def  moveToDone():
    files = os.listdir(apk_signedPath)
    for file in files:
        cmd = "mv %s%s /home/xueling/apkAnalysis/invokeDetection/apk_signed/tune/done/"  %(apk_signedPath,file)
        print(cmd)
        os.system(cmd)


def openWeb():
    # files = os.listdir(apk_signedPath)
    files = open("/home/xueling/apkAnalysis/invokeDetection/temp").readlines()
    for file in files:
        file = file.strip()
        url_1 = "https://play.google.com/store/apps/details?id="
        webbrowser.open(url_1 + file, new=0, autoraise=True)
        time.sleep(2)


if __name__ == '__main__':

    # apk_signedPath = "/home/xueling/apkAnalysis/invokeDetection/apk_signed/test/"
    signedApkPath = "signed-apks/"
    # signedApkPath = "rebuilt-apks/"
    # signedApkPath = "input-apks/"
    apkName = "app-debug.apk"

    signedApkPath = "../test-apks/"
    apkName = "art.coloringpages.paint.number.zodiac.free.apk"

    adbOnPath = True
    if not adbOnPath:
        platformPath = "/home/xueling/Android/Sdk/platform-tools"
    packageNameListALL = []
    apkNameList = []

    # moveToWork()
    # openWeb()

    # installAndStart()


    apkPackageName = getPackageName(apkName, signedApkPath)
    print(apkPackageName, apkName, signedApkPath)
    # uninstallApk(apkPackageName)

    installApk(apkName)

    # apkPackageName = getPackageName(apkName, signedApkPath)
    # startApk(apkPackageName)


    # moveToDone()
