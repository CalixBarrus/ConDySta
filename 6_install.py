# install apk (10 app each batch) and start the app on device


import os
import webbrowser
import time
apk_signedPath = "/home/xueling/apkAnalysis/dynamicSupplementStatic/general_10/apk_signed/"
platformPath = "/home/xueling/Android/Sdk/platform-tools"
packageNameListALL = []
apkNameList = []


def uninstallApk(packageName):
    cmd="adb uninstall %s"%packageName
    print cmd
    print getCmdEexcuteResult(cmd)

#

def getCmdEexcuteResult(cmd):
    tmp = os.popen(cmd).readlines()
    return tmp


def getPackageName(installName):
    installName = apk_signedPath + installName
    cmd = 'aapt dump badging "%s" '%installName
    print cmd
    str= getCmdEexcuteResult(cmd)[0].split(" ")[1]
    return str[6:-1]

def getPackageNameInfo(packageName):
    cmd='adb shell dumpsys package %s'%packageName
    print cmd
    exeResut= getCmdEexcuteResult(cmd)
    #print exeResut
    for index,val  in enumerate(exeResut):
        #print index ,val
        if val.strip("\r\n").strip()=='Action: "android.intent.action.MAIN"':
            return exeResut[index-1].strip().split(" ")[1]

def startApk(packageName):
    try:
        packagename_mainActivity = getPackageNameInfo(packageName)
        print packagename_mainActivity
    except:
        print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        packagename_mainActivity = packageName + "/"

    print packagename_mainActivity
    cmd = "adb shell am start %s"%packagename_mainActivity
    print getCmdEexcuteResult(cmd)

def installApk(name):
    print name
    name = apk_signedPath + name
    cmd='./adb  install "%s"' %name
    os.chdir(platformPath)
    return os.system(cmd)

def batch(apkNameList,index):
    packageNameList=[]
    count_installed = 0
    print "the %dth batch:"%index
    for i in range(0,len(apkNameList)):
        print apkNameList[i][:-4]
    apkName_installed=[]
    for apkName in apkNameList:                      # install 10apk
        # print "%s installing"%apkName
        if ((installApk(apkName)) == 0):
            count_installed += 1
            print "apk_installed: %d" %count_installed
            print apkName[:-4]
            apkName_installed.append(apkName)
    print " the appInstalled in this bath:"
    print apkName_installed
    for apkName in apkName_installed:
        packageName = getPackageName(apkName)
        packageNameList.append(packageName)
        # packageNameListALL.append(packageName)

    # print "start Apk..........................."
    # # start APK
    # for packageName in packageNameList:
    #     startApk(packageName)
    # time.sleep(30)
    print "login to the app...................."
    # time.sleep(180)
    console=raw_input("delete all apk in this batch,enter y")
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
    temp = open("/home/xueling/apkAnalysis/dynamicSupplementStatic/caseStudy25/apk/nameList").readlines()
    print len(temp)
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
    print len(apklist)
    for i in range(0,10):
        cmd = "mv /home/xueling/apkAnalysis/invokeDetection/apk_signed/tune/%s %s" % (apklist[i], apk_signedPath)
        print cmd
        os.system(cmd)


def  moveToDone():
    files = os.listdir(apk_signedPath)
    for file in files:
        cmd = "mv %s%s /home/xueling/apkAnalysis/invokeDetection/apk_signed/tune/done/"  %(apk_signedPath,file)
        print cmd
        os.system(cmd)


def openWeb():
    # files = os.listdir(apk_signedPath)
    files = open("/home/xueling/apkAnalysis/dynamicSupplementStatic/caseStudy/apk/nameList").readlines()
    for file in files:
        file = file.strip()
        url_1 = "https://play.google.com/store/apps/details?id="
        webbrowser.open(url_1 + file, new=0, autoraise=True)
        time.sleep(2)


# moveToWork()
# openWeb()
installAndStart()
# moveToDone()
