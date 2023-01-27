# decode

import os
import commands


APKpath = "/home/xueling/researchProjects/sourceDetection/apk_org/"
# apkPath = "/home/xueling/apkAnalysis/invokeDetection/apks/"
# smaliPath = "/home/xueling/apkAnalysis/invokeDetection/smalis/"
decodeFilePath = "/home/xueling/researchProjects/sourceDetection/decodeFile/"



apkNameList = []


#decode 1007 apks
def decode():
    # get apkNamelist_1007
    # for line in open("/home/xueling/apkAnalysis/invokeDetection/apkName_1007").readlines():

    apks = commands.getoutput('ls ' + APKpath).split('\n')
    print apks
    i = 1
    files = os.listdir(decodeFilePath)
    for apk in apks:
        # decompile to smaliPath
        print i
        if apk in files:
            print apk
            print "exists!!!"
            i += 1
            continue

        else:
            cmd = "apktool d -r %s%s -o %s%s" %(APKpath, apk, decodeFilePath, apk[:-4])
            print cmd
            os.system(cmd)
            i += 1



# move to library name
def move():
    apkNameList = set()
    lines = open("/home/xueling/apkAnalysis/invokeDetection/decodeFile/nameList/branch").readlines()
    print "len(lines): %d" %len(lines)
    for line in lines:
        line = line.strip() + ".apk"
        apkNameList.add(line)
    print "len(apkNameList): %d" % len(apkNameList)

    files = os.listdir(decodeFilePath)
    for line in apkNameList:
        if line in files:
            print "%s exists!!!" %line

        else:
            cmd = "mv %s%s %s" %(smaliPath, line, decodeFilePath)


            print cmd
            ret = os.system(cmd)
            print ret
            if ret == 256:
                fw = open("/home/xueling/apkAnalysis/invokeDetection/decodeFile/nameList/temp", "a")
                fw.write(line + "\n")
                fw.close()

decode()


# move()
