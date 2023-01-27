import processLog
# import commands
import re
import os
import subprocess

def convert(methodSet, app):
    """
    Convert each method in the method set into strings that Flowdroid will
    recognize as taint sources, and write all these strings into a file,
    (presumably) ready for input into flowdroid.

    :param methodSet: Set of strings. Each string is not just a method, but a
    whole signature. I'm not sure how much/what is in the string.
    :param app: String. Name of target file in a number of hard coded
    directories. This is used for both file input and output.
    :return: Void.
    """
    decodeFilePath = "/Users/xueling/Desktop/hybrid/decode_batch2/"
    # signature path that is the same being used globally at the bottom of the file
    signaturePath = "/Users/xueling/Desktop/hybrid/PII_sourceSig_batch2/"

    print(
        'Converting methods into FLowDroid source signatures.................')

    # Only run the function if there is no file in the "signature" folder with
    # name matching the string app.
    files = subprocess.getoutput('ls ' + signaturePath).split('\n')
    if app in files:
        print(app + 'exists!!')
    else:
        # Create new file in "signature" folder
        fw = open(signaturePath + app, 'a')

        for sig in methodSet:
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

            cmd = 'grep --include ' + className + '.smali -F ' + '\'' + methodName + '(\' ' + decodeFilePath  +  app + '/ ' +'-r '  + '| grep \'.method\' ' + '| grep \')Ljava/lang/String;\''
            # cmd = 'grep --include *.smali -F ' + '\'' + methodName + '(\' ' + decodeFilePath  + ' -r '  + '| grep \'.method\' '
            print(cmd)
            outs = subprocess.getoutput(cmd).split('\n')                                # all matches, one app could have multiple method using same name under different classes

            # TODO: why grep more info aabout the command when you already have
            #  the info in sig? Is the arguments info not included?

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
                        fw.write(sigNew + '\n')
                        # print out
                        print(sigNew)
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
                        fw.write(sigNew + '\n')
                        print(sigNew)
                else:
                    continue

def getSources(app):
    PIIstackTraces = processLog.processLog(app)
    # print len(PIIstackTraces)

    # Create set of methods that show up in the app log file after "W System.err:"
    # Each "Method" is a long string with a lot of info that gets parsed by convert.
    # TODO: what are these log files? A simple Flowdroid log file with leaks
    #  does not have any System.err.
    methodSet = set()
    for stack in PIIstackTraces:
        if len(stack) > 1:
            method = stack[1].split("(")[0].split("W System.err: 	at ")[1]
            print(method)
            methodSet.add(method)


    convert(methodSet, app)

signaturePath = "/Users/xueling/Desktop/hybrid/PII_sourceSig_batch2/"
logPath = "/Users/xueling/Desktop/hybrid/log_batch2/"

apks = subprocess.getoutput('ls ' + logPath).split('\n')

i = 1
files = os.listdir(signaturePath)

# Only call getSources on files in the "log" folder who do not have corresponding
# files in the "signature" folder

for apk in apks:
    print(apk)
    if apk in files:
        print(apk)
        print("exists!!!")
        i += 1
    else:
        getSources(apk)