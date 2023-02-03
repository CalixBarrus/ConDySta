
import pexpect
import sys
import os

def main():
    apkNameList = []
    for apk_name in os.listdir(rebuiltApksPath):
        apk_name = apk_name.strip()
        apkNameList.append(apk_name)
    print(len(apkNameList))

    i = 1
    # for line in apkNameList:
    for apkName in os.listdir(rebuiltApksPath):

        # If the apk is already signed, don't sign it again.
        if os.path.exists(os.path.join(signedApksPath, apkName)):
            print("{} already signed.".format(apkName))
            continue

        # Make sure the apk being signed exists
        if os.path.isfile(os.path.join(rebuiltApksPath, apkName)):
            apkKeyName = apkName + ".keystore"
            # cmd = "jarsigner -verbose -keystore {}{} -storepass 123456 -signedjar {}{} {}{} abc.keystore".format(keyPath, apkKeyName, signedApksPath, apkName, rebuiltApksPath, apkName)
            # In theory, this should be "zipalign"ed and verified before signing. It seems to work OK without that step though.
            cmd = "apksigner sign --ks {}{} --ks-pass pass:123456 --in {}{} --out {}{}".format(keyPath, apkKeyName, rebuiltApksPath, apkName, signedApksPath, apkName)
            print(cmd)
            child = pexpect.spawn(cmd, logfile=sys.stdout, encoding='utf-8')

            #password
            try:
                result = child.expect([pexpect.EOF, 'password', pexpect.TIMEOUT])
                if result == 0:
                    # Expected result, do nothing.
                    pass
                elif result == 1:
                    # It might be asking for a password?
                    child.sendline('123456')
                    child.expect(pexpect.EOF)
                else:
                    raise NotImplementedError("Unexpected result from jarsigner")
            except Exception as e:
                print(str(child))
        else:
            print("Apk {} isn't recognized as a file?".format(os.path.join(rebuiltApksPath, apkName)))


if __name__ == '__main__':
    # keyPath = "/home/xueling/apkAnalysis/invokeDetection/keys/"
    keyPath = "apk-keys/"
    # signedApksPath = "/home/xueling/apkAnalysis/invokeDetection/apk_signed/branch/"
    signedApksPath = "signed-apks/"
    # rebuiltApksPath = "/home/xueling/apkAnalysis/invokeDetection/rebuildApk/branch/"
    rebuiltApksPath = "rebuilt-apks/"

    main()


