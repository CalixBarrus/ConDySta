import os

apk = "com.contextlogic.wish"

jar = "/home/xueling/researchProjects/soot-infoflow-cmd-jar-with-dependencies.jar"
apk_signedPath = "/home/xueling/researchProjects/sourceDetection/apk_signed/"
apk_orgPath = "/home/xueling/researchProjects/sourceDetection/apk_org/"

analysis_default = "/home/xueling/researchProjects/sourceDetection/tainAnalysis-default/"
analysis_newSources = "/home/xueling/researchProjects/sourceDetection/tainAnalysis-newSource/"
platformPath = "/home/xueling/researchProjects/platforms/"
SourceAndSinks_default = "/home/xueling/researchProjects/sourceDetection/SourceAndSinks_default.txt"
SourceAndSinks_newSources = "/home/xueling/researchProjects/sourceDetection/SourceAndSinks_newSources.txt"

#
cmd_taint_default = 'java -jar ' + jar + ' -a ' + apk_orgPath + apk + '.apk -p' + platformPath + ' -s ' + SourceAndSinks_default + ' > ' + analysis_default + apk + ' 2>&1'
os.system(cmd_taint_default)
# #
# cmd_install = 'adb install ' + apk_signedPath + apk + '.apk'
# os.system(cmd_install)
#
# cmd_logcat_c = 'adb logcat -c'
# os.system(cmd_logcat_c)
#
#
# logPath = '/home/xueling/researchProjects/sourceDetection/log/'
# cmd_logcat_out = 'adb logcat > ' + logPath + apk
# os.system(cmd_logcat_out)


# cmd_taint_newSource = 'java -jar ' + jar + ' -a ' + apk_orgPath + apk + '.apk -p' + platformPath + ' -s ' + SourceAndSinks_newSources + ' > ' + analysis_newSources + apk + ' 2>&1'
# print cmd_taint_newSource
# os.system(cmd_taint_newSource)