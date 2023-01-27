import os
import re
def instrument(method):
    localsNumber = 0
    locals_index = 0
    v1 = ""
    v2 = ""
    newMethod = []
    cond_index = 0
    parameterCount = 0
    paraNumberList = []

    # print method[0]



    for i in range(len(method)):           # get number of locals
        line = method[i]
        if ".locals" in line:
            locals_index = i
            localsNumber = int(line.split()[1])
            break


    for line in method:        # get number of parameter registers
        paraRegList = re.findall(r'p\d+', line)
        for item in paraRegList:
            number = re.findall(r'\d+', item)
            paraNumberList.append(int(number[0]))


    if len(paraNumberList) > 0:
        parameterCount = max(paraNumberList) + 1
    print "parameterCount: %d"%parameterCount

    print paraNumberList

    print parameterCount
    print localsNumber

    if (16 - localsNumber - parameterCount) >= 1:
        locas_new = "    .locals " + str(localsNumber + 1)
        v1 = "v" + str(localsNumber)
       # v2 = "v" + str(localsNumber + 1)

    else:
        return method


    for line in method:
        if "return-object" in line:
            # print "return index: %d" %i
            returnVar = line.split()[1]

            # if flag_moreReturns == 0:

            # text_toBeAdd_cond = "    if-eqz " + returnVar + ", :cond_returnStringDetection" + str(cond_index)
            # newMethod.append(text_toBeAdd_cond)
            #
            # text_toBeAdd_tag = "    const-string " + v1 + ", \"Return string detection printStackTrace and parameter:\""
            # newMethod.append(text_toBeAdd_tag)
            #
            # text_toBeAdd_s4 = "    invoke-static{" + v1 + "," + returnVar + "},Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I"
            # newMethod.append(text_toBeAdd_s4)
            #
            # text_toBeAdd_s1 = "    new-instance " + v2 + ", Ljava/lang/Exception;"
            # newMethod.append(text_toBeAdd_s1)
            #
            # text_toBeAdd_s2 = "    invoke-direct {" + v2 + "," + v1 + "}, Ljava/lang/Exception;-><init>(Ljava/lang/String;)V"
            # newMethod.append(text_toBeAdd_s2)
            #
            # text_toBeAdd_s3 = "    invoke-virtual {" + v2 + "}, Ljava/lang/Exception;->printStackTrace()V"
            # newMethod.append(text_toBeAdd_s3)
            #
            # text_toBeAdd_s5 = "    :cond_returnStringDetection" + str(cond_index) + "\n"
            # newMethod.append(text_toBeAdd_s5)


            text_toBeAdd_cond = "    if-eqz " + returnVar + ", :cond_returnStringDetection" + str(cond_index)
            newMethod.append(text_toBeAdd_cond)

            text_toBeAdd_s1 = "    new-instance " + v1 + ", Ljava/lang/Exception;"
            newMethod.append(text_toBeAdd_s1)

            text_toBeAdd_s2 = "    invoke-direct {" + v1 + "," + returnVar + "}, Ljava/lang/Exception;-><init>(Ljava/lang/String;)V"
            newMethod.append(text_toBeAdd_s2)

            text_toBeAdd_s3 = "    invoke-virtual {" + v1 + "}, Ljava/lang/Exception;->printStackTrace()V"
            newMethod.append(text_toBeAdd_s3)
            text_toBeAdd_s5 = "    :cond_returnStringDetection" + str(cond_index) + "\n"
            newMethod.append(text_toBeAdd_s5)


            newMethod.append(line)

            # flag_moreReturns = 1
            cond_index += 1




        else:
            newMethod.append(line)
            # print "else: %s" %line

    # print "xxxxxxxxxxxxxxxxxxxxxx new method: "

    # for line in newMethod:
    #         print line.strip()

    newMethod[locals_index] = locas_new

    return newMethod




def stringReturnDetection():
    apkPath = "/home/xueling/researchProjects/sourceDetection/decodeFile/"
    flag = 0

    v1 = " "
    v2 = " "

    cmd = "find %s -iname *.smali " % (apkPath)
    paths = os.popen(cmd).readlines()

    print str(len(paths)) + " smali files found!"

    for path in paths:
        path = path.strip()
        smaliFile = open(path)
        text_org = smaliFile.readlines()
        text_new = []
        method = []
        # print len(text_org)

        for lines in text_org:
            line = lines.rstrip()

            if ".method" in line and "abstract" in line:
                text_new.append(line)
                continue

            if ".method" in line and "constructor" in line:
                text_new.append(line)
                continue


            if ".method" in line and "native" in line:
                text_new.append(line)
                continue

            if ".method" in line and ")Ljava/lang/String;" in line:  #  method return string
                print path
                print "%s" % line
                flag = 1
                method.append(line)
                continue


            if flag == 1:
                if ".end method" in line:
                    method.append(line)
                    flag = 0
                    newMethod = instrument(method)
                    method = []
                    for line in newMethod:
                        text_new.append(line)
                else:
                    method.append(line)


            else:
                text_new.append(line)

        smaliFile.close()
        os.remove(path)
        fw = open(path, 'w+')
        for line in text_new:
            fw.write(line + '\n')

# stringArgumentDetection()
stringReturnDetection()
