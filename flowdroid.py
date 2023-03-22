import os
import intercept.intercept_config


def activate_flowdroid(input_apk_path, apk_name, source_and_sink_path,
                       output_log_path):
    if not apk_name.endswith(".apk"):
        raise ValueError(f"Input apk_name {apk_name} needs to end with \".apk\"")

    intercept_config = \
        intercept.intercept_config.get_default_intercept_config()

    flowdroid_jar = intercept_config.flowdroid_jar_path
    android_platform_path = intercept_config.android_platform_path

    log_name = apk_name.replace(".apk", ".log")

    cmd = 'java -jar ' + flowdroid_jar + ' -a ' + os.path.join(input_apk_path,apk_name) + ' -p' + android_platform_path + ' -s ' + source_and_sink_path + ' > ' + os.path.join(output_log_path, log_name) + ' 2>&1'
    if intercept_config.verbose:
        print(cmd)
    os.system(cmd)


def activate_flowdroid_batch(input_apks_path, source_and_sink_path,
                                 output_log_path, recursive=False):

    if not os.path.isdir(input_apks_path):
        raise FileNotFoundError(f"Directory {input_apks_path} not found.")

    for item in os.listdir(input_apks_path):
        if os.path.isfile(os.path.join(input_apks_path, item)) and item.endswith(".apk"):
            activate_flowdroid(input_apks_path, item, source_and_sink_path,
                               output_log_path)

        if recursive:
            if os.path.isdir(os.path.join(input_apks_path, item)):
                activate_flowdroid_batch(os.path.join(input_apks_path, item),
                                         source_and_sink_path,
                                         output_log_path, recursive)


if __name__ == '__main__':
    apk_name = "app.debug.apk"
    apk_path = intercept_configuration = \
        intercept.intercept_config.get_default_intercept_config().input_apks_path
    sources_and_sinks = "SourcesAndSinks.txt"  # The flowdroid default is in
    # the root of this project

    activate_flowdroid(apk_path, apk_name, sources_and_sinks)



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