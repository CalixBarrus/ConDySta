import pexpect
import sys
import os

def generate_keys():

    apkNameList = []
    for apk_name in os.listdir(rebuilt_apks_path):
        apk_name = apk_name.strip()
        apkNameList.append(apk_name)
    print(len(apkNameList))

    i = 1
    files = os.listdir(keyPath)
    for apkName in apkNameList:


        print(i)
        apkKeyName = apkName + ".keystore"
        if apkKeyName in files:
            print("{} exists!!!!".format(apkKeyName))
        else:
            cmd = "keytool -genkey -alias abc.keystore -keyalg RSA -validity 20000 -keystore {}{}".format(keyPath, apkKeyName)
            print(cmd)
            # Send all the pexpect error messages to stdout.
            # set encoding to utf-8 or stdout will whine about getting bytes, instead of strings
            child = pexpect.spawn(cmd, logfile = sys.stdout, encoding='utf-8')


            #password
            try:
                if(child.expect('password') == 0): # Enter keystore password:
                    child.sendline('123456')
            except Exception as e:
                print(str(child))


            #re-enter password
            try:
                if (child.expect([pexpect.TIMEOUT, 'Re-enter'])): # Re-enter new password:
                    child.sendline('123456')
            except Exception as e:
                print(str(child))


            # first and last name
            try:
                if (child.expect([pexpect.TIMEOUT, 'last'])):# What is you first and last name?\n  [Unknown]:
                    child.sendline('Calix Barrus')
            except Exception as e:
                print(str(child))


            # unit
            try:
                if (child.expect([pexpect.TIMEOUT, 'unit'])): # What is the name of your organizational unit?
                    child.sendline('UTSA')
            except Exception as e:
                print(str(child))


            # organization
            try:
                if (child.expect([pexpect.TIMEOUT, 'organization'])):
                    child.sendline('UTSA')
            except Exception as e:
                print(str(child))


            # city
            try:
                if (child.expect([pexpect.TIMEOUT, 'City'])):
                    child.sendline('San Antonio')
            except Exception as e:
                print(str(child))


            # state
            try:
                if (child.expect([pexpect.TIMEOUT, 'State'])):
                    child.sendline('TX')
            except Exception as e:
                print(str(child))

            # country code
            try:
                if (child.expect([pexpect.TIMEOUT, 'country code'])):
                    child.sendline('01')
            except Exception as e:
                print(str(child))

            # correct?
            try:
                if (child.expect([pexpect.TIMEOUT, 'correct'])):
                    child.sendline('y')
            except Exception as e:
                print(str(child))


            # RETURN
            try:
                child.expect(pexpect.EOF)
            except Exception as e:
                print(str(child))

            i+= 1

if __name__ == '__main__':
    # keyPath = "/home/xueling/apkAnalysis/invokeDetection/keys/"

    keyPath = "apk-keys/"
    rebuilt_apks_path = 'rebuilt-apks/'

    generate_keys()