# this script pick the senstive methods which returns email address from ststem log
import os
import commands

# AdsID  ce3b1e33-8e03-4664-aafc-8d50f474a442
#device_serial	ZX1G22KHQK
IMEI = "355458061189396"
Serial = "ZX1G22KHQK"
Email = "utsaresearch2018@gmail.com"
AndroidID = "757601f43fe6cab0"

PII = (IMEI, Serial, Email, AndroidID)

logPath = "/home/xueling/researchProjects/sourceDetection/log/"


def findMethod(log):
    outFile = "/home/xueling/researchProjects/sourceDetection/out"
    methodPath = "/home/xueling/researchProjects/sourceDetection/methods/"
    setMethods = set()     # remove the duplicated methods from log

    flag = 0
    # # cmd = "grep \"Return string detection printStackTrace and parameter:: utsaresearch2018@gmail.com\" " + logPath + log + " -r -A 5" + " >" + outFile
    # cmd = "grep " + '\"' + IMEI +'\|' + Serial +'\|'+ Email+'\|' + AndroidID + '\" ' + logPath + log + " -r " + " >" + outFile
    #
    # print cmd
    # os.system(cmd)
    #
    # flags = open(outFile).readlines()
    # set_procID = set()
    # set_theadID = set()
    #
    # for flag in flags:
    #     processID = flag.split(' ')[2]
    #     threadID = flag.split(' ')[3]
    #     set_procID.add(processID)
    #     set_theadID.add(threadID)
    #    # print processID, threadID
    # print len(set_procID)
    # print len(set_theadID)
    #
    # logFile = open(logPath + log).readlines()
    # list_temp = list()
    #
    # print "logfile"
    # print len(logFile)
    # temp = open("/home/xueling/researchProjects/sourceDetection/temp", 'a+')
    #
    # # threadID_set_log = set()
    # # procID_set_log = set()
    #
    # for line in logFile:
    #     # print line
    #     processID = line.split(' ')[2]
    #     threadID = line.split(' ')[3]
    #     # procID_set_log.add(processID)
    #     # threadID_set_log.add(threadID)
    #     if processID in set_procID and threadID in set_theadID:
    #         # print processID, threadID
    #         temp.write(line)
    #         # list_temp.append(line)
    # # print "threadID_set_log, threadID_set_log"
    # # print len(threadID_set_log), len(threadID_set_log)
    # # print threadID_set_log,
    #
    #
    # # print len(list_temp)

    fw = open(methodPath + log, 'a')

    lines = open(logPath + log).readlines()
    for line in lines:
        line = line.strip()
        if "W System.err: java.lang.Exception:" in line:
            if any(s in line for s in PII):
                print line
                flag = 1
                continue

        if flag == 1:
            if "W System.err: 	at" in line:
                # print line
                method = line.split("(")[0].split("W System.err: 	at ")[1]
                # print method
                setMethods.add(method)
                flag = 0
                continue
            else:
                print line
                print "the next line is not correct"

        # if "--" in line and flag == 1:
        #     print "can't find method"
        #     print line

    for method in setMethods:
        fw.writelines(method + '\n')


logs = commands.getoutput('ls ' + logPath).split('\n')
print logs
for log in logs:
    if "temp" in log:
        findMethod(log)