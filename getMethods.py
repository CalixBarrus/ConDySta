# this script pick the senstive methods which returns email address from ststem log
import os
import commands


def findMethod(apk):
    logPath = "/Users/xueling/Downloads/log/"
    outFile = "/Users/xueling/Downloads/out"
    methodPath = "/Users/xueling/Downloads/methods/"
    setMethods = set()     # remove the duplicated methods from log


    apkLog = apk + '.log'
    flag = 0

    cmd = "grep \"Return string detection printStackTrace and parameter:: utsaresearch2018@gmail.com\" " + logPath + apkLog + " -r -A 5" + " >" + outFile
    print cmd
    os.system(cmd)

    fw = open(methodPath + apk, 'a')

    lines = open(outFile).readlines()
    for line in lines:
        line = line.strip()
        if "Return string detection printStackTrace and parameter:: utsaresearch2018@gmail.com" in line:
            print line
            flag = 1
            continue
        if flag == 1 and "W System.err: 	at" in line:
            print line
            method = line.split("(")[0].split("W System.err: 	at ")[1]
            print method
            setMethods.add(method)
            flag = 0
            continue

        if "--" in line and flag == 1:
            print "can't find method"

    for method in setMethods:
        fw.writelines(method + '\n')


apkList = open("/Users/xueling/Downloads/25_nameList").readlines()
for apk in apkList:
    apk = apk.strip()
    if apk:
        findMethod(apk)