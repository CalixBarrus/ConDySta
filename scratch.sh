#!/usr/bin/env bash

# Only use absolute paths when working with flowdroid. If you use relative
#   paths (like ~), it will append the path to the current directory.
#flowdroid_jar_path="/home/calix/Documents/coding-projects/FlowDroid/soot-infoflow-cmd/target/soot-infoflow-cmd-jar-with-dependencies.jar"
flowdroid_jar_path="/Users/calix/Documents/CodingProjects/research/soot-infoflow-cmd-jar-with-dependencies.jar"

#android_sdk_path="/home/calix/Android/Sdk/platforms/"
android_sdk_path="/Users/calix/Library/Android/sdk/platforms/"
#source_sink_textfile_path="/home/calix/Documents/coding-projects/FlowDroid/soot-infoflow-android/SourcesAndSinks.txt"
source_sink_textfile_path="/Users/calix/Documents/CodingProjects/research/FlowDroid/test-files/SourcesAndSinks.txt"

apk_to_analyze_path="test-apks/art.coloringpages.paint.number.zodiac.free.apk"

#java -jar $flowdroid_jar_path --help
java -jar $flowdroid_jar_path \
-a $apk_to_analyze_path \
-p $android_sdk_path \
-s $source_sink_textfile_path \
-o flowdroid_xml_output.xml \
2> flowdroid_log_output.txt
