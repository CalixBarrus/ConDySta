import pexpect
import sys
import os
import commands


rebuildApkPath = "/home/xueling/researchProjects/sourceDetection/rebuildApk/"
keyPath = "/home/xueling/researchProjects/sourceDetection/keys/"
apkNameList = []

apks = commands.getoutput('ls ' + rebuildApkPath).split('\n')

for line in apks:
    line = line.strip()
    apkNameList.append(line)
print len(apkNameList)

i = 1
files = os.listdir(keyPath)
for line in apkNameList:
    print i
    line = line + ".keystore"
    if line in files:
        print "%s exists!!!!" %line
    else:
        cmd = "keytool -genkey -alias abc.keystore -keyalg RSA -validity 20000 -keystore %s%s"%(keyPath, line)
        print cmd
        child = pexpect.spawn(cmd, logfile = sys.stdout)

        #password
        try:
            if(child.expect([pexpect.TIMEOUT, 'password'])):
                child.sendline('123456')
        except:
            print (str(child))


        #re-enter password
        try:
            if (child.expect([pexpect.TIMEOUT, 'Re-enter'])):
                child.sendline('123456')
        except:
            print (str(child))


        # last name
        try:
            if (child.expect([pexpect.TIMEOUT, 'last'])):
                child.sendline('zhang')
        except:
            print (str(child))


        # unit
        try:
            if (child.expect([pexpect.TIMEOUT, 'unit'])):
                child.sendline('utsa')
        except:
            print (str(child))


        # organization
        try:
            if (child.expect([pexpect.TIMEOUT, 'organization'])):
                child.sendline('utsa')
        except:
         print (str(child))


        # city
        try:
            if (child.expect([pexpect.TIMEOUT, 'City'])):
                child.sendline('SA')
        except:
            print (str(child))


        # state
        try:
            if (child.expect([pexpect.TIMEOUT, 'State'])):
                child.sendline('Tx')
        except:
            print (str(child))

        # country code
        try:
            if (child.expect([pexpect.TIMEOUT, 'country code'])):
                child.sendline('01')
        except:
            print (str(child))

        # correct?
        try:
            if (child.expect([pexpect.TIMEOUT, 'correct'])):
                child.sendline('y')
        except:
            print (str(child))


        # RETURN
        try:
            if (child.expect([pexpect.TIMEOUT, 'RETURN'])):
                child.sendline('\n')
        except:
            print (str(child))


        try:
            child.expect([pexpect.TIMEOUT, pexpect.EOF])
        except:
            print (str(child))

        i+= 1