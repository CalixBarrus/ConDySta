# import commands
import subprocess
import os


def getLOC(app):

    # decodeFilePath = "/Users/xueling/Desktop/hybrid/decode_batch2/"

    cmd = 'find ' + decodeFilePath + app + '/ -name *.smali'
    # print cmd

    smalis = subprocess.getoutput(cmd).split('\n')
    # print outs

    # print len(smalis)

    sumLen = 0
    for smali in smalis:
        lines = open(smali).readlines()
        sumLen += len(lines)

    print(app + " LOD: " + str(sumLen))
    result.writelines(app + " LOD: " + str(sumLen))


def decode(app):
    #find the apk
    cmd = 'find /Users/xueling/Desktop/research/hybrid_paper2/ -name ' + app +'.apk'
    # print cmd
    # apkPath = commands.getoutput(cmd)
    apkPath = "/Users/xueling/Desktop/research/hybrid_paper2/apk_org_batch2/flipboard.app.apk"
    # apkPath = "/Users/xueling/Desktop/research/hybrid_paper2/apk_1/flipboard.app.apk"

    cmd_decode = 'apktool d -f ' + apkPath + ' -o ' + decodeFilePath + app
    print(cmd_decode)
    os.system(cmd_decode)


# apps = open('/Users/xueling/Desktop/research/hybrid_paper2/temp/temp.txt').readlines()
decodeFilePath = "/Users/xueling/Desktop/research/hybrid_paper2/decodeFile/"
result = open('/Users/xueling/Desktop/research/hybrid_paper2/temp/temp_result.txt', 'w+')

apps = ['flipboard.app']
for app in apps:
    app = app.strip()
    print(app)
    try:
        decode(app)
        getLOC(app)
    except:
        continue