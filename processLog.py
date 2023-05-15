# process the input_log_path, get the call stack into list
import re

Model = "Nexus"
Make = "motorola"
OS = '7.1.1'
IMEI = "355458061189396"
Serial = "ZX1G22KHQK"
Email = "utsaresearch2018@gmail.com"
AndroidID = 'a54eccb914c21863'
PassWord = 'uuuu8888'
UserName_1 = 'utsa'
UserName_2 = 'UTSA'
UserName_3 = 'Utsa'
device_code = "shamu"
code = "Nougat"
language = "English"
country = "US"
advertiserId = "fc1303d8-7fbb-44d8-8a68-a79ffac06fea"
timezone_1 = "CST"
timezone_2 = "Central Standard Time"
CPU_1 = "armeabi"
CPU_2 = "armeabi-v7a"
NetWork = "Wi-Fi"


PII = (Model, Make, OS,  IMEI, Serial, Email, AndroidID, PassWord, UserName_1, UserName_2, UserName_3, device_code , code, language, country,
       advertiserId, timezone_1, timezone_2,
       CPU_1, CPU_2, NetWork)

def getStackTraces(app):       # process input_log_path file into a list, each element will be a stackTrace

    logPath = "/Users/xueling/Desktop/hybrid/input_log_path/"
    # input_log_path = "/Users/xueling/Desktop/hybrid/log_batch2/"

    stackTraces = []
    flag = 0
    lines = open(logPath  + app).readlines()

    temp = []
    for i in range (0, len(lines)):
        if lines[i]:
            line = lines[i].strip()
            if "W System.err: java.lang.Exception:" in line and flag == 0:
                flag += 1
                temp = []
                temp.append(lines[i])
                
                
            elif "W System.err: java.lang.Exception:" in line and flag != 0:
                stackTraces.append(temp)
                temp = []
                temp.append(lines[i])
                flag += 1     
                

            elif re.search(r'W System.err:\s+at .*[(].*[)]', line) and flag != 0 and i != (len(lines) - 1):
                temp.append(lines[i])

           

            elif i == (len(lines) - 1):
                if temp:
                    stackTraces.append(temp)



    return stackTraces

def pickPIIst(stackTraces):
    """Filter the stack traces down to those who contain an exception with value
    equalling one of the PII strings listed at the top of this file."""
    PIIstackTraces = []
    for stack in stackTraces:
        for item in PII:
            if item in stack[0].split('java.lang.Exception: ')[1]:
                # print item
                # print stack[0].strip()
                PIIstackTraces.append(stack)
                break
    return PIIstackTraces

def processLog(app):
    stackTraces = getStackTraces(app)
    print('len(stackTraces): ' + str(len(stackTraces)))
    # for line in stackTraces[0]:
    #     print line
    PIIstackTraces = pickPIIst(stackTraces)
    print('len(PIIstackTraces): ' + str(len(PIIstackTraces)))

    return PIIstackTraces
