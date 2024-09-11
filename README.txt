Setup Notes:

Have Java and Python 3 installed.

Make "data/intercept", "data/logs", "data/sources-and-sinks", "data/logs/instrumentation-run", "input-apk-lists" and "data/input-apks" directories.

Run setup_folders() method in hybrid/experiment.py

Install the following python modules:
pexpect

Install apktool (https://apktool.org/docs/install/)

Ensure the following Android platform tools can be run from the command line:
    To make a tool executable from commandline: mode to directory /usr/local/bin and then run the command
    "sudo ln -s ~/Library/Android/sdk/platform-tools/adb adb" where the second to last
    arg is the path to the executable, and the last arg is the name of the executable.
adb (On my machine, this is found at: ~/Library/Android/sdk/platform-tools/adb)
apksigner (~/Library/Android/sdk/build-tools/34.0.0/apksigner)
aapt (~/Library/Android/sdk/build-tools/34.0.0/aapt)

Get a JAR of FlowDroid, and make sure the path in hybrid_config.py points to it.

You probably will want to download and use benchmarks, I used the ones from ReproDroid's website (https://foellix.github.io/ReproDroid/).

Folders: benchmarks subset, flowdroid-jars, IC3

From mordahls TA Env setup: 
# Android SDK
wget https://dl.google.com/android/repository/sdk-tools-linux-4333796.zip
unzip sdk-tools-linux-4333796.zip
cd tools
./bin/sdkmanager "packages;android-25"
cd ~

Download command line tools from the GUI link here
https://developer.android.com/studio#command-tools
unzip [sdk-tools-linux-4333796.zip]
# make sure java is updated (>= Java 17)
cd [tools]
./bin/sdkmanager "packages;android-25"



