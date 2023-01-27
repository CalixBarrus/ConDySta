
import pexpect
import sys
import os

keyPath = "/home/xueling/researchProjects/sourceDetection/keys/"
apk_signedPath = "/home/xueling/researchProjects/sourceDetection/apk_signed/"
rebuildApkPath = "/home/xueling/researchProjects/sourceDetection/rebuildApk/"
apkNameList = []


i = 1
for file in os.listdir(rebuildApkPath):
    if os.path.isfile(os.path.join(rebuildApkPath, file)):
        # key = file[:-4] + ".keystore"
        key = file + ".keystore"
        cmd = "jarsigner -verbose -keystore %s%s -storepass 123456 -signedjar %s%s %s%s abc.keystore" %(keyPath, key,apk_signedPath,file, rebuildApkPath, file)
        print cmd
        os.system(cmd)

        # child = pexpect.spawn(cmd, logfile = sys.stdout)
        #
        # password
        # try:
        #     if(child.expect([pexpect.TIMEOUT, 'password'])):
        #         child.sendline('123456')
        # except:
        #     print (str(child))
        # try:
        #     child.expect([pexpect.TIMEOUT, pexpect.EOF])
        # except:
        #     print (str(child))



