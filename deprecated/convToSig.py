import sys
import commands
import os
import re




def convert(apk):

    sigOrgPath = "/home/xueling/apkAnalysis/dynamicSupplementStatic/caseStudy25/returnDetectString/risk_methods/" + apk
    sigOrgs = open(sigOrgPath).readlines()
    decodeFilePath = "/home/xueling/apkAnalysis/dynamicSupplementStatic/caseStudy25/returnDetectString/decodeFile/" + apk

    for sig in sigOrgs:
        # print sig.strip()
        className = sig.strip().split('.')[-2]
        # print className
        methodName = sig.strip().split('.')[-1]
        # print methodName

        classPaths = sig.strip().split('.')[:-1]
        classPath = '.'.join(classPaths)
        filePath = '/'.join(classPaths)
        # print classPaths
        # print filePath


        cmd = 'grep --include ' + className + '.smali -F ' + '\'' + methodName + '(\' ' + decodeFilePath  + '/ -r '  + '| grep \'.method\' ' + '| grep \')Ljava/lang/String;\''
        # cmd = 'grep --include *.smali -F ' + '\'' + methodName + '(\' ' + decodeFilePath  + ' -r '  + '| grep \'.method\' '
        # print cmd
        outs = commands.getoutput(cmd).split('\n')                                # all mathes, one app could have multiple method using same name under different classes
        # print outs
        for out in outs:
            # print out
            flag = 0

            if filePath in out:                  # check the path
                flag = 1
                # print out
                # print "in flag1"

            else:
                # print "in flag0"
                flag = 0
                continue

            if flag == 1:
                methodDeclar = out.split(':')[1]
                # print methodDeclar
                arguments = re.findall(r'\(.*\)', methodDeclar)[0]
                # print "arguments: %s" %arguments

                if arguments == '()':          # no argument
                    sigNew = '<' + classPath + ': ' + 'java.lang.String ' + methodName + '()' + '>' + ' -> _SOURCE_'
                    # print out
                    print sigNew
                    continue

                else:
                    # print "argument exists!"
                    newArgumentsList = []
                    arguments = arguments.lstrip('(')
                    arguments = arguments.rstrip(')')
                    # print arguments
                    argumentsList = arguments.split(';')     # multiple arguments

                    # if len(argumentsList) > 2:
                    #     print "multiple argument!!!!"


                    for argument in argumentsList:
                        # print argument
                        if argument == 'V':
                            argument = 'void'
                        elif argument == 'Z':
                            argument ='boolean'
                        elif argument == 'B':
                            argument = 'byte'
                        elif argument == 'I':
                            argument = 'int'
                        elif argument == 'C':
                            argument = 'char'
                        elif argument == 'S':
                            argument = 'short'
                        elif argument == 'J':
                            argument = 'long'
                        elif argument == 'D':
                            argument = 'double'
                        elif argument == 'F':
                            argument = 'float'
                        elif argument == 'IZ':
                            argument = 'int,boolean'

                        elif "[" in argument:
                            argument = argument.lstrip('[') + ("[]")


                        newArgument = argument.lstrip('L').replace("/", ".")
                        # print newArgument
                        newArgumentsList.append(newArgument)
                    newArguments = ','.join(newArgumentsList).rstrip(',')
                    sigNew = '<' + classPath + ': ' + 'java.lang.String ' + methodName + '(' + newArguments + ')' + '>' + ' -> _SOURCE_'
                    print sigNew


            else:
                continue


apks = open( "/home/xueling/apkAnalysis/dynamicSupplementStatic/caseStudy25/25_nameList").readlines()

i = 1
for apk in apks:
    print str(i) + "====================" + apk
    apk = apk.strip()
    if apk:
        convert(apk)
        i += 1


