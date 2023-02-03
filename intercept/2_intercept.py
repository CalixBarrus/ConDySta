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
    print("parameterCount: {}".format(parameterCount))

    print(paraNumberList)

    print(parameterCount)
    print(localsNumber)

    if (16 - localsNumber - parameterCount) >= 1:
        locals_new = "    .locals " + str(localsNumber + 1)
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


            text_toBeAdd_cond = "    if-nez " + returnVar + ", " \
                                                             ":cond_returnStringDetection" + str(cond_index)
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

    newMethod[locals_index] = locals_new

    return newMethod




def stringReturnDetection():
    apkPath = decoded_apks_path
    flag = 0

    v1 = " "
    v2 = " "

    cmd = "find {} -iname *.smali ".format(apkPath)
    smali_paths = os.popen(cmd).readlines()

    print(str(len(smali_paths)) + " smali files found!")

    for smali_path in smali_paths:
        smali_path = smali_path.strip()
        smali_file = open(smali_path)
        text_orig = smali_file.readlines()
        text_new = []
        method = []
        # print len(text_orig)

        for lines in text_orig:
            line = lines.rstrip()

            # Start method collection for any string return functions that are
            # not abstract, contructors, or native.
            if ".method" in line and "abstract" in line:
                text_new.append(line)
                continue

            elif ".method" in line and "constructor" in line:
                text_new.append(line)
                continue


            elif ".method" in line and "native" in line:
                text_new.append(line)
                continue

            elif ".method" in line and ")Ljava/lang/String;" in line:  #  method return string
                print(smali_path)
                print(line)
                flag = 1
                method.append(line)
                continue

            # When an appropriate string return method is detected, collect all
            # the code until ".end method" into the "method" variable. When
            # ".end method" gets hit, pass it to "instrument" and begin scanning
            # for more methods.
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

        smali_file.close()
        # Replace the smali code with the instrumented code
        os.remove(smali_path)
        fw = open(smali_path, 'w+')
        for line in text_new:
            fw.write(line + '\n')

if __name__ == '__main__':
    decoded_apks_path = 'decoded-apks/'

    # stringArgumentDetection()
    stringReturnDetection()
